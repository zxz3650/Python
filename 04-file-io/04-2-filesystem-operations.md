# 04-2. 파일·디렉터리 조작과 작업 범위

경로를 조회하는 작업과 파일 시스템을 변경하는 작업은 위험도가 다르다. 이 절에서는 실습 전용 기준 디렉터리 안에서 파일을 생성·복사·이동·삭제한다. 각 작업에서 원본·목적지·충돌 정책을 먼저 확인하고, 실제 작업 중 발생한 예외까지 처리하는 습관을 익힌다.

{% hint style="info" %}
### 🧭 학습 목표

- 파일 생성과 디렉터리 생성을 구분한다.
- `shutil`과 `Path`로 파일을 복사·이동·이름 변경한다.
- 원본과 목적지가 같거나 목적지가 이미 있는 상황을 처리한다.
- 삭제 전에 대상의 종류와 정확한 경로를 확인한다.
- 사용자 입력 경로를 허용된 기준 디렉터리 안으로 제한한다.
- 사전 검사와 실제 파일 작업의 예외 처리를 함께 적용한다.
{% endhint %}

## 선행 지식

04-1의 상대·절대 경로, `Path.resolve()`, 파일·디렉터리 판정, `resolve_under()`를 이해해야 한다. 이 절의 예제를 하나의 Python 파일에서 실행한다면 04-1에서 완성한 `resolve_under()`를 예제보다 위에 둔다.

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | 전용 작업 영역, `mkdir()`, `x` 모드, `copy2()`, `rename()`, `unlink()`, `rmdir()` |
| 권장 | 원본·목적지 검증, 이름 충돌 정책, 구체적인 파일 시스템 예외 처리 |
| 심화 | 심볼릭 링크 정책, 검사와 사용 사이의 경쟁 조건, 파일 시스템 간 이동 |

