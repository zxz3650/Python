# 03-9. 문법 종합 실습

03-1부터 03-8까지 학습한 값을 하나의 **메모리 기반 이벤트 검토 프로그램**으로 연결한다. 문자열 명령을 해석하고, 입력을 검증된 객체로 바꾸며, 목록·검색·집계·삭제를 수행하고, 예상 가능한 오류를 프로그램 경계에서 처리한다.

파일 저장은 [04장](../04-file-io.md), 실제 네트워크 통신은 [06장](../06-network-programming.md), HTTP 요청은 [07장](../07-http-api.md), pytest 자동화는 [09장](../09-testing-debugging.md)에서 확장한다. 이 실습에서는 03장의 Python 문법과 프로그램 구조에만 집중한다.

{% hint style="info" %}
## 🧭 종합 실습 목표

- 자료형과 문자열 메서드로 사용자 명령을 정규화한다.
- 리스트·딕셔너리·튜플로 여러 값과 결과를 표현한다.
- 조건문과 논리 연산자로 명령·입력 규칙을 판정한다.
- 반복문으로 명령 세션과 객체 목록을 처리한다.
- 함수 계약으로 파싱·실행·표현 책임을 분리한다.
- 예상 가능한 입력 실패를 구체적인 예외로 처리한다.
- 여러 파일의 패키지로 프로그램을 구조화한다.
- 데이터클래스와 일반 객체로 이벤트와 저장소를 표현한다.
- 정상·오류·경계·상태 시나리오를 assert로 검증한다.
- 요구사항, 실행 방법, 완료 기준을 다른 사람이 재현할 수 있게 기록한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | 인수 조건, 값 객체·저장소·명령 파서, 오류 복구 세션, 패키지 실행 |
| 권장 | 테스트 매트릭스, 입출력 주입, 코드 품질 점검, 평가 루브릭 |
| 심화 | 명령 확장, 저장소 정책 변경, 다른 도메인으로 구조 전이 |

## 선행 지식

03-1부터 03-8까지 완료해야 한다.

| 선행 절 | 이 프로젝트에서 사용하는 개념 |
| --- | --- |
| 03-1 | 문자열·정수·불리언, 명시적 형변환 |
| 03-2 | 문자열 정규화, 리스트·딕셔너리·튜플·집합 |
| 03-3 | 명령 분기, 입력 규칙, 논리식 |
| 03-4 | 세션 반복, 검색·집계·필터 패턴 |
| 03-5 | 작은 함수, 인자·반환값, 콜백 주입 |
| 03-6 | 구체적인 예외, 처리 경계, best-effort 정책 |
| 03-7 | 모듈·패키지, 상대 import, `python -m` |
| 03-8 | 데이터클래스, 상태 메서드, 합성 |

전용 실습은 [`notebooks/03-9-syntax-project.ipynb`](../notebooks/03-9-syntax-project.ipynb)에서 전체 시나리오로 실행한다.

## 1. 프로젝트 개요

### 1.1 문제 상황

다음 형태의 이벤트를 메모리에 등록하고 검토한다.

```text
ACTION IP PORT
```

예:

```text
ALLOW 192.0.2.10 443
DENY 198.51.100.4 22
```

이벤트는 교육용 예시 데이터이며 실제 시스템·네트워크에 연결하지 않는다.

### 1.2 지원 명령

| 명령 | 인자 | 동작 |
| --- | --- | --- |
| `add` | `ACTION IP PORT` | 검증 후 이벤트 추가 |
| `list` | 없음 | 등록 순서대로 전체 표시 |
| `find` | `ACTION` | `ALLOW` 또는 `DENY` 이벤트 검색 |
| `summary` | 없음 | 전체·ALLOW·DENY 건수 집계 |
| `remove` | `NUMBER` | 화면에 보이는 1부터 시작하는 번호로 삭제 |
| `quit` | 없음 | 세션 종료 |

명령 이름은 소문자로 정규화하고 action은 대문자로 정규화한다.

### 1.3 프로젝트 경계

이 단계에서 하지 않는 작업:

