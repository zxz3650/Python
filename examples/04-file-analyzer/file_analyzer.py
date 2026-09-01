from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
import csv
import hashlib
import json
import os


SAMPLE_BYTES = 8192
HASH_CHUNK_SIZE = 1024 * 1024

FILE_SIGNATURES = (
    ("PDF document", b"%PDF-", {".pdf"}),
    ("PNG image", b"\x89PNG\r\n\x1a\n", {".png"}),
    ("JPEG image", b"\xff\xd8\xff", {".jpg", ".jpeg"}),
    ("GIF image", b"GIF8", {".gif"}),
    ("ZIP archive", b"PK\x03\x04", {
        ".zip", ".docx", ".xlsx", ".pptx", ".jar", ".apk"
    }),
    ("GZIP archive", b"\x1f\x8b", {".gz", ".tgz"}),
    ("ELF executable", b"\x7fELF", {".elf", ".so", ""}),
    ("RAR archive", b"Rar!\x1a\x07", {".rar"}),
    ("7-Zip archive", b"7z\xbc\xaf\x27\x1c", {".7z"}),
    ("Mach-O binary", b"\xfe\xed\xfa\xce", {".dylib", ""}),
    ("Mach-O binary", b"\xfe\xed\xfa\xcf", {".dylib", ""}),
    ("Mach-O binary", b"\xce\xfa\xed\xfe", {".dylib", ""}),
    ("Mach-O binary", b"\xcf\xfa\xed\xfe", {".dylib", ""}),
)


class JSONPolicyError(ValueError):
    """JSON 문법은 맞지만 입력 정책을 위반한 경우다."""


def reject_nonstandard_constant(value: str) -> None:
    raise JSONPolicyError(f"표준 JSON 숫자가 아닙니다: {value}")


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise JSONPolicyError(f"중복 JSON 키입니다: {key}")
        result[key] = value
    return result


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def has_pe_signature(path: Path, header: bytes) -> bool:
    if not header.startswith(b"MZ") or len(header) < 64:
        return False

    pe_offset = int.from_bytes(header[0x3C:0x40], byteorder="little")
    if pe_offset <= 0 or pe_offset > path.stat().st_size - 4:
        return False

    with path.open("rb") as file:
        file.seek(pe_offset)
        return file.read(4) == b"PE\x00\x00"


def identify_file_header(path: Path) -> dict:
    with path.open("rb") as file:
        header = file.read(4096)

    name = "unknown"
    expected_extensions = set()

    if has_pe_signature(path, header):
        name = "Windows PE executable"
        expected_extensions = {".exe", ".dll", ".sys", ".scr"}
    else:
        for signature_name, magic, extensions in FILE_SIGNATURES:
            if header.startswith(magic):
                name = signature_name
                expected_extensions = extensions
                break

    suffix = path.suffix.lower()
    extension_matches = (
        suffix in expected_extensions
        if expected_extensions
        else None
    )

    result = {
        "detected_format": name,
        "header_hex": header[:16].hex(" "),
        "expected_extensions": sorted(expected_extensions),
        "extension_matches": extension_matches,
    }

    if extension_matches is False:
        result["warning"] = (
            f"확장자 {suffix or '(없음)'}와 "
            "식별된 파일 형식이 다릅니다."
        )

    return result


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
    rows_with_wrong_column_count = 0
    header = []

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file, strict=True)
        header = next(reader, [])

        for row in reader:
            row_count += 1
            max_column_count = max(max_column_count, len(row))
            if not row or any(not value.strip() for value in row):
                rows_with_missing_values += 1
            if len(row) != len(header):
                rows_with_wrong_column_count += 1

    return {
        "header": header,
        "data_row_count": row_count,
        "header_column_count": len(header),
        "max_data_column_count": max_column_count,
        "rows_with_missing_values": rows_with_missing_values,
        "rows_with_wrong_column_count": rows_with_wrong_column_count,
    }


def analyze_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        value = json.load(
            file,
            parse_constant=reject_nonstandard_constant,
            object_pairs_hook=reject_duplicate_keys,
        )

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
        "file_header": identify_file_header(resolved),
        **classification,
    }

    if classification["content_type"] != "text":
        report["analysis"] = {
            "note": (
                "텍스트로 확인되지 않아 "
                "내용 분석을 생략했습니다."
            )
        }
        return report

    report["text"] = analyze_text(resolved)

    try:
        if resolved.suffix.lower() == ".csv":
            report["format"] = {"csv": analyze_csv(resolved)}
        elif resolved.suffix.lower() == ".json":
            report["format"] = {"json": analyze_json(resolved)}
    except (csv.Error, json.JSONDecodeError, JSONPolicyError) as exc:
        report["format_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    return report


def validate_report(report: object) -> None:
    if not isinstance(report, dict):
        raise TypeError("보고서 최상위 값은 JSON 객체여야 합니다")

    required_keys = {
        "path",
        "name",
        "size_bytes",
        "sha256",
        "file_header",
        "content_type",
    }
    missing_keys = required_keys - report.keys()
    if missing_keys:
        names = ", ".join(sorted(missing_keys))
        raise ValueError(f"보고서 필수 필드가 없습니다: {names}")

    if not isinstance(report["file_header"], dict):
        raise TypeError("file_header는 JSON 객체여야 합니다")
    sha256_value = report["sha256"]
    if (
        not isinstance(sha256_value, str)
        or len(sha256_value) != 64
        or any(character not in "0123456789abcdef" for character in sha256_value)
    ):
        raise ValueError("sha256은 64자리 16진수 문자열이어야 합니다")
    if report["content_type"] not in {"text", "binary", "unknown"}:
        raise ValueError("지원하지 않는 content_type입니다")


def ensure_different_paths(input_path: Path, output_path: Path) -> None:
    source = input_path.expanduser().resolve()
    destination = output_path.expanduser().resolve()

    if source == destination:
        raise ValueError("입력과 출력 경로는 달라야 합니다")
    if source.exists() and destination.exists() and source.samefile(destination):
        raise ValueError("입력과 출력이 같은 파일을 가리킵니다")


def save_report(report: dict, output_path: Path) -> None:
    validate_report(report)
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(
                report,
                temporary,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())

        with temporary_path.open("r", encoding="utf-8") as file:
            restored = json.load(file)
        validate_report(restored)

        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    raw_path = input("분석할 파일 경로: ").strip()
    if not raw_path:
        print("파일 경로를 입력해야 합니다.")
        return 1

    try:
        input_path = Path(raw_path).expanduser().resolve()
        report = analyze_file(input_path)
    except (OSError, RuntimeError, UnicodeDecodeError, ValueError) as exc:
        print(f"분석 실패: {exc}")
        return 1

    output_path = input_path.with_name(input_path.name + ".analysis.json")
    try:
        ensure_different_paths(input_path, output_path)
        save_report(report, output_path)

        with output_path.open("r", encoding="utf-8") as file:
            restored = json.load(file)
        validate_report(restored)
    except (OSError, TypeError, ValueError) as exc:
        print(f"보고서 저장 실패: {exc}")
        return 1

    print(f"분석 완료: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
