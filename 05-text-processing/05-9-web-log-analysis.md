# 05-9. 웹 접근 로그 분석 종합 실습

04장에서 익힌 스트리밍 파일 처리와 05장의 문자열·정규표현식·날짜·NumPy·pandas를 연결해 웹 접근 로그 분석기를 완성한다. 단순히 요청 수를 세는 데서 끝내지 않고 **입력 품질 확인 → 필드 검증 → 경로 정규화 → 시간창별 특징 생성 → 조사 후보 선별 → 민감정보를 줄인 결과 저장**의 순서로 분석한다.

{% hint style="info" %}
### 🧭 학습 목표

- Apache/Nginx Combined Log 한 줄을 구조화하고 의미를 검증한다.
- 과대 행·인코딩·형식·값 검증 오류를 서로 다른 품질 지표로 기록한다.
- IPv4와 IPv6를 검증하고 URL 경로를 비교 가능한 형태로 정규화한다.
- 5분 시간창에서 404 비율·고유 경로 수·민감 경로 요청을 계산한다.
- NumPy 배열 연산과 조건 마스크로 조사 후보를 선별한다.
- IP·쿼리 문자열·User-Agent 등 민감할 수 있는 값을 최소 수집하고 가명 처리한다.
- 전체 결과를 숨김 staging 디렉터리에서 완성한 뒤 한 번에 게시한다.
{% endhint %}

## 학습 전 확인

다음 항목을 먼저 확인한다.

- 04장에서 `Path`, `open()`, 문자 인코딩, 스트리밍 처리를 실습했다.
- 05-3부터 05-6까지의 정규표현식·데이터 검증·날짜 변환을 이해한다.
- 05-7의 NumPy 조건 마스크와 05-8의 DataFrame 집계를 실행할 수 있다.
- 실습 로그는 교육용 합성 데이터이며 실제 사용자 로그가 아니다.
- 조사 후보는 공격 확정 결과가 아니라 원본 맥락을 추가 확인할 우선순위이다.

### 실습 자료

- [학습자용 Notebook](../notebooks/05-9-web-log-analysis.ipynb)
- [풀이·검증용 Notebook](../notebooks/solutions/05-9-web-log-analysis-solution.ipynb)
- [기본 합성 로그 fixture](../fixtures/05-text-processing/web-access.log)
- [잘못된 UTF-8 fixture](../fixtures/05-text-processing/web-access-invalid-utf8.log)

학습자용 Notebook은 핵심 함수와 분석 기준을 직접 완성하는 TODO 형식으로 구성한다. 풀이·검증용 Notebook은 결과 비교와 경계 사례 확인을 위한 참고 구현이다. 공개 저장소에서는 누구나 참고 구현을 볼 수 있으므로 평가에 사용할 때에는 정답과 검증 자료를 교사용 공간에서 별도로 배포해야 한다.

{% hint style="warning" %}
실제 로그에는 IP 주소, 계정 식별자, 쿼리 문자열, 세션 토큰, User-Agent 등이 포함될 수 있다. 조직의 수집·보존·반출 정책을 확인하고 원본 로그는 읽기 전용으로 다룬다. 이 실습에서 안전하게 저장했다는 말은 데이터가 완전히 익명화되었다는 뜻이 아니다.
{% endhint %}

## 1. 분석 문제를 먼저 정의한다

웹 로그에는 하나의 정답이 들어 있지 않다. 먼저 답하려는 질문을 정하고 질문에 필요한 최소 필드만 처리한다.

| 분석 관점 | 질문 | 사용할 지표 |
| --- | --- | --- |
| 데이터 신뢰성 | 읽지 못하거나 해석하지 못한 행이 있는가? | 정상 행, 과대 행·인코딩·형식·검증 오류 행 |
| 서비스 상태 | 서버가 요청을 어떻게 처리했는가? | 상태 코드 그룹, 응답 바이트 누락 |
| 이용 패턴 | 어느 시간대와 경로에 요청이 집중되는가? | 5분 요청 수, 정규화 경로 수 |
| 보안 조사 | 짧은 시간에 여러 경로를 탐색했는가? | 404 비율, 고유 404 경로, 민감 경로 |
| 개인정보 보호 | 결과 공유에 불필요한 원문이 남는가? | 가명 IP, 경로 별칭, 원문 미저장 |

분석은 다음 순서로 수행한다.

```text
크기를 제한한 원본 바이트 한 줄
→ UTF-8 strict 디코딩
→ Combined Log 구조 파싱
→ IP·상태 코드·시각 의미 검증
→ URL 경로 정규화
→ 5분 시간창 특징 집계
→ NumPy 규칙으로 후보 선별
→ 가명 처리한 결과만 안전하게 저장
```

파싱 오류가 많은 상태에서 탐지 결과를 먼저 해석하면 실제 현상이 아니라 파서의 결함을 이상 징후로 오인할 수 있다.

## 2. 입력 형식과 결정론적 합성 시나리오

기본 입력은 Apache/Nginx Combined Log 형식이다.

```text
203.0.113.10 - - [14/Aug/2026:10:30:00 +0900] "GET /login?next=%2Fadmin HTTP/1.1" 200 443 "-" "Mozilla/5.0"
```

이 실습에서는 다음 필드만 분석에 사용한다.

| 필드 | 처리 방법 | 저장 여부 |
| --- | --- | --- |
| 출발지 IP | `ipaddress.ip_address()`로 검증한 뒤 메모리에서 집계 | HMAC 별칭만 저장 |
| timestamp | 시간대가 있는 시각으로 파싱한 뒤 UTC로 변환 | 5분 시간창만 저장 |
| method | 구조 파싱 후 길이와 형식을 검증 | 집계값만 저장 |
| target | 쿼리와 경로를 분리하고 경로만 정규화 | 원문과 쿼리는 저장하지 않음 |
| status | ASCII `[0-9]` 세 자리와 `100~599` 범위를 검증 | 집계값만 저장 |
| bytes | ASCII `[0-9]` 자릿수·범위를 검증하고 `-`는 `None`으로 보존 | 합계와 누락 건수만 저장 |
| referrer·User-Agent | 파싱 경계 확인에만 사용 | 집계·저장하지 않음 |

