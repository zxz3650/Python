# 실습 자료 받기와 시작하기

각 챕터의 첫머리에서 **그 장의 교육자료 ZIP**을 내려받는다. ZIP에는 해당 장의 노트북과 필요한 코드·입력 데이터가 함께 들어 있다. 다른 장의 자료는 그 장을 시작할 때 받는다.

[챕터별 다운로드와 자료 버전](downloads/README.md)에서 현재 배포본을 확인한다. 개별 노트북의 학습 내용은 [Jupyter 실습 색인](notebooks/README.md)에서 확인한다.

<a id="download"></a>

## 해당 챕터 자료 받기

1. 수강할 챕터의 **교육자료 ZIP 받기**를 선택한다.
2. ZIP을 새 폴더에 압축 해제한다. 폴더 이름은 `chapter-05-자료버전/`처럼 장 번호와 자료 버전으로 구성된다.
3. 안에 있는 `START-HERE.md`를 읽고, `requirements.txt`가 있는 폴더에서 터미널을 연다.
4. [02장](02-python-setup.md)에서 만든 과정용 가상환경을 활성화한다. 처음 시작하거나 이 장의 요구 패키지가 추가됐을 때 다음 명령으로 설치한다.

```bash
python -m pip install -r requirements.txt
python -m jupyterlab
```

같은 과정용 가상환경을 다른 장에서도 사용할 수 있다. 각 ZIP의 `requirements.txt`에는 해당 장에 필요한 패키지가 기록되어 있다. JupyterLab에서 `notebooks/`를 열고 해당 절의 파일과 과정용 커널을 선택한다. 셀에서 `import sys; print(sys.executable)`을 실행해 터미널의 Python 경로와 비교한다.

교안에서 말하는 **저장소 루트**는 챕터 ZIP에서는 `requirements.txt`가 있는 폴더를 뜻한다. 예제의 상대 경로가 유지되도록 ZIP 안의 폴더를 함께 보관한다. 05장 ZIP에는 실습 입력 데이터와 풀이 참고 파일이, 08장 ZIP에는 실습에 필요한 07장 서버 코드가 포함된다. 13장 ZIP에는 현재 KAPE 프로젝트가 포함된다.

개별 노트북의 **원본 받기** 링크는 파일 하나만 확인하거나 받을 때 사용한다. JSON이 보이면 링크를 ‘다른 이름으로 저장’하고 확장자를 `.ipynb`로 유지한다. 코드·입력 데이터와 버전을 맞춰 실습하려면 해당 챕터 ZIP을 기준으로 진행한다.

## 학습 자료와 풀이 구분

| 자료 | 사용하는 시점 |
| --- | --- |
| 03~04장 절별 노트북 | 본문 개념을 읽고 예측·실행·변경·검증을 반복할 때 |
| 03-9·04-9 종합 실습 노트북 | 과제 구현을 먼저 시도한 뒤 참고 구현과 비교할 때 |
| 05장 `notebooks/05-*.ipynb` | TODO와 공개 검증을 활용해 직접 구현할 때 |
| [05장 풀이 검증용 노트북](notebooks/solutions/README.md) | 자신의 구현과 결과를 비교할 때 |
| 01~02·06~13장 예제 노트북 | 장별 핵심 동작을 실행하고 오류·경계 사례를 확인할 때 |

05장 학습자용 노트북은 TODO를 완성하기 전 검증이 실패할 수 있다. 먼저 빈 구현을 채우고 결과를 확인한다. 마지막에는 커널을 재시작하고 전체 셀을 다시 실행해 이전 실행 순서에 의존하지 않는지 점검한다. 여러 장에서 만든 결과 파일은 교안에 지정된 출력 위치에 저장한다.

08~11장은 현재 표지의 **작업중** 상태를 유지한다. 예제 노트북이 제공되더라도 해당 교안의 완성 상태가 바뀌는 것은 아니다. 09~12장은 장별 개요에 대응하는 노트북을 제공한다.

## 최신 자료로 갱신하기

