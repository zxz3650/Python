# 03-1. 변수와 기본 자료형 — 원시 이벤트를 분석 가능한 데이터로 바꾸기

오전 9시 17분, 조사 파이프라인에 방화벽 이벤트 한 건과 연계 파일의 시작 바이트가 함께 수집되었다고 하자.

```text
방화벽 이벤트: DENY,198.51.100.9,443,0.85,
파일 시작 바이트: b"MZ"
```

사람은 이 기록들을 보고 대략 뜻을 짐작할 수 있다. 그러나 Python에는 먼저 알려 주어야 할 것이 많다.

- `443`은 화면에 표시할 글자인가, 범위를 검사할 포트 번호인가?
- `0.85`는 문자열인가, 계산할 수 있는 위험 점수인가?
- 비어 있는 국가는 정말 `""`인가, 아직 확인하지 못했다는 `None`인가?
- `MZ`는 사람이 읽는 글자인가, 파일에서 읽은 실제 바이트인가?

이 구분을 잘못하면 프로그램이 즉시 오류를 내기도 하지만, 더 위험하게는 **실행은 되면서 잘못된 판단을 내릴 수도 있다.** 예를 들어 `bool("False")`는 `False`가 아니라 `True`다.

이 절의 임무는 문법 이름을 하나씩 외우는 것이 아니다. 이 사건의 값에 의미를 부여해, 이후 조건문·반복문·파일 처리에서 사용할 수 있는 **분석 가능한 이벤트 프로필**로 바꾸는 것이다.

{% hint style="info" %}
### 🧭 이번 임무의 완료 목표

- 원시 이벤트의 각 필드에 의미가 드러나는 이름을 붙인다.
- 분석 질문에 맞게 `int`, `float`, `bool`, `str`, `None`, `bytes`를 선택한다.
- `=`와 `==`, 숫자와 숫자 모양 문자열을 구분한다.
- `type()`, `isinstance()`로 가정을 확인하고 필요한 값을 명시적으로 변환한다.
- “숫자로 바꿀 수 있는가”와 “업무상 유효한 값인가”를 구분한다.
- 정제한 값으로 이벤트 프로필 한 건을 완성하고 설명한다.
{% endhint %}

## 오늘 만들 결과

절의 마지막에는 원본을 보존한 채 다음 상태를 만들게 된다.

```python
raw_port = "443"               # 수집된 원본
port = 443                      # 범위를 검사할 수 있는 정수
risk_score = 0.85               # 계산할 수 있는 실수
is_detected = True              # 판단 결과
country = None                  # 아직 확인되지 않음
file_signature = b"MZ"         # 파일에서 읽은 원시 바이트
```

이 값들은 다음 절들에서 서로 연결된다. 조건문은 `port`와 `risk_score`를 보고 판단하고, 반복문은 여러 이벤트에 같은 처리를 적용하며, 파일 처리 코드는 `file_signature`를 실제 파일과 비교한다. **기본 자료형은 이후 자동화가 믿고 사용할 데이터의 계약**이다.

## 임무 진행 순서

| 단계 | 해결할 질문 | 배우는 도구 |
|---|---|---|
| 1. 사실에 이름 붙이기 | 이 값은 무엇을 뜻하는가? | 변수, 대입, 이름 규칙 |
| 2. Python의 해석 확인하기 | 이름만 보고 자료형도 알 수 있는가? | 값·객체·자료형, `type()`, `isinstance()` |
| 3. 질문에 맞는 형태 고르기 | 이 값으로 무엇을 할 것인가? | `int`, `float`, `bool`, `str`, `None`, `bytes` |
| 4. 원본을 분석 값으로 바꾸기 | 외부 문자열을 어떻게 안전하게 사용할까? | 명시적 형변환 |
| 5. 신뢰 경계 확인하기 | 변환되면 모두 유효한 값일까? | 형식 검증, 범위 검증 |

## 실습하는 방법

각 예제는 다음 순서로 학습한다.

1. 코드를 실행하기 전에 결과와 자료형을 예상한다.
2. 코드를 실행해 예상과 실제 결과를 비교한다.
3. 결과가 나온 이유를 한 문장으로 설명한다.
4. 값 하나를 바꾸고 결과가 어떻게 달라지는지 확인한다.

이 절의 전용 실습은 [`notebooks/03-1-data-types.ipynb`](../notebooks/03-1-data-types.ipynb)에서 진행할 수 있다.

