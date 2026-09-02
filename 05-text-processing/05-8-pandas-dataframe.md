# 05-8. pandas와 DataFrame 기반 대용량 처리

pandas는 행과 열로 이루어진 표 데이터를 조회·변환·집계하는 도구이다. 작은 CSV는 하나의 DataFrame으로 처리할 수 있지만, 큰 파일은 필요한 열만 읽고 청크별 결과를 증분 집계해야 한다. 이 절에서는 **원문 확인 → 명시적 자료형 변환 → 오류 행 분리 → 유효 행 집계 → 안전한 결과 저장**의 흐름을 익힌다.

{% hint style="info" %}
### 🧭 학습 목표

- Series와 DataFrame의 구조와 역할을 설명한다.
- UTF-8 strict 정책과 명시적 스키마로 CSV를 읽는다.
- 결측값·변환 오류·도메인 오류를 구분하고 원문 오류 행을 보존한다.
- 필요한 열과 dtype만 사용해 메모리 사용량을 줄인다.
- `chunksize`로 큰 CSV를 읽고 합칠 수 있는 통계만 증분 집계한다.
- 결과에서 불필요한 민감값을 제외하고 원자적으로 저장한다.
- 같은 처리 원칙을 05-9의 5분 웹 로그 특징표에 적용한다.
{% endhint %}

## 0. 학습 전 확인

다음 내용을 먼저 확인한다.

- 04-5의 CSV 형식과 04-7의 스트리밍·오류 보존을 이해한다.
- 05-7의 NumPy dtype·조건 마스크·벡터 연산을 실행할 수 있다.
- 가상환경에서 `pandas`와 `numpy`를 가져올 수 있다.
- Notebook을 `requirements.txt`가 있는 프로젝트 루트에서 실행한다.

```python
import numpy as np
import pandas as pd

print("NumPy:", np.__version__)
print("pandas:", pd.__version__)
```

### 실습 자료

- [학습자용 Notebook](../notebooks/05-8-pandas-dataframe.ipynb)
- [풀이·검증용 Notebook](../notebooks/solutions/05-8-pandas-dataframe-solution.ipynb)
- [작은 상품 fixture](../fixtures/05-text-processing/items.csv)
- [청크 처리용 상품 fixture](../fixtures/05-text-processing/large_items.csv)

학습자용 Notebook은 핵심 변환·집계 함수를 TODO로 제공한다. 풀이·검증용 Notebook은 결과 비교와 경계 사례 확인을 위한 참고 구현이다. 공개 저장소에서는 참고 구현을 볼 수 있으므로 평가에 사용할 때에는 검증 자료를 교사용 공간에서 별도로 배포한다.

fixture는 다음 열을 사용한다.

| 열 | 의미 | 분석 사용 여부 |
| --- | --- | --- |
| `name` | 상품 이름 | 사용 |
| `category` | 상품 분류 | 사용 |
| `price` | 단가 원문 | 검증 후 사용 |
| `quantity` | 수량 원문 | 검증 후 사용 |

실제 업무 파일에 이메일·전화번호·내부 메모 같은 열이 더 있더라도 이번 집계에 필요하지 않으면 `usecols`에서 제외한다.

### 학습 우선순위

| 우선순위 | 반드시 익힐 내용 | 이유 |
| --- | --- | --- |
| 1 | DataFrame 구조, strict CSV 읽기, 결측·dtype 검증 | 잘못 읽은 데이터를 올바른 통계로 오인하지 않기 위해 필요하다 |
| 2 | 오류 행 분리, `groupby()`, `chunksize` 증분 집계 | 재현 가능한 대용량 처리의 핵심이다 |
| 3 | 메모리 최적화, 원자적 저장, 범주형 dtype | 실제 파일 크기와 공유 범위가 커질 때 필요하다 |

처음에는 `items.csv`로 전체 흐름을 확인하고, 같은 결과가 나오는지 `large_items.csv`의 청크 처리로 검증한다.

## 1. Series와 DataFrame을 구분한다