### 2.1 fixture가 포함해야 하는 상황

합성 데이터는 같은 입력에서 항상 같은 결과가 나오도록 고정 시나리오와 고정 시각을 사용한다. 생성 코드를 학습자 Notebook 안에 두지 않고 fixture로 제공해, 학생이 생성 규칙이 아니라 관찰한 로그를 근거로 분석하게 한다.

| 상황 | 포함 이유 | 기대되는 해석 |
| --- | --- | --- |
| 낮은 404 비율의 일반 요청 | 평상시 기준을 만든다 | 후보가 아님 |
| 한 IP의 동일한 `favicon.ico` 반복 404 | 절대 건수만 쓰는 규칙의 오탐을 보여 준다 | 고유 경로가 1개이므로 탐색 신호가 아님 |
| NAT 환경의 높은 정상 요청량 | IP 하나를 사용자 한 명으로 보면 안 됨을 보여 준다 | 높은 요청량만으로 후보가 아님 |
| 승인된 점검 도구의 민감 경로 요청 | 신호와 최종 판정을 구분한다 | 후보에는 남기되 자산·승인 정보를 확인 |
| 5분 이내 여러 경로를 조회한 탐색 형태 | 비율과 고유 경로 수를 함께 검증한다 | 조사 후보 |
| 민감 경로에서 발생한 `2xx` 한 건 | 단순 404 탐지로 놓칠 수 있는 노출 가능성을 보여 준다 | 높은 우선순위 후보 |
| IPv4·IPv6, CRLF, 잘린 행, 잘못된 시각·상태 코드·IP | 파서 경계 사례를 검증한다 | 오류 유형별로 분리 |
| 잘못된 UTF-8 바이트 | 대체 문자로 숨기지 않고 디코딩 오류로 분리한다 | `encoding_errors` 증가 |

합성 데이터의 문서용 IP는 `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`, `2001:db8::/32` 범위를 사용한다. fixture의 정답 식별자와 예상 품질 건수는 풀이·검증용 Notebook에서 확인한다.

## 3. 바이트 디코딩과 오류 분류

텍스트 모드의 `errors="replace"`는 잘못된 바이트를 `�`로 바꾼다. 프로그램은 계속 실행되지만 어떤 행에 인코딩 문제가 있었는지 알기 어려워지고, 바뀐 문자열이 우연히 정규표현식과 일치할 수도 있다. 따라서 원본을 바이너리로 한 줄씩 읽고 UTF-8 strict 디코딩을 적용한다.

```python
from collections import Counter

MAX_LINE_BYTES = 16_384
ERROR_SAMPLE_LIMIT = 20
quality = Counter()
error_samples = []


def iter_limited_physical_lines(file):
    line_number = 0

    while True:
        raw_line = file.readline(MAX_LINE_BYTES + 1)
        if raw_line == b"":
            return

        line_number += 1
        physical_length = len(raw_line)
        oversized = len(raw_line) > MAX_LINE_BYTES

        # 제한을 넘은 물리 행의 나머지를 다음 LF까지 소비한다.
        if oversized and not raw_line.endswith(b"\n"):
            while True:
                remainder = file.readline(MAX_LINE_BYTES + 1)
                if remainder == b"":
                    break
                physical_length += len(remainder)
                if remainder.endswith(b"\n"):
                    break

        yield (
            line_number,
            None if oversized else raw_line,
            physical_length,
            oversized,
        )


def add_error_sample(source, line, error_type, length):
    if len(error_samples) < ERROR_SAMPLE_LIMIT:
        error_samples.append({
            "source": source,
            "line": line,
            "type": error_type,
            "length": length,
        })


for source_number, log_path in enumerate(input_paths, start=1):
    source_label = f"input-{source_number}"

    with log_path.open("rb") as file:
        for (
            line_number,
            raw_line,
            physical_length,
            oversized,
        ) in iter_limited_physical_lines(file):
            quality["total_lines"] += 1

            if oversized:
                quality["oversized_line_errors"] += 1
                add_error_sample(
                    source_label,
                    line_number,
                    "line_too_long",
                    physical_length,
                )
                continue

            try:
                line = raw_line.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                quality["encoding_errors"] += 1
                add_error_sample(
                    source_label,
                    line_number,
                    "encoding",
                    physical_length,
                )
                continue

            # strict 디코딩에 성공한 행만 구조 파서로 전달한다.
            parse_and_collect(
                line,
                source_label,
                line_number,
                quality,
                error_samples,
            )
```

오류 샘플에는 원문이나 행 해시를 넣지 않는다. 로그인 요청의 쿼리 문자열이나 인증 토큰이 오류 행에 포함될 수 있고, 키 없는 행 해시는 입력 후보를 대입해 원문을 추측하는 단서가 될 수 있다. 승인된 원본에서는 `source`·`line`으로 같은 행을 다시 찾고, 결과에는 오류 `type`과 물리 행 `length`만 추가한다.

형식·값 검증 오류도 같은 `add_error_sample()`을 사용한다. 예외 메시지나 필드 원문을 그대로 복사하지 않고 네 필드의 schema를 유지한다.

`readline(MAX_LINE_BYTES + 1)`은 한 번에 읽는 크기를 제한한다. 제한을 넘은 행은 부분 문자열을 파서에 전달하지 않고 다음 LF 또는 EOF까지 소비해 하나의 `oversized_line_errors`로 기록한다. 따라서 매우 긴 한 행이 다음 행으로 잘못 분리되지 않는다.

### 3.1 개행 제거 오류를 바로잡는다

다음 코드는 개행을 제거하지 않는다.

```python
line.rstrip("\\n")  # 잘못된 예: 역슬래시와 문자 n을 제거한다.
```

Python 문자열 `"\\n"`은 실제 개행이 아니라 역슬래시와 `n` 두 문자이다. 따라서 `login`처럼 `n`으로 끝나는 유효한 데이터까지 바꿀 수 있다. LF와 CRLF만 제거하려면 다음처럼 작성한다.