## 0. 임무 브리핑 — 같은 모양, 다른 의미

아직 실행하지 말고 각 코드의 출력 결과를 예상한다.

```python
print(10 + 20)
print("10" + "20")
print(10 == "10")
print(bool("False"))
```

다음 질문에도 답해 본다.

1. `=`와 `==`는 어떤 차이가 있는가?
2. `0`, `""`, `False`, `None`은 모두 같은 값인가?
3. `input()`으로 입력한 `443`은 숫자일까, 문자열일까?

답을 확신할 수 없어도 괜찮다. 지금의 예상은 출발점이다. 절의 마지막에서 같은 질문에 다시 답하고, 그 차이가 실제 보안 분석에 어떤 영향을 주는지 설명하게 된다.

## 1단계. 흩어진 사실에 이름 붙이기 — 변수와 대입

수집된 이벤트를 그대로 두면 `443`이 출발지 포트인지 목적지 포트인지 알 수 없다. 분석의 첫 단계는 각 사실에 의미가 드러나는 이름을 붙이는 것이다.

변수는 값을 담는 고정 크기 상자가 아니라 **객체를 가리키는 이름**이다. `=`는 같다는 뜻이 아니라 오른쪽 값을 왼쪽 이름에 연결하는 대입 연산자다.

```python
port = 443
service = "https"
is_open = True

print(port, service, is_open)
```

값이 같은지 비교할 때는 `==`를 사용한다.

```python
port = 443

print(port == 443)   # True
print(port == 80)    # False
```

### 변수 이름 규칙

- 문자 또는 밑줄(`_`)로 시작한다.
- 두 번째 글자부터 숫자를 사용할 수 있다.
- 대문자와 소문자를 구분한다. `port`와 `Port`는 다른 이름이다.
- Python 예약어인 `if`, `for`, `class` 등은 변수 이름으로 사용할 수 없다.
- 여러 단어는 `failed_login_count`처럼 `snake_case`로 연결한다.
- 값의 의미가 드러나는 이름을 사용한다.

```python
failed_login_count = 3   # 의미가 분명함
x = 3                    # 짧지만 의미가 불분명함
port_443_open = True     # 숫자는 첫 글자가 아니면 사용 가능

# 3failed = 3            # SyntaxError: 숫자로 시작
# class = "network"      # SyntaxError: 예약어 사용
```

{% hint style="warning" %}
`l`, `O`, `I`처럼 숫자 `1`, `0`과 혼동되는 한 글자 변수명은 피한다. 짧은 예제에서도 데이터의 의미가 드러나는 이름을 사용한다.
{% endhint %}

## 2단계. Python이 값을 어떻게 보는지 확인하기 — 값·객체·자료형

이름을 붙였다고 분석 준비가 끝난 것은 아니다. `destination_port`라는 이름에 `"443"`을 대입해도 Python은 그 값을 여전히 문자열로 다룬다. **변수 이름은 사람에게 의미를 알려 주고, 자료형은 Python에 가능한 연산을 알려 준다.**

값은 실제 데이터이고, 객체는 Python이 값을 메모리에서 다루는 단위다. 자료형은 그 객체가 어떤 값이며 어떤 연산을 지원하는지 결정한다. 변수는 그 객체를 가리키는 이름이다.

```text
변수 이름 port ──가리킴──> 정수 객체 443 ──자료형──> int
```

```python
port = 443

print(type(port))             # <class 'int'>
print(isinstance(port, int))  # True
print(isinstance(port, str))  # False
```

- `type(value)`는 값의 정확한 자료형을 보여 준다.
- `isinstance(value, type)`은 값이 지정한 자료형 또는 그 하위 자료형인지 확인한다.

{% hint style="info" %}
### 조금 더 알아보기

Python에서 `bool`은 `int`의 하위 자료형이므로 `isinstance(True, int)`는 `True`다. 그러나 업무 데이터에서 참·거짓과 횟수는 의미가 다르므로 `True`를 숫자 `1` 대신 사용하지 않는다.
{% endhint %}

## 3단계. 분석 질문으로 자료형 선택하기

자료형은 값의 생김새만 보고 고르지 않는다. **앞으로 그 값에 어떤 질문을 할 것인지**를 보고 고른다.

