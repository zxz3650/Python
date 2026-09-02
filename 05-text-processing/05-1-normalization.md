# 05-1. 문자열 정규화

외부에서 들어온 텍스트는 눈에 같게 보여도 대소문자, 앞뒤 공백, 줄바꿈, 유니코드 구성이 다를 수 있다. 문자열 정규화는 이러한 표현 차이를 **필드의 의미에 맞는 일관된 규칙**으로 바꾸는 과정이다. 정규화는 원문을 없애는 작업이 아니라, 원문과 비교·검색용 값을 분리하는 설계에서 시작한다.

{% hint style="info" %}
### 🧭 학습 목표

- 원문과 정규화 값을 분리해 보존한다.
- `strip()`, `lstrip()`, `rstrip()`의 범위를 구분한다.
- 줄바꿈만 제거할 때 `rstrip("\r\n")`을 사용한다.
- `lower()`와 `casefold()`를 필드 규칙에 맞게 선택한다.
- 유니코드 정규화와 텍스트 인코딩을 구분한다.
- 과도한 정규화가 정보를 손실시키는 사례를 설명한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | 원문 보존, 앞뒤 공백, 대소문자, 줄바꿈 처리 |
| 권장 | 필드별 정규화 정책, 멱등성, 유니코드 NFC |
| 선택 | `casefold()`, NFKC의 정보 변환 특성, 국제화 정책 |

## 학습 방법

각 예제에서 함수를 먼저 실행하지 말고 반환값의 `repr()` 결과를 예상한다. 실행 후에는 원문과 변경된 값을 함께 비교하고, 같은 규칙을 비밀번호·경로·설명 필드에도 적용해도 되는지 판단한다.

- 학습자용 TODO Notebook: [`notebooks/05-1-normalization.ipynb`](../notebooks/05-1-normalization.ipynb)
- 실습 데이터: [`fixtures/05-text-processing/normalization-cases.txt`](../fixtures/05-text-processing/normalization-cases.txt)

## 선행 지식

- 03-2의 문자열 메서드와 불변성을 이해해야 한다.
- 04-3과 04-4의 텍스트 파일·인코딩·줄바꿈을 이해해야 한다.
- 함수의 인자·반환값과 `TypeError`를 이해해야 한다.

## 0. 학습 전 확인

아직 실행하지 말고 각 표현식의 결과를 예상한다.

```python
print(repr("  Alice  ".strip()))
print(repr("record   \r\n".rstrip()))
print(repr("record   \r\n".rstrip("\r\n")))
print("Straße".lower() == "STRASSE".lower())
print("Straße".casefold() == "STRASSE".casefold())
```

다음 질문에도 답해 본다.

1. 이메일, 비밀번호, 파일 경로에 모두 `lower()`를 적용해도 되는가?
2. `strip()`은 문자열 중간의 연속 공백도 제거하는가?
3. 인코딩 오류가 난 `bytes`를 유니코드 정규화로 복구할 수 있는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. 원문과 비교용 값 분리

정규화는 입력을 새 규칙에 맞게 변환하므로 정보 일부를 잃을 수 있다. 재현·감사·오류 분석이 필요하면 원문을 별도 필드에 보존한다.

```python
raw = "  Alice@example.COM \n"
normalized = raw.strip().casefold()

record = {
    "raw": raw,
    "comparison_key": normalized,
}

print(repr(record["raw"]))
print(repr(record["comparison_key"]))
```

`raw`는 입력이 어떻게 들어왔는지 보여 주고, `comparison_key`는 정해진 규칙으로 비교할 때 사용한다. 단, 인증 비밀번호와 토큰은 값을 변형하지 않고 비밀 처리 정책에 따라 다룬다.

## 2. 앞뒤 공백과 내부 공백

`strip()`은 양끝, `lstrip()`은 왼쪽, `rstrip()`은 오른쪽의 공백 문자를 제거한 새 문자열을 반환한다. 원본 문자열은 바뀌지 않는다.

```python
text = "  hello   world  "

print(repr(text.strip()))
print(repr(text.lstrip()))
print(repr(text.rstrip()))
print(repr(" ".join(text.split())))
print(repr(text))
```

`" ".join(text.split())`은 문자열 중간의 연속 공백도 하나로 줄인다. 코드, 정렬된 보고서, 원문 로그처럼 공백 자체가 의미를 가지는 필드에는 적용하지 않는다.

