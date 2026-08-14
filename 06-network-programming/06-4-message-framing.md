# 06-4. 메시지 경계와 프로토콜 설계

TCP는 메시지 목록이 아니라 순서가 보장되는 바이트 스트림입니다. 한 번 전송한 데이터가 여러 번의 `recv()`로 나뉘거나 여러 전송이 한 번에 수신될 수 있으므로 애플리케이션이 메시지 경계를 정의해야 합니다.

{% hint style="info" %}
## 🧭 학습 목표

- TCP의 스트림 특성을 설명합니다.
- 구분자·고정 길이·길이 접두어 방식을 비교합니다.
- 정확한 바이트 수를 받는 함수를 구현합니다.
- 메시지 크기와 디코딩 결과를 검증합니다.
{% endhint %}

## 1. recv()의 숫자는 메시지 길이가 아니다

```python
chunk = sock.recv(4096)
```

`4096`은 최대 수신 바이트 수입니다. 요청이 100바이트라도 30바이트와 70바이트로 나뉘어 도착할 수 있습니다.

## 2. 메시지 경계 방식

| 방식 | 장점 | 주의점 |
| --- | --- | --- |
| 연결 종료 | 구현이 단순함 | 연결을 재사용하기 어려움 |
| 구분자 | 텍스트 프로토콜에 편리함 | 본문 안 구분자 이스케이프 필요 |
| 고정 길이 | 파싱이 단순함 | 공간 낭비와 가변 데이터 제한 |
| 길이 접두어 | 바이너리·텍스트 모두 가능 | 길이 검증 필수 |

## 3. 정확한 길이 수신

```python
def receive_exactly(sock, size):
    if size < 0:
        raise ValueError("수신 길이는 0 이상이어야 합니다")

    received = bytearray()

    while len(received) < size:
        chunk = sock.recv(size - len(received))
        if not chunk:
            raise ConnectionError("메시지 수신 중 연결이 종료되었습니다")
        received.extend(chunk)

    return bytes(received)
```

## 4. 4바이트 길이 접두어

```python
import struct

HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 1024 * 1024


def encode_message(text):
    payload = text.encode("utf-8")

    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError("메시지가 너무 큽니다")

    header = struct.pack("!I", len(payload))
    return header + payload
```

- `!`: 네트워크 바이트 순서(big-endian)
- `I`: 부호 없는 4바이트 정수

## 5. 메시지 디코딩

```python
def receive_message(sock):
    header = receive_exactly(sock, HEADER_SIZE)
    payload_size = struct.unpack("!I", header)[0]

    if payload_size > MAX_MESSAGE_SIZE:
        raise ValueError("허용된 메시지 크기를 초과했습니다")

    payload = receive_exactly(sock, payload_size)
    return payload.decode("utf-8")
```

길이 값을 신뢰하기 전에 반드시 최대 크기와 비교합니다.

## 6. JSON 메시지로 확장

```python
import json

message = {
    "type": "echo",
    "text": "hello",
}

wire_text = json.dumps(
    message,
    ensure_ascii=False,
)
```

JSON은 데이터 구조를 표현하고 길이 접두어는 메시지 경계를 표현합니다. 두 역할을 구분합니다.

## 완료 기준

- [ ] 한 번의 `recv()`가 한 메시지를 보장하지 않는 이유를 설명할 수 있습니다.
- [ ] 길이 접두어 메시지를 인코딩하고 디코딩할 수 있습니다.
- [ ] 메시지 최대 크기와 연결 조기 종료를 처리할 수 있습니다.

---

다음 절: [06-5. UDP 통신](06-5-udp.md)

