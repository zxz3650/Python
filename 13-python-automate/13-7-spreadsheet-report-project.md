# 13-7. 프로젝트 B - 보안 점검 결과 보고서

합성 보안 점검 CSV를 검증하고, 자산별 점검 내역과 미흡 항목을 Excel 보고서로 정리합니다. 입력 형식이 올바른 것과 보안 상태가 양호한 것은 서로 다른 의미입니다. `fail`도 유효한 점검 결과이며 보고서에 반드시 포함합니다.

{% hint style="info" %}
## 🧭 프로젝트 목표

- CSV 입력 계약, 날짜·허용값 검증, 중복 검사를 구현합니다.
- 양호·미흡·검토 필요·해당 없음을 구분해 집계합니다.
- 입력 오류에 원본 레코드 번호와 사유를 남깁니다.
- 외부 문자열의 수식 해석을 방지하고 저장 결과를 재검증합니다.
{% endhint %}

## 1. 시나리오와 실습 파일

담당자가 수집한 설정·로그·파일 점검 결과를 주간 보고서로 정리합니다. 제공 CSV는 모두 가상의 자산과 합성 결과이며, 프로그램이 서버에 접속하거나 실제 취약점을 판정하지 않습니다.

- [`security_report.py`](../examples/13-python-automate/security_report.py)
- [`sample_security_checks.csv`](../examples/13-python-automate/sample_security_checks.csv): 검증 통과 5건
- [`sample_security_checks_with_errors.csv`](../examples/13-python-automate/sample_security_checks_with_errors.csv): 검증 통과 5건, 입력 오류 4건

## 2. 입력 계약

헤더 이름과 순서는 다음과 같습니다.

```csv
date,asset,check_id,severity,status,evidence
2026-09-01,lab-web-01,CFG-001,high,fail,합성 설정 자료에서 디버그 모드 활성화 확인
```

| 열 | 검증 규칙 | 의미 |
| --- | --- | --- |
| `date` | 유효한 `YYYY-MM-DD` | 점검 날짜 |
| `asset` | 공백 제거 후 비어 있지 않음 | 가상 자산 식별자 |
| `check_id` | 공백 제거 후 비어 있지 않음 | 점검 항목 식별자 |
| `severity` | `high`, `medium`, `low`, `info` | 입력에 명시된 분류; CVSS 점수가 아님 |
| `status` | `pass`, `fail`, `review`, `na` | 양호·미흡·검토 필요·해당 없음 |
| `evidence` | 공백 제거 후 비어 있지 않음 | 판단 근거 요약; 비밀번호 등은 기록하지 않음 |

각 값은 최대 4,000자이며 Excel 저장이 불가능한 제어 문자를 허용하지 않습니다. 같은 `date + asset + check_id`의 첫 유효 행을 집계하고 이후 중복은 입력 오류로 분리합니다. 하루 여러 차례 점검이 필요하다면 시각 또는 실행 ID로 계약을 확장해야 합니다.

헤더 오류는 전체 처리를 중단합니다. 행 오류는 별도로 보존합니다. ‘원본 레코드 번호’는 헤더를 1로 세는 CSV 레코드 순서이며, 따옴표 안에 줄바꿈이 있으면 물리적인 줄 번호와 다를 수 있습니다.

## 3. 구현 순서

```text
CSV 바이트 읽기·SHA-256 → 헤더 확인
→ 날짜·열 수·허용값·중복 검증
→ 유효한 점검 결과와 입력 오류 분리
→ 상태별 건수와 high 미흡 건수 집계
→ 요약·점검 결과·입력 오류 시트 생성
→ 새 .xlsx 저장 → 재열기·건수·집계·수식 셀 검사
```

`load_checks()`, `summarize()`, `build_workbook()`을 역할별로 분리해 구현합니다. 잘못된 상태값을 `pass`로 바꾸거나, `review`를 양호에 합치지 않습니다.

## 4. 설치와 실행

저장소 루트에서 실행합니다. 기존 교안과 동일하게 Python `openpyxl`로 작성하며 Excel 프로그램 없이 생성·구조 검증이 가능합니다.

```bash
python -m pip install -r requirements-automate.txt
python examples/13-python-automate/security_report.py examples/13-python-automate/sample_security_checks.csv --output outputs/python-automate/security-report.xlsx
```

예상 출력은 `검증 통과 5건, 입력 오류 0건`입니다.

