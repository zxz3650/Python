"""Turn the chapter 07 loopback HTTP validator into an automation-friendly CLI."""

from __future__ import annotations

import argparse
import ipaddress
import json
import logging
import os
import socket
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Mapping, Sequence
from urllib.parse import urljoin, urlsplit

import requests

EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_USAGE = 2
EXIT_RUNTIME = 3

MAX_RESPONSE_BYTES = 1_048_576
EXPECTED_SECURITY_HEADERS = (
    "content-security-policy",
    "x-content-type-options",
    "referrer-policy",
)
ALLOWED_CONFIG_KEYS = {"target", "output", "timeout", "log_level", "log_file"}
ENVIRONMENT_KEYS = {
    "target": "PYTHON_BASIC_TARGET",
    "output": "PYTHON_BASIC_OUTPUT",
    "timeout": "PYTHON_BASIC_TIMEOUT",
    "log_level": "PYTHON_BASIC_LOG_LEVEL",
    "log_file": "PYTHON_BASIC_LOG_FILE",
}
DEFAULTS: dict[str, object] = {
    "target": "http://127.0.0.1:8080",
    "output": "artifacts/web-security-report.json",
    "timeout": 3.0,
    "log_level": "INFO",
    "log_file": "artifacts/http-tool.log",
}
LOGGER = logging.getLogger("local_http_tool")


class SettingsError(ValueError):
    """Raised when configuration cannot form a safe, usable setting set."""


@dataclass(frozen=True)
class Settings:
    target: str
    output: Path
    timeout: float
    log_level: str
    log_file: Path
    dry_run: bool = False


@dataclass(frozen=True)
class HttpResponseData:
    status_code: int
    headers: dict[str, str]
    body: bytes


def positive_timeout(value: object) -> float:
    if isinstance(value, bool):
        raise SettingsError("timeout must be a number, not a boolean")
    try:
        timeout = float(value)
    except (TypeError, ValueError) as error:
        raise SettingsError("timeout must be a number") from error
    if not 0 < timeout <= 30:
        raise SettingsError("timeout must be greater than 0 and at most 30 seconds")
    return timeout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate only the chapter 07 loopback HTTP training server",
    )
    parser.add_argument("--config", type=Path, help="JSON settings file")
    parser.add_argument("--target", help="loopback base URL")
    parser.add_argument("--output", type=Path, help="JSON report path")
    parser.add_argument(
        "--timeout",
        type=float,
        help="connection and read-inactivity timeout in seconds",
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="minimum log level",
    )
    parser.add_argument("--log-file", type=Path, help="execution log path")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="use DEBUG logging without changing the settings file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and show the plan without HTTP requests or file writes",
    )
    return parser


def load_json_config(path: Path | None) -> dict[str, object]:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SettingsError(f"config file does not exist: {path}") from error
    except OSError as error:
        raise SettingsError(f"config file cannot be read: {path}") from error
    except json.JSONDecodeError as error:
        raise SettingsError(
            f"config JSON is invalid at line {error.lineno}, column {error.colno}"
        ) from error

    if not isinstance(data, dict):
        raise SettingsError("config root must be a JSON object")
    unknown = sorted(set(data) - ALLOWED_CONFIG_KEYS)
    if unknown:
        raise SettingsError("unsupported config keys: " + ", ".join(unknown))
    return data


def environment_settings(environ: Mapping[str, str]) -> dict[str, object]:
    """Read only the documented non-secret variables, never the whole environment."""
    return {
        setting: environ[name]
        for setting, name in ENVIRONMENT_KEYS.items()
        if name in environ and environ[name] != ""
    }


def resolve_settings(
    args: argparse.Namespace,
    environ: Mapping[str, str],
) -> Settings:
    """Resolve values using CLI > environment > JSON > defaults."""
    values = dict(DEFAULTS)
    values.update(load_json_config(args.config))
    values.update(environment_settings(environ))

    cli_values = {
        "target": args.target,
        "output": args.output,
        "timeout": args.timeout,
        "log_level": args.log_level,
        "log_file": args.log_file,
    }
    values.update({key: value for key, value in cli_values.items() if value is not None})
    if args.verbose:
        values["log_level"] = "DEBUG"

    target = values["target"]
    output = values["output"]
    log_file = values["log_file"]
    log_level = values["log_level"]
    if not isinstance(target, str) or not target.strip():
        raise SettingsError("target must be a non-empty string")
    if not isinstance(output, (str, Path)) or not str(output).strip():
        raise SettingsError("output must be a non-empty path")
    if not isinstance(log_file, (str, Path)) or not str(log_file).strip():
        raise SettingsError("log_file must be a non-empty path")
    if not isinstance(log_level, str) or log_level.upper() not in {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
    }:
        raise SettingsError("log_level must be DEBUG, INFO, WARNING, or ERROR")

    output_path = Path(output)
    log_path = Path(log_file)
    if output_path.resolve() == log_path.resolve():
        raise SettingsError("output and log_file must use different paths")

    return Settings(
        target=target.strip(),
        output=output_path,
        timeout=positive_timeout(values["timeout"]),
        log_level=log_level.upper(),
        log_file=log_path,
        dry_run=args.dry_run,
    )


