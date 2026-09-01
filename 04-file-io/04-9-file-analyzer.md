# 04-9. 파일 분석기 종합 실습

04장에서 학습한 경로 검증, 파일 조작, 텍스트·바이너리, 인코딩, CSV·JSON, 스트리밍, 오류 복구, 원자적 저장을 하나의 프로그램으로 연결한다. 완성한 분석기는 허가된 로컬 파일을 실행하거나 변경하지 않고 기본 정보와 형식별 통계를 JSON 보고서로 저장한다.

{% hint style="info" %}
### 🧭 종합 실습 목표

- 파일 분석 요구사항을 작은 함수로 분리한다.
- 매직 바이트로 대표적인 파일 형식을 추정한다.
- 원본 파일을 바이너리와 텍스트 관점에서 읽기 전용으로 확인한다.
- 큰 텍스트 파일을 한 줄씩 읽어 기초 통계를 계산한다.
- CSV와 JSON에 형식별 분석을 적용한다.
- 복구 가능한 형식 오류와 전체 작업 실패를 구분한다.
- 완성된 보고서를 임시 파일을 거쳐 안전하게 저장한다.
- 정상·오류·경계 시나리오를 재현 가능한 결과로 검증한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | 경로 검증, 읽기 전용 분석, 스트리밍 해시·텍스트 통계, JSON 보고서 |
| 권장 | 파일 헤더 추정, CSV·JSON 형식 오류 보존, 원자적 저장, 인수 조건 검증 |
| 심화 | 크기 제한, CSV 구조 품질, 여러 파일 배치 분석, 더 강한 파일 형식 식별 |

## 선행 지식

04-1부터 04-8까지 완료해야 한다.

| 선행 절 | 이 프로젝트에서 사용하는 개념 |
| --- | --- |
| 04-1 | 절대·상대 경로, `Path`, 경로 검증 |
| 04-2 | 파일·디렉터리 메타데이터와 입출력 경로 충돌 정책 |
| 04-3 | 텍스트 파일 모드와 `with` 문 |
| 04-4 | 인코딩·`bytes`·16진수 표현·파일 헤더 |
| 04-5 | CSV 파싱과 행·열 검증 |
| 04-6 | JSON 파싱·검증·직렬화 |
| 04-7 | 스트리밍, 제너레이터, 오류 복구 |
| 04-8 | 임시 파일, 검증, 원자적 교체 |

## 제공 코드