Series는 하나의 이름 있는 1차원 열이고, DataFrame은 여러 Series가 같은 행 인덱스를 공유하는 2차원 표이다.

```python
records = [
    {
        "name": "Keyboard",
        "category": "device",
        "price": 50_000,
        "quantity": 2,
    },
    {
        "name": "Mouse",
        "category": "device",
        "price": 30_000,
        "quantity": 3,
    },
]

frame = pd.DataFrame.from_records(records)

print(type(frame))
print(type(frame["price"]))
print(frame.shape)
print(frame.columns)
print(frame.dtypes)
```

- `shape`: `(행 수, 열 수)`를 반환한다.
- `columns`: 열 이름을 보여 준다.
- `dtypes`: 열마다 pandas가 사용하는 자료형을 보여 준다.
- `index`: 행을 식별하는 레이블이다. CSV의 실제 식별자 열과 같다고 가정하지 않는다.

DataFrame은 리스트와 딕셔너리를 없애는 도구가 아니다. 표 형태의 열 연산·필터·그룹 집계가 반복될 때 사용한다.

## 2. CSV를 strict 정책과 최소 열로 읽는다

먼저 프로젝트 루트와 fixture 경로를 명시한다. 현재 작업 디렉터리가 다르면 같은 상대경로가 다른 파일을 가리킬 수 있다.

```python
from pathlib import Path

PROJECT_ROOT = Path.cwd().resolve()
if not (PROJECT_ROOT / "requirements.txt").is_file():
    raise RuntimeError("프로젝트 루트에서 Notebook을 실행해야 한다")

FIXTURE_DIR = (
    PROJECT_ROOT
    / "fixtures"
    / "05-text-processing"
)
ITEMS_PATH = FIXTURE_DIR / "items.csv"
LARGE_ITEMS_PATH = FIXTURE_DIR / "large_items.csv"

for path in (ITEMS_PATH, LARGE_ITEMS_PATH):
    if not path.is_file():
        raise FileNotFoundError(path)
```

fixture에는 네 열만 있지만 실제 파일에는 분석과 무관한 민감 열이 추가될 수 있다. 허용 목록인 `usecols`를 사용하면 예상하지 못한 열을 읽은 뒤 삭제하는 방식보다 안전하다.

```python
READ_COLUMNS = [
    "name",
    "category",
    "price",
    "quantity",
]

READ_DTYPES = {
    column: "string"
    for column in READ_COLUMNS
}


def read_items(path: Path, *, chunksize=None):
    return pd.read_csv(
        path,
        usecols=READ_COLUMNS,
        dtype=READ_DTYPES,
        encoding="utf-8",
        encoding_errors="strict",
        on_bad_lines="error",
        keep_default_na=False,
        na_values=[""],
        chunksize=chunksize,
    )


frame = read_items(ITEMS_PATH)
print(frame.head())
print(frame.dtypes)
```

### 2.1 각 옵션의 목적

| 옵션 | 목적 |
| --- | --- |
| `usecols` | 분석에 필요한 열만 읽어 메모리와 노출 범위를 줄인다 |
| `dtype="string"` | 숫자처럼 보이는 오류 원문을 먼저 보존한다 |
| `encoding_errors="strict"` | 잘못된 바이트를 대체 문자로 숨기지 않는다 |
| `on_bad_lines="error"` | 열 개수가 맞지 않는 행을 조용히 건너뛰지 않는다 |
| `keep_default_na=False` | 문자열 `NA`, `NULL`을 자동 결측값으로 바꾸지 않는다 |
| `na_values=[""]` | 빈 CSV 필드만 결측값으로 취급한다 |

다른 인코딩으로 자동 재시도하면 읽기는 성공할 수 있지만 원문이 변형되었는지 알기 어렵다. `UnicodeDecodeError`가 발생하면 파일 생성 시스템과 합의한 인코딩을 먼저 확인한다.

## 3. dtype, 결측값, 오류 행을 함께 관리한다

