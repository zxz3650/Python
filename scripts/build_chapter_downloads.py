"""현재 교안의 실습 자료를 장별 ZIP으로 생성하고 배포본의 최신 상태를 검사한다."""

from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "downloads"
CHAPTERS = {
    "01": "Python 소개",
    "02": "개발 및 실습 환경",
    "03": "Python 기초 문법",
    "04": "파일 입출력과 데이터 형식",
    "05": "텍스트 파싱과 데이터 분석",
    "06": "네트워크 프로그래밍",
    "07": "HTTP와 API",
    "08": "시스템 자동화",
    "09": "테스트와 디버깅",
    "10": "프로그램 구조화",
    "11": "동시성과 비동기 처리",
    "12": "Python 활용 종합 프로젝트",
    "13": "Python Automate 실무 자동화",
}
# 다른 장의 실행 코드가 필요하면 이 목록에 해당 의존성을 명시한다.
EXTRA_PATHS = {
    "03": ("examples/03-9-event-review-starter",),
    "04": ("examples/04-file-analyzer",),
    "05": ("fixtures/05-text-processing", "notebooks/solutions"),
    "06": ("examples/06-network-echo",),
    "07": ("examples/07-local-web-security-lab",),
    "08": ("examples/08-toolization-project", "examples/07-local-web-security-lab"),
    "13": ("examples/13-kape-triage", "tests/test_kape_pipeline.py"),
}
EXTRA_REQUIREMENTS = {
    "05": ("numpy>=2", "pandas>=2"),
    "07": ("requests>=2.32,<3",),
    "08": ("requests>=2.32,<3",),
    "09": ("pytest>=8,<9",),
}
IGNORE_PARTS = {"__pycache__", ".ipynb_checkpoints", ".pytest_cache", ".DS_Store"}
SOURCE_SUFFIXES = {".py", ".md", ".ipynb", ".csv", ".json", ".jsonl", ".txt", ".log"}
RAW_BASE = "https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/"


