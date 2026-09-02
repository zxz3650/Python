"""03-9 학습자용 로컬 인증 실습 보조 함수.

HTTP 구현은 제공 코드가 담당한다. 학습자는 반환된 리스트와 딕셔너리를
조건문, 반복문, 함수로 처리한다. 대상 주소는 loopback으로 고정되어 있다.
"""

from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 2


def _get_json(path: str, *, blue_token: str | None = None) -> dict:
    headers = {}
    if blue_token is not None:
        headers["X-Blue-Token"] = blue_token

    request = Request(f"{BASE_URL}{path}", headers=headers, method="GET")
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def get_challenge() -> dict:
    """후보 계정, 후보 비밀번호, 최대 시도 횟수를 반환한다."""
    return _get_json("/api/challenge")


def attempt_login(username: str, password: str, source: str = "red-lab-01") -> dict:
    """제공된 localhost 실습 서버에 인증 시도 한 건을 보낸다."""
    query = urlencode(
        {
            "username": username,
            "password": password,
            "source": source,
        }
    )
    return _get_json(f"/api/login?{query}")


def get_events(blue_token: str) -> list[dict]:
    """블루팀 토큰으로 비밀번호가 제외된 인증 이벤트를 반환한다."""
    payload = _get_json("/api/events", blue_token=blue_token)
    return payload["events"]
