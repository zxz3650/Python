# 04-7. 대용량 스트리밍과 오류 복구

파일이 커지거나 일부 레코드가 잘못되어도 전체 작업을 안정적으로 마쳐야 한다. 이 절에서는 입력을 한 번에 메모리에 올리지 않는 **스트리밍 처리**와, 잘못된 레코드의 위치·값·원인을 남기는 **오류 복구**를 연결한다. 입력만 순차적으로 읽는 경우와 전체 처리 과정의 메모리 사용량이 제한되는 경우도 구분한다.

{% hint style="info" %}
### 🧭 학습 목표

- 전체 읽기와 스트리밍 처리의 차이를 설명한다.
- 제너레이터로 레코드를 하나씩 생성한다.
- CSV 구조 오류와 레코드 값 오류를 구분한다.
- 오류 레코드의 위치·파싱된 값·원인을 보존한다.
- 입력 스트리밍과 전체 메모리 사용량을 구분한다.
- 순차 결과 저장이 필요한 조건을 판단한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | 한 줄씩 읽기, 제너레이터, 레코드 단위 검증, 구체적인 예외 처리 |
| 권장 | 처리 통계, CSV 물리 행 번호, 오류 레코드 보존 |
| 심화 | JSON Lines 순차 출력, 고정 메모리 처리, 출력의 원자적 교체 |

## 선행 지식과 학습 연결

- 경로와 파일 열기는 04-1~04-3에서 학습했다.
- 인코딩과 CSV 구조는 04-4~04-6에서 학습했다.
- 이 절에서는 입력을 순차적으로 처리하고 오류를 분리한다.
- 불완전한 순차 출력이 기존 결과를 덮어쓰지 않게 하는 방법은 [04-8](04-8-safe-output.md)에서 학습한다.
- 모든 개념은 [04-9 파일 분석기](04-9-file-analyzer.md)에서 하나의 프로그램으로 연결한다.

