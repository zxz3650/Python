# 03-4. 반복문: while, True, for

## 학습 목표

- `for`와 `while`의 차이를 이해한다.
- `while True`와 종료 조건을 안전하게 사용한다.
- `break`, `continue`, `enumerate`, `zip`을 활용한다.

## for 반복

```python
events = ["ALLOW", "DENY", "DENY"]

for event in events:
    print(event)
```

로그 행 번호를 보존하려면 `enumerate()`를 사용한다.

```python
for line_number, line in enumerate(lines, start=1):
    if not line.strip():
        continue
    print(line_number, line)
```

## while과 while True

반복 횟수가 정해지지 않은 입력 처리에는 `while`을 사용할 수 있다.

```python
attempts = 0

while attempts < 3:
    attempts += 1
    print(f"attempt: {attempts}")
```

`while True`는 반드시 명확한 종료 조건을 가져야 한다.

```python
index = 0

while True:
    if index >= len(events):
        break
    print(events[index])
    index += 1
```

종료 조건이 없으면 무한 루프가 발생한다.

## break와 continue

- `break`: 반복 전체 종료
- `continue`: 현재 반복만 건너뜀

```python
for event in events:
    if event == "ALLOW":
        continue
    print("검토 필요:", event)
```

## zip과 컴프리헨션

```ips = ["10.0.0.5", "198.51.100.9"]
actions = ["ALLOW", "DENY"]

for ip, action in zip(ips, actions):
    print(ip, action)

denied = [ip for ip, action in zip(ips, actions) if action == "DENY"]
```

## 실습

1. `while True`로 로그를 읽되 빈 입력에서 종료한다.
2. 오류 행은 건너뛰고 행 번호를 기록한다.
3. DENY 이벤트만 별도 목록으로 만든다.