- 포트가 `1`부터 `65535` 사이인지 묻고 싶다면 `int`가 필요하다.
- 위험 점수의 평균을 계산하고 싶다면 `float`가 필요하다.
- 탐지 여부처럼 두 상태를 표현하려면 `bool`이 알맞다.
- IP·URL처럼 계산하지 않는 식별자는 숫자가 섞여 있어도 `str`이 알맞다.
- 정보가 아직 확인되지 않았다면 임의의 값 대신 `None`으로 구분한다.
- 디스크나 네트워크에서 읽은 원시 데이터를 비교하려면 `bytes`가 필요하다.

| 자료형 | 예 | 의미와 활용 |
|---|---|---|
| `int` | `443`, `3` | 포트, 횟수, PID처럼 소수점 없는 수 |
| `float` | `0.85`, `1.2` | 비율, 점수, 측정 시간처럼 소수점이 있는 수 |
| `bool` | `True`, `False` | 탐지 여부, 성공 여부처럼 두 상태 중 하나 |
| `str` | `"443"`, `"DENY"` | 사용자 입력, IP, URL, 로그 원문처럼 문자로 다룰 값 |
| `None` | `None` | 아직 없거나 확인되지 않은 값 |
| `bytes` | `b"MZ"`, `b"\x89PNG"` | 파일 헤더, 패킷처럼 바이트 단위의 원시 데이터 |

따라서 먼저 분석 질문을 정하고, 그 질문에 답할 수 있는 자료형을 선택한다.

```python
source_ip = "198.51.100.9"  # 계산 대상이 아닌 식별 문자열
destination_port = 443      # 범위 비교와 계산이 가능한 정수
risk_score = 0.85           # 소수점이 있는 점수
is_detected = True          # 탐지 여부
country = None              # 아직 확인되지 않음
file_signature = b"MZ"      # 파일의 원시 바이트
```

### 3-1. 계산하고 비교할 값 만들기 — int와 float

포트 번호, 로그인 실패 횟수, 프로세스 ID는 크기와 범위를 비교한다. 위험 점수와 측정 시간은 소수점이 필요할 수 있다. 이처럼 **계산하거나 수치 기준과 비교할 값**에는 숫자 자료형을 사용한다.

`int`는 정수, `float`는 부동소수점 수를 표현한다.

```python
failed_count = 3
risk_score = 0.85

print(type(failed_count))  # <class 'int'>
print(type(risk_score))    # <class 'float'>
```

숫자 연산의 결과도 예상해 본다.

```python
print(7 + 2)   # 9
print(7 - 2)   # 5
print(7 * 2)   # 14
print(7 / 2)   # 3.5: 나눗셈
print(7 // 2)  # 3: 몫
print(7 % 2)   # 1: 나머지
print(2 ** 3)  # 8: 거듭제곱
```

정수와 실수를 연산하면 일반적으로 결과는 `float`가 된다.

```python
print(443 + 0.5)        # 443.5
print(type(443 + 0.5))  # <class 'float'>
```

부동소수점은 일부 소수를 정확히 표현하지 못한다.

```python
print(0.1 + 0.2)  # 0.30000000000000004
```

이 결과는 Python의 계산 오류가 아니라 컴퓨터가 이진수로 소수를 표현하는 방식에서 생긴다. 정확한 금액이나 정밀한 십진 계산에는 목적에 따라 `decimal.Decimal`을 검토한다.

### 3-2. 수집 화면의 443을 그대로 믿지 않기 — 숫자 443과 문자열 "443"

명령행 인자, CSV, 로그, `input()`에서 가져온 값은 화면에 `443`으로 보여도 문자열인 경우가 많다. 사람이 보기에 같다는 이유로 자료형까지 같다고 가정하면 포트 범위 검사나 계산이 실패한다.

- `443`은 계산과 크기 비교에 사용하는 `int`다.
- `"443"`은 문자 `4`, `4`, `3`을 순서대로 모은 `str`이다.

```python
print(443 + 1)          # 444
print("443" + "1")      # 4431
print(443 == "443")     # False
```

서로 맞지 않는 자료형을 연산하면 오류가 발생한다.

```python
# print("443" + 1)
# TypeError: 문자열과 정수는 직접 더할 수 없음
```

`input()`으로 입력받은 값은 화면에 숫자로 보이더라도 항상 문자열이다.

```python
raw_port = input("포트 번호: ")

print(raw_port)
print(type(raw_port))  # <class 'str'>
```

계산이나 범위 비교가 필요하면 명시적으로 변환한다.

```python
raw_port = "443"
port = int(raw_port)

print(port + 1)     # 444
print(type(port))   # <class 'int'>
```

