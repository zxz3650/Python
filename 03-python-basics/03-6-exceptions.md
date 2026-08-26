# 03-6. 예외 처리

예외는 문법적으로 올바른 프로그램이 실행 중 작업을 계속할 수 없는 상황을 만났다는 신호다. 문자열을 정수로 바꿀 수 없거나, 필요한 딕셔너리 키가 없거나, 함수의 입력 계약을 지킬 수 없을 때 발생한다.

예외 처리의 목표는 오류를 무조건 없애는 것이 아니다. **원인을 읽고, 처리할 수 있는 위치에서만 구체적으로 복구하며, 처리할 수 없는 실패는 문맥을 보존해 호출자에게 전달하는 것**이 핵심이다.

{% hint style="info" %}
### 🧭 학습 목표

- 문법 오류, 실행 예외, 논리 오류를 구분한다.
- traceback에서 예외 유형·메시지·발생 위치·호출 경로를 찾는다.
- 예외가 호출 스택을 따라 전파되는 과정을 설명한다.
- `try`, `except`, `else`, `finally`의 실행 조건을 예측한다.
- 구체적인 예외 유형과 처리 순서를 선택한다.
- `raise`, 맨몸 `raise`, `raise ... from ...`을 목적에 맞게 사용한다.
- 조건 검증·반환값·예외 중 함수 계약에 맞는 방식을 선택한다.
- 한 건 실패와 전체 실패를 구분해 배치 처리 전략을 설계한다.
- `assert`와 사용자 입력 예외의 차이를 설명한다.
- 원인과 해결 기준은 담되 민감정보는 노출하지 않는 오류 메시지를 작성한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | traceback 읽기, `try`·`except`, 구체적 예외 유형, `raise` |
| 권장 | `else`·`finally`, 예외 전파, 복구 경계, `assert`와 예외 구분 |
| 심화 | 예외 연쇄·재발생, LBYL·EAFP, fail-fast·best-effort 정책 |

## 학습 범위와 연결

- 비교·논리 조건은 [03-3](03-3-conditions.md), 반복 처리는 [03-4](03-4-loops.md)에서 학습했다.
- 함수의 입력·반환값·부수 효과 계약은 [03-5](03-5-functions.md)에서 학습했다.
- 이 절에서는 함수가 약속한 결과를 만들 수 없을 때 실패를 전달하고 복구하는 방법을 다룬다.
- 파일·JSON·CSV에서 발생하는 실제 입출력 예외는 04장에서 다룬다.
- 예외 처리 코드를 모듈로 분리하는 방법은 [03-7](03-7-modules-packages.md)에서 다룬다.
- 사용자 정의 예외 클래스는 03-8 클래스 기초 이후 확장할 수 있다.

