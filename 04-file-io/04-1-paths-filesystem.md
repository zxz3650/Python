# 04-1. 경로·작업 디렉터리·안전한 경로 검증

파일 입출력 오류의 상당수는 파일 내용이 아니라 **프로그램이 어느 위치를 기준으로 어떤 대상을 가리켰는지**에서 시작한다. 이 절에서는 문자열 경로 대신 `pathlib.Path`를 사용하고, 현재 작업 디렉터리·스크립트 위치·상대 경로·절대 경로를 구분한다. 마지막에는 사용자 입력 경로가 허용된 실습 디렉터리 밖으로 나가지 못하도록 검증한다.

{% hint style="info" %}
### 🧭 학습 목표

- 현재 작업 디렉터리와 Python 파일의 위치를 구분한다.
- 상대 경로와 절대 경로를 기준 위치 의존 여부로 정의한다.
- `Path`로 경로를 구성하고 이름·확장자·상위 경로를 조회한다.
- 파일·디렉터리·심볼릭 링크를 구분한다.
- 탐색 결과를 안정된 순서로 필터링한다.
- `stat()`으로 파일 크기와 수정 시각을 확인한다.
- 사용자 입력 경로를 허용된 기준 디렉터리 안으로 제한한다.
- 정상·오류·경계 입력으로 경로 함수를 검증한다.
{% endhint %}

## 선행 지식

- 변수, 문자열, 리스트, 딕셔너리를 이해해야 한다.
- 조건문과 반복문을 작성할 수 있어야 한다.
- 함수 인자·반환값과 `ValueError`, `FileNotFoundError`를 이해해야 한다.
- 모듈을 `import`하고 `try`/`except`를 사용할 수 있어야 한다.

## 이 절의 핵심 질문

```text
현재 기준 위치는 어디인가?
  ↓
입력 경로는 상대 경로인가, 절대 경로인가?
  ↓
정리된 실제 경로는 어디를 가리키는가?
  ↓
파일·디렉터리·링크 중 무엇인가?
  ↓
허용된 작업 영역 안에 있는가?
```

경로 문자열을 받자마자 파일을 열지 않고 위 질문을 순서대로 확인한다.

전용 실습은 [`notebooks/04-1-paths-filesystem.ipynb`](../notebooks/04-1-paths-filesystem.ipynb)에서 진행할 수 있다.

## 1. Path 객체와 실제 파일은 다르다

`Path` 객체를 만드는 동작은 경로를 표현할 뿐 파일이나 디렉터리를 생성하지 않는다.

```python
from pathlib import Path

path = Path("data") / "users.txt"

print(path)          # data/users.txt 또는 운영체제에 맞는 표현
print(path.exists()) # 실제 대상이 없으면 False
```

다음 세 가지를 구분한다.

| 표현 | 의미 |
| --- | --- |
| `Path("data/users.txt")` | 경로 객체 생성 |
| `path.exists()` | 현재 시점에 대상이 존재하는지 조회 |
| `path.open()` | 실제 파일 자원 열기 |

`Path` 객체가 만들어졌다는 사실은 파일 존재나 접근 권한을 보장하지 않는다.

## 2. 현재 작업 디렉터리

`Path()`나 `open()`에 전달한 상대 경로는 기본적으로 Python 파일이 저장된 위치가 아니라 **프로그램을 실행한 현재 작업 디렉터리**를 기준으로 해석된다.

```python
from pathlib import Path

current = Path.cwd()

print("현재 작업 디렉터리:", current)
print("절대 경로인가:", current.is_absolute())
```

같은 프로그램도 실행 위치가 달라지면 상대 경로가 다른 대상을 가리킬 수 있다.

```text
project/
├── app.py
└── data/
    └── users.txt
```

```bash
cd project
python app.py
```

위 실행에서는 `Path("data/users.txt")`가 `project/data/users.txt`를 가리킨다. 그러나 상위 디렉터리에서 `python project/app.py`로 실행하면 같은 상대 경로가 상위 디렉터리의 `data/users.txt`를 찾는다.

{% hint style="warning" %}
파일을 찾지 못할 때 경로 문자열을 계속 수정하기 전에 `Path.cwd()`와 실행 명령을 먼저 확인한다.
{% endhint %}

## 3. 스크립트 위치와 작업 디렉터리

