# 05-5. 데이터 검증

파싱은 입력 문자열을 필드로 나누는 작업이고, 검증은 각 값이 프로그램의 입력 계약을 만족하는지 확인하는 작업이다. 정규표현식과 JSON 파싱에 성공했더라도 필수값·자료형·범위·필드 간 관계가 잘못될 수 있다.

검증의 목표는 “오류가 없다”는 막연한 결론이 아니다. **어떤 규칙을 통과했는지, 실패한 레코드를 어떻게 격리할지, 오류 보고서에 무엇을 남기지 않을지**까지 일관된 계약으로 만드는 것이 중요하다.

{% hint style="info" %}
### 🧭 학습 목표

- 값 존재 여부·자료형·형식·범위·필드 관계 순서로 검증한다.
- 정규표현식의 형식 검증과 전용 파서의 의미 검증을 구분한다.
- IPv4와 IPv6를 `ipaddress`로 검증하고 정규화한다.
- URL 요청 대상에서 경로만 분리하고 위험하거나 모호한 표현을 거부한다.
- 정상화된 레코드와 구조화된 오류 목록을 함께 반환한다.
- 오류 보고서와 저장 결과에서 계정·IP·쿼리 같은 민감정보를 최소화한다.
- 단일 레코드 실패와 전체 입력 실패의 처리 경계를 설계한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | 필수값·자료형·허용값·범위 검증, 형식과 의미의 분리, 구조화된 오류 |
| 권장 | IP 전용 파서, 경로 정규화 정책, 오류 행 격리, 민감정보 마스킹 |
| 심화 | 필드 간 조건부 규칙, 재식별 위험, 대량 입력의 실패율 임계값과 중단 정책 |

## 선행 지식과 실습 자료

- [05-1. 문자열 정규화](05-1-normalization.md)의 원문·정규화 값 분리를 이해해야 한다.
- [05-4. 그룹과 캡처](05-4-groups-capture.md)의 추출 결과를 입력으로 사용한다.
- 파일 저장은 [04-8. 안전한 출력](../04-file-io/04-8-safe-output.md)의 임시 파일·검증·교체 원칙을 따른다.
- 학습자용 TODO 노트북은 [`05-5-validation.ipynb`](../notebooks/05-5-validation.ipynb)에서 진행한다.
- 재현 가능한 입력은 [`validation-records.jsonl`](../fixtures/05-text-processing/validation-records.jsonl)을 사용한다.

## 0. 학습 전 확인

다음 레코드가 JSON 파싱에는 성공해도 유효한 이벤트가 아닌 이유를 찾는다.

```python
record = {
    "account": "  ",
    "ip": "999.10.20.30",
    "result": "MAYBE",
    "risk_score": True,
    "target": "/admin/%2e%2e/settings?token=secret",
}
```

다음 질문에 답해 본다.

1. 키 누락과 빈 문자열은 같은 오류인가?
2. Python에서 `bool`은 `int` 검사에 통과할 수 있는가?
3. IP 주소를 정규표현식 하나로 검증하면 어떤 의미 검사가 빠질 수 있는가?
4. `/a/../admin`을 단순 문자열 치환으로 정리해도 되는가?
5. 오류 레코드에 `target` 전체를 남기면 어떤 정보가 노출될 수 있는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. 입력 계약과 검증 순서

이 절의 인증 이벤트는 다음 계약을 사용한다.

| 필드 | 규칙 | 정규화 결과 |
| --- | --- | --- |
| `account` | 3~32자의 영문·숫자·`_`·`-` | 양끝 공백 제거 |
| `ip` | 유효한 IPv4 또는 IPv6 | `ipaddress`의 표준 문자열 |
| `result` | `SUCCESS`, `FAILURE`, `LOCKED` 중 하나 | 대문자 |
| `risk_score` | `bool`이 아닌 0~100 정수 | 정수 |
| `target` | `/`로 시작하는 origin-form 경로 | 쿼리를 제거한 비교용 경로 |

검증은 보통 다음 순서로 수행한다.

1. 레코드와 값의 존재 여부
2. 자료형
3. 문자열 길이와 형식
4. 허용값·숫자 범위·전용 파서 의미
5. 필드 간 관계
6. 정상화 결과 생성

앞 단계가 실패하면 뒤 단계가 의미 없거나 새로운 예외를 만들 수 있다. 예를 들어 문자열 여부를 확인하기 전에 `strip()`을 호출하지 않는다.

