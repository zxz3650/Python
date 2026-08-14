from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json


SAMPLE_BYTES = 8192
HASH_CHUNK_SIZE = 1024 * 1024


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def classify_content(path: Path) -> dict:
    with path.open("rb") as file:
        sample = file.read(SAMPLE_BYTES)

    if b"\x00" in sample:
        return {"content_type": "binary", "encoding": None}

    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return {"content_type": "unknown", "encoding": None}

    return {"content_type": "text", "encoding": "utf-8"}


def analyze_text(path: Path) -> dict:
    line_count = 0
    blank_line_count = 0
    max_line_length = 0

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line_count += 1
            clean_line = line.rstrip("\r\n")
            if not clean_line.strip():
                blank_line_count += 1
            max_line_length = max(max_line_length, len(clean_line))

    return {
        "line_count": line_count,
        "blank_line_count": blank_line_count,
        "max_line_length": max_line_length,
    }


def analyze_csv(path: Path) -> dict:
    row_count = 0
    max_column_count = 0
    rows_with_missing_values = 0
    header = []

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        header = next(reader, [])

        for row in reader:
            row_count += 1
            max_column_count = max(max_column_count, len(row))
            if not row or any(not value.strip() for value in row):
                rows_with_missing_values += 1

    return {
        "header": header,
        "data_row_count": row_count,
        "header_column_count": len(header),
        "max_data_column_count": max_column_count,
        "rows_with_missing_values": rows_with_missing_values,
    }


def analyze_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)

    result = {"top_level_type": type(value).__name__}
    if isinstance(value, dict):
        result["top_level_key_count"] = len(value)
        result["top_level_keys"] = list(value)[:20]
    elif isinstance(value, list):
        result["item_count"] = len(value)
    return result


def analyze_file(path: Path) -> dict:
    resolved = path.expanduser().resolve()

    if not resolved.exists():
        raise FileNotFoundError(f"파일이 없습니다: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"일반 파일이 아닙니다: {resolved}")

    stat = resolved.stat()
    classification = classify_content(resolved)
    report = {
        "path": str(resolved),
        "name": resolved.name,
        "suffix": resolved.suffix.lower(),
        "size_bytes": stat.st_size,
        "modified_at_utc": datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        ).isoformat(),
        "sha256": calculate_sha256(resolved),
        **classification,
    }

    if classification["content_type"] != "text":
        report["analysis"] = {
            "note": "텍스트로 확인되지 않아 내용 분석을 생략했습니다."
        }
        return report

    report["text"] = analyze_text(resolved)

    try:
        if resolved.suffix.lower() == ".csv":
            report["format"] = {"csv": analyze_csv(resolved)}
        elif resolved.suffix.lower() == ".json":
            report["format"] = {"json": analyze_json(resolved)}
    except (csv.Error, json.JSONDecodeError) as exc:
        report["format_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    return report


def save_report(report: dict, output_path: Path) -> None:
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary_path.replace(output_path)


def main() -> int:
    raw_path = input("분석할 파일 경로: ").strip()
    if not raw_path:
        print("파일 경로를 입력해야 합니다.")
        return 1

    input_path = Path(raw_path)

    try:
        report = analyze_file(input_path)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, ValueError) as exc:
        print(f"분석 실패: {exc}")
        return 1

    output_path = input_path.with_name(input_path.name + ".analysis.json")
    save_report(report, output_path)
    print(f"분석 완료: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
