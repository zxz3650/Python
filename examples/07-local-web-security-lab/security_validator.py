"""로컬 전용 학습용 HTTP 서비스를 검증하고 JSON 보고서를 작성한다."""

from __future__ import annotations

import argparse
import ipaddress
import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests

CONNECT_TIMEOUT = 2.0
READ_TIMEOUT = 3.0
MAX_RESPONSE_BYTES = 1_048_576
EXPECTED_SECURITY_HEADERS = {
    "Content-Security-Policy": "브라우저 콘텐츠 출처 정책",
    "X-Content-Type-Options": "MIME 추측 방지 정책",
    "Referrer-Policy": "참조 정보 전달 정책",
}
ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1"}


def validate_loopback_url(base_url: str) -> tuple[str, int, str]:
    parts = urlsplit(base_url)
    if parts.scheme != "http":
        raise ValueError("학습용 URL은 http scheme만 허용합니다")
    if not parts.hostname:
        raise ValueError("URL에 호스트가 필요합니다")
    if parts.username or parts.password:
        raise ValueError("URL에 사용자정보를 포함할 수 없습니다")
    if parts.query or parts.fragment:
        raise ValueError("기준 URL에는 query나 fragment를 포함할 수 없습니다")
    if parts.path not in ("", "/"):
        raise ValueError("기준 URL의 path는 비워 두어야 합니다")

    hostname = parts.hostname.lower()
    if hostname not in ALLOWED_HOSTS:
        raise ValueError("외부 호스트는 허용하지 않습니다: localhost만 사용하세요")

    port = parts.port or 80
    addresses = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    resolved = {item[4][0] for item in addresses}
    if not resolved or not all(ipaddress.ip_address(address).is_loopback for address in resolved):
        raise ValueError("외부 주소는 허용하지 않습니다: loopback 대상만 사용하세요")

    url_host = f"[{hostname}]" if ":" in hostname else hostname
    normalized = f"http://{url_host}:{port}"
    return hostname, port, normalized


def result(check: str, status: str, evidence: str) -> dict[str, str]:
    return {"check": check, "status": status, "evidence": evidence}


def check_tcp_connection(host: str, port: int) -> dict[str, str]:
    try:
        with socket.create_connection((host, port), timeout=CONNECT_TIMEOUT):
            return result("tcp_connection", "pass", f"connected to {host}:{port}")
    except OSError as error:
        return result("tcp_connection", "fail", f"{type(error).__name__}: {error}")


def read_limited(response: requests.Response) -> bytes:
    chunks: list[bytes] = []
    size = 0
    for chunk in response.iter_content(8192):
        if not chunk:
            continue
        size += len(chunk)
        if size > MAX_RESPONSE_BYTES:
            raise ValueError("response exceeds the 1 MiB limit")
        chunks.append(chunk)
    return b"".join(chunks)


def request_limited(session: requests.Session, url: str) -> tuple[requests.Response, bytes]:
    response = session.get(
        url,
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        allow_redirects=False,
        stream=True,
    )
    try:
        return response, read_limited(response)
    except Exception:
        response.close()
        raise


def check_health(session: requests.Session, base_url: str) -> dict[str, str]:
    try:
        response, body = request_limited(session, base_url + "/health")
        content_type = response.headers.get("Content-Type", "").lower()
        if response.status_code != 200:
            return result("health_api", "fail", f"expected 200, got {response.status_code}")
        if "application/json" not in content_type:
            return result("health_api", "fail", f"unexpected Content-Type: {content_type}")
        data = json.loads(body.decode(response.encoding or "utf-8"))
        if not isinstance(data, dict) or data.get("status") != "ok":
            return result("health_api", "fail", "JSON contract does not contain status=ok")
        return result("health_api", "pass", "200 JSON response contains status=ok")
    except (requests.RequestException, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return result("health_api", "fail", f"{type(error).__name__}: {error}")


def check_security_headers(session: requests.Session, base_url: str) -> dict[str, str]:
    try:
        response, _ = request_limited(session, base_url + "/headers")
        missing = [name for name in EXPECTED_SECURITY_HEADERS if name not in response.headers]
        if missing:
            return result("security_headers", "warning", "missing: " + ", ".join(missing))
        return result("security_headers", "pass", "all expected training headers are present")
    except (requests.RequestException, ValueError) as error:
        return result("security_headers", "fail", f"{type(error).__name__}: {error}")


def check_redirect(session: requests.Session, base_url: str) -> dict[str, str]:
    try:
        response, _ = request_limited(session, base_url + "/redirect")
        if response.status_code not in {301, 302, 303, 307, 308}:
            return result("redirect_origin", "fail", f"unexpected status: {response.status_code}")
        location = response.headers.get("Location")
        if not location:
            return result("redirect_origin", "fail", "Location header is missing")

        target = urlsplit(urljoin(base_url + "/", location))
        source = urlsplit(base_url)
        target_port = target.port or (80 if target.scheme == "http" else 443)
        source_port = source.port or (80 if source.scheme == "http" else 443)
        same_origin = (
            target.scheme == source.scheme
            and target.hostname == source.hostname
            and target_port == source_port
        )
        if not same_origin:
            return result("redirect_origin", "fail", f"cross-origin redirect: {target.geturl()}")
        return result("redirect_origin", "pass", f"same-origin redirect: {target.geturl()}")
    except (requests.RequestException, ValueError) as error:
        return result("redirect_origin", "fail", f"{type(error).__name__}: {error}")


def run_validation(base_url: str) -> dict[str, Any]:
    host, port, normalized = validate_loopback_url(base_url)
    checks = [check_tcp_connection(host, port)]

    with requests.Session() as session:
        session.trust_env = False
        session.headers.update({"User-Agent": "python-basic-local-validator/1.0"})
        checks.extend(
            [
                check_health(session, normalized),
                check_security_headers(session, normalized),
                check_redirect(session, normalized),
            ]
        )

    return {
        "target": normalized,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "scope": "loopback-only training lab",
        "summary": {
            name: sum(item["status"] == name for item in checks)
            for name in ("pass", "warning", "fail")
        },
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the local HTTP training server")
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8080")
    parser.add_argument("--output", type=Path, default=Path("web-security-report.json"))
    args = parser.parse_args()

    try:
        report = run_validation(args.base_url)
    except (OSError, ValueError) as error:
        parser.error(str(error))

    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
