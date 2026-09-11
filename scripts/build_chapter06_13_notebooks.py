"""01~02장과 06~13장 예제용 Jupyter Notebook을 생성하고 실행 검증한다."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from io import StringIO
import json
from pathlib import Path
import re
import sys
import traceback
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


@dataclass(frozen=True)
class NotebookSpec:
    filename: str
    title: str
    goals: tuple[str, ...]
    setup: str
    step_title: str
    step_text: str
    example: str
    check_text: str
    checks: str
    next_steps: str


def lines(text: str) -> list[str]:
    """Notebook source 필드에 넣을 줄 목록을 만든다."""
    normalized = text.strip("\n") + "\n"
    return normalized.splitlines(keepends=True)


def markdown_cell(source: str, index: int) -> dict:
    return {
        "cell_type": "markdown",
        "id": f"cell-{index:03d}",
        "metadata": {},
        "source": lines(source),
    }


def code_cell(source: str, index: int) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": f"cell-{index:03d}",
        "metadata": {},
        "outputs": [],
        "source": lines(source),
    }


def notebook_for(spec: NotebookSpec) -> dict:
    goals = "\n".join(f"- {goal}" for goal in spec.goals)
    cells = [
        markdown_cell(
            f"# {spec.title}\n\n## Goal\n\n{goals}\n\n"
            "이 노트북은 교안 예제를 안전하게 재현하는 보조 실습입니다. 먼저 결과를 예측한 뒤 셀을 실행하세요.",
            1,
        ),
        markdown_cell(f"## Setup\n\n{spec.setup}", 2),
        markdown_cell(f"## Steps\n\n### {spec.step_title}\n\n{spec.step_text}", 3),
        code_cell(spec.example, 4),
        markdown_cell(f"## Checks\n\n{spec.check_text}", 5),
        code_cell(spec.checks, 6),
        markdown_cell(f"## Next Steps\n\n{spec.next_steps}", 7),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.10+"},
            "course": {
                "chapter": spec.filename.split("-")[0],
                "mode": "example",
                "network_access": False,
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def execute_notebook(notebook: dict, filename: str) -> None:
    """표준 Python으로 코드 셀을 순서대로 실행하고 stdout을 저장한다."""
    module_name = "_course_notebook_" + re.sub(r"\W+", "_", filename)
    module = ModuleType(module_name)
    module.__file__ = filename
    sys.modules[module_name] = module
    namespace = module.__dict__
    execution_count = 0
    failures = []
    try:
        for cell in notebook["cells"]:
            if cell["cell_type"] != "code":
                continue
            execution_count += 1
            cell["execution_count"] = execution_count
            stdout = StringIO()
            stderr = StringIO()
            source = "".join(cell["source"])
            try:
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    exec(compile(source, f"{filename}:cell-{execution_count}", "exec"), namespace)
            except Exception as error:  # 생성 검증 실패를 Notebook 오류 출력과 빌드 실패로 함께 남긴다.
                failures.append((execution_count, error))
                cell["outputs"].append(
                    {
                        "ename": type(error).__name__,
                        "evalue": str(error),
                        "output_type": "error",
                        "traceback": traceback.format_exc().splitlines(),
                    }
                )
            for name, stream in (("stdout", stdout), ("stderr", stderr)):
                value = stream.getvalue()
                if value:
                    cell["outputs"].append(
                        {"name": name, "output_type": "stream", "text": value.splitlines(keepends=True)}
                    )
    finally:
        sys.modules.pop(module_name, None)
    if failures:
        summary = ", ".join(f"셀 {number}: {type(error).__name__}: {error}" for number, error in failures)
        raise RuntimeError(f"{filename} 실행 실패 — {summary}")


def specs() -> list[NotebookSpec]:
    return [
        NotebookSpec(
            "01-python-first-step.ipynb",
            "01. Python 첫 실행 예제",
            ("입력·처리·검증·출력 흐름을 한 번에 확인합니다.", "실행 전에 결과를 예측하고 assert로 다시 검증합니다."),
            "Python 표준 라이브러리만 사용하며 파일이나 네트워크를 변경하지 않습니다.",
            "작은 이벤트 목록 집계",
            "로그인 결과 문자열을 하나씩 확인해 실패 횟수를 집계합니다.",
            '''events = ["LOGIN_OK", "LOGIN_FAIL", "LOGIN_FAIL"]
failure_count = 0

for event in events:
    if event == "LOGIN_FAIL":
        failure_count += 1

summary = {"total": len(events), "login_failures": failure_count}
print(summary)''',
            "입력 건수와 실패 건수가 예상과 같은지 확인합니다.",
            '''assert summary["total"] == 3
assert summary["login_failures"] == 2
assert summary["login_failures"] <= summary["total"]
print("첫 Python 예제 검사 통과")''',
            "이벤트를 추가하거나 이름을 바꾼 뒤 예상 결과도 먼저 적고 다시 실행합니다.",
        ),
        NotebookSpec(
            "02-environment-check.ipynb",
            "02. 개발 및 실습 환경 점검",
            ("Notebook 커널의 Python 버전을 확인합니다.", "표준 모듈과 과정용 외부 패키지의 설치 상태를 구분합니다."),
            "이 노트북을 과정용 가상환경의 Jupyter 커널에서 실행합니다. 설치 작업은 수행하지 않습니다.",
            "현재 커널과 패키지 상태 확인",
            "Python 3.10 이상인지 검사하고, 과정에서 사용하는 패키지를 변경 없이 조회합니다.",
            '''from importlib.util import find_spec
import sys


minimum_version = (3, 10)
python_version = (sys.version_info.major, sys.version_info.minor)
standard_modules = ("json", "pathlib", "socket", "unittest")
course_packages = ("pytest", "numpy", "pandas", "requests", "jupyterlab", "ipykernel")

environment = {
    "python": ".".join(map(str, python_version)),
    "supported": python_version >= minimum_version,
}
package_status = {name: find_spec(name) is not None for name in course_packages}

print(environment)
print("과정 패키지:", package_status)''',
            "지원 버전과 표준 라이브러리를 검사합니다. 외부 패키지 누락은 설치 명령을 안내하기 위한 정보로 남깁니다.",
            '''assert environment["supported"], "Python 3.10 이상이 필요합니다"
assert all(find_spec(name) is not None for name in standard_modules)

missing_packages = [name for name, installed in package_status.items() if not installed]
print("미설치 과정 패키지:", missing_packages or "없음")
print("환경 기본 검사 통과")''',
            "패키지가 누락됐다면 Notebook 셀에서 설치하지 말고, 가상환경을 활성화한 터미널에서 `python -m pip install -r requirements.txt`를 실행합니다.",
        ),
        NotebookSpec(
            "06-1-network-socket-basics.ipynb",
            "06-1. 네트워크와 소켓 기초 예제",
            ("IP 주소와 포트를 하나의 엔드포인트로 검증합니다.", "주소 체계와 소켓 종류를 구분합니다."),
            "Python 표준 라이브러리만 사용하며 외부 네트워크에 연결하지 않습니다.",
            "루프백 엔드포인트 검증",
            "포트의 자료형과 범위를 먼저 확인하고, 학습 대상 주소를 루프백으로 제한합니다.",
            '''from dataclasses import dataclass
import ipaddress
import socket


@dataclass(frozen=True)
class Endpoint:
    host: str
    port: int
    family: socket.AddressFamily


def validate_endpoint(host: str, port: int) -> Endpoint:
    if not isinstance(host, str) or not host:
        raise TypeError("host는 비어 있지 않은 문자열이어야 합니다")
    if isinstance(port, bool) or not isinstance(port, int):
        raise TypeError("port는 정수여야 합니다")
    if not 1 <= port <= 65535:
        raise ValueError("port는 1~65535 범위여야 합니다")
    address = ipaddress.ip_address(host)
    if not address.is_loopback:
        raise ValueError("이 실습은 루프백 주소만 허용합니다")
    family = socket.AF_INET6 if address.version == 6 else socket.AF_INET
    return Endpoint(str(address), port, family)


endpoint = validate_endpoint("127.0.0.1", 9000)
print(endpoint)
print("주소 체계:", endpoint.family.name)
print("스트림 소켓:", socket.SocketKind.SOCK_STREAM.name)''',
            "정상값과 경계값을 검증합니다. `bool`은 `int`의 하위형이므로 별도로 거부합니다.",
            '''assert validate_endpoint("::1", 443).family == socket.AF_INET6
for bad_port in (True, 0, 65536):
    try:
        validate_endpoint("127.0.0.1", bad_port)
    except (TypeError, ValueError):
        pass
    else:
        raise AssertionError(f"거부되지 않은 포트: {bad_port!r}")
print("경계값 검사 통과")''',
            "실제 TCP 연결은 06-2와 06-3의 클라이언트·서버 파일에서 수행합니다.",
        ),
        NotebookSpec(
            "06-2-tcp-client.ipynb",
            "06-2. TCP 클라이언트 예제",
            ("`recv()` 한 번이 전체 메시지를 보장하지 않는 이유를 확인합니다.", "연결 종료를 불완전 수신과 구분합니다."),
            "가짜 소켓으로 부분 수신을 재현하므로 포트를 열지 않습니다.",
            "필요한 길이만큼 반복 수신",
            "수신 조각이 작더라도 목표 바이트 수가 모일 때까지 반복합니다.",
            '''class ScriptedSocket:
    def __init__(self, chunks):
        self.chunks = list(chunks)

    def recv(self, size):
        if not self.chunks:
            return b""
        chunk = self.chunks.pop(0)
        if len(chunk) > size:
            self.chunks.insert(0, chunk[size:])
            return chunk[:size]
        return chunk


def receive_exactly(sock, size: int) -> bytes:
    if size < 0:
        raise ValueError("size는 0 이상이어야 합니다")
    result = bytearray()
    while len(result) < size:
        chunk = sock.recv(size - len(result))
        if not chunk:
            raise ConnectionError("메시지 수신 전에 연결이 종료되었습니다")
        result.extend(chunk)
    return bytes(result)


client_socket = ScriptedSocket([b"HE", b"L", b"LO"])
message = receive_exactly(client_socket, 5)
print(message, message.decode("ascii"))''',
            "부분 수신과 조기 종료를 각각 확인합니다.",
            '''assert message == b"HELLO"
try:
    receive_exactly(ScriptedSocket([b"AB"]), 3)
except ConnectionError as error:
    print("예상한 오류:", error)
else:
    raise AssertionError("조기 종료를 발견하지 못했습니다")''',
            "실제 클라이언트에서는 연결 타임아웃과 읽기 타임아웃을 모두 설정합니다.",
        ),
        NotebookSpec(
            "06-3-tcp-server.ipynb",
            "06-3. TCP 서버 예제",
            ("요청 한 건을 처리하는 서버 경계를 분리합니다.", "서버와 클라이언트의 자원 정리를 확인합니다."),
            "`socketpair()`로 현재 프로세스 안에서만 통신하며 외부 포트를 열지 않습니다.",
            "한 요청 처리 함수 실행",
            "서버 역할은 바이트 수 제한을 적용한 뒤 응답을 전송하고 소켓을 닫습니다.",
            '''import socket
import threading


def serve_once(server_socket: socket.socket, max_bytes: int = 64) -> None:
    try:
        request = server_socket.recv(max_bytes + 1)
        if len(request) > max_bytes:
            server_socket.sendall(b"ERROR:too-large")
            return
        server_socket.sendall(b"ACK:" + request.upper())
    finally:
        server_socket.close()


server_side, client_side = socket.socketpair()
worker = threading.Thread(target=serve_once, args=(server_side,), daemon=True)
worker.start()
with client_side:
    client_side.sendall(b"hello")
    response = client_side.recv(128)
worker.join(timeout=1)
print(response.decode("ascii"))''',
            "응답과 스레드 종료 상태를 검증합니다.",
            '''assert response == b"ACK:HELLO"
assert not worker.is_alive()
assert response.startswith(b"ACK:")
print("서버 경계 검사 통과")''',
            "실제 `bind()`·`listen()`·`accept()` 흐름은 `examples/06-network-echo/echo_server.py`에서 확인합니다.",
        ),
        NotebookSpec(
            "06-4-message-framing.ipynb",
            "06-4. 메시지 경계와 프로토콜 설계 예제",
            ("길이 접두사 프레임을 구성합니다.", "완전한 프레임과 남은 바이트를 분리합니다."),
            "네트워크 바이트 순서의 4바이트 길이 필드를 사용합니다.",
            "길이 접두사 인코딩과 디코딩",
            "TCP 바이트 흐름에서 메시지 경계를 직접 표현합니다.",
            '''import struct

HEADER_SIZE = 4
MAX_PAYLOAD = 1024


def encode_frame(text: str) -> bytes:
    payload = text.encode("utf-8")
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload가 너무 큽니다")
    return struct.pack("!I", len(payload)) + payload


def decode_one(buffer: bytes):
    if len(buffer) < HEADER_SIZE:
        return None, buffer
    size = struct.unpack("!I", buffer[:HEADER_SIZE])[0]
    if size > MAX_PAYLOAD:
        raise ValueError("선언한 payload 크기가 제한을 초과했습니다")
    end = HEADER_SIZE + size
    if len(buffer) < end:
        return None, buffer
    return buffer[HEADER_SIZE:end].decode("utf-8"), buffer[end:]


stream = encode_frame("첫째") + encode_frame("둘째")
first, remainder = decode_one(stream)
second, remainder = decode_one(remainder)
print(first, second, "남은 바이트:", len(remainder))''',
            "한글의 문자 수와 UTF-8 바이트 수가 다름을 함께 확인합니다.",
            '''assert first == "첫째" and second == "둘째"
assert remainder == b""
partial = encode_frame("경계")[:-1]
decoded, saved = decode_one(partial)
assert decoded is None and saved == partial
assert len("경계") != len("경계".encode("utf-8"))
print("프레임 검사 통과")''',
            "프레임 크기 제한은 메모리 고갈을 막기 위해 헤더를 읽은 직후 적용합니다.",
        ),
        NotebookSpec(
            "06-5-udp.ipynb",
            "06-5. UDP 통신 예제",
            ("데이터그램 하나가 메시지 경계 하나임을 확인합니다.", "손상된 데이터그램을 다른 메시지와 분리해 처리합니다."),
            "합성 데이터그램 목록을 사용하므로 네트워크 송수신은 발생하지 않습니다.",
            "데이터그램 단위 검증",
            "각 데이터그램을 독립적으로 디코딩하고 크기·인코딩 오류를 구조화합니다.",
            '''MAX_DATAGRAM = 32


def parse_datagram(payload: bytes) -> dict:
    if len(payload) > MAX_DATAGRAM:
        return {"ok": False, "reason": "too_large", "size": len(payload)}
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return {"ok": False, "reason": "invalid_utf8", "size": len(payload)}
    return {"ok": True, "text": text, "size": len(payload)}


datagrams = [b"alpha", "한글".encode("utf-8"), b"\\xff\\xfe", b"x" * 40]
results = [parse_datagram(item) for item in datagrams]
for result in results:
    print(result)''',
            "한 메시지의 실패가 다른 메시지의 결과를 지우지 않는지 확인합니다.",
            '''assert [item["ok"] for item in results] == [True, True, False, False]
assert results[2]["reason"] == "invalid_utf8"
assert results[3]["reason"] == "too_large"
print("데이터그램 검사 통과")''',
            "실제 UDP에서는 응답 손실·중복·순서 변경 가능성을 애플리케이션 규칙으로 다뤄야 합니다.",
        ),
        NotebookSpec(
            "06-6-dns-address-resolution.ipynb",
            "06-6. DNS와 주소 해석 예제",
            ("호스트 이름과 해석된 IP 주소를 구분합니다.", "모든 해석 결과가 허용 범위인지 검사합니다."),
            "`localhost`만 조회하고 외부 DNS에는 질의하지 않습니다.",
            "주소 해석 결과 정규화",
            "중복 주소를 제거하고 IPv4·IPv6 루프백 여부를 검사합니다.",
            '''import ipaddress
import socket


def resolved_addresses(host: str, port: int) -> tuple[str, ...]:
    records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    addresses = {ipaddress.ip_address(record[4][0]).compressed for record in records}
    return tuple(sorted(addresses, key=lambda value: (ipaddress.ip_address(value).version, value)))


addresses = resolved_addresses("localhost", 80)
print("localhost 해석 결과:", addresses)
print("모두 루프백:", all(ipaddress.ip_address(value).is_loopback for value in addresses))''',
            "빈 결과와 외부 주소를 허용하지 않는 정책을 함수로 분리합니다.",
            '''def require_loopback(addresses):
    if not addresses:
        raise ValueError("주소 해석 결과가 없습니다")
    parsed = [ipaddress.ip_address(value) for value in addresses]
    if not all(address.is_loopback for address in parsed):
        raise ValueError("루프백이 아닌 주소가 포함되어 있습니다")
    return tuple(address.compressed for address in parsed)


assert require_loopback(addresses)
try:
    require_loopback(["127.0.0.1", "192.0.2.10"])
except ValueError:
    print("외부 주소 혼합 거부 확인")''',
            "실제 서비스에서는 연결 직전에도 해석 결과와 허용 범위를 다시 확인합니다.",
        ),
        NotebookSpec(
            "06-7-timeouts-errors.ipynb",
            "06-7. 타임아웃·오류·재시도 예제",
            ("재시도 가능한 오류와 즉시 중단할 오류를 구분합니다.", "대기 계획을 실제 수면 없이 검증합니다."),
            "스크립트된 함수로 실패 순서를 고정해 같은 결과를 재현합니다.",
            "제한된 재시도 정책",
            "시도 횟수와 대기 시간을 기록하며 마지막 오류를 숨기지 않습니다.",
            '''class TemporaryFailure(OSError):
    pass


def run_with_retry(operation, attempts=3, base_delay=0.25):
    history = []
    for number in range(1, attempts + 1):
        try:
            return operation(), history
        except TemporaryFailure as error:
            history.append({"attempt": number, "error": str(error)})
            if number == attempts:
                raise
            history[-1]["next_delay"] = base_delay * (2 ** (number - 1))


outcomes = iter([TemporaryFailure("일시 오류 1"), TemporaryFailure("일시 오류 2"), "성공"])


def scripted_operation():
    outcome = next(outcomes)
    if isinstance(outcome, Exception):
        raise outcome
    return outcome


value, retry_history = run_with_retry(scripted_operation)
print(value)
print(retry_history)''',
            "성공 시도 수와 지수형 대기 계획을 확인합니다.",
            '''assert value == "성공"
assert [item["attempt"] for item in retry_history] == [1, 2]
assert [item["next_delay"] for item in retry_history] == [0.25, 0.5]
print("재시도 정책 검사 통과")''',
            "실제 네트워크 코드에서는 전체 시간 한도, 멱등성, 서버의 재시도 지시를 함께 고려합니다.",
        ),
        NotebookSpec(
            "06-8-echo-project.ipynb",
            "06-8. 로컬 Echo 프로젝트 검증 예제",
            ("교안의 길이 접두사 프로토콜 모듈을 재사용합니다.", "포트를 열지 않고 왕복 메시지를 확인합니다."),
            "저장소 루트에서 실행합니다. `socketpair()`만 사용하며 외부 연결은 없습니다.",
            "프로토콜 모듈로 왕복 메시지 확인",
            "실제 서버와 같은 `send_message()`·`receive_message()`를 로컬 소켓 쌍에 적용합니다.",
            '''from pathlib import Path
import socket
import sys
import threading


def find_project_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "examples/06-network-echo/protocol.py").is_file():
            return candidate
    raise RuntimeError("저장소 루트에서 Notebook을 실행해야 합니다")


PROJECT_ROOT = find_project_root()
MODULE_DIR = PROJECT_ROOT / "examples/06-network-echo"
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
from protocol import receive_message, send_message


def echo_once(sock):
    try:
        send_message(sock, receive_message(sock))
    finally:
        sock.close()


server_side, client_side = socket.socketpair()
worker = threading.Thread(target=echo_once, args=(server_side,), daemon=True)
worker.start()
with client_side:
    send_message(client_side, "로컬 Echo")
    echoed = receive_message(client_side)
worker.join(timeout=1)
print("응답:", echoed)''',
            "한글 메시지와 작업 종료를 확인합니다.",
            '''assert echoed == "로컬 Echo"
assert not worker.is_alive()
print("Echo 왕복 검사 통과")''',
            "터미널에서는 `echo_server.py`를 먼저 실행한 뒤 별도 창에서 `echo_client.py`를 실행합니다.",
        ),
        NotebookSpec(
            "07-1-url-http-messages.ipynb",
            "07-1. URL과 HTTP 메시지 예제",
            ("URL 구성요소를 분리합니다.", "요청 대상에서 프래그먼트를 제외합니다."),
            "표준 라이브러리의 URL 파서만 사용하며 요청을 전송하지 않습니다.",
            "URL 파싱과 요청 대상 구성",
            "경로와 쿼리는 서버에 전달되지만 프래그먼트는 브라우저 내부에서만 사용됩니다.",
            '''from urllib.parse import parse_qs, urlsplit


def inspect_url(url: str) -> dict:
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("HTTP(S) 절대 URL이 필요합니다")
    target = parts.path or "/"
    if parts.query:
        target += "?" + parts.query
    return {
        "scheme": parts.scheme,
        "host": parts.hostname,
        "port": parts.port,
        "target": target,
        "query": parse_qs(parts.query, keep_blank_values=True),
        "fragment": parts.fragment,
    }


url_info = inspect_url("http://127.0.0.1:8080/api/echo?text=hello#result")
print(url_info)
print(f"GET {url_info['target']} HTTP/1.1")''',
            "요청 대상에 프래그먼트가 포함되지 않는지 확인합니다.",
            '''assert url_info["target"] == "/api/echo?text=hello"
assert url_info["fragment"] == "result"
assert url_info["query"] == {"text": ["hello"]}
print("URL 구성요소 검사 통과")''',
            "실제 요청에서는 Host 헤더, 응답 상태선, 헤더와 본문을 각각 관찰합니다.",
        ),
        NotebookSpec(
            "07-2-requests-basics.ipynb",
            "07-2. requests 기초 응답 처리 예제",
            ("응답 크기를 제한해 읽습니다.", "상태 코드와 Content-Type을 함께 검증합니다."),
            "가짜 응답 객체를 사용하므로 `requests` 설치와 네트워크가 필요하지 않습니다.",
            "제한된 응답 읽기",
            "실제 `requests.Response.iter_content()`와 같은 인터페이스를 가진 객체로 처리 경계를 연습합니다.",
            '''class FakeResponse:
    def __init__(self, status_code, headers, chunks):
        self.status_code = status_code
        self.headers = headers
        self._chunks = chunks

    def iter_content(self, chunk_size):
        yield from self._chunks


def read_limited(response, limit=1024):
    parts = []
    size = 0
    for chunk in response.iter_content(128):
        if not chunk:
            continue
        size += len(chunk)
        if size > limit:
            raise ValueError("응답 크기 제한을 초과했습니다")
        parts.append(chunk)
    return b"".join(parts)


response = FakeResponse(200, {"Content-Type": "application/json; charset=utf-8"}, [b'{"status":', b' "ok"}'])
body = read_limited(response)
media_type = response.headers["Content-Type"].split(";", 1)[0].strip().lower()
print(response.status_code, media_type, body.decode("utf-8"))''',
            "정상 응답과 크기 초과 응답을 확인합니다.",
            '''assert response.status_code == 200
assert media_type == "application/json"
try:
    read_limited(FakeResponse(200, {}, [b"x" * 1025]))
except ValueError:
    print("과도한 응답 거부 확인")''',
            "실제 요청에서는 연결 타임아웃과 읽기 타임아웃을 튜플로 명시하고 리다이렉트 정책을 정합니다.",
        ),
        NotebookSpec(
            "07-3-json-api.ipynb",
            "07-3. JSON API와 응답 검증 예제",
            ("JSON 문법 오류와 계약 오류를 구분합니다.", "중복 키를 거부합니다."),
            "합성 JSON 문자열만 파싱합니다.",
            "엄격한 JSON 객체 검증",
            "파싱 성공만으로 필요한 필드와 자료형이 맞다고 판단하지 않습니다.",
            '''import json


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"중복 JSON 키: {key}")
        result[key] = value
    return result


def parse_health(payload: bytes) -> dict:
    data = json.loads(payload.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    if not isinstance(data, dict):
        raise ValueError("최상위 값은 객체여야 합니다")
    if data.get("status") != "ok" or not isinstance(data.get("service"), str):
        raise ValueError("응답 계약이 맞지 않습니다")
    return data


health = parse_health(b'{"status":"ok","service":"training"}')
print(health)''',
            "계약 오류와 중복 키를 각각 거부합니다.",
            '''for payload in (b'{"status":"down"}', b'{"status":"ok","status":"down","service":"x"}'):
    try:
        parse_health(payload)
    except ValueError as error:
        print("예상한 오류:", error)
    else:
        raise AssertionError("잘못된 JSON 계약을 허용했습니다")''',
            "오류 응답도 JSON일 수 있으므로 상태 코드와 오류 스키마를 별도로 정의합니다.",
        ),
        NotebookSpec(
            "07-4-sessions-cookies-auth.ipynb",
            "07-4. 세션·쿠키·인증 예제",
            ("쿠키 속성을 값과 분리해 확인합니다.", "인증 헤더를 로그에서 마스킹합니다."),
            "실제 계정·토큰 없이 합성 헤더만 사용합니다.",
            "쿠키 정책과 헤더 마스킹",
            "민감한 값은 출력하지 않고 보안 속성과 헤더 존재 여부만 기록합니다.",
            '''from http.cookies import SimpleCookie


def cookie_policy(set_cookie: str) -> dict:
    jar = SimpleCookie()
    jar.load(set_cookie)
    if len(jar) != 1:
        raise ValueError("쿠키 하나만 기대합니다")
    name, morsel = next(iter(jar.items()))
    return {
        "name": name,
        "httponly": bool(morsel["httponly"]),
        "secure": bool(morsel["secure"]),
        "samesite": morsel["samesite"].lower(),
    }


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    sensitive = {"authorization", "cookie", "set-cookie"}
    return {name: "[가림]" if name.lower() in sensitive else value for name, value in headers.items()}


policy = cookie_policy("session=training-value; HttpOnly; SameSite=Lax")
safe_headers = redact_headers({"Authorization": "Bearer training-token", "Accept": "application/json"})
print(policy)
print(safe_headers)''',
            "쿠키 값과 토큰이 출력 결과에서 제거되었는지 확인합니다.",
            '''assert policy == {"name": "session", "httponly": True, "secure": False, "samesite": "lax"}
assert safe_headers["Authorization"] == "[가림]"
assert "training-token" not in repr(safe_headers)
print("민감정보 비기록 검사 통과")''',
            "운영 환경의 세션 쿠키에는 HTTPS를 전제로 `Secure` 속성도 적용합니다.",
        ),
        NotebookSpec(
            "07-5-errors-timeouts-retries.ipynb",
            "07-5. HTTP 오류·타임아웃·재시도 예제",
            ("상태 코드별 재시도 여부를 구분합니다.", "서버의 Retry-After 값을 제한해서 사용합니다."),
            "실제 요청과 대기는 수행하지 않고 정책만 계산합니다.",
            "HTTP 재시도 계획 만들기",
            "읽기 전용 요청에서도 무제한 재시도하지 않으며 클라이언트 오류는 기본적으로 즉시 중단합니다.",
            '''RETRYABLE_STATUS = {429, 502, 503, 504}


def retry_decision(method: str, status: int, retry_after: str | None, attempt: int, limit=3):
    if method.upper() not in {"GET", "HEAD"}:
        return {"retry": False, "reason": "method"}
    if status not in RETRYABLE_STATUS or attempt >= limit:
        return {"retry": False, "reason": "status_or_limit"}
    delay = min(float(retry_after), 10.0) if retry_after and retry_after.isdigit() else 0.5 * (2 ** (attempt - 1))
    return {"retry": True, "delay": delay}


scenarios = [
    ("GET", 503, None, 1),
    ("GET", 429, "20", 2),
    ("POST", 503, None, 1),
    ("GET", 404, None, 1),
]
decisions = [retry_decision(*scenario) for scenario in scenarios]
for scenario, decision in zip(scenarios, decisions):
    print(scenario, "->", decision)''',
            "서버 지시 대기 시간의 상한과 비멱등 메서드 거부를 확인합니다.",
            '''assert decisions[0] == {"retry": True, "delay": 0.5}
assert decisions[1] == {"retry": True, "delay": 10.0}
assert decisions[2]["retry"] is False
assert decisions[3]["retry"] is False
print("재시도 정책 검사 통과")''',
            "실제 코드에서는 연결·읽기 타임아웃과 전체 실행 시간 한도를 함께 기록합니다.",
        ),
        NotebookSpec(
            "07-6-http-security-validation.ipynb",
            "07-6. HTTP 보안 검증 기초 예제",
            ("로컬 대상 범위를 먼저 검증합니다.", "관찰값과 취약점 확정을 구분합니다."),
            "루프백 URL과 합성 응답 헤더만 사용합니다.",
            "URL 범위와 보안 헤더 점검",
            "HTTP 학습 서버에서 기대하는 세 헤더의 누락 여부를 구조화합니다.",
            '''import ipaddress
from urllib.parse import urlsplit

EXPECTED_HEADERS = {"content-security-policy", "x-content-type-options", "referrer-policy"}


def validate_local_target(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != "http" or not parts.hostname or parts.username or parts.password:
        raise ValueError("사용자정보가 없는 HTTP URL이 필요합니다")
    if parts.query or parts.fragment or parts.path not in {"", "/"}:
        raise ValueError("기준 URL에는 경로·쿼리·프래그먼트를 넣지 않습니다")
    host = parts.hostname.lower()
    if host != "localhost" and not ipaddress.ip_address(host).is_loopback:
        raise ValueError("루프백 대상만 허용합니다")
    return f"http://{host}:{parts.port or 80}"


def inspect_headers(headers: dict[str, str]) -> dict:
    lowered = {name.lower(): value for name, value in headers.items()}
    missing = sorted(EXPECTED_HEADERS - lowered.keys())
    return {"status": "pass" if not missing else "warning", "missing": missing}


target = validate_local_target("http://127.0.0.1:8080")
header_result = inspect_headers({"X-Content-Type-Options": "nosniff"})
print(target)
print(header_result)''',
            "외부 주소 거부와 누락 헤더 판정을 확인합니다.",
            '''assert header_result["status"] == "warning"
assert len(header_result["missing"]) == 2
try:
    validate_local_target("http://192.0.2.10:8080")
except ValueError:
    print("외부 대상 거부 확인")''',
            "헤더 누락은 관찰 결과이며 실제 취약점 판단에는 HTTPS 종단·프록시·서비스 용도를 함께 확인해야 합니다.",
        ),
        NotebookSpec(
            "07-7-local-web-security-project.ipynb",
            "07-7. 로컬 웹 보안 점검 프로젝트 예제",
            ("여러 점검 결과를 하나의 보고서로 통합합니다.", "경고와 실패를 별도 집계합니다."),
            "가짜 세션으로 고정 응답을 사용하므로 서버 실행과 네트워크가 필요하지 않습니다.",
            "점검 파이프라인 통합",
            "연결·응답 계약·보안 헤더·리다이렉트 결과를 같은 구조로 모읍니다.",
            '''from dataclasses import dataclass


@dataclass(frozen=True)
class FakeResponse:
    status: int
    headers: dict[str, str]
    body: dict


RESPONSES = {
    "/health": FakeResponse(200, {"Content-Type": "application/json"}, {"status": "ok"}),
    "/headers": FakeResponse(200, {"Content-Type": "application/json"}, {}),
    "/redirect": FakeResponse(302, {"Location": "/health"}, {}),
}


def run_checks(responses):
    checks = []
    health = responses["/health"]
    checks.append({"check": "health", "status": "pass" if health.status == 200 and health.body.get("status") == "ok" else "fail"})
    required = {"Content-Security-Policy", "X-Content-Type-Options", "Referrer-Policy"}
    missing = sorted(required - responses["/headers"].headers.keys())
    checks.append({"check": "headers", "status": "warning" if missing else "pass", "missing": missing})
    redirect = responses["/redirect"]
    checks.append({"check": "redirect", "status": "pass" if redirect.headers.get("Location") == "/health" else "fail"})
    summary = {status: sum(item["status"] == status for item in checks) for status in ("pass", "warning", "fail")}
    return {"scope": "합성 로컬 응답", "summary": summary, "checks": checks}


report = run_checks(RESPONSES)
print(report)''',
            "의도한 헤더 경고 한 건과 실패 없음 상태를 확인합니다.",
            '''assert report["summary"] == {"pass": 2, "warning": 1, "fail": 0}
assert report["checks"][1]["missing"]
assert report["scope"] == "합성 로컬 응답"
print("프로젝트 보고서 검사 통과")''',
            "실제 프로젝트는 터미널에서 `training_server.py`와 `security_validator.py`를 별도로 실행합니다.",
        ),
        NotebookSpec(
            "08-1-cli-exit-status.ipynb",
            "08-1. 명령줄 인터페이스와 종료 상태 예제",
            ("인자 파싱과 핵심 실행을 분리합니다.", "성공·검사 실패·사용법 오류 코드를 구분합니다."),
            "`parse_args()`에 고정 인자 목록을 전달해 Notebook 커널 인자와 분리합니다.",
            "테스트 가능한 CLI 함수",
            "`main(argv)`가 출력 대신 종료 코드를 반환하도록 구성합니다.",
            '''import argparse

EXIT_OK = 0
EXIT_CHECK_FAILED = 1


def build_parser():
    parser = argparse.ArgumentParser(prog="local-check")
    parser.add_argument("--value", type=int, required=True)
    parser.add_argument("--minimum", type=int, default=1)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.value < args.minimum:
        return EXIT_CHECK_FAILED
    return EXIT_OK


examples = [
    (["--value", "5"], main(["--value", "5"])),
    (["--value", "0"], main(["--value", "0"])),
]
print(examples)''',
            "정상과 검사 실패가 서로 다른 종료 코드를 반환하는지 확인합니다.",
            '''assert main(["--value", "5"]) == 0
assert main(["--value", "0"]) == 1
assert main(["--value", "5", "--minimum", "5"]) == 0
print("CLI 종료 상태 검사 통과")''',
            "사용법 오류는 `argparse`가 기본적으로 종료 코드 2로 처리하며 터미널 테스트에서 검증합니다.",
        ),
        NotebookSpec(
            "08-2-configuration-environment.ipynb",
            "08-2. 설정 우선순위와 환경 변수 예제",
            ("기본값·JSON·환경 변수·CLI 우선순위를 적용합니다.", "비밀값을 공개 설정과 분리합니다."),
            "실제 환경 전체를 읽지 않고 허용된 합성 딕셔너리만 사용합니다.",
            "설정 계층 병합",
            "뒤에 적용한 계층이 앞의 값을 덮어쓰되 `None`은 덮어쓰지 않습니다.",
            '''DEFAULTS = {"target": "http://127.0.0.1:8080", "timeout": 3.0, "log_level": "INFO"}


def resolve_settings(json_values, environment_values, cli_values):
    allowed = set(DEFAULTS)
    for source in (json_values, environment_values, cli_values):
        unknown = set(source) - allowed
        if unknown:
            raise ValueError(f"지원하지 않는 설정: {sorted(unknown)}")
    result = dict(DEFAULTS)
    for source in (json_values, environment_values, cli_values):
        result.update({key: value for key, value in source.items() if value is not None})
    return result


settings = resolve_settings(
    {"timeout": 5.0},
    {"log_level": "WARNING"},
    {"timeout": 1.5, "target": None},
)
print(settings)''',
            "CLI 값이 최종 우선순위를 가지며 미지정 값은 기본값을 보존하는지 확인합니다.",
            '''assert settings == {"target": "http://127.0.0.1:8080", "timeout": 1.5, "log_level": "WARNING"}
try:
    resolve_settings({}, {}, {"api_token": "값"})
except ValueError:
    print("허용되지 않은 설정 거부 확인")''',
            "API 토큰은 설정 보고서와 로그에 포함하지 않고 필요한 코드 경계에만 전달합니다.",
        ),
        NotebookSpec(
            "08-3-logging-observability.ipynb",
            "08-3. 실행 로그와 관찰 가능성 예제",
            ("이벤트 중심 로그를 만듭니다.", "민감한 원문을 로그에 남기지 않습니다."),
            "메모리 스트림에 로그를 기록하므로 파일을 생성하지 않습니다.",
            "구조화된 실행 이벤트 기록",
            "대상 원문 대신 점검 이름·상태·소요 시간만 로그에 남깁니다.",
            '''from io import StringIO
import logging


def make_logger(stream):
    logger = logging.getLogger("chapter08-notebook")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


stream = StringIO()
logger = make_logger(stream)
secret = "training-secret-value"
logger.info("check_complete name=%s status=%s elapsed_ms=%d", "health", "pass", 12)
log_text = stream.getvalue()
print(log_text, end="")''',
            "로그에 비밀값과 응답 본문이 포함되지 않았는지 확인합니다.",
            '''assert "training-secret-value" not in log_text
assert "check_complete" in log_text
assert "status=pass" in log_text
print("로그 최소화 검사 통과")''',
            "운영 로그에는 실행 ID와 오류 유형을 추가하되 헤더·본문·환경 변수 전체는 기록하지 않습니다.",
        ),
        NotebookSpec(
            "08-4-safe-subprocess.ipynb",
            "08-4. 안전한 외부 프로세스 실행 예제",
            ("명령 문자열 대신 인자 목록을 사용합니다.", "종료 코드·출력 크기·타임아웃을 확인합니다."),
            "현재 Python을 자식 프로세스로 실행하며 셸과 외부 프로그램은 사용하지 않습니다.",
            "안전한 subprocess 경계",
            "고정된 실행 파일과 인자 목록을 사용하고 출력과 시간에 제한을 둡니다.",
            '''import subprocess
import sys


def run_python(code: str, timeout=2.0, output_limit=4096):
    completed = subprocess.run(
        [sys.executable, "-c", code],
        shell=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if len(completed.stdout) + len(completed.stderr) > output_limit:
        raise ValueError("자식 프로세스 출력 제한을 초과했습니다")
    return {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}


process_result = run_python("print('child-ok')")
print(process_result)''',
            "정상 종료와 비정상 종료를 구분합니다.",
            '''assert process_result == {"returncode": 0, "stdout": "child-ok\\n", "stderr": ""}
failed = run_python("import sys; sys.exit(7)")
assert failed["returncode"] == 7
print("프로세스 종료 상태 검사 통과")''',
            "사용자가 입력한 문자열을 `shell=True`로 전달하지 않으며 실행 파일 허용 목록을 별도로 관리합니다.",
        ),
        NotebookSpec(
            "08-5-toolization-project.ipynb",
            "08-5. 로컬 HTTP 점검기 도구화 프로젝트 예제",
            ("설정 검증과 실행 계획을 분리합니다.", "dry-run에서 네트워크·파일 쓰기를 수행하지 않습니다."),
            "합성 설정만 사용하며 HTTP 요청과 결과 파일 저장은 수행하지 않습니다.",
            "검증된 공개 실행 계획 만들기",
            "비밀값을 제외한 설정만 dry-run 결과로 공개합니다.",
            '''import ipaddress
from urllib.parse import urlsplit


def validate_target(url: str) -> str:
    parts = urlsplit(url)
    if parts.scheme != "http" or not parts.hostname:
        raise ValueError("HTTP 기준 URL이 필요합니다")
    host = parts.hostname.lower()
    if host != "localhost" and not ipaddress.ip_address(host).is_loopback:
        raise ValueError("루프백 대상만 허용합니다")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("사용자정보·쿼리·프래그먼트는 허용하지 않습니다")
    return f"http://{host}:{parts.port or 80}"


def dry_run_plan(settings):
    return {
        "mode": "dry-run",
        "target": validate_target(settings["target"]),
        "output": settings["output"],
        "timeout": float(settings["timeout"]),
        "will_request": False,
        "will_write": False,
    }


plan = dry_run_plan({"target": "http://127.0.0.1:8080", "output": "artifacts/report.json", "timeout": 3})
print(plan)''',
            "dry-run의 부작용 없음과 대상 범위를 확인합니다.",
            '''assert plan["will_request"] is False and plan["will_write"] is False
assert plan["target"] == "http://127.0.0.1:8080"
assert set(plan) == {"mode", "target", "output", "timeout", "will_request", "will_write"}
print("도구화 계획 검사 통과")''',
            "실제 CLI 계약은 `examples/08-toolization-project/test_local_http_tool.py`로 검증합니다.",
        ),
        NotebookSpec(
            "09-testing-debugging.ipynb",
            "09. 테스트와 디버깅 예제",
            ("정상·오류·경계값 테스트를 설계합니다.", "실패 메시지로 원인을 좁힙니다."),
            "표준 라이브러리 `unittest`로 실행합니다. pytest의 arrange-act-assert 구조에도 같은 원칙을 적용할 수 있습니다.",
            "테스트 가능한 입력 검증 함수",
            "함수 계약과 테스트 사례를 같은 Notebook에서 비교합니다.",
            '''import unittest
from io import StringIO


def parse_port(value: str) -> int:
    if not isinstance(value, str) or not value.isascii() or not value.isdigit():
        raise ValueError("포트는 ASCII 숫자 문자열이어야 합니다")
    port = int(value)
    if not 1 <= port <= 65535:
        raise ValueError("포트 범위 오류")
    return port


class ParsePortTests(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(parse_port("443"), 443)

    def test_boundaries(self):
        self.assertEqual(parse_port("1"), 1)
        self.assertEqual(parse_port("65535"), 65535)

    def test_invalid_values(self):
        for value in ("", "0", "65536", "４４３"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_port(value)


stream = StringIO()
suite = unittest.defaultTestLoader.loadTestsFromTestCase(ParsePortTests)
test_result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
print({"tests": test_result.testsRun, "successful": test_result.wasSuccessful()})''',
            "테스트 수와 성공 여부를 확인합니다.",
            '''assert test_result.testsRun == 3
assert test_result.wasSuccessful()
assert not test_result.failures and not test_result.errors
print("테스트 설계 검사 통과")''',
            "터미널에서는 실패 테스트만 선택 실행하고 로그·traceback의 최초 원인을 추적합니다.",
        ),
        NotebookSpec(
            "10-program-architecture.ipynb",
            "10. 프로그램 구조화 예제",
            ("입력·검증·처리·출력 책임을 분리합니다.", "입출력 없이 핵심 로직을 테스트합니다."),
            "작은 이벤트 목록을 메모리에서 처리합니다.",
            "계층별 함수 조립",
            "각 함수가 한 가지 책임만 맡고 상위 함수가 흐름을 연결합니다.",
            '''from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    action: str
    source_ip: str


def validate(raw):
    action = raw.get("action", "").upper()
    source_ip = raw.get("source_ip", "")
    if action not in {"ALLOW", "DENY"} or not source_ip:
        raise ValueError("이벤트 형식 오류")
    return Event(action, source_ip)


def summarize(events):
    return {action: sum(event.action == action for event in events) for action in ("ALLOW", "DENY")}


def render(summary):
    return f"ALLOW={summary['ALLOW']} DENY={summary['DENY']}"


def run_pipeline(raw_records):
    events = [validate(record) for record in raw_records]
    return render(summarize(events))


pipeline_output = run_pipeline([
    {"action": "allow", "source_ip": "192.0.2.10"},
    {"action": "DENY", "source_ip": "198.51.100.20"},
])
print(pipeline_output)''',
            "핵심 처리 함수와 전체 파이프라인 결과를 각각 확인합니다.",
            '''assert summarize([Event("DENY", "192.0.2.1")]) == {"ALLOW": 0, "DENY": 1}
assert pipeline_output == "ALLOW=1 DENY=1"
try:
    validate({"action": "UNKNOWN", "source_ip": "192.0.2.1"})
except ValueError:
    print("계약 위반 거부 확인")''',
            "실제 패키지에서는 이 함수들을 모듈로 나누고 공개 API와 CLI 진입점을 문서화합니다.",
        ),
        NotebookSpec(
            "11-concurrency.ipynb",
            "11. 동시성과 비동기 처리 예제",
            ("동시 작업 수를 제한합니다.", "일부 실패를 결과 목록에 보존합니다."),
            "합성 I/O 작업만 사용합니다. 프로세스 풀과 외부 HTTP 요청은 실행하지 않습니다.",
            "제한된 스레드와 비동기 작업",
            "작업별 결과를 구조화하고 입력 순서와 결과 식별자를 유지합니다.",
            '''from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import threading
import time


def simulated_io(item):
    time.sleep(0.01)
    if item == "bad":
        raise OSError("합성 I/O 오류")
    return item.upper()


def run_threaded(items, workers=2):
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(simulated_io, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                results.append({"item": item, "status": "ok", "value": future.result()})
            except OSError as error:
                results.append({"item": item, "status": "error", "error": str(error)})
    return sorted(results, key=lambda row: items.index(row["item"]))


thread_results = run_threaded(["one", "bad", "two"])
for row in thread_results:
    print(row)


async def bounded_double(values, limit=2):
    semaphore = asyncio.Semaphore(limit)
    async def one(value):
        async with semaphore:
            await asyncio.sleep(0.005)
            return value * 2
    return await asyncio.gather(*(one(value) for value in values))


def run_async_in_worker(coroutine):
    box = []
    worker = threading.Thread(target=lambda: box.append(asyncio.run(coroutine)))
    worker.start()
    worker.join()
    return box[0]


async_results = run_async_in_worker(bounded_double([1, 2, 3]))
print("비동기 결과:", async_results)''',
            "오류 보존과 비동기 결과를 확인합니다.",
            '''assert [row["status"] for row in thread_results] == ["ok", "error", "ok"]
assert async_results == [2, 4, 6]
assert thread_results[1]["item"] == "bad"
print("동시성 결과 검사 통과")''',
            "실제 HTTP 작업에는 전체 타임아웃·요청 속도·취소 후 정리 정책을 추가합니다.",
        ),
        NotebookSpec(
            "12-capstone.ipynb",
            "12. Python 활용 종합 프로젝트 예제",
            ("파일 수집·검증·해시·보고서 저장을 통합합니다.", "모든 쓰기를 임시 실습 영역으로 제한합니다."),
            "실행할 때마다 생성되는 임시 디렉터리만 사용합니다.",
            "파일 메타데이터 보고서 파이프라인",
            "일반 파일만 수집하고 SHA-256과 크기를 JSON으로 원자적 저장합니다.",
            '''from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory


def analyze_file(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError("일반 파일만 분석할 수 있습니다")
    data = path.read_bytes()
    return {"name": path.name, "size": len(data), "sha256": sha256(data).hexdigest()}


def write_json_atomic(value: dict, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=output.parent, delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        temporary = Path(stream.name)
    os.replace(temporary, output)


def run_demo():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        evidence = root / "evidence"
        evidence.mkdir()
        (evidence / "alpha.txt").write_text("alpha", encoding="utf-8")
        (evidence / "beta.bin").write_bytes(b"\\x00\\x01")
        records = [analyze_file(path) for path in sorted(evidence.iterdir())]
        report = {"count": len(records), "files": records}
        output = root / "results/report.json"
        write_json_atomic(report, output)
        loaded = json.loads(output.read_text(encoding="utf-8"))
        return loaded


capstone_report = run_demo()
print(json.dumps(capstone_report, ensure_ascii=False, indent=2))''',
            "파일 수·크기·해시 형식을 확인합니다.",
            '''assert capstone_report["count"] == 2
assert [item["name"] for item in capstone_report["files"]] == ["alpha.txt", "beta.bin"]
assert all(len(item["sha256"]) == 64 for item in capstone_report["files"])
print("종합 프로젝트 검사 통과")''',
            "다음 단계에서는 CLI·로그·테스트를 별도 모듈로 분리하고 실제 허용 범위를 문서화합니다.",
        ),
        NotebookSpec(
            "13-1-automation-design.ipynb",
            "13-1. DFIR 자동화 과제와 분석 범위 예제",
            ("자동화 입력·출력·제외 범위를 명시합니다.", "실제 증거와 합성 학습 자료를 구분합니다."),
            "경로 문자열과 범위 정의만 다루며 파일을 읽거나 쓰지 않습니다.",
            "분석 범위 계약 만들기",
            "허용한 아티팩트와 최대 행 수를 변경 불가능한 설정으로 표현합니다.",
            '''from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisScope:
    case_id: str
    allowed_artifacts: frozenset[str]
    max_rows: int
    synthetic: bool


def validate_scope(scope: AnalysisScope) -> AnalysisScope:
    if not scope.case_id.strip():
        raise ValueError("case_id가 필요합니다")
    supported = {"evtx", "prefetch", "registry", "mft", "shimcache", "amcache"}
    if not scope.allowed_artifacts or not scope.allowed_artifacts <= supported:
        raise ValueError("지원하지 않는 아티팩트가 포함되어 있습니다")
    if not 1 <= scope.max_rows <= 100_000:
        raise ValueError("행 수 제한이 범위를 벗어났습니다")
    return scope


scope = validate_scope(AnalysisScope(
    case_id="SYNTHETIC-CASE-001",
    allowed_artifacts=frozenset({"evtx", "prefetch", "registry"}),
    max_rows=10_000,
    synthetic=True,
))
print(scope)''',
            "범위가 비어 있거나 지원하지 않는 아티팩트를 포함하면 거부합니다.",
            '''assert scope.synthetic is True
try:
    validate_scope(AnalysisScope("CASE", frozenset({"memory"}), 100, False))
except ValueError:
    print("범위 밖 아티팩트 거부 확인")''',
            "실제 사건에서는 승인 범위·수집 원본·작업 사본·결과 저장 위치를 별도 기록합니다.",
        ),
        NotebookSpec(
            "13-2-file-batch.ipynb",
            "13-2. KAPE 결과 구조와 증거 목록 예제",
            ("manifest 선언과 실제 파일 상태를 대조합니다.", "입력 CSV 해시와 수집 원본 해시를 구분합니다."),
            "임시 디렉터리에 합성 CSV와 manifest를 만듭니다.",
            "입력 범위와 누락 상태 확인",
            "manifest에 선언한 각 파일을 processed·missing으로 분류합니다.",
            '''from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory


def inspect_manifest(manifest_path: Path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent.resolve()
    coverage = []
    for source in manifest["sources"]:
        candidate = (root / source["path"]).resolve()
        if root not in candidate.parents:
            raise ValueError("입력 루트 밖의 경로입니다")
        if not candidate.exists():
            coverage.append({"id": source["id"], "status": "missing"})
            continue
        data = candidate.read_bytes()
        coverage.append({"id": source["id"], "status": "processed", "sha256": sha256(data).hexdigest()})
    return coverage


with TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "events.csv").write_text("Time,EventId\\n2026-09-01T00:00:00Z,4624\\n", encoding="utf-8")
    manifest = {"case_id": "SYNTHETIC", "sources": [
        {"id": "events", "path": "events.csv"},
        {"id": "amcache", "path": "amcache.csv"},
    ]}
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    coverage = inspect_manifest(manifest_path)
print(coverage)''',
            "처리됨과 누락을 0건과 혼동하지 않는지 확인합니다.",
            '''assert [item["status"] for item in coverage] == ["processed", "missing"]
assert len(coverage[0]["sha256"]) == 64
assert "sha256" not in coverage[1]
print("증거 목록 검사 통과")''',
            "입력 CSV 해시는 파서 출력의 동일성을 확인할 뿐 원본 EVTX의 인계 기록을 대신하지 않습니다.",
        ),
        NotebookSpec(
            "13-3-web-collection.ipynb",
            "13-3. 아티팩트 파서와 분석 엔진 연계 예제",
            ("아티팩트별 처리 도구를 명시적으로 선택합니다.", "명령행 원문과 실행 인자를 분리합니다."),
            "외부 도구를 실행하지 않고 허용된 명령 계획만 구성합니다.",
            "파서 작업 계획 검증",
            "실행 파일과 옵션을 고정된 목록에서 선택하고 셸 문자열을 만들지 않습니다.",
            '''from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ToolSpec:
    artifact: str
    executable: Path
    output_format: str


TOOLS = {
    "evtx": ToolSpec("evtx", Path("/opt/training/EvtxECmd"), "csv"),
    "prefetch": ToolSpec("prefetch", Path("/opt/training/PECmd"), "csv"),
}


def build_command(artifact: str, input_path: Path, output_dir: Path):
    if artifact not in TOOLS:
        raise ValueError("허용하지 않은 아티팩트입니다")
    spec = TOOLS[artifact]
    if not input_path.is_absolute() or not output_dir.is_absolute():
        raise ValueError("검증된 절대 경로가 필요합니다")
    return [str(spec.executable), "--input", str(input_path), "--output", str(output_dir), "--format", spec.output_format]


command = build_command("evtx", Path("/cases/demo/evidence.evtx"), Path("/cases/demo/parser-output"))
print(command)''',
            "인자 목록이 유지되고 지원하지 않는 자료는 거부되는지 확인합니다.",
            '''assert isinstance(command, list) and "--input" in command
assert not any(";" in part for part in command)
try:
    build_command("memory", Path("/tmp/a"), Path("/tmp/b"))
except ValueError:
    print("허용 목록 밖 도구 거부 확인")''',
            "실제 실행 전에는 도구 버전·해시·옵션·종료 코드·출력 헤더를 함께 검증합니다.",
        ),
        NotebookSpec(
            "13-4-spreadsheet-documents.ipynb",
            "13-4. 공통 스키마·시간 정규화·보고서 예제",
            ("원문 시각과 UTC 시각을 함께 보존합니다.", "아티팩트별 시각 의미를 구분합니다."),
            "표준 라이브러리만 사용하며 합성 레코드를 변환합니다.",
            "시간대가 명시된 시각 정규화",
            "시간대가 없는 값은 추측하지 않고 오류로 격리합니다.",
            '''from datetime import datetime, timezone


def to_utc(value: str) -> str | None:
    if value == "":
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("시간대가 없는 시각은 변환할 수 없습니다")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_record(raw: dict) -> dict:
    return {
        "case_id": raw["case_id"],
        "host": raw["host"],
        "artifact": raw["artifact"],
        "timestamp_original": raw["timestamp"],
        "timestamp_utc": to_utc(raw["timestamp"]),
        "timestamp_kind": raw["timestamp_kind"],
        "source_file": raw["source_file"],
    }


record = normalize_record({
    "case_id": "SYNTHETIC", "host": "HOST-A", "artifact": "evtx",
    "timestamp": "2026-09-01T09:06:00+09:00", "timestamp_kind": "event_created",
    "source_file": "events.csv",
})
print(record)''',
            "UTC 변환 결과와 원문·의미 필드 보존을 확인합니다.",
            '''assert record["timestamp_utc"] == "2026-09-01T00:06:00Z"
assert record["timestamp_original"].endswith("+09:00")
try:
    to_utc("2026-09-01 09:06:00")
except ValueError:
    print("시간대 없는 시각 거부 확인")''',
            "보고서에서는 화면 표시 한도와 전체 JSONL 위치를 함께 안내합니다.",
        ),
        NotebookSpec(
            "13-5-scheduling-gui.ipynb",
            "13-5. 완료 감지·워커·재실행 관리 예제",
            ("작업 상태 전이를 명시합니다.", "부분 처리와 실행 실패를 구분합니다."),
            "메모리 상태만 사용하며 폴더 감시나 예약 실행은 수행하지 않습니다.",
            "작업 상태 기계",
            "허용된 이전 상태에서만 다음 상태로 이동합니다.",
            '''ALLOWED_TRANSITIONS = {
    "waiting": {"ready", "failed"},
    "ready": {"running", "failed"},
    "running": {"complete", "partial", "failed"},
    "complete": set(),
    "partial": set(),
    "failed": set(),
}


def transition(job: dict, new_status: str, detail: str) -> dict:
    current = job["status"]
    if new_status not in ALLOWED_TRANSITIONS[current]:
        raise ValueError(f"허용하지 않은 상태 전이: {current} -> {new_status}")
    history = [*job.get("history", []), {"from": current, "to": new_status, "detail": detail}]
    return {**job, "status": new_status, "history": history}


job = {"id": "SYNTHETIC-001", "status": "waiting", "history": []}
job = transition(job, "ready", "manifest 저장 완료")
job = transition(job, "running", "worker-01이 작업 확보")
job = transition(job, "partial", "입력 한 건 누락")
print(job)''',
            "완료 상태의 재실행과 잘못된 건너뛰기를 거부합니다.",
            '''assert job["status"] == "partial"
assert len(job["history"]) == 3
try:
    transition(job, "running", "같은 결과 재사용")
except ValueError:
    print("종료 상태 재사용 거부 확인")''',
            "재실행은 새 출력 디렉터리와 새 실행 ID를 사용하고 이전 완료 표시를 덮어쓰지 않습니다.",
        ),
        NotebookSpec(
            "13-6-safe-file-organizer-project.ipynb",
            "13-6. 프로젝트 A — KAPE 결과 정규화 예제",
            ("제공 합성 CSV를 공통 레코드로 정규화합니다.", "누락·행 오류·시각 없는 기록을 보존합니다."),
            "저장소의 `examples/13-kape-triage` 모듈과 임시 디렉터리를 사용합니다.",
            "합성 사건 생성과 정규화",
            "실제 사건 자료 없이 제공 생성기와 파이프라인의 `load_case()`를 실행합니다.",
            '''from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory


def project_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "examples/13-kape-triage/pipeline.py").is_file():
            return candidate
    raise RuntimeError("저장소 루트에서 Notebook을 실행해야 합니다")


def load_module(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE_ROOT = project_root() / "examples/13-kape-triage"
sample_module = load_module("chapter13_make_sample", MODULE_ROOT / "make_sample.py")
pipeline_module = load_module("chapter13_pipeline", MODULE_ROOT / "pipeline.py")

with TemporaryDirectory() as directory:
    manifest_path = sample_module.make_sample(Path(directory) / "input")
    manifest, manifest_hash, events, issues, coverage = pipeline_module.load_case(manifest_path)
    project_a_summary = {
        "events": len(events),
        "issues": len(issues),
        "missing": sum(item["status"] == "missing" for item in coverage),
        "undated": sum(event["timestamp_utc"] is None for event in events),
        "manifest_sha256_length": len(manifest_hash),
    }
print(project_a_summary)''',
            "교안이 정한 합성 사건의 기준 건수를 확인합니다.",
            '''assert project_a_summary == {
    "events": 14,
    "issues": 1,
    "missing": 1,
    "undated": 1,
    "manifest_sha256_length": 64,
}
print("프로젝트 A 기준 검사 통과")''',
            "실제 KAPE·EZ Tools 출력에는 사용한 버전의 실제 헤더에 맞춘 별도 어댑터가 필요합니다.",
        ),
        NotebookSpec(
            "13-7-spreadsheet-report-project.ipynb",
            "13-7. 프로젝트 B — Windows 아티팩트 통합 분석 예제",
            ("정규화 레코드에 검토 규칙을 적용합니다.", "검토 항목을 악성 확정과 구분합니다."),
            "13-6과 같은 합성 사건을 임시 디렉터리에서 다시 생성합니다.",
            "통합 검토 항목 생성",
            "제공 파이프라인의 `review_findings()`로 근거 UID가 연결된 검토 항목을 만듭니다.",
            '''from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory


def project_root() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "examples/13-kape-triage/pipeline.py").is_file():
            return candidate
    raise RuntimeError("저장소 루트에서 Notebook을 실행해야 합니다")


def load_module(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE_ROOT = project_root() / "examples/13-kape-triage"
sample_module = load_module("chapter13b_make_sample", MODULE_ROOT / "make_sample.py")
pipeline_module = load_module("chapter13b_pipeline", MODULE_ROOT / "pipeline.py")

with TemporaryDirectory() as directory:
    manifest_path = sample_module.make_sample(Path(directory) / "input")
    _, _, events, issues, coverage = pipeline_module.load_case(manifest_path)
    findings, related_paths = pipeline_module.review_findings(events)
    known_uids = {event["uid"] for event in events}
    project_b_summary = {
        "findings": len(findings),
        "related_paths": len(related_paths),
        "priorities": sorted({finding["priority"] for finding in findings}),
        "all_evidence_linked": all(set(finding["event_uids"]) <= known_uids for finding in findings),
    }
print(project_b_summary)
for finding in findings[:3]:
    print(finding["rule_id"], finding["title"], finding["status"])''',
            "검토 항목 수와 근거 UID 연결을 확인합니다.",
            '''assert project_b_summary["findings"] == 8
assert project_b_summary["related_paths"] == 2
assert project_b_summary["all_evidence_linked"] is True
assert all(finding["status"] == "review" for finding in findings)
assert all(finding["event_uids"] for finding in findings)
print("프로젝트 B 기준 검사 통과")''',
            "규칙 일치는 조사 우선순위를 좁히는 단서이며 원본 사건·승인 이력·추가 아티팩트와 대조해야 합니다.",
        ),
    ]


def main() -> int:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    created = []
    for spec in specs():
        notebook = notebook_for(spec)
        execute_notebook(notebook, spec.filename)
        output = NOTEBOOK_DIR / spec.filename
        output.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        created.append(output.relative_to(ROOT).as_posix())
    print(f"생성 및 실행 검증 완료: {len(created)}개")
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
