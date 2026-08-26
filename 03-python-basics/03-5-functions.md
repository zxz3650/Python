# 03-5. 함수와 스코프

함수는 특정 작업에 이름을 붙인 재사용 가능한 코드 단위다. 03-4에서 한 셀에 작성한 이벤트 검증·분류·집계 코드를 함수로 나누면 각 단계의 입력과 결과를 따로 확인할 수 있다.

함수를 잘 작성한다는 것은 코드를 짧게 만드는 일이 아니다. **함수가 무엇을 받고, 무엇을 반환하며, 외부 상태를 변경하는지**가 호출하는 쪽에서 분명해야 한다. 이 약속을 함수의 **계약(contract)**이라고 생각할 수 있다.

{% hint style="info" %}
### 🧭 학습 목표

- 함수 정의와 호출 시점을 설명한다.
- 매개변수와 인자, 위치 인자와 키워드 인자를 구분한다.
- 기본값·키워드 전용 인자·가변 인자를 목적에 맞게 사용한다.
- `return`과 `print()`의 차이, 조기 반환과 여러 값 반환을 설명한다.
- 변경 가능한 기본값이 호출 간 상태를 공유하는 이유를 설명한다.
- 객체 전달에서 재할당과 내부 변경의 차이를 예측한다.
- 지역·바깥 함수·전역·내장 스코프의 이름 탐색 순서를 설명한다.
- 순수 함수, 부수 효과, 단일 책임을 기준으로 함수를 설계한다.
- docstring·타입 힌트·`assert`로 함수의 계약과 경계값을 검증한다.
{% endhint %}

## 학습 범위와 연결

- 자료형과 `None`은 [03-1](03-1-data-types.md)에서 학습했다.
- 리스트·딕셔너리의 변경 가능성과 복사는 [03-2](03-2-strings-collections.md)에서 학습했다.
- 조건식과 조기 분기에는 [03-3](03-3-conditions.md)의 논리를 사용한다.
- 목록 처리와 집계에는 [03-4](03-4-loops.md)의 반복 패턴을 사용한다.
- 이 절에서는 메모리 안의 데이터를 함수로 나누고 반환값을 검증한다.
- `raise`, `try`, `except`를 이용한 실패 전달은 [03-6 예외 처리](03-6-files-data.md)에서 다룬다.
- 함수를 파일로 분리하고 import하는 방법은 03-7에서 다룬다.

