# 05-6. 날짜와 시간

이 교재의 날짜·시간 출력은 **한국 표준시(KST, UTC+09:00)**를 기본으로 한다. 실행하는 컴퓨터나 Colab의 시간대 설정에 관계없이 같은 결과를 얻도록 코드에서 시간대를 지정한다. 날짜와 시간은 `datetime` 객체로 변환해 계산하고, 출력에는 `+09:00` 또는 KST를 표시한다.

서로 다른 지역의 로그를 비교하는 예제에서는 UTC를 공통 기준으로 사용하고, 학습자가 읽는 결과는 KST로 변환한다. **원문·UTC 값·KST 표시값**을 구분하여 원래 오프셋을 지우거나 실제 시각을 바꾸지 않도록 한다. 모든 프로그램이 반드시 UTC로 저장해야 하는 것은 아니며, 여기서는 여러 출처의 로그를 합치는 연습을 위해 선택한 기준이다.

{% hint style="info" %}
### 🧭 학습 목표

- naive와 timezone-aware `datetime`을 구분한다.
- KST를 명시해 현재 시각과 고정된 예제 시각을 출력한다.
- ISO 8601과 지정 형식의 날짜 문자열을 허용 목록에 따라 파싱한다.
- 시간대가 있는 값을 UTC로 변환하고 일관된 문자열로 저장한다.
- 같은 시각을 UTC와 KST로 변환하고 날짜 변경 여부를 확인한다.
- `timedelta`와 `total_seconds()`로 경과 시간을 계산한다.
- 날짜 범위·시간 순서·분석 구간을 검증한다.
- 여러 시간대의 이벤트를 UTC 기준으로 정렬한다.
- DST·시계 오차·로케일·지원하지 않는 윤초 같은 경계 사례를 설명한다.
{% endhint %}

## 선행 지식과 실습 자료

- [05-5. 데이터 검증](05-5-validation.md)의 형식·의미 검증과 구조화된 오류를 이해해야 한다.
- JSON Lines 입력과 안전한 출력은 04장의 [JSON·JSON Lines](../04-file-io/04-6-json-jsonl.md), [안전한 출력](../04-file-io/04-8-safe-output.md)을 참고한다.
- 학습자용 TODO 노트북은 [`05-6-datetime.ipynb`](../notebooks/05-6-datetime.ipynb)에서 진행한다.
- 재현 가능한 입력은 [`timestamp-events.jsonl`](../fixtures/05-text-processing/timestamp-events.jsonl)을 사용한다.

## 0. 학습 전 확인

다음 두 값의 시간 순서를 문자열 비교만으로 정확히 판단할 수 있는지 생각한다.

```python
first = "2026-08-14T10:30:00+09:00"
second = "2026-08-14T02:00:00+00:00"
```

다음 질문에 답해 본다.

1. `datetime.now()`와 `datetime.now(KST)`의 차이는 무엇인가?
2. `2026-08-14T01:30:00Z`의 `Z`는 무엇을 의미하는가?
3. naive와 aware datetime을 직접 비교하면 어떻게 되는가?
4. `timedelta.seconds`와 `timedelta.total_seconds()`는 항상 같은가?
5. 시간대 없는 입력에 현재 컴퓨터의 로컬 시간대를 자동 적용해도 되는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. naive와 timezone-aware datetime

### 한국 시간으로 시작하기

이 절의 현대 한국 시간 예제에서는 고정 오프셋 `UTC+09:00`을 사용한다. 다음 셀을 먼저 실행하고 이후 코드 블록을 순서대로 실행한다. 운영체제의 시간대나 시스템 시계 설정은 변경하지 않는다.

```python
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9), name="KST")

kst_now = datetime.now(KST)
print("현재 한국 시각:", kst_now.isoformat(timespec="seconds"))

lesson_time = datetime(2026, 8, 14, 10, 30, tzinfo=KST)
print(lesson_time.isoformat())
print(lesson_time.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)"))
```

고정 예제의 출력은 다음과 같다. 현재 시각은 실행할 때마다 달라진다.

```text
2026-08-14T10:30:00+09:00
2026-08-14 10:30:00 KST (UTC+0900)
```

`+09:00`은 UTC보다 9시간 빠르다는 뜻이다. `%z`는 같은 오프셋을 `+0900`으로 출력한다. JSON 등 다른 프로그램과 교환할 때는 오프셋이 포함된 `isoformat()` 결과를 사용하면 시간대가 분명해진다.

