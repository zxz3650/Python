from __future__ import annotations

import socket

from protocol import receive_message, send_message


HOST = "127.0.0.1"
PORT = 9000
TIMEOUT_SECONDS = 5.0


def request_echo(message: str) -> str:
    with socket.create_connection(
        (HOST, PORT),
        timeout=TIMEOUT_SECONDS,
    ) as sock:
        sock.settimeout(TIMEOUT_SECONDS)
        send_message(sock, message)
        return receive_message(sock)


def main() -> int:
    message = input("보낼 메시지: ")

    try:
        response = request_echo(message)
    except socket.timeout:
        print("연결 또는 통신 시간이 초과되었습니다.")
        return 1
    except ConnectionRefusedError:
        print("서버가 실행 중인지 확인하세요.")
        return 1
    except (ConnectionError, UnicodeError, ValueError, OSError) as exc:
        print(f"클라이언트 오류: {exc}")
        return 1

    print(f"응답: {response!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
