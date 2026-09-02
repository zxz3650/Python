# 13-7. 프로젝트 B - Excel 요약 보고서

CSV 매출 데이터를 검증하고 Excel 보고서를 생성합니다. 잘못된 행을 버리지 않고 원본 행 번호·이유·원본 값을 `검증 오류` 시트에 보존합니다.

{% hint style="info" %}
## 🧭 프로젝트 목표

- CSV 헤더와 행 자료형을 검증합니다.
- 검증 성공·실패 행을 분리하고 건수를 대조합니다.
- Excel에 요약·상세·오류 시트와 차트를 생성합니다.
- 출력을 다시 열어 시트·행 수·수식을 재검증합니다.
{% endhint %}

## 1. 실습 파일

- [`spreadsheet_report.py`](https://github.com/zxz3650/Python/blob/master/examples/13-python-automate/spreadsheet_report.py)
- [`sample_sales.csv`](https://github.com/zxz3650/Python/blob/master/examples/13-python-automate/sample_sales.csv)
- [`sample_sales_with_errors.csv`](https://github.com/zxz3650/Python/blob/master/examples/13-python-automate/sample_sales_with_errors.csv)

## 2. 입력 계약

```csv
date,category,item,amount
2026-08-03,교육,파이썬 기초,150000
```

| 열 | 규칙 | 오류 예시 |
| --- | --- | --- |
| `date` | `YYYY-MM-DD` | `2026-13-04` |
| `category` | 공백 제거 후 비어 있지 않음 | 빈 값 |
| `item` | 공백 제거 후 비어 있지 않음 | 빈 값 |
| `amount` | 0 이상의 유한한 숫자 | `-1`, `NaN`, `not-a-number` |

필수 열이 하나라도 없으면 전체 입력 계약 오류로 중단합니다. 행 값이 잘못되었다면 그 행만 오류 목록으로 분리합니다.

## 3. 처리 흐름

```text
CSV 헤더 검증
→ 행별 날짜·문자열·금액 검증
→ 정상 레코드와 검증 오류 분리
→ 정상 데이터 분류별 집계
→ Excel 요약·상세·오류 시트 생성
→ 임시 .xlsx에 저장
→ 최종 경로로 교체
→ 재열기·시트·행 수·수식 검증
```

## 4. 설치

```bash
python -m pip install -r requirements-automate.txt
```

이 프로젝트는 `openpyxl`을 사용합니다. Excel 프로그램이 설치되어 있지 않아도 `.xlsx`를 생성·구조 검증할 수 있습니다.

## 5. 정상 데이터 실행

```bash
python examples/13-python-automate/spreadsheet_report.py \
  examples/13-python-automate/sample_sales.csv \
  --output outputs/python-automate/sales-report.xlsx
```

예상 결과:

```text
보고서 생성 완료: .../outputs/python-automate/sales-report.xlsx
정상 5건, 검증 오류 0건
```

## 6. 오류 데이터 실행

```bash
python examples/13-python-automate/spreadsheet_report.py \
  examples/13-python-automate/sample_sales_with_errors.csv \
  --output outputs/python-automate/sales-report-errors.xlsx
```

보고서는 생성되지만 검증 오류가 있으면 종료 코드 2를 반환합니다. 스케줄러나 다음 작업이 오류 있는 보고서를 정상 결과로 오해하지 않게 하기 위한 정책입니다.

검증 오류를 예상하고 보고서 생성 자체를 성공으로 다루려면 다음 인자를 사용합니다.

```bash
python examples/13-python-automate/spreadsheet_report.py \
  examples/13-python-automate/sample_sales_with_errors.csv \
  --output outputs/python-automate/sales-report-errors.xlsx \
  --allow-invalid
```

## 7. 워크북 구조

### `요약`

- 정상 건수
- 검증 오류 건수
- 정상 데이터 총액
- 분류별 합계·막대 차트

건수와 합계는 `정상 데이터`, `검증 오류` 시트를 참조하는 수식입니다. Excel에서 상세 데이터를 수정하면 요약이 재계산됩니다.

### `정상 데이터`

- 날짜, 분류, 항목, 금액, 원본 CSV 행 번호
- 날짜와 금액은 문자열이 아닌 자료형으로 저장
- 헤더 필터와 첫 행 고정

### `검증 오류`

- 원본 CSV 행 번호
- 오류 사유
- JSON 형식의 원본 값

## 8. 수식 주입 방지

외부 CSV의 문자열이 `=`, `+`, `-`, `@`로 시작하면 Excel이 수식으로 해석할 수 있습니다. 프로젝트는 분류·항목·오류 문자열 앞에 작은따옴표를 추가해 텍스트로 저장합니다.

작은따옴표는 Excel 화면에서 텍스트 표시 지시로 사용됩니다. 원본 문자열은 `검증 오류` 시트의 JSON에 별도로 보존됩니다.

## 9. 테스트

```bash
pytest -q tests/test_spreadsheet_report.py
```

확인하는 항목:

1. 필수 열 누락 시 즉시 중단
2. 정상·오류 행 건수 보존
3. `Decimal`을 사용한 분류별 합계
4. 수식 형태 문자열의 텍스트 처리
5. 생성된 Excel의 시트 이름·행 수·요약 수식

## 10. 확장 과제

1. 날짜별·월별 요약 시트를 추가합니다.
2. 허용된 분류 목록을 JSON 설정으로 분리합니다.
3. 중복 행 판별을 위한 업무 키를 정의합니다.
4. CSV 파일 SHA-256와 생성 시각을 `요약`에 추가합니다.
5. 검증 오류가 일정 비율을 넘으면 Excel 생성 자체를 중단합니다.
6. 예약 실행 후 요약만 알림 미리보기로 만듭니다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 전체 행 수가 정상 행과 오류 행의 합계와 같습니다.
- [ ] 날짜·금액 자료형과 표시 서식을 분리했습니다.
- [ ] 오류 행에 원본 행 번호와 이유가 남습니다.
- [ ] 요약 수식이 상세 시트를 참조합니다.
- [ ] 저장한 Excel을 다시 열어 구조를 검증합니다.
{% endhint %}

---

다음 단계: 실무 반복 작업 하나를 선정해 작업 카드·미리보기·원상복구·테스트를 포함한 자동화 도구로 확장합니다.