```python
def strip_line_ending(line: str) -> str:
    return line.rstrip("\r\n")


assert strip_line_ending("record\n") == "record"
assert strip_line_ending("record\r\n") == "record"
assert strip_line_ending("login") == "login"
```

`strip()`을 사용하면 앞뒤 공백까지 제거하므로 로그 구조가 의도치 않게 바뀔 수 있다. 이 단계에서는 줄바꿈 문자만 제거한다.

### 3.2 오류 유형을 구분한다

| 오류 유형 | 예 | 처리 |
| --- | --- | --- |
| `oversized_line_errors` | `MAX_LINE_BYTES`를 넘는 물리 행 | 나머지를 소비하고 source·line·type·length만 기록 |
| `encoding_errors` | UTF-8로 해석할 수 없는 바이트 | source·line·type·length만 기록 |
| `format_errors` | Combined Log 구조와 불일치 | 정규표현식을 무작정 완화하지 않음 |
| `validation_errors` | 잘못된 IP·시각·상태 코드·경로 | 어떤 필드가 실패했는지 기록 |

파서가 발생시키는 예외도 단계에 맞게 구분한다.

```python
class LogFormatError(ValueError):
    """Combined Log 구조와 일치하지 않을 때 사용한다."""


class ValidationError(ValueError):
    """구조화된 필드의 값이 유효하지 않을 때 사용한다."""
```

오류는 한 행을 두 범주에 중복 계수하지 않는다. 분석이 끝난 뒤 실제 Python 식으로 다음 불변식을 검사한다.

```python
error_count = (
    quality["oversized_line_errors"]
    + quality["encoding_errors"]
    + quality["format_errors"]
    + quality["validation_errors"]
)

assert quality["total_lines"] == quality["parsed_lines"] + error_count
assert quality["parsed_lines"] == sum(summary["status"].values())
assert quality["parsed_lines"] == sum(summary["method"].values())
assert quality["parsed_lines"] == (
    quality["known_bytes_rows"] + quality["missing_bytes_rows"]
)
```

검증이 실패하면 후보 목록을 해석하기 전에 읽기·파싱·집계 로직을 먼저 수정한다.

## 4. 필드의 형식과 의미를 함께 검증한다

정규표현식은 문자열의 위치를 분리할 뿐, 값이 실제로 유효한지는 보장하지 않는다. 예를 들어 `999.999.999.999`는 공백이 없는 문자열이지만 IP 주소는 아니다.

먼저 이름 있는 그룹으로 Combined Log의 구조를 분리한다.

```python
import re

COMBINED_LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>[A-Z][A-Z-]*) (?P<target>\S+) '
    r'HTTP/(?P<http_version>[^"]+)" '
    r'(?P<status>[0-9]{3}) (?P<bytes>[0-9]+|-) '
    r'"(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)"$'
)


def extract_fields(line: str) -> dict[str, str]:
    match = COMBINED_LOG_PATTERN.fullmatch(
        strip_line_ending(line)
    )
    if match is None:
        raise LogFormatError("Combined Log 구조와 일치하지 않는다")
    return match.groupdict()
```

정규식 일치에 성공한 필드는 다음 단계에서 의미를 검증한다.

```python
import re
from datetime import datetime, timezone
from ipaddress import ip_address

MAX_RESPONSE_BYTES = (2 ** 63) - 1
MAX_RESPONSE_BYTES_DIGITS = 20


def validate_fields(fields: dict[str, str]) -> dict:
    try:
        address = ip_address(fields["ip"])
    except ValueError as error:
        raise ValidationError("유효하지 않은 IP 주소") from error

    try:
        timestamp = datetime.strptime(
            fields["timestamp"],
            "%d/%b/%Y:%H:%M:%S %z",
        ).astimezone(timezone.utc)
    except ValueError as error:
        raise ValidationError("유효하지 않은 timestamp") from error

    status_text = fields["status"]
    if re.fullmatch(r"[0-9]{3}", status_text) is None:
        raise ValidationError("상태 코드는 ASCII 숫자 세 자리여야 한다")

    try:
        status = int(status_text)
    except ValueError as error:
        raise ValidationError("상태 코드를 정수로 변환할 수 없다") from error

    if not 100 <= status <= 599:
        raise ValidationError("상태 코드는 100~599 범위여야 한다")

    method = fields["method"]
    if re.fullmatch(r"[A-Z][A-Z-]{0,15}", method) is None:
        raise ValidationError("요청 메서드 형식이 유효하지 않다")

    bytes_text = fields["bytes"]
    if bytes_text == "-":
        response_bytes = None
    else:
        if (
            re.fullmatch(r"[0-9]+", bytes_text) is None
            or len(bytes_text) > MAX_RESPONSE_BYTES_DIGITS
        ):
            raise ValidationError(
                "응답 바이트는 허용 길이의 ASCII 숫자여야 한다"
            )

        try:
            response_bytes = int(bytes_text)
        except ValueError as error:
            raise ValidationError(
                "응답 바이트를 정수로 변환할 수 없다"
            ) from error

        if response_bytes > MAX_RESPONSE_BYTES:
            raise ValidationError("응답 바이트가 허용 범위를 넘었다")

    return {
        "ip": str(address),
        "ip_version": address.version,
        "timestamp": timestamp,
        "method": method,
        "status": status,
        "bytes": response_bytes,
    }
```

`ip_address()`는 IPv6를 압축된 표준 표현으로 정리해 같은 주소가 여러 문자열 형태로 집계되는 문제를 줄인다. 다만 프록시·NAT 환경에서 접근 로그의 IP는 최종 사용자가 아니라 중간 장비일 수 있다. 신뢰할 수 있는 프록시 설정을 확인하지 않고 전달 헤더 값을 무조건 사용자 IP로 사용하지 않는다.

