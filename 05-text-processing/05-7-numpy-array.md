# 05-7. NumPy 배열과 대용량 수치 처리

NumPy의 `ndarray`는 같은 자료형의 값을 연속적인 다차원 배열로 저장한다. Python 리스트보다 수치 데이터의 메모리 구조가 단순하고 배열 단위 연산을 제공하므로 반복 집계, 임계값 비교, 비율 계산에 적합하다.

이 절에서는 배열 문법만 익히지 않는다. 05-9 웹 로그 분석에서 IP·시간 구간별 요청 수를 배열로 받은 뒤 **0으로 나누지 않는 비율 계산 → 불리언 마스크 → 여러 조건의 분류**로 연결한다.

{% hint style="info" %}
### 🧭 학습 목표

- Python 리스트와 `ndarray`의 자료형·메모리·연산 차이를 설명한다.
- 배열의 `shape`, `ndim`, `size`, `dtype`, `nbytes`를 확인한다.
- 인덱싱·슬라이싱·view·copy의 차이를 구분한다.
- 벡터 연산과 broadcasting의 결과 shape을 예측한다.
- 불리언 마스크를 결합해 필요한 행을 선택한다.
- `np.divide(..., where=...)`로 0인 분모를 안전하게 처리한다.
- `np.select()`의 조건 우선순위를 정해 탐지 후보를 분류한다.
- 결측값·정수 오버플로·dtype 변환의 경계 사례를 검증한다.
- 배열을 안전한 경로에 저장하고 `allow_pickle=False`로 다시 읽는다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | 배열 구조, 인덱싱, 벡터 연산, 불리언 마스크, 안전한 비율 계산 |
| 권장 | view·copy, broadcasting, NaN, `np.select()`, dtype·메모리 확인 |
| 심화 | 구조화 배열, `.npy` 저장, memmap, 대용량 배열의 임시 메모리 비용 |

## 선행 지식과 실습 자료

- 03장의 리스트·슬라이싱·조건식과 04장의 파일·대용량 처리 개념을 이해해야 한다.
- [05-5. 데이터 검증](05-5-validation.md)의 정상·오류 데이터 분리 이후 수치 배열을 만든다.
- NumPy 결과를 표로 정리하는 방법은 [05-8. pandas와 DataFrame](05-8-pandas-dataframe.md)에서 이어서 다룬다.
- 학습자용 TODO 노트북은 [`05-7-numpy-array.ipynb`](../notebooks/05-7-numpy-array.ipynb)에서 진행한다.
- 풀이 검증용 노트북은 [`05-7-numpy-array-solution.ipynb`](../notebooks/solutions/05-7-numpy-array-solution.ipynb)로 분리한다.
- 재현 가능한 수치 입력은 [`measurements.csv`](../fixtures/05-text-processing/measurements.csv)를 사용한다.

## 0. 학습 전 확인

다음 코드의 결과와 경고 발생 여부를 예상한다.

```python
import numpy as np

requests = np.array([100, 0, 20])
not_found = np.array([10, 0, 15])

rate = np.divide(
    not_found,
    requests,
    out=np.zeros(requests.shape, dtype=np.float64),
    where=requests != 0,
)

candidate = (requests >= 20) & (rate >= 0.5)

print(rate)
print(candidate)
print(np.flatnonzero(candidate))
```

다음 질문에 답해 본다.

1. Python 리스트에 `* 2`를 적용한 결과와 NumPy 배열에 `* 2`를 적용한 결과는 같은가?
2. NumPy 슬라이스를 수정하면 원본도 바뀔 수 있는가?
3. 불리언 배열을 결합할 때 `and` 대신 무엇을 사용하는가?
4. `where=`만 지정하고 `out=`을 생략하면 계산하지 않은 위치의 값이 항상 0인가?
5. 404 건수만으로 후보를 고르면 요청량이 많은 정상 집단이 왜 함께 선택될 수 있는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. NumPy 준비와 버전 확인

02장에서 `requirements.txt`를 설치했다면 NumPy가 이미 포함되어 있다. import가 실패할 때만 현재 활성화한 가상환경을 확인한 뒤 설치한다.

```bash
python -m pip install -r requirements.txt
```

```python
import numpy as np

print(np.__version__)
```

노트북 커널과 패키지를 설치한 Python 환경이 같은지도 확인한다.

```python
import sys

print(sys.executable)
```

## 2. 리스트와 ndarray