전용 실습은 [`notebooks/04-7-streaming-errors.ipynb`](../notebooks/04-7-streaming-errors.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

다음 질문에 먼저 답해 본다.

1. `read_text()`와 파일 객체 반복문은 메모리를 어떻게 사용하는가?
2. 제너레이터가 값을 하나씩 만들어도 호출자가 `list()`로 감싸면 어떻게 되는가?
3. 잘못된 숫자 한 건과 닫히지 않은 CSV 따옴표는 같은 범위에서 복구해야 하는가?
4. 오류 메시지만 남기고 레코드 위치와 값을 버리면 어떤 문제가 생기는가?

## 1. 전체 읽기의 한계

```python
from pathlib import Path

text = Path("large.txt").read_text(encoding="utf-8")
lines = text.splitlines()
```

코드는 간단하지만 파일 전체와 분리된 문자열 목록이 메모리에 함께 존재할 수 있다. 파일이 커질수록 메모리 사용량도 증가한다.

파일 크기가 충분히 작고 크기 상한이 정해져 있다면 전체 읽기도 올바른 선택이다. 스트리밍은 항상 더 좋은 방식이 아니라 **입력 크기와 후속 처리 방식에 따라 선택하는 방식**이다.

## 2. 한 줄씩 처리하기

```python
from pathlib import Path

path = Path("large.txt")

with path.open("r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        clean_line = line.rstrip("\r\n")
        print(line_number, clean_line)
```

파일 객체를 반복하면 현재 행을 중심으로 처리하므로 큰 텍스트 파일에 적합하다. `rstrip()`을 인자 없이 호출하면 의미 있는 공백까지 지울 수 있으므로 여기서는 줄 끝 문자만 제거한다.

한 줄 자체가 매우 클 수 있으므로 “한 줄씩 읽는다”가 언제나 작은 메모리를 보장하지는 않는다. 외부에서 받은 파일을 처리한다면 파일 전체 크기와 한 레코드의 최대 길이에 정책을 둔다.

## 3. 제너레이터와 지연 처리

```python
def non_empty_lines(path):
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            clean_line = line.rstrip("\r\n")
            if clean_line:
                yield line_number, clean_line


for number, line in non_empty_lines(Path("large.txt")):
    print(number, line)
```

제너레이터는 `yield`에서 값 하나를 전달한 뒤 실행 위치를 기억한다. 결과 전체를 미리 만들지 않고 반복문이 다음 값을 요구할 때 처리를 계속한다.

다만 다음 코드는 제너레이터의 모든 결과를 리스트에 모으므로 전체 결과 크기만큼 메모리를 사용한다.

```python
all_lines = list(non_empty_lines(Path("large.txt")))
```

## 4. 한 레코드의 변환과 검증

```python
def parse_item(row):
    if None in row:
        raise ValueError("헤더보다 값이 많은 레코드다")
    if any(value is None for value in row.values()):
        raise ValueError("필드가 누락된 레코드다")

    name = row["name"].strip()
    price_text = row["price"]
    quantity_text = row["quantity"]

    if not name:
        raise ValueError("상품명이 비어 있다")

    price = int(price_text)
    quantity = int(quantity_text)

    if price < 0 or quantity < 0:
        raise ValueError("가격과 수량은 0 이상이어야 한다")

    return {
        "name": name,
        "price": price,
        "quantity": quantity,
        "total": price * quantity,
    }
```

이 함수는 `csv.DictReader`가 반환한 한 레코드의 변환과 검증만 담당한다. CSV를 `split(",")`로 직접 나누지 않는다. 따옴표 안의 쉼표와 줄바꿈은 CSV 파서가 처리해야 하기 때문이다.

## 5. 헤더를 검증하고 레코드를 순차 생성하기

```python
import csv


REQUIRED_FIELDS = {"name", "price", "quantity"}


def csv_rows(path):
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        fieldnames = reader.fieldnames

        if fieldnames is None:
            raise ValueError("CSV 헤더가 없다")

        missing = REQUIRED_FIELDS - set(fieldnames)
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"필수 헤더가 없다: {names}")

        if len(fieldnames) != len(set(fieldnames)):
            raise ValueError("중복된 CSV 헤더가 있다")

        for row in reader:
            yield reader.line_num, row
```

`reader.line_num`은 현재 CSV 레코드를 읽은 뒤의 **마지막 물리 행 번호**다. 따옴표 안에 줄바꿈이 있으면 한 레코드가 여러 물리 행을 차지할 수 있으므로 `enumerate(..., start=2)`와 값이 달라질 수 있다.

`DictReader`가 반환한 딕셔너리는 파싱된 값이며 원본 CSV 문자열과 완전히 같지 않다. 원본 증거가 반드시 필요하면 허가된 입력 파일을 읽기 전용으로 보존하고, 보고서에는 파일 해시와 레코드 위치를 함께 기록한다. 비밀번호·토큰·개인정보가 있는 필드는 오류 보고서에 그대로 복사하지 않는다.

## 6. 오류를 보존하며 처리하기

```python
def process_rows(path):
    records = []
    errors = []

    for line_end, row in csv_rows(path):
        try:
            records.append(parse_item(row))
        except (KeyError, TypeError, ValueError) as exc:
            errors.append({
                "line_end": line_end,
                "row": row,
                "error_type": type(exc).__name__,
                "message": str(exc),
            })

    return records, errors
```

상품명 누락이나 숫자 변환 실패처럼 **한 레코드에 한정된 오류**는 기록한 뒤 다음 레코드를 처리한다. 반면 파일 부재, 권한 문제, 인코딩 오류, 필수 헤더 누락, 복구할 수 없는 CSV 구조 오류는 파일 전체의 계약을 깨므로 호출자에게 전달한다.

넓은 `except Exception`으로 프로그래밍 오류까지 숨기지 않는다. `parse_item()`에서 예상한 예외만 최소 범위로 처리한다.

## 7. 처리 통계와 보존 법칙

```python
records, errors = process_rows(Path("items.csv"))

summary = {
    "processed": len(records) + len(errors),
    "valid": len(records),
    "errors": len(errors),
    "total_amount": sum(
        record["total"]
        for record in records
    ),
}

assert summary["processed"] == summary["valid"] + summary["errors"]
```

처리한 레코드 수가 정상 건수와 오류 건수의 합과 같은지 확인한다. 입력 정책상 건너뛰는 레코드가 있다면 `skipped`를 별도로 집계하고 다음 관계를 검증한다.

```text
processed = valid + errors + skipped
```

빈 물리 행은 CSV 파서가 건너뛸 수 있다. 빈 행도 반드시 집계해야 한다면 “빈 행”의 정의와 집계 위치를 요구사항에 먼저 적는다.

## 8. 입력 스트리밍과 전체 메모리 구분

현재 `process_rows()`는 입력을 한 레코드씩 읽지만 정상 결과와 오류 결과를 리스트에 누적한다.

```text
입력 읽기 메모리: 현재 레코드 크기에 비례
records 메모리: 정상 레코드 전체에 비례
errors 메모리: 오류 레코드 전체에 비례
최종 JSON 메모리: 보고서 전체에 비례할 수 있음
```

따라서 이 구현은 **입력 스트리밍**이지만 전체 과정이 고정 메모리인 것은 아니다. 레코드가 매우 많다면 다음 방법을 선택한다.

- 정상 레코드를 결과 JSON Lines에 순차 저장한다.
- 오류 레코드를 별도 JSON Lines에 순차 저장한다.
- 메모리에는 건수와 합계 같은 집계값만 유지한다.
- 파일 전체 크기와 레코드 하나의 최대 길이에 상한을 적용한다.

JSON Lines는 한 줄에 독립된 JSON 값 하나를 기록하는 형식이다. 전체 배열을 완성하지 않아도 레코드 단위로 쓸 수 있다.

```python
import json


def write_json_lines(events, file):
    for kind, payload in events:
        json.dump(
            {"kind": kind, "data": payload},
            file,
            ensure_ascii=False,
            allow_nan=False,
        )
        file.write("\n")
```

`kind`와 실제 레코드를 `data`로 분리하면 입력 레코드에 같은 이름의 키가 있어도 결과 종류가 덮어써지지 않는다. 이 함수의 `file`에는 04-8의 절차로 만든 임시 파일 객체를 전달한다. 최종 경로에 직접 순차 출력하면 프로그램 중단 시 불완전한 파일이 남을 수 있다.

## 9. 최상위 오류와 종료 코드

```python
def main():
    input_path = Path("items.csv")

    try:
        records, errors = process_rows(input_path)
    except FileNotFoundError:
        print(f"입력 파일이 없다: {input_path}")
        return 1
    except PermissionError:
        print(f"읽기 권한이 없다: {input_path}")
        return 1
    except UnicodeDecodeError as exc:
        print(f"UTF-8로 읽을 수 없다: {exc}")
        return 1
    except (csv.Error, ValueError) as exc:
        print(f"CSV 파일을 처리할 수 없다: {exc}")
        return 1
    except OSError as exc:
        print(f"파일 입출력에 실패했다: {exc}")
        return 1

    print("정상:", len(records))
    print("오류:", len(errors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

예상 가능한 파일 단위 오류를 프로그램 경계에서 설명하고 종료 코드로 성공과 실패를 구분한다. 레코드 오류가 존재해도 결과를 허용할지는 요구사항에 따라 정한다. 예를 들어 오류가 한 건이라도 있으면 종료 코드 `2`를 반환하도록 정책을 확장할 수 있다.

## 10. 연결 실습: CSV 데이터 변환기

다음 입력을 `items.csv`로 저장한다.

```csv
name,price,quantity
키보드,30000,2
마우스,abc,1
모니터,200000,-1
USB,10000,3
```

다음 흐름의 변환기를 작성한다.

1. CSV 입력 파일을 한 레코드씩 읽는다.
2. 필수 헤더와 중복 헤더를 검증한다.
3. 필수값·자료형·범위를 검증한다.
4. 정상 레코드와 오류 레코드를 분리한다.
5. 합계와 처리 건수를 계산한다.
6. 기본 구현은 결과를 JSON으로 저장한다.
7. 확장 구현은 정상·오류 레코드를 JSON Lines로 순차 저장한다.
8. 04-8의 안전한 저장 절차로 완성된 결과만 최종 경로에 반영한다.

위 입력의 인수 조건은 다음과 같다.

```python
assert len(records) == 2
assert len(errors) == 2
assert summary["processed"] == 4
assert summary["total_amount"] == 90000
assert {error["line_end"] for error in errors} == {3, 4}
```

필수 산출물은 다음과 같다.

- 입력 CSV와 입력 규칙
- 변환 프로그램과 실행 방법
- 정상 결과와 오류 목록
- 정상·오류·경계 입력의 실행 결과
- 입력 스트리밍과 전체 메모리 사용의 차이 설명

## 흔한 실수와 점검법

| 실수 | 점검법 |
| --- | --- |
| 큰 파일을 무조건 `read_text()`로 읽음 | 입력 크기 상한과 처리 방식을 요구사항에 적는다. |
| CSV를 `split(",")`로 직접 분리함 | 따옴표 안의 쉼표가 있는 레코드로 검증한다. |
| `enumerate()` 값을 CSV 물리 행 번호로 단정함 | 여러 줄 필드에서 `reader.line_num`을 확인한다. |
| 넓은 `except Exception`으로 오류를 숨김 | 예상 가능한 예외와 복구 범위를 문서화한다. |
| 파싱된 딕셔너리를 원본 문자열이라고 표현함 | 원본과 파싱 결과를 구분해 기록한다. |
| 입력만 스트리밍하면서 고정 메모리라고 표현함 | 누적 리스트와 최종 출력 크기도 계산한다. |
| 불완전한 결과를 기존 파일에 직접 덮어씀 | 04-8의 임시 파일 교체 절차를 적용한다. |

{% hint style="success" %}
### 🧪 최종 점검

정상 레코드, 필드 누락, 숫자 변환 실패, 음수, 한글, 따옴표 안의 쉼표, 여러 줄 필드, 중복 헤더를 포함한 입력을 각각 검증한다. 수업에서는 교사가 제공하거나 학습자가 생성한 허가된 데이터만 사용한다.
{% endhint %}

## 완료 기준

- [ ] 큰 파일을 한 줄 또는 한 레코드씩 처리한다.
- [ ] 제너레이터의 지연 처리 방식을 설명한다.
- [ ] 파일 단위 오류와 레코드 단위 오류를 구분한다.
- [ ] 오류 레코드의 위치·파싱된 값·원인을 보존한다.
- [ ] 정상·오류·건너뜀 통계의 관계를 검증한다.
- [ ] 입력 스트리밍과 전체 처리 메모리를 구분한다.
- [ ] JSON Lines 순차 출력과 원자적 저장의 역할을 구분한다.

## 핵심 정리

- 스트리밍은 전체 결과를 자동으로 고정 메모리로 만드는 기술이 아니다.
- 레코드 단위에서 복구할 오류와 파일 전체를 중단할 오류를 구분한다.
- CSV 위치는 논리 레코드와 물리 행의 차이를 고려해 기록한다.
- 오류 보고서에는 재현에 필요한 문맥을 남기되 민감정보는 제외한다.
- 순차 출력도 임시 파일에 완성한 뒤 최종 경로로 교체해야 기존 결과를 보호할 수 있다.

---

다음 절: [04-8. 임시 파일과 원자적 저장](04-8-safe-output.md)
