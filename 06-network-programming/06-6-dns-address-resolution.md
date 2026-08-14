# 06-6. DNS와 주소 해석

도메인 이름은 소켓이 직접 사용하는 IP 주소가 아닙니다. 주소 해석 과정에서 하나의 이름이 IPv4·IPv6를 포함한 여러 주소 후보로 변환될 수 있습니다.

{% hint style="info" %}
## 🧭 학습 목표

- 도메인 이름과 IP 주소를 구분합니다.
- `getaddrinfo()`의 반환 구조를 읽습니다.
- TCP와 UDP에 필요한 주소 후보를 제한합니다.
- IPv4와 IPv6를 함께 고려합니다.
{% endhint %}

## 1. 주소 정보 조회

```python
import socket

results = socket.getaddrinfo(
    "localhost",
    9000,
    family=socket.AF_UNSPEC,
    type=socket.SOCK_STREAM,
    proto=socket.IPPROTO_TCP,
)

for family, socktype, protocol, canonname, address in results:
    print(family, socktype, protocol, address)
```

`getaddrinfo()`는 다음 5개 값을 가진 튜플 목록을 반환합니다.

```text
(주소 패밀리, 소켓 종류, 프로토콜, 정규 이름, 소켓 주소)
```

결과는 운영체제와 네트워크 설정에 따라 달라질 수 있습니다.

## 2. 필요한 프로토콜로 제한

TCP 연결에 사용할 주소를 찾는다면 `SOCK_STREAM`과 `IPPROTO_TCP`를 지정합니다. 아무 조건도 지정하지 않으면 프로그램이 처리하지 않는 주소 형태가 포함될 수 있습니다.

## 3. IPv4와 IPv6

```python
def family_name(family):
    if family == socket.AF_INET:
        return "IPv4"
    if family == socket.AF_INET6:
        return "IPv6"
    return str(family)
```

- IPv4 소켓 주소: `(host, port)`
- IPv6 소켓 주소: `(host, port, flowinfo, scope_id)`

주소 튜플의 길이를 고정해서 가정하지 말고 `getaddrinfo()`가 반환한 값을 그대로 사용합니다.

## 4. 연결에는 create_connection 사용

```python
with socket.create_connection(
    ("localhost", 9000),
    timeout=3.0,
) as sock:
    sock.sendall(b"hello")
```

단순 TCP 클라이언트는 주소 후보를 직접 순회하기보다 `create_connection()`을 사용하는 편이 안전합니다.

## 5. 이름 해석 오류

```python
try:
    socket.getaddrinfo(
        "invalid.example.invalid",
        9000,
        type=socket.SOCK_STREAM,
    )
except socket.gaierror as exc:
    print(f"주소 해석 실패: {exc}")
```

DNS 실패와 TCP 연결 거부는 서로 다른 단계의 오류입니다.

## 완료 기준

- [ ] 도메인 이름과 IP 주소를 구분할 수 있습니다.
- [ ] `getaddrinfo()` 결과의 다섯 필드를 설명할 수 있습니다.
- [ ] 주소 해석 실패와 연결 실패를 구분할 수 있습니다.

---

다음 절: [06-7. 타임아웃·오류·재시도](06-7-timeouts-errors.md)

