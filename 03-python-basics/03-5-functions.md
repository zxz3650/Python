# 03-5. 함수와 스코프

## 학습 목표

- 함수로 책임을 분리한다.
- 인자와 반환값을 사용한다.
- 지역 변수와 전역 변수의 차이를 이해한다.

```python
def parse_line(line):
    parts = line.split()
    if len(parts) != 4:
        raise ValueError("필드 수가 4개가 아닙니다")
    timestamp, action, ip, path = parts
    return {
        "timestamp": timestamp,
        "action": action,
        "ip": ip,
        "path": path,
    }
```

보안 분석기는 보통 다음처럼 분리한다.

```python
def parse_line(line):
    ...

def validate_record(record):
    ...

def summarize(records):
    ...
```

함수는 한 가지 책임을 가질수록 테스트와 재사용이 쉽다.

## 스코프

```python
threshold = 3

def is_suspicious(count):
    # threshold는 바깥 스코프에서 읽을 수 있다.
    return count >= threshold
```

전역 변수를 함수 안에서 변경하기보다 인자로 전달하고 반환값으로 결과를 받는다.

## 실습

- `parse_line()`, `validate_record()`, `summarize()`를 구현한다.
- 각 함수가 하나의 책임만 갖는지 점검한다.
- 정상·오류·경계값을 함수별로 테스트한다.