자료형 추론에 바로 맡기면 한 열에 숫자와 오류 문자열이 섞였을 때 `object`나 `string`이 될 수 있다. 먼저 원문 문자열을 보존하고 새 숫자 Series를 만든다.

```python
def validate_items(frame: pd.DataFrame):
    work = frame.copy()

    name = work["name"].str.strip()
    category = work["category"].str.strip()
    price_text = work["price"].str.strip()
    quantity_text = work["quantity"].str.strip()

    price_number = pd.to_numeric(
        price_text,
        errors="coerce",
    )
    quantity_number = pd.to_numeric(
        quantity_text,
        errors="coerce",
    )

    missing_name = name.isna() | name.eq("")
    missing_price = price_text.isna() | price_text.eq("")
    missing_quantity = quantity_text.isna() | quantity_text.eq("")

    invalid_price_text = (
        ~missing_price
        & price_number.isna()
    )
    invalid_quantity_text = (
        ~missing_quantity
        & quantity_number.isna()
    )
    finite_price = pd.Series(
        np.isfinite(
            price_number.to_numpy(
                dtype=float,
                na_value=np.nan,
            )
        ),
        index=work.index,
    )
    finite_quantity = pd.Series(
        np.isfinite(
            quantity_number.to_numpy(
                dtype=float,
                na_value=np.nan,
            )
        ),
        index=work.index,
    )
    non_finite_price = (
        price_number.notna()
        & ~finite_price
    )
    non_finite_quantity = (
        quantity_number.notna()
        & ~finite_quantity
    )
    fractional_quantity = (
        quantity_number.notna()
        & ~non_finite_quantity
        & quantity_number.mod(1).ne(0)
    )
    negative_price = (
        price_number.notna()
        & price_number.lt(0)
    )
    negative_quantity = (
        quantity_number.notna()
        & quantity_number.lt(0)
    )

    reason = pd.Series(
        pd.NA,
        index=work.index,
        dtype="string",
    )
    reason = reason.mask(missing_name, "missing_name")
    reason = reason.mask(reason.isna() & missing_price, "missing_price")
    reason = reason.mask(reason.isna() & missing_quantity, "missing_quantity")
    reason = reason.mask(reason.isna() & invalid_price_text, "invalid_price")
    reason = reason.mask(
        reason.isna() & invalid_quantity_text,
        "invalid_quantity",
    )
    reason = reason.mask(
        reason.isna() & non_finite_price,
        "non_finite_price",
    )
    reason = reason.mask(
        reason.isna() & non_finite_quantity,
        "non_finite_quantity",
    )
    reason = reason.mask(
        reason.isna() & fractional_quantity,
        "fractional_quantity",
    )
    reason = reason.mask(reason.isna() & negative_price, "negative_price")
    reason = reason.mask(
        reason.isna() & negative_quantity,
        "negative_quantity",
    )

    invalid = reason.notna()

    # 오류 행은 원문 숫자와 출처 행 번호를 보존한다.
    errors = work.loc[
        invalid,
        ["price", "quantity"],
    ].copy()
    errors.insert(0, "source_row", errors.index + 2)
    errors["error_reason"] = reason.loc[invalid]

    valid = work.loc[~invalid].copy()
    valid["name"] = name.loc[~invalid]
    valid["category"] = (
        category.loc[~invalid]
        .mask(category.loc[~invalid].eq(""))
        .fillna("UNKNOWN")
    )
    valid["price"] = (
        price_number.loc[~invalid]
        .astype("Float64")
    )
    valid["quantity"] = (
        quantity_number.loc[~invalid]
        .astype("Int64")
    )
    valid["total_amount"] = (
        valid["price"]
        * valid["quantity"]
    )

    return valid, errors


valid_rows, error_rows = validate_items(frame)
```

`errors="coerce"`는 변환 오류를 결측값으로 표시하기 위한 중간 단계이다. 변환 결과가 결측이라는 이유로 바로 `dropna()`하면 원문과 실패 이유를 잃는다. 위 코드는 실제 빈 필드와 잘못된 숫자 문자열을 분리하고, 오류 행을 만든 뒤 유효 행만 집계한다.