### 시간대 정보의 유무 비교하기

`tzinfo`가 없거나 UTC 오프셋을 계산할 수 없는 값은 naive datetime이다. 유효한 시간대 또는 고정 오프셋 정보가 있는 값은 aware datetime이다.

```python
from datetime import datetime, timezone

naive_now = datetime.now()
kst_now = datetime.now(KST)

print(naive_now.tzinfo)  # None
print(kst_now.tzinfo)    # KST
print(kst_now.utcoffset())  # 9:00:00
```

naive 값은 어느 지역의 시각인지 객체만 보고 알 수 없다. aware 값은 UTC와의 차이를 계산할 수 있어 다른 시간대 값과 같은 기준으로 비교할 수 있다.

한국 시간은 `datetime.now(KST)`로 얻는다. UTC 자체가 필요할 때는 `datetime.now(timezone.utc)`를 사용한다. `datetime.utcnow()`은 시간대 정보가 없는 naive 값을 반환하므로 두 용도 모두에 권장하지 않는다.

## 2. ISO 8601 파싱과 `Z` 처리

ISO 8601 입력은 `datetime.fromisoformat()`으로 파싱할 수 있다. 과정의 최소 Python 버전과 입력 계약을 고려해 끝의 `Z`만 `+00:00`으로 바꾼다.

```python
from datetime import datetime, timezone


def parse_iso_timestamp(value):
    if not isinstance(value, str):
        raise TypeError("timestamp는 문자열이어야 한다")

    text = value.strip()
    if not text:
        raise ValueError("timestamp는 비어 있을 수 없다")

    normalized = (
        text[:-1] + "+00:00"
        if text.endswith("Z")
        else text
    )

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("ISO 8601 timestamp가 아니다") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("시간대 오프셋이 필요하다")

    return parsed.astimezone(timezone.utc)
```

```python
for text in ("2026-08-14T10:30:00+09:00", "2026-08-14T01:30:00Z"):
    parsed_utc = parse_iso_timestamp(text)
    print("KST:", parsed_utc.astimezone(KST).isoformat())
    print("UTC (비교용):", parsed_utc.isoformat())
```

두 입력 모두 KST로는 `2026-08-14T10:30:00+09:00`, UTC로는 `2026-08-14T01:30:00+00:00`이다. 이 함수는 로그 비교용 UTC 값을 반환하며, `astimezone(KST)`는 같은 순간을 한국 시간으로 표현한다.

`value.replace("Z", "+00:00")`처럼 문자열 전체를 치환하지 않는다. 입력 계약에서 `Z`는 timestamp 끝에만 허용한다.

## 3. 지정 형식 파싱

ISO 8601이 아닌 형식은 입력 계약에 포함된 형식 문자열로만 파싱한다.

```python
timestamp = "2026/08/14 10:30:00 +0900"
parsed = datetime.strptime(
    timestamp,
    "%Y/%m/%d %H:%M:%S %z",
)

print("KST:", parsed.astimezone(KST).isoformat())
print("UTC (비교용):", parsed.astimezone(timezone.utc).isoformat())
```

형식 문자열은 입력과 정확히 일치해야 하며 일치하지 않으면 `ValueError`가 발생한다.

허용 형식이 여러 개라면 목록을 제한하고 어떤 형식이 사용되었는지도 기록한다.

```python
ALLOWED_FORMATS = (
    "%Y/%m/%d %H:%M:%S %z",
    "%d/%b/%Y:%H:%M:%S %z",
)


def parse_known_format(value):
    for format_string in ALLOWED_FORMATS:
        try:
            return datetime.strptime(value, format_string)
        except ValueError:
            continue

    raise ValueError("허용된 timestamp 형식이 아니다")
```

`%b`처럼 월 이름을 읽는 형식은 실행 환경의 로케일에 영향을 받을 수 있다. 웹 로그 형식이 영문 월 이름을 사용한다면 실행 환경과 테스트 fixture에서 해당 계약을 검증한다.

## 4. 시간대 없는 입력 정책

시간대 없는 입력에 시간대를 붙이는 작업은 단순 변환이 아니라 **출처에 대한 가정**이다.

