# 06-7. 타임아웃·오류·재시도

네트워크 작업은 상대 프로그램, 이름 해석, 경로, 운영체제 상태에 영향을 받습니다. 무기한 대기하지 않도록 시간과 데이터 크기를 제한하고 오류 단계별로 대응합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 연결·수신 타임아웃을 적용합니다.
- 주소 해석·연결·통신 오류를 구분합니다.
- 재시도가 안전한 작업인지 판단합니다.
- 제한된 지수 백오프를 구현합니다.
{% endhint %}

## 1. 네트워크 오류 단계

| 단계 | 대표 예외 | 확인할 내용 |
| --- | --- | --- |
| 주소 해석 | `socket.gaierror` | 이름·DNS 설정 |
| 연결 | `ConnectionRefusedError` | 서버 실행·포트 |
| 대기 시간 | `socket.timeout` | 상대 응답·타임아웃 값 |
| 연결 중단 | `ConnectionResetError` | 상대 종료·프로토콜 오류 |
| 공통 OS 오류 | `OSError` | 권한·주소·네트워크 상태 |

구체적인 예외를 먼저 처리하고 마지막에 `OSError`를 처리합니다.

## 2. 타임아웃은 모든 단계에 필요하다

```python
with socket.create_connection(
    (host, port),
    timeout=3.0,
) as sock:
    sock.settimeout(2.0)
    sock.sendall(request)
    response = sock.recv(4096)
```

연결 타임아웃과 연결 후 송수신 타임아웃의 목적을 구분합니다.

## 3. 재시도 판단

재시도하기 전에 다음을 확인합니다.

- 일시적 오류인가?
- 같은 요청을 다시 보내도 부작용이 없는가?
- 서버가 요청을 처리했지만 응답만 유실됐을 가능성이 있는가?
- 전체 시도 횟수와 총 대기 시간이 제한되는가?

데이터 생성·삭제 요청은 요청 ID나 멱등성 정책 없이 자동 재시도하지 않습니다.

## 4. 제한된 백오프

```python
import socket
import time


def connect_with_retry(host, port, attempts=3):
    last_error = None

    for attempt in range(attempts):
        try:
            return socket.create_connection(
                (host, port),
                timeout=3.0,
            )
        except (socket.timeout, ConnectionRefusedError) as exc:
            last_error = exc

            if attempt + 1 == attempts:
                break

            delay = min(0.5 * (2 ** attempt), 2.0)
            time.sleep(delay)

    raise ConnectionError("서버에 연결하지 못했습니다") from last_error
```

학습 예제에서도 시도 횟수와 최대 대기 시간을 작게 유지합니다.

## 5. 오류를 숨기지 않기

```python
except OSError as exc:
    raise ConnectionError(
        f"{host}:{port} 통신 실패"
    ) from exc
```

상위 코드가 실패를 판단할 수 있도록 원래 예외를 연결합니다. 빈 응답이나 기본값을 반환해 장애를 정상 결과처럼 보이게 만들지 않습니다.

## 완료 기준

- [ ] 연결과 송수신 타임아웃을 구분할 수 있습니다.
- [ ] 재시도하면 안 되는 작업을 설명할 수 있습니다.
- [ ] 제한된 횟수와 대기 시간을 적용할 수 있습니다.

---

다음 절: [06-8. 로컬 Echo 통신 프로젝트](06-8-echo-project.md)