일반 `.py` 파일에서는 `__file__`로 현재 Python 파일의 위치를 구할 수 있다.

```python
from pathlib import Path

script_dir = Path(__file__).resolve().parent
data_path = script_dir / "data" / "users.txt"

print("스크립트 디렉터리:", script_dir)
print("데이터 경로:", data_path)
```

| 기준 | 코드 | 적합한 상황 |
| --- | --- | --- |
| 실행 위치 | `Path.cwd()` | 사용자가 현재 폴더의 파일을 지정하는 도구 |
| 스크립트 위치 | `Path(__file__).resolve().parent` | 프로그램과 함께 배포된 고정 자료 |
| 사용자 홈 | `Path.home()` | 사용자별 설정 위치를 구성할 때 |

Jupyter Notebook과 일부 대화형 환경에는 `__file__`이 없다. 이 환경에서는 작업 디렉터리나 명시적인 프로젝트 기준 경로를 사용한다.

## 4. 상대 경로와 절대 경로

경로는 파일이나 디렉터리의 위치를 나타내는 표현이다. 경로가 **어디에서 시작되는지**에 따라 상대 경로와 절대 경로로 구분한다.

- **상대 경로(relative path)**는 현재 작업 디렉터리처럼 정해진 **기준 위치에서 출발해** 대상까지의 위치를 나타낸다. 기준 위치가 바뀌면 같은 문자열이 다른 대상을 가리킬 수 있다.
- **절대 경로(absolute path)**는 루트 디렉터리나 드라이브처럼 파일 시스템의 **시작 위치부터** 대상까지의 전체 위치를 나타낸다. 현재 작업 디렉터리가 바뀌어도 같은 대상을 가리킨다.

| 구분 | 출발점 | 예 | 기준 위치가 바뀔 때 |
| --- | --- | --- | --- |
| 상대 경로 | 현재 작업 디렉터리 또는 프로그램이 명시한 기준 경로 | `data/users.txt`, `../shared/users.txt` | 가리키는 대상이 달라질 수 있음 |
| 절대 경로 | 파일 시스템 루트 또는 드라이브 | POSIX의 `/home/student/data/users.txt`, Windows의 `C:\Users\student\data\users.txt` | 가리키는 대상이 달라지지 않음 |

상대 경로에서 `.`은 현재 위치, `..`은 상위 위치를 뜻한다. 상대 경로라고 해서 반드시 프로젝트 내부를 가리키는 것은 아니다. `../outside.txt`처럼 기준 위치 밖으로 이동할 수도 있다.

```python
relative_path = Path("data") / "users.txt"
absolute_path = Path.cwd() / "data" / "users.txt"

print(relative_path.is_absolute())  # False
print(absolute_path.is_absolute())  # True
```

경로 문자열의 모양을 직접 검사하지 않고 `is_absolute()`로 현재 운영체제 기준의 절대 경로인지 판별한다. 운영체제마다 절대 경로 표현이 다르므로 `/tmp/...`나 `C:\...` 같은 경로를 학습 코드에 고정하지 않는다. `Path.cwd()`, `Path.home()` 또는 프로그램 설정값으로 기준 경로를 정한다.

{% hint style="warning" %}
절대 경로라는 사실은 대상이 실제로 존재하거나 접근 가능하거나 안전하다는 뜻이 아니다. 상대 경로라는 사실도 허용된 디렉터리 안에 있다는 뜻이 아니다. 경로 종류, 존재 여부, 대상 종류, 허용 범위를 각각 검사한다.
{% endhint %}

절대 경로를 다른 기준 경로와 결합할 때는 특히 주의한다.

```python
base = Path("file-lab")
user_path = Path("/outside/example.txt")

print(base / user_path)
```

오른쪽 값이 현재 운영체제에서 절대 경로이면 앞의 `base`가 무시될 수 있다. 사용자 입력이 절대 경로인지 먼저 검사해야 한다.

## 5. 경로 구성요소 조회

```python
path = Path("reports") / "archive.tar.gz"

print(path.name)      # archive.tar.gz
print(path.stem)      # archive.tar
print(path.suffix)    # .gz
print(path.suffixes)  # ['.tar', '.gz']
print(path.parent)    # reports
print(path.parts)     # 운영체제별 경로 구성요소
```

