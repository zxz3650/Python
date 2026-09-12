"""05-3 보안 로그 정규식 예제: 합성 입력을 로컬에서 검사한다."""

from __future__ import annotations

import ipaddress
import json
import re

# 이 예제는 따옴표 이스케이프가 없는 고정 Combined 형식만 대상으로 한다.
# 상태 코드 위치를 고정하여 URL·Referer·User-Agent 안의 404를 오인하지 않는다.
WEB_ERROR = re.compile(
    r'[^ \t\r\n"]{1,64} [^ \t\r\n"]{1,64} [^ \t\r\n"]{1,64} '
    r'\[[^\]\r\n]{1,64}\] '
    r'"[A-Z]{1,16} [^ \t\r\n"]{1,2048} HTTP/[0-9]\.[0-9]" '
    r'[45][0-9]{2} (?:[0-9]{1,12}|-) '
    r'"[^"\r\n]{0,2048}" "[^"\r\n]{0,2048}"'
)
SSH_FAILURE = re.compile(
    r'Failed password for (?:invalid user )?[A-Za-z0-9_.-]{1,64} '
    r'from [0-9A-Fa-f:.]{2,45} port [0-9]{1,5} ssh2'
)
CHANGE_EVENT = re.compile(r'(?:Create|Delete|Update|Put|Attach|Detach)[A-Za-z0-9]{1,80}')
ACCESS_DENIED = re.compile(r'AccessDenied(?:Exception)?|UnauthorizedOperation')
CLI_AGENT = re.compile(r'aws-cli/[0-9]+\.[0-9]+\.[0-9]+(?:[ \t]|$)')
ACCOUNT_ID = re.compile(r'[0-9]{12}')
SHA256 = re.compile(r'[A-Fa-f0-9]{64}')

WEB_LINES = [
    '192.0.2.10 - - [12/Sep/2026:09:00:00 +0900] "GET /missing HTTP/1.1" 404 120 "-" "Mozilla/5.0"',
    '2001:db8::10 - - [12/Sep/2026:09:00:01 +0900] "POST /api/items HTTP/1.1" 503 - "-" "training-client/1.0"',
    '192.0.2.11 - - [12/Sep/2026:09:00:02 +0900] "GET /help/404 HTTP/1.1" 200 240 "-" "client-500"',
    '192.0.2.12 - - [12/Sep/2026:09:00:03 +0900] "GET /home HTTP/1.1" 200 80 "https://example.test/404" "Mozilla/5.0"',
]
AUTH_LINES = [
    'Sep 12 09:00:00 lab sshd[101]: Failed password for invalid user trainee from 192.0.2.20 port 54321 ssh2',
    'Sep 12 09:00:01 lab sshd[102]: Failed password for learner from 2001:db8::20 port 54322 ssh2',
    'Sep 12 09:00:02 lab sshd[103]: Accepted publickey for learner from 192.0.2.20 port 54323 ssh2',
]
# AWS 필드의 역할을 학습하기 위해 필요한 항목만 남긴 합성 레코드다.
CLOUDTRAIL_TEXT = r'''
{
  "Records": [
    {
      "eventID": "training-01",
      "eventSource": "iam.amazonaws.com",
      "eventName": "CreateUser",
      "sourceIPAddress": "192.0.2.30",
      "userAgent": "aws-cli/2.0.0 Python/3.12",
      "userIdentity": {"type": "IAMUser", "accountId": "123456789012"}
    },
    {
      "eventID": "training-02",
      "eventSource": "ec2.amazonaws.com",
      "eventName": "DescribeInstances",
      "sourceIPAddress": "ec2.amazonaws.com",
      "userAgent": "ec2.amazonaws.com",
      "errorCode": "UnauthorizedOperation",
      "userIdentity": {"type": "AWSService"}
    },
    {
      "eventID": "training-03",
      "eventSource": "iam.amazonaws.com",
      "eventName": "ListUsers",
      "sourceIPAddress": "2001:db8::30",
      "userAgent": "training-client/1.0",
      "errorCode": "AccessDeniedException",
      "requestParameters": {"description": "CreateUser is mentioned here"},
      "userIdentity": {"type": "IAMUser", "accountId": "123456789012"}
    },
    {
      "eventID": "training-04",
      "eventSource": "cloudtrail.amazonaws.com",
      "eventName": "StopLogging",
      "sourceIPAddress": "AWS Internal/1",
      "userAgent": null,
      "userIdentity": {"type": "AssumedRole"}
    }
  ]
}
'''


