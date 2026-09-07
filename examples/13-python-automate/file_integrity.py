"""학습용 폴더의 SHA-256 기준선을 만들고 파일 변경을 보고한다."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat


def snapshot(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise ValueError("검사 폴더가 없습니다.")
    hashes = {}

    def fail(error):
        raise error

    for directory, folders, files in os.walk(root, followlinks=False, onerror=fail):
        for name in folders + files:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise ValueError(f"심볼릭 링크는 지원하지 않습니다: {path}")
            if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise ValueError(f"일반 파일/폴더가 아닙니다: {path}")
        for name in sorted(files):
            path = Path(directory) / name
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(65536), b""):
                    digest.update(chunk)
            hashes[path.relative_to(root).as_posix()] = digest.hexdigest()
    return dict(sorted(hashes.items()))


def compare(before: dict[str, str], after: dict[str, str]) -> dict[str, list[str]]:
    return {
        "added": sorted(after.keys() - before.keys()),
        "deleted": sorted(before.keys() - after.keys()),
        "modified": sorted(k for k in before.keys() & after.keys() if before[k] != after[k]),
        "unchanged": sorted(k for k in before.keys() & after.keys() if before[k] == after[k]),
    }


def load_baseline(path: Path, root: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1 or data.get("root") != str(root):
        raise ValueError("기준선 버전 또는 검사 폴더가 일치하지 않습니다.")
    hashes = data.get("sha256")
    if not isinstance(hashes, dict):
        raise ValueError("기준선 sha256 형식 오류")
    for name, digest in hashes.items():
        if (not name or name.startswith("/") or "\\" in name
                or any(part in ("", ".", "..") for part in name.split("/"))
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise ValueError("기준선 경로 또는 해시 형식 오류")
    return hashes


def write_new(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["baseline", "check"])
    parser.add_argument("root", type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--output", type=Path, help="check 결과 JSON의 새 경로")
    args = parser.parse_args(argv)
    try:
        if args.root.is_symlink():
            raise ValueError("검사 폴더에 심볼릭 링크를 사용할 수 없습니다.")
        root = args.root.resolve()
        baseline = args.baseline.resolve()
        output = args.output.resolve() if args.output else None
        for path in (baseline, output):
            if path is not None and (path == root or root in path.parents):
                raise ValueError("기준선과 결과는 검사 폴더 밖에 저장하세요.")
        if args.command == "baseline" and output:
            raise ValueError("--output은 check 명령에서만 사용합니다.")
        if args.command == "baseline":
            current = snapshot(root)
            write_new(baseline, {"version": 1, "root": str(root), "sha256": current})
            print(f"기준선 생성: {len(current)}개 파일")
            return 0
        previous = load_baseline(baseline, root)
        result = compare(previous, snapshot(root))
        if output:
            write_new(output, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if any(result[key] for key in ("added", "deleted", "modified")) else 0
    except (OSError, ValueError) as exc:
        print(f"검사 실패: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