fixture의 가격은 학습 편의를 위해 숫자로 처리한다. 실제 금액은 부동소수점 오차를 피하도록 정수 최소 화폐 단위나 `Decimal` 사용 여부를 별도로 설계한다.

## 4. 선택·필터·복사·집계를 수행한다

열 하나는 Series, 열 목록은 DataFrame을 반환한다.

```python
price_series = valid_rows["price"]
selected_frame = valid_rows[
    ["name", "price"]
]

expensive = valid_rows.loc[
    valid_rows["price"] >= 40_000,
    ["name", "price"],
].copy()
```

필터 결과를 수정하려면 `.copy()`로 독립적인 DataFrame임을 명시한다. `frame[mask]["column"] = value` 같은 연쇄 인덱싱은 원본이 바뀌는지 불명확하므로 사용하지 않는다.

카테고리별 건수·수량·금액은 다음처럼 집계한다.

```python
def summarize_items(valid: pd.DataFrame) -> pd.DataFrame:
    return (
        valid.groupby(
            "category",
            dropna=False,
            observed=True,
        )
        .agg(
            item_count=("name", "size"),
            total_quantity=("quantity", "sum"),
            total_amount=("total_amount", "sum"),
        )
        .sort_index()
    )


summary = summarize_items(valid_rows)
print(summary)
```

`dropna=False`는 결측 그룹을 자동 제외하지 않는다. 이 실습에서는 허용한 결측 category를 먼저 `UNKNOWN`으로 바꾸므로 품질 정책이 결과에 드러난다. `observed=True`는 category dtype을 사용할 때 실제 등장한 그룹만 만든다.

## 5. 메모리 사용량과 고유값 수를 확인한다

```python
memory = valid_rows.memory_usage(
    index=True,
    deep=True,
)

print(memory)
print("전체 바이트:", int(memory.sum()))
```

문자열 열은 `deep=True`를 사용해야 실제 문자열 메모리를 더 가깝게 계산한다. 반복 값이 많은 category는 범주형 dtype으로 줄일 수 있다.

```python
unique_ratio = (
    valid_rows["category"].nunique(dropna=False)
    / max(len(valid_rows), 1)
)

if unique_ratio < 0.5:
    valid_rows["category"] = (
        valid_rows["category"]
        .astype("category")
    )
```

`category`는 고유값이 적고 반복이 많을 때 효과가 있다. 사용자 ID·URL처럼 거의 모든 값이 다르면 오히려 관리 비용이 늘 수 있다. 작은 샘플만 보고 정수 dtype을 지나치게 줄이면 실제 데이터에서 범위를 넘을 수 있으므로 최솟값·최댓값을 먼저 확인한다.

## 6. chunksize로 증분 집계한다

`chunksize`를 지정하면 하나의 DataFrame 대신 청크를 차례로 반환하는 reader를 얻는다. 청크를 모두 리스트에 저장하거나 마지막에 `pd.concat()`하면 메모리 절감 효과가 사라진다.

```python
# 200행 fixture에서 여러 청크를 관찰하기 위한 학습용 크기이다.
CHUNK_SIZE = 50

reader = read_items(
    LARGE_ITEMS_PATH,
    chunksize=CHUNK_SIZE,
)

running_summary = None
quality = {
    "total_rows": 0,
    "valid_rows": 0,
    "error_rows": 0,
}
error_samples = []
ERROR_SAMPLE_LIMIT = 20

for chunk_number, chunk in enumerate(reader, start=1):
    quality["total_rows"] += len(chunk)

    valid_chunk, error_chunk = validate_items(chunk)
    quality["valid_rows"] += len(valid_chunk)
    quality["error_rows"] += len(error_chunk)

    remaining = ERROR_SAMPLE_LIMIT - len(error_samples)
    if remaining > 0:
        error_samples.extend(
            error_chunk.head(remaining).to_dict("records")
        )

    chunk_summary = summarize_items(valid_chunk)
    running_summary = (
        chunk_summary
        if running_summary is None
        else running_summary.add(
            chunk_summary,
            fill_value=0,
        )
    )

assert quality["total_rows"] == (
    quality["valid_rows"] + quality["error_rows"]
)
```

