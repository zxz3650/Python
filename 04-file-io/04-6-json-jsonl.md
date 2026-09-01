# 04-6. JSON·JSON Lines와 직렬화 검증

JSON은 문자열, 숫자, 불리언, `null`, 배열과 객체를 표현하는 텍스트 데이터 형식이다. 최상위 값은 객체나 배열뿐 아니라 JSON이 허용하는 단일 값일 수도 있지만, 업무 레코드를 교환할 때는 객체와 배열을 주로 사용한다.

Python 객체를 JSON 텍스트로 바꾸는 과정을 **직렬화(serialization)**, JSON 텍스트를 Python 값으로 바꾸는 과정을 **역직렬화(deserialization)**라고 한다. 파싱에 성공했다는 사실은 데이터의 필드·자료형·범위가 업무 규칙에 맞다는 뜻이 아니므로 변환 뒤 별도 검증이 필요하다.

{% hint style="info" %}
### 🧭 학습 목표

- Python 자료형과 JSON 값의 대응 관계를 설명한다.
- `dump()`·`load()`와 `dumps()`·`loads()`를 구분한다.
- UTF-8 JSON 파일을 읽고 쓰며 직렬화할 수 없는 값을 처리한다.
- 형식 오류, 중복 객체 키와 비표준 숫자를 구분해 처리한다.
- 파싱 결과의 필수 키·자료형·값 범위를 검증한다.
- JSON과 JSON Lines의 사용 목적과 메모리 특성을 비교한다.
- 입력 크기 제한과 신뢰하지 않는 역직렬화 데이터의 위험을 설명한다.
{% endhint %}

## 선행 지식

딕셔너리·리스트, 예외 처리와 [04-3](04-3-text-files.md)·[04-4](04-4-encoding-binary.md)의 파일·인코딩 개념을 이해해야 한다.