### 3-3. 판단 결과에 이름 붙이기 — bool

보안 자동화는 “HTTPS 포트인가?”, “탐지 이벤트인가?”, “검토가 필요한가?”처럼 예/아니오 질문을 계속 만든다. 그 판단 결과를 설명 가능한 이름에 저장하면 이후 조건문이 읽기 쉬워진다.

`bool`은 `True` 또는 `False` 두 값을 가진다. 비교식의 결과도 `bool`이다.

```python
port = 443
is_https = port == 443
is_privileged = port < 1024

print(is_https)       # True
print(is_privileged)  # True
print(type(is_https)) # <class 'bool'>
```

문자열 `"True"`와 `"False"`는 `bool`이 아니라 `str`이다.

```python
print(type(True))       # <class 'bool'>
print(type("True"))     # <class 'str'>
print(True == "True")   # False
```

`bool()`은 문자열의 내용을 해석하지 않고 **값이 비어 있는지**를 기준으로 판단한다.

```python
print(bool(""))       # False: 빈 문자열
print(bool("False"))  # True: 글자가 있는 문자열
print(bool("0"))      # True: 글자가 있는 문자열
```

따라서 사용자에게서 받은 `"False"`를 `bool("False")`로 변환하면 의도와 다른 결과가 나온다. 문자열의 내용에 따라 참·거짓을 판단하는 방법은 03-3 조건문에서 다룬다.

### 3-4. 0과 미확인을 구분하기 — None

DFIR 타임라인에서 `failed_count = 0`은 확인 결과 실패가 0회라는 뜻이다. 반면 `failed_count = None`은 아직 집계하지 못했거나 자료가 없다는 뜻이다. 둘을 같은 값으로 처리하면 “이상 없음”과 “조사하지 않음”이 섞인다.

`None`은 값이 아직 없거나 확인되지 않았음을 나타낸다. 숫자 `0`, 빈 문자열 `""`, `False`와 업무 의미가 다르다.

```python
failed_count = 0   # 실패 횟수를 확인했으며 0회
country = None     # 국가 정보를 아직 확인하지 못함
username = ""      # 사용자명 문자열이 비어 있음
is_detected = False

print(failed_count == 0)   # True
print(country is None)     # True
print(username == "")      # True
print(is_detected is False) # True
```

`None` 여부는 `== None`보다 `is None` 또는 `is not None`으로 확인한다.

### 3-5. 화면의 글자와 증거의 바이트 구분하기 — str과 bytes

분석 보고서의 `"MZ"`와 디스크에서 읽은 `b"MZ"`는 사람 눈에는 비슷하다. 그러나 전자는 문자이고 후자는 파일에 실제로 기록된 바이트다. 악성코드 분석, 파일 시그니처 확인, 패킷 처리에서는 이 경계를 지켜야 증거와 올바르게 비교할 수 있다.

`str`은 사람이 읽는 문자이고, `bytes`는 파일 헤더나 패킷처럼 바이트 단위의 원시 데이터다.

```python
text = "MZ"
raw = b"MZ"

print(type(text))  # <class 'str'>
print(type(raw))   # <class 'bytes'>
print(text == raw) # False
```

문자열을 바이트로 바꾸는 과정을 인코딩, 바이트를 문자열로 해석하는 과정을 디코딩이라고 한다.

```python
encoded = text.encode("utf-8")
decoded = raw.decode("utf-8")

print(encoded)        # b'MZ'
print(decoded)        # MZ
```

모든 바이트가 UTF-8 문자열인 것은 아니다. 잘못된 방식으로 디코딩하면 `UnicodeDecodeError`가 발생할 수 있다. 인코딩은 [04-3. 인코딩, str, bytes](../04-file-io/04-3-encoding-bytes.md)에서 자세히 다룬다.

{% hint style="success" %}
### 중간 점검 — 자료형은 분석 질문을 가능하게 한다

지금까지 만든 `port`, `risk_score`, `is_detected`, `country`, `file_signature`는 단순히 형태가 다른 값이 아니다. 각각 **범위 비교, 점수 계산, 분기 판단, 미확인 상태 보존, 원시 증거 비교**라는 서로 다른 작업을 가능하게 한다.
{% endhint %}

## 4단계. 외부 입력을 분석 값으로 바꾸기 — 명시적 형변환

방화벽 로그나 사용자 입력은 대개 문자열로 들어온다. 원본을 보존하고, 계산이나 비교가 필요한 필드만 별도 변수로 변환해야 한다.

