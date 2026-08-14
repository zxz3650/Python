# 03-5. 함수와 스코프

함수는 특정 작업에 이름을 붙여 재사용하는 코드 묶음이다. 긴 프로그램을 입력·검증·분석·출력 책임으로 분리하면 이해와 테스트가 쉬워진다.

{% hint style="info" %}
### 🧭 학습 목표

- 함수 정의와 호출, 매개변수와 인자를 구분한다.
- `return`과 `print()`의 차이를 이해한다.
- 위치·키워드·기본값 인자를 사용한다.
- 지역·전역 스코프와 변경 가능한 기본값 문제를 설명한다.
{% endhint %}

## 1. 정의와 호출

```python
def greet():
    print("분석을 시작합니다")

greet()
greet()
```

`def`는 함수를 정의할 뿐 즉시 본문을 실행하지 않는다. 이름 뒤에 괄호를 붙여 호출할 때 실행된다.

## 2. 매개변수와 인자

```python
def show_port(port):       # port: 매개변수
    print("포트:", port)

show_port(443)             # 443: 인자
```

매개변수는 함수가 받을 값의 이름이고 인자는 호출할 때 전달하는 실제 값이다.

## 3. return과 print

```python
def show_action():
    print("DENY")

def get_action():
    return "DENY"

a = show_action()
b = get_action()

print(a)  # None
print(b)  # DENY
```

`print()`는 화면에 표시하고, `return`은 호출한 곳에 값을 돌려준다. `return`이 없으면 함수는 `None`을 반환한다.

## 4. 위치·키워드·기본값 인자

```python
def classify(count, threshold=3):
    if count >= threshold:
        return "WARNING"
    return "NORMAL"

print(classify(5))
print(classify(5, 4))
print(classify(count=5, threshold=4))
```

키워드 인자는 호출 의도를 분명하게 한다. 기본값은 함수가 정의될 때 한 번 평가된다.

## 5. 변경 가능한 기본값 주의

```python
# 피해야 할 형태
# def add_tag(tag, tags=[]):
#     tags.append(tag)
#     return tags

def add_tag(tag, tags=None):
    if tags is None:
        tags = []
    tags.append(tag)
    return tags
```

리스트·딕셔너리 같은 변경 가능한 객체를 기본값으로 직접 사용하면 호출 간 상태가 공유될 수 있다.

## 6. 여러 값 반환과 언패킹

```python
def count_actions(actions):
    allow = actions.count("ALLOW")
    deny = actions.count("DENY")
    return allow, deny

allow_count, deny_count = count_actions(["ALLOW", "DENY", "DENY"])
```

여러 값을 반환하면 실제로는 튜플이 반환된다.

## 7. 스코프와 이름 탐색

```python
threshold = 3

def is_suspicious(count):
    result = count >= threshold
    return result

print(is_suspicious(5))
# print(result)  # NameError: 지역 변수는 함수 밖에서 사용 불가
```

Python은 지역(Local) → 바깥 함수(Enclosing) → 전역(Global) → 내장(Built-in) 순서로 이름을 찾는다. 전역 상태를 함수 안에서 변경하기보다 필요한 값을 인자로 전달하고 결과를 반환한다.

## 8. 객체 전달과 부수효과

```python
def add_event(events, event):
    events.append(event)

records = []
add_event(records, {"action": "DENY"})
print(records)
```

리스트가 변경 가능한 객체이므로 호출한 쪽에서도 변경을 볼 수 있다. 함수가 입력을 변경하는지 문서화하거나 새 값을 반환하는 방식으로 의도를 분명히 한다.

## 9. docstring과 타입 힌트

```python
def classify(count: int, threshold: int = 3) -> str:
    """실패 횟수를 위험 수준으로 분류한다."""
    if count >= threshold:
        return "WARNING"
    return "NORMAL"
```

타입 힌트는 가독성과 도구 지원을 높이지만 실행 시 자료형을 자동으로 강제하지 않는다.

## 10. 로그 분석 함수를 책임별로 분리

```python
def parse_line(line: str) -> dict:
    parts = line.split()
    if len(parts) != 4:
        raise ValueError("필드 수가 4개가 아닙니다")

    action, ip, port_text, path = parts
    return {
        "action": action,
        "ip": ip,
        "port": int(port_text),
        "path": path,
    }

def is_denied(record: dict) -> bool:
    return record["action"] == "DENY"
```

한 함수가 한 가지 책임을 가지면 정상·오류·경계값을 따로 테스트하기 쉽다.

{% hint style="success" %}
## 🧪 실습

1. 두 숫자를 받아 합을 반환하는 함수를 만든다.
2. `print()`만 하는 함수와 `return`하는 함수의 결과를 비교한다.
3. 변경 가능한 기본값 오류를 재현하고 수정한다.
4. `parse_line()`, `validate_record()`, `summarize()`로 책임을 분리한다.
5. 각 함수에 docstring과 타입 힌트를 추가한다.
{% endhint %}

## 핵심 정리

- 정의와 호출, 매개변수와 인자는 서로 다르다.
- 계산 결과를 재사용하려면 `return`해야 한다.
- 함수는 입력을 받고 결과를 반환하도록 설계하면 테스트하기 쉽다.
- 변경 가능한 기본값과 전역 상태 변경을 피한다.