- 파일·CSV·JSON 저장
- 소켓·HTTP 연결
- 실제 방화벽·패킷 조작
- 외부 패키지 설치
- 사용자 인증이나 권한 관리
- 병렬·비동기 처리

기능을 제한해야 현재 학습 목표를 명확히 검증할 수 있다.

## 2. 인수 조건

프로그램은 다음 조건을 만족해야 한다.

### 2.1 정상 기능

- 유효한 이벤트를 등록한다.
- 목록은 `1. ACTION IP PORT` 형태로 출력한다.
- action 검색은 대소문자를 구분하지 않는다.
- 요약은 항상 `total`, `ALLOW`, `DENY`를 포함한다.
- 삭제 후 목록 번호는 다시 1부터 연속으로 표시한다.
- `quit` 뒤의 입력은 처리하지 않는다.

### 2.2 검증 규칙

- action은 `ALLOW` 또는 `DENY`만 허용한다.
- IP는 이 절에서는 비어 있지 않은 문자열이어야 한다. 정확한 IP 주소 검증은 05장에서 `ipaddress`로 확장한다.
- port는 정수 또는 정수 문자열을 받아 1~65535로 제한한다.
- `True`는 정수 포트로 허용하지 않는다.
- 동일한 action·IP·port 이벤트는 중복 등록하지 않는다.
- 삭제 번호는 정수이며 현재 목록 범위 안이어야 한다.

### 2.3 오류 정책

- 잘못된 사용자 입력 한 건은 `오류: ...` 메시지로 남기고 다음 명령을 계속 처리한다.
- `TypeError`, `ValueError`, `IndexError`처럼 복구 기준이 분명한 예외만 세션 경계에서 처리한다.
- 예상하지 못한 프로그래밍 오류를 `except Exception`으로 숨기지 않는다.
- 오류 메시지에 비밀번호·토큰 같은 민감정보를 넣지 않는다.

## 3. 먼저 설계하기

코드를 쓰기 전에 책임과 데이터 흐름을 정한다.

### 3.1 책임 분리

| 구성 요소 | 책임 | 알지 않아도 되는 것 |
| --- | --- | --- |
| `SecurityEvent` | 이벤트 필드 정규화·검증 | 명령어, 목록 저장 방식 |
| `Command` | 해석된 명령 이름과 인자 보관 | 이벤트 규칙 |
| `parse_command()` | 원문 명령을 `Command`로 변환 | 저장소 상태 |
| `EventStore` | 이벤트 추가·조회·검색·삭제·집계 | 입력·출력 방식 |
| `execute_command()` | 명령과 저장소 동작 연결 | `input()`·`print()` |
| `run_session()` | 여러 입력 처리와 오류 복구 | 객체 내부 구현 |
| `main()` | 터미널 입력·출력 연결 | 도메인 계산 세부사항 |

### 3.2 데이터 흐름

```text
원문 명령
  ↓ parse_command
Command
  ↓ execute_command
SecurityEvent / EventStore
  ↓ format_event / summary
출력 문자열 목록
```

### 3.3 패키지 구조

```text
event-review-project/
└── event_review/
    ├── __init__.py
    ├── __main__.py
    ├── app.py
    ├── commands.py
    ├── models.py
    └── store.py
```

의존 방향:

```text
__main__ → app → commands
               → store → models
```

아래 계층이 위 계층의 터미널 입출력을 import하지 않게 한다.

### 3.4 학습자용 TODO 골격

4절 이후의 완성 코드를 보기 전에 아래 계약만 복사해 먼저 구현한다. 각 `NotImplementedError`를 하나씩 제거하고, 해당 단계 검증을 통과한 뒤 다음 책임으로 이동한다.