형변환은 값의 자료형을 의도적으로 바꾸는 작업이다.

| 코드 | 결과 | 주의할 점 |
|---|---:|---|
| `int("443")` | `443` | 정수 모양 문자열만 변환 가능 |
| `int(443.9)` | `443` | 반올림이 아니라 소수 부분 제거 |
| `float("443")` | `443.0` | 정수 모양 문자열도 실수로 변환 가능 |
| `float("0.85")` | `0.85` | 소수점 문자열 변환 |
| `str(443)` | `"443"` | 출력이나 문자열 결합에 활용 |
| `bool(0)` | `False` | 0은 거짓으로 평가 |
| `bool("False")` | `True` | 비어 있지 않은 문자열은 참 |

직접 실행하고 자료형까지 확인한다.

```python
port = int("443")
score = float("0.85")
port_text = str(443)

print(port, type(port))           # 443 <class 'int'>
print(score, type(score))         # 0.85 <class 'float'>
print(port_text, type(port_text)) # 443 <class 'str'>
```

다음 두 변환은 결과가 특히 자주 혼동된다.

```python
print(int(443.9))
# 443: 소수 부분을 버림

# print(int("443.0"))
# ValueError: "443.0"은 정수 모양 문자열이 아님
```

문자열 `"443.0"`을 실수로 변환한 뒤 정수로 바꾸는 코드는 가능하지만, 소수 부분을 버려도 되는 데이터인지 먼저 판단해야 한다.

```python
value = int(float("443.0"))
print(value)  # 443
```

## 5단계. 변환 성공 뒤에도 한 번 더 묻기 — 형식 검증과 범위 검증

`int("70000")`은 오류 없이 실행된다. 그렇다고 `70000`이 올바른 포트가 되는 것은 아니다. 도구가 값을 읽을 수 있다는 사실과 보안 업무에서 그 값을 신뢰할 수 있다는 사실은 다르다.

입력값 검증에는 서로 다른 두 질문이 있다.

1. **형식 검증:** 정수로 변환할 수 있는가?
2. **업무 범위 검증:** 변환된 정수가 허용 범위에 있는가?

```python
raw_port = "443"
port = int(raw_port)
is_valid_range = 1 <= port <= 65535

print(port)            # 443
print(is_valid_range)  # True
```

`"443a"`는 정수로 변환할 수 없으므로 `ValueError`가 발생한다. `70000`은 정수로 변환할 수 있지만 유효한 포트 범위 밖이다.

| 입력 | 정수 변환 | 1~65535 범위 | 판단 |
|---|---:|---:|---|
| `"443"` | 성공 | 포함 | 유효 |
| `"443a"` | 실패 | 확인 불가 | 형식 오류 |
| `"0"` | 성공 | 벗어남 | 범위 오류 |
| `"70000"` | 성공 | 벗어남 | 범위 오류 |

{% hint style="warning" %}
### 이후 절 문법 미리보기

아래 코드는 형식 오류와 범위 오류를 모두 처리한 완성 형태다. `if`는 03-3, `try`와 `except`는 03-6에서 자세히 배운다. 지금은 모든 문법을 외우지 말고 **변환과 범위 확인이 별도 단계**라는 흐름만 관찰한다.

```python
raw_port = "443"

try:
    port = int(raw_port)
except ValueError:
    print("숫자 형식이 아닙니다")
else:
    if 1 <= port <= 65535:
        print("유효한 포트:", port)
    else:
        print("포트 범위를 벗어났습니다")
```
{% endhint %}

## 분석 기록을 보존하는 두 가지 습관

핵심 변환은 끝났지만, 실제 분석에서는 원본과 해석 과정을 다시 확인할 수 있어야 한다. 여러 필드의 대응 관계를 분명히 하고 원본과 정제 값을 구분하는 두 가지 습관을 살펴본다.

### 여러 필드에 이름 붙이기 — 언패킹

로그 한 줄을 필드로 나눈 뒤에는 여러 이름에 값을 한 번에 대입할 수 있다. 지금은 나뉜 값이 준비되어 있다고 가정하고 대입의 모양만 살펴본다. 실제 문자열 분리는 03-2에서 다룬다.

```python
raw_action, raw_ip, raw_port = "DENY", "198.51.100.9", "443"
print(raw_action, raw_ip, raw_port)
```

값의 개수와 변수의 개수가 다르면 `ValueError`가 발생한다.

