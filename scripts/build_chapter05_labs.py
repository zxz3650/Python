"""05장 fixture와 Jupyter Notebook을 결정론적으로 생성한다.

실행 위치와 관계없이 저장소 루트를 기준으로 파일을 만든다.
학습자용 Notebook은 TODO가 남아 있어도 전체 실행이 중단되지 않고,
`notebooks/solutions`의 참고 구현은 검증식을 통과하도록 구성한다.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "fixtures" / "05-text-processing"
NOTEBOOK_DIR = ROOT / "notebooks"
SOLUTION_DIR = NOTEBOOK_DIR / "solutions"


def markdown(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.strip() + "\n",
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.strip() + "\n",
    }


def notebook(cells: list[dict]) -> dict:
    for index, cell in enumerate(cells):
        cell["id"] = f"cell-{index:03d}"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.12",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def write_notebook(path: Path, cells: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(notebook(cells), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )


COMMON_SETUP = r'''
from pathlib import Path
import sys


def find_project_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "requirements.txt").is_file():
            return candidate
    raise FileNotFoundError("requirements.txt가 있는 저장소 루트에서 JupyterLab을 실행하세요.")


ROOT = find_project_root()
FIXTURE_DIR = ROOT / "fixtures" / "05-text-processing"

assert sys.version_info >= (3, 10)
assert FIXTURE_DIR.is_dir()

print("Python:", sys.version.split()[0])
print("실습 데이터:", FIXTURE_DIR)
'''


def learner_cells(
    title: str,
    goal: str,
    fixture_name: str,
    preview_code: str,
    task: str,
    todo_code: str,
    check_code: str,
    next_steps: str,
) -> list[dict]:
    return [
        markdown(f"# {title}\n\n## Goal\n\n{goal}"),
        markdown(
            "## Setup\n\n"
            f"`fixtures/05-text-processing/{fixture_name}`를 읽는다. "
            "저장소 루트에서 JupyterLab을 실행한다."
        ),
        code(COMMON_SETUP + "\n" + preview_code),
        markdown(f"## Steps\n\n{task}"),
        code(todo_code),
        markdown(
            "## Checks\n\n"
            "TODO를 구현한 뒤 `TODO_DONE = True`로 바꾸고 공개 경계 검증을 실행한다. "
            "검증이 통과해도 다른 입력이 모두 올바르다는 보장은 아니다."
        ),
        code(check_code),
        markdown(f"## Next Steps\n\n{next_steps}"),
    ]


def solution_cells(
    title: str,
    goal: str,
    setup_code: str,
    solution_code: str,
    check_code: str,
    takeaway: str,
) -> list[dict]:
    return [
        markdown(
            f"# {title} — 풀이 검증\n\n## Goal\n\n{goal}\n\n"
            "> 학습자용 TODO를 먼저 완성한 뒤 참고한다."
        ),
        markdown("## Setup\n\nfixture와 실행 환경을 확인한다."),
        code(COMMON_SETUP + "\n" + setup_code),
        markdown("## Steps\n\n참고 구현을 실행한다."),
        code(solution_code),
        markdown("## Checks\n\n경계값과 fixture 결과를 대조한다."),
        code(check_code),
        markdown(f"## Next Steps\n\n{takeaway}"),
    ]


def write_text_fixtures() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = {
        "normalization-cases.txt": (
            "name|  Alice  \n"
            "name|  e\u0301lodie  \n"
            "email|  STUDENT01@EXAMPLE.COM  \n"
            "description|  indentation must remain  \n"
            "path|/Admin/Reports  \n"
        ),
        "delimited-events.txt": (
            "2026-08-14 | INFO | login completed\n"
            "2026-08-14 | WARNING | token=training-token&action=retry\n"
            "2026-08-15 | ERROR | message contains | delimiter\n"
            "broken | only-two-fields\n"
        ),
        "regex-cases.txt": (
            "identifier|AB-2026|valid\n"
            "identifier|X-20|invalid\n"
            "identifier|AB-２０２６|invalid\n"
            "filename|report.csv|valid\n"
            "filename|archive.csv.exe|invalid\n"
            "number|ticket 125 completed|125\n"
        ),
        "event-lines.txt": (
            "2026-08-14 INFO completed\n"
            "2026-08-14 WARNING retry scheduled\n"
            "2026-08-15 ERROR authentication failed\n"
            "not-an-event\n"
        ),
        "validation-records.jsonl": (
            '{"account":"alice_01","ip":"203.0.113.10","result":"success","risk_score":12,"target":"/login?token=training"}\n'
            '{"account":"  ","ip":"999.10.20.30","result":"MAYBE","risk_score":true,"target":"/admin/%2e%2e/settings?token=secret"}\n'
            '{"account":"blue-team","ip":"2001:0db8:0000::10","result":"LOCKED","risk_score":85,"target":"/admin"}\n'
            '{"account":"carol","ip":"192.0.2.44","result":"failure","risk_score":101,"target":"/%252e%252e/admin"}\n'
            '{"account":"broken"\n'
        ),
        "timestamp-events.jsonl": (
            '{"event":"login","timestamp":"2026-08-14T10:30:00+09:00"}\n'
            '{"event":"api","timestamp":"2026-08-14T01:45:00Z"}\n'
            '{"event":"naive","timestamp":"2026-08-14T03:00:00"}\n'
            '{"event":"invalid","timestamp":"2026-02-30T10:00:00+09:00"}\n'
        ),
        "measurements.csv": (
            "sample_id,value\n"
            "1,10.5\n"
            "2,12.0\n"
            "3,\n"
            "4,85.0\n"
            "5,invalid\n"
            "6,14.5\n"
        ),
        "items.csv": (
            "name,category,price,quantity\n"
            "Keyboard,input,50000,2\n"
            "Mouse,input,30000,3\n"
            "Monitor,display,240000,1\n"
            "Cable,accessory,invalid,5\n"
            "Adapter,accessory,15000,\n"
            "=TrainingFormula,input,1000,1\n"
        ),
    }

    for name, content in fixtures.items():
        (FIXTURE_DIR / name).write_text(content, encoding="utf-8", newline="")

    large_items = ["name,category,price,quantity"]
    for index in range(1, 201):
        category = ("input", "display", "accessory")[index % 3]
        price = "invalid" if index in {57, 144} else str(1000 + index * 25)
        quantity = "" if index in {88, 177} else str(index % 7 + 1)
        large_items.append(f"item-{index:03d},{category},{price},{quantity}")
    (FIXTURE_DIR / "large_items.csv").write_text(
        "\n".join(large_items) + "\n",
        encoding="utf-8",
        newline="",
    )


def combined_line(
    ip: str,
    timestamp: datetime,
    target: str,
    status: int,
    response_bytes: int | None = 512,
    user_agent: str = "TrainingBrowser/1.0",
) -> str:
    bytes_text = "-" if response_bytes is None else str(response_bytes)
    time_text = timestamp.strftime("%d/%b/%Y:%H:%M:%S %z")
    return (
        f'{ip} - - [{time_text}] "GET {target} HTTP/1.1" '
        f'{status} {bytes_text} "-" "{user_agent}"'
    )


def write_web_log_fixtures() -> None:
    start = datetime(2026, 8, 14, 1, 0, tzinfo=timezone.utc)
    lines: list[str] = []

    # 일반 사용자: 소량의 404만 포함한다.
    for index in range(18):
        path = "/missing-link" if index == 7 else ("/", "/login", "/products")[index % 3]
        status = 404 if index == 7 else 200
        lines.append(
            combined_line(
                "192.0.2.10",
                start + timedelta(seconds=index * 12),
                path,
                status,
                response_bytes=None if index == 3 else 512,
            )
        )

    # NAT 다수 요청 + 같은 favicon 404 반복: 고유 경로가 1개이므로 스캔 후보가 아니어야 한다.
    for index in range(40):
        path = "/favicon.ico" if index < 9 else "/api/items"
        status = 404 if index < 9 else 200
        lines.append(combined_line("192.0.2.20", start + timedelta(seconds=index * 6), path, status))

    # 5분 내 다수의 고유 404 경로: 교육용 스캔 신호.
    for index in range(10):
        lines.append(
            combined_line(
                "198.51.100.40",
                start + timedelta(seconds=index * 10),
                f"/unknown-{index}",
                404 if index < 9 else 200,
                user_agent="TrainingScanner/1.0",
            )
        )

    # 민감 경로에 대한 2xx 1건은 높은 우선순위 신호로 남긴다.
    lines.append(combined_line("203.0.113.50", start + timedelta(minutes=1), "/.env?token=do-not-store", 200))

    # 승인된 스캐너도 신호는 보존하고 허용된 문맥만 표시한다.
    for index in range(9):
        lines.append(
            combined_line(
                "198.51.100.77",
                start + timedelta(minutes=2, seconds=index * 8),
                f"/audit-{index}",
                404,
                user_agent="ApprovedTrainingScanner/1.0",
            )
        )

    # IPv6와 경로 정규화 경계 사례.
    lines.append(combined_line("2001:db8::10", start + timedelta(minutes=6), "/docs/../login", 200))
    lines.append(combined_line("2001:db8::10", start + timedelta(minutes=6, seconds=10), "/A//B/%2e%2e/C", 404))

    # 형식·의미 검증 오류다. 인코딩 오류는 별도 바이너리 테스트 데이터에 둔다.
    lines.append('999.1.1.1 - - [14/Aug/2026:01:07:00 +0000] "GET / HTTP/1.1" 200 10 "-" "TrainingBrowser/1.0"')
    lines.append('192.0.2.30 - - [14/Aug/2026:01:07:10 +0000] "GET / HTTP/1.1" 999 10 "-" "TrainingBrowser/1.0"')
    lines.append('192.0.2.30 - - [32/Aug/2026:01:07:20 +0000] "GET / HTTP/1.1" 200 10 "-" "TrainingBrowser/1.0"')
    lines.append("not a combined log record")

    # CRLF와 LF를 모두 포함해 줄 종료 처리를 검증한다.
    encoded = bytearray()
    for index, line in enumerate(lines):
        encoded.extend(line.encode("utf-8"))
        encoded.extend(b"\r\n" if index % 4 == 0 else b"\n")
    (FIXTURE_DIR / "web-access.log").write_bytes(bytes(encoded))

    invalid_lines = [
        combined_line("192.0.2.90", start, "/", 200).encode("utf-8") + b"\n",
        b'192.0.2.91 - - [14/Aug/2026:01:00:01 +0000] "GET / HTTP/1.1" 200 10 "-" "bad-\xff-agent"\n',
        combined_line("192.0.2.92", start + timedelta(seconds=2), "/health", 200).encode("utf-8") + b"\r\n",
    ]
    (FIXTURE_DIR / "web-access-invalid-utf8.log").write_bytes(b"".join(invalid_lines))


def build_basic_notebooks() -> None:
    write_notebook(
        NOTEBOOK_DIR / "05-1-normalization.ipynb",
        learner_cells(
            "05-1. 문자열 정규화",
            "필드 의미에 맞게 정규화하되 원문을 보존한다.",
            "normalization-cases.txt",
            r'''
fixture_path = FIXTURE_DIR / "normalization-cases.txt"
cases = [line.split("|", maxsplit=1) for line in fixture_path.read_text(encoding="utf-8").splitlines()]
cases[:3]
''',
            "`normalize_value(kind, raw)`를 완성한다. 이름은 NFC 표시값의 대소문자를 보존하고 별도 `comparison_key`에만 `casefold()`를 적용한다. 이메일은 양끝 공백과 대소문자, 설명은 줄바꿈만 처리한다.",
            r'''
import unicodedata

TODO_DONE = False


def normalize_value(kind: str, raw: str) -> dict:
    # 실습 과제: raw를 보존하고 normalized 값을 생성한다.
    raise NotImplementedError
''',
            r'''
if not TODO_DONE:
    print("TODO를 구현한 뒤 TODO_DONE을 True로 바꾸세요.")
else:
    assert normalize_value("email", "  A@EXAMPLE.COM  ")["normalized"] == "a@example.com"
    assert normalize_value("path", "/Admin")["normalized"] == "/Admin"
    assert normalize_value("name", "  E\u0301lodie  ")["normalized"] == "Élodie"
    assert normalize_value("name", "  E\u0301lodie  ")["comparison_key"] == "élodie"

    fixture_results = [normalize_value(kind, raw) for kind, raw in cases]
    assert len(fixture_results) == 5
    assert [result["normalized"] for result in fixture_results] == [
        "Alice",
        "élodie",
        "student01@example.com",
        "  indentation must remain  ",
        "/Admin/Reports  ",
    ]
    assert all(
        result["raw"] == raw
        for result, (_, raw) in zip(fixture_results, cases)
    )
    assert [result["comparison_key"] for result in fixture_results[:2]] == [
        "alice",
        "élodie",
    ]
    print("공개 경계 검증 통과: fixture 정상 5건 / 오류 0건")
''',
            "풀이 검증용 Notebook에서 원문과 파생 값의 차이를 비교한다.",
        ),
    )

    write_notebook(
        NOTEBOOK_DIR / "05-2-split-search-replace.ipynb",
        learner_cells(
            "05-2. 분리·검색·치환",
            "고정 구분자 형식을 필요한 횟수만 나누고 오류 행을 보존한다.",
            "delimited-events.txt",
            r'''
fixture_path = FIXTURE_DIR / "delimited-events.txt"
lines = fixture_path.read_text(encoding="utf-8").splitlines()
lines
''',
            "`parse_event(line)`를 `split(..., maxsplit=2)`로 구현하고 필드 수를 검증한다.",
            r'''
TODO_DONE = False


def parse_event(line: str) -> dict:
    # 실습 과제: date, level, message, raw를 반환한다.
    raise NotImplementedError
''',
            r'''
if not TODO_DONE:
    print("TODO를 구현한 뒤 TODO_DONE을 True로 바꾸세요.")
else:
    parsed = parse_event("2026-08-14 | INFO | a | b")
    assert parsed["message"] == "a | b"
    try:
        parse_event("only | two")
    except ValueError:
        pass
    else:
        raise AssertionError("필드 수 오류를 허용했습니다.")

    fixture_parsed, fixture_errors = [], []
    for line_number, line in enumerate(lines, start=1):
        try:
            fixture_parsed.append(parse_event(line))
        except ValueError as error:
            fixture_errors.append({
                "line": line_number,
                "raw": line,
                "error": error,
            })
    assert len(fixture_parsed) == 3 and len(fixture_errors) == 1
    assert [record["raw"] for record in fixture_parsed] == lines[:3]
    assert fixture_parsed[2]["message"] == "message contains | delimiter"
    assert fixture_errors[0]["line"] == 4
    assert fixture_errors[0]["raw"] == lines[3]
    print("공개 경계 검증 통과: fixture 정상 3건 / 오류 1건")
''',
            "오류 행은 행 번호·원문·오류 코드로 구조화한다.",
        ),
    )

    write_notebook(
        NOTEBOOK_DIR / "05-3-regex-basics.ipynb",
        learner_cells(
            "05-3. 정규표현식 기초",
            "검색과 전체 입력 검증을 구분하고 실패 사례를 함께 확인한다.",
            "regex-cases.txt",
            r'''
fixture_path = FIXTURE_DIR / "regex-cases.txt"
cases = [line.split("|", maxsplit=2) for line in fixture_path.read_text(encoding="utf-8").splitlines()]
cases
''',
            "식별자·파일명 검증 패턴과 문장 내 숫자 검색 패턴을 작성한다.",
            r'''
import re

TODO_DONE = False
IDENTIFIER = re.compile(r"TODO")
FILENAME = re.compile(r"TODO")
NUMBER = re.compile(r"TODO")
''',
            r'''
if not TODO_DONE:
    print("세 패턴을 구현한 뒤 TODO_DONE을 True로 바꾸세요.")
else:
    assert IDENTIFIER.fullmatch("AB-2026")
    assert not IDENTIFIER.fullmatch("X-20")
    assert not IDENTIFIER.fullmatch("AB-２０２６")
    assert FILENAME.fullmatch("report.csv")
    assert not FILENAME.fullmatch("report.csv.exe")
    assert NUMBER.search("ticket 125 completed").group() == "125"

    fixture_results = []
    for kind, text, expected in cases:
        if kind == "identifier":
            actual = "valid" if IDENTIFIER.fullmatch(text) else "invalid"
        elif kind == "filename":
            actual = "valid" if FILENAME.fullmatch(text) else "invalid"
        elif kind == "number":
            match = NUMBER.search(text)
            actual = match.group() if match else ""
        else:
            raise AssertionError(f"알 수 없는 fixture 종류: {kind}")
        fixture_results.append((kind, text, actual))
        assert actual == expected
    assert len(fixture_results) == 6
    assert sum(actual == "valid" for _, _, actual in fixture_results) == 2
    assert sum(actual == "invalid" for _, _, actual in fixture_results) == 3
    print("공개 경계 검증 통과: fixture 6건")
''',
            "패턴을 넓게 만드는 대신 정상·경계·실패 입력을 먼저 정의한다.",
        ),
    )

    write_notebook(
        NOTEBOOK_DIR / "05-4-groups-capture.ipynb",
        learner_cells(
            "05-4. 그룹과 캡처",
            "이름 있는 그룹으로 날짜·수준·메시지를 추출한다.",
            "event-lines.txt",
            r'''
fixture_path = FIXTURE_DIR / "event-lines.txt"
lines = fixture_path.read_text(encoding="utf-8").splitlines()
lines
''',
            "`EVENT_PATTERN`과 `parse_event(line)`를 완성한다. 전체 일치와 이름 있는 그룹을 사용한다.",
            r'''
import re

TODO_DONE = False
EVENT_PATTERN = re.compile(r"TODO")


def parse_event(line: str) -> dict:
    raise NotImplementedError
''',
            r'''
if not TODO_DONE:
    print("TODO를 구현한 뒤 TODO_DONE을 True로 바꾸세요.")
else:
    result = parse_event("2026-08-14 INFO completed now")
    assert result == {"date": "2026-08-14", "level": "INFO", "message": "completed now"}
    try:
        parse_event("broken")
    except ValueError:
        pass
    else:
        raise AssertionError("형식 오류를 허용했습니다.")

    fixture_parsed, fixture_errors = [], []
    for line_number, line in enumerate(lines, start=1):
        try:
            fixture_parsed.append(parse_event(line))
        except ValueError as error:
            fixture_errors.append({
                "line": line_number,
                "raw": line,
                "error": error,
            })
    assert len(fixture_parsed) == 3 and len(fixture_errors) == 1
    assert fixture_parsed[0] == {
        "date": "2026-08-14",
        "level": "INFO",
        "message": "completed",
    }
    assert fixture_parsed[2]["message"] == "authentication failed"
    assert fixture_errors[0]["line"] == 4
    assert fixture_errors[0]["raw"] == "not-an-event"
    print("공개 경계 검증 통과: fixture 정상 3건 / 오류 1건")
''',
            "캡처 순서가 바뀌어도 의미가 유지되도록 그룹 이름을 사용한다.",
        ),
    )

    write_notebook(
        NOTEBOOK_DIR / "05-5-validation.ipynb",
        learner_cells(
            "05-5. 데이터 검증",
            "필수값·형식·허용값·범위 오류를 구조화한다.",
            "validation-records.jsonl",
            r'''
import json

fixture_path = FIXTURE_DIR / "validation-records.jsonl"
raw_lines = fixture_path.read_text(encoding="utf-8").splitlines()
print("전체 JSONL 행:", len(raw_lines))
for line in raw_lines[:2]:
    try:
        print("키:", sorted(json.loads(line)))
    except json.JSONDecodeError:
        print("JSON 문법 오류")
''',
            "JSON 문법 오류와 레코드 검증 오류를 나눈다. `validate_record(record)`는 계정·IPv4/IPv6·인증 결과·위험 점수·요청 경로를 검증하고 `(cleaned, errors)`를 반환한다.",
            r'''
TODO_DONE = False


def validate_record(record: dict) -> tuple[dict, list[dict]]:
    # 실습 과제: 원본 record를 변경하지 않는다.
    raise NotImplementedError
''',
            r'''
if not TODO_DONE:
    print("TODO를 구현한 뒤 TODO_DONE을 True로 바꾸세요.")
else:
    original = {
        "account": " alice_01 ",
        "ip": "2001:0db8:0000::10",
        "result": "success",
        "risk_score": 12,
        "target": "/login?token=do-not-copy",
    }
    before = original.copy()
    cleaned, errors = validate_record(original)
    assert not errors
    assert cleaned["ip"] == "2001:db8::10"
    assert cleaned["result"] == "SUCCESS"
    assert cleaned["target"] == "/login"
    assert original == before
    _, errors = validate_record({})
    assert {error["field"] for error in errors} >= {
        "account", "ip", "result", "risk_score", "target"
    }
    _, errors = validate_record({**original, "risk_score": True})
    assert any(error["field"] == "risk_score" for error in errors)

    fixture_valid, fixture_validation_errors, fixture_json_errors = [], [], []
    for line_number, line in enumerate(raw_lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            fixture_json_errors.append({"line": line_number, "error": error})
            continue

        before = record.copy()
        cleaned, record_errors = validate_record(record)
        assert record == before
        if record_errors:
            fixture_validation_errors.append({
                "line": line_number,
                "errors": record_errors,
            })
        else:
            fixture_valid.append(cleaned)

    assert len(fixture_valid) == 2
    assert len(fixture_validation_errors) == 2
    assert len(fixture_json_errors) == 1
    assert len(raw_lines) == 5
    assert fixture_valid[0]["target"] == "/login"
    assert fixture_valid[1]["ip"] == "2001:db8::10"
    assert [item["line"] for item in fixture_validation_errors] == [2, 4]
    assert fixture_json_errors[0]["line"] == 5
    print("공개 경계 검증 통과: fixture 정상 2건 / 검증 오류 2건 / JSON 오류 1건")
''',
            "파싱 오류와 의미 검증 오류를 서로 다른 코드로 기록한다.",
        ),
    )

    write_notebook(
        NOTEBOOK_DIR / "05-6-datetime.ipynb",
        learner_cells(
            "05-6. 날짜와 시간",
            "시간대가 있는 ISO 8601 값을 UTC로 통일하고 오류 행을 나눈다.",
            "timestamp-events.jsonl",
            r'''
import json

fixture_path = FIXTURE_DIR / "timestamp-events.jsonl"
records = [json.loads(line) for line in fixture_path.read_text(encoding="utf-8").splitlines()]
records
''',
            "`parse_utc(value)`를 완성한다. `Z`를 처리하고 naive datetime은 거부한다.",
            r'''
from datetime import datetime, timezone

TODO_DONE = False


def parse_utc(value: str) -> datetime:
    raise NotImplementedError
''',
            r'''
if not TODO_DONE:
    print("TODO를 구현한 뒤 TODO_DONE을 True로 바꾸세요.")
else:
    assert parse_utc("2026-08-14T10:30:00+09:00").isoformat() == "2026-08-14T01:30:00+00:00"
    assert parse_utc("2026-08-14T01:30:00Z").tzinfo == timezone.utc
    try:
        parse_utc("2026-08-14T01:30:00")
    except ValueError:
        pass
    else:
        raise AssertionError("naive datetime을 허용했습니다.")
    for invalid in ("", "   ", 123):
        try:
            parse_utc(invalid)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError("타입·빈 값 경계를 허용했습니다.")

    fixture_valid, fixture_errors = [], []
    for record in records:
        try:
            fixture_valid.append({
                **record,
                "timestamp_utc": parse_utc(record["timestamp"]),
            })
        except (KeyError, TypeError, ValueError) as error:
            fixture_errors.append({
                "event": record.get("event"),
                "error": error,
            })
    assert len(fixture_valid) == 2 and len(fixture_errors) == 2
    assert all(item["timestamp_utc"].tzinfo == timezone.utc for item in fixture_valid)
    assert [
        item["event"]
        for item in sorted(fixture_valid, key=lambda item: item["timestamp_utc"])
    ] == ["login", "api"]
    assert {item["event"] for item in fixture_errors} == {"naive", "invalid"}
    print("공개 경계 검증 통과: fixture 정상 2건 / 오류 2건")
''',
            "저장·비교용 UTC 값과 표시용 로컬 시간을 나눈다.",
        ),
    )

    write_notebook(
        NOTEBOOK_DIR / "05-7-numpy-array.ipynb",
        learner_cells(
            "05-7. NumPy 배열",
            "결측값 마스크와 다중 조건 마스크를 배열 연산으로 만든다.",
            "measurements.csv",
            r'''
import numpy as np

fixture_path = FIXTURE_DIR / "measurements.csv"
values = np.genfromtxt(fixture_path, delimiter=",", skip_header=1, usecols=1, dtype=float)
print(values)
''',
            "`valid_mask`, 유효값 평균, `high_mask`를 계산한다. 이어서 05-9 축소 특징에 `np.divide(..., where=...)`와 `np.select()`를 적용한다. 원본을 변경하지 않는다.",
            r'''
TODO_DONE = False
valid_mask = None
valid_mean = None
high_mask = None
not_found_rate = None
candidate = None
reason = None

# 실습 과제 1: np.isfinite()과 배열 비교를 사용한다.
# 실습 과제 2: 아래 축소 특징에 대해 05-9 규칙을 벡터 연산으로 계산한다.
total_requests = np.array([10, 40, 5, 0], dtype=np.int64)
not_found_404 = np.array([9, 9, 0, 0], dtype=np.int64)
unique_404_paths = np.array([9, 1, 0, 0], dtype=np.int64)
sensitive_requests = np.array([0, 0, 1, 0], dtype=np.int64)
unique_sensitive_paths = np.array([0, 0, 1, 0], dtype=np.int64)
sensitive_2xx = np.array([0, 0, 1, 0], dtype=np.int64)
''',
            r'''
if not TODO_DONE:
    print("TODO를 구현한 뒤 TODO_DONE을 True로 바꾸세요.")
else:
    assert valid_mask.dtype == np.bool_
    assert int(valid_mask.sum()) == 4
    assert np.isclose(valid_mean, 30.5)
    assert values[high_mask].tolist() == [85.0]
    assert np.allclose(not_found_rate, [0.9, 0.225, 0.0, 0.0])
    assert candidate.tolist() == [True, False, True, False]
    assert reason.tolist() == ["scan", "-", "sensitive", "-"]
    print("공개 경계 검증 통과")
''',
            "05-9에서 여러 탐지 조건을 bool 배열로 결합한다.",
        ),
    )

    write_notebook(
        NOTEBOOK_DIR / "05-8-pandas-dataframe.ipynb",
        learner_cells(
            "05-8. pandas와 DataFrame",
            "결측·변환·도메인 오류 행을 보존하고 카테고리별 건수·합계를 집계한다.",
            "items.csv",
            r'''
import numpy as np
import pandas as pd

fixture_path = FIXTURE_DIR / "items.csv"
frame = pd.read_csv(
    fixture_path,
    dtype={
        "name": "string",
        "category": "string",
        "price": "string",
        "quantity": "string",
    },
    encoding="utf-8",
    encoding_errors="strict",
    keep_default_na=False,
    na_values=[""],
)
frame
''',
            "`price`와 `quantity`를 변환한 뒤 유한성·음수·정수 수량 규칙을 검증하고 `valid_rows`, `error_rows`, `summary`를 만든다.",
            r'''
TODO_DONE = False
valid_rows = None
error_rows = None
summary = None
# 실습 과제 1: pd.to_numeric(errors="coerce")로 변환 오류를 표시한다.
# 실습 과제 2: np.isfinite(), 음수, 소수 수량을 검증하고 오류 이유를 보존한다.
# 실습 과제 3: 유효 행만 카테고리별로 집계한다.
''',
            r'''
if not TODO_DONE:
    print("TODO를 구현한 뒤 TODO_DONE을 True로 바꾸세요.")
else:
    assert len(valid_rows) == 4
    assert len(error_rows) == 2
    assert {"item_count", "total_amount"} <= set(summary.columns)
    assert int(summary["item_count"].sum()) == 4
    print("공개 경계 검증 통과")
''',
            "`large_items.csv`를 `chunksize`로 읽어 전체 실행 결과와 대조한다.",
        ),
    )


def build_solution_notebooks() -> None:
    write_notebook(
        SOLUTION_DIR / "05-1-normalization-solution.ipynb",
        solution_cells(
            "05-1. 문자열 정규화",
            "필드별 정규화 정책과 원문 보존을 검증한다.",
            r'''
import unicodedata
fixture_path = FIXTURE_DIR / "normalization-cases.txt"
cases = [line.split("|", maxsplit=1) for line in fixture_path.read_text(encoding="utf-8").splitlines()]
''',
            r'''
def normalize_value(kind: str, raw: str) -> dict:
    if kind == "name":
        normalized = unicodedata.normalize("NFC", raw.strip())
        comparison_key = normalized.casefold()
    elif kind == "email":
        normalized = raw.strip().lower()
        comparison_key = normalized
    elif kind == "description":
        normalized = raw.removesuffix("\n").removesuffix("\r")
        comparison_key = normalized
    else:
        normalized = raw.removesuffix("\n").removesuffix("\r")
        comparison_key = normalized
    return {
        "kind": kind,
        "raw": raw,
        "normalized": normalized,
        "comparison_key": comparison_key,
    }


results = [normalize_value(kind, raw) for kind, raw in cases]
results
''',
            r'''
assert normalize_value("email", "  A@EXAMPLE.COM  ")["normalized"] == "a@example.com"
assert normalize_value("path", "/Admin")["normalized"] == "/Admin"
assert normalize_value("name", "  E\u0301lodie  ")["normalized"] == "Élodie"
assert normalize_value("name", "  E\u0301lodie  ")["comparison_key"] == "élodie"
assert all(result["raw"] == raw for result, (_, raw) in zip(results, cases))
print("검증 통과:", len(results), "건")
''',
            "정규화 규칙은 데이터 필드의 의미와 일치해야 한다.",
        ),
    )

    write_notebook(
        SOLUTION_DIR / "05-2-split-search-replace-solution.ipynb",
        solution_cells(
            "05-2. 분리·검색·치환",
            "구분자 수와 메시지 내 구분자 경계를 검증한다.",
            r'''
fixture_path = FIXTURE_DIR / "delimited-events.txt"
lines = fixture_path.read_text(encoding="utf-8").splitlines()
''',
            r'''
SENSITIVE_KEYS = {"password", "token", "secret"}


class EventParseError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def parse_event(line: str) -> dict:
    parts = line.split("|", maxsplit=2)
    if len(parts) != 3:
        raise EventParseError("FIELD_COUNT", "필드는 세 개여야 한다.")
    date, level, message = (part.strip() for part in parts)
    if not all((date, level, message)):
        raise EventParseError("EMPTY_FIELD", "빈 필드를 허용하지 않는다.")
    return {"date": date, "level": level, "message": message, "raw": line}


def mask_pairs(text: str) -> str:
    masked_parts = []
    for part in text.split("&"):
        key, separator, value = part.partition("=")
        if separator and key.casefold() in SENSITIVE_KEYS:
            value = "***"
        masked_parts.append(key + separator + value)
    return "&".join(masked_parts)


parsed, errors = [], []
for line_number, line in enumerate(lines, start=1):
    try:
        parsed.append(parse_event(line))
    except EventParseError as exc:
        errors.append({
            "line": line_number,
            "raw": line,
            "code": exc.code,
            "message": str(exc),
        })

masked_messages = [mask_pairs(record["message"]) for record in parsed]
print("정상:", len(parsed), "오류:", len(errors))
print("보고서용 메시지:", masked_messages)
''',
            r'''
assert parse_event("2026-08-14 | INFO | a | b")["message"] == "a | b"
assert len(parsed) == 3 and len(errors) == 1
assert errors[0]["line"] == 4 and errors[0]["code"] == "FIELD_COUNT"
assert errors[0]["raw"] == lines[3]
try:
    parse_event("2026-08-14 | | empty")
except EventParseError as exc:
    assert exc.code == "EMPTY_FIELD"
else:
    raise AssertionError("빈 필드를 허용했다.")
assert all("training-token" not in message for message in masked_messages)
print("검증 통과")
''',
            "오류 원문의 저장 여부는 민감정보 정책과 재처리 필요성을 함께 고려한다.",
        ),
    )

    write_notebook(
        SOLUTION_DIR / "05-3-regex-basics-solution.ipynb",
        solution_cells(
            "05-3. 정규표현식 기초",
            "검색과 전체 일치의 함수 선택을 검증한다.",
            r'''
import re
fixture_path = FIXTURE_DIR / "regex-cases.txt"
cases = [line.split("|", maxsplit=2) for line in fixture_path.read_text(encoding="utf-8").splitlines()]
''',
            r'''
IDENTIFIER = re.compile(r"[A-Z]{2}-[0-9]{4}")
FILENAME = re.compile(r"[A-Za-z0-9_-]+\.(?:txt|csv)")
NUMBER = re.compile(r"[0-9]{3,}")

results = {
    "identifier_valid": bool(IDENTIFIER.fullmatch("AB-2026")),
    "filename_valid": bool(FILENAME.fullmatch("report.csv")),
    "number": NUMBER.search("ticket 125 completed").group(),
}
results
''',
            r'''
assert results == {"identifier_valid": True, "filename_valid": True, "number": "125"}
assert not IDENTIFIER.fullmatch("X-20")
assert not IDENTIFIER.fullmatch("AB-２０２６")
assert not FILENAME.fullmatch("report.csv.exe")
assert NUMBER.search("value 12") is None
assert NUMBER.search("전각 숫자 １２５") is None
print("검증 통과")
''',
            "정규표현식은 형태를 확인하며 연도·범위 같은 의미는 별도 로직으로 검증한다.",
        ),
    )

    write_notebook(
        SOLUTION_DIR / "05-4-groups-capture-solution.ipynb",
        solution_cells(
            "05-4. 그룹과 캡처",
            "이름 있는 그룹으로 레코드를 구조화한다.",
            r'''
import re
fixture_path = FIXTURE_DIR / "event-lines.txt"
lines = fixture_path.read_text(encoding="utf-8").splitlines()
''',
            r'''
EVENT_PATTERN = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<level>INFO|WARNING|ERROR)\s+"
    r"(?P<message>.+)"
)


def parse_event(line: str) -> dict:
    match = EVENT_PATTERN.fullmatch(line)
    if match is None:
        raise ValueError("이벤트 형식이 아니다.")
    return match.groupdict()


parsed = [parse_event(line) for line in lines[:-1]]
parsed
''',
            r'''
assert parsed[0] == {"date": "2026-08-14", "level": "INFO", "message": "completed"}
assert parse_event("2026-08-14 INFO a b")["message"] == "a b"
try:
    parse_event(lines[-1])
except ValueError:
    pass
else:
    raise AssertionError("형식 오류를 허용했다.")
print("검증 통과")
''',
            "그룹 추출 후에도 날짜 범위와 허용 수준은 의미 검증한다.",
        ),
    )

    write_notebook(
        SOLUTION_DIR / "05-5-validation-solution.ipynb",
        solution_cells(
            "05-5. 데이터 검증",
            "여러 오류를 구조화하고 원본 레코드를 변경하지 않는다.",
            r'''
import json
import re
from ipaddress import ip_address, ip_network
from urllib.parse import unquote, urlsplit

fixture_path = FIXTURE_DIR / "validation-records.jsonl"
raw_lines = fixture_path.read_text(encoding="utf-8").splitlines()
records, json_errors = [], []
for line_number, line in enumerate(raw_lines, start=1):
    try:
        records.append(json.loads(line))
    except json.JSONDecodeError:
        encoded = line.encode("utf-8")
        json_errors.append({
            "line": line_number,
            "code": "INVALID_JSON",
            "byte_length": len(encoded),
        })
''',
            r'''
ALLOWED_RESULTS = {"SUCCESS", "FAILURE", "LOCKED"}
ACCOUNT_PATTERN = re.compile(r"[A-Za-z0-9_-]{3,32}")
BAD_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")
ENCODED_AGAIN = re.compile(r"%[0-9A-Fa-f]{2}")


def normalize_request_path(target: str) -> str:
    if not isinstance(target, str) or not target or len(target) > 2048:
        raise ValueError("잘못된 target이다.")
    if any(character in target for character in ("\x00", "\r", "\n", "\\")):
        raise ValueError("허용되지 않은 문자가 있다.")
    try:
        parts = urlsplit(target)
    except ValueError as exc:
        raise ValueError("target 구조를 해석할 수 없다.") from exc
    if parts.scheme or parts.netloc or parts.fragment or not parts.path.startswith("/"):
        raise ValueError("origin-form 경로가 필요하다.")
    if BAD_PERCENT.search(parts.path):
        raise ValueError("잘못된 percent-encoding이다.")
    try:
        decoded = unquote(parts.path, encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("UTF-8 경로가 아니다.") from exc
    if ENCODED_AGAIN.search(decoded):
        raise ValueError("중첩 인코딩을 허용하지 않는다.")
    segments = []
    for segment in decoded.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            raise ValueError("상위 경로 이동을 허용하지 않는다.")
        segments.append(segment)
    return "/" + "/".join(segments)


def validate_account(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("계정은 문자열이어야 한다.")
    cleaned = value.strip()
    if ACCOUNT_PATTERN.fullmatch(cleaned) is None:
        raise ValueError("계정 형식이 올바르지 않다.")
    return cleaned


def validate_ip(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("IP는 문자열이어야 한다.")
    cleaned = value.strip()
    if "%" in cleaned:
        raise ValueError("영역 ID가 포함된 IPv6는 허용하지 않는다.")
    return str(ip_address(cleaned))


def validate_result(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("인증 결과는 문자열이어야 한다.")
    normalized = value.strip().upper()
    if normalized not in ALLOWED_RESULTS:
        raise ValueError("허용되지 않은 인증 결과다.")
    return normalized


def validate_risk_score(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("위험 점수는 정수여야 한다.")
    if not 0 <= value <= 100:
        raise ValueError("위험 점수 범위를 벗어났다.")
    return value


def validate_record(record: dict) -> tuple[dict, list[dict]]:
    cleaned, errors = {}, []

    def add(field: str, code: str, message: str) -> None:
        errors.append({"field": field, "code": code, "message": message})

    if not isinstance(record, dict):
        return {}, [{"field": "record", "code": "INVALID_TYPE", "message": "객체가 필요하다."}]

    validators = {
        "account": validate_account,
        "ip": validate_ip,
        "result": validate_result,
        "risk_score": validate_risk_score,
        "target": normalize_request_path,
    }

    for field, validator in validators.items():
        if field not in record:
            add(field, "MISSING", "필수 필드가 없다.")
            continue
        try:
            cleaned[field] = validator(record[field])
        except (TypeError, ValueError):
            add(field, "INVALID", "필드 규칙을 만족하지 않는다.")

    return cleaned, errors


def make_shareable_record(record: dict) -> dict:
    parsed_ip = ip_address(record["ip"])
    prefix = 24 if parsed_ip.version == 4 else 64
    account = record["account"]
    return {
        "account": account[:2] + "*" * max(0, len(account) - 2),
        "ip_network": str(ip_network(f"{parsed_ip}/{prefix}", strict=False)),
        "result": record["result"],
        "risk_score": record["risk_score"],
        "path": record["target"],
    }


results = [validate_record(record) for record in records]
valid_records = [cleaned for cleaned, errors in results if not errors]
invalid_records = [errors for _, errors in results if errors]
shareable = [make_shareable_record(record) for record in valid_records]
print("정상:", len(valid_records), "검증 오류:", len(invalid_records), "JSON 오류:", len(json_errors))
shareable
''',
            r'''
assert [len(errors) for _, errors in results] == [0, 5, 0, 2]
assert len(json_errors) == 1
assert len(raw_lines) == len(valid_records) + len(invalid_records) + len(json_errors)
before = records[0].copy()
cleaned, errors = validate_record(records[0])
assert records[0] == before and cleaned["result"] == "SUCCESS" and not errors
assert cleaned["target"] == "/login"
assert valid_records[1]["ip"] == "2001:db8::10"
assert all("ip" not in record and "account" in record for record in shareable)
assert all("token" not in record["path"] for record in shareable)
print("검증 통과")
''',
            "오류 코드는 표시 문구와 분리해 집계·다국어·재처리에 사용한다.",
        ),
    )

    write_notebook(
        SOLUTION_DIR / "05-6-datetime-solution.ipynb",
        solution_cells(
            "05-6. 날짜와 시간",
            "ISO 8601 값을 UTC aware datetime으로 변환한다.",
            r'''
from datetime import datetime, timezone
import json
fixture_path = FIXTURE_DIR / "timestamp-events.jsonl"
records = [json.loads(line) for line in fixture_path.read_text(encoding="utf-8").splitlines()]
''',
            r'''
def parse_utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise TypeError("timestamp는 문자열이어야 한다.")
    value = value.strip()
    if not value:
        raise ValueError("timestamp는 비어 있을 수 없다.")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"잘못된 timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ValueError("시간대 정보가 필요하다.")
    return parsed.astimezone(timezone.utc)


valid, errors = [], []
for record in records:
    try:
        valid.append({**record, "timestamp_utc": parse_utc(record["timestamp"])})
    except (KeyError, TypeError, ValueError) as exc:
        event = record.get("event") if isinstance(record, dict) else None
        errors.append({"event": event, "code": "INVALID_TIMESTAMP", "message": str(exc)})
valid
''',
            r'''
assert len(valid) == 2 and len(errors) == 2
assert valid[0]["timestamp_utc"].isoformat() == "2026-08-14T01:30:00+00:00"
assert all(item["timestamp_utc"].tzinfo == timezone.utc for item in valid)
assert [item["event"] for item in sorted(valid, key=lambda item: item["timestamp_utc"])] == ["login", "api"]
for invalid in ("", "   ", 123, "2026-08-14ZT01:30:00"):
    try:
        parse_utc(invalid)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError("타입·빈 값·Z 위치 경계를 허용했다.")
print("검증 통과")
''',
            "UTC는 저장·비교 기준이며, 사용자에게 표시할 때 필요한 시간대로 변환한다.",
        ),
    )

    write_notebook(
        SOLUTION_DIR / "05-7-numpy-array-solution.ipynb",
        solution_cells(
            "05-7. NumPy 배열",
            "결측값·조건 마스크·벡터 집계를 검증한다.",
            r'''
import numpy as np
fixture_path = FIXTURE_DIR / "measurements.csv"
values = np.genfromtxt(fixture_path, delimiter=",", skip_header=1, usecols=1, dtype=float)
''',
            r'''
valid_mask = np.isfinite(values)
valid_values = values[valid_mask]
valid_mean = float(valid_values.mean())
high_mask = valid_mask & (values >= 80)

total_requests = np.array([10, 40, 5, 0], dtype=np.int64)
not_found_404 = np.array([9, 9, 0, 0], dtype=np.int64)
unique_404_paths = np.array([9, 1, 0, 0], dtype=np.int64)
sensitive_requests = np.array([0, 0, 1, 0], dtype=np.int64)
unique_sensitive_paths = np.array([0, 0, 1, 0], dtype=np.int64)
sensitive_2xx = np.array([0, 0, 1, 0], dtype=np.int64)

not_found_rate = np.divide(
    not_found_404,
    total_requests,
    out=np.zeros(total_requests.shape, dtype=float),
    where=total_requests > 0,
)
scan_signal = (
    (not_found_404 >= 8)
    & (not_found_rate >= 0.70)
    & (unique_404_paths >= 6)
)
sensitive_signal = (
    (sensitive_2xx >= 1)
    | ((sensitive_requests >= 3) & (unique_sensitive_paths >= 2))
)
candidate = scan_signal | sensitive_signal
reason = np.select(
    [scan_signal & sensitive_signal, sensitive_signal, scan_signal],
    ["scan+sensitive", "sensitive", "scan"],
    default="-",
)

print("values:", values)
print("valid_mean:", valid_mean)
print("high:", values[high_mask])
print("not_found_rate:", not_found_rate)
print("reason:", reason)
''',
            r'''
assert valid_mask.dtype == np.bool_
assert int(valid_mask.sum()) == 4
assert np.isclose(valid_mean, 30.5)
assert values[high_mask].tolist() == [85.0]
assert np.isnan(values[2]) and np.isnan(values[4])
assert np.allclose(not_found_rate, [0.9, 0.225, 0.0, 0.0])
assert candidate.tolist() == [True, False, True, False]
assert reason.tolist() == ["scan", "-", "sensitive", "-"]
print("검증 통과")
''',
            "다중 조건이 있을 때 간단한 bool 배열을 먼저 이름 붙여 만들고 결합한다.",
        ),
    )

    write_notebook(
        SOLUTION_DIR / "05-8-pandas-dataframe-solution.ipynb",
        solution_cells(
            "05-8. pandas와 DataFrame",
            "오류 행을 보존하며 전체 실행과 청크 실행 결과를 대조한다.",
            r'''
import numpy as np
import pandas as pd
fixture_path = FIXTURE_DIR / "items.csv"
ITEM_DTYPES = {
    "name": "string",
    "category": "string",
    "price": "string",
    "quantity": "string",
}
CSV_READ_OPTIONS = {
    "dtype": ITEM_DTYPES,
    "encoding": "utf-8",
    "encoding_errors": "strict",
    "keep_default_na": False,
    "na_values": [""],
}
frame = pd.read_csv(fixture_path, **CSV_READ_OPTIONS)
''',
            r'''
def clean_items(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    working = frame.copy()
    working["price_number"] = pd.to_numeric(working["price"], errors="coerce")
    working["quantity_number"] = pd.to_numeric(working["quantity"], errors="coerce")

    price_values = working["price_number"].to_numpy(dtype=float, na_value=np.nan)
    quantity_values = working["quantity_number"].to_numpy(dtype=float, na_value=np.nan)
    missing_name = working["name"].astype("string").str.strip().fillna("").eq("").to_numpy()
    invalid_price = ~np.isfinite(price_values) | (price_values < 0)
    invalid_quantity = (
        ~np.isfinite(quantity_values)
        | (quantity_values < 0)
        | np.not_equal(quantity_values, np.floor(quantity_values))
    )
    reasons = np.select(
        [missing_name, invalid_price, invalid_quantity],
        ["missing_name", "invalid_price", "invalid_quantity"],
        default="",
    )
    invalid = pd.Series(reasons != "", index=working.index)
    error_rows = working.loc[invalid].copy()
    error_rows["error_reason"] = reasons[invalid.to_numpy()]
    valid_rows = working.loc[~invalid].copy()
    valid_rows["name"] = valid_rows["name"].astype("string").str.strip()
    valid_rows["category"] = (
        valid_rows["category"].astype("string").str.strip().replace("", pd.NA).fillna("UNKNOWN")
    )
    valid_rows["total"] = valid_rows["price_number"] * valid_rows["quantity_number"]
    summary = valid_rows.groupby("category", dropna=False).agg(
        item_count=("name", "count"),
        total_amount=("total", "sum"),
    ).reset_index()
    return valid_rows, error_rows, summary


valid_rows, error_rows, summary = clean_items(frame)
summary
''',
            r'''
assert len(valid_rows) == 4 and len(error_rows) == 2
assert int(summary["item_count"].sum()) == 4

boundary = pd.DataFrame([
    {"name": "valid", "category": "input", "price": "1", "quantity": "1"},
    {"name": "infinite", "category": "input", "price": "inf", "quantity": "1"},
    {"name": "negative", "category": "input", "price": "-1", "quantity": "1"},
    {"name": "fractional", "category": "input", "price": "1", "quantity": "1.5"},
    {"name": "  ", "category": "input", "price": "1", "quantity": "1"},
])
boundary_valid, boundary_errors, _ = clean_items(boundary)
assert len(boundary_valid) == 1 and len(boundary_errors) == 4
assert set(boundary_errors["error_reason"]) == {
    "missing_name", "invalid_price", "invalid_quantity"
}

large_path = FIXTURE_DIR / "large_items.csv"
full_large = pd.read_csv(large_path, **CSV_READ_OPTIONS)
full_valid, full_errors, full_summary = clean_items(full_large)

chunk_valid = chunk_errors = 0
chunk_summaries = []
for chunk in pd.read_csv(large_path, chunksize=37, **CSV_READ_OPTIONS):
    valid, errors, chunk_summary = clean_items(chunk)
    chunk_valid += len(valid)
    chunk_errors += len(errors)
    chunk_summaries.append(chunk_summary)

combined_summary = (
    pd.concat(chunk_summaries, ignore_index=True)
    .groupby("category", as_index=False)[["item_count", "total_amount"]]
    .sum()
    .sort_values("category")
    .reset_index(drop=True)
)
expected_summary = full_summary.sort_values("category").reset_index(drop=True)

assert chunk_valid == 196 and chunk_errors == 4
assert len(full_valid) == chunk_valid and len(full_errors) == chunk_errors
pd.testing.assert_frame_equal(expected_summary, combined_summary, check_dtype=False)
print("검증 통과:", chunk_valid, "정상 /", chunk_errors, "오류")
''',
            "청크를 모두 저장하지 말고 최종 집계와 오류 건수만 증분 누적한다.",
        ),
    )


WEB_LOG_SOLUTION = r'''
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from ipaddress import ip_address
from pathlib import Path
from tempfile import NamedTemporaryFile, mkdtemp
from urllib.parse import unquote, urlsplit
import hmac
import json
import os
import posixpath
import re
import shutil
import unicodedata

import numpy as np
import pandas as pd


class LogFormatError(ValueError):
    pass


class LogValidationError(ValueError):
    pass


COMBINED_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<target>\S+) HTTP/(?P<http_version>[^"]+)" '
    r'(?P<status>[0-9]{3}) (?P<bytes>[0-9]+|-) '
    r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"'
)
INVALID_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")
SENSITIVE_SEGMENTS = {".env", ".git", "wp-admin", "phpmyadmin", "server-status"}
APPROVED_SCANNERS = {"198.51.100.77"}
RULE_VERSION = "chapter05-training-v2"
BATCH_SIZE = 25
ERROR_SAMPLE_LIMIT = 20
MAX_LINE_BYTES = 16_384
TRAINING_FIXTURE_SHA256 = {
    "web-access.log": "255cee6add742d2ddbc52cd1840ba5c99f1fe319b8b2e362e5a66a1dfc1a4aff",
    "web-access-invalid-utf8.log": "16ac8abb2f322704c0868b8036b7f6d6603de546cfeefb63b4cf3b91d8f963d1",
}


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_masking_key(paths: list[Path]) -> bytes:
    selected_paths = [path.resolve() for path in paths]
    if not selected_paths:
        raise RuntimeError("저장할 입력 경로가 없다.")
    if any(not path.is_file() for path in selected_paths):
        raise FileNotFoundError("저장 시점의 입력 경로를 확인해야 한다.")

    key_text = os.environ.get("LOG_MASKING_KEY")
    if key_text:
        key = key_text.encode("utf-8")
        if len(key) < 32:
            raise RuntimeError("LOG_MASKING_KEY는 UTF-8 기준 32바이트 이상이어야 한다.")
        return key

    training_paths = {
        (FIXTURE_DIR / name).resolve(): expected_digest
        for name, expected_digest in TRAINING_FIXTURE_SHA256.items()
    }
    if all(
        path in training_paths
        and hmac.compare_digest(sha256_file(path), training_paths[path])
        for path in selected_paths
    ):
        return b"chapter05-training-key-not-for-real-data"

    raise RuntimeError("실제 로그 결과를 저장하려면 LOG_MASKING_KEY가 필요하다.")


def remove_record_separator(raw_line: bytes) -> bytes:
    return raw_line.removesuffix(b"\n").removesuffix(b"\r")


def normalize_request_path(target: str) -> tuple[str, str, bool]:
    try:
        parts = urlsplit(target)
    except ValueError as exc:
        raise LogValidationError("URL 구조를 해석할 수 없다.") from exc
    if parts.scheme or parts.netloc:
        raise LogValidationError("절대 URL 형식을 허용하지 않는다.")
    raw_path = parts.path or "/"
    if not raw_path.startswith("/") or INVALID_PERCENT.search(raw_path):
        raise LogValidationError("요청 경로 형식이 올바르지 않다.")
    try:
        decoded = unquote(raw_path, encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise LogValidationError("경로의 percent-encoding을 UTF-8로 해석할 수 없다.") from exc
    decoded = unicodedata.normalize("NFC", decoded).replace("\\", "/")
    if len(decoded) > 2048 or any(ord(char) < 32 or ord(char) == 127 for char in decoded):
        raise LogValidationError("경로 길이 또는 제어 문자 규칙을 위반했다.")
    traversal = any(segment == ".." for segment in decoded.split("/"))
    normalized = posixpath.normpath("/" + decoded.lstrip("/"))
    return raw_path, normalized, traversal


def user_agent_class(value: str) -> str:
    lowered = value.casefold()
    if "approvedtrainingscanner" in lowered:
        return "approved_scanner"
    if "scanner" in lowered:
        return "scanner"
    if "browser" in lowered or "mozilla" in lowered:
        return "browser"
    return "other"


def parse_combined_log(text: str) -> dict:
    match = COMBINED_PATTERN.fullmatch(text)
    if match is None:
        raise LogFormatError("Combined Log 형식과 일치하지 않는다.")
    fields = match.groupdict()
    try:
        canonical_ip = str(ip_address(fields["ip"]))
        timestamp = datetime.strptime(fields["timestamp"], "%d/%b/%Y:%H:%M:%S %z").astimezone(timezone.utc)
    except ValueError as exc:
        raise LogValidationError("IP 또는 timestamp 의미 검증에 실패했다.") from exc
    status = int(fields["status"])
    if not 100 <= status <= 599:
        raise LogValidationError("상태 코드는 100~599 범위여야 한다.")
    if fields["bytes"] == "-":
        response_bytes = None
    else:
        if len(fields["bytes"]) > 19:
            raise LogValidationError("응답 바이트 값이 허용 범위를 벗어났다.")
        response_bytes = int(fields["bytes"])
        if response_bytes > 2**63 - 1:
            raise LogValidationError("응답 바이트 값이 허용 범위를 벗어났다.")
    raw_path, normalized_path, traversal = normalize_request_path(fields["target"])
    segments = {segment.casefold() for segment in normalized_path.split("/") if segment}
    sensitive = bool(segments & SENSITIVE_SEGMENTS)
    return {
        "ip": canonical_ip,
        "timestamp": timestamp,
        "window": timestamp.replace(minute=(timestamp.minute // 5) * 5, second=0, microsecond=0),
        "method": fields["method"],
        "status": status,
        "response_bytes": response_bytes,
        "raw_path": raw_path,
        "normalized_path": normalized_path,
        "normalization_changed": raw_path != normalized_path,
        "path_traversal": traversal,
        "sensitive": sensitive,
        "user_agent_class": user_agent_class(fields["user_agent"]),
    }


def new_summary() -> dict:
    return {
        "total_lines": 0,
        "parsed_lines": 0,
        "encoding_errors": 0,
        "format_errors": 0,
        "oversized_line_errors": 0,
        "validation_errors": 0,
        "known_bytes_rows": 0,
        "missing_bytes": 0,
        "status": Counter(),
        "method": Counter(),
        "windows": defaultdict(lambda: {
            "total_requests": 0,
            "not_found_404": 0,
            "sensitive_requests": 0,
            "sensitive_2xx": 0,
            "normalization_changed_requests": 0,
            "path_traversal_requests": 0,
            "not_found_paths": set(),
            "sensitive_paths": set(),
        }),
        "error_samples": [],
        "_input_paths": (),
    }


def error_sample(
    source: str,
    line: int,
    length: int,
    error_type: str,
) -> dict:
    return {
        "source": source,
        "line": line,
        "type": error_type,
        "length": length,
    }


def merge_batch(summary: dict, records: list[dict]) -> None:
    if not records:
        return
    frame = pd.DataFrame.from_records(records)
    summary["parsed_lines"] += len(frame)
    summary["status"].update(frame["status"].value_counts().to_dict())
    summary["method"].update(frame["method"].value_counts().to_dict())
    summary["known_bytes_rows"] += int(frame["response_bytes"].notna().sum())
    summary["missing_bytes"] += int(frame["response_bytes"].isna().sum())

    for (source_ip, window), group in frame.groupby(["ip", "window"], sort=False):
        bucket = summary["windows"][(source_ip, window)]
        not_found = group["status"].eq(404)
        sensitive = group["sensitive"]
        bucket["total_requests"] += len(group)
        bucket["not_found_404"] += int(not_found.sum())
        bucket["sensitive_requests"] += int(sensitive.sum())
        bucket["sensitive_2xx"] += int((sensitive & group["status"].between(200, 299)).sum())
        bucket["normalization_changed_requests"] += int(group["normalization_changed"].sum())
        bucket["path_traversal_requests"] += int(group["path_traversal"].sum())
        bucket["not_found_paths"].update(group.loc[not_found, "normalized_path"])
        bucket["sensitive_paths"].update(group.loc[sensitive, "normalized_path"])


def analyze_files(paths: list[Path], batch_size: int = BATCH_SIZE) -> tuple[dict, list[dict]]:
    summary = new_summary()
    summary["_input_paths"] = tuple(str(path.resolve()) for path in paths)
    batch: list[dict] = []
    input_manifest = []

    for source_number, path in enumerate(paths, start=1):
        source_label = f"input-{source_number}"
        digest = sha256()
        with path.open("rb") as file:
            line_number = 0
            while True:
                raw_line = file.readline(MAX_LINE_BYTES + 1)
                if not raw_line:
                    break
                line_number += 1
                digest.update(raw_line)
                summary["total_lines"] += 1

                if len(raw_line) > MAX_LINE_BYTES:
                    oversized_length = len(raw_line)
                    while not raw_line.endswith(b"\n"):
                        raw_line = file.readline(MAX_LINE_BYTES + 1)
                        if not raw_line:
                            break
                        digest.update(raw_line)
                        oversized_length += len(raw_line)
                    summary["oversized_line_errors"] += 1
                    if len(summary["error_samples"]) < ERROR_SAMPLE_LIMIT:
                        summary["error_samples"].append(
                            error_sample(
                                source_label,
                                line_number,
                                oversized_length,
                                "line_too_long",
                            )
                        )
                    continue

                raw = remove_record_separator(raw_line)
                try:
                    text = raw.decode("utf-8", errors="strict")
                except UnicodeDecodeError:
                    summary["encoding_errors"] += 1
                    if len(summary["error_samples"]) < ERROR_SAMPLE_LIMIT:
                        summary["error_samples"].append(
                            error_sample(source_label, line_number, len(raw), "encoding")
                        )
                    continue
                try:
                    batch.append(parse_combined_log(text))
                except LogFormatError:
                    summary["format_errors"] += 1
                    if len(summary["error_samples"]) < ERROR_SAMPLE_LIMIT:
                        summary["error_samples"].append(
                            error_sample(source_label, line_number, len(raw), "format")
                        )
                except LogValidationError:
                    summary["validation_errors"] += 1
                    if len(summary["error_samples"]) < ERROR_SAMPLE_LIMIT:
                        summary["error_samples"].append(
                            error_sample(source_label, line_number, len(raw), "validation")
                        )
                if len(batch) >= batch_size:
                    merge_batch(summary, batch)
                    batch.clear()
        merge_batch(summary, batch)
        batch.clear()
        input_manifest.append({
            "name": path.name,
            "sha256": digest.hexdigest(),
            "size_bytes": path.stat().st_size,
        })
    return summary, input_manifest


def build_features(summary: dict) -> pd.DataFrame:
    base_columns = [
        "ip",
        "window",
        "total_requests",
        "not_found_404",
        "unique_404_paths",
        "sensitive_requests",
        "unique_sensitive_paths",
        "sensitive_2xx",
        "normalization_changed_requests",
        "path_traversal_requests",
        "approved_scanner_context",
    ]
    rows = []
    for (source_ip, window), values in summary["windows"].items():
        rows.append({
            "ip": source_ip,
            "window": window,
            "total_requests": values["total_requests"],
            "not_found_404": values["not_found_404"],
            "unique_404_paths": len(values["not_found_paths"]),
            "sensitive_requests": values["sensitive_requests"],
            "unique_sensitive_paths": len(values["sensitive_paths"]),
            "sensitive_2xx": values["sensitive_2xx"],
            "normalization_changed_requests": values["normalization_changed_requests"],
            "path_traversal_requests": values["path_traversal_requests"],
            "approved_scanner_context": source_ip in APPROVED_SCANNERS,
        })
    features = pd.DataFrame(rows, columns=base_columns)
    if features.empty:
        features["not_found_rate"] = pd.Series(dtype="float64")
        features["candidate"] = pd.Series(dtype="bool")
        features["reason"] = pd.Series(dtype="string")
        return features

    features = features.sort_values(["window", "ip"]).reset_index(drop=True)
    total = features["total_requests"].to_numpy(dtype=np.int64)
    not_found = features["not_found_404"].to_numpy(dtype=np.int64)
    not_found_rate = np.divide(
        not_found,
        total,
        out=np.zeros(total.shape, dtype=float),
        where=total > 0,
    )
    unique_404 = features["unique_404_paths"].to_numpy(dtype=np.int64)
    sensitive_requests = features["sensitive_requests"].to_numpy(dtype=np.int64)
    unique_sensitive = features["unique_sensitive_paths"].to_numpy(dtype=np.int64)
    sensitive_2xx = features["sensitive_2xx"].to_numpy(dtype=np.int64)
    scan_signal = (not_found >= 8) & (not_found_rate >= 0.70) & (unique_404 >= 6)
    sensitive_signal = (sensitive_2xx >= 1) | ((sensitive_requests >= 3) & (unique_sensitive >= 2))
    features["not_found_rate"] = not_found_rate
    features["candidate"] = scan_signal | sensitive_signal
    features["reason"] = np.select(
        [scan_signal & sensitive_signal, sensitive_signal, scan_signal],
        ["scan+sensitive", "sensitive", "scan"],
        default="-",
    )
    return features


def alias(value: str, prefix: str, masking_key: bytes) -> str:
    message = f"{prefix}:{value}".encode("utf-8")
    digest = hmac.new(masking_key, message, "sha256").hexdigest()[:24]
    return f"{prefix}_{digest}"


def masked_features(features: pd.DataFrame, masking_key: bytes) -> pd.DataFrame:
    output = features.drop(columns=["ip"]).copy()
    output.insert(
        0,
        "source_alias",
        features["ip"].map(lambda value: alias(value, "ip", masking_key)),
    )
    output["window"] = output["window"].map(lambda value: value.isoformat())
    return output


def validate_summary(summary: dict) -> None:
    errors = (
        summary["encoding_errors"]
        + summary["format_errors"]
        + summary["validation_errors"]
        + summary["oversized_line_errors"]
    )
    assert summary["total_lines"] == summary["parsed_lines"] + errors
    assert summary["parsed_lines"] == sum(summary["status"].values())
    assert summary["parsed_lines"] == sum(summary["method"].values())
    assert summary["parsed_lines"] == summary["known_bytes_rows"] + summary["missing_bytes"]


def atomic_write_text(path: Path, text: str, output_root: Path) -> None:
    root = output_root.resolve()
    target = path.resolve(strict=False)
    target.relative_to(root)
    if path.is_symlink():
        raise ValueError("심볼릭 출력을 허용하지 않는다.")
    temporary = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            delete=False,
        ) as tmp:
            temporary = Path(tmp.name)
            tmp.write(text)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def save_outputs(
    summary: dict,
    features: pd.DataFrame,
    input_paths: list[Path],
    input_manifest: list[dict],
    output_root: Path,
    run_id: str,
    allowed_parent: Path,
) -> Path:
    # 저장 시점의 실제 입력 경로로 키 정책을 다시 검증한다.
    selected_paths = tuple(str(path.resolve()) for path in input_paths)
    if selected_paths != summary.get("_input_paths"):
        raise RuntimeError("분석한 입력과 저장 시점의 입력 경로가 다르다.")
    masking_key = load_masking_key(input_paths)
    allowed_parent.mkdir(parents=True, exist_ok=True)
    if allowed_parent.is_symlink():
        raise ValueError("심볼릭 허용 상위 경로를 허용하지 않는다.")
    allowed_parent = allowed_parent.resolve()

    if output_root.is_symlink():
        raise ValueError("심볼릭 출력 루트를 허용하지 않는다.")
    output_root.resolve(strict=False).relative_to(allowed_parent)
    output_root.mkdir(parents=True, exist_ok=True)
    output_root = output_root.resolve()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("잘못된 run_id이다.")
    run_dir = output_root / run_id
    if run_dir.exists() or run_dir.is_symlink():
        raise FileExistsError("동일한 run_id의 결과가 이미 존재한다.")

    masked = masked_features(features, masking_key)
    candidates = masked.loc[masked["candidate"]].copy()
    quality = {
        key: summary[key]
        for key in (
            "total_lines", "parsed_lines", "encoding_errors", "format_errors",
            "validation_errors", "oversized_line_errors", "known_bytes_rows",
            "missing_bytes",
        )
    }
    manifest = {
        "rule_version": RULE_VERSION,
        "inputs": input_manifest,
        "quality": quality,
        "thresholds": {
            "scan": {"not_found_404": 8, "not_found_rate": 0.70, "unique_404_paths": 6},
            "sensitive": {"sensitive_2xx": 1, "sensitive_requests": 3, "unique_sensitive_paths": 2},
        },
    }
    quality_frame = pd.DataFrame([quality])
    status_frame = pd.DataFrame(
        sorted(summary["status"].items()),
        columns=["status", "requests"],
    )
    staging_dir = Path(mkdtemp(prefix=f".staging-{run_id}-", dir=output_root))
    staging_dir.chmod(0o700)
    try:
        atomic_write_text(staging_dir / "window-features.csv", masked.to_csv(index=False), output_root)
        atomic_write_text(staging_dir / "triage-candidates.csv", candidates.to_csv(index=False), output_root)
        atomic_write_text(staging_dir / "quality-report.csv", quality_frame.to_csv(index=False), output_root)
        atomic_write_text(staging_dir / "status-counts.csv", status_frame.to_csv(index=False), output_root)
        atomic_write_text(
            staging_dir / "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            output_root,
        )
        os.replace(staging_dir, run_dir)
        return run_dir
    finally:
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
'''


def build_web_log_notebooks() -> None:
    learner = [
        markdown(
            "# 05-9. 웹 접근 로그 분석 종합 실습\n\n## Goal\n\n"
            "합성 Combined Log fixture를 스트리밍하고 인코딩·형식·의미 오류를 나눈다. "
            "5분 시간창 특징과 NumPy 마스크로 교육용 조사 후보를 만든다."
        ),
        markdown(
            "## Setup\n\n"
            "실제 로그를 사용하지 않고 문서용 IP 대역으로 만든 fixture를 사용한다. "
            "풀이는 `notebooks/solutions/05-9-web-log-analysis-solution.ipynb`에서 자신의 구현 후 검증한다."
        ),
        code(
            COMMON_SETUP
            + r'''
import numpy as np
import pandas as pd
from tempfile import TemporaryDirectory

LOG_PATHS = [
    FIXTURE_DIR / "web-access.log",
    FIXTURE_DIR / "web-access-invalid-utf8.log",
]
for path in LOG_PATHS:
    print(path.name, path.stat().st_size, "bytes")
'''
        ),
        markdown(
            "## Steps\n\n"
            "1. 바이트 줄에서 CRLF/LF 레코드 종료만 제거한다.\n"
            "2. UTF-8 strict 디코딩 오류를 별도 건수로 나눈다.\n"
            "3. 형식 파싱 후 `ipaddress.ip_address()`로 IPv4·IPv6를 검증한다.\n"
            "4. URL raw path를 보존하되 파생된 정규화 경로로 집계한다.\n"
            "5. 5분·IP별 특징표와 NumPy 조건 마스크를 만든다.\n"
            "6. IP와 경로를 가명처리하고 전용 루트에 원자적으로 저장한다."
        ),
        code(
            r'''
TODO_DONE = False
MAX_LINE_BYTES = 16_384


def remove_record_separator(raw_line: bytes) -> bytes:
    # 실습 과제: b"\\n" 문자 집합이 아니라 실제 CRLF/LF 접미사만 제거한다.
    raise NotImplementedError


def parse_combined_log(text: str) -> dict:
    # 실습 과제: 형식 파싱과 의미 검증을 나눈다.
    raise NotImplementedError


def analyze_files(paths: list[Path]) -> tuple[list[dict], dict]:
    # 실습 과제: 제한 readline, UTF-8 strict, 오류 유형별 건수로 fixture 전체를 처리한다.
    raise NotImplementedError


def build_features(records: list[dict]) -> pd.DataFrame:
    # 실습 과제: 5분·IP별 특징을 반환한다.
    raise NotImplementedError


def classify_candidates(features: pd.DataFrame) -> pd.DataFrame:
    # 실습 과제: np.divide, bool 마스크, np.select를 사용한다.
    raise NotImplementedError


def mask_features(features: pd.DataFrame, masking_key: bytes) -> pd.DataFrame:
    # 실습 과제: HMAC 별칭을 만들고 원문 IP·경로·쿼리를 결과에서 제외한다.
    raise NotImplementedError


def publish_run(
    masked: pd.DataFrame,
    quality: dict,
    output_root: Path,
    run_id: str,
) -> Path:
    # 실습 과제: 숨김 staging 디렉터리에 완성한 뒤 run 디렉터리로 한 번에 게시한다.
    raise NotImplementedError
'''
        ),
        markdown(
            "## Checks\n\n"
            "공개 경계 검증은 줄 종료·정상 IP·잘못된 IP·시간창 규칙을 확인한다. "
            "탐지 후보는 침해 확정이 아니라 원본 맥락을 다시 볼 우선순위이다."
        ),
        code(
            r'''
if not TODO_DONE:
    print("TODO를 구현한 뒤 TODO_DONE을 True로 바꾸세요.")
else:
    assert remove_record_separator(b"record\r\n") == b"record"
    assert remove_record_separator(b"record\n") == b"record"
    assert remove_record_separator(b"login") == b"login"
    sample = (
        '203.0.113.10 - - [14/Aug/2026:10:30:00 +0900] '
        '"GET /login?token=secret HTTP/1.1" 200 443 "-" "TrainingBrowser/1.0"'
    )
    parsed = parse_combined_log(sample)
    assert parsed["ip"] == "203.0.113.10"
    assert parsed["normalized_path"] == "/login"

    records, quality = analyze_files(LOG_PATHS)
    assert quality == {
        "total_lines": 87,
        "parsed_lines": 82,
        "encoding_errors": 1,
        "format_errors": 1,
        "validation_errors": 3,
        "oversized_line_errors": 0,
        "known_bytes_rows": 81,
        "missing_bytes": 1,
    }
    features = classify_candidates(build_features(records))
    masked = mask_features(
        features,
        b"chapter05-learner-public-check-key",
    )
    assert "ip" not in masked.columns
    assert "source_alias" in masked.columns
    assert not masked.astype("string").apply(
        lambda column: column.str.contains("203.0.113.10", regex=False).any()
    ).any()

    with TemporaryDirectory(prefix="chapter05-learner-") as temporary_root:
        output_root = Path(temporary_root).resolve()
        run_dir = publish_run(masked, quality, output_root, "public-check")
        assert run_dir.resolve().parent == output_root
        assert {path.name for path in run_dir.iterdir()} == {
            "window-features.csv",
            "quality-report.json",
        }
        assert not list(output_root.glob(".staging-public-check-*"))
    print("공개 경계 검증 통과")
'''
        ),
        markdown(
            "## Next Steps\n\n"
            "자신의 구현을 풀이 검증용 Notebook의 품질 불변식과 비교한다. "
            "실제 평가에서는 공개 저장소의 풀이본과 별개인 교수자용 비공개 테스트를 사용한다."
        ),
    ]
    write_notebook(NOTEBOOK_DIR / "05-9-web-log-analysis.ipynb", learner)

    solution = [
        markdown(
            "# 05-9. 웹 접근 로그 분석 종합 실습 — 풀이·검증\n\n## Goal\n\n"
            "합성 fixture의 정상·오탐·인코딩·형식·의미 경계를 모두 처리하고, "
            "마스킹된 조사 후보 산출물을 안전하게 저장한다."
        ),
        markdown(
            "## Setup\n\n"
            "fixture에는 문서용 IP 대역, 반복 favicon 404, 승인 스캐너, 다수 고유 404 경로, "
            "민감 경로 2xx, IPv6, CRLF, invalid UTF-8을 포함한다."
        ),
        code(
            COMMON_SETUP
            + r'''
from datetime import datetime, timezone
import os

LOG_PATHS = [
    FIXTURE_DIR / "web-access.log",
    FIXTURE_DIR / "web-access-invalid-utf8.log",
]
ALLOWED_OUTPUT_PARENT = Path(
    os.environ.get("CH05_ALLOWED_OUTPUT_PARENT", ROOT / "outputs")
)
OUTPUT_ROOT = Path(
    os.environ.get("CH05_OUTPUT_ROOT", ALLOWED_OUTPUT_PARENT / "web-log-analysis-lab")
)
RUN_ID = os.environ.get(
    "CH05_RUN_ID",
    datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%S%fZ"),
)
'''
        ),
        markdown("## Steps\n\n디코딩·파싱·검증·집계·가명처리·저장 함수를 정의한다."),
        code(WEB_LOG_SOLUTION),
        markdown("### 분석 실행\n\n원문 오류 샘플 대신 오류 유형·길이·해시 접두사만 남긴다."),
        code(
            r'''
summary, input_manifest = analyze_files(LOG_PATHS)
validate_summary(summary)
features = build_features(summary)
preview_masking_key = load_masking_key(LOG_PATHS)
masked = masked_features(features, preview_masking_key)

quality = {
    key: summary[key]
    for key in (
        "total_lines", "parsed_lines", "encoding_errors", "format_errors",
        "validation_errors", "oversized_line_errors", "known_bytes_rows",
        "missing_bytes",
    )
}
print(quality)
print(masked.loc[masked["candidate"]])
print(summary["error_samples"])
'''
        ),
        markdown("## Checks\n\n품질 불변식과 합성 시나리오의 오탐·정탐 경계를 대조한다."),
        code(
            r'''
assert quality["encoding_errors"] == 1
assert quality["format_errors"] == 1
assert quality["validation_errors"] == 3
assert quality["oversized_line_errors"] == 0
assert quality["missing_bytes"] == 1
assert quality["total_lines"] == 87
assert quality["parsed_lines"] == 82
assert quality["known_bytes_rows"] == 81
assert len(summary["error_samples"]) <= ERROR_SAMPLE_LIMIT
assert Counter(sample["type"] for sample in summary["error_samples"]) == {
    "encoding": 1,
    "format": 1,
    "validation": 3,
}

candidates = features.loc[features["candidate"]]
candidate_ips = set(candidates["ip"])
assert "198.51.100.40" in candidate_ips          # 다수 고유 404 경로
assert "203.0.113.50" in candidate_ips           # 민감 경로 2xx 1건
assert "198.51.100.77" in candidate_ips          # 승인 스캐너도 신호는 보존
assert "192.0.2.20" not in candidate_ips          # 동일 favicon 404 반복 오탐 억제
assert "192.0.2.10" not in candidate_ips          # 소량의 일반 404
assert int(features["normalization_changed_requests"].sum()) == 2
assert int(features["path_traversal_requests"].sum()) == 2

assert not any("raw" in sample for sample in summary["error_samples"])
assert all(
    set(sample) == {"source", "line", "type", "length"}
    for sample in summary["error_samples"]
)
assert "ip" not in masked.columns and "source_alias" in masked.columns
assert alias("same-value", "ip", preview_masking_key) != alias(
    "same-value", "path", preview_masking_key
)

empty_features = build_features(new_summary())
assert empty_features.empty and {"candidate", "reason"} <= set(empty_features.columns)

invalid_target = (
    '192.0.2.1 - - [14/Aug/2026:01:00:00 +0000] '
    '"GET http://[::1 HTTP/1.1" 200 10 "-" "TrainingBrowser/1.0"'
)
huge_bytes = (
    '192.0.2.1 - - [14/Aug/2026:01:00:00 +0000] '
    f'"GET / HTTP/1.1" 200 {"9" * 4_300} "-" "TrainingBrowser/1.0"'
)
for invalid_line in (invalid_target, huge_bytes):
    try:
        parse_combined_log(invalid_line)
    except LogValidationError:
        pass
    else:
        raise AssertionError("경계 입력을 검증 오류로 분류하지 않았다.")

non_ascii_digits = (
    '192.0.2.1 - - [14/Aug/2026:01:00:00 +0000] '
    '"GET / HTTP/1.1" ２００ １０ "-" "TrainingBrowser/1.0"'
)
try:
    parse_combined_log(non_ascii_digits)
except LogFormatError:
    pass
else:
    raise AssertionError("status·bytes에서 ASCII 숫자 경계를 지키지 않았다.")

ALLOWED_OUTPUT_PARENT.mkdir(parents=True, exist_ok=True)
valid_line = (
    '203.0.113.10 - - [14/Aug/2026:10:30:00 +0900] '
    '"GET /login HTTP/1.1" 200 443 "-" "TrainingBrowser/1.0"'
)
with NamedTemporaryFile("wb", dir=ALLOWED_OUTPUT_PARENT, delete=False) as temporary_file:
    oversized_path = Path(temporary_file.name)
    temporary_file.write(b"x" * (MAX_LINE_BYTES + 1) + b"\n")
    temporary_file.write(valid_line.encode("utf-8") + b"\n")
try:
    oversized_summary, _ = analyze_files([oversized_path])
    assert oversized_summary["total_lines"] == 2
    assert oversized_summary["format_errors"] == 0
    assert oversized_summary["oversized_line_errors"] == 1
    assert oversized_summary["parsed_lines"] == 1
    assert oversized_summary["error_samples"][0]["type"] == "line_too_long"
finally:
    oversized_path.unlink(missing_ok=True)
print("품질·탐지 경계 검증 통과")
'''
        ),
        markdown("### 안전한 산출물 저장\n\n실제 로그에서는 가명처리 키를 환경변수·비밀 관리 시스템에서 제공하고 저장소에 넣지 않는다."),
        code(
            r'''
from unittest.mock import patch

# 저장 시점에 현재 입력 경로를 다시 검증하는지 확인한다.
ALLOWED_OUTPUT_PARENT.mkdir(parents=True, exist_ok=True)
with NamedTemporaryFile("wb", dir=ALLOWED_OUTPUT_PARENT, delete=False) as temporary_input:
    outside_input = Path(temporary_input.name)
    temporary_input.write(b"synthetic non-fixture input\n")
previous_key = os.environ.pop("LOG_MASKING_KEY", None)
try:
    try:
        load_masking_key([outside_input])
    except RuntimeError:
        pass
    else:
        raise AssertionError("외부 입력에 교육용 키를 사용했다.")

    try:
        save_outputs(
            summary,
            features,
            [OUTPUT_ROOT / "not-a-training-fixture.log"],
            input_manifest,
            OUTPUT_ROOT,
            f"{RUN_ID}-key-rejected",
            ALLOWED_OUTPUT_PARENT,
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("실제 로그 키 정책을 우회했다.")
finally:
    if previous_key is not None:
        os.environ["LOG_MASKING_KEY"] = previous_key
    outside_input.unlink(missing_ok=True)

# 파일 저장 중 실패해도 완성 run과 staging 디렉터리가 남지 않는지 확인한다.
failure_run_id = f"{RUN_ID}-write-failure"
with patch("os.replace", side_effect=OSError("교육용 저장 실패")):
    try:
        save_outputs(
            summary,
            features,
            LOG_PATHS,
            input_manifest,
            OUTPUT_ROOT,
            failure_run_id,
            ALLOWED_OUTPUT_PARENT,
        )
    except OSError:
        pass
    else:
        raise AssertionError("저장 실패가 전파되지 않았다.")
assert not (OUTPUT_ROOT / failure_run_id).exists()
assert not list(OUTPUT_ROOT.glob(f".staging-{failure_run_id}-*"))

run_dir = save_outputs(
    summary,
    features,
    LOG_PATHS,
    input_manifest,
    OUTPUT_ROOT,
    RUN_ID,
    ALLOWED_OUTPUT_PARENT,
)
expected_files = {
    "window-features.csv",
    "triage-candidates.csv",
    "quality-report.csv",
    "status-counts.csv",
    "manifest.json",
}
assert {path.name for path in run_dir.iterdir()} == expected_files

candidate_text = (run_dir / "triage-candidates.csv").read_text(encoding="utf-8")
assert "198.51.100.40" not in candidate_text
assert "token=do-not-store" not in candidate_text
assert "raw_path" not in candidate_text
print("저장 위치:", run_dir)
'''
        ),
        markdown(
            "## Next Steps\n\n"
            "교육용 임계값은 보편적 침해 판정 기준이 아니다. 서비스 기준선, 프록시·NAT, 승인 스캐너, "
            "자산 역할, 인증 이벤트를 함께 확인해 신호→조사→판정의 순서를 유지한다."
        ),
    ]
    write_notebook(SOLUTION_DIR / "05-9-web-log-analysis-solution.ipynb", solution)


def write_readmes() -> None:
    fixture_readme = """# 05장 실습 fixture

