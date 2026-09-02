# 05-2. 분리·검색·치환

문자열 메서드는 구분자와 필드 순서가 일정한 텍스트를 가장 읽기 쉽게 처리하는 도구다. 정규표현식을 사용하기 전에 `split()`, `partition()`, `startswith()` 같은 메서드로 해결할 수 있는지 확인한다. 파싱 성공은 문자열을 나누었다는 뜻이지, 각 필드가 올바른 값임을 보장하지는 않는다.

{% hint style="info" %}
### 🧭 학습 목표

- `split()`, `rsplit()`, `partition()`을 입력 형식에 맞게 선택한다.
- `maxsplit`과 필드 수 검증으로 메시지 내부의 구분자를 보존한다.
- 존재 여부·위치·접두사·접미사 검색을 구분한다.
- `replace()`의 범위와 횟수를 제한한다.
- 파싱 오류에 행 번호·원문·원인을 보존한다.
- URL 요청 대상에서 경로와 쿼리 문자열을 분리한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | `split()`, `partition()`, `maxsplit`, `in`, `startswith()`, `join()` |
| 권장 | 필드 수 검증, 원문·행 번호 보존, 제한 치환 |
| 선택 | URL 경로·쿼리 분리, 민감 키 마스킹, 경로 표현 통일 |

## 학습 방법

구분자 개수가 0개, 예상한 개수, 예상보다 많은 입력을 항상 함께 실행한다. 성공 입력만으로 파서를 검증하지 않고, 어떤 실패를 오류로 보존할지 먼저 정한다.

- 학습자용 TODO Notebook: [`notebooks/05-2-split-search-replace.ipynb`](../notebooks/05-2-split-search-replace.ipynb)
- 실습 데이터: [`fixtures/05-text-processing/delimited-events.txt`](../fixtures/05-text-processing/delimited-events.txt)

## 선행 지식

- 05-1의 원문 보존·줄바꿈 제거·정규화 정책을 이해해야 한다.
- 리스트, 트리플, 디셔너리, 언패킹을 사용할 수 있어야 한다.
- `ValueError`를 발생시키고 `try`/`except`로 처리할 수 있어야 한다.

## 0. 학습 전 확인

다음 코드의 출력을 예상한 뒤 실행한다.

```python
print("A  B".split())
print("A  B".split(" "))
print("INFO|login|failed|retry".split("|", maxsplit=2))
print("name=alice".partition("="))
print("name".partition("="))
print("/api/users".find("/api/"))
print("/users".find("/api/"))
```

다음 질문에 답해 본다.

1. `split()`과 `split(" ")`의 결과가 다른 이유는 무엇인가?
2. `partition()`은 구분자가 없을 때 예외를 발생시키는가?
3. `find()`의 반환값을 그대로 `if`의 조건으로 사용해도 되는가?

## 1. `split()`과 `maxsplit`

인자 없는 `split()`은 연속된 공백 문자를 하나의 구분 영역으로 처리한다. 구분자를 명시한 `split(separator)`는 구분자 사이의 빈 필드도 보존한다.

```python
print("  INFO   login failed  ".split())
print("INFO||failed".split("|"))
```

마지막 필드에 공백이나 구분자가 포함될 수 있다면 분리 횟수를 제한한다.

```python
line = "INFO 2026-08-14 message with spaces"
level, date, message = line.split(maxsplit=2)

print(level)
print(date)
print(message)
```

```python
event = "2026-08-14|WARNING|login|failed|retry"
timestamp, level, message = event.split("|", maxsplit=2)

print(message)  # login|failed|retry
```

오른쪽 필드 수가 고정되어 있다면 `rsplit(separator, maxsplit)`으로 뒤에서부터 나눈다.

```python
path, extension = "archive.tar.gz".rsplit(".", maxsplit=1)

print(path)
print(extension)
```

## 2. `partition()`으로 한 번만 분리하기

`partition(separator)`은 앞부분, 구분자, 뒷부분의 세 값을 항상 반환한다. 구분자가 없으면 두 번째와 세 번째 값이 빈 문자열이 된다.

```python
header = "Content-Type: application/json"
name, separator, value = header.partition(":")

if not separator:
    raise ValueError("헤더 구분자가 없다")

print(name.strip())
print(value.strip())
```

```python
text = "name=alice=admin"
name, separator, value = text.partition("=")

print(name)       # name
print(separator)  # =
print(value)      # alice=admin
```

최초 구분자 하나만 의미가 있을 때는 `split(separator, maxsplit=1)`보다 구분자 존재 여부가 드러나는 `partition()`이 읽기 쉽다.

## 3. 목적에 맞는 검색 메서드

```python
path = "/api/v1/users"

print(path.startswith("/api/"))
print(path.endswith("/users"))
print("/v1/" in path)
print(path.find("users"))
print(path.count("/"))
```

