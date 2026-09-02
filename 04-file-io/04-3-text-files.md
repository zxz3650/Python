# 04-3. 텍스트 파일·모드·with·줄바꿈

텍스트 파일 입출력은 파일의 바이트를 지정한 인코딩으로 해석해 `str`로 읽거나, `str`을 인코딩해 파일에 저장하는 작업이다. 파일을 열 때는 읽기·쓰기 목적에 맞는 모드와 인코딩을 명시하고, `with`로 파일 자원의 수명을 관리한다. 이 절에서는 전체 읽기와 줄 단위 처리, 덮어쓰기와 추가, 줄바꿈 정규화의 차이를 익힌다.

{% hint style="info" %}
### 🧭 학습 목표

- 읽기·쓰기·추가·배타적 생성 모드를 구분한다.
- `with`를 사용해 정상 실행과 예외 발생 모두에서 파일을 닫는다.
- 파일 크기와 처리 목적에 따라 전체 읽기와 줄 단위 읽기를 선택한다.
- `write()`, `writelines()`, `join()`의 줄바꿈 책임을 설명한다.
- 덮어쓰기와 추가 모드에서 데이터가 손실되거나 이어 붙는 실수를 방지한다.
- 줄바꿈 정규화와 원본 줄바꿈 보존 요구를 구분한다.
{% endhint %}

## 선행 지식

04-1의 경로 검증과 04-2의 파일 변경·충돌 정책을 이해해야 한다. 이 절의 예제 경로는 모두 실습 디렉터리 안에서 사용한다.

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | `r`·`w`·`a`·`x`, `encoding="utf-8"`, `with`, `read()`, 파일 객체 반복 |
| 권장 | `write()`·`writelines()`, 줄 끝 처리, 구체적인 읽기 예외 |
| 심화 | `newline=None`과 `newline=""` 비교, 원본 줄바꿈 조사 |