[다운로드 목록](downloads/README.md)의 해당 장 자료 버전과, 받은 폴더 안 `MANIFEST.json`의 `version`을 비교한다.

- 버전이 같으면 실습 파일은 동일하므로 다시 받지 않는다. 교안 설명만 바뀐 경우도 여기에 해당한다.
- 버전이 다르면 **그 장의 ZIP만** 새 폴더에 풀고, 기존 개인 풀이와 변경 내용을 비교해 옮긴다.
- 다른 장의 폴더와 개인 풀이는 그대로 사용한다.

자료 버전은 실습 파일 묶음을 식별하는 값이다. 설치한 패키지 버전까지 고정하는 값은 아니므로 같은 수업에서는 교수자가 안내한 자료 버전과 과정용 Python 환경을 함께 확인한다.

## 폴더별 역할

| 위치 | 내용 | 학습자가 여는 기준 |
| --- | --- | --- |
| `notebooks/` | 실행 예제와 학습자용 노트북 | 아래 장별 목록에서 선택 |
| `notebooks/solutions/` | 05장 풀이 참고 구현 | 직접 구현한 뒤 비교 |
| [examples 실습 안내](examples/README.md) | 시작 코드, 서버·CLI·종합 프로젝트 | 해당 장에서 터미널 실습을 안내할 때 |
| `fixtures/` | 고정된 실습 입력 데이터 | 노트북과 코드가 정해진 경로로 읽음 |
| `tests/` | 프로젝트 결과 검증 | 교안에서 지정한 검증 명령으로 실행 |
| `START-HERE.md` | 받은 챕터의 실행 안내 | 압축 해제 후 먼저 읽음 |
| `MANIFEST.json` | 자료 버전과 포함 파일 목록 | 해당 장 갱신 여부를 확인 |

<a id="chapters"></a>

## 장별 노트북 선택

<a id="chapter-01"></a>

### 01. Python 소개

