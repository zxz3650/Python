# 07-7. 로컬 네트워크·웹 보안 점검 프로젝트

06장의 TCP 연결 확인과 07장의 HTTP 검증을 결합합니다. 학습용 서버를 `127.0.0.1`에서 실행하고, 점검기가 연결성·응답 계약·보안 헤더·리다이렉트를 확인해 JSON 보고서를 만듭니다.

{% hint style="info" %}
## 🧭 프로젝트 목표

- 소켓과 HTTP 라이브러리의 역할을 구분합니다.
- 점검 관점과 구현 코드를 연결해 설명합니다.
- 안전 경계를 코드로 강제합니다.
- 관찰 결과와 취약점 확정을 구분합니다.
{% endhint %}

## 실습 코드

- [`training_server.py`](https://github.com/zxz3650/Python/blob/master/examples/07-local-web-security-lab/training_server.py)
- [`security_validator.py`](https://github.com/zxz3650/Python/blob/master/examples/07-local-web-security-lab/security_validator.py)

## 1. 프로젝트 구조

```text
training_server.py
├─ /health       정상 JSON과 기본 보안 헤더
├─ /api/echo     쿼리 입력을 JSON으로 반환
├─ /headers      일부 보안 헤더가 없는 학습 응답
└─ /redirect     /health로 이동

security_validator.py
├─ URL·loopback 범위 검증
├─ TCP 연결 확인
├─ 상태·Content-Type·JSON 검사
├─ 보안 헤더 검사
├─ 리다이렉트 출처 검사
└─ JSON 보고서 저장
```

## 2. 점검 관점과 코드 연결

| 점검 관점 | 구현 코드 | 결과 해석 |
| --- | --- | --- |
| 대상 범위 | `validate_loopback_url()` | 외부 주소면 요청 전 중단 |
| 네트워크 연결 | `check_tcp_connection()` | 06장의 socket 연결 확인 |
| API 계약 | `check_health()` | 상태·형식·필수 값 검증 |
| 헤더 정책 | `check_security_headers()` | 누락 헤더를 warning으로 기록 |
| 이동 경로 | `check_redirect()` | scheme·host·port가 같은지 확인 |
| 자원 제한 | timeout, `read_limited()` | 무한 대기·과도한 응답 방지 |

## 3. 실행

의존성을 설치합니다.

```bash
python -m pip install -r requirements.txt
```

첫 번째 터미널에서 서버를 실행합니다.

```bash
python examples/07-local-web-security-lab/training_server.py
```

두 번째 터미널에서 점검기를 실행합니다.

```bash
python examples/07-local-web-security-lab/security_validator.py \
  http://127.0.0.1:8080
```

기본 보고서는 `web-security-report.json`에 저장됩니다.

## 4. 예상 결과

- TCP 연결: pass
- `/health` JSON 계약: pass
- `/headers` 보안 헤더: warning
- `/redirect` 같은 출처 이동: pass

`warning`은 프로젝트가 의도적으로 만든 누락 설정을 발견한 결과입니다. 실제 환경에서는 애플리케이션 용도, 프록시, HTTPS 종단 위치를 함께 확인해야 합니다.

## 5. 안전장치 확인

```bash
python examples/07-local-web-security-lab/security_validator.py \
  https://example.com
```

외부 주소는 요청을 보내기 전에 거부되어야 합니다. `localhost`가 다른 주소로 바뀌도록 hosts/DNS 설정을 조작한 경우에도 해석된 주소가 loopback인지 재확인합니다.

## 6. 분석 질문

1. TCP 연결이 성공했는데 `/health`가 500이면 어느 계층의 문제인가요?
2. Content-Type이 JSON이지만 본문 파싱이 실패하면 무엇을 기록해야 하나요?
3. 보안 헤더 누락을 즉시 취약점으로 확정하면 안 되는 이유는 무엇인가요?
4. 리다이렉트를 자동으로 따르기 전에 목적지를 확인하는 이유는 무엇인가요?

## 7. 확장 과제

1. 점검별 처리 시간을 보고서에 추가합니다.
2. 서버 미실행·잘못된 JSON·응답 지연 테스트를 추가합니다.
3. 예상 상태와 헤더 정책을 별도 JSON 설정 파일로 분리합니다.
4. 08장에서 CLI 옵션과 `logging`을 추가합니다.
5. 09장에서 서버를 별도 프로세스로 실행하지 않는 pytest를 작성합니다.

{% hint style="danger" %}
이 프로젝트는 로컬 학습용입니다. 외부 주소 허용, 주소 범위 반복, 인증 추측, 공격 페이로드 전송 기능을 추가하지 않습니다. 실무 점검은 명시적인 승인과 범위 통제 아래 수행합니다.
{% endhint %}

## 완료 기준

- [ ] 서버와 점검기를 서로 다른 터미널에서 실행할 수 있습니다.
- [ ] 외부 URL이 요청 전에 거부되는 것을 확인했습니다.
- [ ] TCP·HTTP·데이터 검증 실패를 구분할 수 있습니다.
- [ ] warning의 근거와 추가 확인 사항을 설명할 수 있습니다.
- [ ] JSON 보고서를 재실행해 같은 구조로 생성할 수 있습니다.

---

다음 장: [08. 시스템 자동화](../08-system-automation.md)
