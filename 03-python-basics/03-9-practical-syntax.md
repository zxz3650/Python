# 03-9. 실무 보강 문법

앞선 챕터에서 다룬 문법을 실제 로그·파일·자동화 코드에 적용하기 위해 자주 빠지는 Python 문법을 보강한다.

{% hint style="info" %}
### 🧭 학습 목표

- 연산자와 인덱싱·슬라이싱을 정확히 사용한다.
- `range()`, `sorted()`, `reversed()`로 반복을 제어한다.
- 함수 인자와 타입 힌트를 활용한다.
- 컴프리헨션과 generator의 차이를 이해한다.
- 모듈·패키지와 예외 계층을 안전하게 사용한다.
- 보안 자동화 코드에서 피해야 할 Python 기능을 설명한다.
{% endhint %}

## 1. 연산자

### 산술 연산자

```python
total = 17
count = 5

print(total / count)   # 일반 나눗셈: 3.4
print(total // count)  # 몫: 3
print(total % count)   # 나머지: 2
print(2 ** 3)          # 거듭제곱: 8
```

### 비교·논리·멤버십·동일성

```python
action = "DENY"
failed = 5

is_suspicious = action == "DENY" and failed >= 3
is_known = action in {"ALLOW", "DENY"}

value = None
print(value is None)       # None 여부는 is로 확인
print(value is not None)
```

`==`는 값의 같음을 비교하고, `is`는 같은 객체인지 비교한다. `None` 비교에는 `is None`을 사용한다.

## 2. 인덱싱·슬라이싱·복사

```python
ips = ["10.0.0.5", "198.51.100.9", "203.0.113.7"]

print(ips[0])
print(ips[-1])
print(ips[1:])      # 두 번째부터 끝까지
print(ips[::2])     # 한 칸씩 건너뛰기
print(ips[::-1])    # 역순
```

리스트와 딕셔너리는 변경 가능한 객체다. 같은 객체를 가리키는 대입과 복사를 구분한다.

```python
original = {"tags": ["auth"]}
alias = original
alias["tags"].append("deny")
print(original)     # 함께 변경됨

copied = original.copy()  # 얕은 복사
```

중첩 구조를 독립적으로 복사해야 한다면 `copy.deepcopy()`를 검토한다.

## 3. 문자열과 안전한 데이터 접근

```python
line = "DENY,198.51.100.9,/admin"
action, ip, path = line.split(",", maxsplit=2)

if path.startswith("/admin") and path.endswith("min"):
    print(f"{ip} 접근: {action}")

parts = ["DENY", ip, path]
print("|".join(parts))
```

외부 데이터는 키나 필드가 없을 수 있으므로 딕셔너리에서 직접 접근하기 전에 `get()`을 사용할 수 있다.

```python
event = {"action": "DENY"}
ip = event.get("ip")
if ip is None:
    print("IP 누락")
```

원문이 필요한 분석에서는 정규화한 문자열과 원문을 별도로 보존한다.

## 4. 반복 도구

```python
events = ["ALLOW", "DENY", "DENY"]

for index in range(len(events)):
    print(index, events[index])

for event in reversed(events):
    print(event)

for event in sorted(events):
    print(event)
```

정렬 기준은 `key` 함수로 명시할 수 있다.

```python
records = [
    {"ip": "10.0.0.5", "count": 2},
    {"ip": "198.51.100.9", "count": 7},
]

for record in sorted(records, key=lambda item: item["count"], reverse=True):
    print(record)
```

반복이 정상적으로 끝났을 때만 실행되는 `else`도 있다.

```python
for event in events:
    if event == "CRITICAL":
        break
else:
    print("중대 이벤트 없음")
```

## 5. 컴프리헨션과 generator

```python
records = [
    {"action": "DENY", "ip": "10.0.0.5"},
    {"action": "ALLOW", "ip": "198.51.100.9"},
]

denied = [r["ip"] for r in records if r["action"] == "DENY"]
counts = {ip: denied.count(ip) for ip in set(denied)}
unique_actions = {r["action"] for r in records}
```

리스트 컴프리헨션은 결과를 메모리에 만든다. 대용량 로그에는 generator expression 또는 `yield`를 사용한다.

```python
def non_empty_lines(lines):
    for line in lines:
        line = line.strip()
        if line:
            yield line

for line in non_empty_lines(["", "first", "second"]):
    print(line)
```

## 6. 함수 인자와 타입 힌트

```python
def classify(count: int, threshold: int = 3) -> str:
    """실패 횟수를 위험 수준으로 분류한다."""
    if count >= threshold:
        return "WARNING"
    return "NORMAL"

print(classify(count=5, threshold=4))
```

기본값 인자는 변경 가능한 객체를 사용하지 않는다.

```python
def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    if tags is None:
        tags = []
    tags.append(tag)
    return tags
```

필요하면 가변 인자와 키워드 인자를 사용할 수 있다.

```python
def make_event(action, *values, **metadata):
    return {"action": action, "values": values, "metadata": metadata}
```

## 7. 모듈과 패키지

```python
import ipaddress
from pathlib import Path
from datetime import datetime, timezone

address = ipaddress.ip_address("198.51.100.9")
print(address.is_private)
print(datetime.now(timezone.utc))
```

프로젝트 코드는 기능별 모듈로 나누고 실행 진입점을 명확히 한다.

```python
def main() -> None:
    print("분석 시작")

if __name__ == "__main__":
    main()
```

`import` 시 실행되는 부수효과를 줄이고, 모듈은 함수·상수·클래스 중심으로 구성한다.

## 8. 예외 계층과 원인 보존

```python
try:
    port = int("not-a-number")
except ValueError as exc:
    raise ValueError("포트 형식이 올바르지 않습니다") from exc
```

가능한 구체적인 예외를 처리한다.

- `ValueError`: 값의 형식이 잘못됨
- `TypeError`: 자료형이 예상과 다름
- `KeyError`: 딕셔너리 키가 없음
- `IndexError`: 인덱스 범위를 벗어남
- `FileNotFoundError`: 파일이 없음

`except Exception`으로 모든 오류를 숨기면 프로그래밍 오류까지 놓칠 수 있다.

## 9. 보안 자동화에서 피할 것

```python
# 사용자가 입력한 문자열을 코드로 실행하지 않는다.
# eval(user_input)
# exec(user_input)
```

- `eval()`, `exec()`로 외부 입력을 실행하지 않는다.
- `subprocess` 사용 시 문자열 명령어 조합보다 인자 리스트를 사용한다.
- 비밀번호·토큰·API 키를 소스 코드에 저장하지 않는다.
- 파일 경로는 허용된 기준 디렉터리 안에 있는지 검증한다.
- `assert`를 사용자 입력 검증이나 권한 판정에 사용하지 않는다.

{% hint style="success" %}
## 🧪 실습

1. IP별 DENY 횟수를 딕셔너리 컴프리헨션으로 만든다.
2. 대용량 로그를 generator로 한 줄씩 처리한다.
3. 함수에 타입 힌트와 기본값 인자를 추가한다.
4. `ValueError`, `FileNotFoundError`를 구분해 처리한다.
5. 외부 입력을 `eval()` 없이 안전하게 처리한다.
{% endhint %}
