# 04-2. 파일·디렉터리 조작과 작업 범위

경로를 찾는 것과 파일시스템을 변경하는 것은 위험도가 다릅니다. 이 절에서는 실습 전용 기준 디렉터리 안에서 파일을 생성·복사·이동·삭제하고, 잘못된 경로나 심볼릭 링크를 확인하는 습관을 익힙니다.

{% hint style="info" %}
## 🧭 학습 목표

- 파일 생성과 디렉터리 생성을 구분합니다.
- `shutil`과 `Path`로 파일을 복사·이동·이름 변경합니다.
- 삭제 전 대상의 종류와 정확한 경로를 확인합니다.
- 사용자 입력 경로를 허용된 기준 디렉터리 안으로 제한합니다.
- 파일시스템 변경 작업에서 발생하는 예외를 구분합니다.
{% endhint %}

## 선행 지식

04-1의 상대·절대 경로, `Path.resolve()`, 파일·디렉터리 판정을 이해해야 합니다.

## 1. 실습 작업 영역 만들기

파일 변경 실습은 별도 디렉터리에서 수행합니다.

```python
from pathlib import Path

lab_root = Path("file-lab").resolve()
input_dir = lab_root / "input"
output_dir = lab_root / "output"

input_dir.mkdir(parents=True, exist_ok=True)
output_dir.mkdir(parents=True, exist_ok=True)
```

현재 프로젝트 루트나 개인 문서 디렉터리 전체를 삭제·이동 실습 대상으로 사용하지 않습니다.

## 2. 허용된 경로인지 확인하기

사용자가 입력한 경로를 그대로 연결하면 `../` 또는 절대 경로로 작업 영역 밖을 가리킬 수 있습니다. 이 절에서는 04-1에서 작성한 `resolve_under()`를 그대로 재사용합니다.

```python
safe_path = resolve_under(
    lab_root,
    "input/sample.txt",
    must_exist=False,
)
print(safe_path)
```

빈 입력, 절대 경로, `..` 이탈, 외부를 가리키는 심볼릭 링크를 다시 구현하지 않고 하나의 경로 계약으로 관리합니다. 검사 뒤 실제 작업 전에 파일이 바뀌는 경쟁 조건까지 해결하는 것은 아니므로, 실제 복사·이동·삭제에서 발생하는 예외도 처리합니다.

## 3. 새 파일 만들기

기존 파일을 실수로 덮어쓰지 않으려면 `x` 모드를 사용합니다.

```python
path = input_dir / "sample.txt"

try:
    with path.open("x", encoding="utf-8") as file:
        file.write("first record\n")
except FileExistsError:
    print("이미 존재하는 파일입니다:", path)
```

내용을 덮어쓰는 것이 요구사항일 때만 `w` 모드를 선택합니다.

## 4. 파일 복사

파일 내용과 기본 메타데이터를 함께 복사하려면 `shutil.copy2()`를 사용할 수 있습니다.

```python
import shutil

source = input_dir / "sample.txt"
destination = output_dir / "sample-copy.txt"

if not source.is_file():
    raise FileNotFoundError(source)
if destination.exists():
    raise FileExistsError(destination)

shutil.copy2(source, destination)
```

복사 대상이 이미 있을 때 덮어쓸 것인지 거부할 것인지는 프로그램이 명시적으로 정해야 합니다.

## 5. 이동과 이름 변경

같은 파일시스템 안에서 경로를 바꾸려면 `Path.rename()`을 사용할 수 있습니다.

```python
before = output_dir / "sample-copy.txt"
after = output_dir / "sample-renamed.txt"

if after.exists():
    raise FileExistsError(after)

before.rename(after)
```

기존 대상을 교체하는 `replace()`와 덮어쓰기를 피하려는 `rename()`의 정책을 구분합니다. 플랫폼에 따라 기존 대상 처리 차이가 있을 수 있으므로 작업 전에 명시적으로 검사합니다.

## 6. 파일과 빈 디렉터리 삭제

```python
target = output_dir / "sample-renamed.txt"

if target.is_symlink():
    raise ValueError("이 실습에서는 심볼릭 링크를 삭제하지 않습니다")
if not target.is_file():
    raise ValueError("삭제 대상이 일반 파일이 아닙니다")

target.unlink()
```

빈 디렉터리는 `rmdir()`로 삭제합니다.

```python
empty_dir = lab_root / "empty"
empty_dir.mkdir(exist_ok=True)
empty_dir.rmdir()
```

이 단계에서는 재귀 삭제를 사용하지 않습니다. 여러 파일을 한 번에 삭제해야 한다면 먼저 대상 목록을 출력하고 허용된 작업 영역인지 각각 검증합니다.

## 7. 예상 가능한 오류

| 예외 | 대표 원인 | 대응 |
| --- | --- | --- |
| `FileNotFoundError` | 원본 파일 없음 | 입력 경로 확인 |
| `FileExistsError` | 새 파일·목적지가 이미 있음 | 이름 변경 또는 정책 확인 |
| `PermissionError` | 읽기·쓰기·삭제 권한 부족 | 권한과 실행 계정 확인 |
| `IsADirectoryError` | 파일 작업에 디렉터리 전달 | `is_file()` 확인 |
| `NotADirectoryError` | 경로 중간 요소가 파일 | 경로 구성 확인 |

존재 여부 검사는 친절한 오류 메시지를 위한 사전 확인일 뿐입니다. 검사 직후 상태가 달라질 수 있으므로 실제 작업의 예외도 처리합니다.

## 흔한 실수

- 사용자 입력 경로를 검증 없이 기준 경로와 결합함
- 복사·이동 대상이 이미 있는지 확인하지 않음
- 파일과 디렉터리를 같은 삭제 함수로 처리함
- 심볼릭 링크가 가리키는 실제 위치를 확인하지 않음
- 광범위한 재귀 삭제로 실습 디렉터리 밖까지 지움

{% hint style="success" %}
## 🧪 종합 실습

1. `file-lab/input`, `file-lab/output`을 만듭니다.
2. `x` 모드로 입력 파일을 만들고 같은 이름으로 다시 만들 때의 오류를 확인합니다.
3. 입력 파일을 출력 디렉터리로 복사한 뒤 이름을 변경합니다.
4. `../outside.txt`가 작업 영역 검증에서 거부되는지 확인합니다.
5. 일반 파일만 삭제하고 빈 출력 디렉터리를 정리합니다.
{% endhint %}

## 완료 기준

- [ ] 파일 생성·복사·이동·삭제의 차이를 설명할 수 있습니다.
- [ ] 작업 전에 대상 경로와 종류를 확인할 수 있습니다.
- [ ] 입력 경로를 허용된 기준 디렉터리 내부로 제한할 수 있습니다.
- [ ] 재귀 삭제 없이 실습 파일을 안전하게 정리할 수 있습니다.

---

다음 절: [04-3. 텍스트 파일·모드·with·줄바꿈](04-3-text-files.md)
