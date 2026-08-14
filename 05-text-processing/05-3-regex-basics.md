# 05-3. 정규표현식 기초

정규표현식은 문자열의 형태를 패턴으로 표현합니다. 정확한 문자열이 아니라 일정한 규칙을 가진 여러 값을 검색하거나 검증할 때 사용합니다.

{% hint style="info" %}
## 🧭 학습 목표

- raw string으로 패턴을 작성합니다.
- 문자 클래스·수량자·앵커를 이해합니다.
- `search`, `match`, `fullmatch`, `findall`을 구분합니다.
- 지나치게 넓은 패턴을 피합니다.
{% endhint %}

## 선행 지식

05-2의 문자열 검색과 분리를 이해해야 합니다.

## 1. re와 raw string

```python
import re

pattern = r"\d+"
text = "order 125 completed"
result = re.search(pattern, text)

if result:
    print(result.group())  # 125
```

정규표현식에는 역슬래시가 자주 사용되므로 `r"..."` 형태로 작성합니다.

## 2. 문자 클래스

| 패턴 | 의미 |
|---|---|
| `\d` | 숫자 |
| `\w` | 문자·숫자·밑줄 |
| `\s` | 공백 문자 |
| `.` | 줄바꿈 외의 임의 문자 |
| `[ABC]` | A, B, C 중 하나 |
| `[^ABC]` | A, B, C가 아닌 문자 |
| `[0-9]` | 숫자 범위 |

점 자체는 `\.`처럼 이스케이프합니다.

## 3. 수량자

| 패턴 | 의미 |
|---|---|
| `*` | 0회 이상 |
| `+` | 1회 이상 |
| `?` | 0회 또는 1회 |
| `{3}` | 정확히 3회 |
| `{2,4}` | 2~4회 |

```python
text = "IDs: A-12, B-345, C-7"
ids = re.findall(r"[A-Z]-\d+", text)

print(ids)
```

## 4. 시작과 끝

- `^`: 문자열 시작
- `$`: 문자열 끝
- `fullmatch()`: 전체 문자열 일치

```python
pattern = re.compile(r"[A-Z]{2}-\d{4}")

print(bool(pattern.fullmatch("AB-2026")))
print(bool(pattern.fullmatch("X-20")))
```

입력 검증에는 부분 검색보다 `fullmatch()`가 명확합니다.

## 5. 함수 선택

```python
text = "ID=AB-2026"

print(re.search(r"AB-\d+", text))
print(re.match(r"AB-\d+", text))
print(re.fullmatch(r"AB-\d+", text))
print(re.findall(r"\d+", text))
```

- `search`: 어디서든 첫 일치
- `match`: 시작 위치에서 일치
- `fullmatch`: 전체가 일치
- `findall`: 모든 일치값 목록

## 6. 탐욕적 수량자

```python
text = "<b>one</b><b>two</b>"

print(re.findall(r"<b>.*</b>", text))
print(re.findall(r"<b>.*?</b>", text))
```

`*`와 `+`는 가능한 많이 일치합니다. 뒤에 `?`를 붙이면 가능한 적게 일치합니다. HTML 전체 분석에는 전용 파서를 사용합니다.

## 흔한 실수

- raw string을 사용하지 않음
- 검증에 `search()`를 사용해 일부 일치만 확인함
- `.*`로 지나치게 넓게 일치시킴
- 정규표현식만으로 데이터의 의미까지 검증하려 함
- HTML·JSON을 정규표현식으로 완전히 파싱하려 함

{% hint style="success" %}
## 🧪 종합 실습

다음 패턴을 작성합니다.

- `AB-2026` 형태의 식별자
- 문자열 안의 세 자리 이상 숫자
- `.txt` 또는 `.csv`로 끝나는 파일명
- 공백으로 구분된 여러 식별자
{% endhint %}

## 완료 기준

- [ ] 문자 클래스와 수량자를 읽을 수 있습니다.
- [ ] 검색과 전체 입력 검증 함수를 구분할 수 있습니다.
- [ ] 패턴이 지나치게 넓은지 판단할 수 있습니다.

---

다음 절: [05-4. 그룹과 캡처](05-4-groups-capture.md)
