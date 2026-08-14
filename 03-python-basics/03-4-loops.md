# 03-4. 반복문: for와 while

반복문은 같은 작업을 여러 데이터에 적용한다. 로그 파일의 모든 행을 검사하거나 재시도 횟수를 제한할 때 사용한다.

{% hint style="info" %}
### 🧭 학습 목표

- iterable과 반복 변수의 의미를 설명한다.
- `for`와 `while`의 선택 기준을 구분한다.
- `range()`, `enumerate()`, `zip()`을 사용한다.
- `break`, `continue`, 무한 루프를 안전하게 다룬다.
{% endhint %}

## 1. for: 값을 하나씩 꺼내기

```python
events = ["ALLOW", "DENY", "DENY"]

for event in events:
    print(event)
```

리스트처럼 값을 하나씩 제공할 수 있는 객체를 iterable이라고 한다. `event`는 매 반복마다 다음 값을 가리키는 반복 변수다.

문자열과 딕셔너리도 반복할 수 있다.

```python
for char in "DENY":
    print(char)

record = {"action": "DENY", "port": 443}
for key, value in record.items():
    print(key, value)
```

## 2. range: 횟수 반복

```python
for number in range(3):
    print(number)       # 0, 1, 2

for port in range(8000, 8003):
    print(port)         # 8000, 8001, 8002

for number in range(0, 10, 2):
    print(number)       # 0, 2, 4, 6, 8
```

끝값은 포함되지 않는다. 단순히 목록의 값을 처리할 때는 `range(len(items))`보다 직접 반복한다.

## 3. enumerate: 값과 위치 함께 얻기

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

로그의 실제 행 번호처럼 위치가 필요할 때 사용한다.

## 4. zip: 여러 iterable을 함께 처리

```python
ips = ["10.0.0.5", "198.51.100.9"]
actions = ["ALLOW", "DENY"]

for ip, action in zip(ips, actions):
    print(ip, action)
```

기본 `zip()`은 가장 짧은 입력이 끝나면 종료한다. 길이 차이가 오류라면 Python 3.10 이상에서 `zip(..., strict=True)`를 사용할 수 있다.

## 5. while: 조건이 참인 동안 반복

```python
attempts = 0

while attempts < 3:
    attempts += 1
    print(f"attempt: {attempts}")
```

`while`은 반복 횟수보다 종료 조건이 중요한 입력·재시도 처리에 적합하다. 조건에 사용되는 값이 반복 중 바뀌지 않으면 무한 루프가 될 수 있다.

## 6. while True와 종료 조건

```python
inputs = iter(["first", "second", ""])

while True:
    value = next(inputs)
    if value == "":
        break
    print(value)
```

`while True`는 입력 대기나 서비스 루프처럼 종료 시점을 내부에서 판단할 때 사용한다. 반드시 `break`, 예외, 반환 등 종료 경로를 확인한다.

## 7. break와 continue

- `break`: 가장 가까운 반복문 전체를 종료
- `continue`: 현재 반복의 나머지를 건너뛰고 다음 반복으로 이동

```python
events = ["ALLOW", "", "DENY", "STOP", "DENY"]

for event in events:
    if not event:
        continue
    if event == "STOP":
        break
    print("처리:", event)
```

## 8. 중첩 반복과 비용

```python
hosts = ["web-1", "web-2"]
ports = [80, 443]

for host in hosts:
    for port in ports:
        print(host, port)
```

위 코드는 2×2로 네 번 실행된다. 데이터가 커질수록 중첩 반복의 실행 횟수가 빠르게 증가하므로 필요한 경우에만 사용한다.

## 9. 컴프리헨션

간단한 변환·필터는 컴프리헨션으로 표현할 수 있다.

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
```

조건이나 변환이 복잡하면 일반 반복문이 더 읽기 쉽다.

## 10. 흔한 실수

- `range(1, 5)`가 5를 포함한다고 착각
- `while` 조건 변수를 변경하지 않아 무한 루프 발생
- 반복 중 리스트를 삭제해 일부 항목을 건너뜀
- `zip()` 입력 길이 차이를 놓침
- `break`가 모든 중첩 반복을 종료한다고 오해

{% hint style="success" %}
## 🧪 실습

1. `range()`로 1~10을 출력한다.
2. 로그 목록을 행 번호와 함께 출력하고 빈 행은 건너뛴다.
3. `while`로 최대 세 번만 입력을 재시도한다.
4. DENY 이벤트만 별도 리스트로 만든다.
5. 길이가 다른 두 리스트에 `zip(strict=True)`를 적용해 본다.
{% endhint %}

## 핵심 정리

- 값 모음을 처리할 때는 `for`, 조건 중심 반복에는 `while`이 적합하다.
- `enumerate()`는 위치, `zip()`은 여러 입력을 함께 처리한다.
- 무한 루프에는 명확한 종료 경로가 필요하다.
