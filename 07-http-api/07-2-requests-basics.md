# 07-2. requests 기초

> 실습 준비: [이 절의 노트북 보기](../notebooks/07-2-requests-basics.ipynb) · [07장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-07.zip) · [자료 준비·실행 안내](../PRACTICE.md#download)
>
> 07장 ZIP을 새 폴더에 풀고 폴더 구조를 유지한다. 다음 갱신 때도 이 장의 자료 버전이 바뀐 경우에만 다시 받는다.

> **핵심 질문** · HTTP 메시지를 직접 조립하지 않고 Python에서 상태·헤더·본문을 어떻게 읽을까요?

`requests`는 HTTP 클라이언트 라이브러리입니다. 06장에서 직접 다룬 연결과 바이트 처리를 감싸서 URL과 요청 조건을 전달하면 `Response` 객체를 돌려줍니다. 이 객체에는 본문 외에도 상태와 헤더가 들어 있습니다.

{% hint style="info" %}
### 실행 준비

[장 안내의 실습 환경](../07-http-api.md)을 따라 로컬 서버를 실행해 둡니다. 이 절의 예제는 별도 Python 실행 창 또는 파일에서 실행합니다. 코드 블록마다 필요한 변수와 import를 포함합니다.
{% endhint %}

## 1. 첫 응답은 파싱하기 전에 관찰합니다

```python
import requests

url = "http://127.0.0.1:8080/health"
with requests.get(url, timeout=(2, 3), allow_redirects=False) as response:
    print("상태:", response.status_code)
    print("형식:", response.headers.get("Content-Type"))
    print("본문:", response.text)
    print("본문 자료형:", type(response.text).__name__)
```

예상 출력:

```text
상태: 200
형식: application/json; charset=utf-8
본문: {"status": "ok", "service": "python-basic-lab"}
본문 자료형: str
```

본문이 딕셔너리처럼 보이지만 `response.text`의 자료형은 **문자열**입니다. 지금은 서버가 보낸 글을 읽은 단계입니다. `status`라는 필드로 접근하려면 다음 절에서 JSON을 Python 객체로 변환해야 합니다.

| 코드 | 역할 | 주의할 점 |
| --- | --- | --- |
| `requests.get(url, ...)` | GET 요청을 보내 Response 반환 | 응답까지 기다리는 동안 예외가 발생할 수 있음 |
| `timeout=(2, 3)` | 연결 대기 2초, 읽기 대기 3초 설정 | 전체 작업이 정확히 5초 안에 끝난다는 뜻은 아님 |
| `allow_redirects=False` | 이동 응답을 자동으로 따라가지 않음 | 처음 받은 상태와 `Location`을 관찰하기 위한 설정 |
| `with ... as response` | 응답 사용 뒤 자원 정리 | 특히 스트리밍 응답에서 중요 |

## 2. Response의 네 가지 창

| 속성 | 반환하는 값 | 질문 |
| --- | --- | --- |
| `status_code` | `int` | 어떤 상태 코드인가? |
| `headers` | 헤더 이름으로 조회하는 매핑 | 본문 형식 등 메타데이터는 무엇인가? |
| `text` | `str` | 문자로 해석한 본문은 무엇인가? |
| `content` | `bytes` | 바이트 형태의 본문은 무엇인가? |

`content`는 패킷 전체가 아닙니다. 상태 줄과 헤더가 포함되지 않는 **본문 바이트**이며, Requests가 지원하는 응답 압축은 해제될 수 있습니다. 06장에서 본 소켓의 원시 수신 데이터와 구분합니다.

## 3. 쿼리는 params로 전달합니다

`/api/echo`는 받은 `text`와 그 길이를 돌려줍니다. 쿼리는 URL에 붙는 매개변수이며 요청 본문과는 별개입니다.

```python
import requests

with requests.get(
    "http://127.0.0.1:8080/api/echo",
    params={"text": "hello world"},
    timeout=(2, 3),
    allow_redirects=False,
) as response:
    print(response.url)
    print(response.text)
```

```text
http://127.0.0.1:8080/api/echo?text=hello+world
{"text": "hello world", "length": 11}
```

`params`가 공백 등의 URL 인코딩을 처리합니다. `text`를 한글로 바꾸어 주소의 표현과 본문의 표현을 비교해 보세요. 서버는 문자열 길이가 200자를 넘으면 `400`으로 응답합니다.

## 4. 원하는 응답 형식을 헤더로 알립니다

```python
import requests

with requests.get(
    "http://127.0.0.1:8080/health",
    headers={"Accept": "application/json", "User-Agent": "python-basic-lab/1.0"},
    timeout=(2, 3),
    allow_redirects=False,
) as response:
    response.raise_for_status()
    if response.status_code != 200:
        raise ValueError("이 경로는 상태 코드 200을 기대합니다")
    media_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise ValueError("이 경로는 JSON 응답을 기대합니다")
    print(response.text)
```

`raise_for_status()`는 4xx·5xx에 대해 `HTTPError`를 발생시킵니다. **3xx를 거부하거나 본문을 검증하는 함수는 아닙니다.** 따라서 이 예제는 `/health`의 계약에 맞게 상태가 정확히 `200`인지도 확인합니다.

`Content-Type`에서 세미콜론 뒤의 매개변수를 분리하면 `application/json; charset=utf-8`의 기본 미디어 타입을 비교할 수 있습니다. 다른 API의 `application/problem+json` 등은 그 API의 계약에 맞게 처리하며, 이 실습은 `application/json`만 기대합니다.

## 5. 404도 응답 객체입니다

```python
import requests

with requests.get(
    "http://127.0.0.1:8080/missing",
    timeout=(2, 3),
    allow_redirects=False,
) as response:
    print(response.status_code)
    print(response.text)
    try:
        response.raise_for_status()
    except requests.HTTPError:
        print("HTTP 오류로 분류")
```

```text
404
{"error": "not found"}
HTTP 오류로 분류
```

응답을 받는 것과 요청이 성공한 것은 다른 사건입니다. 이 오류 본문도 JSON처럼 보입니다. 다음 절에서는 이 점을 이용해 **파싱 성공과 HTTP 성공을 구분**합니다.

## 직접 확인하기

| 실습 | 관찰할 내용 |
| --- | --- |
| `/health`와 `/missing` 비교 | 상태는 다르지만 둘 다 본문이 있음 |
| `params`의 문자열 변경 | URL 인코딩과 서버의 반영 결과 |
| `Accept`를 생략 | 이 서버는 여전히 JSON을 응답; 희망 헤더와 실제 형식은 별개 |

<details>
<summary>확인 문제: 본문 문자열에서 바로 status 키를 읽을 수 있을까요?</summary>

`response.text["status"]`는 사용할 수 없습니다. `text`는 문자열이므로 문자열 키로 조회하지 못합니다. 다음 절의 JSON 파싱을 거쳐 딕셔너리인지 확인한 뒤 필드에 접근합니다.

</details>

## 정리와 다음 단계

- [ ] Response 객체에서 상태·헤더·본문을 각각 읽습니다.
- [ ] `params`와 본문이 다름을 설명합니다.
- [ ] `raise_for_status()`만으로 본문 검증이 끝나지 않음을 설명합니다.

이제 응답을 관찰할 수 있습니다. 다음 절에서는 본문을 **프로그램이 사용할 데이터**로 바꿉니다.

참고: [Requests — Quickstart](https://requests.readthedocs.io/en/latest/user/quickstart/)

---

이전: [07-1. URL과 HTTP 메시지](07-1-url-http-messages.md) · 다음: [07-3. JSON API와 응답 검증](07-3-json-api.md)