def is_web_error(line: str) -> bool:
    """길이 제한 안의 학습용 로그 행을 확인한다."""
    if not isinstance(line, str):
        raise TypeError("로그는 문자열이어야 한다")
    if len(line) > 8192:
        raise ValueError("교육용 행 길이 제한 초과")
    return WEB_ERROR.fullmatch(line.rstrip("\r\n")) is not None


def find_ssh_failure(line: str) -> str | None:
    """sshd 접두부 다음의 메시지 전체가 지정 형식인지 확인한다."""
    if not isinstance(line, str):
        raise TypeError("로그는 문자열이어야 한다")
    if len(line) > 8192:
        raise ValueError("교육용 행 길이 제한 초과")
    prefix, separator, message = line.rstrip("\r\n").partition(": ")
    if not separator or re.search(r'\bsshd\[[0-9]{1,10}\]$', prefix) is None:
        return None
    match = SSH_FAILURE.fullmatch(message)
    return match.group(0) if match is not None else None


def event_text(event: dict, field: str) -> str:
    """누락·null 필드는 빈 값으로 다루고 다른 자료형은 구분한다."""
    value = event.get(field)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError(f"{field}는 문자열이어야 한다")
    if len(value) > 4096:
        raise ValueError(f"{field}가 교육용 길이 제한을 넘었다")
    return value


def load_events(text: str) -> list[dict]:
    """수업용 Records JSON 문서만 읽는다. JSONL·압축 해제는 별도 단계다."""
    if len(text.encode("utf-8")) > 1024 * 1024:
        raise ValueError("교육용 JSON 크기 제한 초과")
    payload = json.loads(text)
    if not isinstance(payload, dict) or not isinstance(payload.get("Records"), list):
        raise ValueError("Records 배열이 필요하다")
    if not all(isinstance(event, dict) for event in payload["Records"]):
        raise ValueError("각 이벤트는 JSON 객체여야 한다")
    return payload["Records"]


def classify_cloudtrail(event: dict) -> dict:
    """정규식 후보와 서비스별 정확한 이벤트 확인을 구분한다."""
    name = event_text(event, "eventName")
    source = event_text(event, "eventSource")
    address = event_text(event, "sourceIPAddress")
    error = event_text(event, "errorCode")
    agent = event_text(event, "userAgent")
    try:
        address_type = f"IPv{ipaddress.ip_address(address).version}"
    except ValueError:
        # 서비스 이름·AWS Internal 표기·누락·잘못된 IP 모두 원인을 후속 분류한다.
        address_type = "IP로 해석되지 않음"
    return {
        "event_id": event_text(event, "eventID"),
        "name": name,
        "change_name_candidate": CHANGE_EVENT.fullmatch(name) is not None,
        "review_event": (source, name) in {
            ("cloudtrail.amazonaws.com", "StopLogging"),
            ("iam.amazonaws.com", "CreateAccessKey"),
        },
        "access_denied_candidate": ACCESS_DENIED.fullmatch(error) is not None,
        "cli_version_prefix": CLI_AGENT.match(agent) is not None,
        "source_kind": address_type,
    }


def summarize() -> dict:
    return {
        "web_error_lines": [i for i, line in enumerate(WEB_LINES, 1) if is_web_error(line)],
        "ssh_failure_lines": [i for i, line in enumerate(AUTH_LINES, 1) if find_ssh_failure(line)],
        "cloudtrail": [classify_cloudtrail(event) for event in load_events(CLOUDTRAIL_TEXT)],
    }


if __name__ == "__main__":
    print(json.dumps(summarize(), ensure_ascii=False, indent=2))