`strip(chars)`의 인자는 제거할 **정확한 접두사·접미사**가 아니라 양끝에서 반복해 제거할 **문자 집합**이다.

```python
value = "report.txt"

print(value.rstrip(".txt"))        # 'repor'
print(value.removesuffix(".txt"))  # 'report'
```

확정된 접미사 하나를 제거할 때는 `removesuffix()`를 사용한다.

## 3. 대소문자 정규화

```python
action = "Allow"

print(action.lower())
print(action.upper())
print(action.casefold())
```

- `lower()`: 표시나 영문 중심의 소문자 변환에 사용한다.
- `upper()`: `INFO`, `ERROR` 같은 허용값을 통일할 때 사용할 수 있다.
- `casefold()`: 국제화 문자열의 대소문자를 무시한 비교에 적합하다.

```python
left = "Straße"
right = "STRASSE"

print(left.lower() == right.lower())        # False
print(left.casefold() == right.casefold())  # True
```

대소문자 무시 비교가 필요한지는 프로그램의 규칙이 결정한다. 비밀번호, 토큰, 대소문자를 구분하는 경로·식별자에 일괄적으로 적용하면 안 된다.

## 4. 줄바꿈만 제거하기

파일 반복으로 읽은 행은 보통 끝에 `\n` 또는 `\r\n`을 포함한다. 행 끝의 의미 있는 공백은 유지하고 줄바꿈만 제거할 때 `rstrip("\r\n")`을 사용한다.

```python
line = "record   \r\n"

print(repr(line.rstrip()))
print(repr(line.rstrip("\r\n")))

text = "first\r\nsecond\nthird"
print(text.splitlines())
```

`"\n"`은 개행 문자 하나이지만 `"\\n"`은 역슬래시와 알파벳 `n` 두 문자다. 두 표현을 혼동하면 줄바꿈은 남고 정상 데이터의 마지막 `n`이 사라질 수 있다.

```python
print(repr("record\n".rstrip("\\n")))  # 개행이 남는다
print(repr("session".rstrip("\\n")))  # 끝의 n이 제거된다
```

## 5. 유니코드 정규화

화면에 같아 보이는 문자도 코드 포인트 구성이 다를 수 있다.

```python
import unicodedata

composed = "é"
decomposed = "e\u0301"

print(composed == decomposed)  # False

left = unicodedata.normalize("NFC", composed)
right = unicodedata.normalize("NFC", decomposed)

print(left == right)  # True
```

일반적인 문자열 비교용 표현을 통일할 때는 주로 NFC를 검토한다. NFKC는 전각 문자, 호환 문자 등을 더 폭넓게 변환하므로 식별자·증거 원문에 무조건 적용하지 않는다.

{% hint style="warning" %}
인코딩은 `bytes`와 `str`을 변환하는 규칙이고, 유니코드 정규화는 이미 해석된 `str`의 표현을 통일하는 규칙이다. 잘못된 인코딩으로 깨진 문자열을 NFC로 복구할 수는 없다.
{% endhint %}

## 6. 필드별 정규화 정책

정규화 함수에는 어떤 정보를 바꾸는지 드러나야 한다. 하나의 `clean_everything()` 함수로 모든 필드를 같게 처리하지 않는다.

```python
import unicodedata


def normalize_display_name(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("이름은 문자열이어야 한다")

    stripped = value.strip()
    if not stripped:
        raise ValueError("이름은 비어 있을 수 없다")

    return unicodedata.normalize("NFC", stripped)


def make_name_key(value: str) -> str:
    return normalize_display_name(value).casefold()
```

```python
raw_name = "  Chloé  "

profile = {
    "name_raw": raw_name,
    "name_display": normalize_display_name(raw_name),
    "name_key": make_name_key(raw_name),
}

print(profile)
```

같은 정규화 함수를 두 번 적용해도 결과가 더 바뀌지 않는 **멱등성**을 만족하면 반복 처리 결과를 예측하기 쉬워진다.

```python
once = normalize_display_name(raw_name)
twice = normalize_display_name(once)

assert once == twice
```

## 7. 오류·경계 사례

