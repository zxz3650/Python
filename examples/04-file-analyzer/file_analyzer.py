from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
import argparse
import codecs
import csv
import hashlib
import json
import math
import os
import re
import struct
import sys


SAMPLE_BYTES = 8192
HASH_CHUNK_SIZE = 1024 * 1024
DEFAULT_EVIDENCE_DIR = "evidence"
TEXT_EXTENSION_HINTS = {".txt", ".log", ".json", ".csv", ".xml", ".md", ".yml", ".yaml", ".ini", ".cfg", ".py"}
MIN_STRING_LENGTH = 4
ENTROPY_HIGH = 7.6
ENTROPY_MODERATE = 6.8

FILE_SIGNATURES = (
    ("PDF document", b"%PDF-", {".pdf"}, 0),
    ("PNG image", b"\x89PNG\r\n\x1a\n", {".png"}, 0),
    ("JPEG image", b"\xff\xd8\xff", {".jpg", ".jpeg"}, 0),
    ("GIF image", b"GIF8", {".gif"}, 0),
    ("ZIP archive", b"PK\x03\x04", {".zip", ".docx", ".xlsx", ".pptx", ".jar", ".apk", ".odt", ".ods"}, 0),
    ("GZIP archive", b"\x1f\x8b", {".gz", ".tgz"}, 0),
    ("ELF executable", b"\x7fELF", {".elf", ".so", ""}, 0),
    ("RAR archive", b"Rar!\x1a\x07", {".rar"}, 0),
    ("7-Zip archive", b"7z\xbc\xaf\x27\x1c", {".7z"}, 0),
    ("Mach-O binary", b"\xfe\xed\xfa\xce", {".dylib", ""}, 0),
    ("Mach-O binary", b"\xfe\xed\xfa\xcf", {".dylib", ""}, 0),
    ("Mach-O binary", b"\xce\xfa\xed\xfe", {".dylib", ""}, 0),
    ("Mach-O binary", b"\xcf\xfa\xed\xfe", {".dylib", ""}, 0),
)