합계·건수·최솟값·최댓값은 청크별 결과를 다시 결합할 수 있다. 평균은 `평균들의 평균`을 사용하지 않고 전체 합계와 전체 건수로 다시 계산한다. 중앙값·전체 정렬·파일 전체 중복 제거는 청크별 값만 단순히 더할 수 없으므로 외부 정렬, 데이터베이스, 별도 알고리즘이 필요하다.

그룹 키의 고유값이 계속 늘면 `running_summary`도 커진다. `chunksize`는 현재 상세 행 메모리를 제한할 뿐, 모든 누적 상태의 크기를 자동으로 제한하지 않는다.

## 7. 오류 행을 보존하면서 민감값을 최소화한다

오류 행 전체를 리스트에 모으면 큰 파일에서 다시 메모리 문제가 생긴다. 각 청크의 오류 행을 임시 CSV 스트림에 이어 쓰되, 원본을 다시 찾는 데 필요한 행 번호와 숫자 원문·오류 이유만 포함한다. 상품 이름은 결과에 복사하지 않는다.

```python
SAFE_ERROR_COLUMNS = [
    "source_row",
    "price",
    "quantity",
    "error_reason",
]


def append_error_chunk(
    error_chunk: pd.DataFrame,
    file,
    *,
    write_header: bool,
) -> bool:
    if error_chunk.empty:
        return write_header

    error_chunk.loc[:, SAFE_ERROR_COLUMNS].to_csv(
        file,
        index=False,
        header=write_header,
    )
    return False
```

이 함수의 `file`은 8절에서 만드는 같은 실행 디렉터리의 임시 파일이다. 모든 청크 처리가 성공한 뒤에만 최종 `error-rows.csv`로 교체한다. 처리 도중 실패하면 이전의 완전한 결과를 덮어쓰지 않는다.

실제 데이터에서 행 번호만으로 재처리할 수 없고 식별자가 꼭 필요하다면 05-9와 같은 HMAC 별칭을 사용한다. 오류 원문을 보존한다는 말은 모든 열을 무조건 복사한다는 뜻이 아니라, 재처리에 필요한 최소 필드와 실패 이유를 보존한다는 뜻이다.

## 8. 결과를 전용 디렉터리에 원자적으로 저장한다

출력 경로는 프로젝트 내부인지 확인하고, 심볼릭 링크를 통해 다른 위치로 빠져나가지 않게 검사한다. 실행마다 새 디렉터리를 만들어 이전 결과와 섞이지 않게 한다.

```python
from datetime import datetime, timezone
from pathlib import Path


def create_run_directory(project_root: Path) -> Path:
    project_root = project_root.resolve()
    output_parent = project_root / "outputs"

    if output_parent.exists() and output_parent.is_symlink():
        raise RuntimeError("outputs는 심볼릭 링크일 수 없다")

    output_parent.mkdir(exist_ok=True, mode=0o700)
    output_parent = output_parent.resolve()

    if not output_parent.is_relative_to(project_root):
        raise RuntimeError("출력 경로가 프로젝트 밖을 가리킨다")

    output_root = output_parent / "pandas-items"
    if output_root.exists() and output_root.is_symlink():
        raise RuntimeError("출력 루트는 심볼릭 링크일 수 없다")

    output_root.mkdir(exist_ok=True, mode=0o700)
    output_root.chmod(0o700)

    run_id = datetime.now(timezone.utc).strftime(
        "run-%Y%m%dT%H%M%SZ"
    )
    run_dir = output_root / run_id
    run_dir.mkdir(exist_ok=False, mode=0o700)
    return run_dir


RUN_DIR = create_run_directory(PROJECT_ROOT)
```

임시 파일을 같은 디렉터리에 완전히 쓴 뒤 `os.replace()`로 최종 이름을 교체한다.