## 2. 필수 문자열 검증

필수값 검사와 문자열 정리를 하나의 함수 계약으로 만든다.

```python
def require_text(record, key, *, max_length=256):
    if key not in record:
        raise ValueError(f"필수 필드 누락: {key}")

    value = record[key]

    if not isinstance(value, str):
        raise TypeError(f"{key}는 문자열이어야 한다")

    cleaned = value.strip()

    if not cleaned:
        raise ValueError(f"{key}는 비어 있을 수 없다")
    if len(cleaned) > max_length:
        raise ValueError(f"{key}가 허용 길이를 초과했다")

    return cleaned
```

누락, `None`, 빈 문자열, 공백 문자열은 원인이 다르다. 사용자 메시지는 같게 보여 주더라도 내부 오류 코드는 구분하면 데이터 품질 원인을 집계하기 쉽다.

## 3. 허용값·형식·범위 검증

허용 목록이 명확한 값은 정규화한 뒤 집합에 포함되는지 검사한다.

```python
ALLOWED_RESULTS = {"SUCCESS", "FAILURE", "LOCKED"}


def validate_result(value):
    if not isinstance(value, str):
        raise TypeError("result는 문자열이어야 한다")

    normalized = value.strip().upper()

    if normalized not in ALLOWED_RESULTS:
        raise ValueError("허용되지 않은 인증 결과다")

    return normalized
```

계정 이름은 정규표현식으로 형태를 확인하고 길이도 별도로 제한한다.

```python
import re

ACCOUNT_PATTERN = re.compile(r"[A-Za-z0-9_-]{3,32}")


def validate_account(value):
    if not isinstance(value, str):
        raise TypeError("account는 문자열이어야 한다")

    cleaned = value.strip()

    if ACCOUNT_PATTERN.fullmatch(cleaned) is None:
        raise ValueError("계정 형식이 올바르지 않다")

    return cleaned
```

숫자 범위에서는 `bool`을 명시적으로 제외한다. Python에서 `bool`은 `int`의 하위 유형이기 때문이다.

```python
def validate_risk_score(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("risk_score는 정수여야 한다")
    if not 0 <= value <= 100:
        raise ValueError("risk_score는 0부터 100 사이여야 한다")

    return value
```

## 4. IP 주소는 전용 파서로 검증하기

IP 주소는 모양뿐 아니라 각 숫자 범위, IPv6 축약, 표준 표현까지 확인해야 한다. 표준 라이브러리 `ipaddress`를 사용한다.

```python
from ipaddress import ip_address


def validate_ip(value):
    if not isinstance(value, str):
        raise TypeError("ip는 문자열이어야 한다")

    cleaned = value.strip()
    if "%" in cleaned:
        raise ValueError("영역 식별자가 있는 IP는 허용하지 않는다")

    try:
        parsed = ip_address(cleaned)
    except ValueError as exc:
        raise ValueError("유효하지 않은 IP 주소다") from exc

    return str(parsed)
```

```python
print(validate_ip("203.0.113.10"))
print(validate_ip("2001:0db8:0000::10"))  # 2001:db8::10
```

IPv4와 IPv6를 모두 허용할지, IPv4-mapped IPv6와 영역 식별자가 있는 주소를 어떻게 처리할지는 입력 계약에서 정한다. 정규화된 문자열은 같은 주소의 표현 차이를 줄이지만 원문이 필요하면 별도 필드로 보존한다.

## 5. 요청 경로 정규화와 모호한 입력 거부

로그의 요청 대상에는 쿼리 문자열과 민감값이 포함될 수 있다. 분석용 경로를 만들 때는 원본을 덮어쓰지 않고 `urlsplit()`으로 경로만 분리한다.

