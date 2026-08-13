# Python Basic — 보안 실무자를 위한 Python 기초

Python을 처음 배우는 보안 실무자가 코드 실행과 로그 분석을 통해 기초 문법을 익히는 과정입니다.

## 학습 순서

1. 자료형·연산자·형변환
2. 문자열·리스트·튜플·셋·딕셔너리
3. 조건문·반복문·`enumerate`·컴프리헨션
4. 함수·스코프·모듈
5. 파일·`pathlib`·JSON·CSV
6. 예외 처리·`str`과 `bytes`·`assert`
7. 인증 로그 미니 프로젝트

## 실행

```bash
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
python -m pip install -r requirements.txt
python -m pytest
```

주피터를 사용하려면:

```bash
python -m pip install jupyter
jupyter lab
```

실습은 `notebooks/03_python_basic.ipynb`에서 시작합니다. 모든 데이터는 합성 데이터이며, 실제 로그는 소유권 또는 명시적 허가가 있을 때만 사용합니다.

