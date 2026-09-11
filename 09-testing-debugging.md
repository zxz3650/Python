# 09. 테스트와 디버깅

{% hint style="info" %}
### 실습 자료 준비

[09장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-09.zip)로 이 장의 노트북과 필요한 코드·입력 데이터를 준비한다. 구성과 개별 파일은 [이 장의 노트북 목록](PRACTICE.md#chapter-09)에서 확인한다. 자료가 수정되면 이 장의 ZIP만 새로 받는다.

[첫 노트북 보기](notebooks/09-testing-debugging.ipynb) · [첫 노트북 원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/09-testing-debugging.ipynb)

09장 ZIP을 푼 폴더에서 `python -m jupyterlab`을 실행하고 `notebooks/09-testing-debugging.ipynb`를 연다. 자세한 저장·커널 확인 방법은 [자료 준비·실행 안내](PRACTICE.md#download)를 따른다.
{% endhint %}

프로그램이 정상 상황뿐 아니라 오류와 경계 상황에서도 의도대로 동작하는지 검증합니다. 재현 가능한 테스트와 체계적인 디버깅 방법을 학습합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 정상·오류·경계값 테스트를 구분합니다.
- pytest 테스트를 작성합니다.
- 예외와 외부 의존성을 검증합니다.
- 디버거와 로그로 원인을 추적합니다.
{% endhint %}

## 선행 지식

08장까지의 입출력·네트워크·HTTP·자동화

## 학습 순서

1. 09-1 테스트 설계
2. 09-2 pytest 기초
3. 09-3 `parametrize`와 fixture
4. 09-4 예외 테스트
5. 09-5 mock 기초
6. 09-6 디버깅과 로그

## 학습 방법

1. 개념과 용어를 먼저 확인합니다.
2. 최소 예제의 결과를 예측합니다.
3. 정상·오류·경계 입력을 바꾸어 실행합니다.
4. 기능을 작은 함수로 나누어 작성합니다.
5. 종합 실습으로 각 절을 연결합니다.

## Jupyter 예제

[`notebooks/09-testing-debugging.ipynb`](notebooks/09-testing-debugging.ipynb)에서 정상·오류·경계값을 나눈 테스트를 실행하고, 테스트 수·실패·오류를 구분합니다.

## 종합 실습

07장의 로컬 HTTP 보안 점검기를 네트워크 없이 반복 검증할 수 있도록 테스트와 mock을 작성합니다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 테스트가 외부 상태에 불필요하게 의존하지 않습니다.
- [ ] 실패한 테스트만으로 원인을 추적할 수 있습니다.
- [ ] 정상·오류·경계값을 모두 포함합니다.
{% endhint %}

---

다음 장: [10. 프로그램 구조화](10-program-architecture.md)
