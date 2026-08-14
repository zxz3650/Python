# 04-7. 간단한 파일 분석기

04장에서 학습한 경로, 텍스트·바이너리, 인코딩, CSV·JSON, 스트리밍, 예외 처리를 하나의 프로그램으로 연결합니다. 완성한 분석기는 입력 파일을 변경하지 않고 기본 정보와 형식별 통계를 JSON 보고서로 저장합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 파일 분석 요구사항을 작은 함수로 분리합니다.
- 원본 파일을 바이너리와 텍스트 관점에서 안전하게 확인합니다.
- 큰 텍스트 파일을 한 줄씩 읽어 기초 통계를 계산합니다.
- CSV와 JSON에 형식별 분석을 적용합니다.
- 오류를 설명하고 결과를 임시 파일을 거쳐 안전하게 저장합니다.
{% endhint %}

## 선행 지식

04-1부터 04-6까지 완료해야 합니다.

## 완성 프로그램

[전체 `file_analyzer.py` 코드 보기](https://github.com/zxz3650/Python/blob/master/examples/04-file-analyzer/file_analyzer.py)

## 1. 무엇을 분석할 것인가

이 분석기의 목적은 파일 내용을 깊게 해석하는 것이 아니라 다음 단계의 분석이 가능한 파일인지 빠르게 확인하는 것입니다.

| 관점 | 확인 내용 | 사용하는 개념 |
| --- | --- | --- |
| 파일시스템 | 경로·이름·확장자·크기·수정 시각 | `pathlib`, `stat()` |
| 무결성 | 같은 파일인지 비교할 식별값 | `hashlib.sha256()` |
| 내용 분류 | 텍스트·바이너리·알 수 없음 | `bytes`, UTF-8 디코딩 |
| 텍스트 | 전체 행·빈 행·최대 행 길이 | 스트리밍 반복문 |
| CSV | 헤더·행·열·결측 행 | `csv.reader` |
| JSON | 문법·최상위 구조·항목 수 | `json.load` |
| 결과 | 분석 보고서 안전 저장 | 임시 파일과 `replace()` |

{% hint style="warning" %}
확장자는 파일의 성격을 암시할 뿐 실제 내용을 보장하지 않습니다. 먼저 내용을 분류한 뒤 확장자에 맞는 형식 분석을 적용합니다.
{% endhint %}

## 2. 전체 처리 흐름

```text
입력 경로
→ 존재·일반 파일 확인
→ 메타데이터와 SHA-256 계산
→ 텍스트·바이너리 분류
→ 텍스트 기본 통계
→ CSV 또는 JSON 형식 분석
→ 오류 정보 보존
→ JSON 보고서 안전 저장
```

## 3. 파일 검증과 메타데이터

```python
resolved = path.expanduser().resolve()

if not resolved.exists():
    raise FileNotFoundError(f"파일이 없습니다: {resolved}")
if not resolved.is_file():
    raise ValueError(f"일반 파일이 아닙니다: {resolved}")

stat = resolved.stat()
```

분석을 시작하기 전에 잘못된 경로와 디렉터리를 거부합니다. `stat()`은 크기와 수정 시각 등 파일시스템 정보를 제공합니다.

## 4. SHA-256을 스트리밍으로 계산

```python
def calculate_sha256(path):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()
```

전체 파일을 한 번에 읽지 않고 1MiB씩 처리합니다. SHA-256은 파일 내용이 같은지 비교하는 데 사용할 수 있지만 파일이 안전하다는 의미는 아닙니다.

## 5. 텍스트와 바이너리 분류

```python
with path.open("rb") as file:
    sample = file.read(8192)

if b"\x00" in sample:
    content_type = "binary"
else:
    sample.decode("utf-8")
    content_type = "text"
```

처음 8KiB에 NULL 바이트가 있는지 확인하고 UTF-8 디코딩을 시도합니다. 이것은 간단한 휴리스틱이므로 모든 파일 형식을 정확히 판별하지는 못합니다.

## 6. 텍스트 기본 통계

```python
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

현재 행만 메모리에 유지하므로 큰 텍스트 파일에도 사용할 수 있습니다.

## 7. CSV 형식 분석

```python
with path.open("r", encoding="utf-8", newline="") as file:
    reader = csv.reader(file)
    header = next(reader, [])

    for row in reader:
        row_count += 1
        max_column_count = max(max_column_count, len(row))

        if not row or any(not value.strip() for value in row):
            rows_with_missing_values += 1
```

직접 `split(",")`하지 않는 이유는 따옴표 안의 쉼표와 줄바꿈 같은 CSV 규칙을 처리해야 하기 때문입니다.

## 8. JSON 형식 분석

```python
with path.open("r", encoding="utf-8") as file:
    value = json.load(file)

result = {"top_level_type": type(value).__name__}

if isinstance(value, dict):
    result["top_level_key_count"] = len(value)
elif isinstance(value, list):
    result["item_count"] = len(value)
```

이 구현은 단순성을 위해 JSON 전체를 메모리에 읽습니다. 매우 큰 JSON은 JSON Lines 형식이나 스트리밍 파서가 필요하며 이 과정의 확장 과제로 남깁니다.

## 9. 형식 오류를 보고서에 보존

```python
try:
    report["format"] = {"json": analyze_json(path)}
except json.JSONDecodeError as exc:
    report["format_error"] = {
        "type": type(exc).__name__,
        "message": str(exc),
    }
```

형식 오류를 숨기거나 전체 프로그램을 즉시 종료하지 않고 분석 보고서에 남깁니다.

## 10. 결과를 안전하게 저장

```python
temporary_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
temporary_path.replace(output_path)
```

완성된 JSON을 임시 파일에 먼저 작성한 뒤 최종 경로로 교체합니다.

## 11. 실행

```bash
python examples/04-file-analyzer/file_analyzer.py
```

분석할 파일 경로를 입력하면 원본 파일 옆에 `.analysis.json` 보고서가 생성됩니다.

```text
sample.csv
sample.csv.analysis.json
```

## 12. 확인할 실패 사례

- 존재하지 않는 경로
- 파일 대신 디렉터리 입력
- 읽기 권한이 없는 파일
- UTF-8이 아닌 텍스트
- 열 개수가 서로 다른 CSV
- 문법이 잘못된 JSON
- 빈 파일과 매우 긴 한 줄

## 확장 과제

1. 분석 대상의 최대 크기 정책을 추가합니다.
2. CSV 헤더 중복과 행별 열 개수 불일치를 집계합니다.
3. JSON 보고서를 다시 읽어 필수 필드를 검증합니다.
4. 여러 파일의 보고서를 하나로 합칩니다.
5. 05장에서 문자열 파싱과 DataFrame 집계를 연결합니다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 원본 파일을 변경하지 않고 분석할 수 있습니다.
- [ ] 큰 텍스트 파일을 한 줄씩 처리할 수 있습니다.
- [ ] 텍스트·CSV·JSON 분석 함수를 구분할 수 있습니다.
- [ ] 형식 오류를 보고서에 남길 수 있습니다.
- [ ] JSON 결과를 임시 파일을 거쳐 안전하게 저장할 수 있습니다.
- [ ] 정상·오류·경계 입력으로 프로그램을 검증할 수 있습니다.
{% endhint %}

---

다음 장: [05. 텍스트 파싱과 데이터 분석](../05-text-processing.md)
