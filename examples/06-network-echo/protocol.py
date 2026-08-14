from __future__ import annotations

import socket
import struct


HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 1024 * 1024


def receive_exactly(sock: socket.socket, size: int) -> bytes:
    if size < 0:
        raise ValueError("수신 길이는 0 이상이어야 합니다")

    received = bytearray()

    while len(received) < size:
        chunk = sock.recv(size - len(received))
        if not chunk:
            raise ConnectionError("메시지 수신 중 연결이 종료되었습니다")
        received.extend(chunk)

    return bytes(received)


def send_message(sock: socket.socket, text: str) -> None:
    payload = text.encode("utf-8")

    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError("메시지가 허용 크기를 초과했습니다")

    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)


def receive_message(sock: socket.socket) -> str:
    header = receive_exactly(sock, HEADER_SIZE)
    payload_size = struct.unpack("!I", header)[0]

    if payload_size > MAX_MESSAGE_SIZE:
        raise ValueError("메시지가 허용 크기를 초과했습니다")

    payload = receive_exactly(sock, payload_size)
    return payload.decode("utf-8")

