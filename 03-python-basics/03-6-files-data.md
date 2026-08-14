# 03-6. 파일, JSON, CSV, str과 bytes

프로그램은 메모리 안의 값뿐 아니라 파일·API·패킷에서 데이터를 읽고 결과를 저장한다. 형식과 인코딩을 명확히 지정해야 재현 가능한 분석이 된다.

{% hint style="info" %}
### 🧭 학습 목표

- `pathlib`와 `with`로 파일을 안전하게 다룬다.
- 텍스트·JSON·CSV를 읽고 쓴다.
- `str`, `bytes`, 인코딩의 관계를 설명한다.
- 파일 및 디코딩 오류를 구분한다.
{% endhint %}

## 1. 경로와 현재 작업 디렉터리

```python
from pathlib import Path

print(Path.cwd())
path = Path("data") / "auth.log"
print(path.exists())
print(path.suffix)
```

상대 경로는 현재 작업 디렉터리를 기준으로 한다. 파일이 예상 위치에 없으면 `Path.cwd()`를 먼저 확인한다.

## 2. 파일 모드와 with

- `r`: 읽기
- `w`: 새로 쓰기 또는 기존 내용 덮어쓰기
- `a`: 끝에 추가
- `b`: 바이너리 모드

```python
path = Path("auth.log")

with path.open("w", encoding="utf-8") as file:
    file.write("DENY 198.51.100.9 443 /admin\n")

with path.open("r", encoding="utf-8") as file:
    text = file.read()

print(text)
```

`with` 블록을 벗어나면 오류가 발생해도 파일을 닫는다.

## 3. 대용량 파일 한 줄씩 처리

```python
with path.open("r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        clean = line.rstrip("\n")
        print(line_number, clean)
```

대용량 로그는 `read_text()`로 모두 메모리에 올리지 않고 반복 처리한다.

## 4. 파일 오류 처리

```python
try:
    text = Path("missing.log").read_text(encoding="utf-8")
except FileNotFoundError:
    print("파일을 찾을 수 없습니다")
except UnicodeDecodeError:
    print("UTF-8로 해석할 수 없습니다")
```

파일 없음과 인코딩 문제는 원인과 해결 방법이 다르므로 구분한다.

## 5. JSON 읽기와 쓰기

```python
import json
from pathlib import Path

result = {
    "valid_events": 3,
    "parse_errors": 1,
    "deny_by_ip": {"198.51.100.9": 2},
}

output = Path("analysis_result.json")
with output.open("w", encoding="utf-8") as file:
    json.dump(result, file, ensure_ascii=False, indent=2)

with output.open("r", encoding="utf-8") as file:
    loaded = json.load(file)

assert loaded == result
```

`dump/load`는 파일 객체, `dumps/loads`는 문자열을 다룬다. 기본적으로 dict·list·str·int·float·bool·None을 저장할 수 있다.

## 6. CSV를 DictReader로 읽기

```python
import csv
from pathlib import Path

csv_path = Path("events.csv")
csv_path.write_text(
    "action,ip,port,path\n"
    "ALLOW,10.0.0.5,80,/index\n"
    "DENY,198.51.100.9,443,/admin\n",
    encoding="utf-8",
)

with csv_path.open("r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)
    records = []
    for row in reader:
        row["port"] = int(row["port"])
        records.append(row)

print(records)
```

CSV는 인용부호와 필드 안의 쉼표 규칙이 있으므로 직접 `split(",")`하지 않는다.

## 7. CSV 쓰기

```python
fields = ["action", "ip", "port", "path"]

with Path("output.csv").open("w", encoding="utf-8", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)
```

## 8. str, bytes와 인코딩

```python
text = "안녕하세요"
raw = text.encode("utf-8")
restored = raw.decode("utf-8")

print(type(text), type(raw))
print(raw)
assert restored == text
```

인코딩은 문자에서 bytes로, 디코딩은 bytes에서 문자로 바꾼다.

```python
header = b"MZ"
print(header[0])           # 77
print(header.hex())        # 4d5a
```

`bytes`는 불변이다. 수정 가능한 바이트 배열이 필요하면 `bytearray`를 사용한다.

## 9. 바이너리 파일

```python
binary_path = Path("sample.bin")
binary_path.write_bytes(b"MZ\x90\x00")
data = binary_path.read_bytes()

print(data[:2] == b"MZ")
```

텍스트는 인코딩을 지정하고, 파일 헤더·패킷처럼 원시 바이트가 중요한 데이터는 바이너리 모드로 처리한다.

{% hint style="success" %}
## 🧪 실습

1. 인증 로그를 UTF-8 파일에 쓰고 한 줄씩 읽는다.
2. 없는 파일과 잘못된 인코딩 오류를 구분한다.
3. 분석 결과를 JSON으로 저장하고 다시 읽는다.
4. CSV를 `DictReader`로 읽고 포트를 정수로 변환한다.
5. `b"MZ"` 파일 헤더를 검사한다.
{% endhint %}

## 핵심 정리

- 상대 경로는 현재 작업 디렉터리를 기준으로 한다.
- `with`는 파일을 안전하게 닫는다.
- JSON과 CSV는 표준 모듈로 처리한다.
- `str`과 `bytes` 사이에는 명시적인 인코딩·디코딩이 필요하다.
