# 04-5. JSON 직렬화

JSON은 객체와 배열을 표현하는 텍스트 형식입니다. Python의 딕셔너리와 리스트를 파일이나 네트워크에서 교환 가능한 데이터로 변환할 때 사용합니다.

{% hint style="info" %}
## 🧭 학습 목표

- Python 자료형과 JSON 형식의 대응 관계를 설명합니다.
- `dump/load`와 `dumps/loads`를 구분합니다.
- 읽기 쉬운 JSON 파일을 생성합니다.
- 파싱·직렬화 오류와 데이터 검증을 처리합니다.
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

{% hint style="success" %}
## 🧪 종합 실습

CSV 처리 결과를 `summary`, `records`, `errors` 키를 가진 JSON으로 저장합니다. 다시 읽어 원래 결과와 같은지 검증합니다.
{% endhint %}

## 완료 기준

- [ ] 문자열용 함수와 파일용 함수를 구분할 수 있습니다.
- [ ] JSON 오류의 위치와 원인을 확인할 수 있습니다.
- [ ] 필수 키와 자료형을 검증할 수 있습니다.

---

다음 절: [04-6. 대용량 파일과 오류 처리](04-6-streaming-errors.md)