[전체 `file_analyzer.py` 코드 보기](https://github.com/zxz3650/Python/blob/master/examples/04-file-analyzer/file_analyzer.py)

제공 코드는 학습 기준 구현이다. 코드를 먼저 복사하기보다 요구사항과 인수 조건을 읽고 함수별로 구현한 뒤 비교한다.

[셀 단위 검증 노트북](../notebooks/04-9-file-analyzer.ipynb)은 직접 구현을 마친 뒤 전체 흐름을 다시 확인하는 풀이 검증 자료다.

## 1. 프로젝트 개요

### 1.1 문제 상황

파일을 본격적으로 파싱하거나 다른 도구에 전달하기 전에 다음 질문에 답하는 1차 분석기를 만든다.

- 경로가 존재하며 일반 파일인가?
- 파일의 이름·확장자·크기·수정 시각은 무엇인가?
- 현재 내용의 SHA-256 해시는 무엇인가?
- 알려진 파일 헤더가 있는가?
- UTF-8 텍스트로 다룰 수 있는가?
- 텍스트, CSV 또는 JSON이라면 어떤 기초 통계를 얻을 수 있는가?
- 분석 중 발생한 형식 오류를 재현할 정보가 보고서에 남는가?

이 분석기의 목적은 파일 내용을 깊게 해석하거나 안전성을 판정하는 것이 아니라 **다음 분석 단계에 필요한 기초 사실을 수집하는 것**이다.

### 1.2 프로젝트 경계

이 프로젝트에서 하지 않는 작업은 다음과 같다.

- 파일 실행, 동적 라이브러리 로드, 매크로 실행
- 압축 파일 해제와 내부 파일 자동 실행
- 네트워크 전송 또는 외부 서비스 업로드
- 악성·정상 여부의 단정
- 파일 복구·삭제·격리
- 권한이 없는 시스템과 다른 사용자의 파일 분석

{% hint style="warning" %}
교사가 제공하거나 학습자가 직접 만든 허가된 파일만 별도의 학습 디렉터리에서 분석한다. 파일 헤더와 해시는 형식 및 내용 비교 정보일 뿐 안전성·신뢰성·작성자 신원을 증명하지 않는다.
{% endhint %}

## 2. 인수 조건

프로그램은 다음 조건을 만족해야 한다.

### 2.1 입력과 원본 보호

- 존재하는 일반 파일만 분석한다.
- 디렉터리와 존재하지 않는 경로는 설명 가능한 오류로 거부한다.
- 분석 대상은 읽기 모드 또는 바이너리 읽기 모드로만 연다.
- 보고서 이름은 원본 이름 뒤에 `.analysis.json`을 붙인다.
- 분석 전후 원본의 SHA-256 값이 같다.

### 2.2 공통 보고서

- 정규화된 경로·이름·확장자·바이트 크기·UTC 수정 시각을 포함한다.
- 전체 파일을 한 번에 읽지 않고 SHA-256을 계산한다.
- 앞 16바이트를 16진수로 기록한다.
- 알려진 헤더라면 추정 형식·예상 확장자·확장자 일치 여부를 기록한다.
- 텍스트·바이너리·알 수 없음 중 하나로 분류한다.

### 2.3 형식별 분석

- UTF-8 텍스트는 전체 행·빈 행·최대 행 길이를 집계한다.
- `.csv` 텍스트는 헤더·데이터 레코드 수·최대 열 수·빈 필드와 헤더 열 수가 다른 레코드 수를 집계한다.
- `.json` 텍스트는 중복 키와 비표준 숫자를 거부하고 최상위 자료형·항목 수를 기록한다.
- CSV·JSON 형식 오류는 가능한 경우 `format_error`에 유형과 메시지를 남긴다.
- 바이너리 또는 인코딩을 확인할 수 없는 파일은 텍스트 형식 분석을 생략한다.

### 2.4 출력과 실패

- 보고서는 UTF-8 JSON으로 저장한다.
- 같은 디렉터리의 고유한 임시 파일에 완성한 뒤 최종 경로로 교체한다.
- 저장 실패 시 임시 파일을 정리한다.
- 성공은 종료 코드 `0`, 처리할 수 없는 입력 또는 저장 실패는 종료 코드 `1`로 구분한다.

## 3. 함수 책임과 전체 흐름

| 함수 | 입력 | 책임 | 반환 또는 실패 |
| --- | --- | --- | --- |
| `calculate_sha256()` | 파일 경로 | 청크 단위 해시 계산 | 16진수 문자열 |
| `identify_file_header()` | 파일 경로 | 대표 시그니처와 확장자 비교 | 헤더 정보 딕셔너리 |
| `classify_content()` | 파일 경로 | 표본으로 텍스트·바이너리 추정 | 분류 딕셔너리 |
| `analyze_text()` | UTF-8 텍스트 경로 | 행 통계 계산 | 텍스트 통계 |
| `analyze_csv()` | CSV 경로 | CSV 구조 통계 계산 | CSV 통계 또는 `csv.Error` |
| `analyze_json()` | JSON 경로 | JSON 최상위 구조 계산 | JSON 통계 또는 JSON 문법·정책 오류 |
| `analyze_file()` | 입력 경로 | 검증과 분석 결과 조립 | 전체 보고서 |
| `save_report()` | 보고서·출력 경로 | 임시 파일 쓰기와 교체 | 성공 또는 저장 예외 |
| `main()` | 사용자 입력 | 오류 경계와 종료 코드 | 정수 종료 코드 |

```text
입력 경로
→ 존재·일반 파일 확인
→ 메타데이터와 SHA-256 계산
→ 파일 헤더와 확장자 비교
→ 텍스트·바이너리 분류
→ 텍스트 기본 통계
→ CSV 또는 JSON 형식 분석
→ 복구 가능한 형식 오류 보존
→ JSON 보고서 안전 저장
→ 저장 결과 재검증
```

각 함수는 한 가지 책임만 맡고, `analyze_file()`이 결과를 조립하며, `main()`이 사용자에게 보여 줄 오류와 종료 코드를 결정한다.

## 4. 경로 검증과 메타데이터

```python
resolved = path.expanduser().resolve()

if not resolved.exists():
    raise FileNotFoundError(f"파일이 없다: {resolved}")
if not resolved.is_file():
    raise ValueError(f"일반 파일이 아니다: {resolved}")

stat = resolved.stat()
```

`expanduser()`는 `~`를 사용자 홈 디렉터리로 확장하고 `resolve()`는 분석에 사용할 절대 경로를 만든다. 존재 여부만 확인하지 않고 일반 파일인지도 검사한다. `stat()`은 크기와 수정 시각 등 파일 시스템 정보를 제공한다.

경로 검증 뒤 실제 읽기 전까지 파일이 바뀔 수 있으므로 이 코드는 강한 포렌식 증거 수집 도구가 아니다. 학습용 단일 사용자 디렉터리에서 기초 분석 흐름을 익히는 데 사용한다.

## 5. SHA-256을 스트리밍으로 계산하기

```python
import hashlib


def calculate_sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()
```

전체 파일을 한 번에 읽지 않고 1MiB 청크로 처리한다. 같은 SHA-256 값은 두 파일의 내용이 같다고 비교하는 강한 근거로 사용할 수 있지만 파일의 안전성, 출처 또는 작성자 신원을 증명하지는 않는다.

## 6. 파일 헤더로 형식 추정하기

파일 앞부분의 고정된 바이트를 **매직 바이트** 또는 **파일 시그니처**라고 한다. 확장자는 이름의 일부일 뿐 실제 내용을 보장하지 않는다.

```python
FILE_SIGNATURES = (
    ("PDF document", b"%PDF-", {".pdf"}),
    ("PNG image", b"\x89PNG\r\n\x1a\n", {".png"}),
    ("JPEG image", b"\xff\xd8\xff", {".jpg", ".jpeg"}),
    ("ZIP archive", b"PK\x03\x04", {".zip", ".docx"}),
    ("ELF executable", b"\x7fELF", {".elf", ".so", ""}),
)
```

```python
with path.open("rb") as file:
    header = file.read(4096)

for name, magic, extensions in FILE_SIGNATURES:
    if header.startswith(magic):
        detected_format = name
        extension_matches = path.suffix.lower() in extensions
        break
```

제공 분석기는 PDF, PNG, JPEG, GIF, 일부 ZIP 계열, GZIP, ELF, RAR, 7-Zip, 일부 Mach-O와 Windows PE 시그니처를 확인한다. 이 목록은 대표 예시이며 각 형식의 모든 변형을 판별하지 않는다. ZIP 기반 문서도 컨테이너 내부 구조를 확인하지 않으므로 실제 DOCX·XLSX·PPTX인지 단정할 수 없다.

### 6.1 Windows PE 시그니처 확인

Windows PE 파일은 선두의 `MZ`만으로 확정하지 않는다. DOS 헤더의 `e_lfanew`가 가리키는 파일 위치에 `PE\x00\x00` 시그니처가 있는지도 확인한다.

```python
if len(header) < 64 or not header.startswith(b"MZ"):
    is_pe = False
else:
    pe_offset = int.from_bytes(
        header[0x3C:0x40],
        byteorder="little",
    )

    if 0 < pe_offset <= path.stat().st_size - 4:
        with path.open("rb") as file:
            file.seek(pe_offset)
            is_pe = file.read(4) == b"PE\x00\x00"
    else:
        is_pe = False
```

파일 크기 범위를 먼저 검사해야 잘못된 오프셋을 무조건 따라가지 않는다. 이 검사도 PE 구조 전체를 검증하는 파서는 아니다.

### 6.2 헤더 보고서

보고서에는 추정 형식, 앞 16바이트의 16진수 표현, 예상 확장자, 확장자 일치 여부를 기록한다.

```json
{
  "detected_format": "PDF document",
  "header_hex": "25 50 44 46 2d 31 2e 37",
  "expected_extensions": [".pdf"],
  "extension_matches": false,
  "warning": "확장자 .txt와 식별된 파일 형식이 다르다."
}
```

헤더를 모르면 `unknown`으로 기록한다. `unknown`은 안전하거나 위험하다는 뜻이 아니라 현재 시그니처 목록으로 식별하지 못했다는 뜻이다.

## 7. 텍스트와 바이너리 분류

```python
with path.open("rb") as file:
    sample = file.read(8192)

if b"\x00" in sample:
    content_type = "binary"
else:
    sample.decode("utf-8")
    content_type = "text"
```

처음 8KiB에 NULL 바이트가 있는지 확인하고 UTF-8 디코딩을 시도한다. 다음 한계를 가진 간단한 휴리스틱이다.

- UTF-16 텍스트는 NULL 바이트 때문에 바이너리로 분류될 수 있다.
- 표본 뒤에 잘못된 UTF-8 바이트가 있어도 처음에는 텍스트로 분류될 수 있다.
- 표본 경계에서 여러 바이트 문자 하나가 잘리면 UTF-8 파일도 `unknown`이 될 수 있다.
- NULL 바이트가 없는 일부 바이너리도 텍스트로 오인할 수 있다.
- 빈 파일은 UTF-8 텍스트로 분류된다.

따라서 보고서의 값은 확정 판정이 아니라 **표본 기반 분류 결과**로 해석한다. 이후 전체 텍스트를 읽는 과정에서 발생한 `UnicodeDecodeError`도 별도로 처리한다.

## 8. 텍스트 기본 통계를 스트리밍으로 계산하기

```python
line_count = 0
blank_line_count = 0
max_line_length = 0

with path.open("r", encoding="utf-8") as file:
    for line in file:
        line_count += 1
        clean_line = line.rstrip("\r\n")

        if not clean_line.strip():
            blank_line_count += 1

        max_line_length = max(
            max_line_length,
            len(clean_line),
        )
```

현재 행을 중심으로 처리하므로 파일 전체 문자열을 메모리에 올리지 않는다. 다만 한 행 자체가 매우 크면 그 행 크기만큼 메모리를 사용할 수 있다. `max_line_length`는 Python 문자열의 문자 수이며 UTF-8 바이트 수와 다를 수 있다.

## 9. CSV 형식 분석

```python
with path.open("r", encoding="utf-8", newline="") as file:
    reader = csv.reader(file, strict=True)
    header = next(reader, [])

    for row in reader:
        row_count += 1
        max_column_count = max(max_column_count, len(row))

        has_empty_field = any(not value.strip() for value in row)
        has_wrong_column_count = len(row) != len(header)

        if not row or has_empty_field:
            rows_with_missing_values += 1
        if has_wrong_column_count:
            rows_with_wrong_column_count += 1
```

직접 `split(",")`하지 않는 이유는 따옴표 안의 쉼표와 줄바꿈 같은 CSV 규칙을 처리해야 하기 때문이다. `newline=""`은 `csv` 모듈이 줄바꿈을 올바르게 처리하도록 돕는다.

빈 필드와 열 개수 불일치는 다른 문제다. 제공 코드는 `rows_with_missing_values`와 `rows_with_wrong_column_count`로 두 지표를 분리한다. 헤더가 비었거나 중복되었을 때의 정책은 확장 과제에서 추가한다.

## 10. JSON 형식 분석

```python
with path.open("r", encoding="utf-8") as file:
    value = json.load(
        file,
        parse_constant=reject_nonstandard_constant,
        object_pairs_hook=reject_duplicate_keys,
    )

result = {"top_level_type": type(value).__name__}

if isinstance(value, dict):
    result["top_level_key_count"] = len(value)
elif isinstance(value, list):
    result["item_count"] = len(value)
```

이 구현은 단순성을 위해 JSON 전체를 메모리에 읽는다. 매우 큰 JSON에는 입력 크기 상한, JSON Lines 또는 별도의 스트리밍 파서가 필요하다. 깊게 중첩된 JSON도 많은 자원을 사용할 수 있으므로 신뢰할 수 없는 대용량 파일을 제한 없이 처리하지 않는다.

`reject_nonstandard_constant()`와 `reject_duplicate_keys()`는 04-6에서 구현한 입력 정책을 재사용한다. 문법 오류뿐 아니라 `NaN`·무한대와 중복 객체 키도 형식 오류로 보고서에 보존한다.

Python의 `bool`, `None`, `int` 같은 이름은 JSON의 `boolean`, `null`, `number`와 다르다. 보고서가 Python 자료형 이름을 사용할지 JSON 자료형 이름을 사용할지 문서화한다. 제공 코드는 `type(value).__name__`으로 Python 자료형 이름을 기록한다.

## 11. 복구 가능한 오류를 보고서에 보존하기

```python
try:
    report["format"] = {"json": analyze_json(path)}
except json.JSONDecodeError as exc:
    report["format_error"] = {
        "type": type(exc).__name__,
        "message": str(exc),
    }
```

JSON 문법 오류처럼 파일 메타데이터·해시·헤더 분석까지는 유효한 경우 형식 오류를 보고서에 남기고 공통 분석 결과를 보존한다.

다음 오류는 대개 파일 전체 분석을 완료할 수 없으므로 `main()`의 오류 경계에서 종료 코드 `1`로 처리한다.

- 파일 부재와 디렉터리 입력
- 읽기 권한 또는 기타 입출력 실패
- 전체 텍스트를 읽는 중 발생한 인코딩 오류
- 보고서를 저장할 수 없는 오류

오류 메시지에는 원인과 경로를 남기되 파일 내용, 비밀번호, 토큰, 개인정보를 불필요하게 포함하지 않는다.

## 12. 보고서를 안전하게 저장하고 다시 검증하기

04-8의 저장 계약을 그대로 적용한다.

```python
input_path = Path(raw_path).expanduser().resolve()
output_path = input_path.with_name(
    input_path.name + ".analysis.json"
)

ensure_different_paths(input_path, output_path)
save_report(report, output_path)

with output_path.open("r", encoding="utf-8") as file:
    restored = json.load(file)

if not isinstance(restored, dict):
    raise TypeError("보고서 최상위 값은 JSON 객체여야 한다")
```

입력 경로를 먼저 정규화한 뒤 출력 경로를 만든다. 그래야 사용자가 `~`가 포함된 경로를 입력해도 분석한 파일 옆에 보고서가 생성된다.

`save_report()`는 다음 조건을 만족해야 한다.

1. 출력 디렉터리에 고유한 임시 파일을 만든다.
2. 임시 경로를 파일을 연 직후 기록한다.
3. JSON 쓰기와 `flush()`·`fsync()`를 마친다.
4. 임시 파일을 닫은 뒤 최종 경로로 교체한다.
5. 어떤 단계에서 실패해도 남은 임시 파일을 정리한다.

저장 절차의 원자성·내구성·동시성 한계는 [04-8. 임시 파일과 원자적 저장](04-8-safe-output.md)을 참고한다.

## 13. 단계별 구현 순서

정답 파일을 한 번에 완성하지 않고 다음 순서로 구현한다.

1. `Path`로 입력 경로를 정규화하고 일반 파일을 확인한다.
2. 파일 크기·수정 시각·SHA-256만 포함한 최소 보고서를 만든다.
3. 대표 파일 헤더와 앞 16바이트를 추가한다.
4. 표본 기반 텍스트·바이너리 분류를 추가한다.
5. 텍스트 통계를 한 줄씩 계산한다.
6. 확장자에 따라 CSV·JSON 분석 함수를 호출한다.
7. 형식 오류를 `format_error`로 분리한다.
8. 임시 파일 교체 방식으로 보고서를 저장한다.
9. 정상·오류·경계 입력으로 인수 조건을 검증한다.

각 단계가 끝날 때 작은 입력으로 실행하고 보고서 키와 값을 `assert`로 확인한다.

## 14. 재현 가능한 실습 파일 만들기

다음 코드를 학습용 빈 디렉터리에서 한 번 실행한다.

```python
from pathlib import Path


folder = Path("analyzer-lab")
folder.mkdir(exist_ok=True)

(folder / "sample.txt").write_text(
    "첫째 줄\n\n셋째 줄\n",
    encoding="utf-8",
)
(folder / "sample.csv").write_text(
    "name,score\n민준,90\n서연,\n",
    encoding="utf-8",
)
(folder / "sample.json").write_text(
    '{"name": "학습 보고서", "count": 2}\n',
    encoding="utf-8",
)
(folder / "broken.json").write_text(
    '{"name": "닫히지 않은 JSON"\n',
    encoding="utf-8",
)
(folder / "renamed.txt").write_bytes(
    b"%PDF-1.7\ntraining sample\n"
)
(folder / "empty.bin").write_bytes(b"")
```

모두 학습자가 직접 생성한 무해한 입력이며 실제 실행 파일이나 운영 로그를 사용하지 않는다.

## 15. 실행

프로젝트 루트에서 다음 명령을 실행한다.

```bash
python examples/04-file-analyzer/file_analyzer.py
```

프롬프트에 분석할 파일 경로를 입력한다.

```text
분석할 파일 경로: analyzer-lab/sample.csv
분석 완료: <프로젝트 절대 경로>/analyzer-lab/sample.csv.analysis.json
```

완료 메시지는 실제 환경의 절대 경로를 표시하므로 앞부분은 실행 위치에 따라 달라진다.

운영체제에서 `python` 명령이 없고 `python3`만 제공하면 다음 명령을 사용한다.

```bash
python3 examples/04-file-analyzer/file_analyzer.py
```

## 16. 테스트 매트릭스

| 입력 | 확인할 결과 |
| --- | --- |
| `sample.txt` | `content_type == "text"`, 전체 3행, 빈 행 1개 |
| `sample.csv` | 헤더 2개, 데이터 2건, 빈 필드 레코드 1건, 열 수 불일치 0건 |
| `sample.json` | 최상위 `dict`, 최상위 키 2개 |
| `broken.json` | 공통 분석은 유지되고 `format_error`가 존재함 |
| `renamed.txt` | PDF 헤더 추정, 확장자 불일치 경고 |
| `empty.bin` | 크기 0, 빈 파일 정책에 따른 텍스트 분류와 0행 |
| 존재하지 않는 경로 | 보고서를 만들지 않고 종료 코드 `1` |
| 디렉터리 경로 | 일반 파일이 아니라는 오류와 종료 코드 `1` |

보고서를 다시 읽어 핵심 조건을 확인한다.

```python
import json
from pathlib import Path


report_path = Path(
    "analyzer-lab/sample.csv.analysis.json"
)

with report_path.open("r", encoding="utf-8") as file:
    report = json.load(file)

assert report["content_type"] == "text"
assert report["format"]["csv"]["data_row_count"] == 2
assert report["format"]["csv"]["rows_with_missing_values"] == 1
assert report["format"]["csv"]["rows_with_wrong_column_count"] == 0
assert len(report["sha256"]) == 64
```

원본 보호는 분석 전후 해시로 검증한다.

```python
target = Path("analyzer-lab/sample.csv")
before = calculate_sha256(target)
report = analyze_file(target)
after = calculate_sha256(target)

assert before == after
```

## 17. 실패·경계 시나리오

다음 입력을 추가로 설계한다.

- 읽기 권한이 없는 파일
- UTF-8 표본 뒤에 잘못된 바이트가 있는 파일
- UTF-16 텍스트
- 확장자와 파일 헤더가 다른 파일
- `MZ`로 시작하지만 유효한 PE 시그니처가 없는 파일
- 빈 헤더, 중복 헤더, 열 개수가 서로 다른 CSV
- 따옴표가 닫히지 않은 CSV
- 문법이 잘못된 JSON, 중복 객체 키, `NaN`·무한대
- 빈 파일과 매우 긴 한 줄
- 기존 보고서가 있는 상태에서 새 보고서 저장 실패

권한 오류는 운영체제와 실행 계정에 따라 재현 결과가 다를 수 있다. 재현이 어려우면 교사가 제공한 테스트 더블이나 실패 시나리오 설명으로 대체한다.

## 18. 확장 과제

1. 분석 대상의 최대 바이트 크기 정책을 추가한다.
2. CSV 빈 헤더·중복 헤더·필수 열 누락 정책을 추가한다.
3. 표본 경계에서 잘린 UTF-8 문자를 증분 디코더로 처리한다.
4. JSON 보고서를 최종 교체 전에 다시 읽어 필수 필드를 검증한다.
5. 출력 경로 충돌을 `resolve()`와 `samefile()`로 검사한다.
6. 여러 파일을 처리하되 파일별 성공과 실패를 분리한다.
7. 전체 배치의 정상·오류·건너뜀 건수를 보존 법칙으로 검증한다.
8. 05장에서 문자열 파싱과 DataFrame 집계를 연결한다.

## 19. 평가 루브릭

| 평가 항목 | 배점 | 확인 기준 |
| --- | ---: | --- |
| 입력과 원본 보호 | 15 | 경로·일반 파일 검증, 읽기 전용 처리, 원본 해시 유지 |
| 공통 분석 | 20 | 메타데이터, 청크 해시, 헤더, 내용 분류 |
| 형식별 분석 | 20 | 텍스트·CSV·JSON 함수 분리와 정확한 통계 |
| 오류 처리 | 15 | 형식 오류 보존, 파일 단위 실패 구분, 구체적 예외 |
| 안전한 저장 | 15 | 같은 디렉터리 임시 파일, 교체, 실패 정리 |
| 검증 | 10 | 정상·오류·경계 시나리오와 `assert` |
| 문서화 | 5 | 실행 방법, 입력 정책, 알려진 한계 |
| **합계** | **100** |  |

## 흔한 실수와 점검법

| 실수 | 점검법 |
| --- | --- |
| 확장자만 보고 형식을 확정함 | 헤더 추정 결과와 확장자를 따로 기록한다. |
| 매직 바이트를 악성 여부 판정으로 표현함 | 형식 추정과 안전성 판정을 구분한다. |
| SHA-256을 파일 안전성 또는 출처 증명으로 표현함 | 내용 비교용 해시임을 보고서에 적는다. |
| 표본 분류를 전체 파일의 확정 판정으로 표현함 | 휴리스틱의 오분류 사례를 테스트한다. |
| CSV의 빈 필드와 열 개수 불일치를 같은 값으로 집계함 | 두 지표를 분리한다. |
| 큰 JSON도 스트리밍이라고 표현함 | `json.load()`가 전체 값을 메모리에 만든다고 적는다. |
| 입력 경로를 정규화하기 전에 출력 이름을 만듦 | `expanduser().resolve()` 뒤 `with_name()`을 호출한다. |
| 최종 경로에 보고서를 직접 씀 | 04-8의 임시 파일 교체 절차를 사용한다. |
| 오류 메시지에 파일 내용이나 비밀값을 남김 | 재현에 필요한 최소 문맥만 기록한다. |

{% hint style="success" %}
### ✅ 완료 기준

- [ ] 원본 파일을 변경하지 않고 분석한다.
- [ ] 매직 바이트와 확장자의 차이를 설명한다.
- [ ] 헤더 추정·내용 분류·안전성 판정을 구분한다.
- [ ] SHA-256을 청크 단위로 계산한다.
- [ ] 큰 텍스트 파일을 한 줄씩 처리한다.
- [ ] 텍스트·CSV·JSON 분석 함수를 구분한다.
- [ ] 형식 오류와 전체 파일 실패를 서로 다른 경계에서 처리한다.
- [ ] JSON 결과를 임시 파일에 완성한 뒤 안전하게 교체한다.
- [ ] 보고서를 다시 읽어 필수 구조를 검증한다.
- [ ] 정상·오류·경계 입력을 재현 가능한 방식으로 검증한다.
- [ ] 도구의 범위와 알려진 한계를 문서화한다.
{% endhint %}

## 핵심 정리

- 파일 분석은 경로 검증과 원본 보호에서 시작한다.
- 확장자·헤더·표본 분류는 서로 다른 신호이며 어느 하나도 안전성을 증명하지 않는다.
- 해시와 텍스트 통계는 스트리밍할 수 있지만 `json.load()`는 전체 값을 메모리에 만든다.
- 복구 가능한 형식 오류는 공통 분석과 함께 보고서에 남기고, 전체 실패는 프로그램 경계에서 설명한다.
- 보고서는 임시 파일에 완성하고 검증한 뒤 최종 경로로 교체한다.
- 종합 실습의 완성은 코드 작성이 아니라 인수 조건과 실패 시나리오를 재현하는 데서 확인한다.

---

다음 장: [05. 텍스트 파싱과 데이터 분석](../05-text-processing.md)
