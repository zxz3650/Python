# 04-7. 대용량 스트리밍과 오류 복구

파일이 커지거나 일부 행이 잘못되어도 전체 작업을 안정적으로 완료할 수 있어야 합니다. 스트리밍 처리와 오류 보존을 연결하고, 입력만 순차 처리하는 경우와 전체 과정의 메모리가 제한되는 경우를 구분합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 전체 읽기와 스트리밍 처리의 차이를 설명합니다.
- generator로 레코드를 하나씩 생성합니다.
- 오류의 행 번호·원문·원인을 보존합니다.
- 입력 스트리밍과 전체 메모리 사용을 구분합니다.
- 순차 결과 저장이 필요한 조건을 판단합니다.
{% endhint %}

## 선행 지식

04-1부터 04-6까지 완료해야 합니다.

## 1. 전체 읽기의 한계

```python
from pathlib import Path

text = Path("large.txt").read_text(encoding="utf-8")
lines = text.splitlines()
```

간단하지만 파일 전체가 메모리에 올라갑니다. 파일 크기가 커지면 메모리 사용량도 증가합니다.

## 2. 한 줄씩 처리

```python
path = Path("large.txt")

with path.open("r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        print(line_number, line.rstrip("\n"))
```

현재 행만 메모리에 유지하므로 큰 파일에 적합합니다.

## 3. generator와 지연 처리

```python
def non_empty_lines(path):
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            clean = line.rstrip("\n")
            if clean:
                yield line_number, clean

for number, line in non_empty_lines(Path("large.txt")):
    print(number, line)
```

generator는 `yield`에서 값 하나를 전달한 뒤 실행 위치를 기억합니다. 결과 전체를 미리 만들지 않고 반복문이 다음 값을 요구할 때 처리를 계속합니다. 다만 generator가 값을 하나씩 만들어도 호출자가 결과를 리스트에 모두 저장하면 전체 메모리 사용량은 다시 증가합니다.

## 4. 한 행 파싱

```python
def parse_item(row):
    if None in row:
        raise ValueError("헤더보다 값이 많은 행입니다")
    if any(value is None for value in row.values()):
        raise ValueError("필드가 누락된 행입니다")

    name = row["name"].strip()
    price_text = row["price"]
    quantity_text = row["quantity"]

    if not name:
        raise ValueError("상품명이 비어 있습니다")

    price = int(price_text)
    quantity = int(quantity_text)

    if price < 0 or quantity < 0:
        raise ValueError("가격과 수량은 0 이상이어야 합니다")

    return {
        "name": name,
        "price": price,
        "quantity": quantity,
        "total": price * quantity,
    }
```

함수 하나는 `csv.DictReader`가 반환한 한 행의 변환과 검증만 담당합니다. CSV를 `split(",")`로 직접 나누지 않습니다.

## 5. 오류를 보존하며 처리

```python
import csv


def csv_rows(path):
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file, strict=True)
        for line_number, row in enumerate(reader, start=2):
            yield line_number, row


def process_rows(path):
    records = []
    errors = []

    for number, row in csv_rows(path):
        try:
            records.append(parse_item(row))
        except (KeyError, ValueError, TypeError) as exc:
            errors.append({
                "line": number,
                "raw": row,
                "error": str(exc),
            })

    return records, errors
```

잘못된 한 줄 때문에 전체 처리를 중단하지 않으면서 오류를 숨기지도 않습니다.

## 6. 처리 통계

```python
records, errors = process_rows(Path("items.csv"))

summary = {
    "valid": len(records),
    "errors": len(errors),
    "total_amount": sum(
        record["total"]
        for record in records
    ),
}
```

정상·오류 건수와 입력 행 수를 비교하면 누락을 발견하는 데 도움이 됩니다.

## 7. 입력 스트리밍과 전체 메모리 구분

현재 `process_rows()`는 입력을 한 행씩 읽지만 정상 행과 오류 행을 리스트에 누적합니다.

```text
입력 읽기 메모리: 현재 행 크기에 비례
records 메모리: 정상 행 전체에 비례
errors 메모리: 오류 행 전체에 비례
최종 JSON 메모리: 보고서 전체에 비례할 수 있음
```

따라서 이를 **입력 스트리밍**이라고 표현할 수는 있지만 전체 과정이 고정 메모리인 것은 아닙니다. 레코드가 매우 많다면 다음 방법을 선택합니다.

- 정상 행을 결과 CSV 또는 JSON Lines에 순차 저장
- 오류 행을 별도 JSON Lines에 순차 저장
- 메모리에는 건수와 합계 같은 집계값만 유지
- 한 줄의 최대 길이와 전체 입력 크기에 상한 적용

완성되지 않은 출력으로 기존 결과를 덮어쓰지 않는 방법은 04-8에서 별도로 다룹니다.

## 8. 최상위 오류와 종료 코드

```python
def main():
    input_path = Path("items.csv")

    try:
        records, errors = process_rows(input_path)
    except FileNotFoundError:
        print(f"입력 파일이 없습니다: {input_path}")
        return 1
    except PermissionError:
        print(f"읽기 권한이 없습니다: {input_path}")
        return 1
    except csv.Error as exc:
        print(f"CSV 구조 오류: {exc}")
        return 1

    print("정상:", len(records))
    print("오류:", len(errors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

예상 가능한 파일 오류를 설명하고 종료 코드로 성공과 실패를 구분합니다.

## 9. 04장 종합 프로젝트

다음 흐름의 CSV 데이터 변환기를 작성합니다.

1. CSV 입력 파일을 한 줄씩 읽습니다.
2. 필수값·자료형·범위를 검증합니다.
3. 정상 행과 오류 행을 분리합니다.
4. 합계와 처리 건수를 계산합니다.
5. 기본 구현은 결과를 JSON으로 저장합니다.
6. 확장 구현은 정상·오류 행을 JSON Lines로 순차 저장합니다.
7. 저장 결과를 다시 읽어 검증합니다.

필수 산출물:

- 입력 CSV
- 변환 프로그램
- 결과 JSON
- 오류 행 목록
- 정상·오류·경계 입력 실행 결과

## 흔한 실수

- 큰 파일을 무조건 `read_text()`로 읽음
- CSV를 `split(",")`로 직접 분리함
- 넓은 `except Exception`으로 오류를 숨김
- 오류 행의 원문과 번호를 버림
- 입력과 출력에 같은 경로를 사용함
- 불완전한 결과를 기존 파일에 바로 덮어씀

{% hint style="success" %}
## 🧪 최종 점검

정상 데이터, 빈 행, 필드 누락, 숫자 변환 실패, 음수, 한글 데이터를 포함한 입력으로 결과와 오류 목록을 검증합니다.
{% endhint %}

## 완료 기준

- [ ] 큰 파일을 한 줄씩 처리할 수 있습니다.
- [ ] 오류 행을 건너뛰면서 원인을 보존할 수 있습니다.
- [ ] 정상·오류 통계와 결과 파일을 생성할 수 있습니다.
- [ ] 입력 스트리밍과 전체 처리 메모리를 구분해 설명할 수 있습니다.
- [ ] JSON Lines를 이용한 순차 결과 저장 방식을 설명할 수 있습니다.

---

다음 절: [04-8. 임시 파일과 원자적 저장](04-8-safe-output.md)
