# 04-7. NumPy 배열과 대용량 수치 처리

NumPy의 ndarray는 같은 자료형의 값을 연속적인 다차원 배열로 저장합니다. Python 리스트보다 메모리 구조가 단순하고 수치 연산을 배열 단위로 수행할 수 있어 pandas와 과학·통계 처리의 기반이 됩니다.

{% hint style="info" %}
## 🧭 학습 목표

- Python 리스트와 ndarray의 차이를 설명합니다.
- 배열의 shape, ndim, size, dtype을 확인합니다.
- 인덱싱·슬라이싱·조건 마스크를 사용합니다.
- 벡터 연산과 broadcasting을 이해합니다.
- 배열의 메모리 크기를 확인하고 파일로 저장합니다.
- memmap을 이용한 디스크 기반 배열의 목적을 설명합니다.
{% endhint %}

## 선행 지식

03장의 리스트·자료형·슬라이싱과 04-3의 bytes, 04-6의 대용량 처리 개념을 이해해야 합니다.

## 1. NumPy 설치

```bash
python -m pip install numpy
```

```python
import numpy as np

print(np.__version__)
```

## 2. 리스트와 ndarray

```python
import numpy as np

values = [10, 20, 30, 40]
array = np.array(values)

print(type(values))
print(type(array))
print(array)
```

Python 리스트는 서로 다른 자료형을 함께 담을 수 있지만 ndarray는 일반적으로 하나의 dtype으로 값을 저장합니다.

```python
mixed = np.array([1, 2.5, 3])
print(mixed)
print(mixed.dtype)
```

서로 다른 숫자 자료형을 넣으면 공통으로 표현 가능한 자료형으로 변환될 수 있습니다.

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
```

- `shape`: 축별 길이
- `ndim`: 차원 수
- `size`: 전체 원소 수
- `dtype`: 원소 자료형

## 4. 배열 생성

```python
print(np.zeros(5, dtype=np.int64))
print(np.ones((2, 3)))
print(np.arange(0, 10, 2))
print(np.linspace(0, 1, 5))
```

`arange()`는 일정 간격, `linspace()`는 시작과 끝 사이를 지정한 개수로 나눕니다.

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
```

다차원 배열은 `배열[행, 열]` 형태로 접근할 수 있습니다.

## 6. view와 copy

NumPy 슬라이싱은 원본 메모리를 공유하는 view일 수 있습니다.

```python
original = np.array([10, 20, 30, 40])
view = original[1:3]

view[0] = 999

print(original)
```

독립된 배열이 필요하면 `copy()`를 사용합니다.

```python
copied = original[1:3].copy()
copied[0] = 100

print(original)
print(copied)
```

## 7. 벡터 연산

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

Python 반복문을 직접 작성하지 않고 배열 전체에 같은 연산을 적용합니다.

## 8. 조건 마스크

```python
scores = np.array([55, 80, 92, 40])

mask = scores >= 60

print(mask)
print(scores[mask])
```

조건식은 bool 배열을 만들며 이를 이용해 필요한 원소만 선택할 수 있습니다.

```python
scores[scores < 60] = 0
print(scores)
```

조건에 맞는 원본 값도 변경될 수 있으므로 복사 여부를 확인합니다.

## 9. broadcasting

```python
matrix = np.array([
    [10, 20, 30],
    [40, 50, 60],
])

offsets = np.array([1, 2, 3])

print(matrix + offsets)
```

크기가 다른 배열이라도 shape이 호환되면 NumPy가 작은 배열을 확장한 것처럼 계산합니다. 호환되지 않으면 `ValueError`가 발생합니다.

## 10. 결측값과 NaN

```python
values = np.array([10.0, np.nan, 30.0])

print(np.isnan(values))
print(np.mean(values))
print(np.nanmean(values))
```

`NaN`은 부동소수점 결측 표현입니다. 일반 평균은 NaN이 될 수 있으며 `nanmean()`처럼 결측을 제외하는 함수를 목적에 맞게 선택합니다.

```python
print(np.nan == np.nan)  # False
```