```python
from contextlib import contextmanager
import os
import tempfile


@contextmanager
def atomic_text_destination(destination: Path):
    destination = destination.resolve(strict=False)
    if destination.parent != RUN_DIR:
        raise ValueError("실행 디렉터리 밖에는 저장할 수 없다")

    descriptor, temp_name = tempfile.mkstemp(
        dir=RUN_DIR,
        prefix=f".{destination.name}.",
    )
    temp_path = Path(temp_name)

    try:
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
            newline="",
        ) as file:
            yield file
            file.flush()
            os.fsync(file.fileno())

        temp_path.chmod(0o600)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)
```

```python
with atomic_text_destination(
    RUN_DIR / "category-summary.csv"
) as file:
    running_summary.reset_index().to_csv(
        file,
        index=False,
    )
```

오류 행도 같은 방식으로 청크별로 임시 파일에 이어 쓴다.

```python
write_header = True

with atomic_text_destination(
    RUN_DIR / "error-rows.csv"
) as error_file:
    for chunk in read_items(
        LARGE_ITEMS_PATH,
        chunksize=CHUNK_SIZE,
    ):
        _, error_chunk = validate_items(chunk)
        write_header = append_error_chunk(
            error_chunk,
            error_file,
            write_header=write_header,
        )

    if write_header:
        pd.DataFrame(
            columns=SAFE_ERROR_COLUMNS
        ).to_csv(error_file, index=False)
```

실제 Notebook에서는 이 오류 저장을 6절의 집계 루프 안에서 함께 수행해 파일을 두 번 읽지 않는다. 집계 결과, 품질 보고서, 최소화한 오류 행만 저장하고 상품 이름이나 전체 유효 원문은 저장하지 않는다.

CSV를 스프레드시트에서 열면 `=`, `+`, `-`, `@`로 시작하는 문자열이 수식으로 해석될 수 있다. 기계 처리용 원본을 임의로 바꾸지 말고, 스프레드시트 공유가 필요하면 별도의 표시용 사본에서 위험한 셀을 이스케이프한다.

`items.csv`의 `=TrainingFormula` 이름은 이 경계 사례를 확인하기 위한 값이다. 카테고리 요약과 최소 오류 결과에는 이 원문 이름이 포함되지 않아야 한다.

## 9. 05-9의 5분 특징표로 연결한다

05-9에서는 CSV 대신 Combined Log를 한 줄씩 파싱하지만, 파싱된 레코드를 DataFrame 배치로 만든 뒤 집계하는 원리는 같다.

```python
log_frame = pd.DataFrame.from_records(log_records)

log_frame["is_404"] = log_frame["status"].eq(404)
log_frame["path_404"] = log_frame[
    "normalized_path"
].where(log_frame["is_404"])
log_frame["sensitive_path_value"] = log_frame[
    "normalized_path"
].where(log_frame["is_sensitive_path"])
log_frame["sensitive_2xx"] = (
    log_frame["is_sensitive_path"]
    & log_frame["status"].between(200, 299)
)

window_features = (
    log_frame.groupby(
        ["window_start", "ip"],
        observed=True,
    )
    .agg(
        total_requests=("status", "size"),
        not_found_404=("is_404", "sum"),
        unique_404_paths=("path_404", "nunique"),
        sensitive_requests=("is_sensitive_path", "sum"),
        unique_sensitive_paths=(
            "sensitive_path_value",
            "nunique",
        ),
        sensitive_2xx=("sensitive_2xx", "sum"),
    )
    .reset_index()
)
```

`window_features`는 05-9에서 NumPy 조건 마스크의 입력이 된다. 로그의 원문 target·쿼리·User-Agent는 표에 넣지 않고, IP는 결과 저장 직전에 HMAC 별칭으로 바꾼다. 완료된 5분 시간창을 내보내고 메모리에서 제거해야 큰 로그에서도 누적 상태를 제한할 수 있다.

## 10. 오류와 경계 사례