전용 실습은 [`notebooks/03-6-exceptions.ipynb`](../notebooks/03-6-exceptions.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

다음 코드의 실행 순서와 출력 결과를 예상한다.

```python
text = "443"

try:
    port = int(text)
except ValueError:
    result = "변환 실패"
else:
    result = f"변환 성공: {port}"
finally:
    finished = True

print(result)
print(finished)
```

다음 질문에 답해 본다.

1. `SyntaxError`와 `ValueError`는 언제 발생하는가?
2. `except Exception` 하나로 모든 오류를 잡으면 왜 문제가 되는가?
3. `else`와 `finally`는 각각 언제 실행되는가?
4. 처리하지 않은 예외는 호출한 함수의 바깥으로 전달되는가?
5. `raise ValueError(...) from exc`의 `from exc`는 무엇을 보존하는가?
6. 사용자 입력 검증에 `assert`를 사용해도 되는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. 오류의 세 종류

### 1.1 문법 오류

Python 문법 규칙에 맞지 않아 코드를 실행하기 전에 발견된다.

```python
# if True
#     print("콜론이 없음")
```

대표적으로 `SyntaxError`, `IndentationError`가 있다. 문법 오류는 `try`로 정상 실행 흐름처럼 복구하려 하기보다 코드를 수정해야 한다.

### 1.2 실행 예외

문법은 맞지만 실행 중 현재 값이나 상태로 작업을 완료할 수 없을 때 발생한다.

```python
number = int("abc")  # ValueError
```

```python
record = {"action": "DENY"}
port = record["port"]  # KeyError
```

예상 가능한 실행 예외 중 복구 방법이 있는 경우에만 처리한다.

### 1.3 논리 오류

프로그램은 끝까지 실행되지만 요구사항과 다른 결과를 만든다.

```python
def is_valid_port(port):
    return 0 <= port <= 65535  # 0을 허용하는 논리 오류
```

논리 오류는 traceback이 생기지 않을 수 있다. 경계값 테스트, 결정표, `assert`, 코드 리뷰로 찾아야 한다.

| 구분 | 발견 시점 | 대표 대응 |
|---|---|---|
| 문법 오류 | 실행 전 파싱 | 문법·들여쓰기 수정 |
| 실행 예외 | 실행 중 | 원인 확인 후 복구 또는 전파 |
| 논리 오류 | 결과 검증 시 | 요구사항·조건식·테스트 수정 |

## 2. traceback 읽기

처리되지 않은 예외가 발생하면 Python은 호출 경로와 실패 정보를 traceback으로 보여 준다.

```python
def convert_port(value):
    return int(value)

def build_endpoint(host, port_text):
    port = convert_port(port_text)
    return f"{host}:{port}"

build_endpoint("example.com", "not-a-port")
```

대표적인 출력 구조:

```text
Traceback (most recent call last):
  File "example.py", line 8, in <module>
    build_endpoint("example.com", "not-a-port")
  File "example.py", line 5, in build_endpoint
    port = convert_port(port_text)
  File "example.py", line 2, in convert_port
    return int(value)
ValueError: invalid literal for int() with base 10: 'not-a-port'
```

다음 순서로 읽는다.

1. **마지막 줄**에서 예외 유형과 메시지를 확인한다.
2. traceback의 **아래쪽 프레임**에서 실제로 실패한 표현을 찾는다.
3. 위쪽 프레임을 따라가며 어떤 입력과 호출 경로로 도달했는지 확인한다.
4. 표준 라이브러리 내부보다 먼저 자신이 작성한 코드의 파일명과 행을 찾는다.
5. 재현 입력과 함수 계약을 비교한다.

예외 메시지는 원인 단서이지 전체 해결책은 아니다. 실패한 값과 기대 조건을 코드에서 함께 확인한다.

## 3. 예외 전파와 처리 위치

함수 안에서 예외를 처리하지 않으면 호출한 함수로 전달된다. 처리하는 `except`를 만날 때까지 호출 스택을 따라 올라가며, 끝까지 처리되지 않으면 프로그램의 현재 실행이 중단되고 traceback이 출력된다.

```python
def parse_port(value):
    return int(value)

def make_record(port_text):
    port = parse_port(port_text)
    return {"port": port}

try:
    record = make_record("invalid")
except ValueError as exc:
    print("레코드를 만들 수 없음:", exc)
```

`parse_port()`와 `make_record()`는 복구 방법을 모르므로 예외를 전파하고, 호출 경계가 실패를 사용자 메시지로 바꾼다.

{% hint style="info" %}
예외가 발생한 곳과 예외를 처리할 곳은 같지 않을 수 있다. 현재 함수가 실패를 실제로 복구하거나 의미 있는 문맥을 추가할 수 없다면 잡지 않고 전파하는 편이 낫다.
{% endhint %}

## 4. 자주 만나는 예외 유형

| 예외 | 대표 상황 | 예 |
|---|---|---|
| `ValueError` | 자료형은 맞지만 값 형식·범위가 부적절 | `int("abc")` |
| `TypeError` | 연산이나 함수가 자료형을 처리할 수 없음 | `1 + "2"` |
| `KeyError` | 딕셔너리에 키가 없음 | `record["port"]` |
| `IndexError` | 시퀀스 인덱스가 범위를 벗어남 | `items[10]` |
| `AttributeError` | 객체에 속성·메서드가 없음 | `10.strip()` |
| `ZeroDivisionError` | 0으로 나눔 | `10 / 0` |
| `FileNotFoundError` | 대상 파일이 없음 | 04장 파일 입출력 |
| `PermissionError` | 자원 접근 권한이 없음 | 04장 파일 입출력 |

예외는 계층 구조를 가진다. 위 예외 대부분은 `Exception`의 하위 유형이다. `KeyboardInterrupt`, `SystemExit`처럼 프로그램 중단과 관련된 예외까지 무심코 잡지 않도록 일반 코드에서는 맨몸 `except:`를 피한다.

```python
try:
    port = int("abc")
except ValueError as exc:
    print(type(exc).__name__)  # ValueError
    print(str(exc))            # 사람이 읽는 메시지
```

## 5. try와 except

`try`에는 예외가 예상되는 최소 범위만 둔다.

```python
text = "not-a-port"

try:
    port = int(text)
except ValueError as exc:
    print(f"포트 변환 실패: {text!r}")
    print("원인:", exc)
```

`try`가 넓으면 어느 문장이 실패했는지와 `except`가 어떤 실패까지 잡는지 불분명해진다.

```python
# 범위가 너무 넓은 형태
try:
    port = int(text)
    endpoint = f"example.com:{port}"
    report = {"endpoint": endpoint}
    print(report)
except ValueError:
    print("처리 실패")
```

변환만 실패할 수 있다고 판단했다면 변환만 `try`에 넣고, 이후 정상 처리 코드는 `else`나 바깥에 둔다.

## 6. 여러 예외와 처리 순서

예외 유형별 복구 방법이 다르면 `except`를 나눈다.

```python
def read_port(record):
    try:
        return int(record["port"])
    except KeyError:
        return "필수 키 없음"
    except (TypeError, ValueError):
        return "포트 형식 오류"
```

같은 방식으로 처리할 예외는 튜플로 묶을 수 있다.

하위 예외를 먼저, 넓은 상위 예외를 나중에 둔다.

```python
try:
    port = int("abc")
except ValueError:
    print("숫자 형식 오류")
except Exception:
    print("그 밖의 예상하지 못한 오류")
```

`Exception`을 먼저 두면 뒤의 `ValueError` 분기는 도달할 수 없다. 또한 넓은 `Exception` 처리는 보통 프로그램의 최상위 경계에서 기록·종료 정책을 적용할 때 제한적으로 사용한다.

## 7. else와 finally

네 블록의 역할을 구분한다.

| 블록 | 실행 조건 | 주 용도 |
|---|---|---|
| `try` | 항상 시작 | 실패 가능성이 있는 최소 작업 |
| `except` | 지정한 예외 발생 | 복구·대체·메시지 변환 |
| `else` | `try`가 예외 없이 끝남 | 성공했을 때만 수행할 후속 처리 |
| `finally` | 성공·실패와 관계없이 실행 | 정리·상태 복원 |

```python
text = "443"

try:
    port = int(text)
except ValueError:
    result = "변환 실패"
else:
    result = f"변환 성공: {port}"
finally:
    finished = True

print(result)
print(finished)
```

`else`를 사용하면 성공 후속 코드에서 발생한 예외를 앞의 `except`가 잘못 잡는 일을 줄인다.

`finally`는 `return` 또는 예외 전파가 예정되어 있어도 먼저 실행된다.

```python
def demonstrate_finally():
    steps = []
    try:
        steps.append("try")
        return steps
    finally:
        steps.append("finally")

print(demonstrate_finally())  # ['try', 'finally']
```

{% hint style="warning" %}
`finally`에서 새 `return`을 하거나 다른 예외를 발생시키면 원래 반환값이나 예외를 가릴 수 있다. `finally`는 정리 작업에 집중한다. 파일 같은 자원 정리는 04장에서 `with` 문을 우선 사용한다.
{% endhint %}

## 8. raise로 계약 위반 알리기

함수가 약속한 결과를 만들 수 없으면 의미 있는 예외를 직접 발생시킬 수 있다.

```python
def validate_port(port):
    if type(port) is not int:
        raise TypeError("port는 정수여야 합니다")
    if not 1 <= port <= 65535:
        raise ValueError("port는 1~65535 범위여야 합니다")
```

`TypeError`는 허용하지 않는 자료형, `ValueError`는 자료형은 맞지만 허용하지 않는 값에 사용했다.

```python
validate_port(443)    # 정상
# validate_port("443")  # TypeError
# validate_port(70000)  # ValueError
```

예외는 함수의 반환값이 아니다. 정상 경로에서 결과를 반환하고, 계약을 지킬 수 없는 경로에서 예외를 발생시킨다.

## 9. 예외 연쇄와 재발생

### 원인을 보존해 새 예외 발생

낮은 수준의 오류를 업무 문맥이 있는 예외로 바꿀 때 `raise ... from exc`를 사용한다.

```python
def parse_port(value):
    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"포트 형식이 올바르지 않습니다: {value!r}") from exc

    if not 1 <= port <= 65535:
        raise ValueError(f"포트 범위를 벗어났습니다: {port}")
    return port
```

연쇄된 traceback은 원래 변환 오류와 새 문맥을 모두 보여 준다. `exc.__cause__`로 명시적 원인을 확인할 수도 있다.

### 같은 예외를 그대로 다시 전달

현재 위치에서 기록이나 부분 정리를 한 뒤 같은 예외를 유지하려면 맨몸 `raise`를 사용한다.

```python
def convert_with_note(value):
    try:
        return int(value)
    except ValueError:
        print("변환 단계에서 실패")
        raise
```

`raise exc`보다 맨몸 `raise`가 현재 예외의 traceback 문맥을 그대로 보존하는 데 적합하다.

## 10. 검증 결과와 예외 중 무엇을 선택할까

모든 거짓 결과가 예외는 아니다.

| 상황 | 권장 방식 | 예 |
|---|---|---|
| 정상적인 두 결과 중 하나 | bool·상태 반환 | 이벤트가 DENY인지 판단 |
| 값이 없을 수 있음이 계약 | `None` 또는 빈 컬렉션 | 검색 결과 없음 |
| 함수가 약속한 결과를 만들 수 없음 | 예외 | 포트 문자열을 정수로 변환 불가 |
| 호출자가 잘못된 자료형·범위 전달 | `TypeError`·`ValueError` | 포트 범위 위반 |

```python
def is_denied(event):
    return event["action"] == "DENY"  # ALLOW도 정상 결과
```

```python
def require_known_action(action):
    if action not in {"ALLOW", "DENY"}:
        raise ValueError(f"지원하지 않는 action: {action!r}")
    return action
```

`DENY`는 오류가 아니라 유효한 업무 상태다. 기술적 실패와 업무 분류 결과를 혼동하지 않는다.

## 11. LBYL과 EAFP

Python 코드에서는 두 접근을 모두 볼 수 있다.

- **LBYL**(Look Before You Leap): 실행 전에 조건을 검사한다.
- **EAFP**(Easier to Ask Forgiveness than Permission): 정상 작업을 시도하고 예상 예외를 처리한다.

```python
# LBYL
if "port" in record:
    port = record["port"]
else:
    port = None
```

```python
# EAFP
try:
    port = record["port"]
except KeyError:
    port = None
```

선택 기준:

- 조건 확인이 명확하고 실패가 정상적인 분기다 → LBYL
- 검사와 실제 작업 사이 상태가 바뀔 수 있거나 작업 자체가 가장 정확한 검증이다 → EAFP
- 어떤 방식을 쓰든 예상한 예외만 좁게 처리한다.

딕셔너리의 선택 키라면 `record.get("port")`가 더 간단할 수 있다. 필수 키 누락을 조용히 `None`으로 바꾸면 데이터 오류를 숨길 수 있으므로 계약에 따라 결정한다.

## 12. 예외를 잡는 경계와 복구 전략

예외를 잡기 전에 “이 위치에서 무엇을 할 수 있는가?”를 묻는다.

가능한 복구:

- 기본값이나 대체 입력 사용
- 해당 항목만 제외하고 나머지 계속 처리
- 재시도 가능한 작업을 제한된 횟수만큼 재시도
- 사용자에게 수정 가능한 기준을 안내
- 자원을 정리하고 상위 호출자에게 재전파

복구할 수 없다면 억지로 잡지 않는다.

```python
def parse_user_port(text):
    return parse_port(text)  # 실패 정책은 호출자가 결정

try:
    port = parse_user_port("invalid")
except ValueError as exc:
    print("입력한 포트를 확인하세요:", exc)
```

낮은 수준 함수는 구체적인 실패를 전달하고, 사용자 인터페이스·명령줄 같은 바깥 경계는 메시지와 종료 정책을 결정한다. 같은 예외를 여러 계층에서 반복 출력하지 않는다.

## 13. 한 건 실패와 전체 실패

여러 행을 처리할 때 정책을 먼저 정한다.

- **fail-fast**: 한 건이라도 잘못되면 전체 처리를 중단한다.
- **best-effort**: 잘못된 항목을 기록하고 나머지를 계속 처리한다.
- **all-or-nothing**: 모두 유효할 때만 결과 상태를 변경한다.

best-effort 예:

```python
values = ["22", "invalid", "443", "70000"]
valid_ports = []
errors = []

for line_number, value in enumerate(values, start=1):
    try:
        port = parse_port(value)
    except ValueError as exc:
        errors.append({
            "line": line_number,
            "error": str(exc),
        })
        continue

    valid_ports.append(port)
```

`try`를 반복문 전체에 두면 첫 오류에서 나머지 데이터를 처리하지 못할 수 있다. 항목별 복구가 요구사항이면 현재 항목의 최소 코드만 `try`로 감싼다.

{% hint style="warning" %}
오류를 건너뛰는 정책은 실패를 숨기라는 뜻이 아니다. 실패 건수, 행 번호, 안전한 오류 이유를 결과에 포함해 누락을 관찰할 수 있게 한다.
{% endhint %}

## 14. assert와 예외의 차이

`assert`는 개발 중 내부 가정과 테스트 결과를 확인하는 도구다.

```python
summary = {"valid": 4, "invalid": 1}
assert summary["valid"] + summary["invalid"] == 5
```

사용자 입력이나 외부 데이터 검증에는 명시적인 조건과 예외를 사용한다.

```python
def require_positive_count(count):
    if type(count) is not int:
        raise TypeError("count는 정수여야 합니다")
    if count <= 0:
        raise ValueError("count는 1 이상이어야 합니다")
    return count
```

Python은 최적화 옵션에서 `assert`를 제거할 수 있다. 따라서 보안 검사, 권한 검사, 사용자 입력 검증처럼 실행 중 반드시 수행되어야 하는 조건에 의존하지 않는다.

## 15. 안전하고 유용한 오류 메시지

좋은 오류 메시지는 다음 정보를 담는다.

- 어떤 필드나 작업이 실패했는가?
- 어떤 형식이나 범위를 기대했는가?
- 안전하게 표시할 수 있다면 어떤 값이 들어왔는가?
- 여러 항목 중 어디에서 실패했는가? 예: 행 번호

```python
raise ValueError("port는 1~65535 범위여야 합니다: 70000")
```

다음 값은 오류 메시지나 로그에 그대로 넣지 않는다.

- 비밀번호·인증 토큰·세션 쿠키
- 개인식별정보와 민감한 원문
- 전체 요청 헤더나 비밀 환경 변수

입력값을 표시해야 한다면 필요한 일부만, 길이 제한과 마스킹을 적용한다. 초급 예제에서는 공개 실습 데이터만 사용한다.

## 16. 흔한 안티패턴

### 모든 예외 무시

```python
# 피해야 할 코드
try:
    port = int(value)
except Exception:
    pass
```

실패 사실과 원인이 모두 사라지고, 이후 정의되지 않은 변수나 잘못된 상태 때문에 더 먼 곳에서 문제가 나타난다.

### 맨몸 except

```python
# 피해야 할 코드
try:
    port = int(value)
except:
    port = 0
```

프로그램 중단 신호까지 잡을 수 있고, 유효하지 않은 0을 정상 포트처럼 만들 수 있다.

### 너무 넓은 try

여러 독립 작업을 한 블록에 넣으면 예상한 실패와 프로그래밍 오류를 구분하기 어렵다. 실패할 수 있는 최소 표현만 감싼다.

### 잘못된 기본값으로 오류 숨기기

필수 데이터가 없는데 빈 문자열이나 0을 넣어 계속 진행하면 정상 데이터와 구분되지 않는다. 계약상 선택 필드인지, 필수 필드 오류인지 구분한다.

### finally에서 return

원래 예외와 반환값을 가릴 수 있다. `finally`에서는 정리만 수행한다.

### 같은 예외를 잡아 그대로 무의미하게 다시 발생

문맥 추가나 복구가 없다면 처음부터 잡지 않는다.

## 17. 미니 실습: 이벤트 행 파싱과 오류 보고

03-5에서 만든 함수 계약에 예외를 적용한다. 입력 한 행은 `ACTION IP PORT` 세 필드라고 가정한다.

### 17.1 포트 변환

```python
def parse_port(value) -> int:
    """정수 또는 정수 문자열을 1~65535 포트로 변환한다."""
    if type(value) not in {int, str}:
        raise TypeError("port는 정수 또는 정수 문자열이어야 합니다")

    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError(f"port를 정수로 변환할 수 없습니다: {value!r}") from exc

    if not 1 <= port <= 65535:
        raise ValueError(f"port는 1~65535 범위여야 합니다: {port}")
    return port
```

### 17.2 action 정규화

```python
def normalize_action(action) -> str:
    """action을 대문자로 정규화하고 허용되지 않은 값은 거부한다."""
    if not isinstance(action, str):
        raise TypeError("action은 문자열이어야 합니다")

    normalized = action.strip().upper()
    if normalized not in {"ALLOW", "DENY"}:
        raise ValueError(f"지원하지 않는 action: {normalized!r}")
    return normalized
```

### 17.3 한 행 파싱

```python
def parse_event_line(line) -> dict:
    """'ACTION IP PORT' 한 행을 검증된 이벤트 딕셔너리로 변환한다."""
    if not isinstance(line, str):
        raise TypeError("이벤트 행은 문자열이어야 합니다")

    parts = line.split()
    if len(parts) != 3:
        raise ValueError(f"필드 수는 3개여야 합니다: {len(parts)}개")

    action_text, ip, port_text = parts
    if not ip:
        raise ValueError("ip는 빈 문자열일 수 없습니다")

    return {
        "action": normalize_action(action_text),
        "ip": ip,
        "port": parse_port(port_text),
    }
```

### 17.4 여러 행 처리

잘못된 원문 전체를 오류 목록에 복사하지 않고 행 번호와 안전한 메시지만 남긴다.

```python
def parse_event_lines(lines) -> dict:
    """유효한 이벤트와 행별 오류를 분리해 반환한다."""
    events = []
    errors = []

    for line_number, line in enumerate(lines, start=1):
        try:
            event = parse_event_line(line)
        except (TypeError, ValueError) as exc:
            errors.append({
                "line": line_number,
                "type": type(exc).__name__,
                "message": str(exc),
            })
            continue

        events.append(event)

    return {"events": events, "errors": errors}
```

### 17.5 실행과 검증

```python
lines = [
    "ALLOW 10.0.0.5 443",
    "DENY 198.51.100.9 22",
    "BLOCK 203.0.113.10 80",
    "DENY 203.0.113.10 not-a-port",
    "DENY 203.0.113.10 70000",
    "",
]

result = parse_event_lines(lines)

print(result["events"])
print(result["errors"])

assert result["events"] == [
    {"action": "ALLOW", "ip": "10.0.0.5", "port": 443},
    {"action": "DENY", "ip": "198.51.100.9", "port": 22},
]
assert [error["line"] for error in result["errors"]] == [3, 4, 5, 6]
assert [error["type"] for error in result["errors"]] == [
    "ValueError",
    "ValueError",
    "ValueError",
    "ValueError",
]
```

이 실습은 한 건의 오류가 전체 분석을 중단시키지 않는 best-effort 정책이다. 반대로 모든 행이 유효해야만 다음 단계로 진행한다면 오류를 모은 뒤 `errors`가 비어 있지 않을 때 전체 작업을 중단하는 정책을 선택할 수 있다.

## 18. 예외 함수 검증 패턴

외부 테스트 도구를 배우기 전에는 작은 도우미로 예상한 예외 유형과 메시지를 확인할 수 있다.

```python
def expect_exception(expected_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except expected_type as exc:
        return exc
    else:
        raise AssertionError(f"{expected_type.__name__}이 발생하지 않았습니다")

exc = expect_exception(ValueError, parse_port, "invalid")
assert "정수로 변환" in str(exc)
assert isinstance(exc.__cause__, ValueError)

exc = expect_exception(TypeError, parse_port, True)
assert "정수 또는 정수 문자열" in str(exc)
```

예상한 유형과 다른 예외는 도우미 바깥으로 전파되므로 프로그래밍 오류를 조용히 숨기지 않는다.

## 19. 단계별 연습문제

### 19.1 오류 분류

다음 상황을 문법 오류, 실행 예외, 논리 오류로 분류한다.

1. `if value > 0` 뒤에 콜론이 없다.
2. `int("four")`를 실행한다.
3. 성인 기준을 `age > 18`로 작성해 18세를 제외한다.
4. 빈 리스트에서 `items[0]`을 읽는다.

### 19.2 traceback 읽기

2절 예에서 다음을 적는다.

1. 최종 예외 유형
2. 실제 변환이 실패한 함수
3. 호출 순서
4. 재현 입력

### 19.3 try·except·else·finally

문자열 하나를 정수로 변환한다. 실패하면 오류 메시지, 성공하면 두 배의 값, 성공·실패와 관계없이 `"완료"`를 기록한다. `"21"`과 `"abc"` 두 입력을 검증한다.

### 19.4 예외 유형 선택

`require_percentage(value)`를 작성한다.

- 정수가 아니면 `TypeError`
- 0~100 범위가 아니면 `ValueError`
- 정상이면 입력값 반환

`True`가 정수처럼 허용되지 않게 한다.

### 19.5 예외 연쇄

날짜 텍스트를 정수 연도라고 가정해 변환하는 `parse_year(text)`를 작성한다. 변환 실패 시 원래 `ValueError`를 원인으로 보존하면서 `"연도를 변환할 수 없습니다"` 문맥을 추가한다.

### 19.6 항목별 복구

`["10", "bad", "20", ""]`을 정수로 변환한다. 정상값과 오류 정보를 별도 리스트에 모으고 오류 정보에는 위치·유형·메시지를 포함한다.

### 19.7 안티패턴 수정

다음 코드의 문제를 두 가지 이상 설명하고 수정한다.

```python
try:
    value = int(user_input)
    result = 100 / value
except:
    pass
```

### 19.8 미니 실습 확장

17절에 다음 정책을 추가한다.

1. 빈 줄은 오류가 아니라 건너뛴 행으로 별도 집계한다.
2. 오류가 3개를 초과하면 이후 처리를 중단한다.
3. 반환 결과에 `skipped`와 `stopped_early`를 포함한다.
4. 정상 입력, 빈 입력, 연속 오류, 경계 포트를 검증한다.

### 19.9 전이 연습 — 센서 배치 변환

`["21.5", "bad", "", "19.8"]`을 온도 실수로 변환한다.

- 빈 문자열은 `skipped`로 집계한다.
- 변환 실패는 위치·예외 유형·메시지를 `errors`에 저장한다.
- 정상값은 `temperatures`에 저장한다.
- 한 건의 실패가 다음 항목 처리를 막지 않는 best-effort 정책을 사용한다.
- 모든 값이 유효해야 하는 fail-fast 정책이라면 무엇을 바꿀지도 설명한다.

## 20. 연습문제 정답과 해설

<details>
<summary>정답과 해설 펼치기</summary>

### 20.1 오류 분류

1. 콜론 누락은 문법 오류다.
2. 변환할 수 없는 문자열은 실행 중 `ValueError`다.
3. 실행은 되지만 경계 조건이 잘못된 논리 오류다.
4. 빈 리스트 접근은 실행 중 `IndexError`다.

### 20.2 traceback 읽기

최종 유형은 `ValueError`, 실제 실패 함수는 `convert_port()`, 호출 순서는 모듈 → `build_endpoint()` → `convert_port()`, 재현 입력은 `"not-a-port"`다.

### 20.3 try·except·else·finally

```python
def convert_and_double(text):
    log = []
    try:
        number = int(text)
    except ValueError as exc:
        log.append(f"변환 실패: {exc}")
    else:
        log.append(f"결과: {number * 2}")
    finally:
        log.append("완료")
    return log

assert convert_and_double("21")[0] == "결과: 42"
assert convert_and_double("abc")[0].startswith("변환 실패:")
assert convert_and_double("21")[-1] == "완료"
assert convert_and_double("abc")[-1] == "완료"
```

### 20.4 예외 유형 선택

```python
def require_percentage(value):
    if type(value) is not int:
        raise TypeError("percentage는 정수여야 합니다")
    if not 0 <= value <= 100:
        raise ValueError("percentage는 0~100 범위여야 합니다")
    return value

assert require_percentage(0) == 0
assert require_percentage(100) == 100
```

### 20.5 예외 연쇄

```python
def parse_year(text):
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(f"연도를 변환할 수 없습니다: {text!r}") from exc
```

### 20.6 항목별 복구

```python
values = ["10", "bad", "20", ""]
numbers = []
errors = []

for position, value in enumerate(values):
    try:
        number = int(value)
    except ValueError as exc:
        errors.append({
            "position": position,
            "type": type(exc).__name__,
            "message": str(exc),
        })
        continue
    numbers.append(number)

assert numbers == [10, 20]
assert [error["position"] for error in errors] == [1, 3]
```

### 20.7 안티패턴 수정

맨몸 `except`가 모든 실패를 숨기고, 변환 실패와 0 나눗셈을 구분하지 않으며, 실패 후 결과도 정의되지 않는다.

```python
try:
    value = int(user_input)
except ValueError as exc:
    print("정수 입력이 필요합니다:", exc)
else:
    if value == 0:
        print("0으로 나눌 수 없습니다")
    else:
        result = 100 / value
```

### 20.8 미니 실습 확장 예

```python
def parse_event_lines_limited(lines, *, max_errors=3):
    events = []
    errors = []
    skipped = 0
    stopped_early = False

    for line_number, line in enumerate(lines, start=1):
        if isinstance(line, str) and not line.strip():
            skipped += 1
            continue

        try:
            event = parse_event_line(line)
        except (TypeError, ValueError) as exc:
            errors.append({
                "line": line_number,
                "type": type(exc).__name__,
                "message": str(exc),
            })
            if len(errors) > max_errors:
                stopped_early = True
                break
            continue

        events.append(event)

    return {
        "events": events,
        "errors": errors,
        "skipped": skipped,
        "stopped_early": stopped_early,
    }
```

### 20.9 전이 연습 예시 답안

```python
raw_temperatures = ["21.5", "bad", "", "19.8"]
temperatures = []
errors = []
skipped = 0

for position, text in enumerate(raw_temperatures):
    if text == "":
        skipped += 1
        continue
    try:
        temperature = float(text)
    except ValueError as exc:
        errors.append({
            "position": position,
            "type": type(exc).__name__,
            "message": str(exc),
        })
        continue
    temperatures.append(temperature)

assert temperatures == [21.5, 19.8]
assert [error["position"] for error in errors] == [1]
assert skipped == 1
```

fail-fast 정책이라면 첫 `ValueError`를 기록한 뒤 다시 발생시키거나, 오류 목록을 확인한 호출 경계에서 전체 결과를 거부한다.

</details>

## 21. 완료 기준

다음 항목을 코드와 말로 설명하고 결과물로 확인한다.

- [ ] 문법 오류·실행 예외·논리 오류를 구분한다.
- [ ] traceback의 마지막 줄과 호출 프레임에서 원인 위치를 찾는다.
- [ ] 처리하지 않은 예외가 호출자에게 전파됨을 설명한다.
- [ ] 복구 방법에 맞는 구체적인 예외 유형을 잡는다.
- [ ] `try`, `except`, `else`, `finally`의 실행 순서를 예측한다.
- [ ] `raise`, 맨몸 `raise`, `raise ... from ...`을 구분한다.
- [ ] 정상 업무 상태는 반환하고 계약 실패는 예외로 표현한다.
- [ ] fail-fast와 best-effort 처리 정책을 요구사항에 맞게 선택한다.
- [ ] 사용자 입력 검증에 `assert`를 사용하지 않는 이유를 설명한다.
- [ ] 오류를 숨기지 않으면서 민감정보를 제외한 메시지를 작성한다.
- [ ] 센서 배치 전이 연습에서 정상·오류·건너뜀 결과를 분리한다.

## 핵심 정리

- 예외 처리는 오류를 숨기는 문법이 아니라 실패를 전달하고 복구하는 계약이다.
- traceback은 마지막 줄의 유형·메시지부터 읽고 아래쪽 호출 프레임에서 원인을 찾는다.
- 현재 위치에서 복구할 수 있는 구체적인 예외만 최소 범위로 처리한다.
- `else`는 성공 후속 처리, `finally`는 성공·실패와 관계없는 정리에 사용한다.
- 새 문맥으로 바꿀 때는 `raise ... from exc`, 같은 예외를 다시 전달할 때는 맨몸 `raise`를 사용한다.
- bool·상태 반환과 예외를 정상 결과인지 계약 실패인지에 따라 구분한다.
- 배치 처리에서는 실패를 건너뛰더라도 오류 건수와 위치를 관찰 가능하게 남긴다.
- `assert`는 내부 가정과 테스트용이며 사용자 입력·보안 검사를 대신하지 않는다.
- 오류 메시지는 해결 기준을 제공하되 비밀번호·토큰·민감한 원문을 포함하지 않는다.

---

다음 절: [03-7. 모듈과 패키지](03-7-modules-packages.md)
