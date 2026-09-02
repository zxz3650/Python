# 13-2. 파일과 폴더 일괄 처리

파일 자동화는 경로 선택, 분류, 이름 변경, 복사·이동, 압축, 작업 기록으로 구성됩니다. 실수의 영향이 크므로 코드보다 작업 범위와 복구 전략을 먼저 확정합니다.

{% hint style="info" %}
## 🧭 학습 목표

- `pathlib` 경로를 기준 경로와 비교합니다.
- 파일 선택, 분류, 이름 충돌 처리를 함수로 나눕니다.
- 변경 계획을 먼저 만들고 승인 후 적용합니다.
- ZIP 압축 해제 시 경로 탈출을 방지합니다.
{% endhint %}

## 1. 작업 범위 고정

```python
from pathlib import Path

root = Path("lab/inbox").resolve()

if not root.exists() or not root.is_dir():
    raise ValueError("작업 폴더를 확인하세요.")

files = [
    path
    for path in root.iterdir()
    if path.is_file() and not path.is_symlink()
]
```

`iterdir()`는 한 단계만, `rglob()`는 하위 폴더 전체를 탐색합니다. 최초 버전은 한 단계만 처리하고, 하위 폴더가 필요할 때 제외 규칙과 심볼릭 링크 정책을 먼저 추가합니다.

## 2. 분류 규칙을 데이터로 분리

```python
CATEGORIES = {
    "images": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    "documents": {".pdf", ".docx", ".pptx", ".txt", ".md"},
    "data": {".csv", ".json", ".xlsx", ".xml"},
    "archives": {".zip", ".tar", ".gz", ".7z"},
}


def category_for(path):
    suffix = path.suffix.lower()
    for category, suffixes in CATEGORIES.items():
        if suffix in suffixes:
            return category
    return "other"
```

규칙을 조건문 여러 개로 퍼뜨리지 않으면 설정 파일로 분리하거나 테스트하기 쉽습니다. 확장자는 내용을 보증하지 않으므로 보안 판정 기준으로 사용하지 않습니다.

## 3. 이름 충돌

도착지에 같은 이름이 있으면 무조건 덮어쓰지 않습니다.

```python
def unique_destination(destination, reserved):
    candidate = destination
    number = 2

    while candidate.exists() or candidate in reserved:
        candidate = destination.with_name(
            f"{destination.stem}_{number}{destination.suffix}"
        )
        number += 1

    reserved.add(candidate)
    return candidate
```

`reserved`는 현재 계획에서 이미 배정한 이름까지 충돌 검사에 포함합니다.

## 4. 계획과 적용

```text
파일 탐색
→ 제외 규칙
→ 분류·충돌 해결
→ 변경 계획 출력
→ 사용자 검토
→ 작업 기록 생성
→ 하나씩 이동·상태 갱신
→ 최종 건수 검증
```

작업 도중 실패하면 이미 적용된 항목과 적용되지 않은 항목을 기록으로 구분해야 합니다. 그래야 도중부터 재개하거나 이미 적용된 항목만 되돌릴 수 있습니다.

## 5. 복사·이동·삭제

| 작업 | 함수 | 주의점 |
| --- | --- | --- |
| 파일 복사 | `shutil.copy2()` | 메타데이터 보존 여부 확인 |
| 폴더 복사 | `shutil.copytree()` | 기존 도착지 정책 확인 |
| 이동 | `shutil.move()` | 파일시스템 경계에서 복사+삭제가 될 수 있음 |
| 단일 파일 삭제 | `Path.unlink()` | 복구 불가능, 명시적 승인 필요 |
| 빈 폴더 삭제 | `Path.rmdir()` | 비어 있을 때만 성공 |

초기 버전에서는 삭제를 구현하지 않고 격리 폴더로 이동하는 방식이 안전합니다.

## 6. ZIP 압축과 경로 탈출

압축 내부 이름에 `../`나 절대 경로가 있으면 압축 해제 폴더 밖으로 파일을 쓸 수 있습니다.

```python
from zipfile import ZipFile


def safe_extract(archive_path, output_dir):
    output_root = output_dir.resolve()

    with ZipFile(archive_path) as archive:
        for member in archive.infolist():
            destination = (output_root / member.filename).resolve()
            if not destination.is_relative_to(output_root):
                raise ValueError(f"위험한 압축 경로: {member.filename}")
        archive.extractall(output_root)
```

실무에서는 파일 개수, 개별·전체 해제 크기, 압축률 제한도 추가합니다.

## 실습

1. 임시 폴더에 확장자가 다른 파일 6개를 만듭니다.
2. 분류 계획을 JSON으로만 출력합니다.
3. 도착지에 같은 이름의 파일을 미리 만들어 충돌 처리를 확인합니다.
4. 심볼릭 링크가 제외되는지 확인합니다.
5. 원상복구 기록에 필요한 필드를 정의합니다.

## 완료 기준

- [ ] 작업 경로를 명시적으로 고정했습니다.
- [ ] 도착 파일을 무조건 덮어쓰지 않습니다.
- [ ] 미리보기와 적용 단계를 분리했습니다.
- [ ] 작업 도중 실패 시 적용 상태를 확인할 수 있습니다.
- [ ] 위험한 ZIP 내부 경로를 거부할 수 있습니다.

---

다음: [13-3. 웹 정보 수집](13-3-web-collection.md)
