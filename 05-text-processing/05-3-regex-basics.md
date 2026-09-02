# 05-3. 정규표현식 기초

정규표현식은 정확한 문자열 하나가 아니라 **일정한 형태를 따르는 문자열 집합**을 패턴으로 표현한다. 예를 들어 `AB-2026`과 `XY-0042`는 값은 다르지만 `영문 대문자 2자리-숫자 4자리`라는 같은 형태를 가진다. 정규표현식은 강력하지만, 표준 형식의 전용 파서나 간단한 문자열 메서드를 대체하는 도구는 아니다.

{% hint style="info" %}
### 🧭 학습 목표

- raw string으로 패턴을 작성한다.
- 문자 클래스·수량자·앵커의 의미를 설명한다.
- `search()`, `match()`, `fullmatch()`, `findall()`, `finditer()`를 목적에 맞게 선택한다.
- ASCII 범위와 유니코드 범위의 차이를 검증한다.
- 탐욕적·비탐욕적 수량자의 결과를 비교한다.
- 정상·오류·경계 입력을 함께 사용해 패턴을 검증한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | raw string, 문자 클래스, 수량자, `fullmatch()`, `search()` |
| 권장 | `compile()`, 함수 선택, 탐욕성, `re.escape()`, 성공·실패 테스트 |
| 선택 | 유니코드 범위, 플래그, 복잡한 반복 패턴의 성능 위험 |

## 학습 방법

패턴을 한 번에 길게 작성하지 않는다. 고정 문자열 → 문자 범위 → 반복 횟수 → 전체 일치 순서로 확장하고, 매 단계마다 일치해야 하는 값과 일치하면 안 되는 값을 함께 추가한다.

- 학습자용 TODO Notebook: [`notebooks/05-3-regex-basics.ipynb`](../notebooks/05-3-regex-basics.ipynb)
- 실습 데이터: [`fixtures/05-text-processing/regex-cases.txt`](../fixtures/05-text-processing/regex-cases.txt)

## 선행 지식

- 05-2의 문자열 검색·분리 메서드를 이해해야 한다.
- 역슬래시 이스케이프와 raw string의 차이를 설명할 수 있어야 한다.
- 조건문·반복문·함수·예외 처리를 사용할 수 있어야 한다.

## 0. 학습 전 확인

다음 코드를 실행하기 전에 각 결과가 `True`인지 `False`인지 예상한다.

```python
import re

print(bool(re.search(r"[0-9]+", "order 125 completed")))
print(bool(re.match(r"[0-9]+", "order 125 completed")))
print(bool(re.fullmatch(r"[A-Z]{2}-[0-9]{4}", "AB-2026")))
print(bool(re.fullmatch(r"[A-Z]{2}-[0-9]{4}", "AB-2026\n")))
print(bool(re.fullmatch(r"\d+", "１２３")))
```

다음 질문에도 답해 본다.

1. 입력 전체를 검증할 때 `search()`를 사용하면 어떤 문제가 생기는가?
2. `\d`는 `[0-9]`와 항상 같은 문자에 일치하는가?
3. 사용자가 입력한 `.`, `*`, `?`를 패턴에 그대로 붙여도 되는가?

## 1. `re`와 raw string

Python 표준 라이브러리의 `re` 모듈을 가져와서 정규표현식을 사용한다.

```python
import re

pattern = r"[0-9]+"
text = "order 125 completed"
result = re.search(pattern, text)

if result is not None:
    print(result.group())  # 125
```

정규표현식과 Python 문자열은 모두 역슬래시를 특별하게 해석할 수 있다. `r"..."` 형태의 raw string을 사용하면 Python 문자열 단계의 이스케이프를 줄이고 패턴을 읽기 쉽게 만든다.

```python
print("\n" == r"\n")  # False
print(repr("\n"))       # '\n'을 나타내는 개행 문자
print(repr(r"\n"))      # 역슬래시와 n
```

raw string도 마지막이 홀수 개의 역슬래시로 끝나면 작성할 수 없다. 이런 값을 패턴으로 조합해야 한다면 표현을 나누거나 `re.escape()`를 사용한다.

## 2. 패턴 객체 컴파일

