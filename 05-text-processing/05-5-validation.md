# 05-5. 데이터 검증

파싱은 문자열을 나누는 작업이고 검증은 값이 요구사항을 만족하는지 확인하는 작업입니다. 형식이 맞더라도 의미와 범위가 잘못될 수 있습니다.

{% hint style="info" %}
## 🧭 학습 목표

- 필수값·자료형·허용값·범위를 단계적으로 검증합니다.
- 정규표현식 검증과 의미 검증을 구분합니다.
- 오류를 구조화해 여러 건 수집합니다.
- 검증 함수의 입력과 출력을 일관되게 설계합니다.
{% endhint %}

## 선행 지식

조건문, 예외, 정규표현식, 딕셔너리를 이해해야 합니다.

## 1. 검증 순서

권장 순서:

1. 값 존재 여부
2. 자료형
3. 문자열 형식
4. 허용값과 숫자 범위
5. 필드 간 관계

앞 단계가 실패하면 뒤 단계의 검사가 의미 없을 수 있습니다.

## 2. 필수값과 자료형

```python
def require_text(record, key):
    if key not in record:
        raise ValueError(f"필수 필드 누락: {key}")

    value = record[key]

    if not isinstance(value, str):
        raise TypeError(f"{key}는 문자열이어야 합니다")

    value = value.strip()

    if not value:
        raise ValueError(f"{key}는 비어 있을 수 없습니다")

    return value
```

## 3. 허용값

```python
ALLOWED_LEVELS = {"INFO", "WARNING", "ERROR"}

def validate_level(value):
    normalized = value.strip().upper()

    if normalized not in ALLOWED_LEVELS:
        raise ValueError(f"허용되지 않은 수준: {value}")

    return normalized
```

허용 목록이 금지 목록보다 결과를 예측하기 쉽습니다.

## 4. 형식과 의미

```python
import re

def validate_code(value):
    if not re.fullmatch(r"[A-Z]{2}-\d{4}", value):
        raise ValueError("코드 형식이 올바르지 않습니다")

    year = int(value[-4:])

    if not 2000 <= year <= 2099:
        raise ValueError("연도 범위를 벗어났습니다")

    return value
```

정규표현식은 모양을 확인하지만 실제 범위까지 보장하지는 않습니다.

## 5. 여러 오류 수집

```python
def validate_record(record):
    errors = []
    cleaned = {}

    try:
        cleaned["name"] = require_text(record, "name")
    except (ValueError, TypeError) as exc:
        errors.append(str(exc))

    try:
        cleaned["level"] = validate_level(record.get("level", ""))
    except ValueError as exc:
        errors.append(str(exc))

    return cleaned, errors
```

한 레코드의 모든 문제를 보여줄지 첫 오류에서 중단할지는 프로그램 목적에 따라 선택합니다.

## 6. 오류 구조화

```python
error_record = {
    "line": 7,
    "field": "level",
    "value": "UNKNOWN",
    "code": "INVALID_CHOICE",
    "message": "허용되지 않은 수준",
}
```

문자열 메시지만 저장하는 것보다 필드와 오류 코드를 함께 저장하면 집계하기 쉽습니다.

## 흔한 실수

- 파싱 성공을 유효성 검증 성공으로 판단함
- 숫자로 변환만 하고 범위를 확인하지 않음
- 빈 문자열과 누락값을 같게 처리함
- 검증 과정에서 원본 값을 덮어씀
- 오류 메시지 형식이 함수마다 다름

{% hint style="success" %}
## 🧪 종합 실습

이름·이메일·수준·식별자 필드가 있는 레코드를 검증합니다. 정상화된 레코드와 구조화된 오류 목록을 함께 반환하도록 작성합니다.
{% endhint %}

## 완료 기준

- [ ] 형식과 의미 검증을 구분할 수 있습니다.
- [ ] 필수값·허용값·범위를 검증할 수 있습니다.
- [ ] 여러 오류를 구조화해 보존할 수 있습니다.

---

다음 절: [05-6. 날짜와 시간](05-6-datetime.md)
