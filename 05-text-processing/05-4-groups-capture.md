# 05-4. 그룹과 캡처

그룹은 정규표현식의 일부를 하나의 단위로 묶고, 일치한 문자열에서 필요한 필드만 추출하는 기능이다. 단순히 “패턴이 맞는가”를 확인하는 데서 끝나지 않고 날짜·수준·메시지처럼 의미가 다른 값을 구조화할 때 사용한다.

정규표현식은 문자열의 **구조를 분리**하는 도구다. 캡처한 값의 자료형·허용 범위·필드 간 관계는 다음 절의 데이터 검증 단계에서 별도로 확인한다.

{% hint style="info" %}
### 🧭 학습 목표

- 전체 일치와 캡처 그룹을 구분한다.
- 번호 그룹보다 이름 있는 그룹을 우선 사용하는 이유를 설명한다.
- 캡처가 필요 없는 묶음에 비캡처 그룹을 사용한다.
- 선택 그룹이 일치하지 않았을 때의 `None`을 안전하게 처리한다.
- `finditer()`로 일치값과 원문 위치를 함께 수집한다.
- `sub()`의 이름 있는 역참조와 치환 함수를 목적에 맞게 사용한다.
- 추출·검증·변환 단계를 분리해 재사용 가능한 파서를 설계한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | 전체 일치, 이름 있는 그룹, `groupdict()`, 선택 그룹의 `None` 처리 |
| 권장 | 비캡처 그룹, `finditer()`와 `span()`, 추출 함수의 실패 계약 |
| 심화 | 이름 있는 역참조, 치환 함수, 정규표현식 복잡도와 입력 길이 제한 |

## 선행 지식과 실습 자료

- [05-3. 정규표현식 기초](05-3-regex-basics.md)의 문자 클래스·수량자·앵커를 이해해야 한다.
- 추출한 값의 의미 검증은 [05-5. 데이터 검증](05-5-validation.md)에서 이어서 다룬다.
- 학습자용 TODO 노트북은 [`05-4-groups-capture.ipynb`](../notebooks/05-4-groups-capture.ipynb)에서 진행한다.
- 재현 가능한 입력은 [`event-lines.txt`](../fixtures/05-text-processing/event-lines.txt)를 사용한다.

## 0. 학습 전 확인

다음 코드에서 각 출력값을 예상한다.

```python
import re

pattern = re.compile(
    r"(?P<level>INFO|WARNING|ERROR)"
    r"(?:\s+user=(?P<user>[A-Za-z0-9_-]+))?"
)
match = pattern.fullmatch("ERROR")

print(match.group(0))
print(match.group("level"))
print(match.group("user"))
print(match.groupdict())
```

다음 질문에 답해 본다.

1. `group(0)`과 `group(1)`은 같은 값을 의미하는가?
2. `(?:...)`가 일반 괄호와 다른 점은 무엇인가?
3. 선택 그룹이 일치하지 않으면 빈 문자열과 `None` 중 무엇을 반환하는가?
4. `findall()`보다 `finditer()`가 필요한 경우는 언제인가?
5. 캡처에 성공하면 날짜·IP·상태 코드도 유효하다고 판단할 수 있는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. 캡처 그룹과 전체 일치

괄호 `(...)`는 패턴을 묶는 동시에 일치한 부분을 캡처한다.

```python
import re

date_pattern = re.compile(
    r"(\d{4})-(\d{2})-(\d{2})"
)
match = date_pattern.fullmatch("2026-08-14")

if match is not None:
    print(match.group(0))  # 전체 일치: 2026-08-14
    print(match.group(1))  # 첫 번째 그룹: 2026
    print(match.groups())  # ('2026', '08', '14')
```

`group(0)`은 패턴 전체와 일치한 문자열이다. 괄호로 캡처한 값은 왼쪽 괄호가 나타나는 순서대로 1번부터 번호가 붙는다.

번호 그룹은 짧은 실험에는 편리하지만 패턴 중간에 그룹을 추가하면 뒤의 번호가 모두 바뀔 수 있다. 업무 의미가 있는 필드는 이름 있는 그룹을 사용한다.

## 2. 이름 있는 그룹과 구조화

`(?P<이름>패턴)` 형식으로 그룹에 의미를 부여한다.

```python
event_pattern = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})\s+"
    r"(?P<level>INFO|WARNING|ERROR)\s+"
    r"(?P<message>.+)"
)

match = event_pattern.fullmatch(
    "2026-08-14 ERROR authentication failed"
)

if match is None:
    raise ValueError("이벤트 형식과 일치하지 않는다")

fields = match.groupdict()
print(fields["date"])
print(fields["level"])
print(fields["message"])
```

`groupdict()`는 이름 있는 그룹을 딕셔너리로 반환한다. 필드 이름을 후속 검증 함수의 입력 키와 맞추면 정규표현식 그룹 순서에 의존하지 않고 처리할 수 있다.

