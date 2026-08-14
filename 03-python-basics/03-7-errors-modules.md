# 03-7. 모듈과 패키지

모듈과 패키지는 프로그램을 역할별 파일로 나누는 방법입니다. 입력, 처리, 출력 기능을 분리하면 코드의 재사용과 테스트가 쉬워집니다.

{% hint style="info" %}
## 🧭 학습 목표

- 모듈과 패키지의 차이를 설명합니다.
- 표준·외부·사용자 모듈을 가져옵니다.
- 실행 진입점과 import 시 실행을 구분합니다.
- 가상환경과 의존성 파일의 역할을 이해합니다.
{% endhint %}

## 선행 지식

함수와 예외 처리를 이해해야 합니다.

## 1. import

```python
import math
from pathlib import Path

print(math.sqrt(16))
print(Path.cwd())
```

표준 라이브러리는 Python에 포함되고, 외부 패키지는 `pip`로 설치합니다.

## 2. 사용자 모듈

```text
project/
├── main.py
└── calculator.py
```

```python
# calculator.py
def add(a, b):
    return a + b
```

```python
# main.py
from calculator import add

print(add(2, 3))
```

## 3. 패키지 구조

```text
project/
├── app/
│   ├── __init__.py
│   ├── parser.py
│   └── report.py
└── main.py
```

모듈은 하나의 Python 파일이고, 패키지는 관련 모듈을 묶은 디렉터리입니다.

## 4. 실행 진입점

```python
def main():
    print("프로그램 시작")

if __name__ == "__main__":
    main()
```

이 구조는 다른 파일에서 import할 때 프로그램이 자동 실행되는 것을 막습니다.

## 5. 의존성

```bash
python -m pip freeze > requirements.txt
python -m pip install -r requirements.txt
```

프로젝트별 가상환경과 의존성 목록으로 같은 실행환경을 재현합니다.

{% hint style="success" %}
## 🧪 종합 실습

계산 기능을 `calculator.py`, 입력과 출력을 `main.py`로 분리하고 직접 실행과 import 결과를 비교합니다.
{% endhint %}

## 완료 기준

- [ ] 기능을 두 개 이상의 모듈로 분리할 수 있습니다.
- [ ] 표준 라이브러리와 외부 패키지를 구분할 수 있습니다.
- [ ] 실행 진입점의 목적을 설명할 수 있습니다.

---

다음 절: [03-8. 클래스 기초](03-8-log-project.md)