```python
# models.py
def parse_port(value):
    raise NotImplementedError


class SecurityEvent:
    # TODO: dataclass, 정규화, 검증, endpoint()
    pass


# store.py
class EventStore:
    def add(self, event):
        raise NotImplementedError

    def list_all(self):
        raise NotImplementedError

    def find_by_action(self, action):
        raise NotImplementedError

    def remove(self, number):
        raise NotImplementedError

    def summary(self):
        raise NotImplementedError


# commands.py
class Command:
    # TODO: 변경 불가능한 데이터클래스
    pass


def parse_command(text):
    raise NotImplementedError


# app.py
def execute_command(store, command):
    raise NotImplementedError


def process_input(store, text):
    raise NotImplementedError


def run_session(commands, store=None):
    raise NotImplementedError


def main(input_fn=input, output_fn=print):
    raise NotImplementedError
```

구현 순서:

1. 값 한 건의 정규화와 경계값
2. 여러 값의 상태와 중복 정책
3. 문자열 명령의 구조화
4. 명령과 상태 변경 연결
5. 오류 한 건 뒤 계속 실행
6. 터미널 입출력 주입

완성 코드를 그대로 옮기기 전에 현재 실패가 어느 계약에서 발생했는지 한 문장으로 기록한다.

## 4. 1단계: 이벤트 값 객체

`event_review/models.py`를 작성한다.

```python
# event_review/models.py
from dataclasses import dataclass


def parse_port(value):
    if type(value) not in {int, str}:
        raise TypeError("port는 정수 또는 정수 문자열이어야 합니다")

    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError("port를 정수로 변환할 수 없습니다") from exc

    if not 1 <= port <= 65535:
        raise ValueError("port는 1~65535 범위여야 합니다")
    return port


@dataclass(frozen=True)
class SecurityEvent:
    action: str
    ip: str
    port: int

    def __post_init__(self):
        if not isinstance(self.action, str):
            raise TypeError("action은 문자열이어야 합니다")
        action = self.action.strip().upper()
        if action not in {"ALLOW", "DENY"}:
            raise ValueError("action은 ALLOW 또는 DENY여야 합니다")

        if not isinstance(self.ip, str):
            raise TypeError("ip는 문자열이어야 합니다")
        ip = self.ip.strip()
        if not ip:
            raise ValueError("ip는 비어 있을 수 없습니다")

        port = parse_port(self.port)

        object.__setattr__(self, "action", action)
        object.__setattr__(self, "ip", ip)
        object.__setattr__(self, "port", port)

    def endpoint(self):
        return f"{self.ip}:{self.port}"
```

### 4.1 단계 검증

```python
event = SecurityEvent(" allow ", " 192.0.2.10 ", "443")

assert event == SecurityEvent("ALLOW", "192.0.2.10", 443)
assert event.endpoint() == "192.0.2.10:443"
```

검증할 오류:

- `SecurityEvent("BLOCK", "192.0.2.10", 443)`
- `SecurityEvent("ALLOW", "", 443)`
- `SecurityEvent("ALLOW", "192.0.2.10", 0)`
- `SecurityEvent("ALLOW", "192.0.2.10", True)`

## 5. 2단계: 저장소 객체

`event_review/store.py`를 작성한다. 이벤트 목록은 `EventStore` 인스턴스마다 별도로 가져야 한다.

```python
# event_review/store.py
from dataclasses import dataclass, field

from .models import SecurityEvent


@dataclass
class EventStore:
    _events: list[SecurityEvent] = field(default_factory=list)

    def add(self, event):
        if not isinstance(event, SecurityEvent):
            raise TypeError("SecurityEvent만 추가할 수 있습니다")
        if event in self._events:
            raise ValueError("동일한 이벤트가 이미 있습니다")
        self._events.append(event)

    def list_all(self):
        return tuple(self._events)

    def find_by_action(self, action):
        if not isinstance(action, str):
            raise TypeError("action은 문자열이어야 합니다")
        normalized = action.strip().upper()
        if normalized not in {"ALLOW", "DENY"}:
            raise ValueError("action은 ALLOW 또는 DENY여야 합니다")
        return tuple(
            event
            for event in self._events
            if event.action == normalized
        )

    def remove(self, number):
        if type(number) is not int:
            raise TypeError("삭제 번호는 정수여야 합니다")
        if not 1 <= number <= len(self._events):
            raise IndexError("삭제 번호가 목록 범위를 벗어났습니다")
        return self._events.pop(number - 1)

    def summary(self):
        counts = {"total": len(self._events), "ALLOW": 0, "DENY": 0}
        for event in self._events:
            counts[event.action] += 1
        return counts
```