```python
def extract_event(line):
    match = event_pattern.fullmatch(line)
    if match is None:
        raise ValueError("EVENT_FORMAT_MISMATCH")

    return {
        **match.groupdict(),
        "raw": line,
    }
```

원문은 재현과 오류 분석을 위해 보존한다. 다만 운영 로그에 계정·토큰 같은 민감정보가 포함될 수 있으므로 원문을 다른 보고서에 그대로 복사하는 정책은 별도로 검토한다.

## 3. 비캡처 그룹과 선택

괄호가 패턴을 묶는 용도로만 필요하다면 `(?:...)`를 사용한다.

```python
file_pattern = re.compile(
    r"[A-Za-z0-9_-]+\.(?:txt|csv)"
)

print(bool(file_pattern.fullmatch("report.csv")))
print(bool(file_pattern.fullmatch("report.exe")))
```

`txt|csv`는 하나의 대안 묶음이지만 결과 필드로 사용할 필요가 없으므로 캡처하지 않는다. 불필요한 캡처를 줄이면 `groups()`의 의미가 안정되고 패턴을 읽기 쉬워진다.

`|`의 적용 범위도 괄호로 명확히 묶는다.

```python
# ERROR 또는 WARNING 전체를 선택한다.
level_pattern = re.compile(r"(?:ERROR|WARNING)")
```

## 4. 선택 그룹과 기본값

그룹 뒤에 `?`를 붙이면 해당 묶음은 0회 또는 1회 나타날 수 있다.

```python
item_pattern = re.compile(
    r"(?P<name>[A-Za-z]+)"
    r"(?:-(?P<number>\d+))?"
)

for value in ["item", "item-15"]:
    match = item_pattern.fullmatch(value)
    if match is not None:
        print(match.groupdict())
```

`item`에서는 `number`가 빈 문자열이 아니라 `None`이다. 바로 `int()`에 전달하지 않고 먼저 존재 여부를 확인한다.

```python
number_text = match.group("number")
number = int(number_text) if number_text is not None else None
```

빈 문자열, 그룹 불일치의 `None`, 숫자 `0`은 서로 다른 값이다. `if number_text:`만 사용하면 어떤 값이 비어 있는지 의도가 흐려질 수 있으므로 `is None`을 사용한다.

## 5. finditer와 원문 위치

문자열 안의 모든 일치값과 위치가 필요하면 `finditer()`를 사용한다.

```python
text = "IDs: AB-2026 and CD-1000"
identifier_pattern = re.compile(
    r"(?P<prefix>[A-Z]{2})-(?P<number>\d{4})"
)

matches = []

for match in identifier_pattern.finditer(text):
    matches.append({
        **match.groupdict(),
        "matched": match.group(0),
        "start": match.start(),
        "end": match.end(),
    })

print(matches)
```

`start()`, `end()`, `span()`은 원문에서 일치한 범위를 알려 준다. 편집기 강조, 오류 위치 표시, 중복 치환 방지처럼 위치가 필요한 작업에 활용한다.

`findall()`은 그룹 수에 따라 문자열 목록이나 튜플 목록을 반환해 결과 형태가 달라진다. 일치 객체·그룹 이름·위치가 필요하면 `finditer()`가 더 명확하다.

## 6. 그룹을 이용한 치환

단순한 형식 변경에는 이름 있는 역참조를 사용할 수 있다.

```python
changed = re.sub(
    r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})",
    r"\g<year>/\g<month>/\g<day>",
    "2026-08-14",
)

print(changed)
```

조건 판단이나 마스킹 규칙이 필요하면 치환 함수를 사용한다.

```python
account_pattern = re.compile(
    r"(?P<prefix>[A-Za-z0-9]{2})"
    r"(?P<middle>[A-Za-z0-9]*)"
    r"(?P<suffix>[A-Za-z0-9]{2})"
)


def mask_account(match):
    hidden = "*" * len(match.group("middle"))
    return (
        match.group("prefix")
        + hidden
        + match.group("suffix")
    )


def mask_account_value(value):
    if account_pattern.fullmatch(value) is None:
        return "*" * len(value)
    return account_pattern.sub(mask_account, value)


print(mask_account_value("student01"))
```

마스킹은 표시용 복사본에 적용하고 원본을 덮어쓰지 않는다. 짧은 값, 비ASCII 계정, 이메일처럼 구조가 다른 값은 별도 정책으로 처리한다. 마스킹된 값도 다시 식별 가능한지 검토해야 한다.

## 오류·경계 사례

### 일치 실패를 곧바로 그룹 접근으로 이어 감

```python
match = event_pattern.fullmatch("broken line")

if match is None:
    print("형식 불일치")
else:
    print(match.groupdict())
```