응답 바이트의 `-`는 응답 크기가 0이라는 뜻이 아니라 기록된 값이 없다는 뜻이다. 이를 `0`으로 바꾸면 평균과 합계를 왜곡할 수 있으므로 `None`과 누락 건수를 별도로 유지한다.

정규표현식의 `\d`는 유니코드 숫자도 허용하므로 로그 프로토콜의 숫자 경계에는 `[0-9]`를 사용한다. 바이트 문자열은 정수 변환 전에 자릿수와 `2**63 - 1` 범위를 검사한다. 이 검증은 수천 자리 숫자가 Python의 정수 변환 제한을 건드리거나 불필요한 계산 자원을 사용하게 하는 상황을 `validation_errors`로 분리한다.

## 5. URL 경로를 정규화한다

`urlsplit(target).path`만 호출하면 쿼리 문자열은 분리할 수 있지만 인코딩된 점(`%2e`), 역슬래시, 중복 슬래시, `..` 구간처럼 비교를 피하려는 표현은 그대로 남는다. 탐지 비교용 경로는 정규화하되, 정규화가 실제 웹 서버의 라우팅과 항상 같다고 가정하지 않는다.

```python
import re
from urllib.parse import unquote, urlsplit

MAX_TARGET_LENGTH = 4_096


def normalize_url_path(target: str) -> tuple[str, bool]:
    if not target or len(target) > MAX_TARGET_LENGTH:
        raise ValidationError("요청 target 길이가 허용 범위를 벗어났다")

    # origin-form의 `//path`가 URL의 host로 오인되지 않게 기준 URL을 붙인다.
    try:
        parsed_target = (
            urlsplit(f"https://log.invalid{target}")
            if target.startswith("/")
            else urlsplit(target)
        )
    except ValueError as error:
        raise ValidationError("요청 target을 URL로 분리할 수 없다") from error
    raw_path = parsed_target.path or "/"

    if re.search(r"%(?![0-9A-Fa-f]{2})", raw_path):
        raise ValidationError("경로의 퍼센트 인코딩이 잘못되었다")

    try:
        decoded = unquote(
            raw_path,
            encoding="utf-8",
            errors="strict",
        )
    except UnicodeDecodeError as error:
        raise ValidationError("경로의 퍼센트 인코딩이 잘못되었다") from error

    decoded = decoded.replace("\\", "/")
    if any(ord(character) < 32 or ord(character) == 127 for character in decoded):
        raise ValidationError("경로에 제어 문자가 포함되었다")

    segments = []
    for segment in decoded.split("/"):
        if segment in ("", "."):
            continue
        if segment == "..":
            if segments:
                segments.pop()
            continue
        segments.append(segment)

    normalized = "/" + "/".join(segments)
    return normalized, normalized != raw_path
```

```python
assert normalize_url_path("/login?token=secret")[0] == "/login"
assert normalize_url_path("/a/../.env")[0] == "/.env"
assert normalize_url_path("/%2e%2e/.git/config")[0] == "/.git/config"
assert normalize_url_path("//static///app.js")[0] == "/static/app.js"
```

검증된 필드와 정규화 결과는 하나의 레코드로 조립한다.

```python
def build_record(fields: dict[str, str]) -> dict:
    record = validate_fields(fields)
    normalized_path, normalization_changed = normalize_url_path(
        fields["target"]
    )
    record["normalized_path"] = normalized_path
    record["normalization_changed"] = normalization_changed
    return record
```

{% hint style="danger" %}
URL 경로를 `pathlib.Path.resolve()`로 정규화하지 않는다. `Path.resolve()`는 로컬 파일 시스템의 현재 디렉터리·심볼릭 링크를 해석하는 API이며 HTTP 요청 경로의 의미와 다르다. URL 정규화는 별도 함수에서 수행한다.
{% endhint %}

원문 경로와 정규화 경로는 서버 설정에 따라 다른 자원을 가리킬 수 있다. 따라서 `normalization_changed`를 레코드와 시간창 집계에 남기되 원문 경로 자체는 결과 파일에 저장하지 않는다. 재확인이 필요하면 승인된 환경에서 source와 line으로 원본 로그를 조회한다.

퍼센트 디코딩은 이 함수에서 한 번만 수행한다. `%252e`처럼 이중 인코딩된 값을 반복해서 디코딩할지는 웹 서버와 프레임워크의 실제 동작을 확인한 뒤 별도 규칙으로 결정한다.

## 6. 전체 건수 대신 5분 시간창의 특징을 만든다

전체 파일의 404 절대 건수만 사용하면 관찰 시간이 길거나 정상 요청이 많은 IP가 쉽게 임계값을 넘는다. 이 실습은 UTC 기준 5분 시간창별로 다음 특징을 만든다.

| 특징 | 의미 |
| --- | --- |
| `total_requests` | 시간창의 전체 요청 수 |
| `not_found_404` | 상태 코드가 404인 요청 수 |
| `not_found_rate` | `not_found_404 / total_requests` |
| `unique_404_paths` | 서로 다른 404 경로 수 |
| `sensitive_requests` | 민감 경로 요청 수 |
| `unique_sensitive_paths` | 서로 다른 민감 경로 수 |
| `sensitive_2xx` | 민감 경로에서 성공한 2xx 응답 수 |
| `normalization_changed_requests` | 원문과 정규화 경로가 달라진 요청 수 |

```python
def floor_to_five_minutes(timestamp):
    minute = timestamp.minute - timestamp.minute % 5
    return timestamp.replace(
        minute=minute,
        second=0,
        microsecond=0,
    )
```

정상 레코드가 0건이어도 품질 보고서를 저장할 수 있도록 빈 특징표의 열과 dtype을 먼저 고정한다.

```python
import pandas as pd

FEATURE_DTYPES = {
    "window_start": "datetime64[ns, UTC]",
    "ip": "string",
    "total_requests": "Int64",
    "not_found_404": "Int64",
    "unique_404_paths": "Int64",
    "sensitive_requests": "Int64",
    "unique_sensitive_paths": "Int64",
    "sensitive_2xx": "Int64",
    "normalization_changed_requests": "Int64",
}