Python 리스트는 서로 다른 자료형을 함께 담을 수 있고, `ndarray`는 일반적으로 하나의 `dtype`으로 값을 저장한다.

```python
values = [10, 20, 30, 40]
array = np.array(values)

print(type(values))
print(type(array))
print(array)
print(array.dtype)
```

두 자료구조의 `*` 연산 의미도 다르다.

```python
print(values * 2)  # 목록을 반복한다.
print(array * 2)   # 각 원소를 곱한다.
```

서로 다른 숫자 자료형을 넣으면 공통으로 표현 가능한 dtype으로 변환될 수 있다.

```python
mixed = np.array([1, 2.5, 3])

print(mixed)
print(mixed.dtype)
```

문자열 하나가 섞이면 모든 값이 문자열 dtype으로 바뀔 수 있다. 배열을 만든 뒤 dtype을 확인하고 입력 검증을 생략하지 않는다.

## 3. 배열의 구조

```python
matrix = np.array([
    [10, 20, 30],
    [40, 50, 60],
])

print(matrix.shape)  # (2, 3)
print(matrix.ndim)   # 2
print(matrix.size)   # 6
print(matrix.dtype)
print(matrix.nbytes)
```

| 속성 | 의미 |
| --- | --- |
| `shape` | 축별 길이 |
| `ndim` | 차원 수 |
| `size` | 전체 원소 수 |
| `dtype` | 원소의 자료형 |
| `itemsize` | 원소 하나의 바이트 수 |
| `nbytes` | 배열 데이터 영역의 전체 바이트 수 |

`nbytes`는 배열 데이터 버퍼 크기다. 배열 객체 자체와 연결된 Python 객체의 전체 메모리까지 모두 나타내지는 않는다.

## 4. 배열 생성

```python
print(np.zeros(5, dtype=np.int64))
print(np.ones((2, 3), dtype=np.float64))
print(np.arange(0, 10, 2))
print(np.linspace(0, 1, 5))
```

`arange()`는 일정 간격, `linspace()`는 시작과 끝 사이를 지정한 개수로 나눈다. 부동소수점 간격에는 반올림 오차가 있으므로 끝점 포함이 중요한 구간 생성은 결과를 직접 확인한다.

재현 가능한 난수가 필요하면 전역 상태보다 generator를 만든다.

```python
randomizer = np.random.default_rng(seed=443)
sample = randomizer.integers(0, 100, size=5)

print(sample)
```

고정 seed는 학습·테스트 재현용이며 비밀번호·토큰·암호 키 생성에 사용하지 않는다.

## 5. 인덱싱과 슬라이싱

```python
values = np.array([10, 20, 30, 40, 50])

print(values[0])
print(values[-1])
print(values[1:4])

matrix = np.array([
    [1, 2, 3],
    [4, 5, 6],
])

print(matrix[0, 1])
print(matrix[:, 1])
print(matrix[1, :])
```

다차원 배열은 `배열[행, 열]`처럼 축별 위치를 지정한다. 선택 결과의 shape을 확인해 1차원과 2차원을 혼동하지 않는다.

```python
print(matrix[0].shape)      # (3,)
print(matrix[0:1].shape)    # (1, 3)
```

## 6. view와 copy

NumPy의 기본 슬라이싱은 원본 메모리를 공유하는 view일 수 있다.

```python
original = np.array([10, 20, 30, 40])
view = original[1:3]

view[0] = 999

print(original)  # [10, 999, 30, 40]
print(np.shares_memory(original, view))
```

독립된 배열이 필요하면 `copy()`를 사용한다.

```python
copied = original[1:3].copy()
copied[0] = 100

print(original)
print(copied)
print(np.shares_memory(original, copied))
```

일반 슬라이스와 달리 정수 배열·불리언 마스크를 이용한 고급 인덱싱은 보통 복사본을 만든다. 동작을 외우는 데 그치지 않고 수정 전 `shares_memory()`와 요구사항을 확인한다.

## 7. 벡터 연산과 집계

```python
prices = np.array([1000, 2000, 3000])
quantities = np.array([2, 1, 4])

totals = prices * quantities

print(totals)
print(totals.sum())
print(totals.mean())
print(totals.min())
print(totals.max())
```

배열 연산은 Python 반복문을 직접 작성하지 않고 같은 계산을 여러 원소에 적용한다. 다만 두 배열의 행 순서와 의미가 같은지는 NumPy가 확인하지 못한다. 위치로 결합하기 전에 같은 기준으로 정렬되었는지 검증한다.