같은 패턴을 반복 사용하면 `re.compile()`로 패턴 객체를 만든다. 패턴 이름에는 검증하는 형태가 드러나야 한다.

```python
EVENT_ID_PATTERN = re.compile(
    r"[A-Z]{2}-[0-9]{4}"
)

for value in ["AB-2026", "X-20", "AB-2026-extra"]:
    print(value, bool(EVENT_ID_PATTERN.fullmatch(value)))
```

상수로 사용하는 패턴은 보통 대문자 이름으로 두어 함수 내부에서 반복해 만들지 않는다.

## 3. 문자 클래스와 범위

| 패턴 | Python 기본 동작 | ASCII로 제한할 때 |
| --- | --- | --- |
| `\d` | 유니코드 십진 숫자 | `[0-9]` 또는 `re.ASCII` |
| `\w` | 유니코드 문자·숫자·밑줄 | `[A-Za-z0-9_]` 또는 `re.ASCII` |
| `\s` | 여러 유니코드 공백 문자 | `[ \t\r\n]` 등으로 명시 |
| `.` | 기본적으로 줄바꿈을 제외한 문자 | 필요한 범위를 문자 클래스로 명시 |

```python
print(bool(re.fullmatch(r"\d+", "１２３")))     # True
print(bool(re.fullmatch(r"[0-9]+", "１２３")))  # False
```

식별자·포트·상태 코드처럼 프로토콜이 ASCII 범위를 요구하면 `[0-9]`, `[A-Fa-f]` 같이 범위를 명시한다. 사용자 이름처럼 여러 언어를 허용해야 하면 ASCII로 제한하지 않는다.

다음 문자 클래스도 자주 사용한다.

| 패턴 | 의미 |
| --- | --- |
| `[ABC]` | A, B, C 중 하나 |
| `[^ABC]` | A, B, C가 아닌 문자 |
| `[A-Z]` | A부터 Z까지의 ASCII 대문자 |
| `\.` | 임의 문자가 아닌 점 자체 |

## 4. 수량자

| 패턴 | 의미 |
| --- | --- |
| `*` | 0회 이상 |
| `+` | 1회 이상 |
| `?` | 0회 또는 1회 |
| `{3}` | 정확히 3회 |
| `{2,4}` | 2회에서 4회 |
| `{2,}` | 2회 이상 |

```python
text = "IDs: A-12, B-345, C-7"
ids = re.findall(r"[A-Z]-[0-9]+", text)

print(ids)
```

`*`와 `?`는 0회 일치도 허용하므로 빈 문자열이 의도치 않게 성공하지 않는지 확인한다.

```python
OPTIONAL_DIGITS = re.compile(r"[0-9]*")
REQUIRED_DIGITS = re.compile(r"[0-9]+")

print(bool(OPTIONAL_DIGITS.fullmatch("")))  # True
print(bool(REQUIRED_DIGITS.fullmatch("")))  # False
```

## 5. 전체 입력과 일부 입력 검색

| 함수 | 일치 범위 | 주요 목적 |
| --- | --- | --- |
| `search()` | 문자열 어느 위치에서든 첫 일치 | 본문 내부 검색 |
| `match()` | 문자열 시작 위치의 일치 | 접두 형태 확인 |
| `fullmatch()` | 문자열 전체 일치 | 입력 형식 검증 |
| `findall()` | 모든 일치값 목록 | 값 목록 추출 |
| `finditer()` | 모든 Match 객체 반복자 | 값·위치·그룹 추출 |

```python
text = "ID=AB-2026"

print(re.search(r"AB-[0-9]+", text))
print(re.match(r"AB-[0-9]+", text))
print(re.fullmatch(r"AB-[0-9]+", text))
print(re.findall(r"[0-9]+", text))
```

입력 검증에는 `^...$`보다 `fullmatch()`가 의도를 더 직접 표현한다. `$`는 문자열 끝의 최종 개행 직전에도 일치할 수 있으므로, 전체 검증은 `fullmatch()`로 확인한다.