| 집계 | 예상값 |
| --- | --- |
| pass | 1 |
| fail | 2 |
| review | 1 |
| na | 1 |
| high 미흡 (`severity=high`이면서 `status=fail`) | 2 |

`high 미흡`은 `fail`의 부분집합입니다. 상태별 건수에 다시 더하지 않습니다.

## 5. 오류 데이터 실행

```bash
python examples/13-python-automate/security_report.py examples/13-python-automate/sample_security_checks_with_errors.csv --output outputs/python-automate/security-report-errors.xlsx
```

예상 출력은 `검증 통과 5건, 입력 오류 4건`입니다. 날짜, 심각도, 상태, 중복 오류가 각각 1건이며 유효한 결과의 집계는 정상 샘플과 같습니다.

| 종료 코드 | 의미 |
| --- | --- |
| 0 | 보고서 생성·검증 성공, 입력 오류 없음 |
| 1 | 헤더·파일 읽기·저장·출력 검증 실패 |
| 2 | 보고서 생성·검증 성공, 입력 오류 포함 |

종료 코드 0은 보안상 미흡 항목이 없다는 뜻이 아닙니다. 예제는 미흡 2건이 있어도 입력이 유효하면 0입니다. 자동 알림을 확장할 때는 실행 상태와 미흡 건수를 별도로 판단합니다. 기존 출력은 덮어쓰지 않으므로 재실행 시 새 파일명을 사용합니다.

## 6. 워크북 구조와 검증

- `요약`: 검증 통과·입력 오류 행 수, 네 상태의 건수, high 미흡 건수, 원본 CSV SHA-256, 집계 기준
- `점검 결과`: 검증을 통과한 모든 결과와 원본 레코드 번호. 미흡과 검토 필요도 포함
- `입력 오류`: 원본 레코드 번호, 오류 사유, JSON으로 표현한 원본 값

오류 JSON이 30,000자를 넘으면 보고서에서는 일부만 표시하며 원본 CSV를 참조하도록 표시합니다. 원본 CSV는 그대로 보존합니다.

요약 값은 Python에서 계산한 생성 시점의 값입니다. Excel에서 상세 셀을 수정해도 자동 갱신되지 않으므로 원본 CSV를 수정한 뒤 다시 실행합니다. 날짜는 날짜 자료형, 건수는 정수로 저장합니다.

다음 관계를 대조합니다.

```text
입력 레코드 수 = 검증 통과 행 + 입력 오류 행
검증 통과 행 = pass + fail + review + na
high 미흡 ≤ fail
```

## 7. 수식 해석 방지

자산명과 근거 문구는 외부 입력입니다. 예제의 `append_row()`는 모든 문자열 셀의 자료형을 명시적으로 텍스트로 지정합니다. `=2+3` 같은 무해한 문자열을 넣고 재열기 후 값이 그대로이며 `data_type`이 `s`인지 확인합니다.

이 정책은 예제가 생성한 `.xlsx`에 적용됩니다. CSV로 다시 내보내면 대상 프로그램의 해석 정책에 맞게 별도로 검증해야 합니다.

## 8. 테스트와 확장 과제

```bash
python -m pytest -q tests/test_security_automation.py
```

1. 제공 샘플의 행 수·상태별 집계·high 미흡 건수를 대조합니다.
2. 빈 입력, 헤더만 있는 CSV, 열 누락, 중복, 허용되지 않은 상태를 시험합니다.
3. 모든 행이 오류일 때 ‘입력 오류 존재’가 남는지 확인합니다.
4. 확장: 자산별 미흡 건수와 검토 필요 목록을 추가합니다.
5. 확장: 승인된 점검 항목 목록을 JSON 설정으로 관리합니다.
6. 확장: 이전 보고서와 비교하되 누락된 점검을 자동으로 ‘해결됨’ 처리하지 않습니다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 보안상 미흡과 입력 오류를 구분합니다.
- [ ] 상태별 건수와 유효한 결과 수가 일치합니다.
- [ ] 중복은 이중 집계하지 않고 오류에 보존합니다.
- [ ] 원본 CSV와 기존 결과를 덮어쓰지 않습니다.
- [ ] 저장 결과의 시트·행 수·집계·문자열 자료형을 확인합니다.
{% endhint %}

---

다음 단계: 두 프로젝트의 실행 이력과 결과 경로를 기록하는 예약 작업을 설계하고, 변경 발견·검사 실패·입력 오류에 대한 알림 미리보기를 작성합니다.
