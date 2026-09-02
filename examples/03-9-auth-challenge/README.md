# 03-9 로컬 인증 챌린지 서버

교사가 제공하는 블랙박스 실습 환경이다. Linux 실행 파일 하나를 실행하면 `127.0.0.1:8000`에서 학습용 로그인 페이지가 열린다. 학생은 서버 구현이 아니라 Python의 문자열·리스트·딕셔너리·조건문·반복문·함수로 인증 시도와 이벤트 분석을 작성한다.

## 실행 파일 선택

교사가 미리 빌드한 파일을 배포할 때는 해당 Linux 구조의 실행 파일과 `lab_client.py`를 같은 실습 폴더에 제공한다.

- [Linux x86-64 실행 파일](dist/auth-lab-linux-amd64)
- [Linux ARM64 실행 파일](dist/auth-lab-linux-arm64)
- [SHA-256 체크섬](dist/SHA256SUMS)

Linux 터미널에서 `uname -m`으로 구조를 확인한다.

| `uname -m` 결과 | 실행 파일 |
| --- | --- |
| `x86_64` | `auth-lab-linux-amd64` |
| `aarch64`, `arm64` | `auth-lab-linux-arm64` |

실행 권한을 부여하고 서버를 시작한다.

```bash
chmod +x auth-lab-linux-amd64
./auth-lab-linux-amd64
```

브라우저에서 <http://127.0.0.1:8000/login>을 연다. 서버를 종료하려면 실행한 터미널에서 `Ctrl+C`를 누른다. 실행할 때마다 정답 계정·비밀번호 조합과 블루팀 토큰이 새로 만들어지고, 이전 이벤트는 사라진다.

포트가 사용 중이면 1024~65535 범위에서 바꿀 수 있다.

```bash
./auth-lab-linux-amd64 --port 8081
```

`lab_client.py`의 `BASE_URL`도 같은 포트로 바꿔야 한다.

## 제공 인터페이스

| 경로 | 용도 |
| --- | --- |
| `/login` | 브라우저용 GET 로그인 페이지 |
| `/api/challenge` | 후보 계정·비밀번호와 시도 상한 반환 |
| `/api/login` | 학생 프로그램의 인증 시도 한 건 처리 |
| `/api/events` | 블루팀 토큰을 검사한 뒤 원시 이벤트 반환 |
| `/blue?token=...` | 브라우저에서 원시 이벤트 확인 |
| `/health` | 서버 동작 확인 |

Python에서 HTTP 처리 자체는 제공된 `lab_client.py`가 담당한다.

```python
from lab_client import attempt_login, get_challenge

challenge = get_challenge()
print(challenge["accounts"])

result = attempt_login("student01", "연습용-후보")
print(result["result"])
```

위 코드는 사용법만 보여 준다. 계정과 비밀번호 후보를 조합하는 반복문, 성공 시 중단하는 조건, 시도 결과 집계는 학습자가 작성한다.

블루팀 단계에서는 서버 시작 화면에 표시된 토큰을 사용한다.

```python
from lab_client import get_events

events = get_events("서버에-표시된-블루팀-토큰")
```

서버는 `sequence`, `username`, `source`, `result`만 기록한다. 비밀번호 원문은 인증 이벤트에 저장하지 않는다.

## GET 실습의 의미

이 로그인 페이지는 URL 쿼리와 정보 노출 문제를 관찰하기 위해 의도적으로 GET을 사용한다. 실제 인증 구현의 모범 사례가 아니다. 학생은 주소창에 입력값이 나타나는 현상을 확인하고 다음을 설명해야 한다.

- GET 쿼리는 브라우저 기록과 중간 시스템의 URL 로그에 남을 수 있다.
- 실제 로그인은 POST와 HTTPS를 사용해야 한다.
- 성공·실패 로그에도 비밀번호 원문을 기록하면 안 된다.

## 실습 범위

- 제공된 `127.0.0.1` 서버만 대상으로 한다.
- 서버는 외부 인터페이스에 바인딩하지 않는다.
- 더미 후보만 사용하고 실제 계정정보를 입력하지 않는다.
- 기본 최대 시도 횟수는 40회이며 최대 200회를 넘길 수 없다.
- 병렬 요청, 우회, 외부 주소 입력 기능을 추가하지 않는다.
- 종료 후 다시 실행하면 정답과 메모리 이벤트가 초기화된다.

## 교사용 빌드

Go 1.22 이상이 설치된 환경에서 다음 명령을 실행한다.

```bash
chmod +x build-linux.sh
./build-linux.sh
```

`dist/`에 x86-64와 ARM64 Linux 실행 파일 및 `SHA256SUMS`가 생성된다. 소스 변경 후에는 `go test ./...`를 먼저 실행하고 실행 파일을 다시 배포한다.