```python
pattern_with_anchors = re.compile(r"^[A-Z]{2}-[0-9]{4}$")
pattern_for_fullmatch = re.compile(r"[A-Z]{2}-[0-9]{4}")

print(bool(pattern_with_anchors.match("AB-2026\n")))  # True
print(bool(pattern_for_fullmatch.fullmatch("AB-2026\n")))  # False
```

## 6. 탐욕적·비탐욕적 수량자

`*`와 `+`는 기본적으로 가능한 많은 문자와 일치하는 탐욕적 수량자다. 뒤에 `?`를 붙이면 가능한 적은 문자와 일치한다.

```python
text = "<b>one</b><b>two</b>"

print(re.findall(r"<b>.*</b>", text))
print(re.findall(r"<b>.*?</b>", text))
```

비탐욕적 수량자로 바꿔도 HTML의 중첩·속성·주석·잘못된 문서를 완전히 파싱할 수는 없다. HTML·JSON·CSV·URL은 해당 형식의 전용 파서를 사용한다.

## 7. 동적 문자열은 `re.escape()`로 이스케이프하기

패턴 일부에 사용자·파일의 문자열을 **문자 그대로** 붙여야 한다면 `re.escape()`를 사용한다.

```python
literal = "report.2026[final]"
unsafe_pattern = re.compile(literal)
safe_pattern = re.compile(re.escape(literal))

print(bool(unsafe_pattern.fullmatch(literal)))
print(bool(safe_pattern.fullmatch(literal)))
```

사용자가 입력한 정규표현식 자체를 그대로 실행하는 기능은 단순한 문자열 검색과 다르다. 복잡한 패턴은 입력 길이에 따라 매우 오래 실행될 수 있으므로 학습 예제에서는 프로그램이 정의한 패턴만 사용한다.

## 8. 플래그로 일치 규칙 조정하기

```python
case_insensitive = re.compile(
    r"error|warning",
    re.IGNORECASE,
)

multiline_start = re.compile(
    r"^ERROR",
    re.MULTILINE,
)

print(case_insensitive.findall("Error and WARNING"))
print(multiline_start.findall("INFO one\nERROR two"))
```

- `re.IGNORECASE`: 대소문자를 무시한다.
- `re.MULTILINE`: `^`와 `$`가 전체 문자열뿐 아니라 각 행의 시작·끝에도 일치하게 한다.
- `re.DOTALL`: `.`이 줄바꿈에도 일치하게 한다.
- `re.ASCII`: `\d`, `\w`, `\s`의 범위를 ASCII 중심으로 제한한다.

플래그는 패턴 전체의 의미를 바꾸므로 상수 이름과 주변 설명으로 의도를 남긴다.

## 9. 오류·경계 사례

| 상황 | 문제 | 수정 방향 |
| --- | --- | --- |
| 입력 검증에 `search()` 사용 | 일부만 일치해도 성공한다. | `fullmatch()`를 사용한다. |
| `^...$`만으로 전체 검증 | 최종 개행 직전에 `$`가 일치할 수 있다. | `fullmatch()`로 검증한다. |
| ASCII 숫자를 `\d`로 표현 | 전각 숫자 등 유니코드 숫자도 일치할 수 있다. | `[0-9]` 또는 `re.ASCII`를 사용한다. |
| `.*`로 모든 필드 표현 | 필드 경계를 넘거나 예상보다 많이 일치한다. | 허용 문자와 최대 길이를 구체적으로 정한다. |
| `*`, `?`의 0회 일치 무시 | 빈 문자열도 성공할 수 있다. | 빈 값 허용 여부를 테스트한다. |
| 외부 문자열을 패턴에 그대로 삽입 | `.`, `*`, `[` 등이 메타 문자로 해석된다. | 문자 그대로 찾을 때는 `re.escape()`를 사용한다. |
| 중첩된 반복과 매우 긴 입력 | 실패 여부를 확인하는 데 오래 걸릴 수 있다. | 패턴·입력 길이를 제한하고 단순한 패턴으로 나눈다. |
| HTML·JSON·CSV 전체를 정규표현식으로 파싱 | 중첩·이스케이프·줄바꿈 규칙을 놓친다. | 표준·전용 파서를 사용한다. |

## 10. 단계별 실습