```python
from zoneinfo import ZoneInfo

source_timezone = ZoneInfo("Asia/Seoul")
naive_value = datetime.strptime(
    "2026-08-14 10:30:00",
    "%Y-%m-%d %H:%M:%S",
)
aware_value = naive_value.replace(tzinfo=source_timezone)
utc_value = aware_value.astimezone(timezone.utc)

print("한국 시간으로 해석:", aware_value.isoformat())
print("UTC (비교용):", utc_value.isoformat())
```

`replace(tzinfo=...)`는 시계 숫자를 바꾸지 않고 시간대 의미를 부여한다. 입력 시스템이 어느 시간대를 사용했는지 계약으로 확인한 경우에만 적용한다. 알 수 없는 naive 입력을 현재 컴퓨터의 로컬 시간으로 추측하지 않는다.

지역 시간대는 서머타임 규칙을 포함할 수 있다. 고정된 `timezone(timedelta(...))` 오프셋은 특정 순간의 차이만 표현하며 지역의 과거·미래 규칙을 대신하지 않는다.

`ZoneInfo("Asia/Seoul")`은 한국 지역의 과거 시간대 변경 규칙도 참조한다. 앞서 정의한 고정 오프셋 KST는 이 절의 현대 시각 실습에 사용하며, 과거 한국 시각을 다룰 때는 지역 시간대 규칙을 확인한다. `ZoneInfo` 데이터가 없는 환경에서는 `python -m pip install tzdata`로 시간대 데이터를 설치한다. 기본 KST 실습에는 이 추가 설치가 필요하지 않다.

## 5. KST 출력과 UTC 변환·직렬화

서로 다른 시간대의 값을 UTC로 변환하면 같은 기준으로 비교할 수 있다.

```python
original = "2026-08-14T10:30:00+09:00"
utc_value = parse_iso_timestamp(original)

event = {
    "timestamp_raw": original,
    "timestamp_utc": utc_value,
    "timestamp_kst": utc_value.astimezone(KST).isoformat(),
}

print("한국 시각:", event["timestamp_kst"])
```

JSON에는 `datetime` 객체를 직접 저장할 수 없으므로 명시적인 문자열로 변환한다.

```python
def format_utc(value):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("aware datetime이 필요하다")

    text = (
        value.astimezone(timezone.utc)
        .isoformat(timespec="seconds")
    )
    return text.removesuffix("+00:00") + "Z"


print("KST:", utc_value.astimezone(KST).isoformat())
print("UTC 저장값:", format_utc(utc_value))
```

여기서 `removesuffix()`는 직접 만든 UTC 출력 끝의 `+00:00`을 제거한 뒤 `Z`를 붙이기 위해 사용한다. KST 값의 `+09:00`을 `Z`로 바꾸면 다른 시각이 되므로 이렇게 처리하면 안 된다.

### 시간대 변환으로 날짜가 바뀌는 경우

```python
late_utc = parse_iso_timestamp("2026-08-14T18:30:00Z")
next_day_kst = late_utc.astimezone(KST)

print(next_day_kst.isoformat())  # 2026-08-15T03:30:00+09:00
assert next_day_kst == late_utc  # 표시는 달라도 같은 순간이다.
assert next_day_kst.timestamp() == late_utc.timestamp()
```

9시간을 더한 뒤 시간대 이름만 붙이지 않는다. `astimezone()`으로 변환해야 같은 순간을 유지하면서 날짜와 시각이 함께 바뀐다.

## 6. 시간 차이와 순서 검증

aware datetime끼리 빼면 `timedelta`가 반환된다.

```python
start = parse_iso_timestamp(
    "2026-08-14T10:00:00+09:00"
)
end = parse_iso_timestamp(
    "2026-08-14T10:45:30+09:00"
)

if end < start:
    raise ValueError("종료 시각이 시작 시각보다 빠르다")

duration = end - start

print(duration)
print(duration.total_seconds())
```

`timedelta.seconds`는 일(day)을 제외한 하루 안의 초 부분만 반환한다. 음수나 하루 이상의 간격을 포함한 전체 초가 필요하면 `total_seconds()`를 사용한다.

필드 관계도 검증한다.

```python
def validate_interval(start, end, *, max_seconds=86_400):
    if end < start:
        raise ValueError("종료 시각이 시작 시각보다 빠르다")

    elapsed = (end - start).total_seconds()
    if elapsed > max_seconds:
        raise ValueError("허용된 분석 구간을 초과했다")

    return elapsed
```