`list_all()`이 내부 리스트가 아니라 튜플을 반환하므로 호출자가 `append()`로 저장소 상태를 우회 변경하지 못한다.

### 5.1 단계 검증

```python
store = EventStore()
allow_event = SecurityEvent("ALLOW", "192.0.2.10", 443)
deny_event = SecurityEvent("DENY", "198.51.100.4", 22)

store.add(allow_event)
store.add(deny_event)

assert store.list_all() == (allow_event, deny_event)
assert store.find_by_action("allow") == (allow_event,)
assert store.summary() == {"total": 2, "ALLOW": 1, "DENY": 1}
assert store.remove(2) == deny_event
assert store.summary() == {"total": 1, "ALLOW": 1, "DENY": 0}
```

## 6. 3단계: 명령 파싱

`event_review/commands.py`를 작성한다.

```python
# event_review/commands.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    name: str
    arguments: tuple[str, ...] = ()


COMMAND_ARGUMENT_COUNTS = {
    "add": 3,
    "list": 0,
    "find": 1,
    "summary": 0,
    "remove": 1,
    "quit": 0,
}


def parse_command(text):
    if not isinstance(text, str):
        raise TypeError("명령은 문자열이어야 합니다")

    parts = text.split()
    if not parts:
        raise ValueError("명령이 비어 있습니다")

    name = parts[0].lower()
    arguments = tuple(parts[1:])

    if name not in COMMAND_ARGUMENT_COUNTS:
        raise ValueError(f"지원하지 않는 명령: {name}")

    expected = COMMAND_ARGUMENT_COUNTS[name]
    if len(arguments) != expected:
        raise ValueError(
            f"{name} 명령은 인자 {expected}개가 필요합니다: "
            f"현재 {len(arguments)}개"
        )

    return Command(name=name, arguments=arguments)
```

### 6.1 단계 검증

```python
assert parse_command(" ADD allow 192.0.2.10 443 ") == Command(
    "add",
    ("allow", "192.0.2.10", "443"),
)
assert parse_command("summary") == Command("summary")
assert parse_command("quit") == Command("quit")
```

## 7. 4단계: 출력 형식과 명령 실행

`event_review/app.py`의 핵심 함수를 작성한다. `execute_command()`는 직접 출력하지 않고 출력할 문자열 목록을 반환한다.

```python
# event_review/app.py 일부
from .commands import Command, parse_command
from .models import SecurityEvent
from .store import EventStore


def format_event(number, event):
    return f"{number}. {event.action} {event.ip} {event.port}"


def format_events(events):
    if not events:
        return ["목록이 비어 있습니다"]
    return [
        format_event(number, event)
        for number, event in enumerate(events, start=1)
    ]


def format_summary(summary):
    return (
        f"total={summary['total']} "
        f"ALLOW={summary['ALLOW']} "
        f"DENY={summary['DENY']}"
    )


def execute_command(store, command):
    if not isinstance(store, EventStore):
        raise TypeError("store는 EventStore여야 합니다")
    if not isinstance(command, Command):
        raise TypeError("command는 Command여야 합니다")

    if command.name == "add":
        action, ip, port = command.arguments
        event = SecurityEvent(action, ip, port)
        store.add(event)
        return True, [f"추가: {event.action} {event.endpoint()}"]

    if command.name == "list":
        return True, format_events(store.list_all())

    if command.name == "find":
        (action,) = command.arguments
        return True, format_events(store.find_by_action(action))

    if command.name == "summary":
        return True, [format_summary(store.summary())]

    if command.name == "remove":
        (number_text,) = command.arguments
        try:
            number = int(number_text)
        except ValueError as exc:
            raise ValueError("삭제 번호를 정수로 변환할 수 없습니다") from exc
        removed = store.remove(number)
        return True, [f"삭제: {removed.action} {removed.endpoint()}"]

    if command.name == "quit":
        return False, ["종료합니다"]

    raise RuntimeError(f"처리되지 않은 명령: {command.name}")
```

