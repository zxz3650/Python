# 06-3. TCP 서버

TCP 서버는 로컬 주소에 바인딩하고 연결 요청을 기다립니다. 학습용 서버는 외부에 노출하지 않고 한 번의 연결을 안전하게 처리하는 것부터 시작합니다.

{% hint style="info" %}
## 🧭 학습 목표

- `bind()`, `listen()`, `accept()`의 역할을 설명합니다.
- 서버 소켓과 연결 소켓을 구분합니다.
- 로컬 호스트에만 바인딩합니다.
- 연결과 수신에 타임아웃을 적용합니다.
{% endhint %}

## 1. 서버 소켓의 생명주기

```python
import socket

HOST = "127.0.0.1"
PORT = 9000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    connection, address = server.accept()

    with connection:
        data = connection.recv(4096)
        connection.sendall(data)
```

## 2. 각 단계의 역할

- `bind()`: 서버 소켓을 로컬 IP와 포트에 연결
- `listen()`: 연결 요청을 받을 준비
- `accept()`: 연결별 새 소켓과 상대 주소 반환
- `recv()/sendall()`: 연결 소켓에서 실제 데이터 송수신

서버 소켓은 연결 요청을 받고, `accept()`가 반환한 연결 소켓이 각 클라이언트와 통신합니다.

## 3. 로컬 바인딩

```python
HOST = "127.0.0.1"
```

`127.0.0.1`은 같은 시스템에서만 접근할 수 있습니다. `0.0.0.0`은 사용 가능한 모든 IPv4 인터페이스에 바인딩하므로 방화벽과 접근 통제를 이해하기 전에는 사용하지 않습니다.

## 4. 서버 타임아웃

```python
server.settimeout(10.0)
connection, address = server.accept()

with connection:
    connection.settimeout(3.0)
    data = connection.recv(4096)
```

`accept()` 대기 시간과 연결 후 `recv()` 대기 시간은 서로 다르게 설정할 수 있습니다.

## 5. 종료 방향 알리기

```python
connection.sendall(response)
connection.shutdown(socket.SHUT_WR)
```

`shutdown(SHUT_WR)`은 더 이상 데이터를 보내지 않겠다고 알립니다. `close()`는 운영체제 자원을 최종 해제합니다.

## 흔한 실수

- 서버 소켓과 연결 소켓을 혼동함
- 한 번의 `recv()`가 전체 요청이라고 가정함
- 수신 크기와 대기 시간을 제한하지 않음
- 외부 인터페이스에 의도치 않게 바인딩함
- 예외 발생 후 연결 소켓을 닫지 않음

## 완료 기준

- [ ] 서버 소켓과 연결 소켓을 구분할 수 있습니다.
- [ ] 로컬 Echo 서버를 실행할 수 있습니다.
- [ ] 연결 수락과 수신에 타임아웃을 적용할 수 있습니다.

---

다음 절: [06-4. 메시지 경계와 프로토콜 설계](06-4-message-framing.md)