def validate_loopback_url(base_url: str) -> tuple[str, int, str]:
    """Accept only HTTP URLs whose literal host or localhost resolves to loopback."""
    try:
        parts = urlsplit(base_url)
    except ValueError as error:
        raise SettingsError("target URL is invalid") from error
    if parts.scheme != "http":
        raise SettingsError("target must use the http scheme")
    if not parts.hostname:
        raise SettingsError("target URL needs a host")
    if parts.username is not None or parts.password is not None:
        raise SettingsError("target URL must not contain user information")
    if parts.query or parts.fragment:
        raise SettingsError("target base URL must not contain a query or fragment")
    if parts.path not in ("", "/"):
        raise SettingsError("target base URL path must be empty")
    try:
        parsed_port = parts.port
    except ValueError as error:
        raise SettingsError("target URL contains an invalid port") from error
    if parsed_port == 0:
        raise SettingsError("target port must be between 1 and 65535")
    port = 80 if parsed_port is None else parsed_port

    host = parts.hostname.lower()
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        if host != "localhost":
            raise SettingsError("only localhost or a loopback IP address is allowed")
        try:
            addresses = {
                item[4][0]
                for item in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            }
        except OSError as error:
            raise SettingsError("localhost could not be resolved") from error
        resolved_addresses = {ipaddress.ip_address(address) for address in addresses}
        if not resolved_addresses or not all(
            address.is_loopback for address in resolved_addresses
        ):
            raise SettingsError("localhost resolved outside the loopback range")
        selected = min(
            resolved_addresses,
            key=lambda address: (address.version != 4, int(address)),
        )
        connection_host = selected.compressed
    else:
        if not literal.is_loopback:
            raise SettingsError("only a loopback IP address is allowed")
        connection_host = literal.compressed

    url_host = f"[{connection_host}]" if ":" in connection_host else connection_host
    return connection_host, port, f"http://{url_host}:{port}"


def configure_logging(level: str, path: Path) -> None:
    """Configure event-only logs; callers never pass headers, bodies, or environment."""
    path.parent.mkdir(parents=True, exist_ok=True)
    for handler in LOGGER.handlers[:]:
        LOGGER.removeHandler(handler)
        handler.close()

    LOGGER.setLevel(level)
    LOGGER.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    LOGGER.addHandler(stream_handler)

    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    LOGGER.addHandler(file_handler)


def result(check: str, status: str, evidence: str) -> dict[str, str]:
    return {"check": check, "status": status, "evidence": evidence}