def empty_feature_table() -> pd.DataFrame:
    return pd.DataFrame({
        column: pd.Series(dtype=dtype)
        for column, dtype in FEATURE_DTYPES.items()
    })
```

`build_features()`는 집계를 시작하기 전에 정상 레코드가 비어 있는지 확인하고 `empty_feature_table()`을 반환한다. 전부 오류인 입력에서도 `quality-report.csv`와 빈 schema의 특징표를 만들며, 빈 DataFrame에서 존재하지 않는 `window_start`나 `ip` 열을 조회하지 않는다.

민감 경로 목록은 `.env`, `.git`, `wp-admin`, `phpmyadmin`, `server-status`처럼 교육용으로 명시한다. 실제 분석에서는 자산과 애플리케이션의 공개 경로 정책에 맞게 목록과 예외를 관리한다.

### 6.1 스트리밍과 메모리의 경계를 정확히 이해한다

배치가 끝난 뒤 상세 DataFrame을 비워도 `Counter`에 고유 IP·경로·User-Agent를 계속 추가하면 누적 메모리는 고유값 수에 비례해 증가한다. 따라서 “파일 크기와 관계없이 메모리가 일정하다”고 표현하면 안 된다.

- 상세 행 메모리는 `BATCH_SIZE`로 제한한다.
- 경로에서 숫자·UUID 같은 식별자를 route template으로 바꾸어 고유값 폭증을 줄인다.
- 시간순 로그는 완료된 5분 시간창을 결과로 내보낸 뒤 메모리에서 제거한다.
- 시간 역전 행은 별도 품질 지표로 기록하고 허용할 지연 범위를 정한다.
- 정확한 전체 고유값이 꼭 필요하지 않으면 상위 N개 또는 별도 저장소를 사용한다.

약 3GB 파일을 처리할 때에도 배치 크기뿐 아니라 고유 경로 수와 시간창 상태의 크기를 함께 관찰한다.

## 7. NumPy 조건 마스크로 조사 후보를 선별한다

다음 임계값은 fixture의 개념을 설명하기 위한 **교육용 규칙**이다. 모든 서비스에 적용할 보편적인 보안 기준이 아니다.

```python
import numpy as np

total = features["total_requests"].to_numpy(dtype=np.int64)
not_found = features["not_found_404"].to_numpy(dtype=np.int64)
unique_404 = features["unique_404_paths"].to_numpy(dtype=np.int64)
sensitive = features["sensitive_requests"].to_numpy(dtype=np.int64)
unique_sensitive = features["unique_sensitive_paths"].to_numpy(dtype=np.int64)
sensitive_2xx = features["sensitive_2xx"].to_numpy(dtype=np.int64)

not_found_rate = np.divide(
    not_found,
    total,
    out=np.zeros(total.shape, dtype=float),
    where=total > 0,
)

scan_signal = (
    (not_found >= 8)
    & (not_found_rate >= 0.70)
    & (unique_404 >= 6)
)

sensitive_signal = (
    (sensitive_2xx >= 1)
    | ((sensitive >= 3) & (unique_sensitive >= 2))
)

candidate_mask = scan_signal | sensitive_signal

features["not_found_rate"] = not_found_rate
features["candidate"] = candidate_mask
features["reason"] = np.select(
    [
        scan_signal & sensitive_signal,
        sensitive_2xx >= 1,
        sensitive_signal,
        scan_signal,
    ],
    [
        "scan+sensitive",
        "sensitive-success",
        "sensitive",
        "scan",
    ],
    default="-",
)
```

이 코드는 05-7에서 배운 ndarray 변환, `np.divide()`, 벡터 비교, 논리 연산, bool 마스크를 실제 분석 기준에 사용한다.

### 7.1 세 조건을 함께 사용하는 이유

- `404 >= 8`: 너무 적은 표본에서 비율이 커지는 문제를 줄인다.
- `404 비율 >= 70%`: 정상 요청이 많은 IP의 단순 누적 404를 구분한다.
- `고유 404 경로 >= 6`: 같은 잘못된 링크의 반복과 여러 경로 탐색을 구분한다.
- `민감 경로 2xx >= 1`: 반복 횟수가 적어도 노출 가능성이 있는 성공 응답을 놓치지 않는다.

임계값을 바꿀 때에는 후보 수만 보지 않고 fixture의 정상 사례가 얼마나 잘못 포함되는지 함께 확인한다. 후보 IP가 승인된 점검 도구라고 확인되더라도 결과 행을 삭제하지 않고 `approved_scanner` 같은 맥락 열을 추가한다. 그래야 탐지 신호와 운영 판정을 구분할 수 있다.

## 8. 민감정보를 최소화하고 가명 처리한다

분석에 필요하지 않은 정보는 애초에 누적하지 않는다.

- 쿼리 문자열은 경로 분리 후 즉시 버린다.
- referrer와 User-Agent는 이번 분석 목표에 필요하지 않으므로 집계하지 않는다.
- 오류 원문과 행 해시는 저장하지 않고 source·line·type·length만 기록한다.
- IP와 경로는 결과를 저장하기 직전에 서로 다른 namespace로 HMAC 가명 처리한다.

```python
import hashlib
import hmac
import os
from pathlib import Path