마지막 `RuntimeError`는 사용자 입력 오류가 아니라 파서와 실행기의 지원 명령이 불일치하는 프로그래밍 오류를 드러낸다.

## 8. 5단계: 세션 경계와 오류 복구

여러 명령을 순서대로 실행하는 순수한 실습 함수를 먼저 만든다.

```python
# event_review/app.py 일부
def process_input(store, text):
    command = parse_command(text)
    return execute_command(store, command)


def run_session(commands, store=None):
    if store is None:
        store = EventStore()

    outputs = []
    for text in commands:
        try:
            keep_running, messages = process_input(store, text)
        except (TypeError, ValueError, IndexError) as exc:
            outputs.append(f"오류: {exc}")
            continue

        outputs.extend(messages)
        if not keep_running:
            break

    return store, outputs
```

오류가 발생해도 다음 명령으로 진행하는 best-effort 세션 정책이다. `quit`은 정상 종료 신호이므로 예외로 표현하지 않는다.

### 8.1 대표 시나리오

```python
commands = [
    "list",
    "add allow 192.0.2.10 443",
    "add DENY 198.51.100.4 22",
    "add ALLOW 192.0.2.10 443",  # 중복
    "add BLOCK 203.0.113.8 80",   # 잘못된 action
    "add ALLOW 203.0.113.8 https",  # 잘못된 port
    "find allow",
    "summary",
    "remove 2",
    "summary",
    "unknown",
    "quit",
    "add DENY 203.0.113.9 53",  # quit 뒤라 실행되지 않음
]

store, outputs = run_session(commands)

assert store.summary() == {"total": 1, "ALLOW": 1, "DENY": 0}
assert outputs[0] == "목록이 비어 있습니다"
assert outputs[-1] == "종료합니다"
assert sum(output.startswith("오류:") for output in outputs) == 4
```

## 9. 6단계: 터미널 입출력 연결

핵심 함수는 그대로 두고 `input()`과 `print()`을 가장 바깥에서만 연결한다.

```python
# event_review/app.py 일부
def main(input_fn=input, output_fn=print):
    store = EventStore()
    output_fn("명령: add/list/find/summary/remove/quit")

    while True:
        text = input_fn("event> ")

        try:
            keep_running, messages = process_input(store, text)
        except (TypeError, ValueError, IndexError) as exc:
            output_fn(f"오류: {exc}")
            continue

        for message in messages:
            output_fn(message)

        if not keep_running:
            return 0
```

`input_fn`과 `output_fn`을 인자로 받으면 실제 터미널 없이도 입력과 출력을 대체해 검증할 수 있다. 기본값은 각각 `input`, `print`다.

### 9.1 입력·출력 주입 검증

```python
scripted_inputs = iter([
    "add ALLOW 192.0.2.10 443",
    "summary",
    "quit",
])
captured = []


def fake_input(prompt):
    captured.append(prompt)
    return next(scripted_inputs)


exit_code = main(input_fn=fake_input, output_fn=captured.append)

assert exit_code == 0
assert "total=1 ALLOW=1 DENY=0" in captured
assert captured[-1] == "종료합니다"
```

## 10. 7단계: 패키지 공개 API와 진입점

### 10.1 `__init__.py`

```python
# event_review/__init__.py
from .app import process_input, run_session
from .models import SecurityEvent
from .store import EventStore

__all__ = ["EventStore", "SecurityEvent", "process_input", "run_session"]
```

### 10.2 `__main__.py`

```python
# event_review/__main__.py
from .app import main


raise SystemExit(main())
```

프로젝트 루트에서 실행한다.

```bash
python -m event_review
```

패키지 내부 파일인 `event_review/app.py`를 직접 실행하지 않는다.

## 11. 테스트 매트릭스

한두 개 정상 입력만 실행해서는 완료가 아니다.

