# 03-1. 변수와 자료형

{% hint style="info" %}
### 🧭 이 절의 핵심 질문

- 변수는 값을 저장하는 상자인가, 아니면 이름인가?
- 왜 같은 숫자처럼 보여도 문자열과 정수는 다르게 다뤄야 하는가?
- 입력 데이터의 자료형을 확인하는 것이 보안 자동화에서 왜 중요한가?
{% endhint %}

## 변수란 무엇인가

변수는 데이터를 담아 두는 상자라기보다 **값을 가리키는 이름**이다. 대입 연산자 `=`는 “같다”가 아니라 오른쪽의 값을 왼쪽 이름에 연결한다는 뜻이다.

```python
port = 443
another_port = port
port = 8443

print(another_port)  # 443: 이름을 복사한 것이 아니라 당시 값을 다시 가리킴
print(port)          # 8443
```

변수 이름을 사용하면 복잡한 데이터를 기억할 필요 없이 의미를 부여할 수 있다. `443`보다 `https_port`가 코드의 의도를 잘 설명한다. 이름은 `snake_case`로 쓰고, 무엇을 담는지 드러내도록 작성한다.

## 값과 자료형은 왜 중요한가

자료형(type)은 값의 종류뿐 아니라 **그 값에 적용할 수 있는 연산과 해석 방법**을 결정한다.

```python
port_number = 443       # int: 계산·비교 가능
port_text = "443"       # str: 문자 조합·검색에 사용

print(port_number + 1)  # 444
print(port_text + "1")  # "4431"
```

외부 입력은 대부분 문자열로 들어온다. 따라서 로그의 횟수나 포트처럼 계산해야 하는 값은 숫자로 변환하고, 변환 실패도 처리해야 한다.

## `443`과 `"443"`은 왜 다른가

겉으로는 같은 숫자를 표현하는 것처럼 보이지만 자료형이 다르다.

- `443`: 정수(`int`). 계산과 크기 비교를 위한 값이다.
- `"443"`: 문자열(`str`). 문자 `4`, `4`, `3`이 이어진 텍스트다.

따라서 같은 연산을 해도 결과가 달라진다.

```python
port_number = 443
port_text = "443"

print(port_number + 1)        # 444
print(port_text + "1")         # 4431
print(port_number == port_text) # False

# 로그·input()에서 받은 문자열을 계산에 사용하려면 변환한다.
port = int(port_text)
print(port + 1)                # 444
```

문자열 `"443"`에 숫자 `1`을 바로 더하면 `TypeError`가 발생한다. Python은 자료형이 다른 값을 자동으로 적당히 바꾸지 않기 때문에, **데이터의 의미에 맞는 자료형을 선택하거나 명시적으로 변환해야 한다.**

## 객체와 가변성의 기초

Python에서 변수는 객체 자체가 아니라 객체를 참조하는 이름이다. `int`, `str`, `tuple`처럼 변경할 수 없는(immutable) 객체와 `list`, `dict`, `set`처럼 내부 내용을 변경할 수 있는(mutable) 객체를 구분해야 한다. 이 차이는 03-2에서 다루는 자료구조를 함수에 전달할 때 특히 중요하다.

{% hint style="info" %}
### 🧭 학습 목표

- 변수와 객체의 관계를 이해한다.
- `int`, `float`, `bool`, `str`, `None`, `bytes`를 구분한다.
- 보안 데이터의 값에 적절한 자료형을 선택한다.
{% endhint %}

## 변수와 값

Python 변수는 값을 담는 상자라기보다 객체를 가리키는 이름이다.

```python
port = 443
service = "https"
is_open = True

print(type(port))
print(type(service))
print(type(is_open))
```

## 기본 자료형

| 자료형 | 예시 | 보안 실무 활용 |
|---|---|---|
| `int` | `443` | 포트, 횟수, PID |
| `float` | `0.95` | 점수, 비율, 시간 |
| `bool` | `True` | 탐지 여부, 상태 |
| `str` | `"/admin"` | 로그, URL, 명령어 |
| `None` | `None` | 값 없음, 미확인 |
| `bytes` | `b"MZ"` | 파일 헤더, 패킷, 인코딩 데이터 |

## 연산자와 형변환

```python
failed = "3"
threshold = 5

failed_count = int(failed)
print(failed_count + 1)
print(failed_count >= threshold)

# input()은 항상 str을 반환한다.
value = input("포트 번호: ")
port = int(value)
```

외부 입력은 항상 신뢰하지 않는다. 변환 전 형식과 범위를 검증한다.

{% hint style="success" %}
## 🧪 실습

1. 문자열로 입력된 포트 번호를 정수로 변환한다.
2. `None`과 숫자 `0`을 구분한다.
3. IP, 포트, 탐지 여부를 적절한 자료형으로 저장한다.
{% endhint %}
