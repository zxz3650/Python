# 13-6. 프로젝트 A - 파일 무결성 변경 탐지기

서버 설정과 배포 파일이 승인된 상태에서 바뀌었는지 확인하는 도구를 만듭니다. 학습용 폴더의 상대 경로와 SHA-256을 JSON 기준선으로 저장한 뒤, 다시 검사해 추가·수정·삭제된 파일을 보고합니다.

{% hint style="info" %}
## 🧭 프로젝트 목표

- `pathlib`, 반복문, 바이너리 읽기로 파일 목록과 해시를 수집합니다.
- 딕셔너리와 집합 연산으로 두 시점의 차이를 구분합니다.
- `baseline`, `check` CLI와 종료 코드로 예약 검사 흐름을 만듭니다.
- 파일 변경 사실과 보안 사고 판정을 구분합니다.
{% endhint %}

## 1. 보안 업무 시나리오

관리자가 승인한 설정 파일로 기준선을 만듭니다. 이후 설정 변경이나 파일 누락이 발생하면 변경 목록을 확인하고, 승인된 배포인지 조사합니다. 이 도구는 변경을 탐지하며 원인을 확정하거나 파일을 복구하지 않습니다.

실습 코드는 [`file_integrity.py`](../examples/13-python-automate/file_integrity.py)입니다. 저장소 루트에서 명령을 실행합니다. Python 표준 라이브러리만 사용합니다.

## 2. 기능 요구사항

| 기능 | 요구사항 | 실패 처리 |
| --- | --- | --- |
| 기준선 생성 | 하위 폴더의 일반 파일을 64 KiB씩 읽어 SHA-256 기록 | 기존 기준선 덮어쓰기 거부 |
| 경로 관리 | 기준선에 상대 경로, 검사 루트, 형식 버전 저장 | 다른 루트의 기준선 사용 거부 |
| 변경 비교 | `added`, `modified`, `deleted`, `unchanged` 분리 | 손상된 기준선이면 검사 실패 |
| 결과 저장 | 표준 출력과 선택적 JSON 파일 출력 | 기존 결과 덮어쓰기 거부 |
| 범위 관리 | 기준선·결과를 검사 폴더 밖에 저장 | 링크·특수 파일·읽기 실패 시 중단 |

심볼릭 링크는 조용히 제외하지 않고 오류로 처리합니다. 일부 파일을 읽지 못했는데도 전체 검사가 정상이라고 표시하지 않기 위해서입니다.

## 3. 학습용 폴더 준비

저장소 루트에서 아래 Python 코드를 한 번 실행합니다. 실제 설정이나 비밀번호는 사용하지 않습니다. 재실습할 때는 `integrity-lab-02`처럼 새 폴더 이름을 사용합니다.

```python
from pathlib import Path

root = Path("outputs/integrity-lab/target")
root.mkdir(parents=True, exist_ok=False)
(root / "app.conf").write_text("debug=false\n", encoding="utf-8")
(root / "policy.txt").write_text("session_timeout=600\n", encoding="utf-8")
(root / "notice.txt").write_text("training only\n", encoding="utf-8")
```

## 4. 기준선 생성과 정상 검사

```bash
python examples/13-python-automate/file_integrity.py baseline outputs/integrity-lab/target --baseline outputs/integrity-lab/baseline.json
python examples/13-python-automate/file_integrity.py check outputs/integrity-lab/target --baseline outputs/integrity-lab/baseline.json
```

기준선 생성 시 `기준선 생성: 3개 파일`을 출력합니다. 최초 검사에서는 `unchanged`에 세 파일이 있고 나머지 목록은 비어 있습니다. 두 명령 모두 종료 코드 0입니다.

## 5. 변경을 만들어 탐지하기

앞서 만든 학습용 파일만 변경합니다.

```python
from pathlib import Path

root = Path("outputs/integrity-lab/target")
(root / "app.conf").write_text("debug=true\n", encoding="utf-8")
(root / "policy.txt").unlink()
(root / "new.conf").write_text("feature=enabled\n", encoding="utf-8")
```

```bash
python examples/13-python-automate/file_integrity.py check outputs/integrity-lab/target --baseline outputs/integrity-lab/baseline.json --output outputs/integrity-lab/changes.json
```

예상 결과는 다음과 같고 종료 코드는 2입니다.

```json
{
  "added": ["new.conf"],
  "deleted": ["policy.txt"],
  "modified": ["app.conf"],
  "unchanged": ["notice.txt"]
}
```

같은 검사를 반복해도 분류는 같습니다. 저장하려면 새 결과 이름을 지정하거나 `--output`을 생략합니다. 파일 이름 변경은 삭제와 추가로 표시합니다.

## 6. 직접 구현할 핵심 로직

예제 코드를 실행한 다음 `snapshot()`, `compare()`, `load_baseline()`을 직접 구현해 봅니다.

```text
검사 루트 확인 → 일반 파일 목록 → 청크 단위 SHA-256
→ 기준선과 현재 경로 집합 비교
→ 공통 경로의 해시 비교 → 변경 목록 정렬 → 결과 출력
```

| 종료 코드 | 의미 | 예약 작업의 후속 처리 |
| --- | --- | --- |
| 0 | 기준선 생성 성공 또는 변경 없음 | 실행 이력 보관 |
| 1 | 읽기·기준선·출력 오류 | 검사 실패 원인 확인 |
| 2 | 파일 변경 발견 | 승인된 변경인지 검토 |

## 7. 결과 해석과 한계

- 해시가 다르다는 사실만으로 악성 변경이라고 판단할 수 없습니다. 변경 승인 내역과 대조합니다.
- 기준선까지 바뀌면 비교 결과를 신뢰할 수 없습니다. 승인된 기준선을 검사 대상과 분리하고 접근 권한을 관리합니다. SHA-256 자체는 기준선 작성자를 인증하지 않습니다.
- 실습은 검사 중 파일이 바뀌지 않는 폴더를 전제로 합니다. 운영 환경의 동시 변경과 링크 교체 경쟁 조건을 방어하는 제품 수준의 감시 도구는 아닙니다.
- 내용만 비교하므로 권한·소유자·시간 정보의 변경은 탐지하지 않습니다. 빈 폴더 변경도 대상에 포함하지 않습니다.

## 8. 테스트와 확장 과제

```bash
python -m pytest -q tests/test_security_automation.py
```

1. 정상·추가·수정·삭제·빈 파일을 준비해 결과를 비교합니다.
2. 기존 기준선에 다시 쓰기를 시도해 원본이 유지되는지 확인합니다.
3. 없는 폴더, 손상된 JSON, 잘못된 해시, 심볼릭 링크에서 정상 판정이 나오지 않는지 확인합니다.
4. 확장: 검사 시각과 이전·현재 해시를 결과에 추가합니다.
5. 확장: 승인 사유를 기록하고 새로운 이름으로 기준선을 갱신하는 절차를 설계합니다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 기준선 생성 후 원본 파일 내용이 유지됩니다.
- [ ] 추가·수정·삭제·변경 없음을 구분합니다.
- [ ] 검사 실패와 변경 발견의 종료 코드를 구분합니다.
- [ ] 기준선과 출력 파일을 덮어쓰지 않습니다.
- [ ] 파일 변경을 사고로 확정할 수 없는 이유를 설명합니다.
{% endhint %}

---

다음: [13-7. 프로젝트 B - 보안 점검 결과 보고서](13-7-spreadsheet-report-project.md)