| 상황 | 문제가 되는 처리 | 권장 처리 |
| --- | --- | --- |
| 잘못된 UTF-8 | 대체 문자로 계속 읽음 | `encoding_errors="strict"`로 실패를 드러냄 |
| 문자열 `NA` | 기본 규칙으로 결측 처리 | 데이터 계약에 맞게 `keep_default_na`와 `na_values` 지정 |
| 숫자와 오류 문자열 혼합 | 자동 dtype을 신뢰 | 원문 string을 보존하고 새 숫자 Series 생성 |
| `inf`, `-inf` 숫자 | 변환 성공만 보고 유효하다고 판단 | `np.isfinite()`로 유한한 값인지 검증 |
| `errors="coerce"` 사용 | 변환 후 결측 행을 바로 삭제 | 원문·행 번호·오류 이유를 먼저 분리 |
| 빈 category | 전체 행 삭제 | 정책에 따라 `UNKNOWN` 또는 오류로 명시 |
| 연쇄 인덱싱 | 수정 결과가 원본에 반영된다고 가정 | `.loc[]`와 `.copy()` 사용 |
| 모든 청크 저장 | 마지막에 `concat()` | 청크별 집계만 누적하고 상세 행 해제 |
| 평균의 평균 | 청크 평균을 같은 가중치로 평균 | 전체 합계와 전체 건수로 다시 계산 |
| 고유값이 많은 group key | 누적 메모리가 일정하다고 가정 | 템플릿·상위 N개·외부 저장 전략 사용 |
| 오류 행 전체 저장 | 민감 열까지 그대로 복사 | 재처리에 필요한 최소 열만 저장 |
| 고정 결과 파일 덮어쓰기 | 실패해도 이전 결과가 손상됨 | 새 run 디렉터리와 원자적 교체 사용 |
| CSV를 스프레드시트로 공유 | 문자열을 수식으로 실행 | 별도의 표시용 사본에서 이스케이프 |

## 11. 실습

### 실습 1. 작은 fixture 전체 처리

1. `items.csv`를 strict 정책과 `usecols`로 읽는다.
2. 읽은 열·행 수·dtype·결측 건수를 확인한다.
3. `validate_items()`로 유효 행과 오류 행을 분리한다.
4. 오류 이유별 건수와 원문 숫자 필드를 확인한다.
5. 카테고리별 건수·수량·금액을 집계한다.

### 실습 2. 큰 fixture 증분 처리

1. `large_items.csv`를 학습용 `chunksize=50`으로 읽어 여러 청크를 확인한다.
2. 각 청크에서 같은 검증 함수를 재사용한다.
3. 유효·오류 행 수와 카테고리 요약만 누적한다.
4. 오류 행은 임시 CSV에 청크별로 이어 쓴다.
5. 모든 처리가 성공한 뒤 결과 파일을 최종 이름으로 교체한다.

실제 대용량 파일에서는 50,000행 정도로 시작한 뒤 메모리와 처리 시간을 측정해 조정한다. fixture의 작은 청크 크기를 운영 코드에 그대로 복사하지 않는다.

### 실습 3. 전체 처리와 청크 처리 결과 비교

fixture 크기가 메모리에 들어가는 실습 환경에서는 같은 파일을 두 방식으로 처리해 결과를 비교한다.

```python
expected = summarize_items(
    validate_items(read_items(LARGE_ITEMS_PATH))[0]
)
actual = running_summary.sort_index()

pd.testing.assert_frame_equal(
    expected,
    actual,
    check_dtype=False,
)
```

비교가 실패하면 dtype 차이만 무시하고 값·인덱스·열 구조의 차이는 확인한다. 단순히 `check_like=True`로 모든 순서 문제를 숨기기 전에 정렬 기준을 명시한다.

### 실습 4. 최소 수집과 안전 저장 검증

1. DataFrame 열이 `READ_COLUMNS` 허용 목록과 같은지 확인한다.
2. 오류 결과에 `name`과 전체 원문 행이 없는지 확인한다.
3. 출력이 프로젝트의 `outputs/pandas-items/run-*` 아래에만 생성되는지 확인한다.
4. 결과 파일 권한과 임시 파일 잔여 여부를 확인한다.
5. 저장된 CSV에 민감 열 이름이 없는지 검색한다.