URL_RE = re.compile(
    r"(?i)\b(?:(?:https?|s?ftps?)://[^\s\"'<>`|{}\\^\\[\\]();:,]+)",
    re.IGNORECASE,
)
DOMAIN_RE = re.compile(
    r"(?i)\b(?:(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,})(?::\d+)?\b"
)
IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
IPV6_RE = re.compile(r"\b(?:(?:[0-9a-f]{1,4}:){2,7}[0-9a-f]{1,4})\b", re.IGNORECASE)
WIN_PATH_RE = re.compile(r"\b(?:[A-Za-z]:|\\\\[A-Za-z0-9_.-]+\\[A-Za-z0-9_.-]+)\\(?:[^\\/\s\"'<>|:]+\\?)*[^\\/\s\"'<>|:]+\b")
POSIX_PATH_RE = re.compile(r"\b(?:/[^/\s\"'<>|:]+)+\b")
SUSPICIOUS_APIS = (
    b"LoadLibrary", b"GetProcAddress", b"CreateProcess", b"VirtualAlloc",
    b"WriteProcessMemory", b"URLDownloadToFile", b"WinExec", b"ShellExecute",
    b"socket", b"bind", b"connect", b"popen", b"subprocess", b"eval", b"exec"
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


def humanize_bytes(size_bytes: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(size_bytes)
    for unit in units:
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def calculate_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    size = len(data)
    return -sum((count / size) * math.log2(count / size) for count in counts.values())


def calculate_entropy_file(path: Path, sample_size: int = 2 * 1024 * 1024) -> float:
    size = 0
    digest = bytearray()
    with path.open("rb") as file:
        chunk = file.read(sample_size)
        size = len(chunk)
        if size == 0:
            return 0.0
        digest.extend(chunk)
    return calculate_entropy(bytes(digest))


def collect_stat_snapshot(path: Path) -> dict:
    stat = path.stat()
    return {
        "size": stat.st_size,
        "mode": stat.st_mode,
        "inode": stat.st_ino,
        "mtime_ns": stat.st_mtime_ns,
        "ctime_ns": stat.st_ctime_ns,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "uid": getattr(stat, "st_uid", None),
        "gid": getattr(stat, "st_gid", None),
    }


def compare_stats(before: dict, after: dict) -> tuple[bool, list[str]]:
    changed = []
    for key in ("size", "mode", "inode", "mtime_ns", "ctime_ns"):
        if before.get(key) != after.get(key):
            changed.append(key)
    return (len(changed) > 0), changed


def has_pe_signature(path: Path, header: bytes) -> bool:
    if not header.startswith(b"MZ") or len(header) < 64:
        return False

    pe_offset = int.from_bytes(header[0x3C:0x40], byteorder="little")
    if pe_offset <= 0 or pe_offset > path.stat().st_size - 4:
        return False

    with path.open("rb") as file:
        file.seek(pe_offset)
        return file.read(4) == b"PE\x00\x00"


def identify_file_type(path: Path, header: bytes) -> dict:
    suffix = path.suffix.lower()
    detected_format = "unknown"
    mime = "application/octet-stream"
    expected_extensions = set[str]()
    signature_offset = None

    if has_pe_signature(path, header):
        detected_format = "Windows PE executable"
        mime = "application/x-dosexec"
        expected_extensions = {".exe", ".dll", ".sys", ".scr", ".drv", ".ocx", ".msi"}
        signature_offset = 0
    else:
        for name, signature, extensions, offset in FILE_SIGNATURES:
            if header[offset:offset + len(signature)] == signature:
                detected_format = name
                mime = (
                    "application/pdf" if name.startswith("PDF")
                    else "image/png" if "PNG" in name
                    else "image/jpeg" if "JPEG" in name
                    else "image/gif" if "GIF" in name
                    else "application/zip"
                    if "ZIP" in name or "7-Zip" in name
                    else "application/x-elf"
                    if "ELF" in name
                    else "application/x-mach-binary"
                    if "Mach-O" in name
                    else "application/octet-stream"
                )
                expected_extensions = extensions
                signature_offset = offset
                break

    extension_matches = (
        suffix in expected_extensions
        if expected_extensions
        else None
    )

    return {
        "detected_format": detected_format,
        "mime": mime,
        "expected_extensions": sorted(expected_extensions),
        "extension_matches": extension_matches,
        "signature_offset": signature_offset,
        "header_hex": header[:16].hex(" "),
        "match": {
            "status": "YES" if extension_matches else "NO",
            "reason": None if extension_matches is not False else f"확장자 {suffix or '(없음)'}와 식별된 형식이 다릅니다."
        },
    }


def detect_text_and_encoding(path: Path, sample: bytes) -> dict:
    if sample.startswith(codecs.BOM_UTF8):
        return {"content_type": "text", "encoding": "utf-8-sig", "encoding_confidence": "bom"}
    if sample.startswith(codecs.BOM_UTF16_LE):
        return {"content_type": "text", "encoding": "utf-16-le", "encoding_confidence": "bom"}
    if sample.startswith(codecs.BOM_UTF16_BE):
        return {"content_type": "text", "encoding": "utf-16-be", "encoding_confidence": "bom"}
    if sample.startswith(codecs.BOM_UTF32_LE):
        return {"content_type": "text", "encoding": "utf-32-le", "encoding_confidence": "bom"}
    if sample.startswith(codecs.BOM_UTF32_BE):
        return {"content_type": "text", "encoding": "utf-32-be", "encoding_confidence": "bom"}

    if len(sample) == 0:
        return {"content_type": "text", "encoding": "utf-8", "encoding_confidence": "empty"}

    # UTF-16 휴리스틱 판별: 데이터 대부분이 ASCII 문자와 NUL 바이트의 반복인 경우다.
    zero_ratio = sample.count(b"\x00") / len(sample)
    if zero_ratio > 0.35:
        try:
            sample.decode("utf-16-le")
            return {"content_type": "text", "encoding": "utf-16-le", "encoding_confidence": "heuristic-16le"}
        except UnicodeDecodeError:
            pass
        try:
            sample.decode("utf-16-be")
            return {"content_type": "text", "encoding": "utf-16-be", "encoding_confidence": "heuristic-16be"}
        except UnicodeDecodeError:
            pass

    try:
        sample.decode("utf-8")
        return {"content_type": "text", "encoding": "utf-8", "encoding_confidence": "heuristic-utf8"}
    except UnicodeDecodeError:
        pass

    if all(
        byte in range(9, 14)
        or byte in (32, 9, 10, 13)
        or (32 <= byte <= 126)
        for byte in sample
    ):
        return {"content_type": "text", "encoding": "latin-1", "encoding_confidence": "ascii-compatible"}

    return {"content_type": "binary", "encoding": None, "encoding_confidence": "binary"}


def analyze_text(path: Path, encoding: str) -> dict:
    line_count = 0
    blank_line_count = 0
    max_line_length = 0
    char_count = 0

    with path.open("r", encoding=encoding, errors="replace") as file:
        for line in file:
            line_count += 1
            clean_line = line.rstrip("\r\n")
            if not clean_line.strip():
                blank_line_count += 1
            max_line_length = max(max_line_length, len(clean_line))
            char_count += len(clean_line)

    return {
        "line_count": line_count,
        "blank_line_count": blank_line_count,
        "max_line_length": max_line_length,
        "char_count": char_count,
    }


def analyze_csv(path: Path, encoding: str) -> dict:
    row_count = 0
    max_column_count = 0
    rows_with_missing_values = 0
    rows_with_wrong_column_count = 0
    header = []

    with path.open("r", encoding=encoding, newline="", errors="replace") as file:
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


def analyze_json(path: Path, encoding: str) -> dict:
    with path.open("r", encoding=encoding, errors="replace") as file:
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


def _extract_strings_from_bytes(data: bytes, encoding: str) -> list[str]:
    if encoding == "ascii":
        pattern = re.compile(rb"[ -~]{%d,}" % MIN_STRING_LENGTH)
        return [m.group(0).decode("ascii", errors="ignore") for m in pattern.finditer(data)]
    decoded = data.decode(encoding, errors="ignore")
    pattern = re.compile(r"[ -~]{%d,}" % MIN_STRING_LENGTH)
    return [match.group(0) for match in pattern.finditer(decoded)]


def analyze_strings_and_iocs(path: Path) -> dict:
    with path.open("rb") as file:
        data = file.read()

    ascii_strings = _extract_strings_from_bytes(data, "ascii")
    utf16le_strings = _extract_strings_from_bytes(data, "utf-16-le")
    utf16be_strings = _extract_strings_from_bytes(data, "utf-16-be")

    # 상위 200개만 사용해 성능 안정화
    all_strings = []
    for value in ascii_strings + utf16le_strings + utf16be_strings:
        if value not in all_strings:
            all_strings.append(value)
            if len(all_strings) >= 500:
                break

    text_blob = "\n".join(all_strings)
    urls = sorted(set(URL_RE.findall(text_blob)))
    domains = sorted(set(DOMAIN_RE.findall(text_blob)))
    iocs = {
        "urls": sorted(set(URL_RE.findall(text_blob))),
        "ipv4": sorted(set(IPV4_RE.findall(text_blob))),
        "ipv6": sorted(set(IPV6_RE.findall(text_blob))),
        "domains": sorted(set(DOMAINS.strip() for DOMAINS in domains if "." in DOMAINS)),
        "paths": sorted(
            set(
                WIN_PATH_RE.findall(text_blob)
                + POSIX_PATH_RE.findall(text_blob)
            )
        ),
    }

    suspicious_api_hits = sorted(
        {
            api.decode("ascii", errors="ignore")
            for api in SUSPICIOUS_APIS
            if api.decode("ascii", errors="ignore").lower() in text_blob.lower()
        }
    )

    return {
        "string_count": len(all_strings),
        "sample_strings": all_strings[:50],
        "ioc": {
            **iocs,
            "suspicious_api_hits": suspicious_api_hits,
        },
        "ioc_count": sum(len(v) for v in iocs.values()) + len(suspicious_api_hits),
    }


def parse_pe_structure(path: Path) -> dict:
    with path.open("rb") as file:
        header = file.read(4096)

    if not has_pe_signature(path, header):
        return {"parseable": False, "reason": "PE signature not found"}

    with path.open("rb") as file:
        file.seek(0x3C)
        pe_offset = int.from_bytes(file.read(4), byteorder="little")
        file.seek(pe_offset)
        if file.read(4) != b"PE\x00\x00":
            return {"parseable": False, "reason": "PE signature mismatch"}

        coff = file.read(20)
        if len(coff) < 20:
            return {"parseable": False, "reason": "COFF too short"}
        machine, number_of_sections, timestamp, _, _, size_opt_header, characteristics = struct.unpack("<HHIIIHH", coff)

        opt = file.read(size_opt_header)
        if len(opt) < 24:
            return {"parseable": False, "reason": "Optional header too short"}

        magic = struct.unpack("<H", opt[:2])[0]
        if magic not in (0x10B, 0x20B):
            return {"parseable": False, "reason": "Unknown PE optional header"}

        file.seek(pe_offset + 4 + 24 + 16)
        address_of_entry_point = struct.unpack("<I", file.read(4))[0]
        file.seek(pe_offset + 4 + 24 + 28 if magic == 0x10B else pe_offset + 4 + 24 + 28)
        image_base = struct.unpack("<Q" if magic == 0x20B else "<I", file.read(8 if magic == 0x20B else 4))[0]

        # IMAGE_OPTIONAL_HEADER32 필드 오프셋: ImageBase 28, AddressOfEntryPoint 16, Subsystem 68, DllCharacteristics 70
        # IMAGE_OPTIONAL_HEADER64 필드 오프셋: ImageBase 24, AddressOfEntryPoint 16, Subsystem 80, DllCharacteristics 82
        subsystem_offset = 68 if magic == 0x10B else 80
        dll_characteristics_offset = 70 if magic == 0x10B else 82
        number_of_rva_and_sizes_offset = 92 if magic == 0x10B else 108

        file.seek(pe_offset + 4 + 24 + subsystem_offset)
        subsystem = struct.unpack("<H", file.read(2))[0]
        file.seek(pe_offset + 4 + 24 + dll_characteristics_offset)
        dll_characteristics = struct.unpack("<H", file.read(2))[0]
        file.seek(pe_offset + 4 + 24 + number_of_rva_and_sizes_offset)
        number_of_rva_and_sizes = struct.unpack("<I", file.read(4))[0]

        # 인증서 테이블(보안 디렉터리)
        # 데이터 디렉터리 시작 위치: PE32는 96바이트, PE32+는 112바이트이며 보안 디렉터리 인덱스는 4다.
        opt_offset = pe_offset + 4 + 24
        cert_offset = (
            opt_offset + (96 + (4 * 8)) if magic == 0x10B else opt_offset + (112 + (4 * 8))
        )
        has_signature = False
        cert_size = 0
        if len(opt) >= cert_offset - opt_offset + 8:
            file.seek(cert_offset)
            cert_rva = struct.unpack("<I", file.read(4))[0]
            cert_size = struct.unpack("<I", file.read(4))[0]
            has_signature = cert_size > 0 and cert_rva > 0

        machine_map = {
            0x014C: "x86",
            0x8664: "x64",
            0xAA64: "ARM64",
            0x01C4: "ARMv7",
        }

        subsystem_map = {
            1: "native",
            2: "gui",
            3: "cui",
            9: "windows_cui",
            10: "windows_gui",
            16: "efi_application",
            17: "efi_boot_service_driver",
        }

        dll_characteristics_map = {
            0x0020: "dynamic_base",
            0x0040: "force_integrity",
            0x0080: "nx_compat",
            0x0100: "no_isolation",
            0x0200: "no_seh",
            0x0400: "no_bind",
            0x0800: "wmd_call",
            0x1000: "terminal_server",
            0x2000: "gdsm",
            0x4000: "caf",
        }

        flags = [
            name
            for value, name in dll_characteristics_map.items()
            if dll_characteristics & value
        ]

    return {
        "parseable": True,
        "machine": machine_map.get(machine, f"unknown(0x{machine:04x})"),
        "number_of_sections": number_of_sections,
        "timestamp_utc": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
        "image_type": "PE32+" if magic == 0x20B else "PE32",
        "address_of_entry_point": address_of_entry_point,
        "image_base": image_base,
        "subsystem": subsystem_map.get(subsystem, str(subsystem)),
        "dll_characteristics": flags,
        "characteristics": characteristics,
        "number_of_data_directories": number_of_rva_and_sizes,
        "image_base_offset": opt_offset + (0x18 if magic == 0x20B else 0x1C),
        "digital_signature_present": has_signature,
        "certificate_size": cert_size,
        "size_of_optional_header": size_opt_header,
    }


def parse_elf_structure(path: Path) -> dict:
    with path.open("rb") as file:
        header = file.read(64)

    if len(header) < 16 or not header.startswith(b"\x7fELF"):
        return {"parseable": False, "reason": "ELF signature not found"}

    ei_class = header[4]
    ei_data = header[5]
    ei_version = header[6]

    if ei_class not in (1, 2):
        return {"parseable": False, "reason": "Unknown ELF class"}

    endian = "<" if ei_data == 1 else ">"

    if len(header) < 64:
        return {"parseable": False, "reason": "ELF header too short"}

    if ei_class == 1:
        # ELF32 헤더에서 e_type, e_machine, e_version, e_entry 등의 필드를 읽는다.
        values = struct.unpack(f"{endian}HHIIIIIHHHHHH", header[16:52])
        e_type = values[0]
        machine = values[1]
        e_version = values[2]
        entry = values[3]
    else:
        # ELF64 헤더에서 e_type, e_machine, e_version, e_entry 등의 필드를 읽는다.
        values = struct.unpack(f"{endian}HHIQQQIHHHHHH", header[16:64])
        e_type = values[0]
        machine = values[1]
        e_version = values[2]
        entry = values[3]

    class_map = {1: "ELF32", 2: "ELF64"}
    data_map = {1: "LSB", 2: "MSB"}
    type_map = {
        0: "NONE",
        1: "REL",
        2: "EXEC",
        3: "DYN",
        4: "CORE",
    }
    machine_map = {
        0x03: "x86",
        0x3E: "x86_64",
        0xB7: "AArch64",
        0x28: "ARM",
    }

    return {
        "parseable": True,
        "class": class_map.get(ei_class, str(ei_class)),
        "endian": data_map.get(ei_data, str(ei_data)),
        "abi_version": ei_version,
        "type": type_map.get(e_type, str(e_type)),
        "machine": machine_map.get(machine, f"unknown(0x{machine:04x})"),
        "entry_point": entry,
        "version": e_version,
    }


def detect_risk(report: dict, structure: dict) -> dict:
    score = 0
    reasons = []

    if report["file_type"]["extension_matches"] is False:
        score += 25
        reasons.append("확장자와 실제 파일 형식이 일치하지 않습니다.")

    content_type = report["content_type"]
    if content_type == "binary":
        score += 5

    high_entropy = report["entropy"]["overall"] >= ENTROPY_HIGH
    if high_entropy:
        score += 25
        reasons.append("높은 엔트로피 영역 존재")
    elif report["entropy"]["overall"] >= ENTROPY_MODERATE:
        score += 10
        reasons.append("중간 이상 엔트로피 값")

    if report["file_type"]["detected_format"] == "Windows PE executable":
        score += 20
        reasons.append("실행 가능한 PE 파일")
        if structure and structure.get("digital_signature_present") is False:
            score += 10
            reasons.append("디지털 서명 없음")

    if report["file_type"]["detected_format"] == "ELF executable":
        score += 20
        reasons.append("실행 가능한 ELF 파일")

    ioc_count = report.get("strings", {}).get("ioc_count", 0)
    if ioc_count:
        score += 10
        reasons.append("IOC 패턴 탐지")

    suspicious_api_count = len(report.get("strings", {}).get("ioc", {}).get("suspicious_api_hits", []))
    if suspicious_api_count:
        score += 25
        reasons.append("의심 API 호출 단서 탐지")

    if report.get("mutation", {}).get("detected", False):
        score += 30
        reasons.append("분석 전후 stat 변경(증거 변조 의심)")

    if score >= 80:
        level = "HIGH"
    elif score >= 45:
        level = "MEDIUM"
    else:
        level = "LOW"

    if not reasons:
        reasons.append("현재 기준으로 즉시 실행 위험 신호는 제한적입니다.")

    actions = {
        "LOW": [
            "격리 환경에서 1차 확인을 진행하세요.",
        ],
        "MEDIUM": [
            "실행하지 말고 샌드박스에서 동적 분석 수행을 고려하세요.",
            "해시 기반 평판(IOC) 조회를 권고합니다.",
        ],
        "HIGH": [
            "즉시 실행 중단 후 격리하세요.",
            "SHA256 기반 평판 조회 및 디지털 포렌식 추가 분석 필요.",
            "의심 IOC 및 프로세스 행위를 추가 추적하세요.",
        ],
    }

    return {
        "level": level,
        "score": score,
        "reasons": reasons,
        "recommended_actions": actions[level],
    }


def analyze_file(path: Path, baseline_map: dict[str, dict] | None = None) -> dict:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"파일이 없습니다: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"일반 파일이 아닙니다: {resolved}")

    pre_snapshot = collect_stat_snapshot(resolved)
    with resolved.open("rb") as file:
        file_head = file.read(max(4096, SAMPLE_BYTES))
        header = file_head[:4096]
        sample = file_head[:SAMPLE_BYTES]

    classification = detect_text_and_encoding(resolved, sample)
    file_type = identify_file_type(resolved, header)

    base_report = {
        "schema_version": "1.1",
        "analysis_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "path": str(resolved),
        "name": resolved.name,
        "suffix": resolved.suffix.lower(),
        "size_bytes": pre_snapshot["size"],
        "size_human": humanize_bytes(pre_snapshot["size"]),
        "sha256": calculate_sha256(resolved),
        "file_type": file_type,
        "content_type": classification["content_type"],
        "encoding": classification["encoding"],
        "encoding_confidence": classification["encoding_confidence"],
    }

    if classification["content_type"] == "text":
        analysis_encoding = classification["encoding"] or "utf-8"
        base_report["text"] = analyze_text(resolved, analysis_encoding)

        try:
            if resolved.suffix.lower() == ".csv":
                base_report["format"] = {"csv": analyze_csv(resolved, analysis_encoding)}
            elif resolved.suffix.lower() == ".json":
                base_report["format"] = {"json": analyze_json(resolved, analysis_encoding)}
        except (csv.Error, json.JSONDecodeError, JSONPolicyError, UnicodeDecodeError) as exc:
            base_report["format_error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
            }
    else:
        base_report["analysis_note"] = "텍스트로 확인되지 않아 내용 분석을 생략했습니다."

    strings = analyze_strings_and_iocs(resolved)
    base_report["strings"] = strings
    base_report["entropy"] = {
        "overall": round(calculate_entropy_file(resolved), 3)
    }

    if file_type["detected_format"] == "Windows PE executable":
        base_report["pe"] = parse_pe_structure(resolved)
    elif file_type["detected_format"] == "ELF executable":
        base_report["elf"] = parse_elf_structure(resolved)

    post_snapshot = collect_stat_snapshot(resolved)
    mutated, mutation_fields = compare_stats(pre_snapshot, post_snapshot)
    base_report["mutation"] = {
        "pre": pre_snapshot,
        "post": post_snapshot,
        "detected": mutated,
        "changed_fields": mutation_fields,
    }

    base_report["baseline_comparison"] = {"matched": True, "missing": None, "changed_fields": []}
    if baseline_map:
        key = str(resolved)
        if key in baseline_map:
            baseline_before = baseline_map[key]
            compared, fields = compare_stats(baseline_before, pre_snapshot)
            base_report["baseline_comparison"] = {
                "matched": not compared,
                "missing": False,
                "changed_fields": fields,
            }
        else:
            base_report["baseline_comparison"] = {"matched": False, "missing": True, "changed_fields": []}

    base_report["risk"] = detect_risk(base_report, base_report.get("pe") or base_report.get("elf"))

    return base_report


def validate_report(report: object) -> None:
    if not isinstance(report, dict):
        raise TypeError("보고서 최상위 값은 JSON 객체여야 합니다")

    required_keys = {
        "analysis_timestamp_utc",
        "path",
        "name",
        "size_bytes",
        "sha256",
        "file_type",
        "content_type",
        "risk",
    }
    missing_keys = required_keys - report.keys()
    if missing_keys:
        names = ", ".join(sorted(missing_keys))
        raise ValueError(f"보고서 필수 필드가 없습니다: {names}")

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


def load_baseline(path: Path | None) -> dict[str, dict]:
    if not path:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"기준 파일이 없습니다: {path}")
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    snapshots = {}
    if isinstance(data, dict) and "snapshots" in data and isinstance(data["snapshots"], dict):
        snapshots = data["snapshots"]
    elif isinstance(data, dict):
        snapshots = {key: value for key, value in data.items() if isinstance(value, dict)}
    return snapshots


def build_output_path(
    target: Path,
    evidence_root: Path,
    anchor: Path | None,
) -> Path:
    evidence_root = evidence_root.expanduser().resolve()
    report_root = evidence_root / "analysis_reports"

    if anchor and target.is_relative_to(anchor):
        try:
            rel = target.relative_to(anchor)
            destination = report_root / rel.parent
            return destination / (target.name + ".analysis.json")
        except ValueError:
            pass
    return report_root / (target.name + ".analysis.json")


def print_summary(report: dict, report_path: Path) -> None:
    file_type = report["file_type"]
    match_status = file_type["match"]["status"]
    risk = report["risk"]
    print("=" * 50)
    print("File Analysis Result")
    print("=" * 50)
    print(f"File        : {report['name']}")
    print(f"Size        : {report['size_human']}")
    print(f"SHA256      : {report['sha256']}")
    print("")
    print(f"Detected    : {file_type['detected_format']}")
    print(f"Extension   : {report['suffix'] or '(없음)'}")
    print(f"Match       : {match_status}")
    if file_type["match"]["reason"]:
        print("")
        print("[!] WARNING")
        print(f"  {file_type['match']['reason']}")
    print("")
    print(f"Content     : {'Text' if report['content_type']=='text' else 'Binary'}")
    print(f"Risk        : {risk['level']}")
    print("")
    print(f"Report:")
    print(f"{report_path.name}")
    print("=" * 50)
    print(f"Risk: {risk['level']}")
    print("Reasons:")
    for reason in risk["reasons"]:
        print(f"- {reason}")
    print("Recommended action:")
    for action in risk["recommended_actions"]:
        print(f"- {action}")


def find_files(target: Path, recursive: bool) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        raise ValueError("파일 또는 디렉터리 경로여야 합니다.")

    iterator = target.rglob("*") if recursive else target.glob("*")
    return [path for path in iterator if path.is_file()]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = ArgumentParser(description="파일 기초 분석 리포트 생성 도구")
    parser.add_argument("path", nargs="?", help="분석 대상 파일 또는 폴더")
    parser.add_argument(
        "--evidence-dir",
        dest="evidence_dir",
        type=Path,
        default=Path(DEFAULT_EVIDENCE_DIR),
        help="분석 결과 저장 폴더 (입력 대상과 분리)",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="분석 전 비교용 stat 스냅샷 JSON(선택)",
    )
    parser.add_argument(
        "--non-recursive",
        action="store_true",
        help="폴더 분석 시 하위 디렉터리를 재귀 탐색하지 않음",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    raw_path = args.path
    if not raw_path:
        raw_path = input("분석할 파일 또는 폴더 경로: ").strip()
        if not raw_path:
            print("경로를 입력해야 합니다.")
            return 1

    target = Path(raw_path).expanduser().resolve()
    recursive = not args.non_recursive
    evidence_root = args.evidence_dir.expanduser().resolve()

    try:
        baseline_map = load_baseline(args.baseline)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"기준 파일 로드 실패: {exc}")
        return 1

    try:
        targets = find_files(target, recursive=recursive)
    except (OSError, ValueError) as exc:
        print(f"분석 대상 확인 실패: {exc}")
        return 1

    if not targets:
        print("분석할 파일이 없습니다.")
        return 1

    analyzed_files: list[dict] = []
    for file_path in targets:
        try:
            report = analyze_file(file_path, baseline_map=baseline_map)
            report_path = build_output_path(file_path, evidence_root, anchor=target if target.is_dir() else None)
            ensure_different_paths(file_path, report_path)
            save_report(report, report_path)
            analyzed_files.append({"path": str(file_path), "report": str(report_path), "risk": report["risk"]["level"]})
            print_summary(report, report_path)
        except (OSError, RuntimeError, UnicodeError, ValueError, TypeError) as exc:
            print(f"{file_path}: 분석 실패({exc})")
            analyzed_files.append({"path": str(file_path), "error": str(exc)})

    manifest_path = evidence_root / "analysis_manifest.json"
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "target": str(target),
        "evidence_dir": str(evidence_root),
        "files": analyzed_files,
    }
    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2, ensure_ascii=False)

    print(f"총 분석 파일: {len(analyzed_files)}")
    print(f"보고서 인벤토리: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