`suffix`는 마지막 확장자 하나만 반환한다. `.tar.gz`처럼 복합 확장자가 중요하면 `suffixes`를 확인한다.

이름을 바꾼 새 경로도 만들 수 있다.

```python
report = Path("output/report.json")

print(report.with_name("summary.json"))
print(report.with_suffix(".json.tmp"))
```

이 메서드는 새 `Path`를 반환할 뿐 실제 파일 이름을 변경하지 않는다. 파일 이동과 이름 변경은 04-2에서 다룬다.

## 6. 경로 정리와 resolve

```python
path = Path("data") / ".." / "data" / "users.txt"

print(path)
print(path.resolve(strict=False))
```

`resolve()`는 절대 경로를 만들고 `.`·`..`과 확인 가능한 심볼릭 링크를 반영한다.

| 호출 | 대상이 없을 때 | 사용 예 |
| --- | --- | --- |
| `resolve(strict=False)` | 존재하는 앞부분을 정리하고 경로 반환 | 앞으로 생성할 출력 경로 검증 |
| `resolve(strict=True)` | `FileNotFoundError` 발생 | 반드시 존재해야 하는 입력 경로 검증 |

```python
try:
    existing = Path("data/users.txt").resolve(strict=True)
except FileNotFoundError as exc:
    print("입력 파일이 없습니다:", exc)
```

`resolve()`는 경로를 정리하는 기능이다. 정리된 경로가 프로그램이 허용한 범위 안에 있는지는 별도로 확인해야 한다.

## 7. 존재와 대상 종류 확인

```python
path = Path("data/users.txt")

print("존재:", path.exists())
print("일반 파일:", path.is_file())
print("디렉터리:", path.is_dir())
print("심볼릭 링크:", path.is_symlink())
```

심볼릭 링크는 다른 파일이나 디렉터리를 가리킬 수 있다. `is_file()`과 `is_dir()`은 링크가 가리키는 대상을 따라가므로, 링크 자체를 구분해야 하는 정책이라면 `is_symlink()`를 먼저 확인한다.

```python
if path.is_symlink():
    print("링크는 별도 검토합니다")
elif path.is_file():
    print("일반 파일을 처리합니다")
elif path.is_dir():
    print("디렉터리는 처리하지 않습니다")
else:
    print("없거나 지원하지 않는 대상입니다")
```

존재 확인 직후에도 다른 프로그램이 대상을 삭제하거나 바꿀 수 있다. `exists()`만 믿지 말고 실제 파일 작업에서 발생하는 예외도 처리한다.

## 8. 디렉터리 만들기

```python
lab_root = Path("file-lab")
input_dir = lab_root / "input"
output_dir = lab_root / "output"

try:
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
except FileExistsError:
    print("같은 경로에 디렉터리가 아닌 대상이 있습니다")
except PermissionError:
    print("디렉터리를 만들 권한이 없습니다")
```

- `parents=True`: 필요한 상위 디렉터리도 함께 생성
- `exist_ok=True`: 같은 디렉터리가 이미 있으면 계속 진행

`exist_ok=True`여도 같은 경로에 일반 파일이 있거나 권한이 부족하면 예외가 발생한다. `exist_ok`는 모든 오류를 무시하는 옵션이 아니다.

## 9. 디렉터리 탐색

`iterdir()`는 한 단계 아래의 모든 항목을 반환한다.

```python
data_dir = Path("data")

try:
    for child in sorted(data_dir.iterdir()):
        print(child)
except FileNotFoundError:
    print("탐색할 디렉터리가 없습니다:", data_dir)
except NotADirectoryError:
    print("디렉터리가 아닌 경로입니다:", data_dir)
```

파일 시스템의 기본 탐색 순서는 환경마다 다를 수 있다. 보고서와 테스트에서 순서가 중요하면 `sorted()`를 적용한다.

### glob과 rglob

```python
for csv_path in sorted(data_dir.glob("*.csv")):
    if csv_path.is_file():
        print(csv_path)

for json_path in sorted(data_dir.rglob("*.json")):
    if json_path.is_file():
        print(json_path)
```

- `glob("*.csv")`: 현재 디렉터리의 패턴과 일치하는 항목
- `rglob("*.json")`: 모든 하위 디렉터리까지 재귀 탐색

