# 04-8. pandas와 DataFrame 기반 대용량 처리

pandas의 DataFrame은 행과 열로 구성된 표 데이터를 다루는 자료구조입니다. CSV를 분석·필터링·집계할 때 편리하지만, 기본 `read_csv()`는 파일 전체를 메모리에 올립니다. 따라서 대용량 데이터에서는 필요한 열과 자료형을 지정하거나 청크 단위로 처리해야 합니다.

{% hint style="info" %}
## 🧭 학습 목표

- Series와 DataFrame의 구조를 설명합니다.
- CSV를 DataFrame으로 읽고 조회·필터·집계합니다.
- 결측치와 잘못된 자료형을 처리합니다.
- 메모리 사용량을 확인하고 불필요한 열을 줄입니다.
- `chunksize`로 큰 CSV를 나누어 처리합니다.
{% endhint %}

## 선행 지식

04-4의 CSV, 04-6의 스트리밍 처리, 리스트·딕셔너리·함수를 이해해야 합니다.

## 1. pandas 설치

가상환경이 활성화된 상태에서 설치합니다.

```bash
python -m pip install pandas
```

```python
import pandas as pd

print(pd.__version__)
```

## 2. Series와 DataFrame

- Series: 이름이 있는 1차원 열
- DataFrame: 여러 Series가 같은 행 인덱스를 공유하는 2차원 표

```python
import pandas as pd

records = [
    {"name": "Keyboard", "price": 50000, "quantity": 2},
    {"name": "Mouse", "price": 30000, "quantity": 3},
]

frame = pd.DataFrame(records)

print(frame)
print(frame["price"])
print(frame.dtypes)
```

DataFrame은 Python의 리스트·딕셔너리를 대체하는 것이 아니라 표 형태의 반복 연산과 집계를 편리하게 수행하는 도구입니다.

## 3. CSV 읽기

```python
from pathlib import Path

path = Path("items.csv")
frame = pd.read_csv(
    path,
    encoding="utf-8",
)

print(frame.head())
print(frame.shape)
print(frame.columns)
print(frame.dtypes)
```

- `head()`: 앞부분 확인
- `shape`: 행·열 개수
- `columns`: 열 이름
- `dtypes`: 열별 자료형

데이터를 읽은 직후 구조와 자료형을 확인합니다.

## 4. 열 선택과 행 필터링

```python
selected = frame[["name", "price", "quantity"]]

expensive = frame.loc[
    frame["price"] >= 40000,
    ["name", "price"],
]

print(selected)
print(expensive)
```

- `frame["price"]`: Series 한 열
- `frame[["name", "price"]]`: DataFrame 여러 열
- `loc[행 조건, 열 목록]`: 조건에 맞는 행과 열

## 5. 새 열과 집계

```python
frame["total"] = (
    frame["price"]
    * frame["quantity"]
)

print(frame["total"].sum())
print(frame["price"].mean())

summary = frame.groupby("category", dropna=False).agg(
    item_count=("name", "count"),
    total_amount=("total", "sum"),
)

print(summary)
```

열 단위 연산은 Python 반복문으로 행을 하나씩 수정하는 것보다 간결합니다.

## 6. 결측치

CSV의 빈 필드는 일반적으로 결측값으로 읽힙니다.

```python
print(frame.isna().sum())

missing_name = frame["name"].isna()
print(frame.loc[missing_name])
```

처리 방법은 데이터 의미에 따라 선택합니다.

```python
frame["category"] = frame["category"].fillna("UNKNOWN")

valid = frame.dropna(
    subset=["name", "price", "quantity"]
)
```

임의로 0이나 빈 문자열을 채우기 전에 누락의 의미를 확인합니다.

## 7. 안전한 자료형 변환

```python
frame["price_number"] = pd.to_numeric(
    frame["price"],
    errors="coerce",
)

invalid_price = frame["price_number"].isna()

error_rows = frame.loc[invalid_price].copy()
valid_rows = frame.loc[~invalid_price].copy()
```

`errors="coerce"`는 변환할 수 없는 값을 결측값으로 바꿉니다. 오류 행을 먼저 분리하지 않고 삭제하면 원인을 잃을 수 있습니다.

정수 열에 결측치가 필요하면 nullable dtype을 사용할 수 있습니다.

```python
frame["quantity"] = pd.to_numeric(
    frame["quantity"],
    errors="coerce",
).astype("Int64")
```

## 8. 메모리 사용량 확인

```python
memory = frame.memory_usage(
    index=True,
    deep=True,
)

print(memory)
print("전체 바이트:", memory.sum())
```

문자열이 많은 열은 `deep=True`를 사용해야 실제 데이터 크기를 더 가깝게 확인할 수 있습니다.

