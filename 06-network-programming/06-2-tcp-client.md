# 06-2. TCP 클라이언트

TCP 클라이언트는 서버와 연결을 수립한 뒤 바이트 스트림을 송수신합니다. 연결 시도부터 타임아웃·응답 종료까지의 흐름을 구현합니다.

{% hint style="info" %}
## 🧭 학습 목표

- `socket.create_connection()`으로 TCP 서버에 연결합니다.
- 연결 전에 타임아웃을 적용합니다.
- `sendall()`로 전체 요청을 전송합니다.
- 응답 종료 조건을 명시합니다.
{% endhint %}

## 1. 가장 작은 TCP 클라이언트

```python
import socket

HOST = "127.0.0.1"
PORT = 9000
TIMEOUT_SECONDS = 3.0

with socket.create_connection(
    (HOST, PORT),
    timeout=TIMEOUT_SECONDS,
) as sock:
    sock.sendall("hello".encode("utf-8"))
    response = sock.recv(4096)

print(response.decode("utf-8"))
```

`create_connection()`은 호스트 이름을 사용할 때 IPv4와 IPv6 주소 후보를 해석하고 연결 가능한 주소를 시도합니다.

## 2. send()와 sendall()

`send()`는 전달한 바이트 중 일부만 보낼 수 있으며 실제 전송한 길이를 반환합니다. `sendall()`은 전체 바이트를 보내거나 예외를 발생시킵니다.

```python
payload = "한글 메시지".encode("utf-8")
sock.sendall(payload)
```

`len("한글")`과 `len("한글".encode("utf-8"))`은 다를 수 있으므로 네트워크 길이는 인코딩한 바이트를 기준으로 계산합니다.

## 3. 응답을 반복해서 받기

```python
def receive_until_close(sock, chunk_size=4096):
    chunks = []

    while True:
        chunk = sock.recv(chunk_size)
        if not chunk:
            break
        chunks.append(chunk)

    return b"".join(chunks)
```

`recv()`가 빈 바이트 `b""`를 반환하면 상대가 정상적으로 송신 방향을 종료한 것입니다. 다만 서버가 연결을 계속 유지하는 프로토콜에서는 다른 메시지 종료 규칙이 필요합니다.

## 4. 연결 오류 처리

```python
try:
    with socket.create_connection(
        (HOST, PORT),
        timeout=3.0,
    ) as sock:
        sock.sendall(b"hello")
except socket.timeout:
    print("연결 또는 통신 시간이 초과되었습니다.")
except ConnectionRefusedError:
    print("서버가 연결을 거부했습니다.")
except OSError as exc:
    print(f"네트워크 오류: {exc}")
```

## 5. 응답 크기 제한

```python
def receive_limited(sock, limit=1024 * 1024):
    received = bytearray()

    while len(received) < limit:
        chunk = sock.recv(min(4096, limit - len(received)))
        if not chunk:
            return bytes(received)
        received.extend(chunk)

    raise ValueError("응답이 허용 크기를 초과했습니다")
```

신뢰할 수 없는 상대의 응답을 제한 없이 메모리에 저장하지 않습니다.

## 완료 기준

- [ ] 타임아웃이 있는 TCP 연결을 만들 수 있습니다.
- [ ] `sendall()`이 필요한 이유를 설명할 수 있습니다.
- [ ] 빈 `recv()`와 응답 크기 제한을 처리할 수 있습니다.

---

다음 절: [06-3. TCP 서버](06-3-tcp-server.md)

