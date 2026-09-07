# 13장 보안 자동화 실습

저장소 루트에서 교안의 명령을 실행합니다.

| 단원 | 실습 코드 | 입력 |
| --- | --- | --- |
| [13-6. 파일 무결성 변경 탐지기](../../13-python-automate/13-6-safe-file-organizer-project.md) | `file_integrity.py` | 직접 만든 학습용 폴더와 JSON 기준선 |
| [13-7. 보안 점검 결과 보고서](../../13-python-automate/13-7-spreadsheet-report-project.md) | `security_report.py` | `sample_security_checks.csv`, `sample_security_checks_with_errors.csv` |

샘플의 자산명·점검 내용은 모두 합성 데이터입니다. 실행 명령, 예상 결과, 종료 코드, 확장 과제는 각 교안을 참고합니다.

검증은 `openpyxl` 설치 후 다음과 같이 실행할 수도 있습니다.

```bash
python -m unittest discover -s tests -p 'test_security_automation.py' -v
```

`file_organizer.py`, `spreadsheet_report.py`, `sample_sales*.csv`는 이전 교안의 참고 예제로 보존합니다. 현재 13-6·13-7 실습은 위 표의 보안 자동화 코드를 사용합니다.