전용 실습은 [`notebooks/04-2-filesystem-operations.ipynb`](../notebooks/04-2-filesystem-operations.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

다음 코드의 결과와 위험을 예상한다.

```python
from pathlib import Path

source = Path("file-lab/input/report.txt")
destination = Path("file-lab/output/report.txt")

print(source.exists())
print(destination.exists())
```

1. 두 값이 모두 `False`여도 다음 순간까지 같은 상태라고 보장할 수 있는가?
2. 목적지가 이미 있을 때 복사와 이동은 덮어쓰기·거부·새 이름 중 어떤 정책을 따라야 하는가?
3. `unlink()`와 `rmdir()`는 같은 대상을 삭제하는가?
4. `../outside.txt`를 기준 디렉터리와 단순히 결합해도 안전한가?

## 1. 실습 작업 영역 만들기

파일 변경 실습은 별도 디렉터리에서 수행한다.

```python
from pathlib import Path

lab_root = Path("file-lab").resolve()
input_dir = lab_root / "input"
output_dir = lab_root / "output"

input_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)
```

`mkdir()`는 디렉터리를 만들고, `Path()`는 경로 객체만 만든다. `parents=True`는 필요한 상위 디렉터리도 만들며, `exist_ok=True`는 같은 디렉터리가 이미 있을 때 오류를 내지 않는다. 같은 경로에 일반 파일이 있거나 권한이 부족하면 여전히 예외가 발생한다.

현재 프로젝트 루트나 개인 문서 디렉터리 전체를 삭제·이동 실습 대상으로 사용하지 않는다.

## 2. 변경 작업의 계약 정하기

파일을 바꾸기 전에 다음 항목을 정한다.

| 항목 | 확인할 질문 |
| --- | --- |
| 원본 | 존재하는 일반 파일인가? 읽을 권한이 있는가? |
| 목적지 | 허용된 작업 영역 안인가? 부모 디렉터리가 있는가? |
| 충돌 | 목적지가 이미 있으면 거부·새 이름·교체 중 무엇을 하는가? |
| 동일성 | 원본과 목적지가 같은 경로를 가리키는가? |
| 실패 | 작업이 실패하면 어떤 예외를 사용자에게 전달하거나 기록하는가? |

예제에서는 학습자의 기존 파일을 보호하기 위해 **목적지가 있으면 거부한다**는 정책을 기본값으로 사용한다.

## 3. 허용된 경로인지 확인하기

사용자가 입력한 경로를 그대로 연결하면 `../` 또는 절대 경로로 작업 영역 밖을 가리킬 수 있다. 04-1에서 작성한 `resolve_under()`를 재사용한다.

```python
safe_path = resolve_under(
    lab_root,
    "input/sample.txt",
    must_exist=False,
)
print(safe_path)
```

빈 입력, 절대 경로, `..` 이탈, 외부를 가리키는 심볼릭 링크를 여러 함수에서 따로 검사하지 않고 하나의 경로 계약으로 관리한다. `resolve_under()`는 확인 가능한 링크를 따라간 결과가 기준 디렉터리 안인지 검사한다. 링크 자체를 모두 금지해야 하는 프로그램이라면 원래 경로 구성요소에 대한 별도 정책이 필요하다.

경로 검사는 검사 직후 파일이나 링크가 바뀌는 경쟁 조건까지 해결하지 않는다. 실제 복사·이동·삭제에서 발생하는 예외도 반드시 처리한다.

## 4. 새 파일 만들기

기존 파일을 실수로 덮어쓰지 않으려면 `x` 모드를 사용한다.

```python
path = input_dir / "sample.txt"

try:
    with path.open("x", encoding="utf-8") as file:
        file.write("first record\n")
except FileExistsError:
    print("이미 존재하는 파일이다:", path)
```

`x` 모드는 파일이 없으면 만들고, 있으면 `FileExistsError`를 발생시킨다. 내용 전체를 새 값으로 교체하는 것이 요구사항일 때만 `w` 모드를 선택한다. 빈 파일만 필요할 때 사용할 수 있는 `Path.touch()`는 기본 설정에서 기존 파일의 수정 시각을 바꿀 수 있으므로 덮어쓰기 방지 목적이라면 `touch(exist_ok=False)`를 사용한다.

## 5. 파일 복사

파일 내용과 수정 시각 같은 메타데이터를 가능한 범위에서 함께 복사하려면 `shutil.copy2()`를 사용한다.

```python
import shutil

source = input_dir / "sample.txt"
destination = output_dir / "sample-copy.txt"

if not source.exists():
    raise FileNotFoundError(source)
if not source.is_file():
    raise ValueError("원본이 일반 파일이 아니다")
if source == destination:
    raise ValueError("원본과 목적지가 같다")
if destination.exists():
    raise FileExistsError(destination)
if not destination.parent.is_dir():
    raise NotADirectoryError(destination.parent)

shutil.copy2(source, destination)
```

`copy2()`도 소유자·접근 제어 목록·모든 확장 속성을 환경과 파일 시스템에 관계없이 완전히 복제한다고 보장하지는 않는다. 보존해야 하는 메타데이터가 있다면 복사 후 별도로 검증한다.

목적지 존재 여부를 먼저 확인하면 친절한 오류를 만들 수 있지만, 확인 직후 다른 프로세스가 같은 경로를 만들 수 있다. 충돌 방지가 보안·정합성 요구사항이라면 단순한 `exists()` 검사만으로 충분하다고 가정하지 않는다.

## 6. 이동·이름 변경·교체

같은 파일 시스템 안에서 경로를 바꾸려면 `Path.rename()`을 사용할 수 있다.

```python
before = output_dir / "sample-copy.txt"
after = output_dir / "sample-renamed.txt"

if not before.exists():
    raise FileNotFoundError(before)
if not before.is_file():
    raise ValueError("이동 원본이 일반 파일이 아니다")
if after.exists():
    raise FileExistsError(after)

before.rename(after)
```

관련 작업의 목적을 구분한다.

| 작업 | 사용 예 | 주의점 |
| --- | --- | --- |
| 같은 파일 시스템에서 이름·위치 변경 | `source.rename(destination)` | 기존 목적지 처리 방식이 운영체제에 따라 다르므로 먼저 정책을 적용한다. |
| 다른 파일 시스템까지 포함한 이동 | `shutil.move(source, destination)` | 필요하면 복사 후 원본을 삭제하므로 중간 실패와 메타데이터를 고려한다. |
| 기존 목적지를 교체 | `source.replace(destination)` | 덮어쓰기가 명시된 요구사항일 때만 사용한다. |

목적지가 없다는 사전 검사는 사용자 실수를 줄이지만 원자적인 충돌 방지를 보장하지 않는다. 04-8에서는 임시 파일과 원자적 교체를 이용한 저장 정책을 다룬다.

## 7. 일반 파일과 빈 디렉터리 삭제

삭제는 되돌리기 어려우므로 경로와 종류를 확인한 뒤 한 개의 명확한 대상만 처리한다.

```python
target = output_dir / "sample-renamed.txt"

if target.is_symlink():
    raise ValueError("이 실습에서는 심볼릭 링크를 삭제하지 않는다")
if not target.is_file():
    raise ValueError("삭제 대상이 일반 파일이 아니다")

target.unlink()
```

빈 디렉터리는 `rmdir()`로 삭제한다.

```python
empty_dir = lab_root / "empty"
empty_dir.mkdir(exist_ok=True)
empty_dir.rmdir()
```

`unlink()`는 파일이나 심볼릭 링크에, `rmdir()`는 빈 디렉터리에 사용한다. 비어 있지 않은 디렉터리에 `rmdir()`를 호출하면 `OSError`가 발생한다. 이 단계에서는 재귀 삭제를 사용하지 않는다. 여러 파일을 지워야 한다면 먼저 대상 목록을 출력하고 각 경로와 종류를 검증한다.

## 8. 예상 가능한 오류

| 예외 | 대표 원인 | 대응 |
| --- | --- | --- |
| `FileNotFoundError` | 원본이나 삭제 대상이 없음 | 입력 경로와 작업 순서를 확인한다. |
| `FileExistsError` | 새 파일·목적지가 이미 있음 | 새 이름 또는 충돌 정책을 선택한다. |
| `PermissionError` | 읽기·쓰기·삭제 권한 부족 | 권한과 실행 계정을 확인한다. |
| `IsADirectoryError` | 파일 작업에 디렉터리를 전달함 | `is_file()`로 종류를 확인한다. |
| `NotADirectoryError` | 경로 중간 요소가 파일임 | 부모 경로 구성을 확인한다. |
| `OSError` | 파일 시스템·장치 수준 작업 실패 | 구체적인 하위 예외와 메시지를 기록한다. |

존재 여부 검사는 친절한 오류 메시지를 위한 사전 확인일 뿐이다. 검사 직후 상태가 달라질 수 있으므로 실제 작업에서 발생한 예외도 처리한다. 원인을 해결할 수 없다면 무조건 성공한 것처럼 계속하지 않고 호출자에게 예외를 전달한다.

## 흔한 실수

- 사용자 입력 경로를 검증하지 않고 기준 경로와 결합함
- 원본과 목적지가 같은 경로인지 확인하지 않음
- 복사·이동 목적지가 이미 있을 때의 정책을 정하지 않음
- `rename()`이 모든 운영체제에서 같은 방식으로 기존 대상을 처리한다고 가정함
- 파일과 디렉터리를 같은 삭제 함수로 처리함
- 광범위한 재귀 삭제로 실습 디렉터리 밖까지 지움
- `exists()` 검사만으로 작업 중 경로가 바뀌지 않는다고 가정함

## 9. 개념 확인 문제

### 문제 1

`Path("report.txt")`를 만들면 빈 파일도 함께 생성될까?

<details>
<summary>정답 보기</summary>

아니다. `Path`는 경로를 표현한다. 파일은 `open()`, `touch()`, `write_text()` 같은 변경 작업으로 생성한다.

</details>

### 문제 2

기존 파일을 보호하면서 새 파일을 만들 때 `w`와 `x` 중 어떤 모드가 적합할까?

<details>
<summary>정답 보기</summary>

`x`가 적합하다. `w`는 기존 내용을 지우지만 `x`는 같은 경로가 있으면 `FileExistsError`를 발생시킨다.

</details>

### 문제 3

`destination.exists()`가 `False`이면 이어지는 복사도 반드시 충돌 없이 성공할까?

<details>
<summary>정답 보기</summary>

아니다. 검사와 복사 사이에 다른 프로세스가 목적지를 만들 수 있고 권한·저장 공간 같은 다른 오류도 발생할 수 있다. 실제 복사의 예외도 처리해야 한다.

</details>

### 문제 4

비어 있지 않은 디렉터리를 `rmdir()`로 삭제할 수 있을까?

<details>
<summary>정답 보기</summary>

아니다. `rmdir()`는 빈 디렉터리에만 사용한다. 이 절에서는 범위를 실수로 넓히기 쉬운 재귀 삭제를 사용하지 않는다.

</details>

## 10. 단계별 실습: 안전한 파일 전달

### 실습 상황

`file-lab/input/note.txt`를 `file-lab/output/note-copy.txt`로 복사하고 `note-final.txt`로 이름을 변경한 뒤, 확인이 끝나면 결과 파일만 삭제한다.

### 요구사항

- 모든 사용자 경로를 `resolve_under()`로 검증한다.
- 원본은 존재하는 일반 파일이어야 한다.
- 원본과 목적지가 같으면 거부한다.
- 목적지가 이미 있으면 덮어쓰지 않고 `FileExistsError`를 발생시킨다.
- 삭제 대상이 일반 파일이 아니거나 심볼릭 링크이면 거부한다.
- 입력 원본은 수정하거나 삭제하지 않는다.

### 학습자용 TODO 골격

```python
import shutil
from pathlib import Path


# 04-1에서 완성한 resolve_under()를 이 코드 위에 둔다.


def copy_regular_file(base, source_value, destination_value):
    source = resolve_under(base, source_value, must_exist=True)
    destination = resolve_under(base, destination_value, must_exist=False)

    # 실습 과제: source가 일반 파일인지 확인
    # 실습 과제: source와 destination이 같은지 확인
    # 실습 과제: destination과 부모 디렉터리를 확인
    # 실습 과제: copy2()로 복사
    # 실습 과제: 복사된 목적지 Path 반환
    raise NotImplementedError


def rename_without_overwrite(base, before_value, after_value):
    # 실습 과제: 두 경로를 작업 영역 안으로 제한
    # 실습 과제: 원본 종류와 목적지 충돌 확인
    # 실습 과제: rename() 실행 후 새 Path 반환
    raise NotImplementedError


def delete_regular_file(base, target_value):
    target = resolve_under(base, target_value, must_exist=True)
    original_entry = Path(base).resolve(strict=True) / Path(target_value)

    # 실습 과제: original_entry가 심볼릭 링크인지 확인
    # 실습 과제: target이 일반 파일인지 확인
    # 실습 과제: unlink() 실행
    raise NotImplementedError
```

### 권장 구현 순서

1. `file-lab/input`, `file-lab/output`을 만든다.
2. `x` 모드로 `input/note.txt`에 `practice\n`을 쓰고 같은 이름으로 다시 만들 때의 오류를 확인한다.
3. 정상 복사를 구현하고 원본과 복사본의 내용을 비교한다.
4. 기존 목적지와 `../outside.txt`가 거부되는지 확인한다.
5. 복사본의 이름을 바꾸고 이전 경로가 사라졌는지 확인한다.
6. 결과 파일만 삭제하고 입력 원본이 남아 있는지 확인한다.

### 검증 행렬

| 구분 | 입력 | 기대 결과 |
| --- | --- | --- |
| 정상 | `input/note.txt` → `output/note-copy.txt` | 내용이 같은 새 파일 생성 |
| 정상 | 복사본 → `output/note-final.txt` | 이전 경로는 없고 새 경로는 존재 |
| 오류 | 없는 원본 | `FileNotFoundError` |
| 오류 | 디렉터리를 원본으로 지정 | 일반 파일이 아니라는 오류 |
| 오류 | 원본과 목적지가 같음 | `ValueError` |
| 오류 | 이미 존재하는 목적지 | `FileExistsError` |
| 오류 | `../outside.txt` | `ValueError` |

### 구현 후 확인 예

```python
lab_root = Path("file-lab").resolve()

copied = copy_regular_file(
    lab_root,
    "input/note.txt",
    "output/note-copy.txt",
)
assert copied.read_text(encoding="utf-8") == "practice\n"

renamed = rename_without_overwrite(
    lab_root,
    "output/note-copy.txt",
    "output/note-final.txt",
)
assert renamed.is_file()
assert not copied.exists()

delete_regular_file(lab_root, "output/note-final.txt")
assert not renamed.exists()
assert (lab_root / "input" / "note.txt").is_file()
```

{% hint style="success" %}
### ✅ 완료 기준

- [ ] 파일 생성·복사·이동·삭제의 차이를 설명할 수 있다.
- [ ] 변경 전에 원본·목적지·대상 종류와 충돌 정책을 확인할 수 있다.
- [ ] 입력 경로를 허용된 기준 디렉터리 안으로 제한할 수 있다.
- [ ] 사전 검사 뒤에도 실제 파일 작업의 예외를 처리할 수 있다.
- [ ] 재귀 삭제 없이 실습 결과만 안전하게 정리할 수 있다.
- [ ] 정상·오류·경계 입력으로 파일 변경 함수를 검증할 수 있다.
{% endhint %}

---

다음 절: [04-3. 텍스트 파일·모드·with·줄바꿈](04-3-text-files.md)
