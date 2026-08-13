# 03-7. 예외, assert, 모듈과 테스트

## 학습 목표

- 예상 가능한 오류를 예외로 처리한다.
- 오류 행의 위치와 원인을 보존한다.
- `assert`와 테스트 프레임워크를 구분한다.
- 기능을 모듈로 나눈다.

## 예외 처리

```python
def parse_lines(text):
    records, errors = [], []

    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(parse_line(line))
        except ValueError as exc:
            errors.append({
                "line": number,
                "raw": line,
                "error": str(exc),
            })

    return records, errors
```

`except Exception`으로 모든 오류를 숨기지 않는다. 예상 가능한 오류와 프로그래밍 오류를 구분한다.

## raise, else, finally

```python
try:
    value = int("443")
except ValueError:
    print("숫자 변환 실패")
else:
    print("변환 성공:", value)
finally:
    print("항상 실행")
```

## assert와 pytest

`assert`는 학습 중 불변식 확인에 사용한다.

```python
assert denied["198.51.100.9"] == 2
```

사용자 입력 검증이나 권한 판정의 대체 수단으로 사용하지 않는다. 실제 반복 테스트는 pytest로 작성하며 정상·오류·경계값을 모두 포함한다.

## 모듈

```text
python_basic/
├── parser.py
├── validator.py
├── report.py
└── main.py
```

실행 진입점은 다음 구조를 사용한다.

```python
def main():
    ...

if __name__ == "__main__":
    main()
```

## 실습

- 잘못된 로그 한 줄을 오류 목록에 보존한다.
- `pytest`로 정상·오류·경계값을 테스트한다.
- 파서와 보고서 생성기를 별도 모듈로 분리한다.
