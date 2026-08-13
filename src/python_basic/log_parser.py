from __future__ import annotations

from collections import Counter
from datetime import datetime
from ipaddress import ip_address


def parse_auth_line(line: str) -> dict[str, str]:
    parts = line.split()
    if len(parts) != 5:
        raise ValueError(f"expected 5 fields, got {len(parts)}")

    timestamp, action, user, ip, path = parts
    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if action not in {"ALLOW", "DENY"}:
        raise ValueError(f"unknown action: {action}")
    if not user or len(user) > 64:
        raise ValueError("invalid user")
    ip_address(ip)
    if not path.startswith("/"):
        raise ValueError("path must start with '/'")
    return {"time": timestamp, "action": action, "user": user, "ip": ip, "path": path}


def analyze_auth_log(text: str, threshold: int = 3) -> dict:
    records: list[dict[str, str]] = []
    errors: list[dict[str, object]] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(parse_auth_line(line))
        except ValueError as exc:
            errors.append({"line": line_number, "raw": line, "error": str(exc)})

    denied = [record for record in records if record["action"] == "DENY"]
    by_user = Counter(record["user"] for record in denied)
    by_ip = Counter(record["ip"] for record in denied)
    times = [record["time"] for record in records]

    return {
        "valid_events": len(records),
        "parse_errors": len(errors),
        "deny_by_user": dict(by_user),
        "deny_by_ip": dict(by_ip),
        "suspicious_users": {user: count for user, count in by_user.items() if count >= threshold},
        "error_lines": [error["line"] for error in errors],
        "errors": errors,
        "time_range": {"start": min(times) if times else None, "end": max(times) if times else None},
    }