NaN 확인에는 `==`가 아니라 `np.isnan()`을 사용합니다.

## 11. dtype과 메모리

```python
large = np.arange(
    1_000_000,
    dtype=np.int64,
)

print(large.nbytes)

small = large.astype(np.int32)
print(small.nbytes)
```

작은 dtype은 메모리를 줄일 수 있지만 표현 가능한 값의 범위도 줄어듭니다. 실제 최솟값·최댓값을 확인한 뒤 변환합니다.

```python
print(np.iinfo(np.int32))
```

## 12. 텍스트 데이터 읽기

수치 데이터만 있는 단순 파일에는 `loadtxt()`를 사용할 수 있습니다.

```python
data = np.loadtxt(
    "measurements.csv",
    delimiter=",",
    skiprows=1,
)

print(data.shape)
```

누락값이 있으면 `genfromtxt()`를 사용할 수 있지만, 문자열과 수치가 섞인 표 데이터에는 pandas가 더 편리합니다.

## 13. 배열 저장

```python
array = np.arange(10)

np.save("values.npy", array)
loaded = np.load("values.npy")

print(np.array_equal(array, loaded))
```

`.npy` 형식은 shape과 dtype을 보존합니다. 여러 배열은 `np.savez()`로 저장할 수 있습니다.

## 14. 메모리 매핑

파일이 매우 커서 메모리에 모두 올리기 어렵다면 `memmap`으로 디스크 배열의 일부를 접근할 수 있습니다.

```python
mapped = np.memmap(
    "large_array.dat",
    dtype="float32",
    mode="w+",
    shape=(1_000_000,),
)

mapped[:3] = [1.0, 2.0, 3.0]
mapped.flush()
```

memmap은 임의 위치 접근이 필요한 고정 dtype 배열에 적합합니다. 일반 CSV의 행별 검증에는 청크 처리 방식이 더 자연스럽습니다.

## 15. NumPy와 pandas 선택

| 상황 | 권장 도구 |
|---|---|
| 같은 dtype의 수치 배열 | NumPy |
| 행·열 이름이 있는 표 | pandas |
| 행별 오류 보존 CSV 변환 | csv 또는 pandas 청크 |
| 행렬·통계·벡터 연산 | NumPy |
| 문자열·수치가 섞인 데이터 | pandas |
| 매우 큰 고정형 배열 | NumPy memmap |

pandas의 수치 연산 상당 부분은 내부적으로 NumPy 배열 개념과 연결됩니다.

## 흔한 실수

- ndarray에 서로 다른 자료형을 넣고 원래 형식이 유지된다고 생각함
- 슬라이스가 항상 복사본이라고 생각함
- shape이 다른 배열의 broadcasting 결과를 예측하지 않음
- NaN을 `==`로 비교함
- 작은 dtype으로 변환하면서 값의 범위를 확인하지 않음
- CSV 전체를 NumPy로 처리하려고 함

{% hint style="success" %}
## 🧪 종합 실습

측정값 CSV를 NumPy 배열로 읽습니다.

1. 배열의 shape과 dtype을 확인합니다.
2. 결측값을 찾습니다.
3. 정상값의 평균·최솟값·최댓값을 계산합니다.
4. 기준 이상 값만 조건 마스크로 선택합니다.
5. dtype 변경 전후 메모리 크기를 비교합니다.
6. 결과 배열을 `.npy`로 저장하고 다시 읽습니다.
{% endhint %}

## 완료 기준

- [ ] 리스트와 ndarray의 메모리·연산 차이를 설명할 수 있습니다.
- [ ] shape·dtype·조건 마스크를 사용할 수 있습니다.
- [ ] view와 copy의 차이를 설명할 수 있습니다.
- [ ] 결측값을 확인하고 목적에 맞게 집계할 수 있습니다.
- [ ] NumPy와 pandas의 선택 기준을 설명할 수 있습니다.

---

다음 절: [04-8. pandas와 DataFrame 기반 대용량 처리](04-8-pandas-dataframe.md)