def pseudonymize(value: str, namespace: str, secret_key: bytes) -> str:
    message = f"{namespace}:{value}".encode("utf-8")
    digest = hmac.new(
        secret_key,
        message,
        hashlib.sha256,
    ).hexdigest()
    return f"{namespace}_{digest[:24]}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def masking_key_for_save(
    project_root: Path,
    input_paths,
) -> bytes:
    project_root = project_root.resolve()
    approved_training_files = {
        (
            project_root
            / "fixtures"
            / "05-text-processing"
            / "web-access.log"
        ).resolve(): (
            "255cee6add742d2ddbc52cd1840ba5c99f1fe319b8b2e362e5a66a1dfc1a4aff"
        ),
        (
            project_root
            / "fixtures"
            / "05-text-processing"
            / "web-access-invalid-utf8.log"
        ).resolve(): (
            "16ac8abb2f322704c0868b8036b7f6d6603de546cfeefb63b4cf3b91d8f963d1"
        ),
    }

    current_inputs = {
        Path(path).resolve()
        for path in input_paths
    }
    if not current_inputs:
        raise RuntimeError("저장할 입력 경로가 없다")
    if any(not path.is_file() for path in current_inputs):
        raise FileNotFoundError("현재 입력 경로를 다시 확인해야 한다")

    configured_key = os.environ.get("LOG_MASKING_KEY")
    if configured_key:
        key = configured_key.encode("utf-8")
        if len(key) < 32:
            raise RuntimeError("LOG_MASKING_KEY는 32바이트 이상이어야 한다")
        return key

    if current_inputs.issubset(approved_training_files):
        hashes_match = all(
            hmac.compare_digest(
                file_sha256(path),
                approved_training_files[path],
            )
            for path in current_inputs
        )
        if hashes_match:
            return b"public-training-key-not-for-real-logs"

    raise RuntimeError(
        "실제 로그 결과 저장에는 LOG_MASKING_KEY가 필요하다"
    )
```

키는 모듈 전역 변수에 저장하거나 첫 실행 결과를 캐시하지 않는다. 저장 함수가 호출될 때마다 **현재 `input_paths`**를 받아 경로 존재 여부와 교육용 fixture 여부를 다시 확인한다. 지정된 경로이면서 생성 fixture의 고정 SHA-256까지 일치할 때에만 공개 교육용 키를 반환한다. 같은 이름의 변조 fixture, 다른 입력, 실제 로그가 하나라도 섞이면 `LOG_MASKING_KEY`가 없을 때 저장을 중단한다. 교육용 키를 실제 로그에 사용하지 않는다.

여기서 전체 fixture SHA-256은 공개 학습 파일의 무결성을 확인하는 식별자이다. 오류 행별 해시를 결과에 저장하는 방식과 다르며, 오류 샘플 schema에는 여전히 source·line·type·length만 남긴다.

일반 `hash(ip)`는 실행할 때마다 값이 달라질 수 있고, 키가 없는 단순 SHA-256은 가능한 IP 범위를 대입해 원문을 추측하기 쉽다. HMAC 키는 충분히 긴 무작위 값으로 만들고 Notebook·Git 저장소·결과 파일에 기록하지 않는다. 같은 키를 사용하면 여러 실행 결과를 연결할 수 있으므로 키 보관 기간도 데이터 보존 정책에 포함한다.

경로를 사람이 읽을 수 있어야 한다면 `/products/:id`처럼 승인된 route template을 먼저 적용한다. 템플릿이 없는 원문 경로는 HMAC 별칭으로 저장한다. IP나 경로를 가명 처리해도 시간·요청 패턴과 결합하면 재식별 가능성이 있으므로 공유 범위를 제한한다.

## 9. staging 디렉터리를 한 번에 게시한다

파일마다 최종 디렉터리에 바로 저장하면 실행 중간에 일부 산출물만 보일 수 있다. 모든 파일을 숨김 staging 디렉터리에 먼저 쓰고 검증이 끝난 뒤 디렉터리 자체를 최종 run 이름으로 바꾼다. staging과 최종 run을 같은 출력 루트 아래에 두어 rename이 같은 파일 시스템에서 수행되게 한다.

```python
from pathlib import Path


def prepare_output_root(project_root: Path) -> Path:
    project_root = project_root.resolve()
    if not (project_root / "requirements.txt").is_file():
        raise RuntimeError("프로젝트 루트에서 Notebook을 실행해야 한다")

    output_parent = project_root / "outputs"
    if output_parent.exists() and output_parent.is_symlink():
        raise RuntimeError("outputs 디렉터리는 심볼릭 링크일 수 없다")

    output_parent.mkdir(exist_ok=True, mode=0o700)
    output_parent = output_parent.resolve()
    if not output_parent.is_relative_to(project_root):
        raise RuntimeError("outputs 디렉터리가 프로젝트 밖을 가리킨다")

    output_root = output_parent / "web-log-analysis"
    if output_root.exists() and output_root.is_symlink():
        raise RuntimeError("출력 루트는 심볼릭 링크일 수 없다")

    output_root.mkdir(exist_ok=True, mode=0o700)
    output_root = output_root.resolve()
    if not output_root.is_relative_to(project_root):
        raise RuntimeError("출력 루트가 프로젝트 밖을 가리킨다")

    output_root.chmod(0o700)
    return output_root
```

staging 안의 개별 파일은 새 파일로 만들고 flush·`fsync()`를 완료한다.

```python
import os
from pathlib import Path


def write_staged_csv(frame, staging_dir: Path, filename: str) -> None:
    if Path(filename).name != filename:
        raise ValueError("파일 이름에 경로 구간을 넣을 수 없다")

    destination = staging_dir / filename
    with destination.open(
        "x",
        encoding="utf-8",
        newline="",
    ) as file:
        frame.to_csv(file, index=False)
        file.flush()
        os.fsync(file.fileno())

    destination.chmod(0o600)
```

JSON도 같은 원칙으로 staging 안에 새 파일로 쓴다. 게시할 산출물 집합은 다음과 같이 고정한다.

| 파일 | 내용 |
| --- | --- |
| `quality-report.csv` | 정상 행과 오류 유형별 건수, 누락 바이트 수 |
| `status-counts.csv` | 상태 코드별 집계 |
| `window-features.csv` | 가명 IP와 5분 시간창 특징 |
| `triage-candidates.csv` | 가명 처리한 후보와 탐지 이유 |
| `manifest.json` | 입력 파일 이름·해시, 규칙 버전, 임계값, 실행 시각 |

저장 함수는 현재 입력 경로로 가명 키를 다시 검증하고, 전체 산출물이 준비된 경우에만 staging 디렉터리를 게시한다.

```python
from datetime import datetime, timezone
import os
from pathlib import Path
import secrets
import shutil