빈 배열에서 `mean()`, `min()`, `max()`를 호출할 때 경고나 예외가 발생할 수 있다. 집계 전 `array.size`를 확인한다.

## 8. 불리언 마스크

조건식은 원소별 `bool` 배열을 만든다.

```python
scores = np.array([55, 80, 92, 40])
passed = scores >= 60

print(passed)
print(scores[passed])
print(np.count_nonzero(passed))
```

여러 조건은 `&`, `|`, `~`로 결합하고 각 비교식을 괄호로 묶는다.

```python
review = (scores >= 60) & (scores < 90)
priority = (scores >= 90) | (scores < 50)

print(scores[review])
print(scores[priority])
```

Python의 `and`, `or`, `not`은 배열 전체의 참·거짓을 하나로 결정하려 하므로 원소별 조건에 사용하지 않는다.

마스크를 이용한 대입은 원본 배열을 변경한다.

```python
adjusted = scores.copy()
adjusted[adjusted < 60] = 0

print(scores)
print(adjusted)
```

원본 보존이 필요하면 먼저 복사한다.

## 9. 0으로 나누지 않는 비율 계산

웹 로그에서는 `404 건수 / 전체 요청 수`처럼 비율을 계산한다. 분모가 0인 구간이 있을 수 있으므로 단순 `/` 연산보다 `np.divide()`의 출력과 계산 위치를 명시한다.

```python
requests = np.array([100, 0, 20, 4], dtype=np.int64)
not_found = np.array([10, 0, 15, 4], dtype=np.int64)

not_found_rate = np.divide(
    not_found,
    requests,
    out=np.zeros(requests.shape, dtype=np.float64),
    where=requests != 0,
)

print(not_found_rate)
```

- `where=requests != 0`: 분모가 0이 아닌 위치만 계산한다.
- `out=...`: 계산하지 않은 위치를 0으로 초기화한다.
- `dtype=np.float64`: 정수 나눗셈 결과를 부동소수점으로 보존한다.

`where=`만 사용하고 새 출력 배열의 초기값을 지정하지 않으면 계산하지 않은 위치의 값에 의존해서는 안 된다. 탐지에서 “요청 없음”과 “404 비율 0%”를 구분해야 한다면 결과 배열과 함께 `requests == 0` 마스크를 별도로 유지한다.

## 10. np.select로 여러 조건 분류

05-9에서는 단일 임계값보다 전체 요청 수, 404 비율, 민감 경로 요청을 조합해 조사 우선순위를 만든다.

```python
requests = np.array([120, 80, 25, 3, 0])
not_found = np.array([5, 50, 18, 3, 0])
sensitive_paths = np.array([0, 4, 0, 2, 0])

not_found_rate = np.divide(
    not_found,
    requests,
    out=np.zeros(requests.shape, dtype=np.float64),
    where=requests != 0,
)

enough_requests = requests >= 20
high_404_rate = enough_requests & (not_found_rate >= 0.5)
repeated_sensitive_path = sensitive_paths >= 3

labels = np.select(
    condlist=[
        high_404_rate & repeated_sensitive_path,
        repeated_sensitive_path,
        high_404_rate,
    ],
    choicelist=[
        "both-signals",
        "sensitive-path",
        "high-404-rate",
    ],
    default="baseline",
)

candidate_mask = labels != "baseline"

print(not_found_rate)
print(labels)
print(np.flatnonzero(candidate_mask))
```

`np.select()`는 앞에 있는 조건부터 검사하고 처음 참인 선택값을 사용한다. 겹치는 조건 중 더 구체적인 `both-signals`를 먼저 둔다. 조건 순서를 바꾸면 같은 입력의 분류가 달라질 수 있으므로 결정표와 테스트를 함께 둔다.

이 결과는 침해 확정이 아니라 원본 이벤트를 확인할 **후속 조사 후보**다. 임계값은 합성 fixture의 정답에 맞추는 숫자가 아니라 정상 기준선, 시간 구간, 서비스 규모, 승인된 스캐너 정보를 바탕으로 정한다.

## 11. broadcasting

shape이 다른 배열이라도 뒤쪽 축의 길이가 같거나 한쪽이 1이면 NumPy가 작은 배열을 확장한 것처럼 계산할 수 있다.