| 입력·상황 | 잘못된 처리 | 수정 방향 |
| --- | --- | --- |
| `None`, 숫자 | 바로 `.strip()` 호출 | 자료형을 먼저 검증한다. |
| `"record   \n"` | 인자 없는 `rstrip()` | 공백이 의미 있으면 `rstrip("\r\n")`을 사용한다. |
| `"session"` | `rstrip("\\n")` | 개행 문자 `"\n"`과 역슬래시 표현을 구분한다. |
| `"report.txt"` | `rstrip(".txt")` | 정확한 접미사는 `removesuffix()`로 제거한다. |
| 비밀번호·토큰 | `strip().lower()` | 인증 규칙이 허용하지 않으면 원본을 변형하지 않는다. |
| 인코딩 오류 | 유니코드 정규화로 복구 시도 | 04-4의 디코딩 단계에서 인코딩과 오류 정책을 확인한다. |
| 내부 공백이 중요한 코드 | `split()` 후 `join()` | 앞뒤 공백만 제거하고 원문을 보존한다. |

## 8. 단계별 실습

[`normalization-cases.txt`](../fixtures/05-text-processing/normalization-cases.txt)의 각 행을 읽어 원문과 정규화 결과를 만든다.

### 인수 조건

1. 파일은 `encoding="utf-8"`, `errors="strict"`로 읽는다.
2. 원문 행에서 `\r`과 `\n`만 제거해 `raw` 필드에 보존한다.
3. 이름은 앞뒤 공백과 NFC만 적용한다.
4. 비교용 이름은 `casefold()`를 추가 적용한다.
5. 설명은 줄바꿈을 제외한 공백을 보존한다.
6. 빈 이름과 잘못된 필드 수는 행 번호·원문·원인과 함께 오류 목록에 보존한다.

### TODO 골격

```python
from pathlib import Path

FIXTURE_PATH = Path("fixtures/05-text-processing/normalization-cases.txt")


def normalize_fixture_line(line: str, line_number: int) -> tuple[dict | None, dict | None]:
    # TODO 1: 줄바꿈만 제거한 원문을 만든다.
    # TODO 2: 필드를 분리하고 개수를 검증한다.
    # TODO 3: 정상 레코드 또는 구조화된 오류를 반환한다.
    raise NotImplementedError
```

학습자용 Notebook에서 TODO를 구현한 뒤 정상·빈 값·연속 공백·조합형 유니코드·CRLF 입력을 모두 검증한다.

## 9. 자기점검

1. `strip()`과 `removesuffix()`는 제거 대상을 어떻게 다르게 해석하는가?
2. `rstrip("\\n")`이 개행 문자를 제거하지 못하는 이유는 무엇인가?
3. NFC와 인코딩은 각각 어떤 단계의 규칙인가?
4. 원문과 비교용 키를 둘 다 보존해야 하는 이유는 무엇인가?
5. 같은 정규화 함수를 두 번 적용했을 때 결과가 같아야 하는 이유는 무엇인가?

실습 결과로 다음 검증을 통과하는지 확인한다.

```python
assert normalize_display_name("  Chloé ") == "Chloé"
assert make_name_key("  ALICE ") == "alice"
assert normalize_display_name(normalize_display_name("  Alice ")) == "Alice"
```

## 10. 응용 인사이트

정규화는 단순한 문자열 정리가 아니라 **데이터 계약을 정의하는 작업**이다. 로그 수집기, API, 데이터베이스가 서로 다른 정규화 규칙을 사용하면 같은 사용자·경로·상태가 여러 값으로 나뉘어 집계된다. 반대로 규칙을 너무 강하게 적용하면 서로 다른 값이 하나로 합쳐진다.

따라서 실무 코드에서는 다음 네 가지를 함께 기록한다.

1. 정규화 대상 필드
2. 적용 순서와 함수
3. 원문 보존 여부
4. 규칙이 바뀌었을 때 기존 데이터를 다시 처리할 방법

## 완료 기준

- [ ] 원문과 정규화 값을 분리해 보존할 수 있다.
- [ ] 필드 의미에 맞는 공백·대소문자 규칙을 선택할 수 있다.
- [ ] `rstrip("\r\n")`과 `rstrip("\\n")`의 차이를 설명할 수 있다.
- [ ] 유니코드 정규화와 텍스트 인코딩을 구분할 수 있다.
- [ ] 정상·오류·경계 입력으로 정규화 함수을 검증할 수 있다.

---

다음 절: [05-2. 분리·검색·치환](05-2-split-search-replace.md)