EXPECTED_OUTPUTS = {
    "quality-report.csv",
    "status-counts.csv",
    "window-features.csv",
    "triage-candidates.csv",
    "manifest.json",
}


def cleanup_failed_staging(staging_dir: Path, output_root: Path) -> None:
    candidate = staging_dir.resolve(strict=False)
    if (
        candidate.parent != output_root
        or not candidate.name.startswith(".staging-")
    ):
        raise RuntimeError("검증되지 않은 경로는 정리할 수 없다")

    if staging_dir.is_symlink():
        staging_dir.unlink()
    elif staging_dir.exists():
        shutil.rmtree(staging_dir)


def publish_run(
    project_root: Path,
    input_paths,
    write_outputs,
) -> Path:
    output_root = prepare_output_root(project_root)
    current_input_paths = tuple(
        Path(path)
        for path in input_paths
    )

    # 키는 현재 입력을 확인한 이 저장 호출 안에서만 유지한다.
    masking_key = masking_key_for_save(
        project_root,
        current_input_paths,
    )

    run_id = datetime.now(timezone.utc).strftime(
        "run-%Y%m%dT%H%M%SZ"
    )
    published_dir = output_root / run_id
    if published_dir.exists():
        raise FileExistsError(published_dir)

    staging_dir = output_root / (
        f".staging-{run_id}-{secrets.token_hex(8)}"
    )
    staging_dir.mkdir(mode=0o700, exist_ok=False)

    try:
        write_outputs(staging_dir, masking_key)

        entries = list(staging_dir.iterdir())
        if any(path.is_symlink() or not path.is_file() for path in entries):
            raise RuntimeError("staging에는 일반 파일만 둘 수 있다")

        actual_outputs = {path.name for path in entries}
        if actual_outputs != EXPECTED_OUTPUTS:
            raise RuntimeError("산출물 집합이 완료되지 않았다")

        for path in entries:
            path.chmod(0o600)

        # 같은 출력 루트 안의 디렉터리 rename으로 한 번에 게시한다.
        os.replace(staging_dir, published_dir)
        return published_dir
    except Exception:
        cleanup_failed_staging(staging_dir, output_root)
        raise
    finally:
        del masking_key
```

`write_outputs(staging_dir, masking_key)`는 모든 DataFrame을 가명 처리해 저장하고 `manifest.json`을 마지막에 작성하는 함수이다. 절대 입력 경로, HMAC 키, 원문 IP, 원문 target, 쿼리, User-Agent, 오류 원문은 산출물에 포함하지 않는다. 입력 파일 전체 해시는 스트리밍으로 읽는 동안 계산해 3GB 파일을 다시 읽지 않도록 한다.

`os.replace(staging_dir, published_dir)`가 성공하기 전에는 최종 run 디렉터리가 존재하지 않는다. 어느 파일에서든 예외가 발생하면 검증된 `.staging-*` 경로만 정리하고 불완전한 실행을 게시하지 않는다.

## 10. 오류와 경계 사례

| 상황 | 잘못된 처리 | 권장 처리 |
| --- | --- | --- |
| 잘못된 UTF-8 | `errors="replace"`로 계속 진행 | strict 디코딩 후 `encoding_errors`로 분리 |
| 매우 긴 물리 행 | 일반 반복자로 한 번에 읽거나 조각을 각각 파싱 | 제한 `readline()`으로 읽고 나머지를 소비한 뒤 과대 행 1건으로 분류 |
| 줄 끝의 `n` | `rstrip("\\n")` 사용 | `rstrip("\r\n")`로 줄바꿈만 제거 |
| `999.1.1.1` | 문자열 IP로 집계 | `ip_address()`에서 검증 오류 처리 |
| 유니코드 숫자·수천 자리 bytes | `\d` 일치 뒤 바로 `int()` 호출 | ASCII `[0-9]`, 자릿수, 정수 범위를 먼저 검증 |
| bytes가 `-` | 0으로 변환 | `None`과 누락 건수로 보존 |
| `/a/../.env` | 원문 경로만 비교 | 정규화 경로와 변경 여부를 사용 |
| `/item/1001`, `/item/1002` | 모두 고유 경로로 누적 | `/item/:id` route template 적용 |
| 404 절대 건수 증가 | 즉시 공격으로 판단 | 시간창·비율·고유 경로를 함께 비교 |
| 프록시 출발지 IP | 사용자 한 명으로 단정 | 프록시·NAT·승인 자산 맥락 확인 |
| 후보 IP 출력 | 원문 IP를 CSV로 저장 | HMAC 가명값과 탐지 이유만 저장 |
| 전역 가명 키 | 분석 시작 때 한 번 정한 키를 계속 재사용 | 저장 호출마다 현재 입력 경로와 환경변수를 검증 |
| 결과 파일을 하나씩 게시 | 실행 중 일부 파일만 최종 경로에 노출 | 숨김 staging 전체를 검증한 뒤 디렉터리 rename |
| 저장 중 예외 | 불완전 staging을 남김 | 검증된 `.staging-*`만 정리하고 게시하지 않음 |

## 11. 실습

### 실습 1. 파서와 오류 분류 완성

학습자용 Notebook에서 다음 함수를 완성한다.

```python
def strip_line_ending(line: str) -> str:
    # TODO: LF와 CRLF만 제거한다.
    ...


def validate_fields(fields: dict[str, str]) -> dict:
    # TODO: IP, timestamp, status, bytes를 검증한다.
    ...


def normalize_url_path(target: str) -> tuple[str, bool]:
    # TODO: 쿼리 제거, strict percent decoding, dot-segment 처리를 수행한다.
    ...