[`regex-cases.txt`](../fixtures/05-text-processing/regex-cases.txt)의 성공·실패 사례를 사용해 패턴을 검증한다.

### 패턴 과제

1. `AB-2026` 형태의 ASCII 식별자
2. 문자열 안의 세 자리 이상 ASCII 숫자
3. `.txt` 또는 `.csv`로 끝나는 안전한 파일명
4. `INFO`, `WARNING`, `ERROR` 중 하나로 시작하는 행
5. 공백으로 구분된 여러 식별자

### 인수 조건

1. 각 패턴에 성공해야 하는 값과 실패해야 하는 값을 최소 세 개씩 준비한다.
2. 전체 입력 검증은 `fullmatch()`를 사용한다.
3. 식별자·숫자 패턴은 ASCII 범위를 명시한다.
4. 빈 문자열, 최종 개행, 한 문자 부족·초과, 유니코드 숫자를 경계 입력에 포함한다.
5. 기대값과 실제 결과가 다르면 케이스 ID가 포함된 메시지로 실패한다.

### TODO 골격

```python
import re

student_pattern = re.compile(
    r"TODO"
)

cases = [
    # (case_id, value, expected)
]

for case_id, value, expected in cases:
    actual = bool(student_pattern.fullmatch(value))
    assert actual == expected, (
        f"{case_id}: expected={expected}, actual={actual}, value={value!r}"
    )
```

정답 패턴을 먼저 보지 말고 케이스 표를 완성한 뒤 TODO를 구현한다. 패턴이 동작하면 실패 입력을 하나씩 더 추가해 범위가 지나치게 넓지 않은지 확인한다.

## 11. 자기점검

1. raw string은 정규표현식 자체의 역슬래시까지 없애는가?
2. `\d`와 `[0-9]`은 어떤 입력에서 다른 결과를 내는가?
3. `match()`와 `fullmatch()`의 검색 범위는 어떻게 다른가?
4. `$`를 사용한 패턴이 최종 개행을 허용할 수 있는 이유는 무엇인가?
5. 동적 문자열에 `re.escape()`가 필요한 조건은 무엇인가?
6. 탐욕성을 줄이면 HTML 파싱 문제가 완전히 해결되는가?

```python
assert EVENT_ID_PATTERN.fullmatch("AB-2026") is not None
assert EVENT_ID_PATTERN.fullmatch("AB-2026\n") is None
assert EVENT_ID_PATTERN.fullmatch("A-2026") is None
assert EVENT_ID_PATTERN.fullmatch("AB-２０２６") is None
```

## 12. 응용 인사이트

정규표현식은 **형태를 검사하는 1차 필터**다. 날짜 `2026-02-31`은 `숫자 4자리-숫자 2자리-숫자 2자리`라는 형태에 일치하지만 실제 날짜는 아니다. IP주소 `999.999.999.999`도 숫자와 점의 형태만으로는 통과할 수 있다.

따라서 실무 검증은 다음 순서로 나눈다.

```text
문자열 정규화
→ 정규표현식으로 형태 확인
→ datetime·ipaddress 같은 전용 도구로 의미 검증
→ 업무 범위·허용 정책 검증
```

잘 작성된 패턴은 일치해야 할 값을 찾는 규칙인 동시에, 일치하면 안 되는 값을 거르는 계약이다. 패턴과 테스트 케이스를 함께 관리해야 규칙을 바꾸었을 때 누락을 줄일 수 있다.

## 완료 기준

- [ ] raw string과 정규표현식 이스케이프의 관계를 설명할 수 있다.
- [ ] 문자 클래스·수량자·앵커를 읽고 작성할 수 있다.
- [ ] 검색은 `search()`, 전체 검증은 `fullmatch()`로 구분할 수 있다.
- [ ] ASCII 숫자와 유니코드 숫자 범위를 의도하게 선택할 수 있다.
- [ ] 성공·실패·경계 케이스로 패턴을 검증할 수 있다.
- [ ] 정규표현식의 형태 검증과 전용 도구의 의미 검증을 구분할 수 있다.

---

다음 절: [05-4. 그룹과 캡처](05-4-groups-capture.md)
