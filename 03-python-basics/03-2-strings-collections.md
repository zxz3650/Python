# 03-2. 문자열과 자료구조

문자열과 자료구조는 수집한 데이터를 **읽고, 정리하고, 다시 찾기 위한 도구**다. 로그 한 줄은 문자열로 들어오지만, 분석할 때는 필드를 나누어 딕셔너리로 만들고 여러 이벤트를 리스트에 모은다.

{% hint style="info" %}
### 🧭 학습 목표

- 문자열과 숫자의 차이를 설명한다.
- 문자열을 정리·분리·검색·결합한다.
- `list`, `tuple`, `set`, `dict`의 선택 기준을 설명한다.
- 여러 로그를 `list[dict]` 구조로 표현하고 집계한다.
- 변경 가능한 자료구조의 참조와 복사를 구분한다.
{% endhint %}

## 1. 문자열이란 무엇인가

문자열(`str`)은 문자를 순서대로 모은 값이다. 사용자명, IP, URL, 로그 원문처럼 계산 대상이 아닌 텍스트를 표현한다.

```python
action = "DENY"
ip = "198.51.100.9"
port_text = "443"

print(type(action))  # <class 'str'>
print(len(ip))
print(action[0])     # D
```

따옴표 안에 있으면 숫자처럼 보여도 문자열이다.

```python
port_number = 443
port_text = "443"

print(port_number + 1)           # 444
print(port_text + "1")           # 4431
print(port_number == port_text)  # False
```

`443`은 계산 가능한 정수이고 `"443"`은 문자 세 개로 이루어진 텍스트다. 계산하려면 명시적으로 변환한다.

```python
port = int("443")
print(port >= 1024)  # False
```

## 2. 문자열 정리와 검색

외부 문자열에는 불필요한 공백, 줄바꿈, 대소문자 차이가 포함될 수 있다.

```python
raw = "  Deny 198.51.100.9 /Admin\n"
clean = raw.strip()
normalized = clean.lower()

print(clean)
print(normalized)
print(normalized.startswith("deny"))  # True
print("/admin" in normalized)         # True
```

| 메서드 | 역할 | 활용 |
|---|---|---|
| `strip()` | 양끝 공백·줄바꿈 제거 | 로그 한 줄 정리 |
| `lower()`, `upper()` | 대소문자 통일 | action 정규화 |
| `startswith()`, `endswith()` | 시작·끝 확인 | 경로와 확장자 검사 |
| `replace()` | 일부 문자열 치환 | 민감 정보 마스킹 |
| `split()` | 문자열 분리 | 로그 필드 추출 |
| `join()` | 문자열 결합 | 결과 문장 생성 |

분석 증거가 되는 원문은 덮어쓰지 않고 정규화 결과와 함께 보존한다.

## 3. 문자열을 필드로 분리하기

`split()`은 문자열을 나누고 리스트를 반환한다.

```python
line = "DENY 198.51.100.9 443 /admin"
parts = line.split()

print(parts)
# ['DENY', '198.51.100.9', '443', '/admin']

if len(parts) == 4:
    action, ip, port_text, path = parts
    port = int(port_text)
else:
    print("잘못된 로그 형식")
```

CSV처럼 값 안에 쉼표가 들어갈 수 있는 형식은 `split(",")` 대신 표준 `csv` 모듈을 사용한다.

## 4. 자료구조란 무엇인가

자료구조는 여러 값을 어떤 규칙으로 **저장하고, 찾고, 추가하고, 변경할지** 정한 형태다. 같은 데이터라도 앞으로 할 작업에 따라 적합한 구조가 달라진다.

| 자료구조 | 순서 | 중복 | 변경 | 적합한 상황 |
|---|---:|---:|---:|---|
| `list` | 있음 | 허용 | 가능 | 여러 값을 순서대로 처리 |
| `tuple` | 있음 | 허용 | 불가 | 변경되면 안 되는 값의 묶음 |
| `set` | 순서에 의존하지 않음 | 제거 | 가능 | 고유값과 포함 여부 확인 |
| `dict` | 입력 순서 유지 | 키 중복 불가 | 가능 | 이름표가 붙은 속성 표현 |

## 5. 리스트: 순서가 있는 값의 모음

리스트는 대괄호(`[]`)로 만든다. 인덱스는 0부터 시작하고 음수는 뒤에서부터 센다.

```python
ports = [22, 80, 443]

print(ports[0])   # 22
print(ports[-1])  # 443
print(ports[1:])  # [80, 443]

ports.append(8080)
ports[0] = 2222
ports.remove(80)

print(len(ports))
print(443 in ports)
```

로그 이벤트처럼 같은 의미의 데이터가 반복될 때 리스트가 적합하다.

```python
actions = ["ALLOW", "DENY", "DENY"]

for action in actions:
    print(action)
```

{% hint style="warning" %}
존재하지 않는 인덱스를 조회하면 `IndexError`가 발생한다. 가능한 경우 인덱스를 직접 계산하기보다 반복문을 사용한다.
{% endhint %}

## 6. 튜플: 변경하지 않을 값의 묶음

튜플은 소괄호(`()`)로 만들며 생성 후 항목을 변경할 수 없다.