```python
import re
from urllib.parse import unquote, urlsplit

BAD_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")
ENCODED_AGAIN = re.compile(r"%[0-9A-Fa-f]{2}")


def normalize_request_path(target):
    if not isinstance(target, str):
        raise TypeError("target은 문자열이어야 한다")
    if not target or len(target) > 2048:
        raise ValueError("target 길이가 허용 범위를 벗어났다")
    if any(character in target for character in ("\x00", "\r", "\n", "\\")):
        raise ValueError("target에 허용되지 않은 문자가 있다")

    parts = urlsplit(target)
    if (
        parts.scheme
        or parts.netloc
        or parts.fragment
        or not parts.path.startswith("/")
    ):
        raise ValueError("상대 서버 경로가 필요하다")
    if BAD_PERCENT.search(parts.path):
        raise ValueError("잘못된 퍼센트 인코딩이다")

    decoded = unquote(parts.path, encoding="utf-8", errors="strict")
    if ENCODED_AGAIN.search(decoded):
        raise ValueError("중첩 인코딩은 허용하지 않는다")

    segments = []
    for segment in decoded.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            raise ValueError("상위 경로 이동은 허용하지 않는다")
        segments.append(segment)

    return "/" + "/".join(segments)
```

```python
print(normalize_request_path("/login?next=/admin"))  # /login
print(normalize_request_path("/api///items"))        # /api/items
```

이 함수는 **이 교안의 분석용 비교 정책**이다. 웹 서버·프록시·프레임워크마다 디코딩 횟수와 슬래시 처리 방식이 다를 수 있으므로 보안 판정에 사용할 때는 실제 서버의 경로 해석 규칙과 맞춰야 한다. 원본 요청 대상은 승인된 위치에 별도로 보존하고 일반 보고서에는 쿼리를 복사하지 않는다.

## 6. 여러 오류를 구조화해 수집하기

오류는 사람이 읽는 메시지만 저장하기보다 행·필드·코드·메시지를 분리한다.

```python
def issue(field, code, message):
    return {
        "field": field,
        "code": code,
        "message": message,
    }
```

정상화 결과와 오류를 함께 반환하면 호출자가 한 건 실패와 전체 실패를 구분할 수 있다.

```python
def validate_record(record):
    if not isinstance(record, dict):
        return {}, [issue("record", "INVALID_TYPE", "객체가 필요하다")]

    cleaned = {}
    errors = []

    validators = {
        "account": lambda value: validate_account(value),
        "ip": validate_ip,
        "result": validate_result,
        "risk_score": validate_risk_score,
        "target": normalize_request_path,
    }

    for field, validator in validators.items():
        if field not in record:
            errors.append(issue(field, "MISSING", "필수 필드가 없다"))
            continue

        try:
            cleaned[field] = validator(record[field])
        except (TypeError, ValueError):
            errors.append(issue(field, "INVALID", "필드 규칙을 만족하지 않는다"))

    return cleaned, errors
```

오류 보고서에 실패한 값을 그대로 넣지 않았다. 디버깅에 원문이 꼭 필요하면 제한된 격리 저장소에 행 식별자와 함께 보관하고 일반 결과에는 복사하지 않는다.

## 7. 민감정보를 최소화한 결과 만들기

정상 레코드도 공유 범위에 따라 계정과 IP를 그대로 저장하지 않는다.

```python
from ipaddress import ip_address, ip_network


def mask_account(value):
    if len(value) <= 2:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 2)


def summarize_ip(value):
    parsed = ip_address(value)
    prefix = 24 if parsed.version == 4 else 64
    return str(ip_network(f"{parsed}/{prefix}", strict=False))


def make_shareable_record(record):
    return {
        "account": mask_account(record["account"]),
        "ip_network": summarize_ip(record["ip"]),
        "result": record["result"],
        "risk_score": record["risk_score"],
        "path": record["target"],
    }
```

마스킹과 네트워크 단위 집계는 노출을 줄이지만 완전한 익명화를 보장하지 않는다. 적은 사용자 집단, 희귀한 시간대, 다른 데이터와 결합하면 다시 식별될 수 있으므로 최소 필드·접근 권한·보존 기간을 함께 정한다.

## 오류·경계 사례

| 사례 | 잘못된 처리 | 권장 처리 |
| --- | --- | --- |
| 필드 누락과 빈 문자열 | 둘 다 `False`로만 처리 | 서로 다른 오류 코드로 기록한다. |
| `risk_score=True` | `isinstance(value, int)`만 검사 | `bool`을 먼저 제외한다. |
| `999.1.1.1` | 점과 숫자 모양만 정규식 검사 | `ipaddress.ip_address()`로 의미를 검증한다. |
| `/a/%2e%2e/admin` | 디코딩 없이 정상 경로로 집계 | 디코딩 정책을 고정하고 상위 이동을 거부한다. |
| `/login?token=...` | 오류·CSV에 전체 target 저장 | 경로만 저장하고 쿼리는 승인된 원본에 제한한다. |
| 잘못된 행 1개 | 전체 파일을 무조건 중단 | 레코드 오류와 파일 구조 오류의 경계를 정한다. |