## 9. 필요한 열과 dtype만 읽기

```python
frame = pd.read_csv(
    "items.csv",
    usecols=[
        "name",
        "category",
        "price",
        "quantity",
    ],
    dtype={
        "name": "string",
        "category": "category",
    },
)
```

- `usecols`: 필요한 열만 읽기
- `dtype`: 추론 대신 자료형 명시
- `category`: 반복되는 문자열 값이 적을 때 메모리 절감 가능

자료형은 실제 데이터 범위와 결측치 여부를 확인한 뒤 지정합니다.

## 10. chunksize로 나누어 읽기

```python
reader = pd.read_csv(
    "large_items.csv",
    chunksize=100_000,
)

for chunk_number, chunk in enumerate(reader, start=1):
    print(
        chunk_number,
        len(chunk),
    )
```

`chunksize`를 지정하면 DataFrame 하나가 아니라 청크를 차례로 제공하는 reader가 반환됩니다.

## 11. 청크별 증분 집계

모든 청크를 리스트에 저장한 뒤 다시 합치면 메모리 절감 효과가 사라집니다. 가능한 경우 청크별 결과만 누적합니다.

```python
total_rows = 0
total_amount = 0
error_rows = 0

reader = pd.read_csv(
    "large_items.csv",
    chunksize=100_000,
)

for chunk in reader:
    chunk["price"] = pd.to_numeric(
        chunk["price"],
        errors="coerce",
    )
    chunk["quantity"] = pd.to_numeric(
        chunk["quantity"],
        errors="coerce",
    )

    invalid = (
        chunk["price"].isna()
        | chunk["quantity"].isna()
    )

    error_rows += int(invalid.sum())

    valid = chunk.loc[~invalid]
    total_rows += len(valid)
    total_amount += (
        valid["price"]
        * valid["quantity"]
    ).sum()

print(total_rows)
print(error_rows)
print(total_amount)
```

각 청크의 오류 행을 별도 CSV에 추가 저장하면 원문을 보존하면서 메모리 사용을 제한할 수 있습니다.

## 12. 결과 저장

```python
valid_rows.to_csv(
    "valid_items.csv",
    index=False,
    encoding="utf-8",
)

summary.to_json(
    "summary.json",
    orient="index",
    force_ascii=False,
    indent=2,
)
```

표 형태의 데이터는 CSV, 중첩된 보고서는 JSON이 적합합니다. 반복 분석과 자료형 보존이 중요하다면 선택적으로 Parquet 형식을 검토할 수 있으며 별도 엔진 설치가 필요할 수 있습니다.

## 13. pandas와 기본 스트리밍 선택

| 상황 | 권장 방식 |
|---|---|
| 단순히 한 줄씩 변환 | 표준 `csv` 모듈 |
| 표 전체 필터·집계·결합 | pandas DataFrame |
| 파일이 메모리보다 작음 | `pd.read_csv()` |
| 파일이 매우 큼 | `chunksize` 또는 generator |
| 복잡한 증분 처리 | 표준 스트리밍 또는 청크 처리 |
| 전체 정렬·중복 제거가 필요 | 메모리·디스크 전략을 별도로 설계 |

pandas를 사용한다고 대용량 문제가 자동으로 해결되는 것은 아닙니다.

## 흔한 실수

- 큰 CSV를 크기 확인 없이 한 번에 읽음
- 모든 열을 자동 추론에 맡김
- 오류값을 `coerce`한 뒤 그대로 삭제함
- 청크를 모두 리스트에 저장하고 `concat()`함
- 인덱스를 불필요하게 CSV에 저장함
- `object` dtype을 실제 문자열·숫자 자료형으로 오해함

{% hint style="success" %}
## 🧪 종합 실습

상품 CSV를 pandas로 처리합니다.

1. 필요한 열만 읽습니다.
2. 가격·수량을 숫자로 변환합니다.
3. 오류 행을 별도로 보존합니다.
4. 카테고리별 건수와 합계를 집계합니다.
5. 작은 파일은 전체 DataFrame, 큰 파일은 `chunksize`로 처리합니다.
6. 두 방식의 결과가 같은지 비교합니다.
7. 처리 전후 메모리 사용량을 기록합니다.
{% endhint %}

## 완료 기준

- [ ] Series와 DataFrame을 구분할 수 있습니다.
- [ ] CSV의 자료형과 결측치를 확인할 수 있습니다.
- [ ] 필요한 열과 dtype만 지정해 읽을 수 있습니다.
- [ ] 청크를 저장하지 않고 증분 집계할 수 있습니다.
- [ ] pandas와 표준 스트리밍 방식의 선택 기준을 설명할 수 있습니다.

---

다음 장: [05. 텍스트 파싱과 정규표현식](../05-text-processing.md)
