"""Local-only HTTP training server for chapter 07."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

HOST = "127.0.0.1"
DEFAULT_PORT = 8080
MAX_ECHO_LENGTH = 200


class TrainingHandler(BaseHTTPRequestHandler):
    server_version = "PythonBasicLab/1.0"

    def _send_json(
        self,
        status: int,
        payload: dict[str, object],
        *,
        security_headers: bool = True,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if security_headers:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'")
            self.send_header("Referrer-Policy", "no-referrer")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 - HTTP handler API name
        parts = urlsplit(self.path)

        if parts.path == "/health":
            self._send_json(200, {"status": "ok", "service": "python-basic-lab"})
            return

        if parts.path == "/api/echo":
            text = parse_qs(parts.query, keep_blank_values=True).get("text", [""])[0]
            if len(text) > MAX_ECHO_LENGTH:
                self._send_json(400, {"error": "text is too long"})
                return
            self._send_json(200, {"text": text, "length": len(text)})
            return

        if parts.path == "/headers":
            # Intentionally omits the chapter's expected security headers.
            self._send_json(
                200,
                {"purpose": "header validation exercise"},
                security_headers=False,
            )
            return

        if parts.path == "/redirect":
            self._send_json(
                302,
                {"message": "redirect to health"},
                extra_headers={"Location": "/health"},
            )
            return

        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - HTTP handler API name
        self._send_json(
            405,
            {"error": "method not allowed"},
            extra_headers={"Allow": "GET"},
        )

    def log_message(self, format: str, *args: object) -> None:
        # Avoid reflecting request-controlled text in this small training lab.
        print(f"{self.client_address[0]} - {self.command} request completed")


def create_server(port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((HOST, port), TrainingHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local HTTP training server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    with create_server(args.port) as server:
        print(f"Training server: http://{HOST}:{server.server_port}")
        print("Press Ctrl+C to stop")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")


if __name__ == "__main__":
    main()
