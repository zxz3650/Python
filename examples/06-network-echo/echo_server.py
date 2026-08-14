from __future__ import annotations

import socket

from protocol import receive_message, send_message


HOST = "127.0.0.1"
PORT = 9000
ACCEPT_TIMEOUT_SECONDS = 30.0
CONNECTION_TIMEOUT_SECONDS = 5.0


def run_server() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        server.settimeout(ACCEPT_TIMEOUT_SECONDS)

        print(f"대기 중: {HOST}:{PORT}")
        connection, address = server.accept()

        with connection:
            connection.settimeout(CONNECTION_TIMEOUT_SECONDS)
            message = receive_message(connection)
            print(f"수신: {address} {message!r}")
            send_message(connection, message)


if __name__ == "__main__":
    try:
        run_server()
    except socket.timeout:
        print("연결 또는 통신 시간이 초과되었습니다.")
    except (ConnectionError, UnicodeError, ValueError, OSError) as exc:
        print(f"서버 오류: {exc}")