```

정상 IPv4·IPv6, CRLF, 잘못된 IP·시각·상태 코드·UTF-8 fixture를 실행하고 오류 범주별 건수를 기록한다. `MAX_LINE_BYTES`보다 긴 한 행도 추가해 다음 정상 행이 별도 물리 행으로 처리되는지 확인한다.

### 실습 2. 5분 특징 생성

1. timestamp를 UTC로 변환한다.
2. `floor_to_five_minutes()`로 시간창을 만든다.
3. 시간창과 IP별 전체 요청·404·고유 404 경로를 집계한다.
4. 민감 경로 요청·고유 민감 경로·민감 경로 2xx를 집계한다.
5. 완료된 시간창을 내보내고 메모리에서 제거한다.

### 실습 3. 탐지 기준 설명

NumPy 조건 마스크를 실행한 뒤 다음 질문에 답한다.

1. 동일한 `favicon.ico` 404가 많이 발생한 IP는 왜 제외되었는가?
2. 높은 요청량의 NAT IP는 왜 제외되었는가?
3. 민감 경로의 2xx 한 건을 높은 우선순위로 본 이유는 무엇인가?
4. 승인된 점검 도구가 후보에 남아 있어야 하는 이유는 무엇인가?
5. 5분을 1분 또는 30분으로 바꾸면 후보가 어떻게 달라지는가?

### 실습 4. 안전한 결과 저장

1. 저장 직전에 현재 `input_paths`를 바꿔 `LOG_MASKING_KEY`가 없을 때 실제 로그 저장이 중단되는지 확인한다.
2. IP와 비정형 경로가 HMAC 별칭으로 저장되는지 확인한다.
3. 실행 도중 의도적으로 예외를 발생시켜 `.staging-*`가 정리되고 최종 run이 게시되지 않는지 확인한다.
4. 정상 실행에서는 예상한 다섯 산출물이 디렉터리 rename과 함께 한 번에 보이는지 확인한다.
5. 결과 CSV에 쿼리·User-Agent·원문·행 해시가 없는지 검색한다.
6. `manifest.json`의 임계값과 품질 건수로 실행 조건을 재현할 수 있는지 확인한다.

## 12. 자기점검

- [ ] 인코딩 오류와 로그 형식 오류가 왜 다른지 설명할 수 있는가?
- [ ] 과대 행을 끝까지 소비하지 않으면 다음 행 경계가 왜 깨지는지 설명할 수 있는가?
- [ ] `rstrip("\\n")`이 실제 개행을 제거하지 않는 이유를 설명할 수 있는가?
- [ ] 정규표현식 일치 뒤에도 IP와 상태 코드를 검증해야 하는 이유를 설명할 수 있는가?
- [ ] `\d` 대신 `[0-9]`를 사용하고 정수 자릿수를 제한하는 이유를 설명할 수 있는가?
- [ ] URL 경로 정규화와 파일 시스템 경로 해석의 차이를 설명할 수 있는가?
- [ ] 404 절대 건수보다 비율과 고유 경로 수를 함께 보는 이유를 설명할 수 있는가?
- [ ] NumPy bool 마스크가 어떤 행을 후보로 선택하는지 추적할 수 있는가?
- [ ] 가명 처리와 익명화가 같지 않은 이유를 설명할 수 있는가?
- [ ] 배치 처리에서도 고유값 수에 따라 메모리가 증가할 수 있음을 설명할 수 있는가?
- [ ] 결과에 원문 IP·쿼리·User-Agent·오류 원문이 남지 않았는지 확인할 수 있는가?
- [ ] 저장 시점의 입력 경로로 키 정책을 다시 확인할 수 있는가?
- [ ] staging 디렉터리 게시가 파일별 저장보다 안전한 이유를 설명할 수 있는가?

## 13. 응용 인사이트

### 13.1 탐지는 데이터 품질 위에서 동작한다

오류율이 갑자기 늘었다면 공격이 아니라 로그 형식 변경, 프록시 추가, 인코딩 문제일 수 있다. 탐지 지표와 데이터 품질 지표를 같은 실행 결과에 남겨야 잘못된 경보를 설명할 수 있다.

### 13.2 정규화는 관찰 기준이지 정답이 아니다

분석기가 만든 정규화 경로와 웹 서버가 실제로 처리한 경로가 다를 수 있다. 정규화가 바뀐 행을 별도 표시하고 중요한 후보는 서버 설정과 원본 이벤트로 다시 확인한다.

### 13.3 임계값은 서비스 맥락과 함께 버전 관리한다

교육용 `8건·70%·6개 경로` 기준은 학습 fixture의 오탐과 미탐을 비교하기 위한 출발점이다. 실무에서는 평상시 분포, 관찰 시간, 자산 종류, 승인된 자동화 도구를 반영해 조정하고 규칙 버전과 변경 이유를 manifest에 남긴다.

### 13.4 가명 처리도 접근 통제가 필요하다

같은 HMAC 키로 만든 별칭은 여러 날짜의 행동을 연결할 수 있다. 분석 편의성이 높아지는 만큼 키 접근 권한, 보관 기간, 결과 공유 범위를 함께 설계해야 한다.

### 13.5 후보와 사고 판정을 분리한다

반복 404나 민감 경로 요청은 후속 조사를 시작할 신호이다. 공격 여부를 판정하려면 승인된 스캐너 목록, 대상 자산, 인증 로그, 응답 내용, 변경 기록 같은 추가 증거가 필요하다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 두 fixture를 실행해 과대 행·인코딩·형식·검증 오류를 구분했다.
- [ ] IPv4와 IPv6를 검증하고 요청 경로를 비교용 형태로 정규화했다.
- [ ] 5분 시간창 특징과 데이터 품질 불변식을 검증했다.
- [ ] NumPy 조건 마스크로 후보와 탐지 이유를 생성했다.
- [ ] 정상 반복 404와 탐색 형태 요청의 차이를 설명했다.
- [ ] IP와 경로를 가명 처리하고 원문 민감정보를 저장하지 않았다.
- [ ] 현재 입력 경로로 가명 키를 검증했다.
- [ ] staging 전체를 검증하고 디렉터리 rename으로 결과를 게시했다.
- [ ] 실패한 staging을 정리하고 불완전한 run을 게시하지 않았다.
- [ ] 후보와 침해 확정을 구분해 분석 결론을 작성했다.
{% endhint %}

---

다음 장: [06. 네트워크 프로그래밍](../06-network-programming.md)