## 12. 자기점검

- [ ] Series와 DataFrame의 차이를 설명할 수 있는가?
- [ ] `encoding_errors="strict"`를 사용하는 이유를 설명할 수 있는가?
- [ ] 빈 필드와 변환할 수 없는 숫자 문자열을 구분할 수 있는가?
- [ ] pandas nullable dtype인 `string`, `Int64`, `Float64`의 목적을 설명할 수 있는가?
- [ ] `errors="coerce"` 뒤에 오류 행을 보존해야 하는 이유를 설명할 수 있는가?
- [ ] `.loc[]`와 `.copy()`가 필요한 상황을 설명할 수 있는가?
- [ ] 청크별 합계는 결합할 수 있지만 중앙값은 단순 합산할 수 없는 이유를 설명할 수 있는가?
- [ ] `chunksize`가 모든 누적 메모리를 자동 제한하지 않는 이유를 설명할 수 있는가?
- [ ] 분석에 필요하지 않은 열을 `usecols`에서 제외할 수 있는가?
- [ ] 05-9의 5분 특징표가 어떤 group key와 집계값으로 구성되는지 설명할 수 있는가?

## 13. 응용 인사이트

### 13.1 dtype은 메모리 옵션이 아니라 데이터 계약이다

상품 식별자의 앞자리 0, 문자열 `NA`, 결측 가능한 정수처럼 값의 의미는 dtype과 읽기 옵션에 따라 달라진다. 파일을 읽은 직후 열 이름·dtype·결측 건수·값 범위를 검사해야 이후 통계를 신뢰할 수 있다.

### 13.2 오류 데이터도 분석 산출물이다

오류 행을 삭제하면 결과 숫자는 깔끔해지지만 입력 품질 문제를 추적할 수 없다. 오류 유형과 원문 최소 필드를 별도 보존하면 제공 시스템에 수정 근거를 전달하고 같은 규칙으로 재처리할 수 있다.

### 13.3 청크 처리는 결합 가능한 통계부터 설계한다

대용량 파일에서는 먼저 “청크 결과를 어떤 연산으로 합칠 수 있는가?”를 묻는다. 건수·합계·최솟값·최댓값은 결합하기 쉽고, 평균은 합계와 건수를 함께 보존해야 한다. 중앙값·정확한 고유값·전체 정렬은 별도 전략이 필요하다.

### 13.4 메모리는 행 수와 고유값 수에 모두 영향을 받는다

청크 크기를 줄여도 그룹 키가 계속 증가하면 누적 요약표가 커진다. 05-9에서 URL 식별자 구간을 route template으로 바꾸고 완료된 시간창을 비우는 이유도 같은 원칙이다.

### 13.5 최소 수집은 성능과 보안을 함께 개선한다

불필요한 이메일·토큰·원문 문자열을 읽지 않으면 메모리 사용량과 유출 범위가 동시에 줄어든다. 분석 질문이 바뀌어 열이 더 필요해질 때에는 수집 목적과 저장 정책도 함께 다시 검토한다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 두 fixture를 지정된 경로에서 읽고 스키마를 확인했다.
- [ ] strict 인코딩과 명시적 NA 정책을 적용했다.
- [ ] 자료형·결측·도메인 오류를 분리하고 오류 행을 보존했다.
- [ ] 전체 DataFrame과 청크 증분 집계 결과가 같음을 검증했다.
- [ ] 민감 열을 읽거나 결과에 저장하지 않았다.
- [ ] 결과를 전용 실행 디렉터리에 원자적으로 저장했다.
- [ ] 05-9의 5분 특징표에 같은 pandas 처리 원칙을 적용할 수 있다.
{% endhint %}

---

다음 절: [05-9. 웹 접근 로그 분석 종합 실습](05-9-web-log-analysis.md)