전용 실습은 [`notebooks/04-6-json-jsonl.ipynb`](../notebooks/04-6-json-jsonl.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

다음 Python 값이 JSON으로 직렬화된 뒤 다시 역직렬화되면 어떤 자료형이 되는지 예상한다.

```python
source = {
    "position": (10, 20),
    "enabled": True,
    "note": None,
}
```

다음 질문에 답해 본다.

1. JSON 객체의 키는 어떤 자료형이어야 하는가?
2. `json.loads()`가 성공하면 필수 필드도 모두 올바르다고 볼 수 있는가?
3. 하나의 JSON 파일과 JSON Lines는 여러 레코드를 어떻게 다르게 저장하는가?
4. 신뢰하지 않는 `pickle` 파일을 `pickle.load()`하면 왜 위험한가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. Python과 JSON 자료형 대응

| Python | JSON | 주의점 |
| --- | --- | --- |
| `dict` | object | JSON 객체 키는 문자열이어야 한다. |
| `list`, `tuple` | array | 역직렬화하면 모두 `list`가 된다. |
| `str` | string | 파일 인코딩과 JSON 문자열 이스케이프는 별개다. |
| `int`, `float` | number | 상호 운용 범위와 비표준 `NaN`을 확인한다. |
| `True`, `False` | `true`, `false` | JSON에서는 소문자를 사용한다. |
| `None` | `null` | 의미 없는 값과 누락된 키를 구분한다. |

Python의 `json` 인코더는 일부 비문자열 딕셔너리 키를 문자열로 바꾸지만 원래 키 자료형은 복원되지 않는다. 교환용 JSON의 객체 키는 처음부터 문자열로 제한한다.

## 2. JSON 문자열 변환

```python
import json

record = {
    "name": "Alice",
    "active": True,
    "score": 91,
    "tags": ["python", "file"],
}

text = json.dumps(
    record,
    ensure_ascii=False,
    indent=2,
)
restored = json.loads(text)

print(text)
print(restored == record)  # True
```

- `dumps()`는 Python 값을 JSON **문자열**로 변환한다.
- `loads()`는 JSON **문자열**을 Python 값으로 변환한다.
- `ensure_ascii=False`는 한글을 `\uXXXX` 형태로 강제 이스케이프하지 않는다.
- `indent=2`는 사람이 읽기 쉬운 여러 줄 형식으로 출력한다.

함수 이름 끝의 `s`는 문자열(string)을 대상으로 한다고 기억할 수 있다.

## 3. JSON 파일 읽기와 쓰기

`dump()`와 `load()`는 열린 텍스트 파일 객체를 대상으로 한다.

```python
from pathlib import Path

lab_dir = Path("file-lab/json").resolve()
lab_dir.mkdir(parents=True, exist_ok=True)
path = lab_dir / "record.json"

with path.open("w", encoding="utf-8") as file:
    json.dump(
        record,
        file,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )
    file.write("\n")

with path.open("r", encoding="utf-8") as file:
    loaded = json.load(file)

print(loaded)
```

`json.dump()`는 마지막 줄바꿈을 자동으로 추가하지 않는다. 사람이 읽는 파일과 명령줄 도구의 호환성을 위해 예제에서는 `\n`을 명시적으로 쓴다. 한 JSON 문서에는 하나의 최상위 JSON 값만 저장한다.

## 4. JSON 형식 오류 읽기

JSON은 마지막 쉼표, 작은따옴표로 감싼 문자열과 주석을 허용하지 않는다.

```python
invalid = '{"name": "Alice",}'

try:
    json.loads(invalid)
except json.JSONDecodeError as exc:
    print("행:", exc.lineno)
    print("열:", exc.colno)
    print("문자 위치:", exc.pos)
    print("원인:", exc.msg)
```

외부 사용자에게는 필요한 위치와 일반화한 원인을 보여 주고, 토큰·개인정보가 포함될 수 있는 입력 전문을 오류 메시지에 그대로 노출하지 않는다.

## 5. 중복 키와 비표준 숫자 거부하기

Python의 기본 `json.loads()`는 같은 객체 키가 반복되면 마지막 값을 남긴다. 또한 표준 JSON 숫자가 아닌 `NaN`, `Infinity`, `-Infinity`를 기본적으로 허용한다. 설정·권한·금액처럼 무결성이 중요한 입력은 이러한 값에 명시적인 정책을 적용한다.

```python
def reject_nonstandard_constant(value):
    raise ValueError(f"표준 JSON 숫자가 아닙니다: {value}")


def reject_duplicate_keys(pairs):
    result = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(f"중복 JSON 키입니다: {key}")
        result[key] = value

    return result


def loads_strict(text):
    return json.loads(
        text,
        parse_constant=reject_nonstandard_constant,
        object_pairs_hook=reject_duplicate_keys,
    )


def load_strict(file):
    return json.load(
        file,
        parse_constant=reject_nonstandard_constant,
        object_pairs_hook=reject_duplicate_keys,
    )
```

`json.load()`에도 같은 키워드 인수를 전달할 수 있다. 따라서 문자열 입력에는 `loads_strict()`, 열린 파일 객체에는 `load_strict()`를 사용해 동일한 입력 정책을 적용한다.

다음 입력은 모두 거부되어야 한다.

```python
samples = [
    '{"role": "user", "role": "admin"}',
    '{"score": NaN}',
]

for sample in samples:
    try:
        loads_strict(sample)
    except (json.JSONDecodeError, ValueError) as exc:
        print("JSON 입력 거부:", exc)
```

중복 키 처리 방식은 구현마다 다를 수 있으므로 입력 순서에 기대지 않는다. 중복을 허용해야 하는 특별한 요구사항이 없다면 검증 단계에서 거부하는 편이 명확하다.

## 6. 직렬화할 수 없는 값과 왕복 변환

`datetime`, `Path`, `set`, 사용자 정의 객체는 기본 JSON 자료형이 아니므로 바로 직렬화할 수 없다.

```python
from datetime import datetime, timezone

data = {
    "created_at": datetime.now(timezone.utc),
}

try:
    json.dumps(data)
except TypeError as exc:
    print("직렬화 실패:", exc)

data["created_at"] = data["created_at"].isoformat()
print(json.dumps(data))
```

임의 객체를 무조건 문자열로 바꾸는 `default=str`은 자료형 오류를 숨기고 형식을 실행 환경에 의존하게 만들 수 있다. 날짜·경로·집합은 교환 계약에서 표현 형식을 정한 뒤 명시적으로 변환한다.

직렬화와 역직렬화를 거쳤다고 원래 Python 자료형이 항상 그대로 복원되는 것은 아니다.

```python
source = {"position": (10, 20)}
restored = json.loads(json.dumps(source))

print(restored)                    # {'position': [10, 20]}
print(type(restored["position"])) # <class 'list'>
```

정수 키 `1`과 문자열 키 `"1"`처럼 JSON으로 바꿀 때 같은 문자열 키가 되는 값은 데이터 충돌을 만들 수 있다. 객체 키를 문자열로 제한하고 직렬화 전에도 스키마를 검증한다.

## 7. 파싱 결과 검증하기

JSON 파싱 성공과 업무 데이터의 유효성은 별개다. 다음 검증 함수는 필수 키, 알 수 없는 키, 자료형, 빈 값과 숫자 범위를 확인한 뒤 새 딕셔너리를 반환한다.

```python
import math

REQUIRED_KEYS = {"name", "active", "score", "tags"}


def validate_record(data):
    if not isinstance(data, dict):
        raise TypeError("최상위 값은 object여야 합니다")

    keys = set(data)
    missing = REQUIRED_KEYS - keys
    unknown = keys - REQUIRED_KEYS

    if missing:
        raise ValueError(f"필수 키 누락: {sorted(missing)}")
    if unknown:
        raise ValueError(f"알 수 없는 키: {sorted(unknown)}")

    name = data["name"]
    active = data["active"]
    score = data["score"]
    tags = data["tags"]

    if not isinstance(name, str):
        raise TypeError("name은 문자열이어야 합니다")
    if not name.strip():
        raise ValueError("name은 비어 있을 수 없습니다")
    if type(active) is not bool:
        raise TypeError("active는 불리언이어야 합니다")
    if type(score) not in (int, float):
        raise TypeError("score는 숫자여야 합니다")
    if isinstance(score, float) and not math.isfinite(score):
        raise ValueError("score는 유한한 수여야 합니다")
    if not 0 <= score <= 100:
        raise ValueError("score는 0부터 100 사이여야 합니다")
    if not isinstance(tags, list):
        raise TypeError("tags는 배열이어야 합니다")
    if any(not isinstance(tag, str) for tag in tags):
        raise TypeError("모든 태그는 문자열이어야 합니다")
    if any(not tag.strip() for tag in tags):
        raise ValueError("태그는 비어 있을 수 없습니다")

    return {
        "name": name.strip(),
        "active": active,
        "score": score,
        "tags": [tag.strip() for tag in tags],
    }


validated = validate_record(loads_strict(text))
print(validated)
```

`bool`은 Python에서 `int`의 하위 유형이므로 숫자 필드를 검사할 때 `isinstance(True, int)`만 사용하면 `True`가 숫자로 통과할 수 있다. 예제는 `type(score) in (int, float)`로 이를 구분한다.

## 8. 엄격한 JSON 출력

Python의 기본 JSON 인코더는 `NaN`과 무한대를 출력할 수 있지만 이 값들은 표준 JSON 숫자가 아니다. 다른 시스템과 교환하는 JSON은 `allow_nan=False`로 비표준 출력을 막는다.

```python
invalid_output = {"score": float("nan")}

try:
    json.dumps(invalid_output, allow_nan=False)
except ValueError as exc:
    print("JSON 숫자 검증 실패:", exc)
```

큰 정수와 부동소수점의 정밀도 범위는 상대 시스템과 다를 수 있다. 금액·식별자처럼 정확한 값은 교환 계약에서 범위와 문자열 사용 여부를 정한다.

## 9. JSON Lines 읽기와 쓰기

JSON Lines는 한 물리 행에 독립된 JSON 값 하나를 저장하는 형식이다. 여러 이벤트와 로그를 순차 처리하고 오류 위치를 행별로 격리하기 좋다. 이 과정에서는 UTF-8과 `\n` 줄바꿈을 사용하고 BOM은 넣지 않는다. 빈 행은 유효한 JSON 값이 아니며, 보기 좋게 만들기 위한 여러 줄 들여쓰기를 사용하지 않는다.

```python
events = [
    {"username": "alice", "result": "FAIL"},
    {"username": "alice", "result": "SUCCESS"},
]

events_path = lab_dir / "events.jsonl"

with events_path.open("w", encoding="utf-8") as file:
    for event in events:
        line = json.dumps(
            event,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        file.write(line + "\n")
```

JSON Lines의 이벤트 스키마는 앞 절의 일반 레코드 스키마와 다르므로 전용 검증 함수를 사용한다.

```python
ALLOWED_RESULTS = {"FAIL", "SUCCESS"}


def validate_event(data):
    if not isinstance(data, dict):
        raise TypeError("이벤트는 object여야 합니다")
    if set(data) != {"username", "result"}:
        raise ValueError("이벤트 키 구성이 올바르지 않습니다")

    username = data["username"]
    result = data["result"]

    if not isinstance(username, str):
        raise TypeError("username은 문자열이어야 합니다")
    if not username.strip():
        raise ValueError("username은 비어 있을 수 없습니다")
    if not isinstance(result, str):
        raise TypeError("result는 문자열이어야 합니다")
    if result not in ALLOWED_RESULTS:
        raise ValueError("알 수 없는 인증 결과입니다")

    return {
        "username": username.strip(),
        "result": result,
    }
```

한 줄씩 읽으면서 행별 오류를 분리한다.

```python
MAX_LINE_CHARS = 10_000


def load_events(path):
    valid_events = []
    errors = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            text = line.rstrip("\r\n")

            if not text:
                errors.append({
                    "line": line_number,
                    "error": "빈 행입니다",
                })
                continue
            if len(text) > MAX_LINE_CHARS:
                errors.append({
                    "line": line_number,
                    "error": "허용된 행 길이를 초과했습니다",
                })
                continue

            try:
                event = loads_strict(text)
                event = validate_event(event)
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                errors.append({
                    "line": line_number,
                    "error": str(exc),
                })
                continue

            valid_events.append(event)

    return valid_events, errors


valid_events, errors = load_events(events_path)
print(valid_events)
print(errors)
```

오류 목록에는 입력 전문 대신 위치와 원인만 남긴다. 원본이 필요하면 접근이 제한된 격리 저장소에 별도로 보존한다. 이 예제의 길이 검사는 텍스트 모드가 한 행을 메모리에 읽은 **뒤** 수행하므로 비정상적으로 긴 단일 행의 메모리 사용을 사전에 제한하지는 못한다. 처리 전 전체 파일 크기를 제한하고, 강한 메모리 상한이 필요하면 바이트 청크를 제한해 읽는 별도 구현을 사용한다.

또한 입력은 한 줄씩 읽지만 정상·오류 결과를 리스트에 누적하므로 전체 메모리 사용량은 계속 증가한다. 결과까지 순차 저장하는 방법은 [04-7. 대용량 스트리밍](04-7-streaming-errors.md)에서 다룬다.

## 10. 형식 선택과 안전한 처리 경계

| 형식 | 적합한 데이터 | 주요 주의점 |
| --- | --- | --- |
| CSV | 행·열 구조가 일정한 표 | 헤더·열 개수·수식 해석 |
| JSON | 중첩된 문서 한 건 | 전체 크기·중복 키·자료형 검증 |
| JSON Lines | 이벤트·로그 여러 건 | 빈 행·행별 오류·최대 행 길이 |
| bytes | 파일 헤더·바이너리 구조 | 길이·식별자·오프셋·바이트 순서 |

신뢰하지 않는 대용량 JSON을 그대로 `json.load()`하면 메모리와 CPU를 과도하게 사용할 수 있다. 처리 전에 파일 크기 상한을 확인하고, 큰 이벤트 데이터는 JSON Lines처럼 순차 처리할 수 있는 형식을 선택한다. 한 행 자체가 매우 클 수 있으므로 JSON Lines도 행 길이와 전체 크기 제한이 필요하다.

JSON 파싱은 일반적으로 임의 Python 코드를 복원하지 않지만 입력 데이터가 안전하거나 유효하다는 뜻은 아니다. 반면 `pickle`은 객체를 복원하는 과정에서 임의 코드가 실행될 수 있으므로 신뢰하지 않는 파일이나 외부에서 받은 데이터를 절대 `pickle.load()`하지 않는다. 이 과정의 교환 형식에는 JSON·JSON Lines·CSV를 사용한다.

## 흔한 실수

- Python 딕셔너리 표현의 작은따옴표와 JSON 큰따옴표를 혼동한다.
- `dump()`·`load()`와 `dumps()`·`loads()`의 입력 대상을 혼동한다.
- 파싱 성공을 업무 스키마 검증 성공으로 간주한다.
- 중복 객체 키가 마지막 값으로 덮인다는 사실을 놓친다.
- 입력의 `NaN`·무한대와 출력의 `allow_nan` 정책을 확인하지 않는다.
- `default=str`로 모든 미지원 자료형을 조용히 문자열로 바꾼다.
- tuple과 비문자열 딕셔너리 키가 왕복 변환 뒤 그대로 복원된다고 생각한다.
- JSON Lines에 여러 줄 들여쓰기 JSON이나 빈 행을 섞는다.
- 한 줄씩 읽기만 하면 전체 처리 메모리가 제한된다고 생각한다.
- 오류 로그에 토큰·계정정보·개인정보가 포함된 입력 전문을 남긴다.
- 외부에서 받은 `pickle`을 데이터 파일처럼 역직렬화한다.

{% hint style="success" %}
### 🧪 종합 실습: 검증 결과 보고서

04-5의 CSV 처리 결과를 `summary`, `records`, `errors` 키를 가진 JSON 보고서로 저장한다.

1. `summary`에는 전체·정상·오류·격리 건수를 기록한다.
2. 저장 전 필수 키, 리스트·숫자 자료형, 건수 합계를 검증한다.
3. `allow_nan=False`와 UTF-8을 사용해 JSON 파일을 저장하고 다시 읽어 검증한다.
4. 같은 정상 레코드를 JSON Lines로 저장하고 각 행을 전용 스키마로 검증한다.
5. 잘못된 문법, 중복 키, `NaN`, 빈 행, 필수 키 누락 사례를 만들어 예상한 오류로 분리되는지 확인한다.
6. JSON과 JSON Lines의 전체 읽기·행별 오류 격리·메모리 차이를 설명한다.
7. 오류 결과에는 민감한 원문 대신 위치와 일반화한 원인만 기록한다.
{% endhint %}

## 완료 기준

- [ ] Python 자료형과 JSON 값의 대응 및 왕복 변환의 손실 가능성을 설명할 수 있다.
- [ ] 문자열용 함수와 파일용 함수를 구분해 사용할 수 있다.
- [ ] JSON 문법 오류의 행·열·원인을 확인할 수 있다.
- [ ] 중복 키와 비표준 숫자를 정책에 따라 거부할 수 있다.
- [ ] 필수 키·알 수 없는 키·자료형·빈 값·범위를 검증할 수 있다.
- [ ] JSON과 JSON Lines 중 데이터 목적에 맞는 형식을 선택할 수 있다.
- [ ] JSON Lines에서 행별 오류를 격리하고 입력 전문 노출을 피할 수 있다.
- [ ] 입력 크기 제한과 신뢰하지 않는 `pickle`의 위험을 설명할 수 있다.
- [ ] 종합 실습에서 정상·오류·격리 건수의 합을 전체 입력과 대조할 수 있다.

---

다음 절: [04-7. 대용량 스트리밍과 오류 복구](04-7-streaming-errors.md)