```python
# action, ip = "DENY", "198.51.100.9", 443
# ValueError: too many values to unpack
```

중요한 것은 한 줄로 짧게 쓰는 것이 아니라, 필드 수와 의미가 이름에 정확히 대응하는지 확인하는 것이다.

### 원본과 정제 값을 따로 두는 이유 — 불변 객체와 재대입

분석 과정에서는 `raw_port`와 `port`를 구분하는 편이 좋다. 무엇을 수집했고 어떻게 해석했는지 비교할 수 있어야 하기 때문이다.

`int`, `float`, `bool`, `str`, `tuple`은 생성된 뒤 내부 값을 바꿀 수 없는 불변 객체다. 변수에 새 값을 대입하는 것은 기존 객체를 수정하는 것이 아니라 이름이 다른 객체를 가리키게 하는 것이다.

```python
a = 443
b = a
a = 8443

print(a)  # 8443
print(b)  # 443
```

`a`에 새 값을 대입해도 `443` 객체나 `b`가 바뀐 것은 아니다. 변경 가능한 `list`, `dict`, `set`과 복사 문제는 03-2에서 다룬다.

실무 코드에서는 다음처럼 원본과 정제 값을 이름으로 명확히 구분한다.

```python
raw_port = "443"
port = int(raw_port)

print(raw_port, type(raw_port))  # 수집 증거: 443 <class 'str'>
print(port, type(port))          # 분석 값: 443 <class 'int'>
```

## 분석을 틀리게 만드는 다섯 가지 함정

이제 처음의 이벤트로 돌아가 보자. 다음 코드는 문법 실수 모음이 아니라, 보안 자동화의 결과를 바꿀 수 있는 대표적인 데이터 해석 오류다.

### `=`와 `==` 혼동

```python
port = 443        # 대입
print(port == 443) # 비교
```

### 숫자와 문자열을 직접 연산

```python
raw_count = "3"

# print(raw_count + 1)  # TypeError
print(int(raw_count) + 1)  # 4
```

### 문자열 내용을 bool로 잘못 변환

```python
raw_detected = "False"

print(bool(raw_detected))  # True
```

### 형변환 성공과 유효성 검사를 동일하게 생각

```python
port = int("70000")
print(port)                    # 변환은 성공
print(1 <= port <= 65535)      # False: 포트로는 유효하지 않음
```

### None과 0을 같은 의미로 처리

```python
success_count = 0  # 집계 결과가 0
error_count = None # 아직 집계하지 않음
```

## 이 기초가 실제 보안 자동화로 이어지는 곳

이번 절에서는 이벤트 한 건의 값을 정확히 표현하는 데 집중한다. 이후 조건문과 반복문을 배우면 같은 자료형이 다음과 같은 자동화의 기반이 된다.

| 활용 장면 | 이번 절에서 준비하는 값 | 이후 만들 수 있는 자동화 |
|---|---|---|
| 포트 스캐닝 | 대상 포트를 `str`에서 `int`로 변환하고 범위를 확인하며, 응답 여부를 `bool`로 표현 | `for`로 여러 포트를 순회하고 열린 포트만 기록 |
| 브루트포스 탐지 | 로그인 실패 횟수를 `int`, 계정을 `str`, 임계값 충족 여부를 `bool`로 표현 | 여러 인증 로그를 반복 처리해 임계값을 넘긴 계정을 분류 |
| DFIR 파일 분석 | 파일 헤더를 `bytes`, PID와 크기를 `int`, 미확인 메타데이터를 `None`으로 표현 | 여러 파일의 매직 바이트를 검사하고 의심 파일 목록 작성 |
| 위협 인텔리전스 처리 | IP·해시를 `str`, 위험 점수를 `float`, 조회 실패를 `None`으로 구분 | API 응답 여러 건을 정규화하고 우선 조사 대상을 선별 |

예를 들어 포트 스캐너의 반복문은 아직 배우지 않았지만, 그 반복문이 순회할 값은 먼저 올바른 정수여야 한다.

```python
raw_start_port = "20"
raw_end_port = "25"

start_port = int(raw_start_port)
end_port = int(raw_end_port)

print(start_port, end_port)  # 다음 단계에서 20~25를 반복할 수 있음
```

자료형이 틀리면 반복문을 잘 작성해도 잘못된 대상을 검사하거나 비교 단계에서 중단된다. 그래서 **자동화의 출발은 반복 자체가 아니라, 반복할 데이터의 의미를 정확히 만드는 것**이다.

