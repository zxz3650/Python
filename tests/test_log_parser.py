from python_basic.log_parser import analyze_auth_log, parse_auth_line


def test_parse_auth_line():
    record = parse_auth_line("2026-08-10T10:00:00Z DENY bob 198.51.100.9 /admin")
    assert record["user"] == "bob"
    assert record["action"] == "DENY"


def test_analyze_preserves_invalid_rows():
    text = """2026-08-10T10:00:00Z DENY bob 198.51.100.9 /admin
BROKEN LINE
2026-08-10T10:00:02Z DENY bob 198.51.100.9 /login
"""
    result = analyze_auth_log(text, threshold=2)
    assert result["valid_events"] == 2
    assert result["error_lines"] == [2]
    assert result["suspicious_users"] == {"bob": 2}


def test_invalid_ip_is_rejected():
    try:
        parse_auth_line("2026-08-10T10:00:00Z DENY bob 198.51.100.999 /admin")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid IP must be rejected")

