# 13-3. 웹 정보 수집

웹 자동화는 요청을 보내는 기술보다 수집 범위, 응답 계약, 속도 제한, 변경 감지를 설계하는 일이 더 중요합니다. 가능하면 HTML 화면보다 공식 API를 우선합니다.

{% hint style="info" %}
## 🧭 학습 목표

- API, 정적 HTML, 브라우저 자동화의 선택 기준을 설명합니다.
- 타임아웃·상태·형식·크기를 검증합니다.
- 상대 URL과 콘텐츠를 해석합니다.
- 서비스 정책·개인정보·수집 주기를 통제합니다.
{% endhint %}

## 1. 가장 안정적인 접근부터 선택

1. **공식 API**: 필드와 오류 형식이 정의되어 있으면 가장 먼저 선택합니다.
2. **정적 HTML**: 서버가 보낸 HTML에 필요한 데이터가 있을 때 `requests`와 Beautiful Soup을 사용합니다.
3. **브라우저 자동화**: JavaScript 실행·사용자 상호작용이 필수인 경우에만 사용합니다.

CSS 선택자와 화면 좌표에 강하게 의존할수록 사이트 변경에 취약해집니다.

## 2. 수집 전 확인

- 명시적으로 허용된 사이트와 경로인가?
- 사이트 이용 약관과 `robots.txt`를 확인했는가?
- 로그인, 유료 콘텐츠, 개인정보를 수집하지 않는가?
- 요청 주기와 최대 건수가 서버에 부담을 주지 않는가?
- 저장 기간·접근 권한·삭제 방법이 있는가?

`robots.txt`는 접근 권한을 부여하는 문서가 아니며, 허용 범위는 이용 약관과 소유자의 승인을 함께 확인해야 합니다.

## 3. 제한이 있는 HTTP 요청

```python
import requests

MAX_BYTES = 2 * 1024 * 1024


def download_html(url):
    with requests.get(
        url,
        timeout=(3.05, 10),
        stream=True,
        headers={"User-Agent": "Python-Automate-Class/1.0"},
    ) as response:
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type.lower():
            raise ValueError(f"예상하지 않은 형식: {content_type}")

        chunks = []
        size = 0
        for chunk in response.iter_content(64 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError("응답 크기 제한을 초과했습니다.")
            chunks.append(chunk)

        return b"".join(chunks).decode(
            response.encoding or "utf-8",
            errors="replace",
        )
```

연결 타임아웃과 응답 타임아웃을 두고, 전체 응답 크기를 제한합니다. `Content-Length`는 없거나 부정확할 수 있으므로 실제로 읽은 바이트도 계산합니다.

## 4. HTML 해석

```python
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def extract_articles(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    for article in soup.select("article"):
        heading = article.select_one("h2")
        link = article.select_one("a[href]")
        if heading is None or link is None:
            continue

        rows.append({
            "title": heading.get_text(" ", strip=True),
            "url": urljoin(base_url, link["href"]),
        })

    return rows
```

하나의 선택자에 모든 규칙을 묶지 말고, 필수 필드·선택 필드·누락 건수를 나누어 기록합니다.

## 5. 변경 감지와 저장

웹 데이터에는 수집 시각, 원본 URL, 응답 식별자를 함께 저장합니다.

- `ETag`, `Last-Modified`가 있으면 조건부 요청에 활용합니다.
- 중복 URL과 중복 콘텐츠 해시를 분리합니다.
- HTML 전체보다 필요한 정규화 필드를 저장합니다.
- 원본을 저장해야 한다면 보관 기간과 접근 권한을 적용합니다.

## 6. 재시도 정책

| 상황 | 기본 동작 |
| --- | --- |
| 연결 실패·타임아웃 | 지수 백오프로 제한적 재시도 |
| 429 | `Retry-After`를 존중하고 재시도 횟수 제한 |
| 500·502·503·504 | 일시 장애로 판단하되 제한적 재시도 |
| 400·401·403·404 | 요청·권한·경로를 수정하기 전에 재시도하지 않음 |

POST·전송·결제처럼 상태를 변경하는 요청은 멱등성 키나 처리 ID 확인 없이 자동 재시도하지 않습니다.

## 7. 로컬 재현 실습

외부 사이트 대신 실습용 HTML을 로컬 서버로 제공합니다.

```bash
cd lab-site
python -m http.server 8000 --bind 127.0.0.1
```

다음 상황을 별도 HTML 파일로 만듭니다.

- 정상 기사 3건
- 제목이 없는 기사 1건
- 상대 URL과 절대 URL이 섞인 링크
- 크기 제한을 넘는 응답

## 완료 기준

- [ ] API가 있는지 먼저 확인했습니다.
- [ ] 수집 범위와 요청 주기를 정의했습니다.
- [ ] 타임아웃·상태·형식·크기를 검증합니다.
- [ ] 누락 필드와 파싱 오류 건수를 보존합니다.
- [ ] 재시도해야 할 실패와 즉시 중단할 실패를 구분합니다.

---

다음: [13-4. 스프레드시트와 문서 자동화](13-4-spreadsheet-documents.md)