`glob` 패턴은 정규표현식이 아니다. 대소문자 구분 방식도 파일 시스템에 따라 다를 수 있으므로 결과를 다시 검증한다. 범위가 넓은 `rglob("*")`은 불필요한 파일과 많은 디렉터리를 탐색할 수 있다.

## 10. 파일 메타데이터 확인

```python
from datetime import datetime, timezone

path = Path("data/users.txt")

try:
    info = path.stat()
except FileNotFoundError:
    print("파일이 없습니다:", path)
else:
    modified_at = datetime.fromtimestamp(
        info.st_mtime,
        tz=timezone.utc,
    )

    print("크기(bytes):", info.st_size)
    print("수정 시각(UTC):", modified_at.isoformat())
```

`st_size`는 바이트 단위다. 텍스트의 문자 수와 같다고 가정하면 안 된다. `st_mtime`은 수정 시각을 나타내지만 분석 중 파일이 바뀔 수 있으므로 해시나 내용 분석 결과와 항상 같은 시점의 상태라고 보장되지는 않는다.

## 11. 허용된 기준 디렉터리 검증

사용자 입력을 파일 경로로 받을 때는 빈 입력과 절대 경로를 거부하고, 정리된 결과가 허용된 기준 디렉터리 안에 있는지 확인한다.

```python
def resolve_under(base, user_value, *, must_exist=False):
    if not isinstance(user_value, str):
        raise TypeError("경로 입력은 문자열이어야 합니다")
    if not user_value.strip():
        raise ValueError("경로가 비어 있습니다")

    raw_path = Path(user_value)
    if raw_path.is_absolute():
        raise ValueError("절대 경로는 허용하지 않습니다")

    resolved_base = Path(base).resolve(strict=True)
    candidate = (resolved_base / raw_path).resolve(
        strict=must_exist,
    )

    if not candidate.is_relative_to(resolved_base):
        raise ValueError("허용된 디렉터리 밖의 경로입니다")

    return candidate
```

기준 디렉터리는 먼저 만들어져 있어야 한다.

```python
lab_root = Path("file-lab").resolve()
lab_root.mkdir(parents=True, exist_ok=True)

safe_output = resolve_under(
    lab_root,
    "output/report.json",
    must_exist=False,
)
print(safe_output)
```

기존 입력 파일은 `must_exist=True`로 확인한다.

```python
try:
    input_path = resolve_under(
        lab_root,
        "input/users.txt",
        must_exist=True,
    )
except FileNotFoundError as exc:
    print("입력 파일이 없습니다:", exc)
```

### 문자열 접두 비교를 사용하지 않는 이유

다음 검사는 안전하지 않다.

```python
if str(candidate).startswith(str(resolved_base)):
    print("허용")
```

`/srv/lab-other`도 문자열상 `/srv/lab`으로 시작할 수 있고 운영체제별 대소문자·구분자 문제도 있다. 경로 구성요소를 이해하는 `is_relative_to()`를 사용한다.

### 검증 입력 예

| 사용자 입력 | 예상 결과 | 이유 |
| --- | --- | --- |
| `input/users.txt` | 허용 | 기준 디렉터리 내부 상대 경로 |
| `input/../input/users.txt` | 허용 | 존재하는 경로 구성요소를 정리한 내부 경로 |
| `../outside.txt` | 거부 | 상위 디렉터리로 이탈 |
| `/etc/passwd` | 거부 | 절대 경로 |
| 빈 문자열 | 거부 | 대상이 명확하지 않음 |
| 외부를 가리키는 링크 아래 경로 | 거부 | `resolve()` 후 기준 밖 |

이 검사는 기본적인 작업 범위 제한이다. 검사 뒤 실제 사용 전에 링크나 디렉터리가 교체되는 경쟁 조건까지 완전히 해결하지는 않는다. 운영 환경에서는 최소 권한, 컨테이너·샌드박스, 운영체제 수준의 안전한 파일 열기 정책을 함께 사용한다.

## 12. 경로 오류 진단 순서

파일을 찾지 못하거나 잘못된 파일을 열었을 때 다음 순서로 확인한다.