검증이 실패한 값을 자동으로 “수정”해 정상값으로 만들지 않는다. 예를 들어 잘못된 IP의 일부 숫자를 잘라내거나 알 수 없는 결과를 `FAILURE`로 바꾸면 원래 오류가 사라지고 집계가 왜곡된다.

허용하지 않은 필드를 조용히 버릴지도 정책으로 정한다. 보안·감사 데이터에서는 예상하지 못한 필드가 입력 형식 변경의 신호일 수 있으므로 오류 또는 경고로 남기는 편이 안전하다.

## 실습

학습자용 TODO 노트북 [`05-5-validation.ipynb`](../notebooks/05-5-validation.ipynb)에서 [`validation-records.jsonl`](../fixtures/05-text-processing/validation-records.jsonl)을 검증한다.

1. JSON Lines를 한 줄씩 읽고 JSON 문법 오류와 레코드 검증 오류를 구분한다.
2. 계정·IP·인증 결과·위험 점수·요청 경로를 순서대로 검증한다.
3. IPv4와 IPv6를 표준 문자열로 정규화한다.
4. 경로에서는 쿼리를 제외하고 모호한 퍼센트 인코딩과 상위 이동을 거부한다.
5. 정상 레코드와 구조화된 오류를 별도 목록으로 보존한다.
6. 공유용 결과에서는 계정과 IP를 마스킹·집계한다.
7. 입력과 다른 출력 경로에 저장하고 다시 읽어 건수와 필드 구성을 검증한다.
8. `전체 행 = 정상 행 + JSON 오류 행 + 검증 오류 행`인지 확인한다.

{% hint style="warning" %}
학습 fixture에는 실제 계정·IP·토큰이 없다. 운영 데이터를 사용할 때는 출력 셀, traceback, 오류 샘플, 저장 파일까지 민감정보 노출 범위에 포함해 검토한다.
{% endhint %}

## 자기점검

1. 파싱 성공과 검증 성공의 차이를 설명할 수 있는가?
2. 필수값·자료형·형식·범위·필드 관계의 검증 순서를 설명할 수 있는가?
3. `bool`을 정수 범위 검증에서 제외해야 하는 이유는 무엇인가?
4. IP 정규표현식보다 `ipaddress`가 적합한 이유는 무엇인가?
5. 경로 정규화 규칙을 실제 서버와 맞춰야 하는 이유는 무엇인가?
6. 마스킹된 데이터도 재식별될 수 있는 조건을 하나 설명할 수 있는가?

## 응용 인사이트

- **입력 경계**: API, 로그 수집기, CSV 변환기처럼 외부 데이터가 내부 모델로 들어오는 지점에 검증을 집중하면 이후 코드의 가정을 단순화할 수 있다.
- **오류 집계**: 구조화된 오류 코드는 배포 후 입력 형식 변경이나 특정 공급자의 품질 문제를 수치로 찾는 근거가 된다.
- **보안 탐지**: 정규화되지 않은 IP·경로를 그대로 집계하면 같은 대상을 여러 값으로 세거나 우회 표현을 놓칠 수 있다.
- **데이터 최소화**: 탐지에 필요한 통계와 원본 조사 자료를 분리하면 일반 보고서의 민감정보 노출을 줄일 수 있다.
- **실패 정책**: 레코드 단위 오류는 격리하고 계속 처리할 수 있지만 헤더·인코딩·전체 스키마 오류는 분석 자체를 중단해야 할 수 있다.

## 완료 기준

- [ ] 파싱·정규화·검증을 서로 다른 단계로 설명할 수 있다.
- [ ] 필수값·자료형·허용값·범위를 순서대로 검증할 수 있다.
- [ ] IPv4와 IPv6를 전용 파서로 검증하고 표준화할 수 있다.
- [ ] 분석용 경로 정규화 규칙과 한계를 설명할 수 있다.
- [ ] 정상화된 레코드와 구조화된 오류를 함께 반환할 수 있다.
- [ ] 오류·공유 결과에서 민감정보를 최소화하고 안전한 출력 경로를 사용할 수 있다.

---

다음 절: [05-6. 날짜와 시간](05-6-datetime.md)
