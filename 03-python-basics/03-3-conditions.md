# 03-3. 조건문과 논리

조건문은 데이터에 따라 프로그램의 다음 행동을 선택한다. 보안 자동화에서는 입력이 유효한지, 이벤트가 정상인지 의심스러운지, 허용할지 검토할지를 명시적인 규칙으로 표현한다.

조건문을 잘 작성한다는 것은 단순히 `if` 문법을 아는 것이 아니다. **판단 기준을 bool 식으로 분리하고, 경계값을 포함해 검증하며, 읽는 사람이 같은 결론을 내릴 수 있게 만드는 것**이 핵심이다.

{% hint style="info" %}
### 🧭 학습 목표

- 조건식과 `bool` 결과의 관계를 설명한다.
- `if`, `elif`, `else`의 실행 순서와 독립된 `if`의 차이를 설명한다.
- 비교·연쇄 비교·멤버십·동일성 연산자를 구분한다.
- `and`, `or`, `not`의 진리표와 우선순위를 적용한다.
- 단락 평가와 논리 연산자의 반환값을 안전하게 사용한다.
- truthy/falsey와 명시적 업무 상태 비교를 구분한다.
- 드모르간 법칙과 `any()`, `all()`로 복합 조건을 설명한다.
- 경계값과 결정표를 이용해 조건 로직을 검증한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | `if`·`elif`·`else`, 비교·멤버십 연산자, `and`·`or`·`not` |
| 권장 | 연쇄 비교, 단락 평가, truthy/falsey, 경계값 검증 |
| 심화 | 피연산자를 반환하는 논리 연산, 드모르간 법칙, `any()`·`all()`, 결정표 |

## 학습 범위와 연결

- `bool`, `None`, 숫자·문자열 구분은 [03-1](03-1-data-types.md)에서 학습했다.
- 문자열 검색, `set` 멤버십, 딕셔너리 조회는 [03-2](03-2-strings-collections.md)에서 학습했다.
- 이 절에서는 한 이벤트에 대한 판단을 작성한다.
- 여러 이벤트에 같은 조건을 반복 적용하는 방법은 [03-4 반복문](03-4-loops.md)에서 다룬다.
- 판단 코드를 재사용 가능한 함수로 만드는 방법은 03-5에서 다룬다.