1. `Path.cwd()`로 현재 작업 디렉터리를 출력한다.
2. 원래 입력이 상대 경로인지 절대 경로인지 확인한다.
3. `resolve(strict=False)` 결과를 출력한다.
4. 존재해야 한다면 `resolve(strict=True)`로 검증한다.
5. `is_file()`, `is_dir()`, `is_symlink()`로 종류를 확인한다.
6. 사용자 입력이면 허용된 기준 디렉터리 안인지 확인한다.
7. 실제 작업의 `FileNotFoundError`, `PermissionError`를 구분한다.

오류 메시지에는 원본 비밀번호·토큰 같은 민감정보를 포함하지 않는다.

## 13. 개념 확인 문제

### 문제 1

`Path("data/users.txt")`를 만들면 파일도 생성되는가?

<details>
<summary>정답 보기</summary>

아니다. `Path`는 경로를 표현한다. 파일 생성은 `open()`, `touch()`, `write_text()` 같은 별도 작업이 필요하다.

</details>

### 문제 2

다음 프로그램을 서로 다른 디렉터리에서 실행하면 `path`가 항상 같은 파일을 가리키는가?

```python
path = Path("data/users.txt")
```

<details>
<summary>정답 보기</summary>

아니다. `Path("data/users.txt")`는 파일 시스템의 시작 위치부터 표현하지 않았으므로 상대 경로다. 기본 기준 위치인 현재 작업 디렉터리가 바뀌면 가리키는 대상도 달라질 수 있다.

</details>

### 문제 3

`resolve()`를 호출했으므로 사용자 경로가 안전하다고 말할 수 있는가?

<details>
<summary>정답 보기</summary>

아니다. 정리된 결과가 허용된 기준 디렉터리 안에 있는지 별도로 확인해야 한다.

</details>

### 문제 4

`path.is_file()`이 `False`이면 반드시 디렉터리인가?

<details>
<summary>정답 보기</summary>

아니다. 존재하지 않거나, 디렉터리·링크·특수 파일 등 다른 대상일 수 있다. 필요한 판정을 각각 수행한다.

</details>

### 문제 5

`path.is_absolute()`가 `True`이면 그 경로는 반드시 존재하고 안전하게 사용할 수 있는가?

<details>
<summary>정답 보기</summary>

아니다. `is_absolute()`는 경로가 파일 시스템의 시작 위치부터 표현되었는지만 판별한다. 존재 여부는 `exists()`, 대상 종류는 `is_file()`·`is_dir()`, 허용 범위는 별도의 경로 검증으로 확인해야 한다.

</details>

## 14. 단계별 실습: 안전한 파일 목록 보고서

### 실습 상황

교사가 제공한 `file-lab/input` 디렉터리에서 `.txt` 파일만 찾아 다음 정보를 리스트로 반환한다.

```python
{
    "name": "users.txt",
    "relative_path": "input/users.txt",
    "size_bytes": 128,
}
```

### 인수 조건

- 기준 디렉터리가 없으면 `FileNotFoundError`를 발생시킨다.
- 빈 사용자 입력과 절대 경로를 거부한다.
- 기준 디렉터리 밖으로 나가는 경로를 거부한다.
- 디렉터리와 심볼릭 링크를 결과에서 제외한다.
- `.txt` 파일만 포함한다.
- 결과는 상대 경로 문자열을 기준으로 정렬한다.
- 원본 파일을 만들거나 수정하거나 삭제하지 않는다.

### 학습자용 TODO 골격

```python
from pathlib import Path


def resolve_under(base, user_value, *, must_exist=False):
    # TODO: 입력 자료형·빈 값·절대 경로 검사
    # TODO: 기준 경로와 후보 경로 resolve
    # TODO: is_relative_to로 범위 검사
    raise NotImplementedError


def collect_text_files(base, user_directory):
    directory = resolve_under(
        base,
        user_directory,
        must_exist=True,
    )

    # TODO: directory인지 확인
    # TODO: 한 단계 아래의 .txt 일반 파일만 선택
    # TODO: 이름·상대 경로·크기를 딕셔너리로 구성
    # TODO: 안정된 순서로 반환
    raise NotImplementedError
```

### 권장 구현 순서

