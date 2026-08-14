# 03-6. 예외 처리

예외는 문법적으로 올바른 코드가 실행 중 처리할 수 없는 상황을 만났을 때 발생합니다. 오류를 숨기기보다 원인과 위치를 읽고, 예상 가능한 실패만 처리하는 것이 목표입니다.

{% hint style="info" %}
## 🧭 학습 목표

- 문법 오류와 실행 예외를 구분합니다.
- traceback에서 오류 유형·메시지·발생 위치를 찾습니다.
- `try`, `except`, `else`, `finally`를 사용합니다.
- `raise`로 의미 있는 오류를 전달합니다.
{% endhint %}

## 선행 지식

함수, 조건문, 자료형을 이해해야 합니다.

## 1. 오류 메시지 읽기

```python
def convert(value):
    return int(value)

convert("abc")
```

traceback은 마지막 줄의 예외 유형과 메시지를 먼저 확인하고, 위쪽의 파일명과 행 번호를 따라갑니다.

## 2. 예상 가능한 예외 처리

```python
value = "443"

try:
    number = int(value)
except ValueError as exc:
    print("숫자로 변환할 수 없습니다:", exc)
else:
    print("변환 결과:", number)
finally:
    print("변환 작업 종료")
```

`try` 블록에는 실제로 실패가 예상되는 최소 코드만 둡니다.

## 3. 구체적인 예외

- `ValueError`: 값의 형식이나 범위가 잘못됨
- `TypeError`: 자료형이 맞지 않음
- `KeyError`: 딕셔너리 키가 없음
- `IndexError`: 인덱스 범위를 벗어남
- `FileNotFoundError`: 파일을 찾을 수 없음

모든 오류를 `except Exception`으로 숨기지 않습니다.

## 4. raise와 원인 보존

```python
def parse_age(value):
    try:
        age = int(value)
    except ValueError as exc:
        raise ValueError(f"잘못된 나이: {value!r}") from exc

    if age < 0:
        raise ValueError("나이는 0 이상이어야 합니다")
    return age
```

{% hint style="success" %}
## 🧪 종합 실습

사용자 입력을 정수로 변환하고 허용 범위를 검사합니다. 정상값, 문자 입력, 범위 밖 숫자를 각각 실행하고 결과를 기록합니다.
{% endhint %}

## 완료 기준

- [ ] traceback에서 예외 유형과 발생 행을 찾을 수 있습니다.
- [ ] 예상 가능한 예외를 구체적으로 처리할 수 있습니다.
- [ ] 업무 의미를 가진 예외를 직접 발생시킬 수 있습니다.

---

다음 절: [03-7. 모듈과 패키지](03-7-errors-modules.md)