| 질문 | 권장 표현 |
| --- | --- |
| 포함되었는가? | `needle in text` |
| 포함되지 않았는가? | `needle not in text` |
| 특정 문자열로 시작하는가? | `text.startswith(prefix)` |
| 특정 문자열로 끝나는가? | `text.endswith(suffix)` |
| 첫 위치가 필요한가? | `text.find(needle)` |
| 없을 때 예외이 필요한가? | `text.index(needle)` |

`find()`는 첫 위치가 0이면 0, 찾지 못하면 -1을 반환한다. Python에서 0은 거짓, -1은 참으로 해석되므로 결과를 조건식에 바로 사용하지 않는다.

```python
path = "/api/users"

if path.find("/api/") != -1:
    print("API 경로")

if "/api/" in path:
    print("API 경로")
```

## 4. 치환과 결합

`replace(old, new, count)`는 기본적으로 모든 일치를 바꾸며, 세 번째 인자로 치환 횟수를 제한할 수 있다.

```python
message = "token=abc123&next=/home&note=token=example"
masked_once = message.replace("abc123", "***", 1)

print(masked_once)
```

정확한 이전 값을 알 때만 `replace()`로 민감정보를 마스킹한다. 변할 수 있는 토큰·비밀번호를 고정 문자열로 치환하면 누락이 생기므로, 키와 값을 먼저 파싱한 뒤 민감 키의 값만 마스킹한다.

```python
SENSITIVE_KEYS = {"password", "token", "secret"}


def mask_pairs(text: str) -> str:
    masked_parts = []

    for part in text.split("&"):
        key, separator, value = part.partition("=")
        if separator and key.casefold() in SENSITIVE_KEYS:
            value = "***"
        masked_parts.append(key + separator + value)

    return "&".join(masked_parts)


print(mask_pairs("user=alice&token=abc123&next=/home"))
```

`join()`은 문자열 목록을 구분자로 연결한다.

```python
parts = ["2026-08-14", "INFO", "completed"]
line = " | ".join(parts)

print(line)
```

숫자·`None`과 같은 문자열이 아닌 값은 출력 규칙에 따라 먼저 변환한다.

## 5. 고정 형식 텍스트 파싱

파서는 정상 결과에는 원문과 구조화된 필드를, 실패 결과에는 행 번호·원문·원인을 남기도록 설계한다.

```python
def parse_event_line(line: str, line_number: int) -> dict:
    raw = line.rstrip("\r\n")
    parts = raw.split("|", maxsplit=2)

    if len(parts) != 3:
        raise ValueError(
            f"{line_number}번 행: 필드는 세 개여야 한다"
        )

    timestamp, level, message = (
        part.strip()
        for part in parts
    )

    if not timestamp or not level or not message:
        raise ValueError(
            f"{line_number}번 행: 빈 필드가 있다"
        )

    return {
        "line": line_number,
        "timestamp": timestamp,
        "level": level.upper(),
        "message": message,
        "raw": raw,
    }
```

```python
event = parse_event_line(
    "2026-08-14T10:30:00Z | info | login|completed\n",
    line_number=1,
)

print(event)
```

현재 함수는 필드 수와 빈 값만 확인한다. timestamp의 실제 날짜, level의 허용값은 05-5와 05-6에서 추가로 검증한다.

## 6. URL 경로와 쿼리 문자열 분리

`/login?next=/admin` 전체를 경로로 집계하면 쿼리 값이 다른 요청이 모두 다른 경로로 계산된다. `urllib.parse.urlsplit()`으로 요청 대상의 구성을 분리한다.

```python
from urllib.parse import parse_qsl, urlsplit

target = "/login?next=%2Fadmin&token=abc123"
parts = urlsplit(target)

path = parts.path or "/"
query_pairs = parse_qsl(
    parts.query,
    keep_blank_values=True,
)

print(path)
print(query_pairs)
```

쿼리 값에는 토큰·이메일·검색어 등이 포함될 수 있으므로 보고서에 원문 전체를 남기기 전에 필요성과 마스킹 정책을 확인한다.

경로 표현을 통일할 때는 규칙을 명시한다. `//`, `.`·`..`, 퍼센트 인코딩을 무조건 문자열 `replace()`로 수정하면 서버가 해석한 요청과 다른 경로를 만들 수 있다. 분석 목적이라면 원본 `target`과 분리한 `path`를 둘 다 보존한다.

## 7. 정규표현식이 필요한 시점

다음 상황은 문자열 메서드가 적합하다.

- 구분자가 고정되어 있다.
- 정확한 접두사·접미사·포함 여부를 확인한다.
- 한 번만 분리하거나 정해진 횟수만 치환한다.

다음 상황에서는 05-3의 정규표현식을 검토한다.