def check_tcp_connection(host: str, port: int, timeout: float) -> dict[str, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return result("tcp_connection", "pass", "loopback TCP connection succeeded")
    except OSError as error:
        return result(
            "tcp_connection",
            "fail",
            f"connection failed ({type(error).__name__})",
        )


def request_limited(
    session: requests.Session,
    url: str,
    timeout: float,
) -> HttpResponseData:
    with session.get(
        url,
        timeout=(timeout, timeout),
        allow_redirects=False,
        stream=True,
    ) as response:
        chunks: list[bytes] = []
        size = 0
        for chunk in response.iter_content(8192):
            if not chunk:
                continue
            size += len(chunk)
            if size > MAX_RESPONSE_BYTES:
                raise ValueError("response exceeds the 1 MiB limit")
            chunks.append(chunk)
        return HttpResponseData(
            status_code=response.status_code,
            headers={name.lower(): value for name, value in response.headers.items()},
            body=b"".join(chunks),
        )


def check_health(
    session: requests.Session,
    base_url: str,
    timeout: float,
) -> dict[str, str]:
    try:
        response = request_limited(session, base_url + "/health", timeout)
        content_type = response.headers.get("content-type", "").lower()
        if response.status_code != 200:
            return result("health_api", "fail", "health endpoint did not return 200")
        if "application/json" not in content_type:
            return result("health_api", "fail", "health response is not JSON")
        data = json.loads(response.body.decode("utf-8"))
        if not isinstance(data, dict) or data.get("status") != "ok":
            return result("health_api", "fail", "health JSON contract is not satisfied")
        return result("health_api", "pass", "health JSON contract is satisfied")
    except (requests.RequestException, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return result("health_api", "fail", f"request failed ({type(error).__name__})")


def check_security_headers(
    session: requests.Session,
    base_url: str,
    timeout: float,
) -> dict[str, str]:
    try:
        response = request_limited(session, base_url + "/headers", timeout)
        missing = [name for name in EXPECTED_SECURITY_HEADERS if name not in response.headers]
        if missing:
            return result("security_headers", "warning", "missing: " + ", ".join(missing))
        return result("security_headers", "pass", "expected training headers are present")
    except (requests.RequestException, ValueError) as error:
        return result(
            "security_headers",
            "fail",
            f"request failed ({type(error).__name__})",
        )


def check_redirect(
    session: requests.Session,
    base_url: str,
    timeout: float,
) -> dict[str, str]:
    try:
        response = request_limited(session, base_url + "/redirect", timeout)
        if response.status_code not in {301, 302, 303, 307, 308}:
            return result("redirect_origin", "fail", "redirect status was not returned")
        location = response.headers.get("location")
        if not location:
            return result("redirect_origin", "fail", "Location header is missing")

        source = urlsplit(base_url)
        target = urlsplit(urljoin(base_url + "/", location))
        source_port = source.port or 80
        target_port = target.port or (80 if target.scheme == "http" else 443)
        same_origin = (
            target.scheme == source.scheme
            and target.hostname == source.hostname
            and target_port == source_port
        )
        if not same_origin:
            return result("redirect_origin", "fail", "redirect leaves the allowed origin")
        return result("redirect_origin", "pass", "redirect stays on the allowed origin")
    except (requests.RequestException, ValueError) as error:
        return result(
            "redirect_origin",
            "fail",
            f"request failed ({type(error).__name__})",
        )


def run_validation(settings: Settings) -> dict[str, Any]:
    host, port, normalized = validate_loopback_url(settings.target)
    checks = [check_tcp_connection(host, port, settings.timeout)]

    with requests.Session() as session:
        # Ignore proxy and .netrc settings so the local-only boundary is explicit.
        session.trust_env = False
        session.headers.update({"User-Agent": "python-basic-local-tool/1.0"})
        checks.extend(
            (
                check_health(session, normalized, settings.timeout),
                check_security_headers(session, normalized, settings.timeout),
                check_redirect(session, normalized, settings.timeout),
            )
        )

    for item in checks:
        # Do not log evidence, headers, response bodies, or environment values.
        LOGGER.info("check_complete name=%s status=%s", item["check"], item["status"])

    return {
        "schema_version": 1,
        "target": normalized,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "scope": "loopback-only training lab",
        "summary": {
            status: sum(item["status"] == status for item in checks)
            for status in ("pass", "warning", "fail")
        },
        "checks": checks,
    }


def write_json_report(report: Mapping[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(
                report,
                temporary,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())

        with temporary_path.open("r", encoding="utf-8") as saved:
            restored = json.load(saved)
        if not isinstance(restored, dict) or "summary" not in restored:
            raise ValueError("report does not satisfy the required JSON structure")

        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def dry_run_plan(settings: Settings, normalized_target: str) -> dict[str, object]:
    return {
        "mode": "dry-run",
        "target": normalized_target,
        "output": str(settings.output),
        "log_file": str(settings.log_file),
        "timeout": settings.timeout,
        "log_level": settings.log_level,
        "http_requests_sent": False,
        "tcp_connections_opened": False,
        "files_written": False,
    }


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = resolve_settings(args, os.environ if environ is None else environ)
        _, _, normalized = validate_loopback_url(settings.target)
    except SettingsError as error:
        print(f"configuration error: {error}", file=sys.stderr)
        return EXIT_USAGE

    if settings.dry_run:
        print(json.dumps(dry_run_plan(settings, normalized), ensure_ascii=False, indent=2))
        return EXIT_OK

    try:
        configure_logging(settings.log_level, settings.log_file)
        LOGGER.info("run_started target=%s", normalized)
        report = run_validation(replace(settings, target=normalized))
        write_json_report(report, settings.output)
        LOGGER.info(
            "run_finished pass=%d warning=%d fail=%d",
            report["summary"]["pass"],
            report["summary"]["warning"],
            report["summary"]["fail"],
        )
    except (OSError, TypeError, ValueError) as error:
        print(f"runtime error: {type(error).__name__}", file=sys.stderr)
        return EXIT_RUNTIME

    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"Report: {settings.output}")
    return EXIT_CHECK_FAILED if report["summary"]["fail"] else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
