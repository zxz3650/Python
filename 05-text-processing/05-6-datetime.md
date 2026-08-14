# 05-6. 날짜와 시간

날짜와 시간은 문자열 상태로 비교하기보다 `datetime` 객체로 변환해야 계산과 정렬을 안전하게 수행할 수 있습니다. 특히 서로 다른 시간대를 같은 기준으로 맞추는 것이 중요합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 날짜 문자열을 datetime으로 변환합니다.
- ISO 8601 형식을 읽고 생성합니다.
- naive와 timezone-aware datetime을 구분합니다.
- UTC 변환과 시간 차이를 계산합니다.
{% endhint %}

## 선행 지식

문자열 파싱, 예외 처리, 데이터 검증을 이해해야 합니다.

## 1. 현재 시각

```python
from datetime import datetime, timezone

local_like = datetime.now()
utc_now = datetime.now(timezone.utc)

print(local_like)
print(utc_now)
```

timezone 정보가 없는 datetime을 naive, 포함된 datetime을 aware라고 합니다.

## 2. ISO 8601 읽기

```python
timestamp = "2026-08-14T10:30:00+09:00"
parsed = datetime.fromisoformat(timestamp)

print(parsed)
print(parsed.tzinfo)
```

UTC를 `Z`로 표기한 값은 다음처럼 처리할 수 있습니다.

```python
timestamp = "2026-08-14T01:30:00Z"
parsed = datetime.fromisoformat(
    timestamp.replace("Z", "+00:00")
)
```

## 3. 지정 형식 읽기

```python
timestamp = "2026/08/14 10:30:00"
parsed = datetime.strptime(
    timestamp,
    "%Y/%m/%d %H:%M:%S",
)

print(parsed)
```

형식 문자열은 입력과 정확히 일치해야 하며, 일치하지 않으면 `ValueError`가 발생합니다.

## 4. 문자열로 출력

```python
print(parsed.strftime("%Y-%m-%d %H:%M:%S"))
print(parsed.isoformat())
```

가능하면 저장과 교환에는 ISO 8601 형식을 사용하고 표시할 때만 사용자 형식으로 바꿉니다.

## 5. UTC 변환

```python
timestamp = "2026-08-14T10:30:00+09:00"
parsed = datetime.fromisoformat(timestamp)
utc_value = parsed.astimezone(timezone.utc)

print(utc_value.isoformat())
```

여러 시간대의 데이터를 비교할 때는 UTC 같은 공통 기준으로 변환합니다. 원래 문자열과 원래 시간대도 필요하면 함께 보존합니다.

## 6. 시간 차이

```python
start = datetime.fromisoformat(
    "2026-08-14T10:00:00+09:00"
)
end = datetime.fromisoformat(
    "2026-08-14T10:45:30+09:00"
)

duration = end - start

print(duration)
print(duration.total_seconds())
```

datetime의 차이는 `timedelta` 객체입니다.

## 7. 날짜 범위 검증

```python
def parse_timestamp(value):
    try:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise ValueError(
            f"잘못된 timestamp: {value!r}"
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError("시간대 정보가 필요합니다")

    return parsed.astimezone(timezone.utc)
```

형식뿐 아니라 시간대 정보의 존재 여부도 검증합니다.

## 8. 정렬

```python
records = [
    {"time": "2026-08-14T02:00:00Z"},
    {"time": "2026-08-14T01:30:00Z"},
]

ordered = sorted(
    records,
    key=lambda record: parse_timestamp(record["time"]),
)

print(ordered)
```

문자열 표현이 서로 다를 수 있으므로 datetime으로 변환한 값을 기준으로 정렬합니다.

## 흔한 실수

- naive와 aware datetime을 직접 비교함
- 로컬 시간을 UTC로 가정함
- 시간대 오프셋을 제거하고 저장함
- 날짜 형식 검증을 정규표현식만으로 끝냄
- `timedelta.seconds`를 전체 초로 오해함

{% hint style="success" %}
## 🧪 05장 종합 실습

서로 다른 형식의 이벤트 텍스트를 처리합니다.

1. 원문을 보존하고 문자열을 정규화합니다.
2. 문자열 메서드 또는 정규표현식으로 필드를 추출합니다.
3. 필수값·허용값·형식을 검증합니다.
4. timestamp를 UTC datetime으로 변환합니다.
5. 시간순으로 정렬해 JSON으로 저장합니다.
6. 오류의 행 번호·원문·필드·원인을 기록합니다.
{% endhint %}

## 완료 기준

- [ ] 문자열을 datetime으로 변환할 수 있습니다.
- [ ] naive와 aware datetime을 구분할 수 있습니다.
- [ ] 여러 시간대의 값을 UTC로 통일할 수 있습니다.
- [ ] 시간 차이와 시간순 정렬을 수행할 수 있습니다.

---

다음 절: [05-7. NumPy 배열과 대용량 수치 처리](05-7-numpy-array.md)