- 숫자 개수, 문자 범위, 반복 횟수처럼 **형태**를 표현해야 한다.
- 구분자의 종류·개수·공백이 변할 수 있다.
- 원문의 여러 위치에서 동일한 형태를 반복 추출한다.

형식이 CSV·JSON·URL 쿼리와 같이 이미 표준화되어 있다면 정규표현식보다 해당 파서를 사용한다.

## 8. 오류·경계 사례

| 상황 | 문제 | 수정 방향 |
| --- | --- | --- |
| `split()` 결과를 바로 언패킹 | 필드 수가 다르면 `ValueError`가 난다. | 길이를 먼저 검증한다. |
| 내부에도 구분자가 있는 메시지 | 모든 구분자를 나누어 필드가 늘어난다. | `maxsplit`으로 횟수를 제한한다. |
| `partition()` 구분자 누락 | 예외 없이 빈 구분자를 반환한다. | 두 번째 반환값을 확인한다. |
| `if text.find(key):` | 인덱스 0과 -1을 반대로 해석할 수 있다. | 존재 여부는 `in`을 사용한다. |
| 민감 값을 고정 `replace()`로 마스킹 | 다른 값은 누락된다. | 키·값을 파싱한 뒤 허용된 키만 표시한다. |
| 숫자 리스트에 `join()` | 문자열이 아니면 `TypeError`가 난다. | 출력 형식에 맞게 명시적으로 변환한다. |
| URL을 `/`로만 나눔 | 쿼리·프래그먼트·인코딩 경계가 섞인다. | `urllib.parse`의 전용 함수를 사용한다. |

## 9. 단계별 실습

[`delimited-events.txt`](../fixtures/05-text-processing/delimited-events.txt)를 읽어 정상 이벤트와 오류를 분리한다.

### 인수 조건

1. 각 행의 줄바꿈만 제거하고 원문을 보존한다.
2. `timestamp | level | message`의 세 필드로 최대 두 번만 나눈다.
3. 필드 수와 빈 필드를 검증한다.
4. 정상 행은 디셔너리, 오류 행은 `line`·`raw`·`code`·`message`를 갖는 디셔너리로 만든다.
5. 정상 건수 + 오류 건수가 전체 행 수와 같은지 검증한다.
6. 메시지에 `password=`·`token=`이 있으면 보고서용 값에서는 마스킹한다.

### 실습 과제 골격

```python
from pathlib import Path

FIXTURE_PATH = Path("fixtures/05-text-processing/delimited-events.txt")

records = []
errors = []

with FIXTURE_PATH.open("r", encoding="utf-8", errors="strict") as file:
    for line_number, line in enumerate(file, start=1):
        # 실습 과제 1: parse_event_line()을 호출한다.
        # 실습 과제 2: 정상 레코드와 구조화된 오류를 분리한다.
        pass
```

## 10. 자기점검

1. 인자 없는 `split()`과 `split(" ")`은 빈 필드를 어떻게 다르게 처리하는가?
2. `partition()`의 두 번째 반환값을 확인해야 하는 이유는 무엇인가?
3. 존재 여부 확인에 `find()`보다 `in`이 안전한 이유는 무엇인가?
4. 민감정보 마스킹을 고정 문자열 `replace()`만으로 구현하면 어떤 누락이 생기는가?
5. 파싱 성공과 필드 검증 성공은 어떻게 다른가?

```python
assert "A  B".split() == ["A", "B"]
assert "A||B".split("|") == ["A", "", "B"]
assert "name".partition("=")[1] == ""
assert mask_pairs("user=alice&password=pw") == "user=alice&password=***"
```

## 11. 응용 인사이트

파서는 외부 문자열을 프로그램 내부 자료구조로 바꾸는 **신뢰 경계**다. 이 경계에서 원문, 행 번호, 파싱 규칙, 오류 코드를 남기면 후속 단계가 문자열 위치를 다시 추측하지 않아도 된다.

단, 원문 보존은 무조건 전체 출력을 의미하지 않는다. 입력에 계정, 토큰, 세션 식별자가 있다면 원문 저장소의 접근을 제한하고, 학습자·보고서에 제공할 때는 필요한 필드만 마스킹한다.

## 완료 기준

- [ ] 구분자와 필드 규칙에 맞는 분리 메서드를 선택할 수 있다.
- [ ] `maxsplit`과 필드 수 검증으로 변형된 입력을 처리할 수 있다.
- [ ] 원문·행 번호·원인을 구조화한 오류로 보존할 수 있다.
- [ ] URL의 경로와 쿼리 문자열을 분리할 수 있다.
- [ ] 보고서에 포함할 민감 필드를 마스킹할 수 있다.
- [ ] 문자열 메서드, 정규표현식, 전용 파서의 선택 기준을 설명할 수 있다.

---

다음 절: [05-3. 정규표현식 기초](05-3-regex-basics.md)
