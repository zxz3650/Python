# 04-6. JSON·JSON Lines와 직렬화 검증

JSON은 객체와 배열을 표현하는 텍스트 형식입니다. Python의 딕셔너리와 리스트를 파일이나 네트워크에서 교환 가능한 데이터로 변환할 때 사용합니다.

{% hint style="info" %}
## 🧭 학습 목표

- Python 자료형과 JSON 형식의 대응 관계를 설명합니다.
- `dump/load`와 `dumps/loads`를 구분합니다.
- 읽기 쉬운 JSON 파일을 생성합니다.
- 파싱·직렬화 오류와 데이터 검증을 처리합니다.
- JSON과 JSON Lines의 사용 목적을 구분합니다.
- 신뢰하지 않는 직렬화 데이터의 위험을 설명합니다.
{% endhint %}

## 선행 지식

딕셔너리·리스트, 파일과 인코딩을 이해해야 합니다.

## 1. 자료형 대응

| Python | JSON |
|---|---|
| `dict` | object |
| `list`, `tuple` | array |
| `str` | string |
| `int`, `float` | number |
| `True`, `False` | true, false |
| `None` | null |

## 2. 문자열 변환

```python
import json

record = {
    "name": "Alice",
    "active": True,
    "score": 91,
    "tags": ["python", "file"],
}

text = json.dumps(record, ensure_ascii=False, indent=2)
restored = json.loads(text)

print(text)
print(restored == record)
```

- `dumps()`: Python 객체에서 JSON 문자열
- `loads()`: JSON 문자열에서 Python 객체

## 3. 파일 읽기와 쓰기

```python
from pathlib import Path

path = Path("record.json")

with path.open("w", encoding="utf-8") as file:
    json.dump(record, file, ensure_ascii=False, indent=2)

with path.open("r", encoding="utf-8") as file:
    loaded = json.load(file)
```

`dump/load`는 파일 객체를 대상으로 합니다.

## 4. 중첩 구조

```python
report = {
    "summary": {"total": 2, "active": 1},
    "records": [
        {"name": "Alice", "active": True},
        {"name": "Bob", "active": False},
    ],
}
```

중첩은 데이터 관계를 표현하지만 너무 깊으면 접근과 검증이 어려워집니다.

## 5. JSON 형식 오류

```python
invalid = '{"name": "Alice",}'

try:
    json.loads(invalid)
except json.JSONDecodeError as exc:
    print("행:", exc.lineno)
    print("열:", exc.colno)
    print("원인:", exc.msg)
```

JSON은 마지막 쉼표, 작은따옴표, 주석을 허용하지 않습니다.

## 6. 직렬화할 수 없는 값

```python
from datetime import datetime

data = {"created_at": datetime.now()}

try:
    json.dumps(data)
except TypeError as exc:
    print("직렬화 실패:", exc)

data["created_at"] = data["created_at"].isoformat()
```

datetime·Path·set 등은 저장 가능한 자료형으로 명시적으로 변환합니다.

## 7. 데이터 검증

```python
def validate_record(data):
    if not isinstance(data, dict):
        raise TypeError("object 형식이 필요합니다")
    if "name" not in data:
        raise ValueError("name 필드가 없습니다")
    if not isinstance(data["name"], str):
        raise TypeError("name은 문자열이어야 합니다")
```

JSON 파싱 성공과 업무 데이터의 유효성은 별개입니다.

## 8. 엄격한 JSON 출력

Python의 기본 JSON 인코더는 `NaN`과 무한대를 출력할 수 있지만 이 값들은 표준 JSON 숫자가 아닙니다. 다른 시스템과 교환하는 JSON은 `allow_nan=False`로 조용한 비표준 출력을 막습니다.

```python
data = {"score": float("nan")}

try:
    json.dumps(data, allow_nan=False)
except ValueError as exc:
    print("JSON 숫자 검증 실패:", exc)
```

tuple은 JSON array로 저장된 뒤 다시 읽으면 list가 됩니다. 정수 딕셔너리 키도 JSON object의 문자열 키로 바뀔 수 있습니다. 단순히 파싱에 성공했다는 이유만으로 원래 Python 자료형과 완전히 같다고 가정하지 않습니다.

## 9. JSON Lines

JSON Lines는 한 줄에 독립된 JSON 값 하나를 저장합니다. 대용량 이벤트와 로그를 순차 처리하고, 오류가 있는 행의 위치를 기록하기 좋습니다.

```python
from pathlib import Path

events = [
    {"username": "alice", "result": "FAIL"},
    {"username": "alice", "result": "SUCCESS"},
]

with Path("events.jsonl").open("w", encoding="utf-8") as file:
    for event in events:
        text = json.dumps(
            event,
            ensure_ascii=False,
            allow_nan=False,
        )
        file.write(text + "\n")
```

한 줄씩 읽으면서 행별 오류를 분리합니다.

```python
valid_events = []
errors = []

with Path("events.jsonl").open("r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        try:
            event = json.loads(line)
            validate_record(event)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            errors.append({
                "line": line_number,
                "error": str(exc),
            })
            continue

        valid_events.append(event)
```

이 예제는 입력을 한 줄씩 읽지만 정상 이벤트를 리스트에 모으므로 전체 메모리는 계속 증가합니다. 04-7에서 입력 스트리밍과 전체 처리 메모리를 구분합니다.

## 10. 입력 크기와 직렬화 형식 선택

신뢰하지 않는 대용량 JSON을 그대로 `json.load()`하면 메모리와 CPU를 과도하게 사용할 수 있습니다. 처리 전에 파일 크기 상한을 확인하고, 큰 이벤트 데이터는 JSON Lines 같은 순차 형식을 선택합니다.

| 형식 | 적합한 데이터 | 주요 주의점 |
| --- | --- | --- |
| CSV | 행·열이 일정한 표 | 헤더·열 개수·수식 해석 |
| JSON | 중첩된 문서 한 건 | 전체 크기·자료형 검증 |
| JSON Lines | 이벤트·로그 여러 건 | 행별 오류·최대 행 길이 |
| bytes | 파일 헤더·바이너리 구조 | 길이·오프셋·바이트 순서 |

`pickle`은 Python 객체를 복원하면서 코드를 실행할 수 있으므로 신뢰하지 않는 파일이나 외부에서 받은 데이터를 역직렬화하지 않습니다. 이 장에서는 교환 형식으로 JSON·CSV를 사용합니다.

{% hint style="success" %}
## 🧪 종합 실습

CSV 처리 결과를 `summary`, `records`, `errors` 키를 가진 JSON으로 저장합니다. 다시 읽어 필수 키와 자료형을 검증합니다. 같은 레코드를 JSON Lines로도 저장하고 두 형식의 메모리 사용 방식과 오류 격리 차이를 설명합니다.
{% endhint %}

## 완료 기준

- [ ] 문자열용 함수와 파일용 함수를 구분할 수 있습니다.
- [ ] JSON 오류의 위치와 원인을 확인할 수 있습니다.
- [ ] 필수 키와 자료형을 검증할 수 있습니다.
- [ ] JSON과 JSON Lines 중 데이터 목적에 맞는 형식을 선택할 수 있습니다.
- [ ] 비표준 숫자와 신뢰하지 않는 pickle의 위험을 설명할 수 있습니다.

---

다음 절: [04-7. 대용량 스트리밍과 오류 복구](04-7-streaming-errors.md)
