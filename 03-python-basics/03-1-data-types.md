# 03-1. 변수와 자료형

## 학습 목표

- 변수와 객체의 관계를 이해한다.
- `int`, `float`, `bool`, `str`, `None`, `bytes`를 구분한다.
- 보안 데이터의 값에 적절한 자료형을 선택한다.

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

## 실습

1. 문자열로 입력된 포트 번호를 정수로 변환한다.
2. `None`과 숫자 `0`을 구분한다.
3. IP, 포트, 탐지 여부를 적절한 자료형으로 저장한다.
