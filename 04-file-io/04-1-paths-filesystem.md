# 04-1. 경로·작업 디렉터리·안전한 경로 검증

파일을 읽기 전에 프로그램이 **어느 위치를 기준으로 어떤 파일을 가리키는지** 이해해야 합니다. 문자열을 직접 이어 붙이기보다 `pathlib.Path`를 사용하면 운영체제별 경로 차이를 줄일 수 있습니다.

{% hint style="info" %}
## 🧭 학습 목표

- 현재 작업 디렉터리와 상대·절대 경로를 구분합니다.
- `Path`로 경로를 만들고 결합합니다.
- 파일·디렉터리의 존재와 종류를 확인합니다.
- 디렉터리를 탐색하고 파일 정보를 조회합니다.
- 사용자 입력 경로를 허용된 기준 디렉터리 안으로 제한합니다.
{% endhint %}

## 선행 지식

변수, 문자열, 조건문, 반복문, 예외 처리를 이해해야 합니다.

## 1. 현재 작업 디렉터리

상대 경로는 Python 파일의 위치가 아니라 **프로그램을 실행한 현재 작업 디렉터리**를 기준으로 해석됩니다.

```python
from pathlib import Path

current = Path.cwd()

print(current)
print(current.is_absolute())
```

파일을 찾지 못할 때는 먼저 `Path.cwd()`로 기준 위치를 확인합니다.

## 2. Path 객체 만들기

```python
from pathlib import Path

relative_path = Path("data") / "users.txt"
absolute_path = Path("/tmp") / "users.txt"

print(relative_path)
print(relative_path.name)    # users.txt
print(relative_path.stem)    # users
print(relative_path.suffix)  # .txt
print(relative_path.parent)  # data
```

`/` 연산자는 경로 구성요소를 운영체제에 맞게 연결합니다.

## 3. 존재와 종류 확인

```python
path = Path("data/users.txt")

print(path.exists())
print(path.is_file())
print(path.is_dir())
```

존재 확인 직후에도 다른 프로그램이 파일을 삭제할 수 있습니다. 실제 파일 작업에서는 예외 처리도 함께 사용합니다.

## 4. 디렉터리 만들기

```python
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)
```

- `parents=True`: 상위 디렉터리도 함께 생성
- `exist_ok=True`: 이미 존재해도 오류를 발생시키지 않음

## 5. 디렉터리 탐색

```python
data_dir = Path("data")

for child in data_dir.iterdir():
    print(child)
```

확장자를 제한하려면 `glob()`을 사용합니다.

```python
for csv_path in data_dir.glob("*.csv"):
    print(csv_path)

for json_path in data_dir.rglob("*.json"):
    print(json_path)
```

`glob()`은 현재 디렉터리, `rglob()`은 하위 디렉터리까지 탐색합니다.

파일시스템의 탐색 순서는 환경마다 다를 수 있습니다. 결과 순서가 중요한 실습과 보고서에서는 `sorted()`를 적용합니다.

```python
for csv_path in sorted(data_dir.glob("*.csv")):
    print(csv_path)
```

## 6. 파일 정보 확인

```python
path = Path("data/users.txt")

if path.is_file():
    info = path.stat()
    print("크기:", info.st_size)
    print("수정 시각:", info.st_mtime)
```

크기는 바이트 단위입니다. 수정 시각은 timestamp이므로 사람이 읽는 시간으로 변환하려면 `datetime`을 사용합니다.

## 7. 절대 경로 확인

```python
path = Path("data/users.txt")
print(path.resolve())
```

`resolve()`는 `..`과 심볼릭 링크를 반영해 경로를 절대 경로로 정리합니다. 절대 경로로 바꾸는 것만으로 안전해지는 것은 아닙니다.

## 8. 허용된 기준 디렉터리 확인

사용자 입력을 파일 경로로 받을 때는 정리된 결과가 허용된 기준 디렉터리 안에 있는지 확인합니다.

```python
def resolve_under(base, user_value):
    base = base.resolve()
    candidate = (base / user_value).resolve()

    if not candidate.is_relative_to(base):
        raise ValueError("허용된 디렉터리 밖의 경로입니다")

    return candidate


lab_root = Path("file-lab").resolve()
safe_path = resolve_under(lab_root, "input/users.txt")
```

```python
try:
    resolve_under(lab_root, "../../outside.txt")
except ValueError as exc:
    print("경로 거부:", exc)
```

이 검사는 실습 작업 범위를 제한하는 기본 방어입니다. 경로 확인 뒤 파일이 교체되는 경쟁 조건과 운영체제별 권한 정책은 더 높은 단계에서 다룹니다.

## 흔한 실수

- Python 파일의 위치와 현재 작업 디렉터리를 같다고 생각함
- 문자열에 `"/"` 또는 `"\\"`를 직접 이어 붙임
- 파일과 디렉터리를 구분하지 않고 처리함
- `rglob("*")`으로 필요 없는 파일까지 모두 읽음
- 경로 존재 확인만 믿고 실제 예외를 처리하지 않음
- `resolve()`만 호출하면 경로가 안전하다고 생각함
- 심볼릭 링크가 작업 영역 밖을 가리킬 수 있다는 점을 놓침

{% hint style="success" %}
## 🧪 종합 실습

1. `data/input`, `data/output` 디렉터리를 생성합니다.
2. 현재 작업 디렉터리와 각 디렉터리의 절대 경로를 출력합니다.
3. `data/input` 아래의 `.txt` 파일만 찾습니다.
4. 파일명, 확장자, 크기를 딕셔너리로 정리합니다.
5. `../../outside.txt`처럼 기준 디렉터리를 벗어나는 입력을 거부합니다.
{% endhint %}

## 완료 기준

- [ ] 상대 경로의 기준을 설명할 수 있습니다.
- [ ] `Path`로 경로를 결합할 수 있습니다.
- [ ] 파일 탐색 결과에서 파일과 디렉터리를 구분할 수 있습니다.
- [ ] 정리된 경로가 허용된 기준 디렉터리 안에 있는지 확인할 수 있습니다.

---

다음 절: [04-2. 파일·디렉터리 조작과 작업 범위](04-2-filesystem-operations.md)