```python
matrix = np.array([
    [10, 20, 30],
    [40, 50, 60],
])
offsets = np.array([1, 2, 3])

result = matrix + offsets

print(result)
print(result.shape)
```

`(2, 3)`과 `(3,)`은 호환되어 열별로 더해진다. shape이 호환되지 않으면 `ValueError`가 발생한다.

```python
try:
    matrix + np.array([1, 2])
except ValueError as exc:
    print(type(exc).__name__)
```

우연히 broadcasting이 성립해도 의도한 축과 다를 수 있다. 연산 전 입력 shape과 기대 출력 shape을 검증한다.

## 12. 결측값과 NaN

`NaN`은 주로 부동소수점 배열의 결측 표현으로 사용한다.

```python
values = np.array([10.0, np.nan, 30.0])

print(np.isnan(values))
print(np.mean(values))
print(np.nanmean(values))
print(np.nan == np.nan)  # False
```

NaN 확인에는 `==`가 아니라 `np.isnan()`을 사용한다. `nanmean()`은 결측을 제외하지만 “결측을 무시해도 되는가”라는 분석 정책까지 결정하지 않는다.

모든 값이 NaN인 배열의 `nanmean()`도 경고와 NaN을 만들 수 있다. 유효값 개수를 함께 확인한다.

```python
valid_count = np.count_nonzero(~np.isnan(values))
print(valid_count)
```

## 13. dtype·범위·메모리

```python
large = np.arange(
    1_000_000,
    dtype=np.int64,
)
small = large.astype(np.int32)

print(large.nbytes)
print(small.nbytes)
print(np.iinfo(np.int32))
```

작은 dtype은 메모리를 줄이지만 표현 가능한 범위도 줄인다. 변환 전 실제 최솟값·최댓값과 `np.iinfo()`를 비교한다.

정수 연산은 자동으로 무제한 정밀도로 확장되지 않을 수 있다.

```python
values = np.array([2_000_000_000], dtype=np.int32)
overflowed = values * 2

print(overflowed)
```

합계·곱셈 전에 더 넓은 dtype으로 변환하거나 집계 함수의 dtype을 명시한다.

```python
safe_values = values.astype(np.int64)
print(safe_values * 2)
```

## 14. fixture CSV 읽기

저장소 루트에서 JupyterLab을 실행한다는 과정 규칙에 따라 fixture 경로를 명시한다.

```python
from pathlib import Path

fixture_path = Path(
    "fixtures/05-text-processing/measurements.csv"
)

sample_ids = np.genfromtxt(
    fixture_path,
    delimiter=",",
    skip_header=1,
    usecols=0,
    dtype=np.int64,
)
values = np.genfromtxt(
    fixture_path,
    delimiter=",",
    skip_header=1,
    usecols=1,
    dtype=np.float64,
)

print(sample_ids)
print(values)
```

fixture의 열은 `sample_id`, `value` 순서다. 빈 값과 숫자로 바꿀 수 없는 값은 `genfromtxt()`가 NaN으로 표현한다. 행 수와 식별자 구조를 먼저 검증하고 유효값은 마스크로 분리한다.

```python
if sample_ids.ndim != 1 or values.ndim != 1:
    raise ValueError("measurements.csv는 1차원 열 두 개가 필요하다")
if sample_ids.shape != values.shape:
    raise ValueError("식별자와 측정값의 행 수가 다르다")
if np.unique(sample_ids).size != sample_ids.size:
    raise ValueError("중복 sample_id가 있다")

valid_mask = np.isfinite(values)
valid_values = values[valid_mask]

if valid_values.size == 0:
    raise ValueError("집계할 유효 측정값이 없다")

valid_mean = float(valid_values.mean())
high_mask = valid_mask & (values >= 80)

print(valid_mean)
print(sample_ids[high_mask])
```

`genfromtxt()`는 이 작은 수치 fixture에서 결측 마스크를 연습하기 위한 선택이다. 문자열·수치가 섞인 표와 행별 오류 원문 보존에는 05-8의 pandas 또는 표준 `csv` 모듈이 더 적합하다.

## 15. 배열 저장과 다시 읽기

`.npy`는 shape과 dtype을 보존한다. 실습에서는 fixture와 다른 전용 출력 경로를 사용한다.

```python
output_dir = Path("outputs/numpy-lab")
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / "not-found-rate.npy"

np.save(output_path, not_found_rate, allow_pickle=False)
restored = np.load(output_path, allow_pickle=False)

if not np.array_equal(not_found_rate, restored):
    raise ValueError("저장 전후 배열이 다르다")
```