## 임무 실습 — 이벤트 한 건을 분석 가능한 상태로 만들기

앞에서 살펴본 개념을 처음의 이벤트에 다시 적용한다. 연습 1~3은 필요한 도구를 점검하고, 연습 4에서 하나의 사건 프로필로 결합한다.

### 연습 1. 출력 결과 예측

실행하기 전에 결과와 자료형을 적는다.

```python
print(20 + 3)
print("20" + "3")
print(20 == "20")
print(int("20") + 3)
print(bool(""))
print(bool("False"))
print(None == 0)
```

### 연습 2. 오류 원인 설명과 수정

각 코드가 실행되지 않거나 의도와 다른 결과를 내는 이유를 설명하고 수정한다.

```python
# 문제 A
port = "443"
# print(port + 1)

# 문제 B
raw_score = "0.85"
# score = int(raw_score)

# 문제 C
raw_detected = "False"
detected = bool(raw_detected)

# 문제 D
port = int("70000")
print("변환 성공:", port)
```

수정 목표는 다음과 같다.

- 문제 A: `444`를 출력한다.
- 문제 B: 실수 `0.85`로 변환한다.
- 문제 C: 문자열의 내용이 `"True"`일 때만 `True`가 되게 한다. 조건식 문법은 예시를 참고한다.
- 문제 D: 정수 변환 성공과 포트 범위 유효성을 별도로 출력한다.

### 연습 3. 자료형 선택

다음 값에 적합한 자료형과 이유를 적는다.

| 데이터 | 예시 값 | 선택할 자료형 |
|---|---|---|
| 접속 원본 IP | `198.51.100.9` | ? |
| 목적지 포트 | `443` | ? |
| 위험 점수 | `0.85` | ? |
| 탐지 여부 | 참 | ? |
| 아직 확인되지 않은 국가 | 값 없음 | ? |
| PE 파일 시작 바이트 | `MZ` | ? |

### 연습 4. 오늘의 임무 완수 — 이벤트 프로필 만들기

다음 원본 데이터는 방화벽과 파일 수집 시스템에서 전달되었다고 가정한다. 원본 변수는 수집 당시의 상태를 보여 주므로 덮어쓰지 않는다.

```python
raw_ip = "198.51.100.9"
raw_port = "443"
raw_score = "0.85"
raw_action = "DENY"
raw_country = ""
file_signature = b"MZ"
```

이제 “값의 모양”을 “분석에 필요한 의미”로 바꾼다.

1. `raw_port`를 정수로 변환해 `port`에 저장한다.
2. `raw_score`를 실수로 변환해 `risk_score`에 저장한다.
3. `raw_action`이 `"DENY"`와 같은지 비교해 `is_detected`에 저장한다.
4. 국가 문자열이 비어 있으므로 `country`에 `None`을 저장한다.
5. `port`가 유효 범위인지 비교해 `is_valid_port`에 저장한다.
6. 모든 값과 자료형을 출력한다.
7. 아래 자기점검 코드를 실행한다.

```python
assert raw_ip == "198.51.100.9"
assert port == 443
assert type(port) is int
assert risk_score == 0.85
assert type(risk_score) is float
assert is_detected is True
assert country is None
assert is_valid_port is True
assert file_signature == b"MZ"

print("모든 자기점검을 통과했습니다.")
```

예상 출력의 핵심은 다음과 같다. `print()` 형식에 따라 공백이나 괄호 표현은 달라질 수 있다.

```text
198.51.100.9 <class 'str'>
443 <class 'int'>
0.85 <class 'float'>
True <class 'bool'>
None
True <class 'bool'>
b'MZ' <class 'bytes'>
모든 자기점검을 통과했습니다.
```

### 연습 5. 다음 장과 연결하기

이번 절에서는 올바른 값을 준비했다. 03-3 조건문, 03-4 반복문, 03-6 예외 처리를 학습한 뒤 같은 사건을 다음과 같이 확장한다.

- 포트 입력이 `"443a"`일 때 프로그램이 중단되지 않게 한다.
- 포트가 `0` 또는 `70000`일 때 범위 오류 메시지를 출력한다.
- `raw_action`이 `"ALLOW"` 또는 `"DENY"`인지 확인한다.
- 정상 입력, 형식 오류, 경계값 `1`과 `65535`, 범위 밖 값을 모두 시험한다.
- 여러 이벤트를 반복 처리해 `DENY` 건수와 의심 IP별 실패 횟수를 집계한다.
- DFIR 관점에서는 여러 파일의 시작 바이트를 확인해 `b"MZ"`인 파일만 별도 목록에 모은다.

