# 13-5. 예약·알림·이미지·GUI 자동화

자동화 프로그램을 시간에 맞춰 실행하고, 결과를 알리고, 이미지나 GUI를 처리하는 단계를 다룹니다. 외부 영향이 있는 자동화이므로 중단 조건, 중복 방지, 비밀값 분리를 핵심으로 둡니다.

{% hint style="info" %}
## 🧭 학습 목표

- 프로그램 내부 대기와 운영체제 스케줄러를 구분합니다.
- 중복 실행 방지와 실행 결과 코드를 설계합니다.
- 알림을 미리보기와 실제 전송으로 나눕니다.
- Pillow 이미지 일괄 처리와 GUI 자동화의 중단 장치를 적용합니다.
{% endhint %}

## 1. 시간을 다루는 기준

- 경과 시간 측정은 `time.monotonic()`을 사용합니다.
- 업무 시각은 타임존 정보가 있는 `datetime`으로 표현합니다.
- 로그와 저장은 UTC, 사용자 표시는 지역 타임존을 원칙으로 합니다.

```python
from datetime import datetime, timezone
import time

started = time.monotonic()
created_at = datetime.now(timezone.utc).isoformat()

# 작업

elapsed_seconds = time.monotonic() - started
```

시스템 시각은 NTP 보정이나 사용자 변경으로 거꾸로 이동할 수 있으므로 경과 시간 측정에 적합하지 않습니다.

## 2. 운영체제 스케줄러

계속 실행하며 `sleep()`하는 Python 프로세스보다 운영체제의 스케줄러를 우선합니다.

| 환경 | 도구 | 확인 사항 |
| --- | --- | --- |
| Windows | 작업 스케줄러 | 사용자, 작업 폴더, 최고 권한 필요 여부 |
| macOS | `launchd` | `WorkingDirectory`, 표준 출력·오류 경로 |
| Linux | `systemd timer` 또는 cron | 환경변수, 재시작 정책, 로그 |

스케줄러에는 절대 경로를 사용하고, 대화형 입력에 의존하지 않도록 CLI 인자와 설정 파일을 사용합니다.

## 3. 중복 실행과 잠금

앞선 작업이 종료되기 전에 다음 스케줄이 시작될 수 있습니다. 작업 식별자나 잠금 파일을 사용하되, 비정상 종료 후 남은 잠금을 식별할 수 있어야 합니다.

```python
import os

lock_path = output_dir / ".weekly-report.lock"

try:
    descriptor = lock_path.open("x", encoding="utf-8")
except FileExistsError:
    raise SystemExit("이미 실행 중인 작업이 있습니다.")

try:
    descriptor.write(str(os.getpid()))
    descriptor.close()
    run_job()
finally:
    lock_path.unlink(missing_ok=True)
```

실무에서는 PID의 생존 여부, 잠금 생성 시각, 호스트 정보를 함께 검증합니다.

## 4. 종료 코드와 로그

| 종료 코드 | 의미 | 스케줄러 동작 예시 |
| --- | --- | --- |
| 0 | 성공 | 다음 예정 실행 |
| 1 | 일반 실패 | 알림 후 수동 확인 |
| 2 | 입력·설정 오류 | 재시도 없이 설정 수정 |
| 75 | 일시적 실패 | 제한된 재시도 |

로그에는 작업 ID, 시작·종료 시각, 입력 건수, 정상·오류 건수, 출력 경로, 오류 유형을 남깁니다. 토큰·비밀번호·전체 개인정보는 남기지 않습니다.

## 5. 알림과 전송

알림은 다음 두 단계로 나눕니다.

1. `preview`: 수신자, 제목, 본문 요약, 첨부파일, 건수를 출력합니다.
2. `send`: 명시적 승인 인자가 있을 때만 외부 서비스를 호출합니다.

```python
smtp_password = os.environ["AUTOMATE_SMTP_PASSWORD"]
```

- 계정 비밀번호보다 전용 앱 비밀번호나 API 토큰을 사용합니다.
- 테스트에서는 실제 서버 대신 목 객체와 로컬 수신함을 사용합니다.
- 수신자 수, 일일 전송 건수, 재시도 횟수를 제한합니다.
- 전송 성공 응답을 받은 후 메시지 ID를 기록합니다.

## 6. Pillow 이미지 일괄 처리

```python
from PIL import Image, ImageOps

with Image.open(input_path) as image:
    image = ImageOps.exif_transpose(image)
    image.thumbnail((1600, 1600))
    image.convert("RGB").save(
        output_path,
        format="JPEG",
        quality=88,
        optimize=True,
    )
```

- 원본 파일은 덮어쓰지 않습니다.
- EXIF 회전 정보를 화면 방향에 반영합니다.
- 투명도가 있는 이미지를 JPEG로 바꿀 때 배경색을 명시합니다.
- 출력 크기, 포맷, 가로·세로 범위를 다시 열어 검증합니다.
- 위치·장치 정보가 불필요하면 EXIF 메타데이터 제거 정책을 적용합니다.

## 7. GUI 자동화는 마지막 선택

GUI 자동화는 창 크기, 해상도, 폰트, 언어, 로딩 시간, 포커스에 영향을 받습니다. API, CLI, 파일 교환 방식이 없을 때만 사용합니다.

```python
import pyautogui

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3
```

필수 안전 장치:

- 마우스를 화면 모서리로 옮기면 중단되는 fail-safe를 활성화합니다.
- 실행 전 카운트다운과 대상 창 확인 단계를 둡니다.
- 최대 반복 횟수와 전체 실행 시간을 제한합니다.
- 결제, 삭제, 전송 버튼은 사람이 직접 확인하게 합니다.
- 별도의 테스트 계정·테스트 환경에서 검증합니다.

## 8. 장애 시나리오

예약 실행 전에 다음 실패를 재현합니다.

- 입력 파일 미도착·일부 도착
- 이전 작업이 종료되지 않음
- 출력 디스크 공간 부족·권한 없음
- API 429·503·타임아웃
- 알림 수신자·첨부파일 오류
- GUI 창 이동·팝업·화면 잠금

각 실패에 대해 `즉시 중단`, `일부 결과 보존`, `제한적 재시도`, `사람 확인`중 하나를 선택합니다.

## 완료 기준

- [ ] 스케줄러에 절대 경로와 비대화형 인자를 설정했습니다.
- [ ] 중복 실행과 비정상 종료 후 잠금을 처리합니다.
- [ ] 알림 미리보기와 실제 전송을 분리합니다.
- [ ] 원본 이미지를 보존하고 출력을 재검증합니다.
- [ ] GUI 자동화에 중단 장치와 최대 반복 횟수를 둡니다.

---

다음: [13-6. 프로젝트 A - 안전한 파일 정리기](13-6-safe-file-organizer-project.md)
