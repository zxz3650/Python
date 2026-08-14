# 03-3. 조건문과 논리

조건문은 데이터에 따라 프로그램의 다음 행동을 선택한다. 보안 자동화에서는 허용·차단, 정상·의심, 유효·오류를 구분하는 판단 규칙이 된다.

{% hint style="info" %}
### 🧭 학습 목표

- 조건식과 bool의 관계를 이해한다.
- `if`, `elif`, `else`의 실행 순서를 설명한다.
- 비교·논리·멤버십·동일성 연산자를 구분한다.
- truthy/falsey와 단락 평가를 안전하게 사용한다.
{% endhint %}

## 1. 가장 단순한 if

조건식이 `True`일 때 들여쓰기 된 코드가 실행된다.

```python
failed_count = 4

if failed_count >= 3:
    print("검토 필요")

print("분석 종료")
```

콜론과 들여쓰기는 선택 사항이 아니다. 같은 깊이로 들여쓴 문장이 하나의 코드 블록을 이룬다.

## 2. 두 갈래: if와 else

```python
is_open = True

if is_open:
    status = "OPEN"
else:
    status = "CLOSED"

print(status)
```

조건이 참이면 `if`, 거짓이면 `else` 블록 하나만 실행된다.

## 3. 여러 갈래: elif

위에서부터 조건을 검사하고 처음 참이 된 블록 하나만 실행한다.

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

조건 순서를 반대로 쓰면 넓은 조건이 먼저 모든 값을 가져갈 수 있다.

## 4. 비교와 멤버십

```python
port = 443
action = "DENY"

print(port == 443)
print(port != 80)
print(1 <= port <= 65535)
print(action in {"ALLOW", "DENY"})
print(action not in {"BLOCK", "DROP"})
```

- `==`, `!=`: 값이 같은지·다른지
- `<`, `<=`, `>`, `>=`: 크기 비교
- `in`, `not in`: 컨테이너에 포함되는지
- `is`, `is not`: 같은 객체인지. 주로 `None` 확인에 사용

## 5. and, or, not

```python
action = "DENY"
path = "/admin"
failed_count = 4

is_suspicious = (
    action == "DENY"
    and path in {"/admin", "/login"}
    and failed_count >= 3
)

if is_suspicious:
    print("의심 이벤트")
```

| 연산자 | 의미 |
|---|---|
| `A and B` | 둘 다 참일 때 참 |
| `A or B` | 하나 이상 참일 때 참 |
| `not A` | 참과 거짓을 반대로 변경 |

복합 조건은 괄호와 의미 있는 변수 이름으로 분리하면 읽기 쉽다.

## 6. 단락 평가

`and`는 앞 조건이 거짓이면 뒤를 평가하지 않고, `or`는 앞 조건이 참이면 뒤를 평가하지 않는다.

```python
user = None

if user is not None and user.startswith("admin"):
    print("관리자 계정")
```

첫 조건 덕분에 `None.startswith()` 오류가 발생하지 않는다. 하지만 너무 복잡한 단락 평가에 업무 로직을 숨기지 않는다.

## 7. truthy와 falsey

조건문은 bool 이외의 값도 참·거짓으로 해석한다. 다음 값은 거짓으로 평가된다.

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

```python
records = []

if not records:
    print("분석할 레코드가 없습니다")
```

업무 의미가 다르면 명시적으로 비교한다.

```python
count = 0

if count is None:
    print("미집계")
elif count == 0:
    print("실패 없음")
```

## 8. 흔한 실수

```python
action = "DENY"

# if action = "DENY":   # SyntaxError: 비교는 ==
# if action == "DENY" or "BLOCK":  # 항상 참처럼 동작
if action in {"DENY", "BLOCK"}:
    print("차단 계열")
```

문자열 `"BLOCK"` 자체는 비어 있지 않아 truthy다. 여러 값 비교에는 `in`이 명확하다.

{% hint style="success" %}
## 🧪 실습

1. 포트가 1~65535인지 분류한다.
2. 실패 횟수를 NORMAL/WARNING/CRITICAL로 구분한다.
3. action이 허용 목록에 없는 경우 오류로 처리한다.
4. `None`, `0`, 빈 문자열을 서로 다르게 처리한다.
5. 복합 조건을 의미 있는 bool 변수 세 개로 나누어 본다.
{% endhint %}

## 핵심 정리

- 조건식은 참 또는 거짓으로 평가된다.
- `elif`에서는 처음 참인 분기 하나만 실행된다.
- 들여쓰기는 Python 문법이며 실행 범위를 결정한다.
- truthy/falsey는 편리하지만 업무 의미가 다르면 명시적으로 비교한다.