[이 장의 교안](01-python-intro.md) · [01장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-01.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 01. Python 소개 | [01-python-first-step.ipynb](notebooks/01-python-first-step.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/01-python-first-step.ipynb) |

<a id="chapter-02"></a>

### 02. 개발 및 실습 환경

[이 장의 교안](02-python-setup.md) · [02장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-02.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 02. 개발 및 실습 환경 | [02-environment-check.ipynb](notebooks/02-environment-check.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/02-environment-check.ipynb) |

<a id="chapter-03"></a>

### 03. Python 기초 문법

[이 장의 교안](03-python-basics.md) · [03장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-03.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 03-1. 변수와 기본 자료형 | [03-1-data-types.ipynb](notebooks/03-1-data-types.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/03-1-data-types.ipynb) |
| 03-2. 문자열과 자료구조 | [03-2-strings-collections.ipynb](notebooks/03-2-strings-collections.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/03-2-strings-collections.ipynb) |
| 03-3. 조건문과 논리 | [03-3-conditions-logic.ipynb](notebooks/03-3-conditions-logic.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/03-3-conditions-logic.ipynb) |
| 03-4. 반복문: for와 while | [03-4-loops.ipynb](notebooks/03-4-loops.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/03-4-loops.ipynb) |
| 03-5. 함수와 스코프 | [03-5-functions-scope.ipynb](notebooks/03-5-functions-scope.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/03-5-functions-scope.ipynb) |
| 03-6. 예외 처리 | [03-6-exceptions.ipynb](notebooks/03-6-exceptions.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/03-6-exceptions.ipynb) |
| 03-7. 모듈과 패키지 | [03-7-modules-packages.ipynb](notebooks/03-7-modules-packages.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/03-7-modules-packages.ipynb) |
| 03-8. 클래스 기초 | [03-8-classes-dataclasses.ipynb](notebooks/03-8-classes-dataclasses.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/03-8-classes-dataclasses.ipynb) |
| 03-9. 문법 종합 실습 | [03-9-syntax-project.ipynb](notebooks/03-9-syntax-project.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/03-9-syntax-project.ipynb) |

종합 실습의 시작 코드는 [이벤트 검토 프로그램](examples/03-9-event-review-starter/README.md)을 사용한다.

<a id="chapter-04"></a>

### 04. 파일 입출력과 데이터 형식

[이 장의 교안](04-file-io.md) · [04장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-04.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 04-1. 경로·작업 디렉터리·안전한 경로 검증 | [04-1-paths-filesystem.ipynb](notebooks/04-1-paths-filesystem.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/04-1-paths-filesystem.ipynb) |
| 04-2. 파일·디렉터리 조작과 작업 범위 | [04-2-filesystem-operations.ipynb](notebooks/04-2-filesystem-operations.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/04-2-filesystem-operations.ipynb) |
| 04-3. 텍스트 파일·모드·with·줄바꿈 | [04-3-text-files.ipynb](notebooks/04-3-text-files.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/04-3-text-files.ipynb) |
| 04-4. 인코딩·bytes와 바이너리 구조 | [04-4-encoding-binary.ipynb](notebooks/04-4-encoding-binary.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/04-4-encoding-binary.ipynb) |
| 04-5. CSV 읽기·검증·안전한 출력 | [04-5-csv.ipynb](notebooks/04-5-csv.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/04-5-csv.ipynb) |
| 04-6. JSON·JSON Lines와 직렬화 검증 | [04-6-json-jsonl.ipynb](notebooks/04-6-json-jsonl.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/04-6-json-jsonl.ipynb) |
| 04-7. 대용량 스트리밍과 오류 복구 | [04-7-streaming-errors.ipynb](notebooks/04-7-streaming-errors.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/04-7-streaming-errors.ipynb) |
| 04-8. 임시 파일과 원자적 저장 | [04-8-safe-output.ipynb](notebooks/04-8-safe-output.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/04-8-safe-output.ipynb) |
| 04-9. 파일 분석기 종합 실습 | [04-9-file-analyzer.ipynb](notebooks/04-9-file-analyzer.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/04-9-file-analyzer.ipynb) |

종합 실습의 참고 실행 코드는 [파일 분석기](examples/04-file-analyzer/file_analyzer.py)다.

<a id="chapter-05"></a>

### 05. 텍스트 파싱과 데이터 분석

[이 장의 교안](05-text-processing.md) · [05장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-05.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 05-1. 문자열 정규화 | [05-1-normalization.ipynb](notebooks/05-1-normalization.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-1-normalization.ipynb) |
| 05-2. 분리·검색·치환 | [05-2-split-search-replace.ipynb](notebooks/05-2-split-search-replace.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-2-split-search-replace.ipynb) |
| 05-3. 정규표현식 기초 | [05-3-regex-basics.ipynb](notebooks/05-3-regex-basics.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-3-regex-basics.ipynb) |
| 05-3. 보안 로그 정규식 보충 예제 | [05-3-security-log-patterns.ipynb](notebooks/05-3-security-log-patterns.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-3-security-log-patterns.ipynb) |
| 05-4. 그룹과 캡처 | [05-4-groups-capture.ipynb](notebooks/05-4-groups-capture.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-4-groups-capture.ipynb) |
| 05-5. 데이터 검증 | [05-5-validation.ipynb](notebooks/05-5-validation.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-5-validation.ipynb) |
| 05-6. 날짜와 시간 | [05-6-datetime.ipynb](notebooks/05-6-datetime.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-6-datetime.ipynb) |
| 05-7. NumPy 배열과 대용량 수치 처리 | [05-7-numpy-array.ipynb](notebooks/05-7-numpy-array.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-7-numpy-array.ipynb) |
| 05-8. pandas와 DataFrame 기반 대용량 처리 | [05-8-pandas-dataframe.ipynb](notebooks/05-8-pandas-dataframe.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-8-pandas-dataframe.ipynb) |
| 05-9. 웹 접근 로그 분석 종합 실습 | [05-9-web-log-analysis.ipynb](notebooks/05-9-web-log-analysis.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/05-9-web-log-analysis.ipynb) |

[입력 데이터 안내](fixtures/05-text-processing/README.md)를 함께 읽는다. 풀이 파일은 구현 후 비교한다.

<a id="chapter-06"></a>

### 06. 네트워크 프로그래밍

[이 장의 교안](06-network-programming.md) · [06장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-06.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 06-1. 네트워크와 소켓 기초 | [06-1-network-socket-basics.ipynb](notebooks/06-1-network-socket-basics.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/06-1-network-socket-basics.ipynb) |
| 06-2. TCP 클라이언트 | [06-2-tcp-client.ipynb](notebooks/06-2-tcp-client.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/06-2-tcp-client.ipynb) |
| 06-3. TCP 서버 | [06-3-tcp-server.ipynb](notebooks/06-3-tcp-server.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/06-3-tcp-server.ipynb) |
| 06-4. 메시지 경계와 프로토콜 설계 | [06-4-message-framing.ipynb](notebooks/06-4-message-framing.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/06-4-message-framing.ipynb) |
| 06-5. UDP 통신 | [06-5-udp.ipynb](notebooks/06-5-udp.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/06-5-udp.ipynb) |
| 06-6. DNS와 주소 해석 | [06-6-dns-address-resolution.ipynb](notebooks/06-6-dns-address-resolution.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/06-6-dns-address-resolution.ipynb) |
| 06-7. 타임아웃·오류·재시도 | [06-7-timeouts-errors.ipynb](notebooks/06-7-timeouts-errors.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/06-7-timeouts-errors.ipynb) |
| 06-8. 로컬 Echo 통신 프로젝트 | [06-8-echo-project.ipynb](notebooks/06-8-echo-project.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/06-8-echo-project.ipynb) |

서버와 클라이언트 실행 자료는 [examples 실습 안내](examples/README.md)의 06장 항목에서 확인한다.

<a id="chapter-07"></a>

### 07. HTTP와 API

[이 장의 교안](07-http-api.md) · [07장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-07.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 07-1. URL과 HTTP 메시지 | [07-1-url-http-messages.ipynb](notebooks/07-1-url-http-messages.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/07-1-url-http-messages.ipynb) |
| 07-2. requests 기초 | [07-2-requests-basics.ipynb](notebooks/07-2-requests-basics.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/07-2-requests-basics.ipynb) |
| 07-3. JSON API와 응답 검증 | [07-3-json-api.ipynb](notebooks/07-3-json-api.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/07-3-json-api.ipynb) |
| 07-4. 세션·쿠키·인증 | [07-4-sessions-cookies-auth.ipynb](notebooks/07-4-sessions-cookies-auth.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/07-4-sessions-cookies-auth.ipynb) |
| 07-5. 오류·타임아웃·재시도 | [07-5-errors-timeouts-retries.ipynb](notebooks/07-5-errors-timeouts-retries.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/07-5-errors-timeouts-retries.ipynb) |
| 07-6. HTTP 보안 검증 기초 | [07-6-http-security-validation.ipynb](notebooks/07-6-http-security-validation.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/07-6-http-security-validation.ipynb) |
| 07-7. 로컬 네트워크·웹 보안 점검 프로젝트 | [07-7-local-web-security-project.ipynb](notebooks/07-7-local-web-security-project.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/07-7-local-web-security-project.ipynb) |

로컬 서버 실행 자료는 [examples 실습 안내](examples/README.md)의 07장 항목에서 확인한다.

<a id="chapter-08"></a>

### 08. 시스템 자동화

[이 장의 교안](08-system-automation.md) · [08장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-08.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 08-1. 명령줄 인터페이스와 종료 상태 | [08-1-cli-exit-status.ipynb](notebooks/08-1-cli-exit-status.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/08-1-cli-exit-status.ipynb) |
| 08-2. 설정 우선순위와 환경 변수 | [08-2-configuration-environment.ipynb](notebooks/08-2-configuration-environment.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/08-2-configuration-environment.ipynb) |
| 08-3. 실행 로그와 관찰 가능성 | [08-3-logging-observability.ipynb](notebooks/08-3-logging-observability.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/08-3-logging-observability.ipynb) |
| 08-4. 안전한 외부 프로세스 실행 | [08-4-safe-subprocess.ipynb](notebooks/08-4-safe-subprocess.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/08-4-safe-subprocess.ipynb) |
| 08-5. 로컬 HTTP 점검기 도구화 프로젝트 | [08-5-toolization-project.ipynb](notebooks/08-5-toolization-project.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/08-5-toolization-project.ipynb) |

실제 CLI 실행·종료 상태 검증은 [도구화 프로젝트](examples/08-toolization-project/README.md)에서 진행한다.

<a id="chapter-09"></a>

### 09. 테스트와 디버깅

[이 장의 교안](09-testing-debugging.md) · [09장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-09.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 09. 테스트와 디버깅 | [09-testing-debugging.ipynb](notebooks/09-testing-debugging.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/09-testing-debugging.ipynb) |

<a id="chapter-10"></a>

### 10. 프로그램 구조화

[이 장의 교안](10-program-architecture.md) · [10장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-10.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 10. 프로그램 구조화 | [10-program-architecture.ipynb](notebooks/10-program-architecture.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/10-program-architecture.ipynb) |

<a id="chapter-11"></a>

### 11. 동시성과 비동기 처리

[이 장의 교안](11-concurrency.md) · [11장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-11.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 11. 동시성과 비동기 처리 | [11-concurrency.ipynb](notebooks/11-concurrency.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/11-concurrency.ipynb) |

<a id="chapter-12"></a>

### 12. Python 활용 종합 프로젝트

[이 장의 교안](12-capstone.md) · [12장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-12.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 12. Python 활용 종합 프로젝트 | [12-capstone.ipynb](notebooks/12-capstone.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/12-capstone.ipynb) |

<a id="chapter-13"></a>

### 13. Python Automate 실무 자동화

[이 장의 교안](13-python-automate.md) · [13장 교육자료 ZIP 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/downloads/chapter-13.zip) · [자료 버전 확인](downloads/README.md)

| 학습 항목 | 노트북 | 다운로드 |
| --- | --- | --- |
| 13-1. DFIR 자동화 과제와 분석 범위 | [13-1-automation-design.ipynb](notebooks/13-1-automation-design.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/13-1-automation-design.ipynb) |
| 13-2. KAPE 결과 구조와 증거 목록 | [13-2-file-batch.ipynb](notebooks/13-2-file-batch.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/13-2-file-batch.ipynb) |
| 13-3. 아티팩트 파서와 분석 엔진 연계 | [13-3-web-collection.ipynb](notebooks/13-3-web-collection.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/13-3-web-collection.ipynb) |
| 13-4. 공통 스키마·시간 정규화·보고서 | [13-4-spreadsheet-documents.ipynb](notebooks/13-4-spreadsheet-documents.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/13-4-spreadsheet-documents.ipynb) |
| 13-5. 완료 감지·워커·재실행 관리 | [13-5-scheduling-gui.ipynb](notebooks/13-5-scheduling-gui.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/13-5-scheduling-gui.ipynb) |
| 13-6. 프로젝트 A - KAPE 결과 정규화 | [13-6-safe-file-organizer-project.ipynb](notebooks/13-6-safe-file-organizer-project.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/13-6-safe-file-organizer-project.ipynb) |
| 13-7. 프로젝트 B - Windows 아티팩트 통합 분석 | [13-7-spreadsheet-report-project.ipynb](notebooks/13-7-spreadsheet-report-project.ipynb) | [원본 받기](https://github.com/zxz3650/Python/raw/refs/heads/master/notebooks/13-7-spreadsheet-report-project.ipynb) |

현재 종합 프로젝트는 [KAPE 후처리·Windows 아티팩트 통합 분석](examples/13-kape-triage/README.md)이다. 이전 13장 예제와 구분한다.
