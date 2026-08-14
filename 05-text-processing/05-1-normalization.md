# 05-1. 문자열 정규화

외부 텍스트는 대소문자, 공백, 줄바꿈, 유니코드 표현이 다를 수 있습니다. 정규화는 비교와 분석 전에 표현을 일관된 형태로 만드는 과정입니다.

{% hint style="info" %}
## 🧭 학습 목표

- 원문과 정규화 값을 함께 보존합니다.
- 공백·대소문자·줄바꿈을 목적에 맞게 정리합니다.
- 유니코드 정규화의 필요성을 이해합니다.
- 과도한 정규화로 정보가 손실되는 상황을 구분합니다.
{% endhint %}

## 선행 지식

문자열 메서드와 04장의 파일·인코딩을 이해해야 합니다.

## 1. 원문 보존

```python
raw = "  Alice@example.COM \n"
normalized = raw.strip().lower()

print(repr(raw))
print(repr(normalized))
```

원문은 재현을 위해 유지하고 검색·비교용 값을 별도로 만듭니다.

## 2. 공백 처리

```python
text = "  hello   world  "

print(text.strip())
print(text.lstrip())
print(text.rstrip())
print(" ".join(text.split()))
```

`strip()`은 양끝 공백을 제거하고, `" ".join(text.split())`은 연속 공백을 하나로 줄입니다.

## 3. 대소문자 정규화

```python
action = "Allow"

print(action.lower())
print(action.upper())
print(action.casefold())
```

영문 비교에는 `lower()`, 국제화 문자열의 대소문자 없는 비교에는 `casefold()`가 적합할 수 있습니다. 경로·비밀번호처럼 대소문자가 중요한 값에는 적용하지 않습니다.

## 4. 줄바꿈

```python
line = "record\r\n"

print(repr(line.rstrip("\r\n")))

text = "first\r\nsecond\nthird"
print(text.splitlines())
```

`strip()`은 공백까지 제거하지만 `rstrip("\r\n")`은 줄바꿈만 제거합니다.

## 5. 유니코드 정규화

```python
import unicodedata

a = "é"
b = "e\u0301"

print(a == b)  # False

a_nfc = unicodedata.normalize("NFC", a)
b_nfc = unicodedata.normalize("NFC", b)

print(a_nfc == b_nfc)  # True
```

화면에 같아 보이는 문자도 내부 구성이 다를 수 있습니다.

## 6. 정규화 함수

```python
def normalize_name(value):
    if not isinstance(value, str):
        raise TypeError("문자열이 필요합니다")

    clean = value.strip()
    return unicodedata.normalize("NFC", clean).casefold()
```

함수로 분리하면 모든 입력에 같은 정책을 적용할 수 있습니다.

## 흔한 실수

- 원문을 정규화 값으로 덮어씀
- 의미 있는 공백까지 삭제함
- 모든 필드를 소문자로 변경함
- 인코딩과 유니코드 정규화를 같은 개념으로 생각함

{% hint style="success" %}
## 🧪 종합 실습

이름·이메일·설명 필드를 정리합니다. 원문은 유지하고 이름은 NFC, 이메일은 공백 제거와 소문자 변환, 설명은 줄바꿈만 정리합니다.
{% endhint %}

## 완료 기준

- [ ] 원문과 정규화 값을 함께 보존할 수 있습니다.
- [ ] 필드 의미에 맞는 정규화 방법을 선택할 수 있습니다.
- [ ] 유니코드 정규화와 인코딩의 차이를 설명할 수 있습니다.

---

다음 절: [05-2. 분리·검색·치환](05-2-split-search-replace.md)