외부에서 받은 `.npy`의 object 배열을 pickle 허용 상태로 읽지 않는다. 수치 배열은 `allow_pickle=False`로 제한하고 shape·dtype·값 범위를 다시 검증한다.

운영 출력은 04-8의 임시 파일·재검증·원자적 교체 원칙을 적용한다. 입력 fixture를 출력 경로로 사용하지 않는다.

## 16. 메모리 매핑

파일이 매우 커서 메모리에 모두 올리기 어렵고 고정 dtype 배열에 임의 위치 접근이 필요하면 `memmap`을 검토한다.

```python
mapped_path = output_dir / "large-array.dat"
mapped = np.memmap(
    mapped_path,
    dtype="float32",
    mode="w+",
    shape=(1_000_000,),
)

mapped[:3] = [1.0, 2.0, 3.0]
mapped.flush()

print(mapped[:3])
```

memmap은 일반 CSV의 행별 형식 검증이나 가변 길이 문자열 처리에 적합하지 않다. 파일 shape·dtype·생성 주체를 신뢰할 수 있어야 하며 파일 생명주기와 동시 접근 정책도 별도로 관리한다.

## 17. NumPy와 pandas 선택

| 상황 | 권장 도구 |
| --- | --- |
| 같은 dtype의 수치 배열 | NumPy |
| 행·열 이름이 있는 표 | pandas |
| 행별 오류를 보존하는 CSV 변환 | 표준 `csv` 또는 pandas 청크 |
| 행렬·통계·벡터 연산 | NumPy |
| 문자열·수치가 섞인 데이터 | pandas |
| 매우 큰 고정형 배열 | NumPy memmap 검토 |
| IP별 집계 결과의 비율·분류 | NumPy 또는 pandas 열 연산 |

pandas의 수치 연산 상당 부분은 NumPy 배열 개념과 연결된다. 반대로 NumPy 배열에는 열 이름과 데이터 의미가 없으므로 열 순서 계약을 코드와 문서에서 관리해야 한다.

## 오류·경계 사례

### 마스크 결합에 `and`와 `or`를 사용함

배열의 원소별 조건에는 `&`, `|`, `~`를 사용하고 비교식을 괄호로 묶는다. `and`와 `or`는 배열 전체를 하나의 bool로 바꾸려 해 `ValueError`를 발생시킬 수 있다.

### `np.divide()`에서 계산하지 않은 위치를 초기화하지 않음

`where=`와 함께 `out=`을 명시적으로 0 또는 정책상 결측값으로 초기화한다. 분모 0을 비율 0으로 표현했다면 `zero_denominator` 마스크도 유지해 “관측 없음”과 실제 0%를 구분한다.

### 404 건수만으로 후보를 선택함

높은 트래픽은 절대 404 건수도 크게 만들 수 있다. 최소 요청 수, 404 비율, 민감 경로 요청, 시간 구간을 함께 보고 임계값은 정상 기준선으로 검증한다.

### `np.select()` 조건 순서를 바꿈

여러 조건이 동시에 참이면 첫 번째 조건의 선택값이 사용된다. 더 구체적인 결합 조건을 먼저 두고 결정표와 경계값 테스트로 순서를 고정한다.

### 슬라이스를 복사본으로 생각하고 수정함

기본 슬라이스는 view일 수 있다. 원본 보존이 필요하면 `.copy()`를 사용하고 저장 전후 원본 배열이 바뀌지 않았는지 검증한다.

### 작은 dtype으로 바꾼 뒤 오버플로를 놓침

파일 크기만 보고 dtype을 줄이지 않는다. 최솟값·최댓값뿐 아니라 이후 덧셈·곱셈·누적 결과 범위까지 확인한다.

### 벡터화가 항상 메모리를 줄인다고 가정함

연산식 중간에 큰 임시 배열과 마스크가 여러 개 만들어질 수 있다. 대용량 처리에서는 배치 크기, dtype, 임시 배열 수와 실제 메모리 사용량을 함께 측정한다.

## 실습

먼저 학습자용 TODO 노트북 [`05-7-numpy-array.ipynb`](../notebooks/05-7-numpy-array.ipynb)을 완성한다. 구현 후에만 [`05-7-numpy-array-solution.ipynb`](../notebooks/solutions/05-7-numpy-array-solution.ipynb)의 검증 결과와 비교한다.

