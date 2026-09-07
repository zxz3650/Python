# 13-6. 프로젝트 A - KAPE 결과 정규화

> **핵심 질문** · 분석 조건을 적용하기 전에 자료를 같은 기준으로 읽고 출처를 보존할 수 있을까요?

프로젝트 A에서는 파서 출력 CSV를 공통 레코드로 바꾸는 부분을 구현합니다. 프로젝트 B는 같은 레코드에서 검토 항목과 관련 근거를 추출합니다. 제공 `pipeline.py`에는 두 단계가 함께 있으므로 먼저 `load_case()`와 `normalize()`를 읽고 결과를 대조합니다.

## 1. 실습 파일

- [`make_sample.py`](../examples/13-kape-triage/make_sample.py): 합성 CSV·manifest 생성
- [`pipeline.py`](../examples/13-kape-triage/pipeline.py): 정규화·검토 항목 추출·HTML 보고
- [`실행 안내`](../examples/13-kape-triage/README.md)

Python 표준 라이브러리만 사용합니다. 제공 자료는 실제 KAPE·PECmd·EvtxECmd 출력이 아니며 **열 매핑과 오류 처리를 학습하기 위한 합성 내보내기 형식**입니다. 해당 도구들의 원본 CSV와 직접 호환된다고 가정하지 않습니다.

## 2. 입력 만들기

저장소 루트에서 실행합니다. 기존 폴더가 없는 새 이름을 사용합니다.

```bash
python examples/13-kape-triage/make_sample.py outputs/kape-input
```

```text
kape-input/
├── manifest.json
├── events-host-a.csv
├── events-host-b.csv
├── prefetch.csv
├── registry.csv
├── mft.csv
└── shimcache.csv
```

manifest에는 `amcache.csv`도 선언되어 있지만 파일은 만들지 않습니다. 미수집 상태를 보고하는 연습입니다. 합성 IP `192.0.2.50`은 자료 안의 값이며 접속 대상이 아닙니다.

## 3. 한 행의 변환을 따라갑니다

예제 `events-host-b.csv`의 첫 시각은 `2026-09-01T09:06:00+09:00`입니다.

| 입력·설정 | 정규화 결과 |
| --- | --- |
| source의 `host=HOST-B` | 원래 호스트 유지 |
| `columns.timestamp=When` | `When` 열을 시각 필드로 읽음 |
| 시각의 `+09:00` | UTC로 바꾸어 `2026-09-01T00:06:00Z` |
| `timestamp_kind=event_created` | 다른 아티팩트의 실행·파일 시각과 구분 |
| CSV 바이트·레코드 번호 | 해시·출처 위치·안정적인 UID 생성 |

`When`이 모든 파서에 있는 표준 열이어서 읽는 것이 아닙니다. manifest가 원본 열과 공통 필드의 관계를 알려 줍니다.

## 4. 실행과 예상 결과

```bash
python examples/13-kape-triage/pipeline.py outputs/kape-input/manifest.json --output outputs/kape-report-01
```

표준 출력 첫 줄:

```json
{"events": 14, "findings": 8, "issues": 1, "undated": 1, "missing_sources": 1}
```

종료 코드는 `2`이며 처리 상태는 `partial`입니다. 실패한 프로그램이라는 뜻이 아니라, 일부 입력 문제와 누락을 보존한 보고서가 만들어졌다는 뜻입니다.

| 대조 항목 | 예상값 | 의미 |
| --- | --- | --- |
| 선언 자료 | 7개 | CSV 6개 + 누락 Amcache 1개 |
| 읽은 CSV 행 | 15개 | 헤더 제외 |
| 유효한 레코드 | 14개 | 시각 없는 Shimcache 1개 포함 |
| 격리 행 | 1개 | 시간대 없는 HOST-B 이벤트 |
| 시각 있는 레코드 | 13개 | UTC 타임라인에 정렬 |
| 시각 없는 레코드 | 1개 | 삭제하지 않고 끝에 보존 |

자료 파일 형식 전체가 손상된 경우에는 읽지 못한 뒷부분의 행 수까지 알 수 없습니다. 이때 `parse_failed`와 실제 읽은 행 수를 기록하므로 모든 실패 파일에서 전체 입력 행 수를 정확히 계산했다고 설명하지 않습니다.

## 5. 산출물 확인

```text
kape-report-01/
├── normalized.jsonl     공통 레코드 전체
├── report.json          처리 범위·오류·검토 항목·관련 경로 전체
├── report.html          로컬에서 읽는 요약 화면
└── complete.json        결과 저장 완료 표시와 report.json 해시
```

```python
import json
from pathlib import Path

report = json.loads(Path("outputs/kape-report-01/report.json").read_text(encoding="utf-8"))
assert len(report["events"]) == 14
assert report["summary"]["undated"] == 1
assert report["processing_status"] == "partial"
print("입력 검증 결과 확인 완료")
```

## 6. 직접 구현할 부분

| 함수 | 학습할 책임 |
| --- | --- |
| `input_path()` | 입력 루트·상대 경로·링크 정책 확인 |
| `utc_time()` | 문법·시간대·정밀도 확인 후 UTC 변환 |
| `normalize()` | 열 매핑·필수 값·출처·UID 생성 |
| `load_case()` | 자료별 상태·오류 분리와 시간 정렬 |

다음 변경을 각각 새 출력 경로로 시험합니다.

1. HOST-B source에 근거 있는 `utc_offset`을 지정하면 어떤 행이 복구되는지 확인합니다. 합성 자료에서는 `+09:00`을 사용합니다.
2. Prefetch CSV를 헤더만 남긴 작업 사본으로 바꾸어 `empty`를 확인합니다.
3. 매핑에 없는 열 이름을 설정해 `parse_failed`를 확인합니다.
4. 같은 입력 파일을 두 번 선언하면 오류로 중단되는지 확인합니다.

## 7. 실제 KAPE 결과로 바꾸는 절차

1. 파서와 출력 프로필을 고정하고 익명화된 소량 샘플을 준비합니다.
2. 실제 헤더와 필드 값을 확인해 manifest를 작성합니다.
3. 복합 Payload·다중 시각·경로 결합이 필요하면 전용 어댑터를 작성합니다.
4. 원본 몇 행을 수작업으로 대조한 뒤 전체 자료를 처리합니다.
5. 파서·규칙 업데이트 시 같은 계약 검증을 다시 수행합니다.

실제 원본 EVTX·Prefetch·하이브 파싱, KAPE 실행, 전체 사건의 모든 아티팩트 자동 식별은 이 기본 프로젝트의 구현 범위가 아닙니다.

## 완료 기준

- [ ] 정상·누락·빈 파일·파일 오류·행 오류를 구분합니다.
- [ ] 14개 레코드와 1개 오류 행을 샘플과 대조합니다.
- [ ] 시각 없는 레코드를 버리지 않습니다.
- [ ] 원본 해시·레코드 위치·파서 버전을 보존합니다.

---

다음: [13-7. 프로젝트 B - Windows 아티팩트 통합 분석](13-7-spreadsheet-report-project.md)
