# 03-4. 반복문: for와 while

반복문은 같은 규칙을 여러 데이터에 적용한다. 로그의 모든 행을 검사하고, 조건을 만족하는 이벤트를 모으고, IP별 발생 횟수를 집계하거나, 정해진 횟수만큼 연결을 재시도할 때 사용한다.

반복문을 잘 작성한다는 것은 단순히 여러 번 실행하는 문법을 아는 것이 아니다. **무엇을 반복할지, 언제 끝낼지, 반복할 때마다 어떤 상태가 변할지, 결과를 어디에 모을지**를 명확히 설계해야 한다.

{% hint style="info" %}
### 🧭 학습 목표

- iterable, iterator, 반복 변수의 관계를 설명한다.
- 데이터 중심 반복에는 `for`, 조건 중심 반복에는 `while`을 선택한다.
- `range()`, `enumerate()`, `zip()`, `sorted()`, `reversed()`를 목적에 맞게 사용한다.
- 카운트·누적·필터·변환·검색·빈도 집계 패턴을 구현한다.
- `break`, `continue`, 반복문의 `else`가 실행 흐름에 미치는 영향을 설명한다.
- `while`의 종료 조건과 상태 갱신을 점검해 무한 루프를 예방한다.
- 반복 중 자료구조를 변경할 때 생기는 문제와 안전한 대안을 설명한다.
- 중첩 반복과 컴프리헨션을 실행 비용과 가독성 관점에서 판단한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | `for`·`while`, `range()`, 종료 조건, `break`·`continue` |
| 권장 | `enumerate()`·`zip()`, 카운트·누적·필터·검색·집계 패턴 |
| 심화 | iterable·iterator 내부 모델, 반복문 `else`, 중첩 비용, 컴프리헨션 |

처음 학습한다면 2절의 `for`부터 실습한 뒤 1절의 iterable·iterator 설명으로 돌아와도 된다.

## 학습 범위와 연결

- 리스트·튜플·딕셔너리·집합의 특성은 [03-2](03-2-strings-collections.md)에서 학습했다.
- 비교·논리 연산자와 한 이벤트에 대한 판단은 [03-3](03-3-conditions.md)에서 학습했다.
- 이 절에서는 같은 판단을 여러 이벤트에 반복 적용하고 결과를 모은다.
- 반복 코드를 재사용 가능한 단위로 분리하는 함수는 03-5에서 다룬다.
- 파일을 한 줄씩 반복해 읽는 방법과 오류 처리는 이후 절에서 다룬다.

