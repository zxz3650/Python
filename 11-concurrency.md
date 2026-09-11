# 11. 동시성과 비동기 처리

{% hint style="info" %}
### 실습 자료 준비

[11장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-11.zip)로 이 장의 노트북과 필요한 코드·입력 데이터를 준비한다. 구성과 개별 파일은 [이 장의 노트북 목록](PRACTICE.md#chapter-11)에서 확인한다. 자료가 수정되면 이 장의 ZIP만 새로 받는다.

[첫 노트북 보기](notebooks/11-concurrency.ipynb) · [첫 노트북 원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/11-concurrency.ipynb)

11장 ZIP을 푼 폴더에서 `python -m jupyterlab`을 실행하고 `notebooks/11-concurrency.ipynb`를 연다. 자세한 저장·커널 확인 방법은 [자료 준비·실행 안내](PRACTICE.md#download)를 따른다.
{% endhint %}

여러 입출력 작업을 효율적으로 처리하기 위한 동시성 개념을 학습합니다. 빠른 실행보다 요청 제한·취소·오류 수집을 포함한 안전한 제어에 집중합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 동시성과 병렬성의 차이를 설명합니다.
- 스레드·프로세스·asyncio의 선택 기준을 구분합니다.
- 비동기 작업에 타임아웃과 제한을 적용합니다.
- 여러 작업의 오류를 수집합니다.
{% endhint %}

## 선행 지식

10장의 프로그램 구조와 테스트

## 학습 순서

1. 11-1 동시성과 병렬성
2. 11-2 스레드
3. 11-3 프로세스
4. 11-4 `asyncio`
5. 11-5 비동기 HTTP
6. 11-6 제한·취소·오류 처리

## 학습 방법

1. 개념과 용어를 먼저 확인합니다.
2. 최소 예제의 결과를 예측합니다.
3. 정상·오류·경계 입력을 바꾸어 실행합니다.
4. 기능을 작은 함수로 나누어 작성합니다.
5. 종합 실습으로 각 절을 연결합니다.

## Jupyter 예제

[`notebooks/11-concurrency.ipynb`](notebooks/11-concurrency.ipynb)에서 제한된 스레드와 비동기 작업을 실행하고 일부 실패가 다른 결과를 숨기지 않는지 확인합니다.

## 종합 실습

여러 학습용 URL의 상태를 제한된 동시성으로 확인하고 처리 시간과 오류를 보고합니다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 작업 특성에 맞는 실행 방식을 선택합니다.
- [ ] 동시 작업 수와 요청 속도를 제한합니다.
- [ ] 일부 작업 실패가 전체 결과를 숨기지 않습니다.
{% endhint %}

---

다음 장: [12. Python 활용 종합 프로젝트](12-capstone.md)