[`measurements.csv`](../fixtures/05-text-processing/measurements.csv)를 다음 순서로 처리한다.

1. fixture 경로와 `sample_id`·`value` 행 수를 검증한다.
2. `np.isfinite()`로 유효값 마스크를 만들고 평균을 계산한다.
3. 유효한 값 가운데 80 이상인 행을 마스크로 선택한다.
4. 원본 `values`를 변경하지 않았는지 검증한다.
5. 10절의 요청 수·404 수·민감 경로 수 배열로 05-9 연결 실습을 진행한다.
6. `np.divide(..., out=..., where=...)`로 404 비율을 계산한다.
7. 최소 요청 수·404 비율·민감 경로 반복 조건을 불리언 마스크로 결합한다.
8. `np.select()`로 `both-signals`, `sensitive-path`, `high-404-rate`, `baseline`을 분류한다.
9. 조건 순서를 바꿨을 때 겹치는 행의 분류가 어떻게 달라지는지 설명한다.
10. 결과 배열을 전용 출력 경로에 저장하고 `allow_pickle=False`로 다시 읽어 검증한다.
11. 입력 fixture의 해시와 내용이 바뀌지 않았는지 확인한다.

{% hint style="warning" %}
fixture는 탐지 로직 검증을 위한 합성 집계다. 특정 임계값에서 예상 행이 선택된다는 사실은 운영 환경에서 같은 임계값이 유효하다는 뜻이 아니다.
{% endhint %}

## 자기점검

1. 리스트와 ndarray의 `*` 연산 차이를 설명할 수 있는가?
2. `shape`, `dtype`, `nbytes`가 각각 무엇을 나타내는가?
3. view와 copy를 어떻게 구분하고 원본 변경을 피하는가?
4. 불리언 마스크에서 `&`, `|`, `~`와 괄호가 필요한 이유는 무엇인가?
5. `np.divide()`의 `out`과 `where`는 각각 어떤 문제를 해결하는가?
6. `np.select()`에서 조건 순서가 결과에 영향을 주는 이유는 무엇인가?
7. 절대 건수와 비율을 함께 봐야 하는 이유를 설명할 수 있는가?
8. NumPy보다 pandas 또는 스트리밍 처리가 적합한 입력을 구분할 수 있는가?

## 응용 인사이트

- **웹 로그 탐지**: pandas·Counter로 만든 IP별 집계를 NumPy 배열로 변환하면 비율·마스크·분류를 명시적인 수치 단계로 검증할 수 있다.
- **기준선 비교**: 절대 건수만 보는 규칙보다 최소 표본 수와 비율을 함께 사용하면 높은 정상 트래픽이 만드는 후보 수를 줄이는 데 도움이 된다.
- **결정표 구현**: `np.select()`는 여러 신호의 우선순위를 코드로 표현한다. 조건 순서와 기본값을 문서화해야 결과를 설명할 수 있다.
- **데이터 품질**: 0인 분모, NaN, 음수 건수, dtype 오버플로는 탐지 결과를 바꾸므로 분석 전에 별도 품질 지표로 확인한다.
- **성능 설계**: 벡터 연산은 Python 반복문 비용을 줄이지만 입력 정렬·메모리·임시 배열 문제까지 자동으로 해결하지 않는다.
- **후속 조사**: 배열 분류 결과는 원본 로그, 프록시 구조, 승인된 스캐너, 시간 범위를 확인하기 위한 우선순위이지 공격 확정값이 아니다.

## 완료 기준

- [ ] 리스트와 ndarray의 자료형·메모리·연산 차이를 설명할 수 있다.
- [ ] shape·dtype·인덱싱·view·copy를 구분할 수 있다.
- [ ] 불리언 마스크와 broadcasting 결과를 예측할 수 있다.
- [ ] `np.divide(..., where=...)`로 0인 분모를 안전하게 처리할 수 있다.
- [ ] `np.select()` 조건 우선순위로 조사 후보를 분류할 수 있다.
- [ ] NaN·dtype·오버플로·빈 배열의 경계 사례를 검증할 수 있다.
- [ ] fixture를 수정하지 않고 결과 배열을 별도 경로에 저장·재검증할 수 있다.
- [ ] 05-9 로그 집계에서 NumPy를 사용하는 이유와 한계를 설명할 수 있다.

---

다음 절: [05-8. pandas와 DataFrame 기반 대용량 처리](05-8-pandas-dataframe.md)
