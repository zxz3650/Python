# 05-3 보안 로그 정규식 예제

Python 표준 라이브러리로 합성 웹로그·SSH 로그·CloudTrail 필드를 검사한다.
실제 로그 수집이나 AWS API 호출은 수행하지 않는다.

```bash
python examples/05-security-regex/security_regex.py
```

웹로그와 SSH 로그는 각각 1·2행이 일치한다. CloudTrail은 이름 패턴, 정확한 서비스·이벤트 목록, 오류 코드와 CLI 접두부를 구분해 출력한다.

입력은 코드 안의 WEB_LINES, AUTH_LINES, CLOUDTRAIL_TEXT에 있다. AWS 레코드는 필요한 필드만 남긴 합성 자료이며 완전한 이벤트 스키마 예제가 아니다.

웹 패턴은 정해진 필드 순서·길이와 따옴표 이스케이프가 없는 형식에 한정된다. 불일치는 정상 또는 형식 미지원일 수 있다. SSH 주소·포트는 모양만 검사하며 유효성 검증은 별도다. 패턴 일치는 공격 확정이 아니다.

노트북은 notebooks/05-3-security-log-patterns.ipynb를 연다. 본문은 저장소의 05-text-processing/05-3-regex-basics.md를 참고한다.
