# 03-9. 실무 보강 문법

앞 절에서 기초를 익힌 뒤 코드의 표현력·성능·안전성을 높이는 문법을 다룬다. 처음부터 모두 암기할 필요는 없으며 실제 문제에서 필요할 때 다시 찾아본다.

{% hint style="info" %}
### 🧭 학습 목표

- 정렬과 컴프리헨션을 읽고 작성한다.
- generator로 대용량 데이터를 지연 처리한다.
- 가변 인자와 lambda의 사용 범위를 이해한다.
- 예외 원인을 보존하고 외부 입력을 안전하게 다룬다.
{% endhint %}

## 1. 정렬과 key 함수

```python
records = [
    {"ip": "10.0.0.5", "count": 2},
    {"ip": "198.51.100.9", "count": 7},
]

sorted_records = sorted(
    records,
    key=lambda record: record["count"],
    reverse=True,
)

for record in sorted_records:
    print(record)
```

`sorted()`는 새 리스트를 반환한다. `list.sort()`는 원본 리스트를 직접 변경한다. `lambda`는 한 표현식으로 된 짧은 함수를 인자로 전달할 때만 제한적으로 사용한다.

## 2. 딕셔너리·세트 컴프리헨션

```python
events = [
    {"action": "DENY", "ip": "10.0.0.5"},
    {"action": "ALLOW", "ip": "198.51.100.9"},
]

denied_by_ip = {
    event["ip"]: event
    for event in events
    if event["action"] == "DENY"
}

unique_actions = {event["action"] for event in events}
```

집계는 `list.count()`를 반복하기보다 한 번의 반복으로 누적한다.

```python
counts = {}

for event in events:
    ip = event["ip"]
    counts[ip] = counts.get(ip, 0) + 1
```

## 3. generator와 yield

리스트 컴프리헨션은 결과 전체를 메모리에 만든다. generator는 필요한 값을 하나씩 생성한다.

```python
def non_empty_lines(lines):
    for line in lines:
        clean = line.strip()
        if clean:
            yield clean

lines = ["", "first", "second"]
for line in non_empty_lines(lines):
    print(line)
```

대용량 로그처럼 전체를 동시에 메모리에 올릴 필요가 없을 때 유용하다. generator는 한 번 소비하면 다시 사용하려면 새로 만들어야 한다.

## 4. 가변 인자

```python
def make_event(action, *tags, **metadata):
    return {
        "action": action,
        "tags": list(tags),
        "metadata": metadata,
    }

event = make_event(
    "DENY",
    "auth",
    "critical",
    ip="198.51.100.9",
    port=443,
)
```

- `*args`: 위치 인자를 튜플로 받음
- `**kwargs`: 키워드 인자를 딕셔너리로 받음

고정된 매개변수로 충분하다면 가변 인자를 남용하지 않는다.

## 5. 날짜와 시간

```python
from datetime import datetime, timezone

timestamp = "2026-08-10T10:00:00+00:00"
parsed = datetime.fromisoformat(timestamp)

now = datetime.now(timezone.utc)
print(parsed, now)
```

시간 데이터는 문자열 상태로만 비교하지 않고 timezone 정보를 포함한 `datetime`으로 변환한다.

## 6. 명령줄 인자

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--output", default="result.json")
parser.add_argument("--threshold", type=int, default=3)
args = parser.parse_args()
```

반복 실행되는 실무 도구는 코드 안의 경로·기준값을 직접 수정하지 않고 인자로 받는다.

## 7. 예외 원인 보존

```python
try:
    port = int("not-a-number")
except ValueError as exc:
    raise ValueError("포트 형식이 올바르지 않습니다") from exc
```

구체적인 예외를 처리하고 원래 오류를 유지한다.

## 8. 보안 자동화에서 피할 것

```python
# 외부 입력을 Python 코드로 실행하지 않는다.
# eval(user_input)
# exec(user_input)
```

- `eval()`, `exec()`로 외부 입력을 실행하지 않는다.
- `subprocess`에는 문자열 명령보다 인자 리스트를 전달한다.
- 비밀번호·토큰·API 키를 소스 코드에 넣지 않는다.
- 입력 파일 경로가 허용된 기준 디렉터리 안인지 검증한다.
- `assert`를 권한 판정과 사용자 입력 검증에 사용하지 않는다.
- 로그 출력 전에 토큰과 개인정보를 마스킹한다.

{% hint style="success" %}
## 🧪 실습

1. DENY 횟수 기준으로 레코드를 내림차순 정렬한다.
2. 대용량 로그를 generator로 한 줄씩 처리한다.
3. 03-8 프로젝트에 명령줄 인자를 추가한다.
4. timestamp를 timezone-aware datetime으로 변환한다.
5. 외부 입력을 `eval()` 없이 안전하게 해석한다.
{% endhint %}

## 핵심 정리

- 03-9의 문법은 기초 문법을 대체하지 않고 실무 코드를 확장한다.
- 짧은 표현보다 읽기 쉬운 코드를 우선한다.
- 대용량 입력에는 generator, 반복 실행 도구에는 명령줄 인자를 고려한다.
- 외부 입력은 코드·명령·경로로 사용하기 전에 검증한다.
