# 06-8. 로컬 Echo 통신 프로젝트

06장에서 학습한 TCP 연결, 바이트 인코딩, 메시지 경계, 타임아웃, 오류 처리를 하나의 프로그램으로 연결합니다. 서버가 받은 UTF-8 메시지를 같은 내용으로 돌려주는 로컬 Echo 프로토콜을 구현합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 프로토콜·서버·클라이언트 역할을 파일로 분리합니다.
- 4바이트 길이 접두어 메시지를 송수신합니다.
- 메시지 크기·인코딩·연결 종료를 검증합니다.
- 로컬 환경에서 정상·오류·경계 입력을 시험합니다.
{% endhint %}

## 실습 코드

- [`protocol.py`](https://github.com/zxz3650/Python/blob/master/examples/06-network-echo/protocol.py)
- [`echo_server.py`](https://github.com/zxz3650/Python/blob/master/examples/06-network-echo/echo_server.py)
- [`echo_client.py`](https://github.com/zxz3650/Python/blob/master/examples/06-network-echo/echo_client.py)

## 1. 프로토콜 규칙

```text
4바이트 길이 헤더 + UTF-8 본문
```

- 바이트 순서: network byte order(big-endian)
- 최대 본문: 1MiB
- 인코딩: UTF-8
- 응답: 요청과 동일한 메시지
- 연결: 요청과 응답 한 번 후 종료

## 2. 공통 프로토콜 함수

```python
def send_message(sock, text):
    payload = text.encode("utf-8")

    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError("메시지가 너무 큽니다")

    sock.sendall(struct.pack("!I", len(payload)) + payload)
```

```python
def receive_message(sock):
    header = receive_exactly(sock, 4)
    payload_size = struct.unpack("!I", header)[0]

    if payload_size > MAX_MESSAGE_SIZE:
        raise ValueError("메시지가 너무 큽니다")

    payload = receive_exactly(sock, payload_size)
    return payload.decode("utf-8")
```

클라이언트와 서버가 같은 프로토콜 함수를 사용해 규칙 불일치를 줄입니다.

## 3. 서버 실행

```bash
python examples/06-network-echo/echo_server.py
```

서버는 `127.0.0.1:9000`에서 한 번의 연결을 기다립니다.

## 4. 클라이언트 실행

다른 터미널에서 실행합니다.

```bash
python examples/06-network-echo/echo_client.py
```

메시지를 입력하면 서버가 돌려준 응답을 출력합니다.

## 5. 실행 순서

```text
서버 socket 생성
→ 127.0.0.1:9000 bind
→ listen·accept
→ 클라이언트 connect
→ 길이 헤더와 본문 전송
→ 서버가 정확한 길이만큼 수신
→ 같은 형식으로 응답
→ 클라이언트 응답 검증
→ 양쪽 소켓 종료
```

## 6. 검증 입력

| 입력 | 확인할 내용 |
| --- | --- |
| `hello` | 기본 ASCII 송수신 |
| `한글 메시지` | UTF-8 바이트 길이 |
| 빈 문자열 | 길이 0 메시지 |
| 1MiB 이하 긴 문자열 | 반복 `recv()` |
| 1MiB 초과 문자열 | 크기 제한 오류 |
| 서버를 실행하지 않음 | 연결 거부 처리 |
| 서버 응답 지연 | 타임아웃 처리 |

## 7. 보안 관점의 점검

- 외부가 아닌 로컬 주소에만 바인딩했는가?
- 길이 헤더를 메모리 할당 전에 검증하는가?
- 연결과 수신 시간이 제한되는가?
- 잘못된 UTF-8을 정상 메시지로 처리하지 않는가?
- 오류가 발생해도 소켓이 닫히는가?

## 확장 과제

1. JSON 요청과 응답 구조를 추가합니다.
2. 요청 ID와 서버 처리 시간을 응답에 포함합니다.
3. 여러 요청을 한 연결에서 처리하는 종료 규칙을 설계합니다.
4. 07장에서 CLI 인자와 `logging`을 추가합니다.
5. 08장에서 HTTP 요청·응답 구조와 비교합니다.

{% hint style="success" %}
## ✅ 완료 기준

- [ ] 서버와 클라이언트를 서로 다른 터미널에서 실행할 수 있습니다.
- [ ] 한글과 빈 메시지를 정확히 송수신할 수 있습니다.
- [ ] 메시지 크기 초과와 연결 조기 종료를 처리할 수 있습니다.
- [ ] 서버 미실행과 타임아웃 오류를 설명할 수 있습니다.
{% endhint %}

---

다음 장: [07. HTTP와 API](../07-http-api.md)