def json_bytes(value: object) -> bytes:
    """항목 순서가 고정된 UTF-8 JSON을 만든다."""
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_source(path: Path) -> bytes:
    """배포 경로의 심볼릭 링크와 저장소 밖 파일을 거부한다."""
    relative = path.relative_to(ROOT)
    if any((ROOT.joinpath(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
        raise ValueError(f"심볼릭 링크는 배포하지 않습니다: {relative}")
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError(f"저장소 밖 파일입니다: {relative}")
    return path.read_bytes()


def package_files(chapter: str) -> dict[str, bytes]:
    """현재 장의 노트북과 명시된 의존 파일만 선택한다."""
    files = {}
    notebooks = sorted((ROOT / "notebooks").glob(f"{chapter}-*.ipynb"))
    if not notebooks:
        raise FileNotFoundError(f"{chapter}장 노트북이 없습니다")
    selected = list(notebooks)
    for relative in EXTRA_PATHS.get(chapter, ()):
        path = ROOT / relative
        if not path.exists():
            raise FileNotFoundError(path)
        selected.extend(sorted(path.rglob("*")) if path.is_dir() else [path])
    for path in selected:
        if not path.is_file() or any(part in IGNORE_PARTS for part in path.parts):
            continue
        if path.suffix not in SOURCE_SUFFIXES:
            continue
        files[path.relative_to(ROOT).as_posix()] = read_source(path)
    if chapter == "02":
        files["requirements.txt"] = read_source(ROOT / "requirements.txt")
    else:
        requirements = ("jupyterlab>=4", "ipykernel>=6", *EXTRA_REQUIREMENTS.get(chapter, ()))
        files["requirements.txt"] = ("\n".join(requirements) + "\n").encode("utf-8")
    entries = "\n".join(f"- [`{p.name}`](notebooks/{p.name})" for p in notebooks)
    note = ""
    if chapter == "05":
        note = "\n학습자용 Notebook의 TODO를 먼저 구현한다. 풀이 참고 파일은 notebooks/solutions에 있다.\n"
    if chapter == "08":
        note = "\n08장 실습에 필요한 07장 로컬 서버 코드도 이 묶음에 포함되어 있다.\n"
    files["START-HERE.md"] = f"""# {chapter}. {CHAPTERS[chapter]} 실습 자료

이 묶음은 {chapter}장 실습용이다. 교안 본문은 온라인에서 읽고 이 폴더의 노트북·코드로 실습한다.
교안에서 말하는 '저장소 루트'는 이 ZIP에서는 requirements.txt가 있는 폴더를 뜻한다.

1. 이 폴더에서 터미널을 열고 02장에서 만든 과정용 가상환경을 활성화한다.
2. 처음 시작하거나 requirements.txt가 바뀌면 다음 명령으로 필요한 패키지를 준비한다.

```bash
python -m pip install -r requirements.txt
python -m jupyterlab
```

3. 아래 노트북을 번호 순서로 열고 과정용 커널을 선택한다.
4. 코드에서 사용하는 상대 경로를 유지하도록 notebooks·examples·fixtures 폴더를 함께 보관한다.
{note}
## 이 장의 노트북

{entries}

## 이 장만 갱신하기

교안의 해당 장 다운로드 링크에서 새 ZIP을 받아 별도 폴더에 압축 해제한다.
MANIFEST.json의 version이 같다면 실습 파일은 같은 배포본이다.
다른 장을 다시 받을 필요는 없다. 기존 폴더의 개인 풀이를 확인한 뒤 필요한 변경을 옮긴다.
교안 문구만 바뀌고 실습 파일 버전이 같다면 다시 받지 않아도 된다.
패키지 설치 버전은 로컬 환경에 따라 다를 수 있으며 version은 실습 파일 묶음을 식별한다.
""".encode("utf-8")
    return files


def build_archive(chapter: str) -> tuple[bytes, dict]:
    """파일 내용 해시와 고정 ZIP 메타데이터로 재현 가능한 배포본을 만든다."""
    files = package_files(chapter)
    records = {
        name: {"sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
        for name, data in sorted(files.items())
    }
    # 교안 본문은 입력에서 제외하여 문구 수정만으로 ZIP 버전이 바뀌지 않게 한다.
    version = hashlib.sha256(json_bytes(records)).hexdigest()[:12]
    manifest = {"chapter": chapter, "title": CHAPTERS[chapter], "version": version, "files": records}
    files["MANIFEST.json"] = json_bytes(manifest)
    archive_root = f"chapter-{chapter}-{version}"
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            info = ZipInfo(f"{archive_root}/{name}", date_time=(2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data, compresslevel=9)
    data = buffer.getvalue()
    record = {
        "chapter": chapter,
        "title": CHAPTERS[chapter],
        "version": version,
        "file": f"chapter-{chapter}.zip",
        "archive_root": archive_root,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    return data, record


def write_or_check(path: Path, data: bytes, check: bool) -> bool:
    """내용이 달라진 배포 파일만 갱신한다. 검사 모드는 파일을 쓰지 않는다."""
    same = path.is_file() and path.read_bytes() == data
    if same:
        return True
    if check:
        print(f"갱신 필요: {path.relative_to(ROOT)}", file=sys.stderr)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="원본과 배포 ZIP이 일치하는지 검사만 한다")
    args = parser.parse_args()
    records = []
    valid = True
    for chapter in CHAPTERS:
        data, record = build_archive(chapter)
        records.append(record)
        valid = write_or_check(OUTPUT / record["file"], data, args.check) and valid
    valid = write_or_check(OUTPUT / "index.json", json_bytes(records), args.check) and valid
    lines = [
        "# 챕터별 교육자료 다운로드", "",
        "수강할 챕터만 내려받는다. 각 ZIP에 해당 장의 노트북과 필요한 코드·입력 데이터가 함께 들어 있다.",
        "교안만 수정되고 아래 자료 버전이 같다면 다시 받을 필요가 없다.",
        "사용법은 [실습 자료 받기와 시작하기](../PRACTICE.md)를 따른다.", "",
        "| 장 | 교육자료 | 자료 버전 | ZIP 크기 |",
        "| --- | --- | --- | --- |",
    ]
    for r in records:
        lines.append(
            f"| {r['chapter']}. {r['title']} | [ZIP 받기]({RAW_BASE}{r['file']}) | "
            f"`{r['version']}` | {r['size_bytes'] / 1024:.1f} KiB |"
        )
    lines += [
        "", "ZIP 안의 START-HERE.md에서 시작 파일과 실행 방법을 확인한다.",
        "MANIFEST.json에 자료 버전과 파일별 SHA256을 기록하며, [배포 목록](index.json)에 ZIP의 SHA256을 기록한다.",
        "08~11장 교안은 작업중이며, 현재 제공된 예제 범위만 배포한다.", "",
        "자료 관리 절차는 [배포본 관리 안내](../scripts/CHAPTER-DOWNLOADS.md)를 참고한다.", "",
    ]
    valid = write_or_check(OUTPUT / "README.md", "\n".join(lines).encode("utf-8"), args.check) and valid
    print(f"챕터 ZIP {len(records)}개 " + ("검사 완료" if args.check else "생성 완료"))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