전용 실습은 [`notebooks/03-4-loops.ipynb`](../notebooks/03-4-loops.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

실행하기 전에 출력 결과와 반복 횟수를 예상한다.

```python
for number in range(1, 5):
    print(number)

for index, action in enumerate(["ALLOW", "DENY"], start=1):
    print(index, action)

attempts = 0
while attempts < 3:
    attempts += 1
print(attempts)
```

다음 질문에 답해 본다.

1. `range(1, 5)`는 몇 개의 값을 만드는가?
2. 리스트의 값만 필요할 때 `range(len(items))`를 사용해야 하는가?
3. `break`와 `continue`는 각각 어디로 실행 흐름을 이동시키는가?
4. `while`이 반드시 끝나게 하려면 무엇을 확인해야 하는가?
5. 반복 중 현재 리스트에서 항목을 삭제해도 안전한가?
6. 반복문의 `else`는 언제 실행되는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. 반복 모델: iterable과 iterator

리스트, 문자열, 딕셔너리처럼 값을 하나씩 제공할 수 있는 객체를 **iterable**이라고 한다. `for`는 iterable에서 iterator를 만들고, 값이 모두 소진될 때까지 하나씩 꺼낸다.

```python
events = ["ALLOW", "DENY", "DENY"]

for event in events:
    print(event)
```

`event`는 매 반복마다 현재 값을 가리키는 **반복 변수**다. 반복 변수의 이름은 `x`보다 `event`, `line`, `port`처럼 값의 의미를 드러내는 것이 좋다.

`iter()`와 `next()`를 사용하면 `for`가 내부적으로 값을 꺼내는 모습을 확인할 수 있다.

```python
events = ["ALLOW", "DENY"]
event_iterator = iter(events)

print(next(event_iterator))  # ALLOW
print(next(event_iterator))  # DENY
```

iterator는 현재 위치를 기억하며 한 번 소비한 값을 자동으로 되돌리지 않는다. 값이 모두 소진된 뒤 `next()`를 다시 호출하면 `StopIteration`이 발생한다. 일반적인 데이터 순회에는 이 세부 처리를 맡아 주는 `for`가 더 안전하고 읽기 쉽다.

{% hint style="warning" %}
`iterable`은 반복 가능한 데이터이고 `iterator`는 그 데이터에서 **다음 값을 꺼내는 상태를 가진 객체**다. 두 용어를 같은 뜻으로 사용하지 않는다.
{% endhint %}

## 2. for: 값을 직접 순회하기

`for`는 값 모음의 모든 항목을 처리할 때 기본 선택이다.

```python
actions = ["ALLOW", "DENY", "DENY"]

for action in actions:
    print(action)
```

문자열은 문자 단위로 반복된다.

```python
for character in "DENY":
    print(character)
```

딕셔너리를 직접 반복하면 키가 나온다. 키와 값이 모두 필요하면 `.items()`를 사용한다.

```python
record = {"action": "DENY", "port": 443}

for key in record:
    print(key)

for key, value in record.items():
    print(key, value)
```

목적에 맞는 순회 방식을 선택한다.

| 필요한 값 | 권장 방식 |
|---|---|
| 리스트의 값 | `for item in items` |
| 위치와 값 | `for index, item in enumerate(items)` |
| 딕셔너리 키 | `for key in mapping` |
| 딕셔너리 키와 값 | `for key, value in mapping.items()` |
| 두 자료의 대응 값 | `for left, right in zip(a, b)` |

## 3. range: 정수 구간과 반복 횟수

`range(start, stop, step)`은 정수 구간을 표현한다. `stop`은 포함하지 않는다.

```python
for number in range(3):
    print(number)       # 0, 1, 2

for port in range(8000, 8003):
    print(port)         # 8000, 8001, 8002

for number in range(0, 10, 2):
    print(number)       # 0, 2, 4, 6, 8
```

감소하는 구간에는 음수 `step`이 필요하다.

```python
for remaining in range(3, 0, -1):
    print(remaining)    # 3, 2, 1
```

| 표현 | 생성되는 값 | 반복 횟수 |
|---|---|---:|
| `range(4)` | `0, 1, 2, 3` | 4 |
| `range(1, 4)` | `1, 2, 3` | 3 |
| `range(2, 8, 2)` | `2, 4, 6` | 3 |
| `range(3, 0, -1)` | `3, 2, 1` | 3 |

끝값 제외 규칙을 놓치면 **off-by-one 오류**, 즉 경계에서 한 번 많거나 적게 반복하는 오류가 생긴다. `list(range(...))`로 작은 예를 확인하면 경계를 빠르게 검증할 수 있다.

```python
print(list(range(1, 5)))       # [1, 2, 3, 4]
print(list(range(5, 0, -2)))   # [5, 3, 1]
```

{% hint style="info" %}
`range()`는 “숫자를 만들어야 할 때” 또는 “정해진 횟수만큼 반복할 때” 사용한다. 목록의 값을 처리하려는 목적이라면 인덱스를 만들지 말고 값을 직접 순회한다.
{% endhint %}

## 4. 값, 위치, 여러 입력 중 무엇이 필요한가

### 값만 필요하면 직접 순회

```python
actions = ["ALLOW", "DENY"]

for action in actions:
    print(action)
```

다음 코드는 동작하지만 값만 필요한 상황에서는 불필요하게 복잡하다.

```python
for index in range(len(actions)):
    print(actions[index])
```

### 위치와 값이 필요하면 enumerate

`enumerate()`는 `(위치, 값)` 쌍을 제공한다.

```python
lines = [
    "ALLOW 10.0.0.5",
    "",
    "DENY 198.51.100.9",
]

for line_number, line in enumerate(lines, start=1):
    if not line.strip():
        continue
    print(line_number, line)
```

`start=1`은 로그의 실제 행 번호처럼 사람이 세는 번호와 맞출 때 유용하다. 원본 리스트의 인덱스가 필요한 경우에는 기본값 `0`을 유지한다.

### 대응하는 여러 입력은 zip

```python
ips = ["10.0.0.5", "198.51.100.9"]
actions = ["ALLOW", "DENY"]

for ip, action in zip(ips, actions):
    print(ip, action)
```

기본 `zip()`은 가장 짧은 입력이 끝나면 종료한다. 길이 차이가 데이터 오류라면 Python 3.10 이상에서 `strict=True`로 조용한 누락을 막는다.

```python
ips = ["10.0.0.5", "198.51.100.9"]
actions = ["ALLOW", "DENY"]

for ip, action in zip(ips, actions, strict=True):
    print(ip, action)
```

입력 길이가 다르면 `ValueError`가 발생한다. 오류 처리는 이후 절에서 배우므로, 지금은 `strict=True`가 잘못 정렬된 병렬 데이터를 발견하는 장치라는 점을 기억한다.

## 5. while: 조건이 참인 동안 반복

`while`은 데이터 모음보다 **상태와 종료 조건**이 중심일 때 적합하다. 재시도, 입력 대기, 임계값 도달 과정이 대표적이다.

```python
attempts = 0

while attempts < 3:
    attempts += 1
    print(f"시도 {attempts}")
```

안전한 `while`에는 다음 세 요소가 필요하다.

| 요소 | 위 예의 코드 | 점검 질문 |
|---|---|---|
| 초기 상태 | `attempts = 0` | 시작값이 조건과 맞는가? |
| 계속 조건 | `attempts < 3` | 언제 거짓이 되는가? |
| 상태 갱신 | `attempts += 1` | 매 반복이 종료에 가까워지는가? |

반복이 진행되는 동안 반드시 참이어야 하는 관계를 **불변 조건(invariant)**으로 생각할 수도 있다. 위 예에서는 반복 중 `0 <= attempts <= 3`이어야 한다. 시작 전, 반복 중, 종료 후의 값을 확인하면 무한 루프와 경계 오류를 찾기 쉽다.

### for와 while 선택 기준

| 상황 | 권장 |
|---|---|
| 목록의 모든 이벤트 처리 | `for` |
| 정확히 5번 실행 | `for ... in range(5)` |
| 성공하거나 최대 횟수에 도달할 때까지 재시도 | `while` |
| 종료 표식을 만날 때까지 처리 | `while` 또는 `for`와 `break` |

횟수가 명확한데 `while`로 직접 카운터를 관리할 필요는 없다.

```python
for attempt_number in range(1, 4):
    print(f"시도 {attempt_number}")
```

## 6. while True와 종료 경로

종료 조건을 반복문 내부에서 판단할 때 `while True`를 사용할 수 있다.

```python
inputs = ["first", "second", ""]
position = 0

while True:
    value = inputs[position]
    position += 1

    if value == "":
        break

    print(value)
```

`while True`를 쓰기 전에 다음을 확인한다.

- 정상 입력에서 `break`에 도달하는가?
- 빈 입력이나 잘못된 입력에서도 종료할 수 있는가?
- 외부 시스템이 응답하지 않을 때 최대 시도 횟수나 시간 제한이 있는가?
- 상태 갱신이 `continue` 때문에 건너뛰어지지 않는가?

실제 재시도 로직에는 무제한 반복보다 최대 횟수를 두는 편이 안전하다.

```python
responses = [False, False, True]
attempt = 0
is_connected = False

while attempt < 3 and not is_connected:
    is_connected = responses[attempt]
    attempt += 1

print(attempt, is_connected)  # 3 True
```

## 7. continue와 break

- `continue`: 현재 반복의 남은 문장을 건너뛰고 다음 반복으로 이동한다.
- `break`: 가장 가까운 반복문을 즉시 종료한다.

```python
events = ["ALLOW", "", "DENY", "STOP", "DENY"]

for event in events:
    if not event:
        continue

    if event == "STOP":
        break

    print("처리:", event)
```

출력:

```text
처리: ALLOW
처리: DENY
```

빈 문자열에서는 `continue` 때문에 아래 코드가 실행되지 않는다. `STOP`에서는 `break` 때문에 마지막 `DENY`까지 도달하지 않는다.

중첩 반복에서 `break`는 가장 가까운 반복문 하나만 종료한다.

```python
for host in ["web-1", "web-2"]:
    for port in [80, 443, 8080]:
        if port == 443:
            break
        print(host, port)
```

각 호스트의 내부 반복만 443에서 종료되므로 외부 반복은 `web-2`까지 계속된다.

{% hint style="warning" %}
`while`에서 상태 갱신 전에 `continue`하면 갱신 코드가 실행되지 않아 무한 루프가 생길 수 있다. 상태를 먼저 갱신하거나 실행 경로마다 종료 방향으로 상태가 변하는지 확인한다.
{% endhint %}

## 8. 반복문의 else: 중단 없이 끝났는가

`for`와 `while`에도 `else`를 붙일 수 있다. 반복 대상이 모두 소진되거나 `while` 조건이 거짓이 되어 **정상 종료하면** `else`가 실행되고, `break`로 종료하면 실행되지 않는다.

검색에서 특히 유용하다.

```python
open_ports = [22, 80, 443]
target_port = 3389

for port in open_ports:
    if port == target_port:
        print("대상 포트 발견")
        break
else:
    print("대상 포트 없음")
```

출력:

```text
대상 포트 없음
```

`else`는 마지막 `if`가 아니라 `for`와 같은 들여쓰기 깊이에 있다. 의미는 “조건이 거짓”이 아니라 **`break` 없이 반복을 완료함**이다.

```python
attempt = 0

while attempt < 3:
    attempt += 1
    if attempt == 2:
        print("성공")
        break
else:
    print("모든 재시도 실패")
```

## 9. 핵심 반복 패턴

반복문 문제는 대부분 몇 가지 패턴의 조합이다. 반복 전에 결과를 저장할 변수를 초기화하고, 반복 안에서 현재 값에 따라 갱신한다.

### 9.1 카운트: 몇 개인가

```python
actions = ["ALLOW", "DENY", "DENY", "ALLOW"]
deny_count = 0

for action in actions:
    if action == "DENY":
        deny_count += 1

print(deny_count)  # 2
```

### 9.2 누적: 합계가 얼마인가

```python
packet_sizes = [120, 80, 200]
total_size = 0

for size in packet_sizes:
    total_size += size

print(total_size)  # 400
```

숫자 합계는 `sum(packet_sizes)`로도 구할 수 있다. 먼저 반복 패턴을 이해하고, 의도가 분명한 내장 함수가 있다면 활용한다.

### 9.3 필터: 조건을 만족하는 값만 모으기

```python
actions = ["ALLOW", "DENY", "DENY"]
denied_actions = []

for action in actions:
    if action == "DENY":
        denied_actions.append(action)

print(denied_actions)
```

### 9.4 변환: 각 값을 다른 형태로 바꾸기

```python
raw_actions = [" allow ", "Deny", "DENY"]
normalized_actions = []

for action in raw_actions:
    normalized_actions.append(action.strip().upper())

print(normalized_actions)
```

### 9.5 빈도 집계: 값별로 몇 번인가

```python
source_ips = ["10.0.0.5", "198.51.100.9", "198.51.100.9"]
count_by_ip = {}

for ip in source_ips:
    count_by_ip[ip] = count_by_ip.get(ip, 0) + 1

print(count_by_ip)
```

`.get(ip, 0)`은 처음 등장한 IP의 기존 횟수를 0으로 간주한다.

### 9.6 고유값 수집: 중복 없이 무엇이 있는가

```python
source_ips = ["10.0.0.5", "198.51.100.9", "198.51.100.9"]
unique_ips = set()

for ip in source_ips:
    unique_ips.add(ip)

print(unique_ips)
```

결과의 순서가 중요하면 집합을 그대로 출력하지 말고 `sorted(unique_ips)`를 사용한다.

## 10. 검색: 첫 항목, 모든 항목, 존재 여부

반복을 시작하기 전에 원하는 결과를 구분한다.

- 첫 번째 일치 항목만 필요하다 → 찾으면 `break`
- 모든 일치 항목이 필요하다 → 리스트에 계속 추가
- 존재 여부만 필요하다 → bool 변수 또는 `any()` 고려
- 모든 항목이 조건을 만족해야 한다 → `all()` 고려

첫 번째 DENY 이벤트를 찾는다.

```python
events = [
    {"action": "ALLOW", "ip": "10.0.0.5"},
    {"action": "DENY", "ip": "198.51.100.9"},
    {"action": "DENY", "ip": "203.0.113.10"},
]

first_denied_event = None

for event in events:
    if event["action"] == "DENY":
        first_denied_event = event
        break

print(first_denied_event)
```

`break`가 없으면 마지막 일치 항목이 저장될 수 있다. “첫 번째”가 요구사항이라면 종료 위치도 요구사항의 일부다.

존재 여부만 필요하면 다음과 같이 표현할 수 있다.

```python
has_denied_event = any(
    event["action"] == "DENY"
    for event in events
)

print(has_denied_event)  # True
```

## 11. 중첩 반복과 실행 비용

```python
hosts = ["web-1", "web-2"]
ports = [80, 443, 8080]

for host in hosts:
    for port in ports:
        print(host, port)
```

외부 반복 2번마다 내부 반복 3번이 실행되므로 총 6쌍을 처리한다. 데이터가 각각 `n`개와 `m`개라면 조합은 `n × m`개다.

모든 조합이 정말 필요한지 먼저 확인한다. 단순 멤버십 검사를 위해 목록 전체를 매번 순회한다면 집합이나 딕셔너리로 바꿀 수 있다.

```python
blocked_ips = {"198.51.100.9", "203.0.113.10"}
event_ips = ["10.0.0.5", "198.51.100.9", "192.0.2.7"]

for ip in event_ips:
    if ip in blocked_ips:
        print("차단 목록 일치:", ip)
```

집합 멤버십을 사용하면 각 IP마다 차단 목록을 직접 중첩 순회할 필요가 없다. 데이터가 커질수록 자료구조 선택이 반복 비용에 큰 영향을 준다.

## 12. 반복 중 자료구조 변경

순회 중인 리스트에서 항목을 삭제하면 인덱스가 당겨져 일부 값이 건너뛰어질 수 있다.

```python
numbers = [1, 2, 2, 3]

# 피해야 할 코드
for number in numbers:
    if number == 2:
        numbers.remove(number)

print(numbers)  # [1, 2, 3]: 2 하나가 남음
```

필요한 값으로 새 리스트를 만드는 방법이 가장 명확하다.

```python
numbers = [1, 2, 2, 3]
filtered_numbers = []

for number in numbers:
    if number != 2:
        filtered_numbers.append(number)

print(filtered_numbers)  # [1, 3]
```

원본 객체 자체를 변경해야 한다면 먼저 복사본을 순회할 수 있다.

```python
numbers = [1, 2, 2, 3]

for number in numbers.copy():
    if number == 2:
        numbers.remove(number)

print(numbers)  # [1, 3]
```

딕셔너리도 순회 중 크기를 바꾸면 안 된다. 삭제할 키를 먼저 모으거나 `list(mapping)`처럼 키의 복사본을 순회한다.

```python
counts = {"ALLOW": 0, "DENY": 2, "UNKNOWN": 0}
keys_to_delete = []

for key, count in counts.items():
    if count == 0:
        keys_to_delete.append(key)

for key in keys_to_delete:
    del counts[key]

print(counts)  # {'DENY': 2}
```

## 13. 정렬된 순회와 역순 순회

`sorted()`는 정렬된 새 리스트를 만들고, `reversed()`는 역순 iterator를 제공한다. 원본을 직접 바꾸지 않고 순회 순서만 정할 수 있다.

```python
ports = [443, 22, 80]

for port in sorted(ports):
    print(port)              # 22, 80, 443

print(ports)                 # [443, 22, 80]
```

```python
steps = ["수집", "분석", "보고"]

for step in reversed(steps):
    print(step)              # 보고, 분석, 수집
```

집합과 딕셔너리는 목적에 따라 순서 가정이 위험할 수 있다. 사람이 비교할 출력이나 재현 가능한 보고서가 필요하면 정렬 기준을 명시한다.

## 14. 컴프리헨션: 간단한 변환과 필터

컴프리헨션은 새 컬렉션을 만드는 짧은 반복 표현이다.

### 리스트 컴프리헨션

```python
events = [
    {"action": "ALLOW", "ip": "10.0.0.5"},
    {"action": "DENY", "ip": "198.51.100.9"},
]

denied_ips = [
    event["ip"]
    for event in events
    if event["action"] == "DENY"
]

print(denied_ips)
```

### 집합·딕셔너리 컴프리헨션

```python
unique_actions = {event["action"] for event in events}
action_by_ip = {event["ip"]: event["action"] for event in events}

print(unique_actions)
print(action_by_ip)
```

컴프리헨션은 다음 조건에서 적합하다.

- 결과가 새 리스트·집합·딕셔너리다.
- 변환식이 짧다.
- 필터 조건이 하나이거나 즉시 이해할 수 있다.
- 부수 효과보다 값 생성이 목적이다.

여러 상태를 갱신하거나, 여러 단계의 조건 분기·로깅·`break`가 필요하면 일반 반복문이 더 읽기 쉽다.

{% hint style="warning" %}
짧은 코드가 언제나 쉬운 코드는 아니다. 중첩 컴프리헨션이나 복잡한 삼항 조건식은 일반 반복문으로 풀어 써서 판단 단계를 드러낸다.
{% endhint %}

## 15. 미니 실습: 이벤트 목록 분석

03-2의 중첩 자료구조와 03-3의 조건식을 여러 이벤트에 적용한다. 아직 함수를 배우기 전이므로 한 셀에서 단계별로 처리한다.

### 요구사항

1. `action`은 `ALLOW` 또는 `DENY`, `port`는 1~65535의 정수여야 한다.
2. 유효하지 않은 이벤트는 행 번호와 함께 `invalid_events`에 모으고 이후 분석에서 제외한다.
3. 유효한 DENY 이벤트, 고유 IP, IP별 DENY 횟수를 구한다.
4. DENY이면서 포트가 22 또는 3389이면 중요 이벤트로 분류한다.

```python
events = [
    {"action": "ALLOW", "ip": "10.0.0.5", "port": 443},
    {"action": "DENY", "ip": "198.51.100.9", "port": 22},
    {"action": "DENY", "ip": "198.51.100.9", "port": 3389},
    {"action": "BLOCK", "ip": "203.0.113.10", "port": 70000},
    {"action": "DENY", "ip": "203.0.113.10", "port": 443},
]

valid_actions = {"ALLOW", "DENY"}
sensitive_ports = {22, 3389}

valid_event_count = 0
invalid_events = []
denied_events = []
unique_ips = set()
deny_count_by_ip = {}
critical_events = []

for line_number, event in enumerate(events, start=1):
    action = event.get("action")
    port = event.get("port")

    has_valid_action = action in valid_actions
    has_valid_port = isinstance(port, int) and 1 <= port <= 65535

    if not (has_valid_action and has_valid_port):
        invalid_events.append({"line": line_number, "event": event})
        continue

    valid_event_count += 1
    unique_ips.add(event["ip"])

    if action == "DENY":
        denied_events.append(event)
        ip = event["ip"]
        deny_count_by_ip[ip] = deny_count_by_ip.get(ip, 0) + 1

        if port in sensitive_ports:
            critical_events.append(event)

summary = {
    "valid": valid_event_count,
    "invalid": len(invalid_events),
    "deny": len(denied_events),
    "unique_ip": len(unique_ips),
    "critical": len(critical_events),
}

print(summary)
print(deny_count_by_ip)
```

예상 결과:

```text
{'valid': 4, 'invalid': 1, 'deny': 3, 'unique_ip': 3, 'critical': 2}
{'198.51.100.9': 2, '203.0.113.10': 1}
```

결과를 눈으로만 확인하지 말고 핵심 조건을 `assert`로 고정한다.

```python
assert summary == {
    "valid": 4,
    "invalid": 1,
    "deny": 3,
    "unique_ip": 3,
    "critical": 2,
}
assert deny_count_by_ip == {
    "198.51.100.9": 2,
    "203.0.113.10": 1,
}
assert invalid_events[0]["line"] == 4
```

이 실습에는 순회, 위치 추적, 조건 분기, 조기 건너뛰기, 카운트, 리스트·집합·딕셔너리 누적이 함께 사용된다.

## 16. 흔한 실수와 점검법

| 실수 | 문제 | 점검·개선 |
|---|---|---|
| `range(1, 5)`가 5를 포함한다고 생각 | 마지막 값 누락 | `list(range(...))`로 경계 확인 |
| 값만 필요한데 `range(len(items))` 사용 | 코드가 복잡하고 인덱스 오류 가능 | 값을 직접 순회 |
| `while` 상태를 갱신하지 않음 | 무한 루프 | 초기값·조건·갱신을 표로 확인 |
| 갱신 전에 `continue` | 갱신이 건너뛰어짐 | 모든 실행 경로에서 진행 확인 |
| `zip()` 길이 차이를 무시 | 뒤쪽 데이터가 조용히 누락 | 필요하면 `strict=True` |
| 반복 중 리스트·딕셔너리 크기 변경 | 항목 누락 또는 실행 오류 | 새 컬렉션 생성·복사본 순회 |
| `break`가 모든 중첩 반복을 끝낸다고 생각 | 외부 반복이 계속 실행 | 가장 가까운 반복만 종료함을 확인 |
| 반복문 `else`를 `if`의 `else`로 오해 | 검색 실패 처리 위치 오류 | `break` 없이 끝났을 때 실행됨을 기억 |
| 누적 변수를 반복문 안에서 초기화 | 매번 이전 결과가 사라짐 | 반복문 전에 초기화 |
| 복잡한 컴프리헨션을 한 줄에 작성 | 조건과 결과를 검증하기 어려움 | 일반 반복문으로 분해 |

디버깅할 때는 다음 값을 작은 입력으로 출력한다.

```python
items = ["ALLOW", "", "DENY"]

for index, item in enumerate(items):
    print("반복 시작:", index, repr(item))
    if not item:
        print("건너뜀")
        continue
    print("처리 완료:", item)
```

현재 반복 번호, 현재 값, 분기 결과, 누적 변수의 변화를 확인하면 실행 흐름을 추적하기 쉽다.

## 17. 단계별 연습문제

### 17.1 출력 예측

코드를 실행하지 않고 출력과 반복 횟수를 적는다.

```python
for number in range(2, 8, 2):
    print(number)
```

```python
for action in ["ALLOW", "", "DENY", "STOP", "DENY"]:
    if action == "":
        continue
    if action == "STOP":
        break
    print(action)
```

### 17.2 경계와 역순

1. `range()`로 1~10을 포함해 출력한다.
2. 10부터 2까지 짝수만 역순으로 출력한다.
3. 두 표현의 `start`, `stop`, `step`을 설명한다.

### 17.3 enumerate와 zip

다음 두 목록을 사용해 `1: 10.0.0.5 -> ALLOW` 형식으로 출력한다.

```python
ips = ["10.0.0.5", "198.51.100.9"]
actions = ["ALLOW", "DENY"]
```

행 번호에는 `enumerate(..., start=1)`, 대응 값에는 `zip(..., strict=True)`를 사용한다.

### 17.4 반복 패턴

다음 목록에서 조건을 만족하도록 코드를 작성한다.

```python
ports = [22, 80, 443, 22, 3389, 70000]
```

1. 유효한 포트만 새 리스트에 모은다.
2. 포트별 등장 횟수를 딕셔너리에 집계한다.
3. 22 또는 3389가 하나라도 있는지 bool로 구한다.
4. 중복을 제거한 뒤 오름차순으로 출력한다.

### 17.5 검색과 loop else

`[80, 443, 8080]`에서 22를 검색한다. 찾으면 위치를 출력하고 `break`, 찾지 못한 경우 반복문의 `else`에서 `"없음"`을 출력한다. 그다음 대상을 443으로 바꿔 두 실행 경로를 모두 확인한다.

### 17.6 오류 수정

다음 코드가 종료되지 않는 이유를 설명하고 1, 2, 3을 한 번씩 출력하도록 수정한다.

```python
count = 1

while count <= 3:
    if count == 2:
        continue
    print(count)
    count += 1
```

### 17.7 안전한 필터링

다음 코드가 모든 빈 문자열을 제거하지 못할 수 있는 이유를 설명하고 새 리스트를 만드는 방식으로 수정한다.

```python
lines = ["ALLOW", "", "", "DENY"]

for line in lines:
    if line == "":
        lines.remove(line)
```

### 17.8 미니 실습 확장

15절의 이벤트에 다음 요구사항을 추가한다.

1. 유효한 이벤트의 포트별 횟수를 `count_by_port`에 집계한다.
2. 가장 먼저 등장한 중요 이벤트 하나만 `first_critical_event`에 저장한다.
3. 중요 이벤트가 없다면 반복문의 `else`에서 안내 문구를 출력한다.
4. 결과를 예상한 뒤 `assert`로 검증한다.

### 17.9 전이 연습 — 재고 목록 집계

다음 재고 목록에서 유효한 항목만 처리한다.

```python
stocks = [12, 0, -1, 7, 0, 15]
```

1. 음수는 잘못된 값이므로 별도 `invalid_stocks`에 모은다.
2. 0인 항목 수를 센다.
3. 양수 재고의 합계와 평균을 구한다.
4. 첫 번째 품절 위치를 찾고, 없으면 반복문의 `else`에서 `None`을 유지한다.
5. 원본 리스트를 변경하지 않는다.

## 18. 연습문제 정답과 해설

<details>
<summary>정답과 해설 펼치기</summary>

### 18.1 출력 예측

첫 코드는 `2`, `4`, `6`을 출력한다. `8`은 끝값이므로 포함되지 않는다. 두 번째 코드는 `ALLOW`, `DENY`만 출력한다. 빈 문자열은 `continue`, `STOP`과 그 뒤 값은 `break` 때문에 출력되지 않는다.

### 18.2 경계와 역순

```python
for number in range(1, 11):
    print(number)

for number in range(10, 1, -2):
    print(number)
```

### 18.3 enumerate와 zip

```python
ips = ["10.0.0.5", "198.51.100.9"]
actions = ["ALLOW", "DENY"]

for line_number, (ip, action) in enumerate(
    zip(ips, actions, strict=True),
    start=1,
):
    print(f"{line_number}: {ip} -> {action}")
```

### 18.4 반복 패턴

```python
ports = [22, 80, 443, 22, 3389, 70000]
valid_ports = []
count_by_port = {}

for port in ports:
    if 1 <= port <= 65535:
        valid_ports.append(port)
        count_by_port[port] = count_by_port.get(port, 0) + 1

has_sensitive_port = any(port in {22, 3389} for port in valid_ports)

print(valid_ports)
print(count_by_port)
print(has_sensitive_port)
print(sorted(set(valid_ports)))
```

### 18.5 검색과 loop else

```python
ports = [80, 443, 8080]
target = 22

for index, port in enumerate(ports):
    if port == target:
        print("위치:", index)
        break
else:
    print("없음")
```

`target = 22`이면 `없음`, `target = 443`이면 `위치: 1`을 출력한다.

### 18.6 오류 수정

`count == 2`일 때 `continue`가 `count += 1`을 건너뛰므로 `count`가 계속 2에 머문다. 상태를 분기 전에 갱신하거나 `continue`를 제거한다.

```python
count = 1

while count <= 3:
    print(count)
    count += 1
```

### 18.7 안전한 필터링

첫 번째 빈 문자열을 삭제하면 뒤의 값이 앞으로 이동하지만 iterator는 다음 위치로 진행하므로 두 번째 빈 문자열을 건너뛸 수 있다.

```python
lines = ["ALLOW", "", "", "DENY"]
non_empty_lines = []

for line in lines:
    if line != "":
        non_empty_lines.append(line)

print(non_empty_lines)
```

### 18.8 미니 실습 확장 예

```python
count_by_port = {}

for event in events:
    action = event.get("action")
    port = event.get("port")
    is_valid = (
        action in valid_actions
        and isinstance(port, int)
        and 1 <= port <= 65535
    )

    if is_valid:
        count_by_port[port] = count_by_port.get(port, 0) + 1

first_critical_event = None

for event in events:
    if (
        event.get("action") == "DENY"
        and event.get("port") in sensitive_ports
    ):
        first_critical_event = event
        break
else:
    print("중요 이벤트 없음")

assert count_by_port == {443: 2, 22: 1, 3389: 1}
assert first_critical_event == events[1]
```

### 18.9 전이 연습 예시 답안

```python
stocks = [12, 0, -1, 7, 0, 15]
valid_positive_stocks = []
invalid_stocks = []
out_of_stock_count = 0

for stock in stocks:
    if stock < 0:
        invalid_stocks.append(stock)
        continue
    if stock == 0:
        out_of_stock_count += 1
        continue
    valid_positive_stocks.append(stock)

total_stock = sum(valid_positive_stocks)
average_stock = total_stock / len(valid_positive_stocks)

first_out_of_stock = None
for index, stock in enumerate(stocks):
    if stock == 0:
        first_out_of_stock = index
        break
else:
    first_out_of_stock = None

assert invalid_stocks == [-1]
assert out_of_stock_count == 2
assert total_stock == 34
assert average_stock == 34 / 3
assert first_out_of_stock == 1
assert stocks == [12, 0, -1, 7, 0, 15]
```

</details>

## 19. 완료 기준

다음 항목을 코드와 말로 설명하고 결과물로 확인한다.

- [ ] 값을 직접 순회할 때와 `range()`가 필요할 때를 구분한다.
- [ ] 위치가 필요하면 `enumerate()`, 대응 값이 필요하면 `zip()`을 사용한다.
- [ ] `while`의 초기 상태·계속 조건·상태 갱신을 찾을 수 있다.
- [ ] 카운트·누적·필터·변환·검색·집계를 직접 작성한다.
- [ ] `continue`, `break`, 반복문의 `else` 실행 시점을 예측한다.
- [ ] 반복 중 자료구조의 크기를 바꾸는 코드의 위험을 설명한다.
- [ ] 중첩 반복의 실행 횟수와 컴프리헨션의 가독성을 판단한다.
- [ ] 작은 입력과 `assert`로 경계와 누적 결과를 검증한다.
- [ ] 재고 전이 연습을 원본 변경 없이 완성한다.

## 핵심 정리

- 데이터 모음의 값을 처리할 때는 `for`, 상태가 조건을 만족하는 동안 반복할 때는 `while`이 적합하다.
- `range()`의 끝값은 제외되며, 값만 필요하면 인덱스 대신 직접 순회한다.
- 반복 결과는 카운트·누적·필터·변환·검색·빈도 집계 패턴으로 설계할 수 있다.
- `break`는 가장 가까운 반복을 종료하고, `continue`는 현재 반복의 남은 코드를 건너뛴다.
- 반복문의 `else`는 `break` 없이 반복을 완료했을 때 실행된다.
- 안전한 `while`에는 명확한 초기값, 종료 조건, 상태 갱신이 필요하다.
- 순회 중인 컬렉션의 크기를 바꾸지 말고 새 컬렉션이나 복사본을 사용한다.
- 중첩 반복은 실행 횟수를 계산하고, 컴프리헨션은 단순한 값 생성에만 사용한다.
