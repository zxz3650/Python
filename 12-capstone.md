# 12. Python 활용 종합 프로젝트

{% hint style="info" %}
### 실습 자료 준비

[12장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-12.zip)로 이 장의 노트북과 필요한 코드·입력 데이터를 준비한다. 구성과 개별 파일은 [이 장의 노트북 목록](PRACTICE.md#chapter-12)에서 확인한다. 자료가 수정되면 이 장의 ZIP만 새로 받는다.

[첫 노트북 보기](notebooks/12-capstone.ipynb) · [첫 노트북 원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/12-capstone.ipynb)

12장 ZIP을 푼 폴더에서 `python -m jupyterlab`을 실행하고 `notebooks/12-capstone.ipynb`를 연다. 자세한 저장·커널 확인 방법은 [자료 준비·실행 안내](PRACTICE.md#download)를 따른다.
{% endhint %}

기초과정에서 학습한 문법, 파일, 파싱, 시스템, 네트워크, HTTP, 테스트와 구조화를 하나의 일반 자동화 프로그램으로 통합합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 요구사항을 기능과 테스트로 분해합니다.
- 파일 또는 API 데이터를 수집합니다.
- 데이터를 검증·정규화·저장합니다.
- CLI·로그·테스트·문서를 완성합니다.
{% endhint %}

## 선행 지식

01~11장 전체

## 학습 순서

1. 12-1 요구사항과 범위
2. 12-2 데이터 수집
3. 12-3 검증과 정규화
4. 12-4 결과 저장
5. 12-5 CLI와 로깅
6. 12-6 테스트와 문서화

## 학습 방법

1. 개념과 용어를 먼저 확인합니다.
2. 최소 예제의 결과를 예측합니다.
3. 정상·오류·경계 입력을 바꾸어 실행합니다.
4. 기능을 작은 함수로 나누어 작성합니다.
5. 종합 실습으로 각 절을 연결합니다.

## Jupyter 예제

[`notebooks/12-capstone.ipynb`](notebooks/12-capstone.ipynb)에서 임시 실습 파일의 수집·검증·해시·JSON 저장을 하나의 재현 가능한 파이프라인으로 연결합니다.

## 종합 실습

공개 API 데이터 수집기, 파일 메타데이터 도구, 서버 상태 확인기 중 하나를 선택해 완성합니다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 허가된 데이터와 대상만 사용합니다.
- [ ] 정상·오류·경계값 테스트가 통과합니다.
- [ ] 설치·실행·출력 형식이 문서화되어 있습니다.
- [ ] 보안 심화과정에서 재사용할 수 있는 구조입니다.
{% endhint %}

---

다음 장: 취약점 진단 또는 CSIRT 심화과정
