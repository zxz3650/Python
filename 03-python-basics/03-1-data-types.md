# 03-1. 변수와 기본 자료형

변수와 자료형은 Python이 데이터를 기억하고 해석하는 출발점이다. 같은 `443`이라도 숫자인지 문자열인지에 따라 가능한 연산과 결과가 달라진다.

{% hint style="info" %}
### 🧭 학습 목표

- 변수·값·객체·자료형의 관계를 설명한다.
- `int`, `float`, `bool`, `str`, `None`, `bytes`를 구분한다.
- `type()`, `isinstance()`와 명시적 형변환을 사용한다.
- 변환 오류와 유효 범위를 확인한다.
{% endhint %}

## 1. 변수와 대입

변수는 값을 담는 고정 크기 상자가 아니라 **객체를 가리키는 이름**이다. `=`는 같다는 비교가 아니라 오른쪽 값을 왼쪽 이름에 연결하는 대입 연산자다.

```python
port = 443
service = "https"
is_open = True

print(port, service, is_open)
```

값 비교에는 `==`를 사용한다.

```python
port = 443
print(port == 443)  # True
```

변수 이름은 문자 또는 밑줄로 시작하며 숫자로 시작할 수 없다. 의미가 드러나는 `snake_case` 이름을 사용한다.

```python
failed_count = 3       # 권장
x = 3                  # 의미가 불분명
# 3failed = 3          # SyntaxError
```

## 2. 값·객체·자료형

값은 실제 데이터이고, 객체는 Python이 값을 메모리에서 다루는 단위다. 자료형은 객체가 어떤 값이며 어떤 연산을 지원하는지 결정한다.

```python
port = 443

print(type(port))              # <class 'int'>
print(isinstance(port, int))   # True
print(isinstance(port, str))   # False
```

`type()`은 정확한 자료형을 확인하고, `isinstance()`는 특정 자료형 또는 그 하위 자료형인지 검사한다.

## 3. `443`과 `"443"`이 다른 이유

- `443`: 정수 `int` — 계산과 크기 비교에 사용
- `"443"`: 문자열 `str` — 문자 `4`, `4`, `3`의 순서

```python
print(443 + 1)          # 444
print("443" + "1")      # 4431
print(443 == "443")     # False
```

자료형이 맞지 않으면 오류가 발생한다.

```python
# print("443" + 1)
# TypeError: 문자열과 정수는 바로 더할 수 없음

print(int("443") + 1)   # 444
# int("443a")           # ValueError: 정수로 변환할 수 없음
```

{% hint style="warning" %}
외부 입력과 `input()`의 결과는 기본적으로 문자열이다. 계산하기 전에 형식과 범위를 검증하고 변환한다.
{% endhint %}

## 4. 숫자: int와 float

```python
failed_count = 3       # int
risk_score = 0.85      # float

print(7 / 2)   # 3.5
print(7 // 2)  # 3
print(7 % 2)   # 1
print(2 ** 3)  # 8
```

`int`는 포트·횟수·PID처럼 정수값에, `float`는 비율·점수·측정 시간에 사용한다. 부동소수점은 일부 소수를 정확히 표현하지 못한다.

```python
print(0.1 + 0.2)  # 0.30000000000000004
```

정확한 금액이나 정밀 계산에는 목적에 따라 `decimal.Decimal`을 검토한다.

## 5. bool과 비교 결과

`bool`은 `True` 또는 `False` 두 값을 가진다. 비교식의 결과도 bool이다.

```python
port = 443
is_https = port == 443
is_privileged = port < 1024

print(is_https)      # True
print(is_privileged) # True
```

`True`와 `False`는 문자열 `"True"`, `"False"`와 다르다.

```python
print(bool(""))       # False
print(bool("False"))  # True: 비어 있지 않은 문자열
```

## 6. None: 값이 없음을 표현

`None`은 값이 아직 없거나 확인되지 않았음을 나타낸다. 숫자 `0`이나 빈 문자열과 의미가 다르다.

```python
count = 0
country = None

print(count == 0)        # True
print(country is None)   # True
```

`None`은 `==`보다 `is None`으로 확인한다.

## 7. str과 bytes

`str`은 사람이 읽는 문자, `bytes`는 파일 헤더·패킷처럼 바이트 단위의 원시 데이터에 사용한다.

```python
text = "MZ"
raw = b"MZ"

print(type(text))  # str
print(type(raw))   # bytes

encoded = text.encode("utf-8")
decoded = raw.decode("utf-8")
```

문자열과 bytes를 직접 결합할 수 없다. 인코딩 또는 디코딩으로 같은 자료형으로 맞춘다.

## 8. 형변환과 입력 검증

```python
raw_port = "443"

try:
    port = int(raw_port)
except ValueError:
    print("숫자 형식이 아닙니다")
else:
    if not 1 <= port <= 65535:
        print("포트 범위를 벗어났습니다")
    else:
        print("유효한 포트:", port)
```

변환 성공만 확인하지 말고 업무 범위도 검증한다.

## 9. 여러 변수 대입과 언패킹

```python
action, ip, port = "DENY", "198.51.100.9", 443
x, y = 10, 20
x, y = y, x

print(x, y)  # 20 10
```

항목 수가 맞지 않으면 `ValueError`가 발생한다.

## 10. 객체의 변경 가능성

`int`, `float`, `bool`, `str`, `tuple`은 생성 후 내부 값을 바꿀 수 없는 불변 객체다. `list`, `dict`, `set`은 내용을 바꿀 수 있다.

```python
a = 443
b = a
a = 8443

print(a)  # 8443
print(b)  # 443
```

`a`에 새 값을 대입해도 `443` 객체 자체를 고친 것이 아니라 `a`가 새 객체를 가리키게 된다.

{% hint style="success" %}
## 🧪 실습

1. `443`, `"443"`, `443.0`의 자료형과 비교 결과를 확인한다.
2. `"443a"`를 `int()`로 변환하고 오류를 읽는다.
3. `None`, `0`, `""`, `False`의 차이를 출력한다.
4. 입력된 포트가 정수이며 1~65535 범위인지 검증한다.
5. IP·포트·탐지 여부를 적절한 자료형으로 저장한다.
{% endhint %}

## 핵심 정리

- 변수는 객체를 가리키는 이름이다.
- 자료형은 값의 의미와 가능한 연산을 결정한다.
- 외부 입력은 문자열일 가능성이 높으므로 변환과 검증이 필요하다.
- `None`, `0`, 빈 문자열은 업무 의미가 서로 다르다.
- 불변 객체와 변경 가능한 객체의 차이는 자료구조와 함수에서 중요하다.