## 정답과 해설

<details>
<summary>학습 전 확인과 연습 1 정답</summary>

학습 전 확인:

```text
30
1020
False
True
```

`"10" + "20"`은 숫자 덧셈이 아니라 문자열 결합이다. `"False"`는 비어 있지 않은 문자열이므로 `bool("False")`는 `True`다.

연습 1:

```text
23
203
False
23
False
True
False
```

</details>

<details>
<summary>연습 2 수정 예시</summary>

```python
# 문제 A
port = "443"
print(int(port) + 1)

# 문제 B
raw_score = "0.85"
score = float(raw_score)
print(score)

# 문제 C
raw_detected = "False"
detected = raw_detected == "True"
print(detected)

# 문제 D
port = int("70000")
is_valid_port = 1 <= port <= 65535
print("변환 성공:", port)
print("유효한 포트:", is_valid_port)
```

</details>

<details>
<summary>연습 3과 미니 실습 예시 답안</summary>

자료형 선택:

- IP: `str` — 숫자 계산 대상이 아니라 점을 포함한 식별 문자열이다.
- 포트: `int` — 허용 범위 비교가 필요하다.
- 위험 점수: `float` — 소수점이 있는 수치다.
- 탐지 여부: `bool` — 참과 거짓 두 상태를 표현한다.
- 미확인 국가: `None` — 값이 아직 확인되지 않았다.
- 파일 시작 바이트: `bytes` — 파일의 원시 바이트다.

미니 실습:

```python
raw_ip = "198.51.100.9"
raw_port = "443"
raw_score = "0.85"
raw_action = "DENY"
raw_country = ""
file_signature = b"MZ"

port = int(raw_port)
risk_score = float(raw_score)
is_detected = raw_action == "DENY"
country = None
is_valid_port = 1 <= port <= 65535

print(raw_ip, type(raw_ip))
print(port, type(port))
print(risk_score, type(risk_score))
print(is_detected, type(is_detected))
print(country)
print(is_valid_port, type(is_valid_port))
print(file_signature, type(file_signature))
```

</details>

## 임무 완료 기준

- [ ] `=`와 `==`의 차이를 예제로 설명할 수 있다.
- [ ] 변수·값·객체·자료형의 관계를 설명할 수 있다.
- [ ] `int`, `float`, `bool`, `str`, `None`, `bytes`에 맞는 사용 사례를 선택할 수 있다.
- [ ] 숫자와 숫자 모양 문자열의 연산 결과를 예측할 수 있다.
- [ ] `type()`과 `isinstance()`로 자료형을 확인할 수 있다.
- [ ] `int()`, `float()`, `str()`을 이용해 값을 명시적으로 변환할 수 있다.
- [ ] `bool("False")`가 `True`인 이유를 설명할 수 있다.
- [ ] 형변환 실패와 업무 범위 오류를 구분할 수 있다.
- [ ] 미니 실습의 모든 `assert`를 통과했다.

## 임무 복기

처음에 본 방화벽 이벤트와 파일 시작 바이트는 이제 단순한 글자와 바이트 나열이 아니다.

- 변수는 각 사실에 이름을 붙이고, `=`는 그 이름을 값에 연결한다.
- 자료형은 값의 의미와 앞으로 가능한 연산을 결정한다.
- 외부에서 들어온 `"443"`은 원본 문자열로 보존하고, 분석에는 정수 `443`을 사용한다.
- `None`, `0`, 빈 문자열, `False`를 구분해야 조사하지 않은 상태를 정상 상태로 오인하지 않는다.
- 파일과 패킷의 원시 증거는 `str`이 아니라 `bytes`로 다룬다.
- 형변환 성공은 형식 확인일 뿐이다. 업무 범위 검증까지 통과해야 신뢰할 수 있다.

이제 이벤트 한 건의 각 값을 정확히 표현할 수 있다. 다음 절에서는 이 값들을 문자열에서 분리하고, 이벤트 한 건을 딕셔너리로, 여러 이벤트를 리스트로 구조화한다. 그다음 조건문으로 판단하고 반복문으로 같은 작업을 여러 대상에 확장한다.

---

다음 절: [03-2. 문자열과 자료구조](03-2-strings-collections.md)
