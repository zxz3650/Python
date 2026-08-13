# 🐍 Python Basic
## 보안 실무자를 위한 Python 기초 과정

Python을 처음 배우는 보안 실무자가 **소개 → 설치 → 문법 기초 → 실습** 순서로 학습할 수 있는 GitBook 교재입니다.

### 학습 순서

1. [파이썬 소개 — 보안 실무자를 위한 언어 선택](01-python-intro.md)
2. [파이썬 설치 — 기본 설치 vs 아나콘다](02-python-setup.md)
3. [Python 문법 기초교안](03-python-basics.md)
4. [주피터 실습](notebooks/03_python_basic.ipynb)

### 학습 규칙

- 각 챕터의 개념을 읽은 뒤 코드 블록을 직접 실행합니다.
- 실습 데이터는 합성 데이터 또는 명시적으로 허가된 데이터만 사용합니다.
- 외부 시스템에 대한 스캔·요청·분석은 소유권 또는 서면 허가가 있는 환경에서만 수행합니다.

### 실행 환경

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
```