모든 파일은 교육용 합성 데이터이며 실제 계정·IP·토큰을 포함하지 않는다.

| 파일 | 연결 절 | 경계 사례 |
| --- | --- | --- |
| `normalization-cases.txt` | 05-1 | 양끝 공백, 분해된 유니코드, 대소문자 민감 경로 |
| `delimited-events.txt` | 05-2 | 메시지 내 구분자, 필드 수 오류 |
| `regex-cases.txt` | 05-3 | 전체 일치와 부분 검색 |
| `event-lines.txt` | 05-4 | 이름 있는 그룹, 형식 오류 |
| `validation-records.jsonl` | 05-5 | 계정·IP·허용값·점수·경로·JSON 문법 오류 |
| `timestamp-events.jsonl` | 05-6 | 시간대, `Z`, naive, 존재하지 않는 날짜 |
| `measurements.csv` | 05-7 | NaN, 숫자 변환 실패, 임계값 |
| `items.csv`, `large_items.csv` | 05-8 | 자료형 오류, 결측치, 청크 집계 |
| `web-access.log` | 05-9 | 정상·오탐·IPv6·CRLF·형식·의미 오류 |
| `web-access-invalid-utf8.log` | 05-9 | UTF-8 strict 디코딩 오류 |

`web-access-invalid-utf8.log`는 의도적으로 잘못된 바이트를 포함하므로 텍스트 편집기에서 재저장하지 않는다.
"""
    (FIXTURE_DIR / "README.md").write_text(fixture_readme, encoding="utf-8")

    solution_readme = """# 05장 풀이 검증용 Notebook

학습자용 Notebook의 TODO를 먼저 완성한 뒤 해당 `-solution.ipynb`와 비교한다. 이 파일은 공개 참고 구현이며 평가 정답을 숨기지 않는다. 실제 평가에서는 교수자용 비공개 테스트를 별도로 사용한다.

- 05-1~05-8: 절별 fixture의 정상·경계·오류 결과를 `assert`로 대조한다.
- 05-9: 품질 불변식, 오탐 억제, NumPy 탐지 마스크, 가명처리, 안전한 출력을 검증한다.
"""
    (SOLUTION_DIR / "README.md").write_text(solution_readme, encoding="utf-8")


def main() -> None:
    write_text_fixtures()
    write_web_log_fixtures()
    build_basic_notebooks()
    build_solution_notebooks()
    build_web_log_notebooks()
    write_readmes()
    print("05장 fixture와 Notebook 생성 완료")


if __name__ == "__main__":
    main()
