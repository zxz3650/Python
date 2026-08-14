# 03-8. 미니 프로젝트: 인증 로그 분석기

03-1~03-7에서 배운 자료형, 자료구조, 조건문, 반복문, 함수, 파일, 예외, 테스트를 하나의 실행 가능한 프로그램으로 연결한다.

## 1. 목표

합성 인증 로그를 읽어 이벤트를 구조화하고 사용자·IP별 DENY 횟수와 파싱 오류를 JSON으로 보고한다.

## 2. 입력 형식

```text
2026-08-10T10:00:00Z ALLOW alice 10.0.0.5 /index
2026-08-10T10:00:01Z DENY bob 198.51.100.9 /admin
2026-08-10T10:00:02Z DENY bob 198.51.100.9 /login
BROKEN LINE
```

필드 순서는 `timestamp action user ip path`이다.

## 3. 프로젝트 구조

```text
python-security-lab/
├── data/
│   └── auth.log
├── python_basic/
│   ├── __init__.py
│   └── log_parser.py
├── tests/
│   └── test_log_parser.py
└── main.py
```

## 4. 1단계: 한 줄 파싱

먼저 IP와 timestamp의 상세 검증 없이 필드 수와 action만 처리한다.

```python
def parse_line(line: str) -> dict:
    parts = line.split()
    if len(parts) != 5:
        raise ValueError(f"필드 수 오류: {len(parts)}")

    timestamp, action, user, ip, path = parts

    if action not in {"ALLOW", "DENY"}:
        raise ValueError(f"허용되지 않은 action: {action}")

    return {
        "timestamp": timestamp,
        "action": action,
        "user": user,
        "ip": ip,
        "path": path,
    }
```

## 5. 2단계: IP 검증

```python
from ipaddress import ip_address

def validate_ip(value: str) -> str:
    try:
        ip_address(value)
    except ValueError as exc:
        raise ValueError(f"잘못된 IP: {value}") from exc
    return value
```

`parse_line()`에서 딕셔너리를 반환하기 전에 `ip = validate_ip(ip)`를 호출한다.

## 6. 3단계: 여러 줄과 오류 보존

```python
def parse_lines(text: str) -> tuple[list[dict], list[dict]]:
    records = []
    errors = []

    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue

        try:
            records.append(parse_line(line))
        except ValueError as exc:
            errors.append({
                "line": number,
                "raw": line,
                "error": str(exc),
            })

    return records, errors
```

## 7. 4단계: DENY 집계

```python
def summarize(records: list[dict], threshold: int = 2) -> dict:
    deny_by_user = {}
    deny_by_ip = {}

    for record in records:
        if record["action"] != "DENY":
            continue

        user = record["user"]
        ip = record["ip"]
        deny_by_user[user] = deny_by_user.get(user, 0) + 1
        deny_by_ip[ip] = deny_by_ip.get(ip, 0) + 1

    suspicious_users = {
        user: count
        for user, count in deny_by_user.items()
        if count >= threshold
    }

    return {
        "deny_by_user": deny_by_user,
        "deny_by_ip": deny_by_ip,
        "suspicious_users": suspicious_users,
    }
```

## 8. 5단계: 파일 입출력

```python
import json
from pathlib import Path

input_path = Path("data/auth.log")
output_path = Path("analysis_result.json")

text = input_path.read_text(encoding="utf-8")
records, errors = parse_lines(text)
summary = summarize(records)

report = {
    "valid_events": len(records),
    "parse_errors": len(errors),
    **summary,
    "errors": errors,
}

output_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

{% hint style="info" %}
## 📌 예상 결과

```json
{
  "valid_events": 3,
  "parse_errors": 1,
  "deny_by_user": {"bob": 2},
  "deny_by_ip": {"198.51.100.9": 2},
  "suspicious_users": {"bob": 2},
  "errors": [
    {
      "line": 4,
      "raw": "BROKEN LINE",
      "error": "필드 수 오류: 2"
    }
  ]
}
```
{% endhint %}

## 9. 최소 테스트

```python
import pytest

def test_parse_line_valid():
    record = parse_line(
        "2026-08-10T10:00:01Z DENY bob 198.51.100.9 /admin"
    )
    assert record["action"] == "DENY"
    assert record["user"] == "bob"

def test_parse_line_invalid():
    with pytest.raises(ValueError):
        parse_line("BROKEN LINE")

def test_summarize_threshold():
    records = [
        {"action": "DENY", "user": "bob", "ip": "198.51.100.9"},
        {"action": "DENY", "user": "bob", "ip": "198.51.100.9"},
    ]
    result = summarize(records, threshold=2)
    assert result["suspicious_users"] == {"bob": 2}
```

## 10. 구현 순서와 중간 점검

1. 로그 한 줄이 딕셔너리로 변환되는지 확인한다.
2. 잘못된 필드 수가 `ValueError`인지 확인한다.
3. 여러 줄에서 오류 행만 별도로 보존하는지 확인한다.
4. 사용자·IP별 DENY 집계가 맞는지 확인한다.
5. JSON 저장 후 다시 읽었을 때 값이 같은지 확인한다.
6. 마지막에만 파일과 함수를 결합한다.

## 11. 확장 과제

- `datetime.fromisoformat()`으로 timestamp 검증
- `argparse`로 `--input`, `--output`, `--threshold` 추가
- CSV와 JSON 입력 지원
- 대용량 로그를 generator로 처리
- 사용자명·토큰·민감 경로 마스킹
- IPv4와 IPv6 집계 분리

## 완료 기준

- [ ] 03-1~03-7의 핵심 개념을 코드에 적용했다.
- [ ] 정상·오류·경계값 테스트를 통과한다.
- [ ] 오류의 행 번호·원문·원인을 보존한다.
- [ ] 결과 JSON을 같은 입력으로 재현할 수 있다.
- [ ] 합성 데이터 또는 허가된 데이터만 사용한다.
