# 05-2. 분리·검색·치환

문자열 메서드는 형식이 일정한 텍스트를 처리하는 가장 읽기 쉬운 방법입니다. 정규표현식을 사용하기 전에 문자열 메서드로 충분한지 확인합니다.

{% hint style="info" %}
## 🧭 학습 목표

- `split`, `partition`, `join`을 구분합니다.
- 문자열의 시작·끝·포함 여부를 검사합니다.
- 제한된 횟수만 치환합니다.
- 고정 형식 텍스트를 딕셔너리로 변환합니다.
{% endhint %}

## 선행 지식

05-1의 원문 보존과 정규화를 이해해야 합니다.

## 1. split과 maxsplit

```python
line = "INFO 2026-08-14 message with spaces"
level, date, message = line.split(maxsplit=2)

print(level)
print(date)
print(message)
```

`maxsplit`을 사용하면 마지막 필드에 공백이 포함되어도 필요한 개수만 나눕니다.

## 2. partition

```python
header = "Content-Type: application/json"
name, separator, value = header.partition(":")

if not separator:
    raise ValueError("구분자가 없습니다")

print(name.strip())
print(value.strip())
```

`partition()`은 앞부분·구분자·뒷부분 세 값을 반환합니다.

## 3. 검색

```python
path = "/api/v1/users"

print(path.startswith("/api/"))
print(path.endswith("/users"))
print("/v1/" in path)
print(path.find("users"))
```

존재 여부에는 `in`, 위치가 필요하면 `find()`를 사용합니다. 찾지 못하면 -1입니다.

## 4. 치환과 결합

```python
message = "token=abc123&user=alice"
masked = message.replace("abc123", "***", 1)

parts = ["2026-08-14", "INFO", "completed"]
line = " | ".join(parts)

print(masked)
print(line)
```

`replace()`의 세 번째 인자는 치환 횟수를 제한합니다. `join()`은 문자열 목록을 결합합니다.

## 5. 고정 형식 파싱

```python
def parse_line(line):
    parts = line.split("|", maxsplit=2)

    if len(parts) != 3:
        raise ValueError("필드는 세 개여야 합니다")

    date, level, message = (
        part.strip()
        for part in parts
    )

    return {
        "date": date,
        "level": level,
        "message": message,
        "raw": line,
    }
```

형식 검증과 자료구조 변환을 함수로 분리합니다.

## 6. 정규표현식이 필요한 시점

문자열 메서드는 구분자가 고정되거나 접두사·접미사·정확한 문자열을 다룰 때 적합합니다. 숫자 개수, 문자 범위, 반복 패턴처럼 형태를 표현해야 할 때 정규표현식을 사용합니다.

## 흔한 실수

- `split()` 결과 수를 확인하지 않고 언패킹함
- 메시지 안의 구분자까지 모두 나눔
- `find()`의 -1을 유효 인덱스로 사용함
- 숫자 목록에 `join()`을 직접 호출함

{% hint style="success" %}
## 🧪 종합 실습

`날짜 | 수준 | 메시지` 형식의 여러 줄을 파싱합니다. 잘못된 필드 수는 오류 목록에 저장하고 정상 행은 딕셔너리 리스트로 변환합니다.
{% endhint %}

## 완료 기준

- [ ] 분리 결과의 필드 수를 검증할 수 있습니다.
- [ ] 검색 목적에 맞는 문자열 메서드를 선택할 수 있습니다.
- [ ] 원문을 포함한 구조화 레코드를 만들 수 있습니다.

---

다음 절: [05-3. 정규표현식 기초](05-3-regex-basics.md)
