# 13-6. 프로젝트 A - 안전한 파일 정리기

하나의 입력 폴더에 쌓인 파일을 이미지·문서·데이터·압축·기타로 분류합니다. 기본 명령은 파일을 바꾸지 않고 계획만 보여 주며, 적용 후에는 JSON 작업 기록으로 원상복구할 수 있습니다.

{% hint style="info" %}
## 🧭 프로젝트 목표

- 파일 선택·분류·충돌 처리를 서로 다른 함수로 구현합니다.
- `plan`, `apply`, `undo` CLI를 작성합니다.
- 심볼릭 링크와 폴더를 자동 이동에서 제외합니다.
- 작업 도중 실패해도 적용된 항목을 작업 기록에 보존합니다.
{% endhint %}

## 1. 실습 코드

[`file_organizer.py`](https://github.com/zxz3650/Python/blob/master/examples/13-python-automate/file_organizer.py)

```text
examples/13-python-automate/
└── file_organizer.py
```

## 2. 기능 요구사항

| 기능 | 요구사항 | 실패 조건 |
| --- | --- | --- |
| 계획 | 한 단계의 일반 파일만 분류 | 출발 폴더 없음 |
| 분류 | 확장자 기준 5개 분류 | 알 수 없는 확장자는 `other` |
| 충돌 | `name_2.ext`, `name_3.ext` 순서로 회피 | 덮어쓰기 금지 |
| 적용 | 이동 전 전체 계획 재검증 | 출발·도착 상태 변경 |
| 기록 | 이동 후 항목별 `applied` 저장 | 기록 덮어쓰기 금지 |
| 원상복구 | 적용 역순으로 되돌림 | 원본 경로 충돌 시 중단 |

## 3. 작업 흐름

```text
SOURCE의 파일 목록
→ 폴더·심볼릭 링크 제외
→ 확장자 분류
→ 이름 충돌 해결
→ JSON 미리보기
→ apply 시 작업 기록 선생성
→ 파일별 이동·상태 갱신
→ undo 시 역순 원상복구
```

## 4. 학습용 폴더 준비

실제 다운로드 폴더를 바로 사용하지 말고 임시 폴더를 만듭니다.

```bash
mkdir -p /tmp/python-automate-inbox
touch /tmp/python-automate-inbox/photo.jpg
touch /tmp/python-automate-inbox/report.pdf
touch /tmp/python-automate-inbox/events.csv
touch /tmp/python-automate-inbox/archive.zip
touch /tmp/python-automate-inbox/README
```

Windows에서는 사용자 문서 아래에 `python-automate-inbox` 학습용 폴더를 만듭니다.

## 5. 미리보기

```bash
python examples/13-python-automate/file_organizer.py \
  plan /tmp/python-automate-inbox
```

기본 도착 폴더는 `SOURCE/_organized`입니다. 표준 출력의 JSON에서 다음을 확인합니다.

- `total`이 예상 파일 수와 같은가?
- `counts`의 분류별 건수가 맞는가?
- 모든 `source`가 입력 폴더 안에 있는가?
- 모든 `destination`이 의도한 도착 폴더 안에 있는가?
- 덮어쓰기 대상이 없는가?

## 6. 적용

```bash
python examples/13-python-automate/file_organizer.py \
  apply /tmp/python-automate-inbox
```

성공하면 이동 건수와 작업 기록 경로를 출력합니다.

```text
/tmp/python-automate-inbox/_organized/
├── .automation-manifests/
├── archives/
├── data/
├── documents/
├── images/
└── other/
```

작업 기록은 각 항목의 출발·도착 경로와 `planned`, `applied`, `undone` 상태를 보존합니다.

## 7. 원상복구

`적용 완료` 출력에서 표시된 작업 기록 경로를 사용합니다.

```bash
python examples/13-python-automate/file_organizer.py \
  undo /tmp/python-automate-inbox/_organized/.automation-manifests/organize-YYYYMMDDTHHMMSSZ.json
```

도착 파일이 사라졌거나 원본 경로에 다른 파일이 있으면 원상복구를 시작하지 않습니다. 사용자가 충돌을 확인한 후 해결해야 합니다.

## 8. 테스트 시나리오

1. 확장자 대소문자: `PHOTO.JPG`를 `images`로 분류합니다.
2. 확장자 없음: `README`를 `other`로 분류합니다.
3. 이름 충돌: 기존 `photo.jpg`가 있으면 `photo_2.jpg`를 계획합니다.
4. 심볼릭 링크: 계획에 포함하지 않습니다.
5. 도중 상태 변경: `plan` 후 출발 파일을 없애면 `apply`가 이동 전에 중단됩니다.
6. 원상복구 충돌: 원본 경로에 다른 파일을 만들면 `undo`가 중단됩니다.

```bash
pytest -q tests/test_file_organizer.py
```

## 9. 확장 과제

1. JSON 설정으로 분류 규칙을 바꾸게 합니다.
2. `--recursive`를 추가하되 제외 폴더와 순환 링크를 처리합니다.
3. 이동 전·후 SHA-256을 기록해 복사 만료를 확인합니다.
4. 원상복구 후 빈 분류 폴더만 정리합니다.
5. 30일이 지난 작업 기록을 보관 압축하되 삭제는 사람이 승인하게 합니다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] `plan`이 파일을 변경하지 않습니다.
- [ ] `apply`가 작업 기록을 먼저 만든 후 이동합니다.
- [ ] 같은 이름의 파일을 덮어쓰지 않습니다.
- [ ] `undo`가 충돌을 사전 검사하고 역순으로 되돌립니다.
- [ ] 정상·오류·경계 테스트가 통과합니다.
{% endhint %}

---

다음: [13-7. 프로젝트 B - Excel 요약 보고서](13-7-spreadsheet-report-project.md)
