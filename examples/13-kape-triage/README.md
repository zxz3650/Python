# KAPE 후처리·Windows 아티팩트 통합 분석 실습

완료된 파서 CSV를 manifest의 열 매핑으로 읽는 Python 표준 라이브러리 예제입니다. 원본 EVTX·하이브를 직접 파싱하거나 KAPE·외부 엔진을 실행하지 않습니다.

```bash
python examples/13-kape-triage/make_sample.py outputs/kape-input
python examples/13-kape-triage/pipeline.py outputs/kape-input/manifest.json --output outputs/kape-report-01
```

샘플은 실제 KAPE/EZ Tools 출력이 아닌 합성 CSV입니다. 실제 파서 출력에는 버전별 어댑터와 헤더 검증이 필요합니다. 이름·경로·IP·시각은 모두 학습용입니다.

예상 요약은 `events=14`, `findings=8`, `issues=1`, `undated=1`, `missing_sources=1`이며 종료 코드는 2입니다. 시간대 누락과 미수집 Amcache를 의도적으로 포함했습니다.

출력:

- `normalized.jsonl`: 원본 참조·시각 의미가 있는 공통 레코드 전체
- `report.json`: 처리 범위·입력 오류·규칙 일치·관련 경로 전체
- `report.html`: 외부 연결 없는 정적 보고서; 타임라인 최대 1,000건 표시
- `complete.json`: 저장 완료 표시와 보고서 해시. `processing_status`는 `partial`일 수도 있음

종료 코드 0은 선언 입력의 처리 완료, 1은 실행 실패, 2는 부분 처리입니다. 검토 항목 수와 독립된 값입니다. 기존 출력 폴더는 덮어쓰지 않으며, 오류 후 마커 없는 부분 출력은 완료로 사용하지 않습니다.

입력은 CSV당 25 MiB, 사건당 100,000행으로 제한됩니다. ISO 시각의 마이크로초까지 지원하며 더 높은 정밀도는 격리합니다. 학습용 메모리 기반 처리이므로 대규모 사건은 저장·정렬 구조를 별도로 설계해야 합니다.

```bash
python -m unittest discover -s tests -p 'test_kape_pipeline.py' -v
```

[프로젝트 A: 정규화](../../13-python-automate/13-6-safe-file-organizer-project.md) · [프로젝트 B: 통합 분석](../../13-python-automate/13-7-spreadsheet-report-project.md)
