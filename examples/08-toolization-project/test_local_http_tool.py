"""08장 도구화 프로젝트에서 실행할 수 있는 인수 테스트다."""

from __future__ import annotations

import io
import json
import tempfile
import threading
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator
from unittest import mock

import local_http_tool as tool


class TrainingHandler(BaseHTTPRequestHandler):
    def send_json(
        self,
        status: int,
        payload: dict[str, str],
        *,
        location: str | None = None,
    ) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if location is not None:
            self.send_header("Location", location)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - HTTP 처리기 API 이름
        if self.path == "/health":
            self.send_json(200, {"status": "ok"})
        elif self.path == "/headers":
            # 헤더 누락 경고가 한 건 발생하도록 의도적으로 구성한다.
            self.send_json(200, {"purpose": "header exercise"})
        elif self.path == "/redirect":
            self.send_json(302, {"status": "redirect"}, location="/health")
        else:
            self.send_json(404, {"error": "not found"})

    def log_message(self, format: str, *args: object) -> None:
        return


@contextmanager
def local_training_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), TrainingHandler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


class ToolAcceptanceTests(unittest.TestCase):
    def tearDown(self) -> None:
        for handler in tool.LOGGER.handlers[:]:
            tool.LOGGER.removeHandler(handler)
            handler.close()

    def test_external_target_is_rejected_before_validation(self) -> None:
        with mock.patch.object(tool, "run_validation") as run_validation:
            exit_code = tool.main(
                ["--target", "https://example.com"],
                environ={},
            )

        self.assertEqual(exit_code, tool.EXIT_USAGE)
        run_validation.assert_not_called()

    def test_dry_run_does_not_request_or_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            output = temp_dir / "report.json"
            log_file = temp_dir / "tool.log"

            with (
                mock.patch.object(tool, "run_validation") as run_validation,
                mock.patch.object(tool, "configure_logging") as configure_logging,
                mock.patch.object(tool, "write_json_report") as write_json_report,
                mock.patch.object(tool.socket, "create_connection") as create_connection,
                mock.patch.object(tool.requests, "Session") as session_type,
            ):
                exit_code = tool.main(
                    [
                        "--target",
                        "http://127.0.0.1:8080",
                        "--output",
                        str(output),
                        "--log-file",
                        str(log_file),
                        "--dry-run",
                    ],
                    environ={},
                )

            self.assertEqual(exit_code, tool.EXIT_OK)
            run_validation.assert_not_called()
            configure_logging.assert_not_called()
            write_json_report.assert_not_called()
            create_connection.assert_not_called()
            session_type.assert_not_called()
            self.assertFalse(output.exists())
            self.assertFalse(log_file.exists())

    def test_cli_overrides_environment_and_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "target": "http://127.0.0.1:8001",
                        "output": "from-config.json",
                        "timeout": 1,
                        "log_level": "WARNING",
                        "log_file": "from-config.log",
                    }
                ),
                encoding="utf-8",
            )
            args = tool.build_parser().parse_args(
                ["--config", str(config), "--target", "http://127.0.0.1:8003"]
            )
            settings = tool.resolve_settings(
                args,
                {
                    "PYTHON_BASIC_TARGET": "http://127.0.0.1:8002",
                    "PYTHON_BASIC_TIMEOUT": "2",
                },
            )

        self.assertEqual(settings.target, "http://127.0.0.1:8003")
        self.assertEqual(settings.timeout, 2)
        self.assertEqual(settings.output, Path("from-config.json"))

    def test_scope_rejects_credentials_query_and_port_zero(self) -> None:
        invalid_targets = (
            "http://user:pass@127.0.0.1:8080",
            "http://@127.0.0.1:8080",
            "http://127.0.0.1:8080?token=secret",
            "http://127.0.0.1:8080#secret",
            "http://127.0.0.1:0",
            "http://[::1",
        )
        for target in invalid_targets:
            with self.subTest(target=target):
                with self.assertRaises(tool.SettingsError):
                    tool.validate_loopback_url(target)

    def test_localhost_is_pinned_to_a_resolved_loopback_literal(self) -> None:
        addresses = [
            (tool.socket.AF_INET6, tool.socket.SOCK_STREAM, 6, "", ("::1", 8080, 0, 0)),
            (tool.socket.AF_INET, tool.socket.SOCK_STREAM, 6, "", ("127.0.0.1", 8080)),
        ]
        with mock.patch.object(tool.socket, "getaddrinfo", return_value=addresses):
            host, port, normalized = tool.validate_loopback_url(
                "http://localhost:8080"
            )

        self.assertEqual(host, "127.0.0.1")
        self.assertEqual(port, 8080)
        self.assertEqual(normalized, "http://127.0.0.1:8080")

    def test_request_contract_disables_redirects_and_sets_timeouts(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status_code = 200
        response.headers = {"Content-Type": "application/json"}
        response.iter_content.return_value = [b'{"status":"ok"}']
        session = mock.MagicMock()
        session.get.return_value = response

        received = tool.request_limited(session, "http://127.0.0.1/health", 2.5)

        session.get.assert_called_once_with(
            "http://127.0.0.1/health",
            timeout=(2.5, 2.5),
            allow_redirects=False,
            stream=True,
        )
        self.assertEqual(received.status_code, 200)

    def test_cross_origin_redirect_is_reported_without_following_it(self) -> None:
        redirect = tool.HttpResponseData(
            status_code=302,
            headers={"location": "https://example.com/elsewhere"},
            body=b"",
        )
        with mock.patch.object(tool, "request_limited", return_value=redirect):
            observed = tool.check_redirect(
                mock.MagicMock(),
                "http://127.0.0.1:8080",
                1.0,
            )

        self.assertEqual(observed["status"], "fail")
        self.assertEqual(observed["evidence"], "redirect leaves the allowed origin")

    def test_response_size_limit_rejects_oversized_body(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status_code = 200
        response.headers = {}
        response.iter_content.return_value = [b"x" * (tool.MAX_RESPONSE_BYTES + 1)]
        session = mock.MagicMock()
        session.get.return_value = response

        with self.assertRaisesRegex(ValueError, "1 MiB"):
            tool.request_limited(session, "http://127.0.0.1/health", 1.0)

    def test_run_validation_disables_environment_inheritance(self) -> None:
        settings = tool.Settings(
            target="http://127.0.0.1:8080",
            output=Path("report.json"),
            timeout=1.0,
            log_level="INFO",
            log_file=Path("tool.log"),
        )
        session = mock.MagicMock()
        session.__enter__.return_value = session
        passed = lambda name: tool.result(name, "pass", "ok")

        with (
            mock.patch.object(tool.requests, "Session", return_value=session),
            mock.patch.object(
                tool,
                "check_tcp_connection",
                return_value=passed("tcp_connection"),
            ),
            mock.patch.object(
                tool,
                "check_health",
                return_value=passed("health_api"),
            ),
            mock.patch.object(
                tool,
                "check_security_headers",
                return_value=passed("security_headers"),
            ),
            mock.patch.object(
                tool,
                "check_redirect",
                return_value=passed("redirect_origin"),
            ),
        ):
            report = tool.run_validation(settings)

        self.assertIs(session.trust_env, False)
        session.headers.update.assert_called_once_with(
            {"User-Agent": "python-basic-local-tool/1.0"}
        )
        self.assertEqual(report["summary"], {"pass": 4, "warning": 0, "fail": 0})

    def test_settings_reject_path_collision_and_invalid_json(self) -> None:
        parser = tool.build_parser()
        collision = parser.parse_args(
            ["--output", "same-path", "--log-file", "same-path"]
        )
        with self.assertRaisesRegex(tool.SettingsError, "different paths"):
            tool.resolve_settings(collision, {})

        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "invalid.json"
            config.write_text('{"timeout":', encoding="utf-8")
            invalid = parser.parse_args(["--config", str(config)])
            with self.assertRaisesRegex(tool.SettingsError, "line 1, column"):
                tool.resolve_settings(invalid, {})

            unknown = Path(directory) / "unknown.json"
            unknown.write_text('{"unexpected": true}', encoding="utf-8")
            with self.assertRaisesRegex(tool.SettingsError, "unsupported config keys"):
                tool.load_json_config(unknown)

    def test_argparse_help_and_usage_error_use_documented_system_exit(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            tool.main(["--help"], environ={})

        self.assertEqual(raised.exception.code, tool.EXIT_OK)

        with self.assertRaises(SystemExit) as raised:
            tool.main(["--unknown-option"], environ={})

        self.assertEqual(raised.exception.code, tool.EXIT_USAGE)

    def test_failed_check_returns_exit_one_and_still_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            output = temp_dir / "report.json"
            log_file = temp_dir / "tool.log"
            failed_report = {
                "schema_version": 1,
                "summary": {"pass": 0, "warning": 0, "fail": 1},
                "checks": [],
            }

            with mock.patch.object(tool, "run_validation", return_value=failed_report):
                exit_code = tool.main(
                    [
                        "--output",
                        str(output),
                        "--log-file",
                        str(log_file),
                    ],
                    environ={},
                )

            self.assertEqual(exit_code, tool.EXIT_CHECK_FAILED)
            self.assertTrue(output.exists())

    def test_report_write_error_returns_exit_three(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_file = Path(directory) / "tool.log"
            passed_report = {
                "schema_version": 1,
                "summary": {"pass": 1, "warning": 0, "fail": 0},
                "checks": [],
            }

            with (
                mock.patch.object(tool, "run_validation", return_value=passed_report),
                mock.patch.object(
                    tool,
                    "write_json_report",
                    side_effect=OSError("simulated write failure"),
                ),
            ):
                exit_code = tool.main(
                    ["--log-file", str(log_file)],
                    environ={},
                )

            self.assertEqual(exit_code, tool.EXIT_RUNTIME)

    def test_logging_setup_error_returns_exit_three_before_validation(self) -> None:
        with (
            mock.patch.object(
                tool,
                "configure_logging",
                side_effect=OSError("simulated log failure"),
            ),
            mock.patch.object(tool, "run_validation") as run_validation,
        ):
            exit_code = tool.main([], environ={})

        self.assertEqual(exit_code, tool.EXIT_RUNTIME)
        run_validation.assert_not_called()

    def test_invalid_report_preserves_existing_output_and_cleans_temporary_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            output = temp_dir / "report.json"
            original = {"summary": {"pass": 1, "warning": 0, "fail": 0}}
            output.write_text(json.dumps(original), encoding="utf-8")

            invalid_report = {
                "summary": {"pass": 1, "warning": 0, "fail": 0},
                "not_json": object(),
            }

            with self.assertRaises(TypeError):
                tool.write_json_report(invalid_report, output)

            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                original,
            )
            self.assertEqual(
                list(temp_dir.glob(f".{output.name}.*.tmp")),
                [],
            )

    def test_local_run_writes_report_without_secret(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            output = temp_dir / "report.json"
            log_file = temp_dir / "tool.log"
            secret_marker = "never-write-this-api-token"
            environ = {"PYTHON_BASIC_API_TOKEN": secret_marker}
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                local_training_server() as target,
                redirect_stdout(stdout),
                redirect_stderr(stderr),
            ):
                exit_code = tool.main(
                    [
                        "--target",
                        target,
                        "--output",
                        str(output),
                        "--log-file",
                        str(log_file),
                        "--verbose",
                    ],
                    environ=environ,
                )

            self.assertEqual(exit_code, tool.EXIT_OK)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                report["summary"],
                {"pass": 3, "warning": 1, "fail": 0},
            )
            self.assertEqual(report["schema_version"], 1)

            persisted_text = output.read_text(encoding="utf-8") + log_file.read_text(
                encoding="utf-8"
            )
            self.assertNotIn(secret_marker, persisted_text)
            self.assertNotIn("header exercise", persisted_text)
            self.assertNotIn(secret_marker, stdout.getvalue())
            self.assertNotIn(secret_marker, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