`None.group(...)`은 `AttributeError`를 발생시킨다. 실패 입력을 건너뛸지, 구조화된 오류로 남길지 함수 계약을 먼저 정한다.

### 정규표현식만으로 날짜 의미를 검증함

`2026-99-99`는 `\d{4}-\d{2}-\d{2}`와 일치할 수 있다. 캡처는 형태를 분리할 뿐 실제 달력 날짜를 보장하지 않는다. 날짜 의미는 05-6에서 `datetime`으로 검증한다.

### `.*`가 필요한 범위보다 넓게 일치함

구분자가 정해져 있다면 `.*`보다 허용 문자나 종료 조건을 구체적으로 표현한다. 입력 길이를 제한하지 않은 복잡한 중첩 수량자는 처리 시간이 급격히 늘 수 있으므로 외부 입력에는 길이 상한과 시간·자원 경계를 함께 둔다.

### `^...$`와 여러 줄 입력을 혼동함

한 레코드 전체를 검사할 때는 `fullmatch()`를 사용한다. 여러 줄 문자열에서 `^`, `$`의 의미는 플래그에 따라 달라질 수 있으므로 한 줄 레코드와 전체 문서를 같은 패턴으로 처리하지 않는다.

### 민감정보를 캡처 결과와 오류에 그대로 남김

캡처한 계정·토큰·쿼리 문자열을 `print()`나 오류 CSV에 그대로 기록하지 않는다. 필요한 식별자는 마스킹하거나 일방향 요약값으로 바꾸고, 원문 접근 권한과 보존 기간을 분리한다.

## 실습

학습자용 TODO 노트북 [`05-4-groups-capture.ipynb`](../notebooks/05-4-groups-capture.ipynb)에서 [`event-lines.txt`](../fixtures/05-text-processing/event-lines.txt)를 처리한다.

1. 각 행에서 날짜·수준·메시지를 이름 있는 그룹으로 추출한다.
2. 선택적인 `user=` 필드가 없는 행에서 `None`을 처리한다.
3. 정상 행에는 원문 위치와 `groupdict()` 결과를 저장한다.
4. 형식이 맞지 않는 행은 행 번호와 일반화된 오류 코드만 별도 수집한다.
5. 계정 필드는 보고서 출력 전에 마스킹한다.
6. 정상·오류 건수의 합이 전체 행 수와 같은지 검증한다.

{% hint style="warning" %}
fixture는 무해한 학습용 합성 데이터다. 실제 로그를 대신 넣을 때는 계정·세션·토큰·쿼리 문자열이 출력 셀과 저장 파일에 노출되지 않는지 먼저 확인한다.
{% endhint %}

## 자기점검

1. `group(0)`, `groups()`, `groupdict()`의 반환값 차이를 설명할 수 있는가?
2. 이름 있는 그룹이 번호 그룹보다 유지보수에 유리한 이유는 무엇인가?
3. 비캡처 그룹이 필요한 예를 하나 만들 수 있는가?
4. 선택 그룹의 `None`과 빈 문자열을 구분할 수 있는가?
5. `findall()` 대신 `finditer()`를 선택해야 하는 조건은 무엇인가?
6. 캡처 성공 뒤에도 의미 검증이 필요한 이유를 설명할 수 있는가?

## 응용 인사이트

- **로그 파서**: 그룹 이름을 출력 스키마의 필드 이름으로 사용하면 정규표현식과 후속 검증 코드의 연결이 분명해진다.
- **민감정보 마스킹**: `sub()`의 치환 함수는 값의 길이와 유형에 따라 다른 정책을 적용할 수 있지만 원본 보존·접근 통제까지 대신하지는 않는다.
- **오류 위치 표시**: `span()`은 편집기, 검수 보고서, 데이터 정제 UI에서 문제가 있는 원문 범위를 표시하는 근거가 된다.
- **파서 유지보수**: 추출 함수와 의미 검증 함수를 분리하면 입력 형식이 바뀌어도 검증 정책을 재사용할 수 있다.
- **성능과 안전성**: 정규표현식은 입력 길이와 패턴 구조에 따라 처리 시간이 달라진다. 외부 대용량 입력에는 길이 제한·표본 테스트·처리 시간 측정을 함께 적용한다.

## 완료 기준

- [ ] 전체 일치와 캡처 그룹을 구분할 수 있다.
- [ ] 이름 있는 그룹과 `groupdict()`로 구조화된 결과를 만들 수 있다.
- [ ] 비캡처 그룹과 선택 그룹을 목적에 맞게 사용할 수 있다.
- [ ] 선택 그룹의 `None`을 안전하게 처리할 수 있다.
- [ ] `finditer()`로 값과 원문 위치를 함께 수집할 수 있다.
- [ ] 추출 결과를 검증 결과와 구분하고 민감값을 노출하지 않을 수 있다.

---

다음 절: [05-5. 데이터 검증](05-5-validation.md)