| 분류 | 입력·상태 | 기대 결과 |
| --- | --- | --- |
| 정상 | `add ALLOW 192.0.2.10 443` | 정규화 후 추가 |
| 정상 | `find allow` | ALLOW만 반환 |
| 정상 | 빈 저장소 `summary` | 모두 0 |
| 경계 | port 1 | 허용 |
| 경계 | port 65535 | 허용 |
| 오류 | port 0·65536 | `ValueError` |
| 오류 | port `https` | 원인 보존 `ValueError` |
| 오류 | port `True` | `TypeError` |
| 오류 | action `BLOCK` | `ValueError` |
| 오류 | 빈 명령 | 오류 메시지 후 계속 |
| 오류 | 인자 부족·초과 | 필요한 개수 설명 |
| 상태 | 동일 이벤트 두 번 추가 | 중복 거부 |
| 상태 | 빈 목록에서 remove | 범위 오류 |
| 상태 | 삭제 후 list | 번호 재정렬 |
| 종료 | quit 이후 명령 | 실행하지 않음 |

### 11.1 예외 검증 도우미

```python
def expect_exception(expected_type, function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except expected_type as exc:
        return exc
    except Exception as exc:
        raise AssertionError(
            f"{expected_type.__name__} 대신 {type(exc).__name__} 발생"
        ) from exc
    raise AssertionError(f"{expected_type.__name__}이 발생하지 않음")
```

### 11.2 핵심 검증 예

```python
assert SecurityEvent("ALLOW", "192.0.2.10", 1).port == 1
assert SecurityEvent("DENY", "192.0.2.10", 65535).port == 65535

expect_exception(ValueError, SecurityEvent, "ALLOW", "192.0.2.10", 0)
expect_exception(ValueError, SecurityEvent, "ALLOW", "192.0.2.10", 65536)
expect_exception(TypeError, SecurityEvent, "ALLOW", "192.0.2.10", True)
expect_exception(ValueError, parse_command, "add ALLOW 192.0.2.10")
expect_exception(ValueError, parse_command, "unsupported")
```

## 12. 단계별 작업 순서

한 번에 전체 정답을 복사하지 않고 각 단계의 검증을 통과한 뒤 다음으로 간다.

### 단계 A: 모델

1. `parse_port()`를 작성한다.
2. `SecurityEvent`를 작성한다.
3. 정상·타입·값·경계 입력을 검증한다.

완료 신호: 유효하지 않은 이벤트 인스턴스가 생성되지 않는다.

### 단계 B: 컬렉션과 상태

1. `EventStore.add()`를 작성한다.
2. `list_all()`, `find_by_action()`, `summary()`를 작성한다.
3. 중복과 삭제 범위를 검증한다.

완료 신호: 내부 목록을 직접 노출하지 않고 모든 상태 변경이 메서드를 거친다.

### 단계 C: 명령

1. 지원 명령과 인자 수를 표로 정의한다.
2. `parse_command()`를 작성한다.
3. 빈 입력·미지원 명령·인자 수 오류를 검증한다.

완료 신호: 원문 문자열이 항상 유효한 `Command`이거나 구체적 예외가 된다.

### 단계 D: 실행 연결

1. 출력 포맷 함수를 작성한다.
2. `execute_command()`를 작성한다.
3. 각 명령이 저장소 상태와 출력에 미치는 영향을 검증한다.

완료 신호: `execute_command()` 안에 `input()`이나 `print()`이 없다.

### 단계 E: 세션과 패키지

1. `run_session()`으로 스크립트 입력을 실행한다.
2. 오류 후 계속과 quit 종료를 검증한다.
3. 모듈을 분리하고 상대 import를 적용한다.
4. `python -m event_review`로 실행한다.

완료 신호: import해도 대화형 루프가 자동 실행되지 않는다.

## 13. 코드 품질 점검

### 이름

- 클래스는 `SecurityEvent`, `EventStore`처럼 명사형 CamelCase를 사용한다.
- 함수와 변수는 `parse_command`, `keep_running`처럼 snake_case를 사용한다.
- `data`, `item`, `temp` 같은 모호한 이름은 범위가 작을 때만 사용한다.

### 함수

