# 03-8. 미니 프로젝트: 인증 로그 분석기

## 목표

합성 인증 로그를 읽어 이벤트를 구조화하고, 사용자·IP별 DENY 횟수와 파싱 오류를 JSON으로 보고한다.

## 입력 형식

```text
2026-08-10T10:00:00Z ALLOW alice 10.0.0.5 /index
2026-08-10T10:00:01Z DENY bob 198.51.100.9 /admin
2026-08-10T10:00:02Z DENY bob 198.51.100.9 /login
BROKEN LINE
```

필드 순서는 `timestamp action user ip path`이다.

## 구현 단계

1. `split()`으로 필드를 분리한다.
2. 필드 수가 5개인지 확인한다.
3. timestamp, action, user, ip, path를 딕셔너리로 만든다.
4. IP는 `ipaddress.ip_address()`로 검증한다.
5. action은 ALLOW 또는 DENY만 허용한다.
6. 사용자별·IP별 DENY 횟수를 집계한다.
7. 오류 행 번호, 원문, 원인을 보존한다.
8. 결과를 JSON으로 저장하고 다시 읽어 검증한다.

## 결과 예시

```json
{
  "valid_events": 3,
  "parse_errors": 1,
  "deny_by_user": {"bob": 2},
  "deny_by_ip": {"198.51.100.9": 2},
  "suspicious_users": {"bob": 2},
  "error_lines": [4]
}
```

## 확장 과제

- `--input`, `--output`, `--threshold` 명령줄 인자 추가
- JSON과 CSV 입력 지원
- UTC 시간 범위 계산
- 사용자명·토큰·민감 경로 마스킹
- generator로 대용량 로그 한 줄씩 처리
- 정상·오류·경계값 테스트 추가

## 완료 기준

- [ ] 03-1~03-7의 핵심 개념을 코드에 적용했다.
- [ ] 정상 입력과 비정상 입력을 구분한다.
- [ ] 오류의 행 번호·원문·원인을 보존한다.
- [ ] 결과 JSON을 재현할 수 있다.
- [ ] 합성 데이터 또는 허가된 데이터만 사용한다.
