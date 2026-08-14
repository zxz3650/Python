# 06-1. 네트워크와 소켓 기초

네트워크 프로그램은 호스트의 특정 포트에서 다른 프로그램과 바이트를 주고받습니다. Python의 `socket` 객체는 운영체제의 네트워크 기능을 사용하는 프로그래밍 인터페이스입니다.

{% hint style="info" %}
## 🧭 학습 목표

- 호스트·IP 주소·포트·프로토콜을 구분합니다.
- 주소 패밀리와 소켓 종류를 설명합니다.
- 소켓의 생성부터 종료까지의 흐름을 설명합니다.
- 문자열과 네트워크 바이트의 차이를 적용합니다.
{% endhint %}

## 1. 통신을 식별하는 정보

| 용어 | 의미 | 예 |
| --- | --- | --- |
| 호스트 | 네트워크에 연결된 시스템 | `localhost` |
| IP 주소 | 네트워크 계층의 주소 | `127.0.0.1`, `::1` |
| 포트 | 호스트 안의 통신 종단점 번호 | `8000` |
| 프로토콜 | 통신 규칙 | TCP, UDP |
| 소켓 | 프로그램이 통신에 사용하는 객체 | `socket.socket(...)` |

같은 포트 번호라도 TCP와 UDP는 서로 다른 통신 종단점입니다.

## 2. 주소 패밀리와 소켓 종류

```python
import socket

tcp_ipv4_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM,
)
tcp_ipv4_socket.close()
```

- `AF_INET`: IPv4 주소
- `AF_INET6`: IPv6 주소
- `SOCK_STREAM`: TCP 바이트 스트림
- `SOCK_DGRAM`: UDP 데이터그램

## 3. 클라이언트와 서버

```text
서버: socket → bind → listen → accept → recv/send → close
클라이언트: socket → connect → send/recv → close
```

서버는 주소에 바인딩하고 연결을 기다립니다. 클라이언트는 서버 주소로 연결합니다.

## 4. 문자열이 아니라 bytes 송수신

```python
message = "안녕하세요"
payload = message.encode("utf-8")
restored = payload.decode("utf-8")

print(message)
print(payload)
print(restored)
```

네트워크 소켓은 `bytes`를 송수신합니다. 인코딩은 송신자와 수신자가 합의한 프로토콜의 일부입니다.

## 5. with 문으로 소켓 닫기

```python
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    print(sock.fileno())

print(sock.fileno())  # 닫힌 소켓은 일반적으로 -1
```

예외가 발생하더라도 소켓이 닫히도록 `with` 문을 사용합니다.

## 흔한 실수

- 포트 번호와 IP 주소를 같은 개념으로 이해함
- `str`을 인코딩하지 않고 `send()`에 전달함
- 소켓을 닫지 않음
- TCP가 메시지 단위를 보존한다고 가정함
- 테스트 서버를 `0.0.0.0`에 무조건 공개함

## 완료 기준

- [ ] IP·포트·프로토콜의 역할을 구분할 수 있습니다.
- [ ] `AF_INET`, `SOCK_STREAM`, `SOCK_DGRAM`을 설명할 수 있습니다.
- [ ] 송수신 전후의 인코딩 과정을 설명할 수 있습니다.

---

다음 절: [06-2. TCP 클라이언트](06-2-tcp-client.md)