## 7. 허용 범위와 미래 시각 검증

형식이 올바른 timestamp라도 과정의 데이터 범위를 벗어날 수 있다.

```python
def validate_timestamp_range(value, *, earliest, latest):
    if value < earliest:
        raise ValueError("허용 시작 시각보다 이르다")
    if value > latest:
        raise ValueError("허용 종료 시각보다 늦다")

    return value
```

검증 기준으로 “현재 시각”을 사용할 때는 함수 안에서 매번 시간을 읽기보다 호출자가 기준 시각을 전달하면 테스트가 재현 가능하다.

```python
reference_now = datetime(
    2026, 8, 15,
    tzinfo=KST,
)
```

미래 시각을 모두 오류로 단정하기보다 허용 가능한 시계 오차를 계약에 포함한다. 분산 시스템에서는 장비 간 시계가 몇 초 차이 날 수 있다.

## 8. 시간순 정렬과 시간대별 묶기

원문 문자열 형식과 오프셋이 다르면 문자열 순서가 실제 시간 순서와 다를 수 있다. UTC datetime을 정렬 키로 사용한다.

```python
records = [
    {"time": "2026-08-14T10:30:00+09:00", "event": "A"},
    {"time": "2026-08-14T02:00:00Z", "event": "B"},
]

for record in records:
    record["time_utc"] = parse_iso_timestamp(record["time"])

ordered = sorted(
    records,
    key=lambda record: record["time_utc"],
)

print([record["event"] for record in ordered])
```

한국 시간 기준의 시간별·일별 집계는 KST로 변환한 뒤 구간을 나눈다. 예를 들어 UTC 8월 14일 18:30은 한국에서는 8월 15일 03:30이므로 한국 날짜별 보고서에서는 8월 15일에 포함해야 한다.

```python
hour_bucket_kst = utc_value.astimezone(KST).replace(
    minute=0,
    second=0,
    microsecond=0,
)
print("한국 시간별 집계 구간:", hour_bucket_kst.isoformat())
day_bucket_kst = next_day_kst.date()
assert day_bucket_kst.isoformat() == "2026-08-15"
```

국제 로그를 UTC 구간으로 집계해야 하는 경우에는 UTC에서 구간을 나누고 결과에 UTC 기준이라고 명시한다. 한국 날짜별 집계와 UTC 날짜별 집계는 날짜 경계가 다르다.

## 오류·경계 사례

### naive와 aware 값을 직접 비교함

```python
naive = datetime(2026, 8, 14, 10, 0)
aware = datetime(2026, 8, 14, 10, 0, tzinfo=KST)

# naive < aware  # TypeError
```

양쪽의 시간대 의미를 확인한 뒤 모두 aware 값으로 만든다. naive 값에 무조건 UTC를 붙여 오류를 숨기지 않는다.

### DST 전환 시각을 하나로 단정함

일부 지역에서는 서머타임 종료 때 같은 현지 시각이 두 번 나타나고, 시작 때 특정 현지 시각이 존재하지 않을 수 있다. `zoneinfo`의 지역 규칙과 `fold`를 이해하고, 가능하면 입력에 오프셋을 포함한다.

### 월 이름과 로케일을 무시함

`14/Aug/2026` 같은 입력의 `%b`는 로케일 영향을 받을 수 있다. 실행 환경이 달라져도 같은 결과가 나오는지 fixture로 검증하거나 숫자 월 형식을 우선한다.

### 윤초를 일반 datetime이 처리한다고 가정함

Python `datetime`은 `23:59:60` 같은 윤초 입력을 일반적으로 허용하지 않는다. 해당 데이터가 필요하면 원본을 보존하고 전용 시간 체계·라이브러리 정책을 검토한다.

### 시스템 시각을 절대적인 사실로 사용함

로그 발생 장비의 시계 동기화 상태, 수집 지연, 재전송 때문에 기록 시각과 수집 시각이 다를 수 있다. 가능한 경우 두 시각을 별도 필드로 유지한다.

### 원문 오프셋을 지워 원인 분석이 어려워짐

UTC 값만 남기면 정렬은 쉬워지지만 원래 시스템이 어떤 오프셋을 기록했는지 확인하기 어렵다. 조사 가능성이 필요하면 원문 또는 원래 오프셋을 함께 보존한다.

