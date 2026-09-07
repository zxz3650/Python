"""Offline teaching pipeline for declared, parser-produced Windows artifact CSVs.

No collection, binary parser execution, Sigma evaluation or network access occurs here.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import csv
from datetime import datetime, timedelta, timezone
import hashlib
from html import escape
import io
import ipaddress
import json
import ntpath
from pathlib import Path
import re
import sys

VERSION = "1.0"
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_TOTAL_ROWS = 100_000
FIELDS = {
    "timestamp", "event_id", "channel", "provider", "record_id", "user",
    "src_ip", "logon_type", "path", "registry_key", "other_timestamp",
    "rule_id", "rule_title", "rule_level", "attack_id",
}
ARTIFACTS = {"evtx", "prefetch", "shimcache", "amcache", "registry", "mft", "usn", "tasks", "services", "detection"}


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def input_path(root, name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("입력 경로는 manifest 기준 / 구분 상대 경로여야 합니다")
    path = Path(name)
    if path.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")):
        raise ValueError("입력 경로의 절대 경로·상위 경로 참조 금지")
    current = root
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("입력 경로의 심볼릭 링크 금지")
    resolved = current.resolve()
    if root not in resolved.parents:
        raise ValueError("입력 루트 밖의 경로")
    return resolved


def utc_time(value, offset=None):
    if not value:
        return None
    # ISO 날짜+시각만 허용. 정밀도 손실을 숨기지 않도록 6자리 초과는 격리.
    pattern = r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})?"
    if not re.fullmatch(pattern, value):
        raise ValueError("ISO 시각 형식 오류 또는 마이크로초보다 높은 정밀도")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        if not isinstance(offset, str) or not re.fullmatch(r"[+-]\d{2}:\d{2}", offset):
            raise ValueError("시각에 UTC 오프셋이 없고 source의 utc_offset도 없음")
        hours, minutes = map(int, offset[1:].split(":"))
        if hours > 14 or minutes > 59 or (hours == 14 and minutes):
            raise ValueError("UTC 오프셋 범위 오류")
        delta = timedelta(hours=hours, minutes=minutes)
        result = result.replace(tzinfo=timezone(delta if offset[0] == "+" else -delta))
    return result.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize(raw, source, number, digest, case_id):
    if None in raw or any(value is None for value in raw.values()):
        raise ValueError("CSV 열 수 불일치")
    values = {field: raw[column].strip() for field, column in source["columns"].items()}
    if any(len(value) > 16000 for value in values.values()):
        raise ValueError("정규화 필드 16000자 초과")
    timestamp = utc_time(values.get("timestamp", ""), source.get("utc_offset"))
    other = utc_time(values.get("other_timestamp", ""), source.get("utc_offset"))
    if source["artifact"] == "evtx" and not all(values.get(key) for key in ("event_id", "channel", "provider", "record_id")):
        raise ValueError("EVTX 결과에는 event_id/channel/provider/record_id가 필요합니다")
    if values.get("event_id") and not values["event_id"].isdigit():
        raise ValueError("event_id는 숫자 문자열이어야 합니다")
    if values.get("src_ip") and values["src_ip"] != "-":
        address = ipaddress.ip_address(values["src_ip"])
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        values["src_ip"] = str(address)
    else:
        values["src_ip"] = ""
    uid = sha256(json_bytes([case_id, source["id"], digest, number]))[:24]
    return {
        **{key: values.get(key, "") for key in FIELDS if key not in {"timestamp", "other_timestamp"}},
        "uid": uid, "case_id": case_id, "host": source["host"], "artifact": source["artifact"],
        "timestamp_utc": timestamp, "timestamp_original": values.get("timestamp", ""),
        "timestamp_kind": source["timestamp_kind"], "utc_offset_assumption": source.get("utc_offset"),
        "other_timestamp_utc": other, "source_id": source["id"], "source_file": source["path"],
        "source_sha256": digest, "source_record": number,
        "parser": source["parser"], "parser_version": source["parser_version"],
    }


def load_case(manifest_path):
    raw_manifest = manifest_path.read_bytes()
    manifest = json.loads(raw_manifest)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValueError("manifest schema_version은 1이어야 합니다")
    if not isinstance(manifest.get("case_id"), str) or not manifest["case_id"].strip():
        raise ValueError("case_id가 필요합니다")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources는 비어 있지 않은 목록이어야 합니다")
    root = manifest_path.resolve().parent
    seen_ids, seen_paths = set(), set()
    validated = []
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("source 형식 오류")
        for key in ("id", "host", "artifact", "timestamp_kind", "parser", "parser_version", "path"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise ValueError(f"source 필수 필드: {key}")
        if source["artifact"] not in ARTIFACTS:
            raise ValueError("지원하지 않는 artifact 이름")
        columns = source.get("columns")
        if not isinstance(columns, dict) or not columns or not set(columns) <= FIELDS:
            raise ValueError("columns 매핑 필드 오류")
        if any(not isinstance(value, str) or not value for value in columns.values()):
            raise ValueError("columns의 값은 CSV 헤더 이름이어야 합니다")
        path = input_path(root, source["path"])
        if source["id"] in seen_ids or path in seen_paths:
            raise ValueError("source ID 또는 입력 파일 중복: 반복 수집은 별도 사건/버전으로 처리하세요")
        seen_ids.add(source["id"])
        seen_paths.add(path)
        validated.append((source, path))
    events, issues, coverage = [], [], []
    total_rows = 0
    for source, path in validated:
        item = {"source_id": source["id"], "host": source["host"], "artifact": source["artifact"],
                "path": source["path"], "status": "missing", "rows": 0, "accepted": 0, "rejected": 0}
        coverage.append(item)
        if not path.exists():
            continue
        if not path.is_file():
            raise ValueError("입력은 일반 파일이어야 합니다")
        with path.open("rb") as stream:
            content = stream.read(MAX_FILE_BYTES + 1)
        if len(content) > MAX_FILE_BYTES:
            raise ValueError("입력 파일은 25 MiB 이하여야 합니다")
        digest = sha256(content)
        item["sha256"] = digest
        try:
            reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""), strict=True)
            headers = reader.fieldnames
            if not headers or len(headers) != len(set(headers)) or not set(source["columns"].values()) <= set(headers):
                raise ValueError("CSV 헤더 누락·중복 또는 매핑 불일치")
            # 형식이 깨진 파일의 일부만 정상 결과로 게시하지 않는다.
            local_events, local_issues = [], []
            for number, raw in enumerate(reader, 2):
                total_rows += 1
                if total_rows > MAX_TOTAL_ROWS:
                    raise RuntimeError("사건 입력 100000행 제한 초과")
                item["rows"] += 1
                try:
                    local_events.append(normalize(raw, source, number, digest, manifest["case_id"]))
                except (ValueError, OverflowError) as exc:
                    local_issues.append({"source_id": source["id"], "source_sha256": digest,
                                         "source_record": number, "reason": str(exc)})
            item.update(accepted=len(local_events), rejected=len(local_issues),
                        status="partial" if local_issues else ("empty" if not local_events else "processed"))
            events.extend(local_events)
            issues.extend(local_issues)
        except (UnicodeError, csv.Error, ValueError) as exc:
            item.update(status="parse_failed", accepted=0, rejected=item["rows"], reason=str(exc))
            issues.append({"source_id": source["id"], "source_sha256": digest,
                           "source_record": None, "reason": str(exc)})
    events.sort(key=lambda event: (event["timestamp_utc"] is None,
                                  datetime.fromisoformat(event["timestamp_utc"].replace("Z", "+00:00")) if event["timestamp_utc"] else datetime.max.replace(tzinfo=timezone.utc),
                                  event["host"], event["uid"]))
    return manifest, sha256(raw_manifest), events, issues, coverage


def event_matches(event, channel, provider, event_id):
    return event["artifact"] == "evtx" and event["channel"] == channel and event["provider"] == provider and event["event_id"] == event_id


def review_findings(events):
    findings = []

    def add(rule_id, title, priority, matches, explanation, attack_id=None):
        findings.append({"rule_id": rule_id, "rule_version": VERSION, "title": title,
                         "priority": priority, "status": "review", "event_uids": sorted({e["uid"] for e in matches}),
                         "reason": explanation, "attack_id": attack_id,
                         "attack_mapping": "analyst_review_required" if attack_id else "not_assigned"})

    failures, remote_logons = defaultdict(list), defaultdict(list)
    seen_evtx = set()
    for event in events:
        if event["artifact"] == "evtx":
            identity = tuple(event[key] for key in ("host", "channel", "provider", "record_id", "timestamp_utc"))
            if identity in seen_evtx:
                continue  # 원본 레코드는 보존하지만 복제된 EVTX 이벤트를 중복 가산하지 않는다.
            seen_evtx.add(identity)
        path = ntpath.normcase(ntpath.normpath(event["path"])) if event["path"] else ""
        security = lambda number: event_matches(event, "Security", "Microsoft-Windows-Security-Auditing", number)
        if security("4625") and event["timestamp_utc"] and event["user"] and event["src_ip"]:
            failures[(event["host"], event["user"], event["src_ip"])].append(event)
        if security("4624") and event["logon_type"] in {"3", "10"} and event["timestamp_utc"] and event["user"] and event["src_ip"]:
            remote_logons[(event["user"], event["src_ip"])].append(event)
        process_event = event_matches(event, "Microsoft-Windows-Sysmon/Operational", "Microsoft-Windows-Sysmon", "1")
        if process_event and ("\\appdata\\" in path or path.startswith("c:\\windows\\temp\\")):
            add("LAB-PROCESS-01", "사용자 쓰기 가능 경로의 프로세스 생성 검토", 30, [event],
                "경로만으로 악성 실행을 확정하지 않습니다. 부모 프로세스·서명·배포 이력을 확인하세요.")
        if security("4720"):
            add("LAB-ACCOUNT-01", "계정 생성 이벤트 검토", 20, [event],
                "계정 생성 관찰입니다. 계정 생성 요청·담당자·승인 이력과 대조하세요.")
        if security("4698"):
            add("LAB-TASK-01", "예약 작업 생성 이벤트 검토", 20, [event],
                "예약 작업 생성 관찰입니다. 작업 XML·실행 대상·트리거·승인 이력을 함께 확인하세요.")
        if event_matches(event, "System", "Service Control Manager", "7045"):
            add("LAB-SERVICE-01", "서비스 설치 이벤트 검토", 20, [event],
                "서비스 설치 관찰입니다. 설치 프로그램과 서비스 실행 경로·운영 변경 이력을 대조하세요.")
        if event["artifact"] == "registry" and event["registry_key"].lower().rstrip("\\").endswith(("\\currentversion\\run", "\\currentversion\\runonce")):
            add("LAB-AUTORUN-01", "Run/RunOnce 값 검토", 40, [event],
                "등록 관찰이며 실행 시각이 아닙니다. 승인된 시작 프로그램인지 확인하세요.", "T1547.001")
        if event["artifact"] == "mft" and event["timestamp_utc"] and event["other_timestamp_utc"] and event["timestamp_utc"] != event["other_timestamp_utc"]:
            add("LAB-TIME-01", "MFT 타임스탬프 차이 검토", 20, [event],
                "SI/FN 차이만으로 시간 조작을 확정하지 않습니다. 복사·이동·파일시스템 동작을 함께 검토하세요.")
        if event["artifact"] == "detection" and event["rule_id"]:
            add("IMPORTED:" + event["rule_id"], event["rule_title"] or "외부 엔진 매칭 결과", 30, [event],
                "외부 결과 가져오기이며 Sigma를 다시 실행한 결과가 아닙니다. 원본 규칙·엔진 버전을 확인하세요.", event["attack_id"] or None)
    # 시간순 데이터에 슬라이딩 창을 적용한다. 그룹당 첫 일치 창만 보고한다.
    def first_window(group, seconds, minimum, hosts):
        window, host_counts = deque(), Counter()
        for event in group:
            now = datetime.fromisoformat(event["timestamp_utc"].replace("Z", "+00:00"))
            window.append((now, event))
            host_counts[event["host"]] += 1
            while (now - window[0][0]).total_seconds() > seconds:
                _, expired = window.popleft()
                host_counts[expired["host"]] -= 1
                if not host_counts[expired["host"]]:
                    del host_counts[expired["host"]]
            if len(window) >= minimum and len(host_counts) >= hosts:
                return [entry[1] for entry in window]
        return []

    for group in failures.values():
        window = first_window(group, 300, 3, 1)
        if window:
            add("LAB-AUTH-01", "5분 내 반복 로그온 실패 검토", 40, window,
                "동일 호스트·계정·출발 IP 기준입니다. 오입력·서비스 계정 설정 오류도 가능합니다.")
    for group in remote_logons.values():
        window = first_window(group, 600, 2, 2)
        if window:
            add("LAB-HOST-01", "10분 내 여러 호스트의 원격 로그온 검토", 20, window,
                "동일 계정·출발 IP의 시간상 근접성입니다. 내부 이동 경로의 확정이 아니며 NAT·관리 작업·시계 오차를 확인하세요.")
    # 같은 경로를 공유하는 별도 아티팩트는 근거 조회용 연결이다. 점수를 합산하지 않는다.
    path_groups = defaultdict(list)
    for event in events:
        if event["path"]:
            path_groups[(event["host"], ntpath.normcase(ntpath.normpath(event["path"])))].append(event)
    related = [{"host": host, "path": path, "event_uids": sorted(e["uid"] for e in group),
                "artifacts": sorted({e["artifact"] for e in group}), "meaning": "same_path_context_only"}
               for (host, path), group in sorted(path_groups.items()) if len({e["artifact"] for e in group}) >= 2]
    return sorted(findings, key=lambda f: (-f["priority"], f["rule_id"], f["event_uids"])), related


def report_html(report):
    def table(headers, rows):
        return '<div class="scroll"><table><thead><tr>' + ''.join('<th>'+escape(h)+'</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>'+''.join('<td>'+escape(str(cell) if cell is not None else "시각 없음")+'</td>' for cell in row)+'</tr>' for row in rows) + '</tbody></table></div>'
    summary = report["summary"]
    cards = ''.join(f'<div class="card"><span>{escape(label)}</span><strong>{summary[key]}</strong></div>' for label, key in [("정규화 레코드", "events"), ("검토 항목", "findings"), ("입력 문제", "issues"), ("누락 자료", "missing_sources")])
    coverage = table(["호스트", "아티팩트", "처리 상태", "유효 행", "격리 행"], ((s["host"],s["artifact"],s["status"],s["accepted"],s["rejected"]) for s in report["coverage"]))
    findings = table(["우선순위", "규칙", "제목", "근거 UID", "해석"], ((f["priority"],f["rule_id"],f["title"],', '.join(f["event_uids"]),f["reason"]) for f in report["findings"]))
    timeline = table(["UTC", "호스트", "아티팩트 / 시각 의미", "경로·이벤트", "출처 레코드", "UID"], ((e["timestamp_utc"], e["host"], e["artifact"]+' / '+e["timestamp_kind"],e["path"] or e["event_id"],e["source_file"]+':'+str(e["source_record"]),e["uid"]) for e in report["events"][:1000]))
    issues = table(["자료 ID", "레코드", "사유"], ((i["source_id"],i["source_record"],i["reason"]) for i in report["issues"]))
    return f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'"><title>Windows 아티팩트 검토 보고서</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;background:#f3f6fa;color:#203449;margin:0}}main{{max-width:1240px;margin:auto;padding:32px}}header{{background:#112c43;color:white;padding:30px;border-radius:18px}}h1{{margin:6px 0;font-size:30px}}h2{{margin-top:32px}}.cards{{display:flex;gap:16px;flex-wrap:wrap;margin:24px 0}}.card{{background:white;border:1px solid #dbe4ed;border-radius:12px;padding:16px 24px;flex:1;min-width:130px}}strong{{display:block;font-size:30px;color:#1f6d84}}.scroll{{overflow:auto;background:white;border-radius:12px;border:1px solid #dbe4ed}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #e2e8ef;vertical-align:top;min-width:100px;overflow-wrap:anywhere}}th{{background:#e8f0f7}}td{{max-width:360px}}.note{{border-left:4px solid #c28a25;padding:12px 16px;background:#fff4db}}footer{{margin-top:28px;color:#53697b}}</style>
<main><header><div>DFIR · OFFLINE TRIAGE</div><h1>Windows 아티팩트 통합 검토</h1><div>사건: {escape(report['case_id'])} · 처리 상태: {escape(report['processing_status'])}</div></header>{cards}<p class="note">검토 우선순위는 침해 확률이 아닙니다. 누락·파싱 실패는 탐지 0건과 구분합니다. 시각 없는 레코드는 마지막에 표시합니다.</p><h2>수집·처리 범위</h2>{coverage}<h2>검토 항목과 근거</h2>{findings}<h2>통합 타임라인</h2><p>시간 정렬은 인과관계를 확정하지 않습니다. HTML은 최대 1,000건을 표시하며 전체 결과는 report.json과 normalized.jsonl에 있습니다.</p>{timeline}<h2>입력 오류</h2>{issues}<footer>규칙 버전 {VERSION} · 원본 파일 해시와 레코드 위치는 JSON에 보존 · 외부 전송 없음</footer></main></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        manifest_path = args.manifest.resolve()
        output = args.output.resolve()
        if output == manifest_path.parent or manifest_path.parent in output.parents:
            raise ValueError("출력은 입력 자료 루트 밖의 새 폴더를 사용하세요")
        if output.exists():
            raise ValueError("출력 폴더가 이미 존재합니다. 새 경로를 지정하세요")
        manifest, manifest_hash, events, issues, coverage = load_case(manifest_path)
        findings, related = review_findings(events)
        partial = bool(issues) or any(s["status"] in {"missing", "parse_failed", "partial"} for s in coverage)
        report = {"case_id": manifest["case_id"], "pipeline_version": VERSION,
                  "manifest_sha256": manifest_hash, "processing_status": "partial" if partial else "complete",
                  "summary": {"events": len(events), "findings": len(findings), "issues": len(issues),
                              "undated": sum(e["timestamp_utc"] is None for e in events),
                              "missing_sources": sum(s["status"] == "missing" for s in coverage)},
                  "events": events, "issues": issues, "coverage": coverage, "findings": findings, "related_paths": related}
        output.mkdir(parents=True, exist_ok=False)
        (output / "report.json").write_bytes(json_bytes(report))
        (output / "normalized.jsonl").write_text(''.join(json.dumps(e, ensure_ascii=False, sort_keys=True)+'\n' for e in events), encoding="utf-8")
        (output / "report.html").write_text(report_html(report), encoding="utf-8")
        # 워커는 마지막 마커로 결과 저장 완료 여부를 확인한다.
        (output / "complete.json").write_bytes(json_bytes({"processing_status": report["processing_status"],
                                                         "report_sha256": sha256((output / "report.json").read_bytes())}))
        print(json.dumps(report["summary"], ensure_ascii=False))
        print(f"처리 상태: {report['processing_status']} / {output}")
        return 2 if partial else 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"파이프라인 실패: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
