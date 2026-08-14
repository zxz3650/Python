# 03-2. 문자열과 자료구조

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
