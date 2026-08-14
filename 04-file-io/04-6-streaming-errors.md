# 04-6. 대용량 파일과 오류 처리

파일이 커지거나 일부 행이 잘못되어도 전체 작업을 안정적으로 완료할 수 있어야 합니다. 스트리밍 처리, 오류 보존, 안전한 결과 저장을 하나의 프로그램으로 연결합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 전체 읽기와 스트리밍 처리의 차이를 설명합니다.
- generator로 레코드를 하나씩 생성합니다.
- 오류의 행 번호·원문·원인을 보존합니다.
- 임시 파일을 이용해 결과를 안전하게 교체합니다.
{% endhint %}

## 선행 지식

04-1부터 04-5까지 완료해야 합니다.

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

## 3. generator

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

generator는 결과 전체를 만들지 않고 필요할 때 하나씩 생성합니다.

## 4. 한 행 파싱

```python
def parse_item(line):
    name, price_text, quantity_text = line.split(",")

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

함수 하나는 한 행의 변환과 검증만 담당합니다.

## 5. 오류를 보존하며 처리

```python
def process_lines(path):
    records = []
    errors = []

    for number, line in non_empty_lines(path):
        try:
            records.append(parse_item(line))
        except (ValueError, TypeError) as exc:
            errors.append({
                "line": number,
                "raw": line,
                "error": str(exc),
            })

    return records, errors
```

잘못된 한 줄 때문에 전체 처리를 중단하지 않으면서 오류를 숨기지도 않습니다.

## 6. 처리 통계

```python
records, errors = process_lines(Path("items.txt"))

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

## 7. 안전한 결과 저장

완성되지 않은 결과가 기존 파일을 덮어쓰지 않도록 임시 파일에 먼저 저장한 뒤 교체합니다.

```python
import json
from pathlib import Path

output = Path("result.json")
temporary = output.with_suffix(".json.tmp")

report = {
    "summary": summary,
    "records": records,
    "errors": errors,
}

temporary.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

temporary.replace(output)
```

기존 결과 보존이 필요하면 교체 전에 백업 정책을 적용합니다.

## 8. 최상위 오류와 종료 코드

```python
def main():
    input_path = Path("items.txt")

    try:
        records, errors = process_lines(input_path)
    except FileNotFoundError:
        print(f"입력 파일이 없습니다: {input_path}")
        return 1
    except PermissionError:
        print(f"읽기 권한이 없습니다: {input_path}")
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
5. 결과를 JSON으로 저장합니다.
6. 저장한 JSON을 다시 읽어 검증합니다.

필수 산출물:

- 입력 CSV
- 변환 프로그램
- 결과 JSON
- 오류 행 목록
- 정상·오류·경계 입력 실행 결과

## 흔한 실수

- 큰 파일을 무조건 `read_text()`로 읽음
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
- [ ] 임시 파일을 이용해 결과를 안전하게 교체할 수 있습니다.

---

다음 절: [04-7. pandas와 DataFrame 기반 대용량 처리](04-7-pandas-dataframe.md)
