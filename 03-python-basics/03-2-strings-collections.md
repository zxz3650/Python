# 03-2. 문자열과 자료구조

{% hint style="info" %}
### 🧭 이 절의 핵심 질문

- 문자열 하나와 여러 데이터를 담는 자료구조는 어떻게 다른가?
- `list`, `tuple`, `set`, `dict` 중 무엇을 언제 선택하는가?
- 자료구조를 선택하면 로그 분석과 탐지 로직이 어떻게 쉬워지는가?
{% endhint %}

## `list`와 `dict`를 먼저 이해하기

### 리스트(`list`): 순서가 있는 여러 값

리스트는 여러 값을 순서대로 담는 자료구조다. 대괄호(`[]`)로 만들며, 인덱스는 0부터 시작한다. 로그 이벤트처럼 **같은 종류의 데이터가 여러 개 있고 순서대로 처리해야 할 때** 사용한다.

```python
ports = [22, 80, 443]

print(ports[0])       # 22
print(ports[-1])      # 443
ports.append(8080)    # 값 추가
print(ports)          # [22, 80, 443, 8080]

for port in ports:
    print(port)
```

리스트에는 서로 다른 자료형도 담을 수 있지만, 한 리스트에는 가능한 한 의미가 비슷한 값을 담는 것이 읽기 쉽고 안전하다.

### 딕셔너리(`dict`): 이름표가 붙은 값의 묶음

딕셔너리는 키(key)와 값(value)을 연결한다. 중괄호(`{}`)로 만들며, **한 대상을 여러 속성으로 표현할 때** 사용한다.

```python
event = {
    "action": "DENY",
    "ip": "198.51.100.9",
    "port": 443,
}

print(event["ip"])          # 키로 값 조회
event["user"] = "bob"       # 새 필드 추가
event["action"] = "REVIEW"  # 기존 값 수정

for key, value in event.items():
    print(key, value)
```

키가 없을 수 있는 외부 데이터는 대괄호로 바로 조회하면 `KeyError`가 날 수 있다. 이때는 기본값을 정하는 `get()`을 사용한다.

```python
path = event.get("path", "(경로 없음)")
```

실무에서는 보통 **여러 이벤트를 리스트에 담고, 이벤트 하나는 딕셔너리로 표현**한다.

```python
events = [
    {"action": "ALLOW", "ip": "10.0.0.5"},
    {"action": "DENY", "ip": "198.51.100.9"},
]

denied_ips = [event["ip"] for event in events if event["action"] == "DENY"]
print(denied_ips)
```

## 자료구조란 무엇인가

자료구조(data structure)는 여러 데이터를 **어떤 규칙으로 묶고, 찾고, 추가하고, 수정할지** 정한 형태다. 같은 데이터라도 구조에 따라 처리 방법과 속성이 달라진다.

예를 들어 로그 이벤트 하나는 여러 속성이 함께 있어야 하므로 `dict`가 적합하고, 이벤트 여러 개는 순서대로 처리해야 하므로 `list`에 담는다. 중복을 제거하거나 포함 여부만 빠르게 확인할 때는 `set`을 사용한다.

| 자료구조 | 핵심 특징 | 선택 기준 | 보안 실무 예 |
|---|---|---|---|
| `list` | 순서 있음, 중복 허용, 수정 가능 | 순서대로 모으고 반복할 때 | 로그 이벤트 목록 |
| `tuple` | 순서 있음, 수정 불가 | 변경되면 안 되는 묶음 | `(프로토콜, 포트)` |
| `set` | 중복 제거, 순서에 의존하지 않음 | 고유값·포함 여부를 다룰 때 | 중복 없는 IP 목록 |
| `dict` | 키와 값의 연결 | 이름으로 값을 찾을 때 | 한 이벤트의 필드 |
| 문자열 `str` | 문자들의 순서 있는 값 | 원문·메시지·경로를 다룰 때 | 로그 한 줄, URL |

{% hint style="info" %}
### 🧭 학습 목표

- 문자열을 정규화하고 분리한다.
- `list`, `tuple`, `set`, `dict`의 차이를 설명한다.
- 로그 이벤트를 구조화한다.
{% endhint %}

## 문자열 처리

```python
line = "  DENY 198.51.100.9 /admin  "
clean = line.strip()
parts = clean.split()

action, ip, path = parts
print(action.lower())
print("/admin" in path)

message = f"{ip} requested {path}"
```

원본 문자열이 필요한 분석에서는 원문과 정규화 결과를 별도로 보존한다.

## 자료구조

```python
ports = [22, 80, 443]                 # 순서와 중복 허용
connection = ("tcp", 443)             # 변경하지 않을 묶음
users = {"admin", "root", "admin"}    # 중복 제거
event = {"action": "DENY", "ip": "198.51.100.9"}
```

딕셔너리는 구조화된 이벤트 표현에 적합하다.

```python
event["action"] = "ALLOW"
event["path"] = "/health"

for key, value in event.items():
    print(key, value)
```

{% hint style="success" %}
## 🧪 실습

1. 로그 한 줄을 `dict`로 변환한다.
2. 중복 IP를 `set`으로 제거한다.
3. IP별 이벤트 목록을 딕셔너리에 저장한다.
{% endhint %}