전용 실습은 [`notebooks/03-5-functions-scope.ipynb`](../notebooks/03-5-functions-scope.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

실행 전에 출력과 각 변수의 값을 예상한다.

```python
def show_action():
    print("DENY")

def get_action():
    return "DENY"

shown = show_action()
returned = get_action()

print(shown)
print(returned)
```

다음 질문에 답해 본다.

1. `def` 문을 실행하면 함수 본문도 즉시 실행되는가?
2. 매개변수와 인자는 같은 것인가?
3. `print()`한 값을 호출한 곳에서 계산에 다시 사용할 수 있는가?
4. `return` 뒤의 문장은 실행되는가?
5. 함수에 리스트를 전달하면 원본이 언제 변경되는가?
6. 함수 안에서 만든 지역 변수는 함수 밖에서도 사용할 수 있는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. 함수의 계약: 입력, 처리, 출력

함수는 다음 세 요소로 읽는다.

| 요소 | 질문 | 예 |
|---|---|---|
| 입력 | 어떤 값을 받는가? | 이벤트 딕셔너리, 임계값 |
| 처리 | 어떤 규칙을 적용하는가? | 횟수와 임계값 비교 |
| 출력 | 무엇을 돌려주는가? | `"WARNING"` 또는 `"NORMAL"` |

```python
def classify_count(count, threshold):
    if count >= threshold:
        return "WARNING"
    return "NORMAL"
```

이 함수의 계약을 문장으로 표현하면 다음과 같다.

- 입력: 비교 가능한 두 정수 `count`, `threshold`
- 처리: `count`가 임계값 이상인지 판단
- 출력: 상태 문자열 하나
- 부수 효과: 입력이나 외부 상태를 변경하지 않음

함수를 작성하기 전에 이 네 항목을 정하면 이름, 매개변수, 반환값, 테스트 사례를 결정하기 쉽다.

## 2. 정의와 호출

`def`는 함수 객체를 만들고 이름에 연결한다. 함수 본문은 정의할 때가 아니라 이름 뒤에 괄호를 붙여 **호출할 때** 실행된다.

```python
def greet():
    print("분석을 시작합니다")

print("호출 전")
greet()
print("호출 후")
```

출력:

```text
호출 전
분석을 시작합니다
호출 후
```

정의만 하고 호출하지 않으면 본문은 실행되지 않는다.

```python
def unused_function():
    print("이 문장은 호출 전에는 실행되지 않음")
```

함수는 호출 전에 정의되어 있어야 한다.

```python
def announce():
    return "READY"

message = announce()
print(message)
```

## 3. 매개변수와 인자

**매개변수(parameter)**는 함수 정의에서 받을 값에 붙인 이름이고, **인자(argument)**는 호출할 때 전달하는 실제 값이다.

```python
def show_port(port):       # port: 매개변수
    return f"포트: {port}"

message = show_port(443)   # 443: 인자
print(message)
```

매개변수는 함수 내부의 지역 이름이다. 같은 함수를 다른 인자로 호출하면 같은 처리 규칙을 재사용할 수 있다.

```python
def is_valid_port(port):
    return type(port) is int and 1 <= port <= 65535

print(is_valid_port(1))       # True
print(is_valid_port(65535))   # True
print(is_valid_port(65536))   # False
print(is_valid_port("443"))   # False
```

`bool`은 Python에서 `int`의 하위 자료형이므로 엄격한 입력 검증 예에서는 `type(port) is int`를 사용했다. 일반적인 객체 지향 코드에서는 `isinstance()`가 더 유연할 수 있으므로 검증 목적에 따라 선택한다.

## 4. return과 print

`print()`는 화면에 문자를 표시하는 부수 효과이고, `return`은 계산 결과를 호출한 곳으로 돌려준다.

```python
def show_action():
    print("DENY")

def get_action():
    return "DENY"

shown = show_action()
returned = get_action()

print(shown)      # None
print(returned)   # DENY
```

`show_action()`은 화면에 출력하지만 명시적인 반환값이 없다. Python 함수는 `return`이 없으면 `None`을 반환한다.

반환값은 저장·비교·조합·테스트할 수 있다.

```python
def add(left, right):
    return left + right

total = add(10, 20)
print(total * 2)       # 60
assert add(2, 3) == 5
```

계산 함수에서 직접 출력하기보다 값을 반환하고, 화면 출력은 호출하는 쪽에서 담당하면 재사용과 테스트가 쉬워진다.

## 5. return은 함수를 즉시 끝낸다

`return`이 실행되면 함수는 즉시 종료된다. 그 뒤에 있는 문장은 실행되지 않는다.

```python
def classify_count(count):
    if count >= 5:
        return "CRITICAL"
    if count >= 3:
        return "WARNING"
    return "NORMAL"
```

조기 반환은 잘못된 입력이나 특별한 경우를 먼저 처리하고 정상 흐름의 들여쓰기를 줄이는 데 유용하다.

```python
def normalize_action(action):
    if not isinstance(action, str):
        return None

    normalized = action.strip().upper()
    if normalized not in {"ALLOW", "DENY"}:
        return None

    return normalized
```

`return` 다음의 도달 불가능한 코드는 작성하지 않는다.

```python
def get_status():
    return "READY"
    # print("실행되지 않음")
```

## 6. 여러 값 반환과 언패킹

쉼표로 여러 값을 반환하면 실제 반환 객체는 튜플이다.

```python
def count_actions(actions):
    allow_count = actions.count("ALLOW")
    deny_count = actions.count("DENY")
    return allow_count, deny_count

result = count_actions(["ALLOW", "DENY", "DENY"])
print(result, type(result))  # (1, 2) <class 'tuple'>

allow_count, deny_count = result
print(allow_count, deny_count)
```

반환값의 의미가 두세 개의 고정된 값이면 튜플 언패킹이 간결하다. 값이 많거나 필드 이름이 중요하면 딕셔너리, 이후에 배우는 `dataclass` 같은 구조를 고려한다.

```python
def summarize_actions(actions):
    return {
        "total": len(actions),
        "allow": actions.count("ALLOW"),
        "deny": actions.count("DENY"),
    }
```

호출하는 쪽에서 결과 구조를 예측할 수 있도록 한 함수의 반환 형태를 일관되게 유지한다. 어떤 경로에서는 리스트, 다른 경로에서는 bool을 반환하는 식의 혼합을 피한다.

## 7. 위치·키워드·기본값 인자

### 위치 인자

위치 인자는 전달 순서로 매개변수와 대응한다.

```python
def make_endpoint(host, port):
    return f"{host}:{port}"

print(make_endpoint("example.com", 443))
```

### 키워드 인자

키워드 인자는 매개변수 이름을 명시한다.

```python
print(make_endpoint(port=443, host="example.com"))
```

순서를 바꿀 수 있고, bool이나 숫자 인자의 의미를 드러내는 데 유용하다.

### 기본값 인자

```python
def classify(count, threshold=3):
    if count >= threshold:
        return "WARNING"
    return "NORMAL"

print(classify(5))
print(classify(5, 4))
print(classify(count=5, threshold=4))
```

기본값이 없는 필수 매개변수는 기본값이 있는 매개변수보다 먼저 정의한다.

```python
# 올바른 순서
def connect(host, port=443):
    return f"{host}:{port}"
```

호출할 때 위치 인자는 일반적으로 키워드 인자보다 먼저 둔다. 같은 매개변수에 위치와 키워드로 값을 두 번 전달할 수 없다.

## 8. 키워드 전용 인자로 호출 의도 고정

매개변수 목록의 `*` 뒤에 있는 매개변수는 키워드로만 전달할 수 있다.

```python
def classify(count, *, warning=3, critical=5):
    if count >= critical:
        return "CRITICAL"
    if count >= warning:
        return "WARNING"
    return "NORMAL"

print(classify(4, warning=3, critical=5))
```

`classify(4, 3, 5)`처럼 의미를 알기 어려운 숫자 나열을 막고, 호출 코드를 설명처럼 읽게 한다.

키워드 전용 인자는 다음 상황에 유용하다.

- 같은 자료형의 선택 인자가 여러 개일 때
- bool 인자의 의미가 위치만으로 불분명할 때
- 잘못된 인자 순서가 정책 결과를 바꿀 수 있을 때

## 9. 가변 인자: *args와 **kwargs

필요할 때만 가변 인자를 사용한다. `*args`는 남은 위치 인자를 튜플로, `**kwargs`는 남은 키워드 인자를 딕셔너리로 모은다.

```python
def total_attempts(*counts):
    return sum(counts)

print(total_attempts(1, 2, 3))  # 6
```

```python
def build_record(action, **fields):
    record = {"action": action}
    record.update(fields)
    return record

event = build_record("DENY", ip="198.51.100.9", port=443)
print(event)
```

정의에서는 값을 **모으고**, 호출에서는 iterable과 딕셔너리를 `*`, `**`로 **펼칠 수 있다**.

```python
def make_endpoint(host, port):
    return f"{host}:{port}"

endpoint_parts = ["example.com", 443]
endpoint_options = {"host": "example.com", "port": 443}

print(make_endpoint(*endpoint_parts))
print(make_endpoint(**endpoint_options))
```

가변 인자가 모든 함수에 필요한 것은 아니다. 허용할 입력이 정해져 있다면 명시적인 매개변수가 계약과 오타를 더 잘 드러낸다.

## 10. 변경 가능한 기본값

기본값은 호출할 때마다가 아니라 **함수를 정의할 때 한 번** 평가된다. 리스트·딕셔너리·집합을 기본값으로 직접 사용하면 같은 객체가 호출 사이에 공유될 수 있다.

```python
# 피해야 할 형태
def add_tag_bad(tag, tags=[]):
    tags.append(tag)
    return tags

print(add_tag_bad("web"))       # ['web']
print(add_tag_bad("critical"))  # ['web', 'critical']
```

호출마다 새 컬렉션이 필요하면 `None`을 표식으로 사용한다.

```python
def add_tag(tag, tags=None):
    if tags is None:
        tags = []

    tags.append(tag)
    return tags

first = add_tag("web")
second = add_tag("critical")

print(first)   # ['web']
print(second)  # ['critical']
assert first is not second
```

문자열·숫자·튜플처럼 변경 불가능한 값은 기본값으로 안전하게 사용할 수 있다.

## 11. 객체 전달: 재할당과 내부 변경

Python은 객체에 대한 참조를 인자로 전달한다. 함수 안의 매개변수 이름을 다른 객체로 **재할당**하는 것과, 전달받은 변경 가능한 객체의 내부를 **변경**하는 것은 결과가 다르다.

### 재할당은 호출자의 이름을 바꾸지 않는다

```python
def replace_events(events):
    events = [{"action": "REPLACED"}]
    return events

original = [{"action": "ALLOW"}]
replacement = replace_events(original)

print(original)     # [{'action': 'ALLOW'}]
print(replacement)  # [{'action': 'REPLACED'}]
```

### 내부 변경은 호출자에게 보인다

```python
def append_event(events, event):
    events.append(event)

records = []
append_event(records, {"action": "DENY"})

print(records)  # [{'action': 'DENY'}]
```

입력을 변경하는 함수는 이름과 docstring에 그 사실을 드러낸다. 변경이 필요하지 않다면 새 객체를 반환하는 방식이 예측하기 쉽다.

```python
def with_event(events, event):
    new_events = events.copy()
    new_events.append(event)
    return new_events

records = []
updated_records = with_event(records, {"action": "DENY"})

assert records == []
assert updated_records == [{"action": "DENY"}]
```

얕은 복사에서는 중첩 객체가 공유될 수 있다는 03-2의 규칙도 함께 기억한다.

## 12. 순수 함수와 부수 효과

같은 입력에 항상 같은 결과를 반환하고 외부 상태를 바꾸지 않는 함수를 **순수 함수**라고 한다.

```python
def is_sensitive_port(port):
    return port in {22, 3389}
```

다음 동작은 부수 효과의 예다.

- 화면에 출력
- 전달받은 리스트·딕셔너리 변경
- 전역 변수 변경
- 파일이나 네트워크 사용

부수 효과가 잘못된 것은 아니다. 다만 계산과 부수 효과를 분리하면 핵심 로직을 외부 환경 없이 시험할 수 있다.

```python
def format_alert(event):
    return f"[{event['action']}] {event['ip']}:{event['port']}"

alert = format_alert({
    "action": "DENY",
    "ip": "198.51.100.9",
    "port": 22,
})

print(alert)  # 출력은 경계에서 한 번만 수행
```

## 13. 스코프와 LEGB 이름 탐색

스코프는 이름을 사용할 수 있는 코드 영역이다. Python은 이름을 다음 순서로 찾는다.

1. **Local**: 현재 함수
2. **Enclosing**: 현재 함수를 감싼 바깥 함수
3. **Global**: 모듈 최상위
4. **Built-in**: `len`, `print` 같은 내장 이름

```python
threshold = 3  # Global

def is_suspicious(count):
    result = count >= threshold  # count와 result는 Local
    return result

print(is_suspicious(5))
# print(result)  # NameError: 지역 이름은 함수 밖에서 보이지 않음
```

함수 안에서 같은 이름에 값을 대입하면 기본적으로 새로운 지역 이름이 만들어진다.

```python
status = "GLOBAL"

def get_local_status():
    status = "LOCAL"
    return status

print(get_local_status())  # LOCAL
print(status)              # GLOBAL
```

내장 이름을 변수나 매개변수로 덮어쓰지 않는다.

```python
# 피해야 할 이름: list, dict, str, sum, input
port_list = [22, 443]
print(sum(port_list))
```

## 14. global과 nonlocal

`global`은 함수 안에서 전역 이름을 재할당하고, `nonlocal`은 중첩 함수에서 가장 가까운 바깥 함수의 이름을 재할당한다.

```python
processed_count = 0

def mark_processed():
    global processed_count
    processed_count += 1
```

```python
def make_counter():
    count = 0

    def increment():
        nonlocal count
        count += 1
        return count

    return increment

counter = make_counter()
print(counter())  # 1
print(counter())  # 2
```

문법을 알아야 기존 코드를 읽을 수 있지만, 초급 단계에서는 전역 상태를 바꾸기보다 값을 인자로 받고 결과를 반환하는 방식을 우선한다. 숨은 상태가 적을수록 호출 순서에 덜 의존하고 테스트하기 쉽다.

## 15. 한 함수에는 한 가지 책임

함수 분리 기준은 단순히 줄 수가 아니다. 함수 이름으로 하나의 책임을 자연스럽게 설명할 수 있는지 확인한다.

```python
def normalize_action(action):
    if not isinstance(action, str):
        return None

    normalized = action.strip().upper()
    if normalized not in {"ALLOW", "DENY"}:
        return None
    return normalized

def is_sensitive_event(event):
    return (
        event["action"] == "DENY"
        and event["port"] in {22, 3389}
    )
```

좋은 함수 이름은 동작이나 질문을 드러낸다.

- `normalize_action`: 값을 정규화한다.
- `is_valid_event`: 참·거짓을 판단한다.
- `count_events_by_ip`: 횟수를 집계한다.
- `format_report`: 출력 문자열을 만든다.

`process_data()`처럼 범위가 넓은 이름은 입력 검증, 변환, 집계, 출력을 한 함수에 섞는 신호일 수 있다.

## 16. docstring과 타입 힌트

docstring은 함수 본문의 첫 문자열로 목적, 인자, 반환값, 중요한 제약을 설명한다.

```python
def classify_count(count: int, threshold: int = 3) -> str:
    """횟수가 임계값 이상이면 WARNING, 아니면 NORMAL을 반환한다."""
    if count >= threshold:
        return "WARNING"
    return "NORMAL"
```

타입 힌트는 입력과 반환 형태를 문서화하고 편집기·정적 분석 도구를 돕지만, 실행 중 자료형을 자동으로 강제하지 않는다.

```python
print(classify_count.__annotations__)
print(classify_count.__doc__)
```

초급 함수의 docstring에는 다음을 우선 기록한다.

- 함수가 하는 일
- 입력값의 의미와 허용 범위
- 반환값의 의미와 형태
- 입력 객체를 변경하는지 여부

코드와 같은 내용을 단순 반복하기보다 호출자가 알아야 할 계약을 적는다.

## 17. 함수도 값이다: 콜백과 lambda

Python에서 함수는 이름에 저장하고 다른 함수의 인자로 전달할 수 있는 객체다.

```python
def is_denied(event):
    return event["action"] == "DENY"

def select_events(events, rule):
    selected = []
    for event in events:
        if rule(event):
            selected.append(event)
    return selected

events = [
    {"action": "ALLOW", "port": 443},
    {"action": "DENY", "port": 22},
]

denied_events = select_events(events, is_denied)
print(denied_events)
```

여기서 `is_denied`는 호출 결과가 아니라 함수 자체로 전달된다. `is_denied()`라고 쓰면 필요한 인자 없이 즉시 호출하려는 다른 의미가 된다.

짧고 한 번만 쓰는 식은 `lambda`로 표현할 수도 있다.

```python
sorted_events = sorted(events, key=lambda event: event["port"])
print(sorted_events)
```

조건이 길거나 재사용·설명이 필요하면 `lambda`보다 이름 있는 `def`가 낫다.

## 18. 확장 개념: 재귀 함수

재귀 함수는 자기 자신을 호출한다. 반드시 호출을 멈추는 **기저 조건**과 그 조건에 가까워지는 변화가 필요하다.

```python
def countdown(number):
    if number <= 0:              # 기저 조건
        return ["done"]
    return [number] + countdown(number - 1)

print(countdown(3))  # [3, 2, 1, 'done']
```

기저 조건이 없거나 입력이 기저 조건에 가까워지지 않으면 재귀가 끝나지 않는다. Python은 재귀 깊이에 제한이 있으므로 단순 목록 처리나 큰 반복에는 03-4의 `for`·`while`이 더 자연스러운 경우가 많다.

## 19. 함수 검증: 정상값, 경계값, 잘못된 값

함수의 계약에서 테스트 사례를 도출한다.

```python
def is_valid_port(port):
    return type(port) is int and 1 <= port <= 65535
```

| 구분 | 입력 | 예상 결과 |
|---|---:|---:|
| 최솟값 바로 아래 | `0` | `False` |
| 유효한 최솟값 | `1` | `True` |
| 유효한 최댓값 | `65535` | `True` |
| 최댓값 바로 위 | `65536` | `False` |
| 잘못된 자료형 | `"443"` | `False` |
| bool 혼동 방지 | `True` | `False` |

```python
assert is_valid_port(0) is False
assert is_valid_port(1) is True
assert is_valid_port(65535) is True
assert is_valid_port(65536) is False
assert is_valid_port("443") is False
assert is_valid_port(True) is False
```

목록을 받는 함수에는 빈 목록, 한 항목, 여러 항목, 잘못된 항목이 섞인 경우를 확인한다. `assert`는 학습과 내부 가정 확인에 유용하다. 사용자 입력 오류를 처리하는 방법은 03-6에서 예외와 함께 다룬다.

## 20. 미니 실습: 이벤트 분석을 함수로 분리

03-4의 이벤트 목록 분석을 검증·분류·집계·표현 책임으로 나눈다.

### 20.1 이벤트 검증

```python
def is_valid_event(event: dict) -> bool:
    """필수 필드와 action·ip·port 값이 유효한지 반환한다."""
    action = event.get("action")
    ip = event.get("ip")
    port = event.get("port")

    has_valid_action = action in {"ALLOW", "DENY"}
    has_valid_ip = isinstance(ip, str) and bool(ip.strip())
    has_valid_port = type(port) is int and 1 <= port <= 65535

    return has_valid_action and has_valid_ip and has_valid_port
```

### 20.2 이벤트 분류

선택 인자는 키워드로만 전달하고, 변경 불가능한 튜플을 기본값으로 사용한다.

```python
def classify_event(event: dict, *, sensitive_ports=(22, 3389)) -> str:
    """유효한 이벤트를 ALLOW, DENY, CRITICAL 중 하나로 분류한다."""
    if event["action"] == "DENY" and event["port"] in sensitive_ports:
        return "CRITICAL"
    if event["action"] == "DENY":
        return "DENY"
    return "ALLOW"
```

### 20.3 목록 집계

입력 목록과 이벤트 딕셔너리를 변경하지 않고 새 결과를 반환한다.

```python
def summarize_events(events: list[dict]) -> dict:
    """이벤트 목록을 검증·분류하고 건수와 IP별 DENY 횟수를 반환한다."""
    counts = {
        "valid": 0,
        "invalid": 0,
        "allow": 0,
        "deny": 0,
        "critical": 0,
    }
    deny_count_by_ip = {}

    for event in events:
        if not is_valid_event(event):
            counts["invalid"] += 1
            continue

        counts["valid"] += 1
        level = classify_event(event)

        if level == "ALLOW":
            counts["allow"] += 1
        else:
            counts["deny"] += 1
            ip = event["ip"]
            deny_count_by_ip[ip] = deny_count_by_ip.get(ip, 0) + 1

            if level == "CRITICAL":
                counts["critical"] += 1

    return {
        "counts": counts,
        "deny_count_by_ip": deny_count_by_ip,
    }
```

### 20.4 보고 문자열 생성

```python
def format_summary(summary: dict) -> str:
    """집계 딕셔너리를 한 줄 보고 문자열로 변환한다."""
    counts = summary["counts"]
    return (
        f"valid={counts['valid']} "
        f"invalid={counts['invalid']} "
        f"deny={counts['deny']} "
        f"critical={counts['critical']}"
    )
```

### 20.5 호출과 검증

```python
events = [
    {"action": "ALLOW", "ip": "10.0.0.5", "port": 443},
    {"action": "DENY", "ip": "198.51.100.9", "port": 22},
    {"action": "DENY", "ip": "198.51.100.9", "port": 3389},
    {"action": "BLOCK", "ip": "203.0.113.10", "port": 70000},
    {"action": "DENY", "ip": "203.0.113.10", "port": 443},
]

summary = summarize_events(events)
report = format_summary(summary)

print(summary)
print(report)

assert summary == {
    "counts": {
        "valid": 4,
        "invalid": 1,
        "allow": 1,
        "deny": 3,
        "critical": 2,
    },
    "deny_count_by_ip": {
        "198.51.100.9": 2,
        "203.0.113.10": 1,
    },
}
assert report == "valid=4 invalid=1 deny=3 critical=2"
```

`summarize_events()`는 화면에 출력하지 않고 결과를 반환한다. 따라서 같은 결과를 콘솔, 파일, 웹 화면 등 서로 다른 경계에서 재사용할 수 있다.

여기서 `deny`는 모든 DENY 이벤트 수이고 `critical`은 그중 민감 포트에 해당하는 부분집합이다. 따라서 `allow + deny == valid`이지만 `allow + deny + critical`을 합치면 중복 계산된다. 03-4와 같은 지표 의미를 유지했으며, 실제 함수에서도 집계 필드의 포함 관계를 계약에 명시해야 한다.

## 21. 흔한 실수와 점검법

| 실수 | 문제 | 개선 |
|---|---|---|
| 함수 객체와 호출을 혼동 | `rule`과 `rule()`의 의미가 달라짐 | 지금 값이 함수인지 호출 결과인지 확인 |
| 계산 함수가 `print()`만 수행 | 결과를 재사용·검증하기 어려움 | 값을 `return`하고 출력은 호출부에서 수행 |
| 일부 경로에만 `return` 작성 | 예상하지 못한 `None` 반환 | 모든 분기의 반환 형태 확인 |
| `return` 뒤에 코드 작성 | 도달할 수 없는 코드 | 반환 위치와 실행 경로 추적 |
| 위치 인자가 너무 많음 | 호출 의미와 순서가 불명확 | 키워드·키워드 전용 인자 사용 |
| 리스트·딕셔너리를 기본값으로 사용 | 호출 간 상태 공유 | `None` 표식으로 새 객체 생성 |
| 입력 리스트를 조용히 변경 | 호출자의 데이터가 예상 밖으로 바뀜 | 새 객체 반환 또는 변경 사실 문서화 |
| 전역 상태에 의존 | 호출 순서에 따라 결과 변화 | 필요한 값을 인자로 전달 |
| `list`, `str`, `sum`을 이름으로 사용 | 내장 함수를 가림 | 의미 있는 다른 이름 사용 |
| 타입 힌트가 검증한다고 생각 | 실행 중 잘못된 자료형이 그대로 전달 | 조건 검사 또는 03-6의 예외 처리 사용 |
| 한 함수가 검증·집계·출력을 모두 담당 | 테스트와 변경 영향 범위 증가 | 책임별 함수로 분리 |

함수 호출을 디버깅할 때는 다음 순서로 추적한다.

1. 전달한 인자와 매개변수 대응
2. 각 분기에서 실행되는 `return`
3. 반환값의 자료형과 구조
4. 입력 객체와 전역 상태의 변경 여부

## 22. 단계별 연습문제

### 22.1 출력과 반환값 예측

```python
def announce(message):
    print(message)

def build_message(message):
    return f"[{message}]"

first = announce("READY")
second = build_message("READY")
```

`first`, `second`의 값을 예상하고 이유를 설명한다.

### 22.2 경계값 함수

점수가 0~100의 정수인지 확인하는 `is_valid_score(score)`를 작성한다. `-1`, `0`, `100`, `101`, `"90"`, `True`를 `assert`로 검증한다.

### 22.3 조기 반환

문자열을 받아 양쪽 공백을 제거하고 대문자로 바꾸는 `normalize_ip_label(value)`를 작성한다. 입력이 문자열이 아니거나 정리한 결과가 빈 문자열이면 `None`을 조기 반환한다.

### 22.4 호출 방식

`make_scan_plan(host, *, start_port=1, end_port=1024)`를 작성한다. 키워드 전용 인자가 호출 의미를 어떻게 분명하게 만드는지 설명한다.

### 22.5 변경 가능한 기본값

`def add_item(item, items=[])`가 호출 간 상태를 공유하는 현상을 재현하고 `None` 기본값으로 수정한다. 두 번의 독립 호출 결과가 서로 다른 객체인지 `is not`으로 검증한다.

### 22.6 입력 객체 변경 여부

태그 리스트와 새 태그를 받아 원본을 변경하지 않고 새 리스트를 반환하는 `with_tag(tags, tag)`를 작성한다. 호출 전후 원본을 `assert`로 확인한다.

### 22.7 함수 전달

이벤트 목록과 판단 함수 하나를 받아 조건을 만족하는 이벤트만 반환하는 `select_events(events, rule)`을 작성한다. DENY 판단 함수와 443 포트 판단 함수를 각각 전달한다.

### 22.8 미니 실습 확장

20절의 코드에 다음 기능을 추가한다.

1. `count_events_by_port(events)`를 별도 함수로 작성한다.
2. 유효한 이벤트만 집계하고 입력 목록을 변경하지 않는다.
3. 빈 목록, 잘못된 이벤트만 있는 목록, 정상 목록을 검증한다.
4. 함수마다 입력·반환·변경 여부를 docstring으로 기록한다.

## 23. 연습문제 정답과 해설

### 23.1 출력과 반환값

`announce()`는 `READY`를 출력하지만 명시적 반환값이 없으므로 `first`는 `None`이다. `build_message()`는 출력하지 않고 문자열을 반환하므로 `second`는 `"[READY]"`다.

### 23.2 경계값 함수

```python
def is_valid_score(score):
    return type(score) is int and 0 <= score <= 100

assert is_valid_score(-1) is False
assert is_valid_score(0) is True
assert is_valid_score(100) is True
assert is_valid_score(101) is False
assert is_valid_score("90") is False
assert is_valid_score(True) is False
```

### 23.3 조기 반환

```python
def normalize_ip_label(value):
    if not isinstance(value, str):
        return None

    normalized = value.strip().upper()
    if not normalized:
        return None
    return normalized
```

### 23.4 호출 방식

```python
def make_scan_plan(host, *, start_port=1, end_port=1024):
    return {
        "host": host,
        "start_port": start_port,
        "end_port": end_port,
    }

plan = make_scan_plan(
    "example.com",
    start_port=20,
    end_port=25,
)
```

두 정수가 무엇을 뜻하는지 호출부에서 바로 확인할 수 있고 순서 교환 실수를 줄인다.

### 23.5 변경 가능한 기본값

```python
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

first = add_item("A")
second = add_item("B")

assert first == ["A"]
assert second == ["B"]
assert first is not second
```

### 23.6 입력 객체 변경 여부

```python
def with_tag(tags, tag):
    new_tags = tags.copy()
    new_tags.append(tag)
    return new_tags

original = ["web"]
updated = with_tag(original, "critical")

assert original == ["web"]
assert updated == ["web", "critical"]
assert original is not updated
```

### 23.7 함수 전달

```python
def select_events(events, rule):
    selected = []
    for event in events:
        if rule(event):
            selected.append(event)
    return selected

def is_denied(event):
    return event["action"] == "DENY"

def uses_https(event):
    return event["port"] == 443

denied = select_events(events, is_denied)
https_events = select_events(events, uses_https)
```

### 23.8 미니 실습 확장

```python
def count_events_by_port(events):
    """유효한 이벤트의 포트별 횟수를 새 딕셔너리로 반환한다."""
    counts = {}
    for event in events:
        if is_valid_event(event):
            port = event["port"]
            counts[port] = counts.get(port, 0) + 1
    return counts

assert count_events_by_port([]) == {}
assert count_events_by_port([
    {"action": "BLOCK", "ip": "", "port": 70000},
]) == {}
assert count_events_by_port(events) == {
    443: 2,
    22: 1,
    3389: 1,
}
```

## 24. 완료 기준

다음 항목을 코드와 말로 설명할 수 있으면 이 절의 목표를 달성한 것이다.

- 함수의 입력·처리·출력·부수 효과를 설명한다.
- 정의와 호출, 매개변수와 인자를 구분한다.
- `return`, 조기 반환, 여러 값 반환의 실행 흐름을 예측한다.
- 위치·키워드·기본값·키워드 전용·가변 인자를 구분한다.
- 변경 가능한 기본값이 호출 사이에 공유되는 이유를 설명한다.
- 함수 안의 재할당과 변경 가능한 객체의 내부 변경을 구분한다.
- LEGB 순서와 `global`, `nonlocal`의 영향을 설명한다.
- 계산과 출력·상태 변경을 분리한다.
- 함수 객체를 인자로 전달하고 짧은 `lambda`의 적정 범위를 판단한다.
- 정상·경계·잘못된 입력과 빈 컬렉션을 `assert`로 검증한다.

## 핵심 정리

- 함수는 입력, 처리, 반환값, 부수 효과가 분명한 계약으로 설계한다.
- `def`는 함수를 정의하고, 본문은 호출할 때 실행된다.
- `print()`는 표시하고 `return`은 호출한 곳에 결과를 전달한다.
- 기본값은 정의 시 한 번 평가되므로 변경 가능한 객체를 직접 기본값으로 사용하지 않는다.
- 함수에 전달한 변경 가능한 객체의 내부를 바꾸면 호출자에게도 보인다.
- 전역 상태 변경보다 필요한 값을 인자로 받고 결과를 반환하는 방식을 우선한다.
- 한 함수는 한 책임에 집중하고 계산과 부수 효과를 분리한다.
- docstring과 타입 힌트는 계약을 설명하지만 실행 시 입력을 자동 검증하지 않는다.
- 작은 함수도 정상값·경계값·잘못된 값·빈 입력으로 검증한다.
