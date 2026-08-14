# 05-4. 그룹과 캡처

그룹은 패턴의 일부를 하나의 단위로 묶고, 일치한 문자열에서 필요한 값만 추출하는 기능입니다.

{% hint style="info" %}
## 🧭 학습 목표

- 캡처 그룹과 비캡처 그룹을 구분합니다.
- 이름 있는 그룹으로 결과의 의미를 표현합니다.
- `finditer()`로 값과 위치를 함께 수집합니다.
- `sub()`에서 그룹을 이용해 문자열을 변환합니다.
{% endhint %}

## 선행 지식

05-3의 문자 클래스와 수량자를 이해해야 합니다.

## 1. 캡처 그룹

```python
import re

text = "2026-08-14"
result = re.fullmatch(
    r"(\d{4})-(\d{2})-(\d{2})",
    text,
)

if result:
    print(result.group(0))
    print(result.group(1))
    print(result.groups())
```

0번 그룹은 전체 일치, 1번부터 괄호로 묶은 그룹입니다.

## 2. 이름 있는 그룹

```python
pattern = re.compile(
    r"(?P<year>\d{4})-"
    r"(?P<month>\d{2})-"
    r"(?P<day>\d{2})"
)

result = pattern.fullmatch("2026-08-14")

if result:
    print(result.group("year"))
    print(result.groupdict())
```

이름을 사용하면 그룹 순서보다 의미가 분명합니다.

## 3. 비캡처 그룹과 선택

```python
file_pattern = re.compile(
    r"^[a-zA-Z0-9_-]+\.(?:txt|csv)$"
)

print(bool(file_pattern.fullmatch("report.csv")))
```

`(?:...)`는 묶음은 필요하지만 결과로 캡처하지 않을 때 사용합니다. `|`는 여러 대안 중 하나를 의미합니다.

## 4. 선택 항목

```python
pattern = re.compile(
    r"(?P<name>[A-Za-z]+)"
    r"(?:-(?P<number>\d+))?"
)

for value in ["item", "item-15"]:
    result = pattern.fullmatch(value)
    print(result.groupdict())
```

선택 그룹이 일치하지 않으면 값은 `None`입니다.

## 5. finditer

```python
text = "IDs: AB-2026 and CD-1000"
pattern = re.compile(r"[A-Z]{2}-\d{4}")

for result in pattern.finditer(text):
    print(result.group(), result.start(), result.end())
```

일치값뿐 아니라 원문 위치가 필요하면 `finditer()`를 사용합니다.

## 6. 그룹을 이용한 치환

```python
text = "2026-08-14"

changed = re.sub(
    r"(\d{4})-(\d{2})-(\d{2})",
    r"\1/\2/\3",
    text,
)

print(changed)
```

복잡한 치환은 이름 있는 그룹과 함수를 사용하면 읽기 쉽습니다.

## 흔한 실수

- 전체 일치와 첫 번째 그룹을 혼동함
- 그룹을 추가한 뒤 번호가 바뀐 사실을 놓침
- 캡처가 필요 없는 묶음도 모두 캡처함
- 선택 그룹이 항상 문자열이라고 가정함
- 추출 후 값의 범위를 검증하지 않음

{% hint style="success" %}
## 🧪 종합 실습

`2026-08-14 INFO completed` 형태에서 날짜·수준·메시지를 이름 있는 그룹으로 추출하고 딕셔너리로 변환합니다. 일치 위치도 함께 기록합니다.
{% endhint %}

## 완료 기준

- [ ] 그룹과 전체 일치를 구분할 수 있습니다.
- [ ] 이름 있는 그룹으로 딕셔너리를 만들 수 있습니다.
- [ ] 일치값의 원문 위치를 수집할 수 있습니다.

---

다음 절: [05-5. 데이터 검증](05-5-validation.md)