- 함수 하나가 파싱·상태 변경·출력을 모두 하지 않는다.
- 반환값과 예외 조건을 설명할 수 있다.
- 숨겨진 전역 목록 대신 인자와 객체 상태를 사용한다.

### 예외

- 맨몸 `except`와 `except Exception: pass`를 사용하지 않는다.
- 복구 가능한 입력 오류만 사용자 경계에서 처리한다.
- 변환 예외에 새 문맥을 붙일 때 원인을 보존한다.

### 클래스

- 클래스 변수로 변경 가능한 인스턴스 상태를 공유하지 않는다.
- 데이터클래스의 리스트 기본값은 `default_factory`를 사용한다.
- 상속이 필요 없는 관계에 상속을 사용하지 않는다.

### 모듈

- 서로 순환 import하지 않는다.
- 모듈 import 시 입력 루프가 시작되지 않는다.
- 실행은 패키지 루트에서 `python -m`을 사용한다.

## 14. 흔한 실패와 진단

### `attempted relative import with no known parent package`

패키지 내부 파일을 직접 실행했는지 확인한다. 프로젝트 루트에서 `python -m event_review`로 실행한다.

### 테스트할 때 `input()`에서 멈춤

핵심 로직 안에서 직접 `input()`을 호출하지 않는다. `run_session()`이나 주입한 `input_fn`을 사용한다.

### 중복 이벤트가 계속 추가됨

`SecurityEvent`의 데이터클래스 값 동등성과 `event in self._events`를 확인한다.

### 오류 뒤 세션이 종료됨

예상 가능한 입력 예외를 명령 단위로 처리하는지, try 범위가 반복 전체가 아닌 현재 명령인지 확인한다.

### 삭제 번호가 한 칸씩 어긋남

사용자 번호는 1부터, 리스트 인덱스는 0부터다. 범위를 먼저 확인한 뒤 `number - 1`을 사용한다.

### `True`가 포트 1로 허용됨

`bool`이 `int`의 하위 타입이므로 `isinstance(True, int)` 대신 이 계약에서는 `type(value) is int` 또는 허용 타입의 정확한 집합을 사용한다.

## 15. 평가 루브릭

| 영역 | 배점 | 확인 기준 |
| --- | ---: | --- |
| 기능 완성 | 25 | 6개 명령과 종료 동작 |
| 데이터·검증 | 15 | action·IP·port·중복·번호 규칙 |
| 조건·반복·자료구조 | 10 | 분기·세션·검색·집계 패턴 |
| 함수 계약 | 10 | 파싱·실행·표현 분리 |
| 예외 처리 | 10 | 구체적 유형, 명령별 복구, 원인 보존 |
| 클래스 설계 | 10 | 값 객체, 저장소 상태, 합성 |
| 모듈 구조 | 10 | 단방향 의존성, `python -m` 실행 |
| 검증 | 5 | 정상·오류·경계·상태 시나리오 |
| 문서화 | 5 | 실행 방법·규칙·완료 기준 |
| 합계 | 100 | 80점 이상이며 필수 기능이 모두 동작하면 완료 |

오류를 숨겨 우연히 실행되는 프로그램은 높은 점수를 받을 수 없다. 각 선택을 설명하고 재현할 수 있어야 한다.

## 16. 확장 과제

### 16.1 03장 범위 확장

- `find port 443` 형태의 포트 검색
- 중복 이벤트를 거부하지 않고 발생 횟수를 집계하는 정책
- `clear` 명령과 확인 단계
- 명령 별칭 `ls`, `rm`, `exit`
- 정렬 기준 action·port 선택
- 읽기 전용 `EventStore` 스냅샷 비교

### 16.2 이후 장 연결

- 04장: 이벤트를 CSV·JSON으로 저장하고 다시 읽기
- 05장: `ipaddress`, 정규식, 날짜·시간, pandas 집계
- 06장: 로컬 TCP에서 이벤트 메시지 수신
- 07장: 로컬 HTTP API 응답 검증
- 09장: assert 시나리오를 pytest 테스트로 분리
- 10장: 설정·로깅·의존성 구조화

현재 절에서 이후 장 기능을 미리 구현하지 않는다. 확장 지점을 설명할 수 있으면 충분하다.