전용 실습은 [`notebooks/03-3-conditions-logic.ipynb`](../notebooks/03-3-conditions-logic.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

실행 전에 각 결과를 예상한다.

```python
print(3 >= 3)
print("DENY" in {"ALLOW", "DENY"})
print(True and False)
print(True or False)
print(not True)
print("" or "UNKNOWN")
```

다음 질문에 답해 본다.

1. 여러 `if`와 `if`·`elif`는 같은 방식으로 실행되는가?
2. `A and B or C`에서 어떤 연산이 먼저 수행되는가?
3. `value is target`과 `value == target`은 같은 비교인가?
4. `and`와 `or`의 결과는 언제나 정확히 `True` 또는 `False`인가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. 조건식과 bool

조건식은 판단 결과를 나타내는 식이다. 비교식과 멤버십 검사의 결과는 `bool`이다.

```python
port = 443
action = "DENY"

is_https = port == 443
is_known_action = action in {"ALLOW", "DENY"}

print(is_https, type(is_https))
print(is_known_action, type(is_known_action))
```

조건을 의미 있는 bool 변수로 분리하면 판단 기준을 설명하고 시험하기 쉽다.

```python
failed_count = 4
path = "/admin"

has_repeated_failures = failed_count >= 3
is_sensitive_path = path in {"/admin", "/login"}

print(has_repeated_failures)  # True
print(is_sensitive_path)      # True
```

`if`는 조건식이 truthy인지 확인하지만, 정책 판단 변수에는 가능하면 의미가 분명한 비교식을 저장한다.

## 2. if와 들여쓰기

`if`의 조건이 참이면 들여쓰기 된 코드 블록을 실행한다.

```python
failed_count = 4

if failed_count >= 3:
    print("검토 필요")

print("분석 종료")
```

출력:

```text
검토 필요
분석 종료
```

콜론과 들여쓰기는 선택 사항이 아니다. 같은 깊이로 들여쓴 문장이 하나의 블록을 이룬다.

```python
is_detected = True

if is_detected:
    print("탐지 이벤트")
    print("분석 큐에 추가")

print("처리 완료")
```

조건이 거짓이면 해당 블록만 건너뛰고 그다음 문장을 계속 실행한다.

## 3. if와 else: 두 갈래

두 결과 중 하나만 선택할 때 `if`와 `else`를 사용한다.

```python
is_open = True

if is_open:
    status = "OPEN"
else:
    status = "CLOSED"

print(status)
```

`else`에는 조건을 쓰지 않는다. 앞의 `if` 조건이 거짓인 나머지 모든 경우를 담당한다.

```python
port = 70000

if 1 <= port <= 65535:
    print("유효한 포트")
else:
    print("포트 범위 오류")
```

## 4. if·elif·else: 여러 갈래 중 하나

`elif`는 위에서부터 조건을 검사하고 **처음 참이 된 블록 하나만** 실행한다.

```python
failed_count = 4

if failed_count >= 5:
    level = "CRITICAL"
elif failed_count >= 3:
    level = "WARNING"
else:
    level = "NORMAL"

print(level)  # WARNING
```

조건 범위가 겹치면 더 구체적이거나 더 높은 기준을 먼저 검사한다.

```python
# 잘못된 순서
failed_count = 7

if failed_count >= 3:
    level = "WARNING"
elif failed_count >= 5:
    level = "CRITICAL"  # 실행될 수 없음

print(level)  # WARNING
```

`failed_count >= 3`이 `>= 5`인 값까지 먼저 가져가기 때문이다.

## 5. 독립된 if와 elif의 차이

여러 `if`는 각각 독립적으로 검사하므로 두 개 이상의 블록이 실행될 수 있다.

```python
failed_count = 7

if failed_count >= 3:
    print("경고 조건 충족")

if failed_count >= 5:
    print("심각 조건 충족")
```

출력:

```text
경고 조건 충족
심각 조건 충족
```

반면 `if`·`elif`는 상호 배타적인 분류에서 하나만 선택한다.

```python
failed_count = 7

if failed_count >= 5:
    print("CRITICAL")
elif failed_count >= 3:
    print("WARNING")
else:
    print("NORMAL")
```

선택 기준:

- 여러 규칙이 동시에 성립할 수 있고 각각 처리해야 한다 → 독립된 `if`
- 하나의 등급이나 상태만 선택해야 한다 → `if`·`elif`·`else`

## 6. 비교 연산자와 자료형

| 연산자 | 의미 | 예 |
|---|---|---|
| `==` | 값이 같음 | `port == 443` |
| `!=` | 값이 다름 | `action != "ALLOW"` |
| `<` | 왼쪽이 작음 | `port < 1024` |
| `<=` | 왼쪽이 작거나 같음 | `score <= 1.0` |
| `>` | 왼쪽이 큼 | `failed_count > 3` |
| `>=` | 왼쪽이 크거나 같음 | `failed_count >= 3` |

```python
port = 443

print(port == 443)  # True
print(port != 80)   # True
print(port < 1024)  # True
print(port >= 1)    # True
```

같음을 비교할 때 자료형도 영향을 준다.

```python
print(443 == "443")  # False

# print(443 < "1024")
# TypeError: 정수와 문자열의 크기를 직접 비교할 수 없음
```

외부 문자열은 03-1에서 배운 방법으로 변환한 뒤 수치 범위를 비교한다.

## 7. 연쇄 비교와 경계값

Python은 하나의 값을 여러 경계와 자연스럽게 비교할 수 있다.

```python
port = 443

print(1 <= port <= 65535)  # True
```

이는 다음 논리와 같은 의미다.

```python
print(port >= 1 and port <= 65535)  # True
```

경계값은 조건식의 포함 여부를 검증하는 가장 중요한 입력이다.

| 포트 | `1 <= port <= 65535` | 의미 |
|---:|---:|---|
| `0` | `False` | 최솟값 바로 아래 |
| `1` | `True` | 유효한 최솟값 |
| `65535` | `True` | 유효한 최댓값 |
| `65536` | `False` | 최댓값 바로 위 |

`<`와 `<=`의 차이는 정상값 하나만 시험해서는 발견하기 어렵다. 항상 경계값과 경계 바로 밖의 값을 함께 시험한다.

## 8. 멤버십 연산자: in과 not in

`in`은 값이 컨테이너에 포함되는지, `not in`은 포함되지 않는지 검사한다.

```python
action = "DENY"
allowed_actions = {"ALLOW", "DENY"}

print(action in allowed_actions)      # True
print(action not in allowed_actions)  # False
```

문자열에서는 부분 문자열을 검사한다.

```python
path = "/admin/login"

print("/admin" in path)  # True
```

딕셔너리에서 `in`은 기본적으로 키를 검사한다.

```python
event = {"action": "DENY", "port": 443}

print("action" in event)  # True
print("DENY" in event)    # False
print("DENY" in event.values())  # True
```

여러 값 중 하나와 같은지 확인할 때 연속된 `or`보다 멤버십이 명확하다.

```python
action = "BLOCK"

print(action in {"DENY", "BLOCK", "DROP"})
```

## 9. 값 비교 ==와 동일성 비교 is

`==`는 두 값이 같은지 비교하고, `is`는 두 이름이 **같은 객체**를 가리키는지 확인한다.

```python
a = ["DENY"]
b = ["DENY"]

print(a == b)  # True: 내용이 같음
print(a is b)  # False: 서로 다른 리스트 객체
```

업무 데이터의 문자열·숫자·리스트 내용은 `==`로 비교한다.

```python
action = "DENY"

print(action == "DENY")
# print(action is "DENY")  # 사용하지 않음
```

`None`은 하나뿐인 특별한 객체이므로 `is None`과 `is not None`으로 확인한다.

```python
country = None

print(country is None)      # True
print(country is not None)  # False
```

{% hint style="warning" %}
작은 정수나 일부 문자열에서 `is` 비교가 우연히 `True`처럼 보일 수 있다. 이는 구현상의 객체 재사용 결과일 수 있으며 값 비교 규칙이 아니다. `None` 확인 이외의 일반적인 값 비교에는 `==`를 사용한다.
{% endhint %}

## 10. 논리 연산자 and, or, not

논리 연산자는 여러 조건을 하나의 판단으로 결합한다.

| `A` | `B` | `A and B` | `A or B` |
|---:|---:|---:|---:|
| `False` | `False` | `False` | `False` |
| `False` | `True` | `False` | `True` |
| `True` | `False` | `False` | `True` |
| `True` | `True` | `True` | `True` |

`not`은 조건의 참·거짓을 반대로 바꾼다.

| `A` | `not A` |
|---:|---:|
| `False` | `True` |
| `True` | `False` |

### and: 모든 조건이 필요

```python
action = "DENY"
path = "/admin"
failed_count = 4

is_critical = (
    action == "DENY"
    and path in {"/admin", "/login"}
    and failed_count >= 3
)

print(is_critical)  # True
```

### or: 하나 이상의 조건이 필요

```python
action = "BLOCK"

needs_review = action == "DENY" or action == "BLOCK"
print(needs_review)  # True
```

여러 값과 비교하는 목적이라면 다음 표현이 더 명확하다.

```python
needs_review = action in {"DENY", "BLOCK"}
```

### not: 조건을 반대로

```python
action = "UNKNOWN"
allowed_actions = {"ALLOW", "DENY"}

is_invalid_action = action not in allowed_actions
print(is_invalid_action)  # True
```

`not action in allowed_actions`도 실행되지만 `action not in allowed_actions`가 의도를 더 직접 표현한다.

## 11. 논리 연산 우선순위

조건식에서 중요한 우선순위는 다음과 같다.

```text
비교·멤버십·동일성  →  not  →  and  →  or
```

따라서 다음 식은 `and`를 먼저 계산한다.

```python
A = True
B = False
C = False

result = A or B and C
print(result)  # True
```

위 식은 다음과 같다.

```python
result = A or (B and C)
```

의도한 판단이 `(A or B) and C`라면 괄호가 반드시 필요하다.

```python
print((A or B) and C)  # False
```

복합 조건은 우선순위를 암기해 한 줄로 압축하기보다 괄호와 의미 있는 bool 변수로 분리한다.

```python
is_block_action = action in {"DENY", "BLOCK"}
is_sensitive_path = path in {"/admin", "/login"}
has_repeated_failures = failed_count >= 3

is_critical = (
    is_block_action
    and is_sensitive_path
    and has_repeated_failures
)
```

## 12. 단락 평가

Python은 결과가 이미 결정되면 뒤 조건을 평가하지 않는다.

- `A and B`: `A`가 falsey이면 `B`를 평가하지 않는다.
- `A or B`: `A`가 truthy이면 `B`를 평가하지 않는다.

```python
user = None

is_admin = user is not None and user.startswith("admin")
print(is_admin)  # False
```

첫 조건이 거짓이므로 `None.startswith()`를 실행하지 않는다.

순서가 반대면 오류가 발생한다.

```python
user = None

# is_admin = user.startswith("admin") and user is not None
# AttributeError: None에는 startswith 메서드가 없음
```

안전성 검사와 비용이 낮은 조건을 앞에 두고, 그 조건이 만족될 때만 실행할 검사를 뒤에 둔다.

```python
parts = ["DENY", "198.51.100.9"]

has_port = len(parts) >= 3 and parts[2].isdigit()
print(has_port)  # False, parts[2]는 조회하지 않음
```

## 13. and와 or는 피연산자를 반환한다

`and`와 `or`는 항상 정확히 `True` 또는 `False`를 반환하는 것이 아니다.

- `A and B`: 첫 번째 falsey 값 또는 마지막 값을 반환한다.
- `A or B`: 첫 번째 truthy 값 또는 마지막 값을 반환한다.

```python
print("" or "UNKNOWN")       # UNKNOWN
print(None or "UNKNOWN")     # UNKNOWN
print("DENY" or "UNKNOWN")   # DENY

print("DENY" and 443)        # 443
print("" and 443)            # 빈 문자열
```

기본값 선택에는 `or`가 간결하지만, `0`, `""`, `False`가 정상 입력일 수 있다면 주의한다.

```python
configured_timeout = 0
timeout = configured_timeout or 30

print(timeout)  # 30: 유효한 0이 기본값으로 바뀜
```

`None`만 “설정되지 않음”을 의미한다면 명시적으로 비교한다.

```python
configured_timeout = 0

if configured_timeout is None:
    timeout = 30
else:
    timeout = configured_timeout

print(timeout)  # 0
```

정책 판단 결과를 반드시 bool로 제한하려면 비교식 또는 `bool()`을 사용한다.

## 14. truthy와 falsey

조건문은 `bool` 이외의 값도 참·거짓으로 해석한다.

대표적인 falsey 값:

```python
None
False
0
0.0
""
[]
{}
set()
```

그 밖의 대부분 값은 truthy다.

```python
records = []

if not records:
    print("처리할 레코드가 없습니다")
```

단순히 비어 있는지만 확인한다면 이 표현이 적합하다. 하지만 업무 의미가 다르면 명시적으로 비교한다.

```python
count = 0

if count is None:
    print("아직 집계하지 않음")
elif count == 0:
    print("집계 완료, 결과 0건")
else:
    print("한 건 이상")
```

`None`, `0`, 빈 문자열을 모두 `if not value`로 묶으면 서로 다른 상태를 구분할 수 없다.

## 15. 드모르간 법칙과 부정 조건

복합 조건을 부정할 때는 각 조건과 연산자가 함께 바뀐다.

```text
not (A and B)  ==  (not A) or (not B)
not (A or B)   ==  (not A) and (not B)
```

예를 들어 action이 허용 목록에 있고 포트도 유효해야 전체 입력이 유효하다고 하자.

```python
action = "UNKNOWN"
port = 443

is_known_action = action in {"ALLOW", "DENY"}
is_valid_port = 1 <= port <= 65535

is_valid = is_known_action and is_valid_port
is_invalid = not is_known_action or not is_valid_port

print(is_valid)    # False
print(is_invalid)  # True
```

다음처럼 전체 식을 부정해도 같은 결과다.

```python
is_invalid = not (is_known_action and is_valid_port)
```

부정이 여러 번 겹치면 읽기 어려워진다. `is_not_invalid`보다 `is_valid`처럼 긍정형 이름을 우선한다.

## 16. any와 all

`any()`는 하나 이상 truthy이면 `True`, `all()`은 모든 값이 truthy이면 `True`를 반환한다.

```python
signals = [True, False, True]

print(any(signals))  # True
print(all(signals))  # False
```

여러 검증 결과를 결합할 때 유용하다.

```python
is_known_action = True
is_valid_port = True
has_valid_path = False

validation_results = [
    is_known_action,
    is_valid_port,
    has_valid_path,
]

print(all(validation_results))  # False
print(any(validation_results))  # True
```

빈 컨테이너의 결과도 알아 둔다.

```python
print(any([]))  # False
print(all([]))  # True
```

`all([])`이 `True`인 이유는 “거짓인 항목이 하나도 없다”는 논리 규칙 때문이다. 필수 검증 목록이 비어 있으면 별도 오류로 처리해야 하는 업무도 있으므로 맥락을 확인한다.

## 17. 중첩 조건과 복합 조건

조건 안에 다른 조건을 넣을 수 있다.

```python
action = "DENY"
failed_count = 4

if action == "DENY":
    if failed_count >= 3:
        print("반복 차단 이벤트")
```

두 조건을 항상 함께 확인한다면 `and`로 표현하는 편이 간결하다.

```python
if action == "DENY" and failed_count >= 3:
    print("반복 차단 이벤트")
```

중첩은 단계별로 다른 처리가 필요할 때 사용한다.

```python
if action == "DENY":
    print("차단 이벤트")

    if failed_count >= 3:
        print("반복 발생")
```

중첩 깊이가 계속 늘어나면 판단 변수를 분리하거나 03-5에서 함수로 나눈다.

## 18. 조건 표현식

두 값 중 하나를 선택하는 짧고 단순한 경우 조건 표현식을 사용할 수 있다.

```python
is_open = True
status = "OPEN" if is_open else "CLOSED"

print(status)
```

다음과 같은 의미다.

```python
if is_open:
    status = "OPEN"
else:
    status = "CLOSED"
```

조건이 복잡하거나 여러 작업을 수행한다면 일반 `if` 문을 사용한다. 한 줄로 줄이는 것이 항상 더 읽기 좋은 것은 아니다.

## 19. 결정표로 조건 설계하기

복합 조건을 코드로 작성하기 전에 입력 조합과 예상 결과를 표로 정리하면 빠진 경우와 우선순위를 찾기 쉽다.

예시 정책:

- action 또는 port 형식이 잘못되면 `INVALID`
- DENY이고 민감 경로이며 실패 횟수가 3 이상이면 `CRITICAL`
- DENY이거나 민감 경로면 `REVIEW`
- 나머지는 `NORMAL`

| 유효 입력 | DENY | 민감 경로 | 실패 3회 이상 | 결과 |
|---:|---:|---:|---:|---|
| 아니요 | 상관없음 | 상관없음 | 상관없음 | `INVALID` |
| 예 | 예 | 예 | 예 | `CRITICAL` |
| 예 | 예 | 아니요 | 상관없음 | `REVIEW` |
| 예 | 아니요 | 예 | 상관없음 | `REVIEW` |
| 예 | 아니요 | 아니요 | 상관없음 | `NORMAL` |

코드에서는 더 높은 우선순위를 먼저 배치한다.

```python
action = "DENY"
port = 443
path = "/admin"
failed_count = 4

is_known_action = action in {"ALLOW", "DENY"}
is_valid_port = 1 <= port <= 65535
is_valid_input = is_known_action and is_valid_port

is_deny = action == "DENY"
is_sensitive_path = path in {"/admin", "/login"}
has_repeated_failures = failed_count >= 3

if not is_valid_input:
    level = "INVALID"
elif is_deny and is_sensitive_path and has_repeated_failures:
    level = "CRITICAL"
elif is_deny or is_sensitive_path:
    level = "REVIEW"
else:
    level = "NORMAL"

print(level)  # CRITICAL
```

유효성 검증과 위험 분류를 별도 bool 변수로 분리하면 정책을 검토하고 시험하기 쉽다.

## 20. 안전한 기본값과 판단 순서

정책 코드에서는 모든 입력 조합이 어떤 결과로 이어지는지 확인한다. 판단되지 않은 상태를 무조건 허용으로 처리하지 않는다.

```python
action = "UNKNOWN"

if action == "ALLOW":
    decision = "ALLOW"
elif action == "DENY":
    decision = "DENY"
else:
    decision = "REVIEW"
```

이는 모든 알 수 없는 값을 공격으로 단정한다는 뜻이 아니다. **확인되지 않은 상태를 정상으로 오분류하지 않고 별도 검토 상태로 보존한다**는 뜻이다.

판단 순서를 다음처럼 분리한다.

1. 값이 필요한 형식과 범위를 만족하는가?
2. 분류 규칙에 필요한 정보가 모두 있는가?
3. 높은 우선순위 규칙부터 평가하는가?
4. 어떤 규칙에도 맞지 않는 경우의 결과가 명확한가?

## 21. 자주 발생하는 오류

### 대입과 비교 혼동

```python
action = "DENY"

# if action = "DENY":
# SyntaxError: 비교에는 == 사용
```

### 여러 값 비교에서 or를 잘못 사용

```python
action = "ALLOW"

# if action == "DENY" or "BLOCK":
#     print("항상 실행되는 것처럼 보임")

if action in {"DENY", "BLOCK"}:
    print("차단 계열")
```

`"BLOCK"` 자체가 비어 있지 않은 truthy 문자열이기 때문이다.

### 값 비교에 is 사용

```python
action = "DENY"

# if action is "DENY":
#     ...

if action == "DENY":
    print("차단")
```

### 넓은 elif 조건을 먼저 배치

```python
score = 95

# if score >= 60:
#     grade = "PASS"
# elif score >= 90:
#     grade = "EXCELLENT"

if score >= 90:
    grade = "EXCELLENT"
elif score >= 60:
    grade = "PASS"
else:
    grade = "FAIL"
```

### and와 or를 괄호 없이 혼합

```python
is_admin = True
is_internal = False
is_approved = False

unclear = is_admin or is_internal and is_approved
clear = is_admin or (is_internal and is_approved)
```

두 식은 같은 결과지만 두 번째가 평가 순서를 드러낸다. 의도가 `(is_admin or is_internal) and is_approved`라면 결과가 달라진다.

### falsey 정상값을 기본값으로 덮어쓰기

```python
configured_retry = 0

wrong_retry = configured_retry or 3
correct_retry = 3 if configured_retry is None else configured_retry

print(wrong_retry)    # 3
print(correct_retry)  # 0
```

### 경계값을 시험하지 않음

```python
port = 65535
print(1 <= port <= 65535)  # True

port = 65536
print(1 <= port <= 65535)  # False
```

## 22. 단계별 연습문제

### 연습 1. 진리표 완성

다음 표의 빈칸을 채운다.

| `A` | `B` | `A and B` | `A or B` | `not A` |
|---:|---:|---:|---:|---:|
| `False` | `False` | ? | ? | ? |
| `False` | `True` | ? | ? | ? |
| `True` | `False` | ? | ? | ? |
| `True` | `True` | ? | ? | ? |

### 연습 2. 출력 결과 예측

```python
print(True or False and False)
print((True or False) and False)
print("" or "UNKNOWN")
print("DENY" and 443)
print(not (True and False))
print(any([False, False, True]))
print(all([True, True, False]))
print(all([]))
```

### 연습 3. 오류 수정

```python
# 문제 A: DENY 또는 BLOCK일 때만 True
action = "ALLOW"
is_blocked = action == "DENY" or "BLOCK"

# 문제 B: 문자열 값 비교
action = "DENY"
is_deny = action is "DENY"

# 문제 C: 90 이상 EXCELLENT, 60 이상 PASS
score = 95
if score >= 60:
    grade = "PASS"
elif score >= 90:
    grade = "EXCELLENT"
else:
    grade = "FAIL"

# 문제 D: 설정값 0을 보존
configured_retry = 0
retry = configured_retry or 3
```

### 연습 4. 경계값 검증

포트 조건 `1 <= port <= 65535`에 대해 다음 입력의 예상 결과를 기록하고 실행한다.

```text
-1, 0, 1, 2, 65534, 65535, 65536
```

실패 횟수 등급에도 경계값을 적용한다.

```text
0, 2, 3, 4, 5, 6
```

기준:

- 5 이상: `CRITICAL`
- 3 이상: `WARNING`
- 나머지: `NORMAL`

### 연습 5. 결정표 해석

19절의 결정표를 보고 다음 입력의 결과를 예측한다.

| action | port | path | failed_count | 예상 결과 |
|---|---:|---|---:|---|
| `ALLOW` | `80` | `/index` | `0` | ? |
| `DENY` | `443` | `/admin` | `4` | ? |
| `DENY` | `443` | `/public` | `1` | ? |
| `ALLOW` | `443` | `/admin` | `1` | ? |
| `UNKNOWN` | `443` | `/admin` | `4` | ? |
| `DENY` | `70000` | `/admin` | `4` | ? |

### 연습 6. 미니 실습 — 단일 이벤트 분류

다음 이벤트를 결정표에 따라 분류한다.

```python
event = {
    "action": "DENY",
    "port": 443,
    "path": "/admin",
    "failed_count": 4,
    "country": None,
}
```

요구사항:

1. action, port, path, failed_count를 의미 있는 변수로 꺼낸다.
2. `is_known_action`, `is_valid_port`, `is_valid_input`을 만든다.
3. `is_deny`, `is_sensitive_path`, `has_repeated_failures`를 만든다.
4. `if`·`elif`·`else`로 `INVALID`, `CRITICAL`, `REVIEW`, `NORMAL` 중 하나를 선택한다.
5. `country is None`을 사용해 국가 정보 미확인 여부를 별도 bool로 저장한다.
6. 다음 자기점검을 통과한다.

```python
assert is_known_action is True
assert is_valid_port is True
assert is_valid_input is True
assert is_deny is True
assert is_sensitive_path is True
assert has_repeated_failures is True
assert is_country_unknown is True
assert level == "CRITICAL"

print("모든 자기점검을 통과했습니다.")
```

### 연습 7. 확장 과제

- 미니 실습의 이벤트 값을 연습 5의 여섯 입력으로 바꾸며 결과를 확인한다.
- 03-4를 학습한 뒤 이벤트 리스트 전체를 반복 분류한다.
- 03-5를 학습한 뒤 분류 로직을 `classify_event(event)` 함수로 만든다.
- 예상 결과와 실제 결과가 다를 때 어떤 bool 조건에서 달라졌는지 출력한다.

### 연습 8. 전이 연습 — 주문 배송 결정

다음 규칙을 결정표로 먼저 작성하고 조건문으로 구현한다.

- 수량이 1보다 작거나 재고보다 많으면 `INVALID`
- 결제하지 않았으면 `PAYMENT_REQUIRED`
- 결제했고 총액이 50,000 이상이면 `FREE_SHIPPING`
- 그 외에는 `STANDARD_SHIPPING`

`quantity`, `stock`, `is_paid`, `total_price`를 입력으로 사용한다. 수량 경계 `0`, `1`, `stock`, `stock + 1`과 총액 경계 `49_999`, `50_000`을 확인한다.

## 23. 정답과 해설

<details>
<summary>연습 1 진리표 정답</summary>

| `A` | `B` | `A and B` | `A or B` | `not A` |
|---:|---:|---:|---:|---:|
| `False` | `False` | `False` | `False` | `True` |
| `False` | `True` | `False` | `True` | `True` |
| `True` | `False` | `False` | `True` | `False` |
| `True` | `True` | `True` | `True` | `False` |

</details>

<details>
<summary>연습 2 출력 정답</summary>

```text
True
False
UNKNOWN
443
True
True
False
True
```

첫 식은 `and`가 `or`보다 먼저 평가된다. `or`와 `and`는 bool이 아닌 피연산자를 반환할 수도 있다. 빈 리스트에 대한 `all([])`은 `True`다.

</details>

<details>
<summary>연습 3 수정 예시</summary>

```python
# 문제 A
action = "ALLOW"
is_blocked = action in {"DENY", "BLOCK"}

# 문제 B
action = "DENY"
is_deny = action == "DENY"

# 문제 C
score = 95
if score >= 90:
    grade = "EXCELLENT"
elif score >= 60:
    grade = "PASS"
else:
    grade = "FAIL"

# 문제 D
configured_retry = 0
retry = 3 if configured_retry is None else configured_retry
```

</details>

<details>
<summary>연습 4·5 정답</summary>

포트:

| 값 | 결과 |
|---:|---:|
| `-1` | `False` |
| `0` | `False` |
| `1` | `True` |
| `2` | `True` |
| `65534` | `True` |
| `65535` | `True` |
| `65536` | `False` |

실패 횟수:

| 값 | 등급 |
|---:|---|
| `0` | `NORMAL` |
| `2` | `NORMAL` |
| `3` | `WARNING` |
| `4` | `WARNING` |
| `5` | `CRITICAL` |
| `6` | `CRITICAL` |

결정표:

| action | port | path | failed_count | 결과 |
|---|---:|---|---:|---|
| `ALLOW` | `80` | `/index` | `0` | `NORMAL` |
| `DENY` | `443` | `/admin` | `4` | `CRITICAL` |
| `DENY` | `443` | `/public` | `1` | `REVIEW` |
| `ALLOW` | `443` | `/admin` | `1` | `REVIEW` |
| `UNKNOWN` | `443` | `/admin` | `4` | `INVALID` |
| `DENY` | `70000` | `/admin` | `4` | `INVALID` |

</details>

<details>
<summary>미니 실습 예시 답안</summary>

```python
event = {
    "action": "DENY",
    "port": 443,
    "path": "/admin",
    "failed_count": 4,
    "country": None,
}

action = event["action"]
port = event["port"]
path = event["path"]
failed_count = event["failed_count"]

is_known_action = action in {"ALLOW", "DENY"}
is_valid_port = 1 <= port <= 65535
is_valid_input = is_known_action and is_valid_port

is_deny = action == "DENY"
is_sensitive_path = path in {"/admin", "/login"}
has_repeated_failures = failed_count >= 3
is_country_unknown = event.get("country") is None

if not is_valid_input:
    level = "INVALID"
elif is_deny and is_sensitive_path and has_repeated_failures:
    level = "CRITICAL"
elif is_deny or is_sensitive_path:
    level = "REVIEW"
else:
    level = "NORMAL"

print(level)
```

</details>

<details>
<summary>연습 8 전이 연습 예시 답안</summary>

```python
quantity = 2
stock = 5
is_paid = True
total_price = 50_000

is_valid_quantity = 1 <= quantity <= stock

if not is_valid_quantity:
    shipping_status = "INVALID"
elif not is_paid:
    shipping_status = "PAYMENT_REQUIRED"
elif total_price >= 50_000:
    shipping_status = "FREE_SHIPPING"
else:
    shipping_status = "STANDARD_SHIPPING"

assert shipping_status == "FREE_SHIPPING"
```

분기 순서는 유효성, 결제 상태, 무료 배송 기준 순서다. 총액부터 검사하면 결제하지 않은 주문을 무료 배송으로 잘못 분류할 수 있다.

</details>

## 완료 기준

- [ ] `if`, `elif`, `else`의 실행 순서를 설명할 수 있다.
- [ ] 독립된 여러 `if`와 `if`·`elif`의 결과 차이를 설명할 수 있다.
- [ ] 비교·연쇄 비교·멤버십·동일성 연산자를 구분할 수 있다.
- [ ] `and`, `or`, `not`의 진리표를 완성할 수 있다.
- [ ] 비교 → `not` → `and` → `or` 우선순위를 적용할 수 있다.
- [ ] 단락 평가로 오류를 피하는 조건 순서를 설명할 수 있다.
- [ ] `and`와 `or`가 피연산자를 반환할 수 있음을 설명할 수 있다.
- [ ] truthy/falsey와 `None`, `0`, 빈 값의 업무 의미를 구분할 수 있다.
- [ ] 드모르간 법칙과 `any()`, `all()`을 사용할 수 있다.
- [ ] 경계값과 결정표로 분기 로직을 검증할 수 있다.
- [ ] 미니 실습의 모든 `assert`를 통과했다.
- [ ] 주문 배송 전이 연습의 분기 순서와 경계값을 검증했다.

## 핵심 정리

- 조건문은 데이터를 판단 규칙에 따라 분류하고 다음 행동을 선택한다.
- `if`·`elif`는 처음 참인 하나만 실행하고, 독립된 `if`는 각각 실행될 수 있다.
- 값 비교는 `==`, `None` 동일성 확인은 `is None`을 사용한다.
- `and`는 모두 참, `or`는 하나 이상 참, `not`은 판단을 반대로 만든다.
- 논리 우선순위는 비교 → `not` → `and` → `or`이며 복합 조건에는 괄호를 사용한다.
- 단락 평가는 뒤 조건의 실행 여부를 결정한다.
- `and`와 `or`는 bool이 아닌 피연산자를 반환할 수 있다.
- truthy/falsey가 같은 값도 업무 의미는 다를 수 있으므로 필요한 경우 명시적으로 비교한다.
- 경계값과 결정표는 누락된 분기와 잘못된 우선순위를 찾는 도구다.
- 유효성 검증과 위험 분류를 분리하고, 알 수 없는 상태의 처리 방식을 명시한다.

---

이전 절: [03-2. 문자열과 자료구조](03-2-strings-collections.md)  
다음 절: [03-4. 반복문](03-4-loops.md)