## 실습

학습자용 TODO 노트북 [`05-6-datetime.ipynb`](../notebooks/05-6-datetime.ipynb)에서 [`timestamp-events.jsonl`](../fixtures/05-text-processing/timestamp-events.jsonl)을 처리한다.

1. ISO 8601, `Z`, 지정 형식의 timestamp를 허용 목록에 따라 파싱한다.
2. naive 입력은 자동 추측하지 않고 별도 오류로 분류한다.
3. 정상값을 UTC aware datetime으로 변환한다.
4. 원문과 UTC 값을 보존하고, KST 표시값을 `+09:00`이 포함된 ISO 8601 문자열로 만든다.
5. 허용 범위 밖의 과거·미래 값과 잘못된 달력 날짜를 분리한다.
6. 이벤트를 UTC 시간순으로 정렬하고, KST로 변환해 한국 시간별·날짜별 건수를 집계한다.
7. 인접 이벤트의 시간 차이를 `total_seconds()`로 계산한다.
8. 정상·오류 건수와 정렬, UTC↔KST 변환 후 같은 순간인지, 한국 날짜가 다음 날로 바뀌는지를 `assert`로 검증한다.

{% hint style="warning" %}
실습의 기준 시각은 fixture에 고정한다. 실제 실행 시각을 기준으로 검사하면 같은 노트북도 실행 날짜에 따라 결과가 달라질 수 있다.
{% endhint %}

## 자기점검

1. naive와 aware datetime을 어떻게 판별하는가?
2. 서로 다른 오프셋의 값을 비교하기 전에 무엇을 해야 하는가?
3. 시간대 없는 입력에 시간대를 붙이는 일이 왜 단순 형식 변환이 아닌가?
4. `timedelta.seconds` 대신 `total_seconds()`가 필요한 사례는 무엇인가?
5. UTC 값과 원문 timestamp를 함께 보존할 이유는 무엇인가?
6. DST와 시스템 시계 오차가 이벤트 순서 분석에 어떤 영향을 주는가?

## 응용 인사이트

- **로그 상관분석**: 여러 서버·클라우드·엔드포인트의 이벤트를 UTC로 맞추면 하나의 타임라인에서 비교할 수 있다.
- **탐지 구간**: “5분 동안 실패 10회” 같은 규칙은 파싱된 aware datetime과 명시적인 구간 경계가 있어야 재현할 수 있다.
- **감사 가능성**: 원문·UTC 값·사용한 파서 형식을 함께 남기면 변환 오류와 입력 형식 변경을 나중에 설명할 수 있다.
- **분산 시스템**: 기록 시각, 수집 시각, 처리 시각을 분리하면 네트워크 지연과 장비 시계 오차를 구분하는 데 도움이 된다.
- **한국 시간 보고서**: 비교용 UTC 값은 유지하고 결과는 KST로 출력한다. 한국 날짜별 건수는 KST로 변환한 뒤 집계한다.

## 완료 기준

- [ ] naive와 aware datetime을 구분할 수 있다.
- [ ] 실행 컴퓨터의 시간대와 관계없이 KST로 출력하고 `+09:00`의 의미를 설명할 수 있다.
- [ ] ISO 8601과 허용된 지정 형식을 파싱할 수 있다.
- [ ] 시간대가 있는 값을 UTC로 변환하고 일관되게 직렬화할 수 있다.
- [ ] 날짜 범위·시간 순서·분석 구간을 검증할 수 있다.
- [ ] `total_seconds()`로 경과 시간을 계산하고 UTC 기준으로 정렬할 수 있다.
- [ ] DST·로케일·시계 오차와 원문 보존의 필요성을 설명할 수 있다.
- [ ] UTC↔KST 변환이 같은 순간을 유지하는지, 한국 날짜별 집계가 올바른지 검증할 수 있다.

## 공식 참고 자료

- [Python datetime: 시간대가 있는 객체와 시간대 변환](https://docs.python.org/3/library/datetime.html)
- [Python zoneinfo: 지역 시간대와 tzdata 설치](https://docs.python.org/3/library/zoneinfo.html)

---

다음 절: [05-7. NumPy 배열과 대용량 수치 처리](05-7-numpy-array.md)