전용 실습은 [`notebooks/04-3-text-files.ipynb`](../notebooks/04-3-text-files.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

다음 코드에서 기존 `message.txt`가 이미 있다면 파일 내용이 어떻게 바뀔지 예상한다.

```python
from pathlib import Path

path = Path("message.txt")

with path.open("w", encoding="utf-8") as file:
    file.write("new\n")
```

다음 질문에도 답해 본다.

1. `w`와 `a`는 기존 파일을 다루는 방식이 어떻게 다른가?
2. `writelines(["alpha", "beta"])`의 결과에 줄바꿈이 생기는가?
3. `strip()`과 줄바꿈 하나만 제거하는 처리는 어떤 차이가 있는가?
4. 큰 로그 파일을 `read()`로 한 번에 읽지 않아야 하는 이유는 무엇인가?

## 1. 실습 디렉터리 준비

```python
from pathlib import Path

lab_root = Path("file-lab").resolve()
text_dir = lab_root / "text"
text_dir.mkdir(parents=True, exist_ok=True)
```

이후 예제는 같은 Python 파일에서 순서대로 실행한다고 가정한다. 외부 입력으로 경로를 받는 프로그램에서는 04-1의 `resolve_under()`로 경로를 먼저 검증한다.

## 2. 텍스트 파일 모드

| 모드 | 목적 | 파일이 없을 때 | 파일이 있을 때 |
| --- | --- | --- | --- |
| `r` | 읽기 | `FileNotFoundError` | 기존 내용을 읽음 |
| `w` | 새 내용 쓰기 | 새로 만듦 | **열 때 기존 내용을 비움** |
| `a` | 내용 추가 | 새로 만듦 | 기존 내용 끝에 씀 |
| `x` | 새 파일만 생성 | 새로 만듦 | `FileExistsError` |

모드 문자에는 다음 접미사를 조합할 수 있다.

| 접미사 | 의미 | 주의점 |
| --- | --- | --- |
| `t` | 문자열을 처리하는 텍스트 모드 | 기본값이므로 `r`과 `rt`는 같은 의미다. |
| `b` | 바이트를 처리하는 바이너리 모드 | 인코딩을 지정하지 않으며 04-4에서 다룬다. |
| `+` | 한 파일 객체에서 읽기와 쓰기를 모두 허용 | 앞의 `r`·`w`·`a`·`x`가 정한 생성·삭제·추가 정책은 그대로 적용되며 파일 위치도 관리해야 한다. |

예를 들어 `r+`는 기존 파일을 비우지 않고 읽고 쓸 수 있지만 파일이 없으면 실패하고, `w+`는 읽기도 가능하지만 기존 파일을 먼저 비운다. 처음 배우는 코드에서는 하나의 파일 객체에 여러 책임을 섞기보다 읽기와 쓰기의 목적을 나누고 기본 모드를 명시한다.

{% hint style="warning" %}
`w` 모드는 첫 번째 `write()`를 호출할 때가 아니라 파일을 성공적으로 여는 시점에 기존 내용을 비운다. 기존 파일을 보존해야 한다면 `x`, `a`, 별도 출력 경로, 04-8의 원자적 교체 중 요구사항에 맞는 정책을 선택한다.
{% endhint %}

## 3. with로 파일 열고 닫기

```python
path = text_dir / "message.txt"

with path.open("w", encoding="utf-8") as file:
    file.write("첫 번째 줄\n")
    file.write("두 번째 줄\n")
```

`with` 블록이 끝나면 정상 실행과 예외 발생 여부에 관계없이 파일이 닫힌다. 닫힌 파일 객체에는 더 이상 읽기·쓰기를 시도하지 않는다.

```python
with path.open("r", encoding="utf-8") as file:
    print("블록 안:", file.closed)   # False

print("블록 밖:", file.closed)     # True
```

`with`는 파일을 닫는 책임을 해결하지만, 쓰던 데이터를 논리적으로 올바른 상태로 되돌리거나 기존 파일을 자동 복구하지는 않는다. 중요한 파일의 완전한 저장은 04-8의 임시 파일과 교체 절차로 처리한다.

## 4. 전체 내용 읽기와 쓰기

```python
with path.open("r", encoding="utf-8") as file:
    text = file.read()

print(text)
print(type(text))  # str
```

`read()`는 현재 위치부터 파일 끝까지 읽어 하나의 문자열을 만든다. 크기가 작다고 확인한 설정 파일이나 템플릿처럼 전체 내용이 한 번에 필요할 때 사용한다.

`Path`의 편의 메서드는 파일을 내부에서 열고 닫는다.

```python
text = path.read_text(encoding="utf-8")
print(text)

written_count = path.write_text("새 내용\n", encoding="utf-8")
print("쓴 문자 수:", written_count)
```

`read_text()`도 전체 파일을 메모리에 올리고, `write_text()`도 기본적으로 기존 내용을 덮어쓴다. 큰 파일이라는 사실을 알고 있다면 편리함만 보고 선택하지 않는다.

## 5. 한 줄씩 읽기

```python
with path.open("r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        clean = line.removesuffix("\n")
        print(line_number, clean)
```

파일 객체는 반복 가능한 객체다. 반복할 때 한 줄씩 가져오므로 전체 파일을 한꺼번에 문자열로 만들지 않는다. 마지막 줄에 줄바꿈이 없어도 `removesuffix("\n")`는 다른 문자를 지우지 않는다.

기본 `newline=None`으로 읽으면 `\n`, `\r\n`, `\r`이 문자열의 `\n`으로 정규화된다. 이 조건에서 `removesuffix("\n")`로 줄 끝 하나만 제거할 수 있다. 반면 `strip()`은 앞뒤 공백·탭까지 제거하므로 들여쓰기나 고정 폭 데이터에 의미 있는 공백을 잃을 수 있다.

```python
sample = "  ALLOW  \n"

print(repr(sample.removesuffix("\n")))  # '  ALLOW  '
print(repr(sample.strip()))               # 'ALLOW'
```

`readlines()`는 줄 단위 문자열의 리스트를 만들지만 결국 모든 줄을 메모리에 저장한다. 큰 파일의 스트리밍 처리에는 파일 객체를 직접 반복한다.

## 6. 여러 줄 쓰기

`write()`는 전달한 문자열만 쓴다. 줄을 구분하려면 `\n`을 직접 포함한다.

```python
items_path = text_dir / "items.txt"
lines = ["alpha\n", "beta\n", "gamma\n"]

with items_path.open("w", encoding="utf-8") as file:
    file.writelines(lines)
```

`writelines()`는 이름과 달리 줄바꿈을 자동으로 추가하지 않는다. 다음 코드는 `alphabeta`를 저장한다.

```python
with items_path.open("w", encoding="utf-8") as file:
    file.writelines(["alpha", "beta"])
```

줄바꿈이 없는 값의 목록이라면 `join()`으로 출력 형식을 명확하게 만들 수 있다.

```python
items = ["alpha", "beta", "gamma"]
items_path.write_text(
    "\n".join(items) + "\n",
    encoding="utf-8",
)
```

마지막 `+ "\n"`은 마지막 레코드도 줄바꿈으로 끝낸다는 파일 형식의 선택이다. 요구사항이 마지막 줄바꿈을 금지한다면 추가하지 않는다.

## 7. 파일 끝에 추가하기

```python
history_path = text_dir / "history.log"

with history_path.open("a", encoding="utf-8") as file:
    file.write("프로그램 실행\n")
```

`a` 모드는 기존 내용을 지우지 않고 파일 끝에 쓴다. 그러나 기존 파일이 줄바꿈 없이 끝나면 새 문자열이 마지막 줄에 그대로 이어진다.

```python
history_path.write_text("시작", encoding="utf-8")

with history_path.open("a", encoding="utf-8") as file:
    file.write("다음\n")

print(repr(history_path.read_text(encoding="utf-8")))
# '시작다음\n'
```

프로그램이 파일 전체 형식을 관리한다면 처음부터 **한 레코드를 쓸 때마다 줄바꿈까지 함께 쓴다**는 계약을 유지한다. 출처를 알 수 없는 기존 파일에 이어 쓰기 전에는 마지막 줄 경계를 어떻게 처리할지 별도 정책을 정한다.

## 8. 읽기 오류 처리

```python
missing_path = text_dir / "missing.txt"

try:
    text = missing_path.read_text(encoding="utf-8")
except FileNotFoundError as exc:
    print("파일을 찾을 수 없다:", exc.filename)
except PermissionError as exc:
    print("파일을 읽을 권한이 없다:", exc.filename)
else:
    print(text)
```

파일 없음과 권한 부족은 해결 방법이 다르므로 구분한다. `except Exception` 하나로 모든 실패를 성공처럼 숨기지 않는다. 잘못된 바이트를 텍스트로 해석할 때 발생하는 `UnicodeDecodeError`와 인코딩 선택은 04-4에서 다룬다.

## 9. 줄바꿈 처리

운영체제와 파일 생성 도구에 따라 줄 끝은 `\n`, `\r\n`, `\r`일 수 있다. 텍스트 읽기의 `newline` 인자는 어떤 줄 끝을 인식하고 반환할지 결정한다.

| 읽기 설정 | 동작 | 적합한 상황 |
| --- | --- | --- |
| `newline=None` | 여러 줄 끝을 인식하고 반환 문자열에서는 `\n`으로 정규화함 | 일반적인 줄 단위 텍스트 처리 |
| `newline=""` | 여러 줄 끝을 인식하지만 원래 줄 끝 문자를 그대로 반환함 | 원래 줄바꿈 종류 조사, `csv` 모듈 사용 |

혼합 줄바꿈을 가진 실습 파일을 만든다. `newline=""`으로 쓸 때는 문자열에 넣은 줄바꿈을 추가 변환하지 않는다.

```python
mixed_path = text_dir / "mixed-lines.txt"

with mixed_path.open("w", encoding="utf-8", newline="") as file:
    file.write("alpha\nbeta\r\ngamma\r")
```

먼저 일반 텍스트 처리 방식으로 읽는다.

```python
with mixed_path.open(
    "r",
    encoding="utf-8",
    newline=None,
) as file:
    normalized = list(file)

print(normalized)
# ['alpha\n', 'beta\n', 'gamma\n']
```

원래 줄 끝을 보존해 읽으면 차이가 보인다.

```python
with mixed_path.open(
    "r",
    encoding="utf-8",
    newline="",
) as file:
    original_endings = list(file)

print(original_endings)
# ['alpha\n', 'beta\r\n', 'gamma\r']
```

텍스트 쓰기에서 `newline=None`이면 문자열의 `\n`을 현재 운영체제의 기본 줄바꿈으로 변환할 수 있다. `newline=""` 또는 `newline="\n"`이면 `\n`을 추가 변환하지 않는다. CSV는 `csv` 모듈이 레코드의 줄바꿈을 관리하도록 파일을 `newline=""`으로 연다.

원본 바이트를 정확히 보존하거나 줄바꿈 이외의 바이트까지 조사해야 한다면 바이너리 모드로 읽는다.

## 흔한 실수

- 기존 파일에 `w` 모드를 사용해 내용을 잃음
- 파일 모드와 인코딩을 실행 환경의 기본값에 맡김
- `with` 바깥에서 닫힌 파일 객체를 사용함
- `writelines()`가 줄바꿈을 자동으로 추가한다고 생각함
- 줄바꿈 없이 끝난 파일에 `a` 모드로 바로 이어 씀
- 파일 전체를 읽은 뒤 다시 줄 단위로 처리함
- `strip()`으로 의미 있는 공백까지 제거함
- 일반 텍스트의 줄바꿈 정규화와 원본 바이트 보존을 혼동함

## 10. 개념 확인 문제

### 문제 1

`w` 모드로 기존 파일을 연 뒤 `write()` 전에 예외가 발생하면 기존 내용은 남아 있을까?

<details>
<summary>정답 보기</summary>

일반적으로 남아 있지 않는다. `w` 모드는 파일을 성공적으로 여는 시점에 기존 내용을 비운다.

</details>

### 문제 2

`with`를 사용하면 파일 내용도 예외 발생 전 상태로 자동 복구될까?

<details>
<summary>정답 보기</summary>

아니다. `with`는 블록을 벗어날 때 파일을 닫는다. 이미 기록하거나 비운 내용을 되돌리는 트랜잭션 기능은 아니다.

</details>

### 문제 3

한 줄씩 읽으면서 들여쓰기를 보존하려면 `line.strip()`이 적합할까?

<details>
<summary>정답 보기</summary>

적합하지 않다. `strip()`은 줄바꿈뿐 아니라 앞뒤 공백과 탭도 지운다. 기본 줄바꿈 정규화 상태에서는 `removesuffix("\n")`처럼 제거 범위를 명시한다.

</details>

### 문제 4

원래 파일이 `\r\n`을 사용했는지 조사할 때 `newline=None`으로 충분할까?

<details>
<summary>정답 보기</summary>

충분하지 않다. `newline=None`은 읽은 줄 끝을 `\n`으로 정규화한다. `newline=""`으로 원래 줄 끝을 보존해 읽거나 정확한 바이트가 필요하면 바이너리 모드를 사용한다.

</details>

## 11. 단계별 실습: 작업 목록과 실행 이력

### 실습 상황

작업 목록을 UTF-8 텍스트 파일에 저장하고, 행 번호와 함께 다시 읽는다. 실행 결과는 별도의 이력 파일 끝에 한 줄씩 추가한다.

### 요구사항

- 호출자가 04-1의 정책으로 검증한 `Path`만 함수에 전달한다.
- 작업 목록은 `list[str]`로 받고, 항목을 한 줄에 하나씩 저장하며 마지막 항목도 줄바꿈으로 끝낸다.
- 작업 항목 자체에 `\n`이나 `\r`이 있으면 `ValueError`를 발생시킨다.
- 새 작업 목록이 이미 있으면 덮어쓰지 않는다.
- 작업 목록은 전체 문자열이 아니라 한 줄씩 읽는다.
- 행 번호는 1부터 시작하고 작업의 앞뒤 공백은 보존한다.
- 이력 레코드는 한 번 쓸 때 줄바꿈까지 함께 추가한다.

### 학습자용 TODO 골격

```python
from pathlib import Path


def save_new_tasks(path, tasks):
    # 실습 과제: 각 항목이 str이고 줄바꿈을 포함하지 않는지 검증
    # 실습 과제: x 모드와 UTF-8로 새 파일 생성
    # 실습 과제: 한 항목과 줄바꿈을 함께 기록
    raise NotImplementedError


def load_numbered_tasks(path):
    records = []

    # 실습 과제: r 모드와 UTF-8로 열기
    # 실습 과제: enumerate(..., start=1)로 한 줄씩 반복
    # 실습 과제: 줄 끝 하나만 제거하고 (행 번호, 작업) 튜플 저장

    return records


def append_history(path, message):
    # 실습 과제: message의 자료형과 줄바꿈 포함 여부 검증
    # 실습 과제: a 모드로 message와 줄바꿈을 함께 기록
    raise NotImplementedError
```

### 권장 구현 순서

1. `file-lab/text` 디렉터리를 만든다.
2. 작업 세 건을 `x` 모드로 저장한다.
3. 같은 경로에 다시 저장해 `FileExistsError`를 확인한다.
4. 파일 객체를 반복해 `(행 번호, 작업)` 튜플 리스트를 만든다.
5. 이력 두 건을 추가하고 두 줄이 분리되었는지 다시 읽는다.
6. 없는 작업 파일을 전달해 `FileNotFoundError`를 확인한다.
7. 혼합 줄바꿈 파일을 `newline=None`과 `newline=""`으로 각각 읽어 비교한다.

### 검증 행렬

| 구분 | 입력 | 기대 결과 |
| --- | --- | --- |
| 정상 | 작업 세 건 | UTF-8 파일에 세 줄 저장 |
| 정상 | 저장된 작업 읽기 | `[(1, ...), (2, ...), (3, ...)]` 반환 |
| 정상 | 이력 두 건 추가 | 기존 내용을 유지한 두 줄 생성 |
| 경계 | 빈 작업 목록 | 빈 파일 생성 |
| 오류 | 항목 안의 `\n`·`\r` | `ValueError` |
| 오류 | 이미 존재하는 작업 파일 | `FileExistsError` |
| 오류 | 없는 입력 파일 | `FileNotFoundError` |

### 구현 후 확인 예

```python
text_dir = Path("file-lab/text").resolve()
text_dir.mkdir(parents=True, exist_ok=True)

tasks_path = text_dir / "tasks.txt"
history_path = text_dir / "history.log"

save_new_tasks(tasks_path, ["로그 확인", "  공백 보존", "보고서 저장"])

assert load_numbered_tasks(tasks_path) == [
    (1, "로그 확인"),
    (2, "  공백 보존"),
    (3, "보고서 저장"),
]

append_history(history_path, "작업 목록 읽기 성공")
append_history(history_path, "검증 완료")

assert history_path.read_text(encoding="utf-8").splitlines() == [
    "작업 목록 읽기 성공",
    "검증 완료",
]
```

{% hint style="success" %}
### ✅ 완료 기준

- [ ] 파일 모드별 생성·덮어쓰기·추가 동작을 설명할 수 있다.
- [ ] `with`를 사용해 파일을 읽고 쓸 수 있다.
- [ ] 파일 크기와 목적에 따라 전체 읽기와 줄 단위 읽기를 선택할 수 있다.
- [ ] `write()`와 `writelines()`의 줄바꿈 책임을 설명할 수 있다.
- [ ] 의미 있는 공백을 보존하면서 줄 끝만 제거할 수 있다.
- [ ] `newline=None`과 `newline=""`의 읽기 결과를 구분할 수 있다.
- [ ] 정상·오류·경계 입력으로 텍스트 입출력 함수를 검증할 수 있다.
{% endhint %}

---

다음 절: [04-4. 인코딩·bytes와 바이너리 구조](04-4-encoding-binary.md)