## 17. 전이 실습: 다른 주제로 바꾸기

같은 구조를 유지하면서 도메인만 바꿀 수 있다.

| 이벤트 검토 | 연락처 | 도서 | 작업 | 재고 |
| --- | --- | --- | --- | --- |
| action | group | category | status | category |
| ip | name | title | title | product |
| port | phone | year | priority | quantity |
| `EventStore` | `ContactBook` | `Library` | `TaskBoard` | `Inventory` |
| action 검색 | group 검색 | 제목 검색 | 상태 검색 | 분류 검색 |

도메인을 바꿔도 다음 구조는 유지한다.

```text
원문 입력 → 파싱·검증 → 값 객체 → 저장소 → 검색·집계 → 출력
```

다음 중 하나를 선택해 이벤트 검토 큐의 코드를 복사하지 않고 같은 설계 원칙으로 다시 작성한다.

1. 값 객체의 필드와 유효성 규칙을 정의한다.
2. 지원 명령 6개와 각 인자 개수를 정한다.
3. 정상·오류·경계·상태 입력을 각각 한 개 이상 만든다.
4. 기존 100점 루브릭에서 도메인 이름만 바꾸고 같은 기준으로 평가한다.
5. 이벤트 검토 구현과 동일한 점, 달라진 점을 각각 두 가지 설명한다.

## 18. 최종 제출물

- `event_review/` 패키지 전체
- 실행 방법과 지원 명령을 설명한 README
- 정상·오류·경계 시나리오 결과
- 설계 선택 설명: 딕셔너리 대신 객체를 쓴 이유, 합성을 쓴 이유
- 아직 구현하지 않은 04장 이후 확장 목록

비밀키, 실제 공격 대상, 개인 데이터, 운영 시스템 로그는 제출물에 포함하지 않는다.

## 19. 완료 기준

다음 항목을 모두 확인한다.

- [ ] 03-1~03-8 개념이 최소 한 번 이상 실제 코드에 사용된다.
- [ ] `add`, `list`, `find`, `summary`, `remove`, `quit`가 동작한다.
- [ ] 정상·오류·경계·상태 입력을 구분해 검증한다.
- [ ] 잘못된 명령 한 건이 전체 세션을 종료시키지 않는다.
- [ ] quit 이후 명령을 처리하지 않는다.
- [ ] 내부 이벤트 목록을 호출자가 직접 변경할 수 없게 한다.
- [ ] 변경 가능한 기본값을 인스턴스끼리 공유하지 않는다.
- [ ] 파싱·상태·출력·입력 책임이 함수와 모듈로 분리되어 있다.
- [ ] import만으로 대화형 프로그램이 시작되지 않는다.
- [ ] 프로젝트 루트에서 `python -m event_review`로 실행된다.
- [ ] 전체 시나리오를 수동 입력 없이 다시 실행할 수 있다.
- [ ] 구현하지 않은 파일·네트워크 기능이 다음 장 범위임을 설명한다.
- [ ] 같은 구조를 연락처·도서·작업·재고 중 하나에 전이해 설명한다.

## 핵심 정리

- 종합 실습의 목표는 많은 기능이 아니라 이미 배운 개념을 명확한 책임으로 연결하는 것이다.
- 원문 입력은 파싱하고, 도메인 객체는 유효한 상태를 지키며, 저장소는 여러 객체의 상태를 관리한다.
- 입력·출력을 핵심 계산에서 분리하면 자동 시나리오 검증이 가능하다.
- 사용자 오류는 명령 단위로 복구하되 프로그래밍 오류를 넓은 except로 숨기지 않는다.
- 모듈 의존 방향을 단순하게 유지하고 패키지는 `python -m`으로 실행한다.
- 파일과 네트워크가 없어도 자료형·조건·반복·함수·예외·모듈·클래스를 모두 검증할 수 있다.
- 다음 장부터 이 메모리 모델에 저장·파싱·통신 기능을 한 층씩 추가한다.

---

다음 장: [04. 파일 입출력과 데이터 형식](../04-file-io.md)
