# 03-7. 오류, 예외, 모듈과 테스트

오류를 없애는 것만큼 중요한 능력은 오류 메시지를 읽고 예상 가능한 실패를 보존하는 것이다.

{% hint style="info" %}
### 🧭 학습 목표

- 문법 오류와 실행 중 예외를 구분한다.
- traceback에서 오류 유형·메시지·발생 위치를 찾는다.
- 구체적인 예외를 처리하고 원인을 보존한다.
- 모듈과 패키지로 코드를 나누고 pytest 테스트를 작성한다.
{% endhint %}

## 1. 문법 오류와 예외

```python
# if True print("hello")
# SyntaxError: Python 문법으로 해석할 수 없음
```

```python
# print(10 / 0)
# ZeroDivisionError: 문법은 맞지만 실행 중 실패
```

문법 오류는 실행 전에 발견되고, 예외는 실행 과정에서 발생한다.

## 2. traceback 읽는 순서

```python
def convert_port(value):
    return int(value)

convert_port("443a")
```

traceback은 마지막 줄부터 읽는다.

1. 마지막 줄의 예외 유형: `ValueError`
2. 뒤의 오류 메시지: 무엇이 잘못됐는지
3. 위쪽 파일명과 행 번호: 어디서 호출됐는지
4. 호출 흐름을 위로 따라가며 원인을 찾기

## 3. try와 except

```python
raw_port = "443a"

try:
    port = int(raw_port)
except ValueError as exc:
    print("포트 변환 실패:", exc)
else:
    print("변환 성공:", port)
finally:
    print("검증 종료")
```

`else`는 예외가 없을 때, `finally`는 성공·실패와 관계없이 실행된다. `try`에는 실제로 예외가 예상되는 최소 코드만 넣는다.

## 4. 구체적인 예외 처리

```python
from pathlib import Path

try:
    text = Path("auth.log").read_text(encoding="utf-8")
    port = int(text.strip())
except FileNotFoundError:
    print("파일 없음")
except UnicodeDecodeError:
    print("인코딩 오류")
except ValueError:
    print("숫자 형식 오류")
```

`except Exception`으로 모든 오류를 숨기면 프로그래밍 오류까지 놓칠 수 있다.

## 5. raise와 원인 보존

```python
def parse_port(value):
    try:
        port = int(value)
    except ValueError as exc:
        raise ValueError(f"잘못된 포트: {value!r}") from exc

    if not 1 <= port <= 65535:
        raise ValueError("포트 범위는 1~65535입니다")
    return port
```

`raise ... from exc`는 원래 오류와 새 업무 오류의 관계를 traceback에 남긴다.

## 6. 오류 행을 버리지 않기

```python
def parse_lines(text):
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

원문·행 번호·원인을 함께 보존해야 문제를 재현할 수 있다.

## 7. assert의 역할

```python
result = {"deny": 2}
assert result["deny"] == 2
```

`assert`는 개발 중 가정과 테스트를 확인하는 도구다. 실행 옵션으로 제거될 수 있으므로 사용자 입력 검증이나 권한 판정에는 사용하지 않는다.

## 8. 모듈과 패키지

모듈은 하나의 `.py` 파일이고 패키지는 관련 모듈을 담은 디렉터리다.

```text
python_basic/
├── __init__.py
├── parser.py
├── validator.py
├── report.py
└── main.py
```

```python
# main.py
from python_basic.parser import parse_line

def main():
    print(parse_line("DENY 198.51.100.9 443 /admin"))

if __name__ == "__main__":
    main()
```

실행 진입점을 분리하면 import 시 분석 코드가 자동 실행되는 부수효과를 막을 수 있다.

## 9. pytest로 실제 테스트 작성

```python
# test_parser.py
import pytest
from python_basic.parser import parse_line

def test_parse_line_valid():
    record = parse_line("DENY 198.51.100.9 443 /admin")
    assert record["port"] == 443

def test_parse_line_invalid_field_count():
    with pytest.raises(ValueError):
        parse_line("BROKEN LINE")

@pytest.mark.parametrize("port", ["0", "65536", "abc"])
def test_invalid_ports(port):
    with pytest.raises(ValueError):
        parse_port(port)
```

정상값, 오류값, 경계값을 각각 검증한다.

```bash
python -m pytest -q
```

{% hint style="success" %}
## 🧪 실습

1. `TypeError`, `ValueError`, `KeyError`를 각각 발생시키고 traceback을 읽는다.
2. 포트 변환 오류를 원인과 함께 다시 발생시킨다.
3. 오류 행의 번호·원문·원인을 딕셔너리로 보존한다.
4. 파서와 보고서 기능을 별도 모듈로 나눈다.
5. 정상·오류·경계값 pytest를 작성한다.
{% endhint %}

## 핵심 정리

- 오류 유형과 traceback은 문제의 원인을 찾는 정보다.
- 예상 가능한 예외만 구체적으로 처리한다.
- 모듈은 책임을 분리하고 테스트 가능성을 높인다.
- 테스트는 정상·오류·경계값을 모두 포함한다.