1. 정상 상대 경로 한 건을 절대 경로로 변환한다.
2. 빈 값과 절대 경로를 거부한다.
3. `..` 이탈 입력을 거부한다.
4. 존재하는 디렉터리인지 확인한다.
5. `.txt` 일반 파일만 필터링한다.
6. 기준 디렉터리에 대한 상대 경로를 저장한다.
7. 결과를 정렬하고 경계 입력을 검증한다.

### 검증 행렬

| 구분 | 입력 | 기대 결과 |
| --- | --- | --- |
| 정상 | `input` | `.txt` 일반 파일 목록 |
| 정상 | `input/../input` | 존재하는 경로 구성요소를 정리한 뒤 같은 목록 |
| 경계 | 비어 있는 디렉터리 | 빈 리스트 |
| 경계 | 이름이 `.txt`인 디렉터리 | 결과에서 제외 |
| 오류 | 빈 문자열 | `ValueError` |
| 오류 | 절대 경로 | `ValueError` |
| 오류 | `../outside` | `ValueError` |
| 오류 | 존재하지 않는 경로 | `FileNotFoundError` |
| 오류 | 일반 파일을 디렉터리로 전달 | `NotADirectoryError` |

### 구현 후 확인 예

```python
lab_root = Path("file-lab").resolve()

records = collect_text_files(lab_root, "input")

assert isinstance(records, list)
assert all(record["name"].endswith(".txt") for record in records)
assert all(not Path(record["relative_path"]).is_absolute() for record in records)
assert records == sorted(
    records,
    key=lambda record: record["relative_path"],
)
```

## 15. 흔한 실수와 수정 방향

| 흔한 실수 | 문제 | 수정 방향 |
| --- | --- | --- |
| Python 파일 위치와 현재 작업 디렉터리를 같다고 생각함 | 실행 위치에 따라 파일을 못 찾음 | `Path.cwd()`와 실행 명령 확인 |
| 경로를 문자열 `+`로 결합 | 구분자·슬래시 오류 | `Path / "child"` 사용 |
| 절대 경로 입력을 기준 경로와 바로 결합 | 기준 경로가 무시될 수 있음 | 결합 전 `is_absolute()` 검사 |
| `resolve()`만 호출 | 기준 디렉터리 이탈을 놓침 | `is_relative_to()` 추가 |
| `str.startswith()`로 포함 관계 검사 | 비슷한 이름의 다른 경로 허용 | 경로 구성요소 기반 검사 |
| `exists()` 결과만 신뢰 | 검사 뒤 상태 변경 가능 | 실제 작업 예외도 처리 |
| `is_file()`만 확인 | 링크 정책을 놓침 | 필요한 경우 `is_symlink()` 먼저 확인 |
| `rglob("*")` 사용 | 범위가 불필요하게 커짐 | 필요한 확장자·깊이로 제한 |
| 탐색 순서를 그대로 사용 | 환경마다 결과 순서 변화 | `sorted()` 적용 |
| `suffix`로 `.tar.gz` 전체를 기대 | 마지막 `.gz`만 반환 | `suffixes` 사용 |

## 16. 완료 기준

- [ ] `Path` 객체 생성과 실제 파일 생성을 구분할 수 있다.
- [ ] 현재 작업 디렉터리와 스크립트 디렉터리의 차이를 설명할 수 있다.
- [ ] 상대·절대 경로를 판별하고 목적에 맞는 기준 경로를 선택할 수 있다.
- [ ] `name`, `stem`, `suffix`, `suffixes`, `parent`, `parts`를 사용할 수 있다.
- [ ] `resolve(strict=False)`와 `resolve(strict=True)`를 구분할 수 있다.
- [ ] 파일·디렉터리·심볼릭 링크를 구분할 수 있다.
- [ ] `iterdir()`, `glob()`, `rglob()`의 탐색 범위를 설명할 수 있다.
- [ ] 파일 크기와 수정 시각을 메타데이터로 조회할 수 있다.
- [ ] 빈 값·절대 경로·기준 경로 이탈을 거부할 수 있다.
- [ ] 문자열 접두 비교 대신 `is_relative_to()`를 사용할 수 있다.
- [ ] 정상·오류·경계 입력으로 경로 함수를 검증할 수 있다.
- [ ] 원본 파일을 변경하지 않고 파일 목록 보고서를 만들 수 있다.

---

다음 절: [04-2. 파일·디렉터리 조작과 작업 범위](04-2-filesystem-operations.md)
