from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Iterable


CATEGORIES = {
    "images": {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"},
    "documents": {".docx", ".md", ".pdf", ".pptx", ".txt"},
    "data": {".csv", ".json", ".tsv", ".xlsx", ".xml"},
    "archives": {".7z", ".gz", ".rar", ".tar", ".tgz", ".zip"},
}


@dataclass(frozen=True)
class MoveOperation:
    source: str
    destination: str
    category: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_directory(path: Path, *, must_exist: bool) -> Path:
    resolved = path.expanduser().resolve()
    if must_exist and (not resolved.exists() or not resolved.is_dir()):
        raise ValueError(f"폴더를 확인할 수 없습니다: {resolved}")
    if resolved.exists() and not resolved.is_dir():
        raise ValueError(f"폴더가 아닙니다: {resolved}")
    return resolved


def category_for(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, suffixes in CATEGORIES.items():
        if suffix in suffixes:
            return category
    return "other"


def unique_destination(destination: Path, reserved: set[Path]) -> Path:
    candidate = destination
    number = 2
    while candidate.exists() or candidate in reserved:
        candidate = destination.with_name(
            f"{destination.stem}_{number}{destination.suffix}"
        )
        number += 1
    reserved.add(candidate)
    return candidate


def iter_source_files(source_root: Path, destination_root: Path) -> Iterable[Path]:
    for path in sorted(source_root.iterdir(), key=lambda item: item.name.lower()):
        if path.is_symlink() or not path.is_file():
            continue
        if path == destination_root or path.is_relative_to(destination_root):
            continue
        yield path


def build_plan(source_root: Path, destination_root: Path) -> list[MoveOperation]:
    source = resolve_directory(source_root, must_exist=True)
    destination = resolve_directory(destination_root, must_exist=False)
    if source == destination:
        raise ValueError("출발 폴더와 도착 폴더는 달라야 합니다.")

    reserved: set[Path] = set()
    operations = []
    for path in iter_source_files(source, destination):
        category = category_for(path)
        target = unique_destination(destination / category / path.name, reserved)
        if not target.resolve().is_relative_to(destination):
            raise ValueError(f"도착 경로가 작업 범위 밖입니다: {target}")
        operations.append(
            MoveOperation(
                source=str(path),
                destination=str(target),
                category=category,
            )
        )
    return operations


def plan_payload(
    source_root: Path,
    destination_root: Path,
    operations: list[MoveOperation],
) -> dict:
    counts = {category: 0 for category in [*CATEGORIES, "other"]}
    for operation in operations:
        counts[operation.category] += 1
    return {
        "source_root": str(source_root.expanduser().resolve()),
        "destination_root": str(destination_root.expanduser().resolve()),
        "total": len(operations),
        "counts": {key: value for key, value in counts.items() if value},
        "operations": [asdict(operation) for operation in operations],
    }


def write_json_atomic(payload: dict, output_path: Path) -> None:
    output = output_path.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(output)


def default_manifest_path(destination_root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return destination_root / ".automation-manifests" / f"organize-{stamp}.json"


def validate_plan_before_apply(
    operations: list[MoveOperation],
    source_root: Path,
    destination_root: Path,
) -> None:
    for operation in operations:
        raw_source = Path(operation.source)
        if raw_source.is_symlink():
            raise ValueError(f"심볼릭 링크는 이동하지 않습니다: {raw_source}")
        source = raw_source.resolve()
        destination = Path(operation.destination).resolve()
        if source.parent != source_root:
            raise ValueError(f"출발 경로가 작업 범위 밖입니다: {source}")
        if not destination.is_relative_to(destination_root):
            raise ValueError(f"도착 경로가 작업 범위 밖입니다: {destination}")
        if not source.exists() or not source.is_file():
            raise ValueError(f"출발 파일 상태가 변경되었습니다: {source}")
        if destination.exists():
            raise FileExistsError(f"도착 경로가 이미 있습니다: {destination}")


def apply_plan(
    source_root: Path,
    destination_root: Path,
    operations: list[MoveOperation],
    manifest_path: Path,
) -> Path:
    source = resolve_directory(source_root, must_exist=True)
    destination = resolve_directory(destination_root, must_exist=False)
    manifest = manifest_path.expanduser().resolve()
    if manifest.exists():
        raise FileExistsError(f"작업 기록이 이미 있습니다: {manifest}")

    validate_plan_before_apply(operations, source, destination)
    payload = {
        "version": 1,
        "action": "organize_files",
        "status": "in_progress",
        "created_at_utc": utc_now(),
        "updated_at_utc": utc_now(),
        "source_root": str(source),
        "destination_root": str(destination),
        "operations": [
            {**asdict(operation), "status": "planned"}
            for operation in operations
        ],
    }
    write_json_atomic(payload, manifest)

    try:
        for index, operation in enumerate(operations):
            source_path = Path(operation.source)
            destination_path = Path(operation.destination)
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(destination_path))
            payload["operations"][index]["status"] = "applied"
            payload["updated_at_utc"] = utc_now()
            write_json_atomic(payload, manifest)
    except Exception as exc:
        payload["status"] = "partial_failure"
        payload["error"] = f"{type(exc).__name__}: {exc}"
        payload["updated_at_utc"] = utc_now()
        write_json_atomic(payload, manifest)
        raise

    payload["status"] = "completed"
    payload["updated_at_utc"] = utc_now()
    write_json_atomic(payload, manifest)
    return manifest


def read_manifest(manifest_path: Path) -> dict:
    manifest = manifest_path.expanduser().resolve()
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"작업 기록을 읽을 수 없습니다: {manifest}") from exc
    if payload.get("version") != 1 or payload.get("action") != "organize_files":
        raise ValueError("지원하지 않는 작업 기록입니다.")
    if not isinstance(payload.get("operations"), list):
        raise ValueError("작업 기록의 operations가 잘못되었습니다.")
    return payload


def validate_undo_paths(payload: dict) -> None:
    source_root = Path(payload["source_root"]).resolve()
    destination_root = Path(payload["destination_root"]).resolve()
    for operation in payload["operations"]:
        source = Path(operation["source"]).resolve()
        destination = Path(operation["destination"]).resolve()
        if not source.is_relative_to(source_root):
            raise ValueError(f"원본 경로가 작업 범위 밖입니다: {source}")
        if not destination.is_relative_to(destination_root):
            raise ValueError(f"도착 경로가 작업 범위 밖입니다: {destination}")


def undo_manifest(manifest_path: Path) -> int:
    manifest = manifest_path.expanduser().resolve()
    payload = read_manifest(manifest)
    validate_undo_paths(payload)

    candidates = [
        operation
        for operation in reversed(payload["operations"])
        if operation.get("status") == "applied"
    ]
    for operation in candidates:
        source = Path(operation["source"])
        destination = Path(operation["destination"])
        if not destination.exists() or not destination.is_file():
            raise FileNotFoundError(f"되돌릴 파일이 없습니다: {destination}")
        if source.exists():
            raise FileExistsError(f"원본 경로가 이미 있습니다: {source}")

    restored = 0
    try:
        for operation in candidates:
            source = Path(operation["source"])
            destination = Path(operation["destination"])
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(source))
            operation["status"] = "undone"
            restored += 1
            payload["updated_at_utc"] = utc_now()
            write_json_atomic(payload, manifest)
    except Exception as exc:
        payload["status"] = "undo_partial_failure"
        payload["error"] = f"{type(exc).__name__}: {exc}"
        payload["updated_at_utc"] = utc_now()
        write_json_atomic(payload, manifest)
        raise

    payload["status"] = "undone"
    payload.pop("error", None)
    payload["updated_at_utc"] = utc_now()
    write_json_atomic(payload, manifest)
    return restored


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="미리보기와 원상복구를 지원하는 파일 정리기",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("plan", "apply"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("source", type=Path)
        command_parser.add_argument(
            "--destination",
            type=Path,
            help="기본값: SOURCE/_organized",
        )
        if command == "apply":
            command_parser.add_argument("--manifest", type=Path)

    undo_parser = subparsers.add_parser("undo")
    undo_parser.add_argument("manifest", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "undo":
            restored = undo_manifest(args.manifest)
            print(f"원상복구 완료: {restored}건")
            return 0

        source = resolve_directory(args.source, must_exist=True)
        destination = (
            args.destination.expanduser().resolve()
            if args.destination
            else source / "_organized"
        )
        operations = build_plan(source, destination)

        if args.command == "plan":
            print(
                json.dumps(
                    plan_payload(source, destination, operations),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        manifest = (
            args.manifest.expanduser().resolve()
            if args.manifest
            else default_manifest_path(destination)
        )
        saved_manifest = apply_plan(source, destination, operations, manifest)
        print(f"적용 완료: {len(operations)}건")
        print(f"작업 기록: {saved_manifest}")
        return 0
    except (FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        print(f"작업 실패: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
