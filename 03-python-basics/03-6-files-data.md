# 03-6. 파일, JSON, CSV, str과 bytes

## 학습 목표

- 파일을 안전하게 읽고 쓴다.
- `pathlib`, JSON, CSV를 사용한다.
- `str`과 `bytes`를 구분한다.

## pathlib와 파일 I/O

```python
from pathlib import Path

path = Path("auth.log")

with path.open("r", encoding="utf-8") as file:
    for line in file:
        print(line.rstrip())
```

대용량 로그는 `read_text()`로 모두 읽기보다 한 줄씩 처리한다.

## JSON

```python
import json
from pathlib import Path

result = {"valid_events": 3, "parse_errors": 1}
output = Path("analysis_result.json")
output.write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

loaded = json.loads(output.read_text(encoding="utf-8"))
assert loaded == result
```

## CSV

쉼표가 포함된 필드와 인용부호를 고려해 문자열 `split(",")` 대신 `csv` 모듈을 사용한다.

## str과 bytes

```python
text = "안녕하세요"
raw = text.encode("utf-8")
restored = raw.decode("utf-8")

print(type(text), type(raw))
assert restored == text
```

파일 헤더나 패킷처럼 바이트 단위 데이터는 `bytes`로 처리한다. 문자열과 bytes를 암묵적으로 섞지 않는다.

## 실습

- 인증 로그를 파일에서 한 줄씩 읽는다.
- 분석 결과를 JSON으로 저장하고 재로드한다.
- CSV 로그를 `csv.DictReader`로 읽는다.
