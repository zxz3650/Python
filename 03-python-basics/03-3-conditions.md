# 03-3. 조건문과 논리

{% hint style="info" %}
### 🧭 학습 목표

- `if`, `elif`, `else`를 사용한다.
- `None`, 빈 문자열, `0`의 truthy/falsey 특성을 이해한다.
- 여러 조건을 조합해 탐지 기준을 만든다.
{% endhint %}

```python
action = "DENY"
path = "/admin"
failed_count = 4

if action == "DENY" and path in {"/admin", "/login"}:
    if failed_count >= 5:
        level = "CRITICAL"
    elif failed_count >= 3:
        level = "WARNING"
    else:
        level = "NORMAL"
else:
    level = "NORMAL"

print(level)
```

## truthy와 falsey

다음 값은 조건식에서 거짓으로 평가된다.

```python
None
False
0
""
[]
{}
set()
```

단, “값이 없음”과 “정상적인 0”은 업무 의미가 다를 수 있으므로 명시적으로 비교해야 한다.

```python
count = 0
if count is None:
    print("미집계")
elif count == 0:
    print("실패 없음")
```

{% hint style="success" %}
## 🧪 실습

- 허용 목록에 없는 action을 오류로 처리한다.
- 실패 횟수에 따라 NORMAL/WARNING/CRITICAL을 분류한다.
- 누락된 IP와 유효한 IP를 구분한다.
{% endhint %}