```python
endpoint = ("tcp", "198.51.100.9", 443)
protocol, ip, port = endpoint
```

프로토콜·IP·포트처럼 하나의 의미를 이루며 변경되면 안 되는 묶음에 적합하다.

## 7. 세트: 중복 없는 값의 모음

세트는 중복을 제거하고 포함 여부를 확인하기 좋다.

```python
observed_ips = {"198.51.100.9", "10.0.0.5", "198.51.100.9"}
blocked_ips = {"198.51.100.9", "203.0.113.7"}

print("198.51.100.9" in observed_ips)
print(observed_ips & blocked_ips)  # 교집합
print(observed_ips - blocked_ips)  # 차집합
print(observed_ips | blocked_ips)  # 합집합
```

빈 세트는 `set()`으로 만든다. `{}`는 빈 딕셔너리다.

## 8. 딕셔너리: 키와 값의 연결

딕셔너리는 `키: 값`으로 속성에 이름을 붙인다. 로그 이벤트 하나를 표현하기에 적합하다.

```python
event = {
    "action": "DENY",
    "ip": "198.51.100.9",
    "port": 443,
    "path": "/admin",
}

print(event["ip"])
event["user"] = "bob"
event["action"] = "REVIEW"
```

없는 키를 대괄호로 조회하면 `KeyError`가 발생한다. 값이 없을 수 있다면 `get()`을 사용한다.

```python
country = event.get("country")                # None
severity = event.get("severity", "UNKNOWN")  # 기본값

for key, value in event.items():
    print(key, value)
```

## 9. 가장 중요한 조합: 리스트 안의 딕셔너리

실무에서는 이벤트 하나를 딕셔너리로, 이벤트 여러 개를 리스트로 표현한다.

```python
events = [
    {"action": "ALLOW", "ip": "10.0.0.5", "port": 80},
    {"action": "DENY", "ip": "198.51.100.9", "port": 443},
    {"action": "DENY", "ip": "198.51.100.9", "port": 443},
]

for event in events:
    if event["action"] == "DENY":
        print("검토 대상:", event["ip"], event["port"])
```

조건에 맞는 이벤트만 새 리스트로 만들 수 있다.

```python
denied_events = [
    event for event in events
    if event["action"] == "DENY"
]
```

## 10. 딕셔너리로 횟수 집계하기

IP별 DENY 횟수처럼 키별 값을 누적할 때 딕셔너리를 사용한다.

```python
deny_count_by_ip = {}

for event in events:
    if event["action"] != "DENY":
        continue

    ip = event["ip"]
    deny_count_by_ip[ip] = deny_count_by_ip.get(ip, 0) + 1

print(deny_count_by_ip)
# {'198.51.100.9': 2}
```

딕셔너리의 값으로 다른 딕셔너리나 리스트를 넣어 보고서를 구성할 수도 있다.

```python
report = {
    "summary": {"total": 3, "deny": 2},
    "events": events,
}
```

## 11. 변경 가능한 객체와 복사

리스트와 딕셔너리는 변경 가능하다. 단순 대입은 복사가 아니라 같은 객체에 새 이름을 붙인다.

```python
original = {"tags": ["auth"]}
alias = original

alias["tags"].append("deny")
print(original)  # {'tags': ['auth', 'deny']}
```

중첩된 값까지 분리하려면 `deepcopy()`를 사용한다.

```python
from copy import deepcopy

copied = deepcopy(original)
copied["tags"].append("critical")

print(original)
print(copied)
```

## 12. 자료구조 선택 기준

1. 값 하나인가? → 기본 자료형 또는 문자열
2. 여러 값을 순서대로 처리하는가? → `list`
3. 변경되면 안 되는 값의 묶음인가? → `tuple`
4. 중복 제거나 포함 확인이 중요한가? → `set`
5. 각 값에 이름표가 필요한가? → `dict`
6. 이름표가 있는 이벤트가 여러 개인가? → `list[dict]`

{% hint style="success" %}
## 🧪 단계별 실습

다음 로그를 사용한다.

```text
ALLOW 10.0.0.5 80 /index
DENY 198.51.100.9 443 /admin
DENY 198.51.100.9 443 /login
```

1. 각 줄을 `split()`으로 분리한다.
2. 포트 문자열을 `int`로 변환한다.
3. 이벤트 하나를 `dict`로 만든다.
4. 모든 이벤트를 `list`에 추가한다.
5. 관측된 IP를 `set`으로 중복 제거한다.
6. IP별 DENY 횟수를 `dict`로 집계한다.
7. DENY 이벤트만 새 리스트로 만든다.
{% endhint %}

## 핵심 정리

- 따옴표 안의 `"443"`은 문자열이고 `443`은 정수다.
- 리스트는 여러 값을 순서대로 처리할 때 사용한다.
- 튜플은 변경하지 않을 묶음, 세트는 고유값과 포함 확인에 적합하다.
- 딕셔너리는 한 대상을 이름이 붙은 속성으로 표현한다.
- 로그 분석에서는 `list[dict]`가 가장 자주 쓰이는 기본 구조다.
- 데이터의 모양뿐 아니라 앞으로 할 작업을 기준으로 자료구조를 선택한다.
