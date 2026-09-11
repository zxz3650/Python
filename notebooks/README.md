# 주피터 실습

처음 자료를 받는다면 [실습 자료 받기와 시작하기](../PRACTICE.md)를 먼저 읽습니다. 챕터별 교육자료 ZIP과 개별 노트북 다운로드, 커널 확인과 해당 장만 갱신하는 방법을 안내합니다. 이 페이지는 각 노트북의 학습 내용과 활용 시점을 설명하는 색인입니다.

01~13장 노트북은 Python 3.10 이상에서 실행하며 Python 3.12를 권장합니다. 커널 버전은 첫 셀을 실행하기 전에 `import sys; print(sys.version)`으로 확인하세요.

## 01~02장 시작 및 환경 점검

- [`01-python-first-step.ipynb`](01-python-first-step.ipynb): 입력·처리·검증·출력의 흐름을 작은 이벤트 집계로 처음 실행합니다.
- [`02-environment-check.ipynb`](02-environment-check.ipynb): 현재 커널의 Python 버전과 과정용 패키지 설치 상태를 변경 없이 점검합니다.

02장 Notebook은 패키지를 직접 설치하지 않습니다. 누락 항목은 과정용 가상환경을 활성화한 터미널에서 `python -m pip install -r requirements.txt`로 설치합니다.

## 절별 기초 실습

- [`03-1-data-types.ipynb`](03-1-data-types.ipynb): 변수, 기본 자료형, 명시적 형변환, 형식과 범위 검증의 차이를 외부 모듈 없이 연습합니다.
- [`03-2-strings-collections.ipynb`](03-2-strings-collections.ipynb): 문자열 처리, 자료구조 선택, 중첩 구조, 별칭과 복사를 조건문·반복문 없이 연습합니다.
- [`03-3-conditions-logic.ipynb`](03-3-conditions-logic.ipynb): 비교·논리 연산자, 우선순위, 단락 평가, truthy/falsey, 결정표 기반 단일 이벤트 분류를 연습합니다.
- [`03-4-loops.ipynb`](03-4-loops.ipynb): `for`·`while`, 반복 종료, 카운트·누적·필터·검색·집계 패턴, 안전한 컬렉션 순회, 이벤트 목록 분석을 연습합니다.
- [`03-5-functions-scope.ipynb`](03-5-functions-scope.ipynb): 함수 계약, 인자 전달, 반환값, 변경 가능한 기본값, 객체 변경, 스코프, 콜백, 이벤트 분석 함수 분리를 연습합니다.
- [`03-6-exceptions.ipynb`](03-6-exceptions.ipynb): traceback, 예외 전파, `try` 흐름, 예외 연결, 입력 검증, 배치 처리 정책을 연습합니다.
- [`03-7-modules-packages.ipynb`](03-7-modules-packages.ipynb): 과정별 모듈 지도, import 이름, 모듈 캐시·검색 경로, 일반 패키지, 상대 import, `python -m`, import 오류 진단을 연습합니다.
- [`03-8-classes-dataclasses.ipynb`](03-8-classes-dataclasses.ipynb): 클래스·인스턴스, 메서드 바인딩, 클래스 변수, 상태 전이, property, dataclass, 상속·합성, 이벤트 객체 모델을 연습합니다.
- [`03-9-syntax-project.ipynb`](03-9-syntax-project.ipynb): 03-1~03-8의 문법을 이벤트 검토 큐에 통합하고 일반 데이터클래스, 명시적 반복문, 명령 파서, 오류 복구 세션, 터미널과 분리된 자동 시나리오를 단계별로 검증합니다.

처음 Python 문법을 학습한다면 번호 순서대로 실행하세요. 각 셀은 결과를 먼저 예측하고, 실행 결과를 설명한 뒤 값을 변경하는 순서로 구성되어 있습니다.

`03-9-syntax-project.ipynb`는 본문의 접힌 참고 구현 중 데이터·저장소·명령·세션 로직을 한 커널에서 실행하는 풀이 검증용 노트북입니다. 패키지 분리, 상대 import, 공개 API, `python -m` 실행은 다루지 않으므로 `examples/03-9-event-review-starter`에서 별도로 완성하고 검증합니다. 학습자는 시작 코드를 먼저 구현하고 막히는 단계에서만 해당 노트북 셀을 비교합니다.

## 04장 절별 실습

- [`04-1-paths-filesystem.ipynb`](04-1-paths-filesystem.ipynb): 상대·절대 경로, 현재 작업 디렉터리, 파일 종류·메타데이터, 허용된 작업 영역 검증을 연습합니다.
- [`04-2-filesystem-operations.ipynb`](04-2-filesystem-operations.ipynb): 전용 실습 영역에서 파일·디렉터리 생성, 복사, 이동, 이름 변경, 충돌 처리와 정확한 삭제를 연습합니다.
- [`04-3-text-files.ipynb`](04-3-text-files.ipynb): 텍스트 파일 모드, `with`, 전체·줄 단위 읽기, 쓰기·추가, 줄바꿈 처리를 연습합니다.
- [`04-4-encoding-binary.ipynb`](04-4-encoding-binary.ipynb): `str`·`bytes`, 인코딩, 디코딩, 바이너리 위치·길이·바이트 순서와 구조 검증을 연습합니다.
- [`04-5-csv.ipynb`](04-5-csv.ipynb): CSV 규칙, 헤더·행·자료형 검증, 안전한 출력과 스프레드시트 수식 처리 정책을 연습합니다.
- [`04-6-json-jsonl.ipynb`](04-6-json-jsonl.ipynb): JSON 직렬화·역직렬화, 엄격한 파싱과 구조 검증, JSON Lines 순차 처리를 연습합니다.
- [`04-7-streaming-errors.ipynb`](04-7-streaming-errors.ipynb): 제너레이터와 줄 단위 스트리밍, 레코드 단위 오류 복구, 처리 통계와 메모리 범위를 연습합니다.
- [`04-8-safe-output.ipynb`](04-8-safe-output.ipynb): 출력 구조 검증, 고유한 임시 파일, 원자적 교체, 실패 후 정리와 기존 결과 보존을 연습합니다.
- [`04-9-file-analyzer.ipynb`](04-9-file-analyzer.ipynb): 학습자가 파일 분석기를 직접 구현한 뒤 메타데이터·해시·헤더·형식별 분석·원자적 저장을 셀 단위로 다시 검증합니다.

04-1~04-8은 개념을 익힌 뒤 바로 실행하는 학습자용 실습입니다. 04-9는 정답 코드를 먼저 보는 자료가 아니라, 요구사항에 맞게 직접 구현한 뒤 기준 구현과 결과를 비교하는 풀이 검증용 노트북입니다.

## 05장 절별 실습

- [`05-1-normalization.ipynb`](05-1-normalization.ipynb): 원문을 보존하며 필드별 공백·대소문자·유니코드 정규화를 연습합니다.
- [`05-2-split-search-replace.ipynb`](05-2-split-search-replace.ipynb): 고정 구분자 형식, 필드 수, 메시지 내 구분자 경계를 연습합니다.
- [`05-3-regex-basics.ipynb`](05-3-regex-basics.ipynb): 부분 검색과 전체 일치, 정상·경계·실패 패턴을 연습합니다.
- [`05-4-groups-capture.ipynb`](05-4-groups-capture.ipynb): 이름 있는 그룹으로 날짜·수준·메시지를 구조화합니다.
- [`05-5-validation.ipynb`](05-5-validation.ipynb): 필수값·형식·허용값·범위 오류를 구조화합니다.
- [`05-6-datetime.ipynb`](05-6-datetime.ipynb): KST(UTC+09:00) 설정·출력, ISO 8601, naive/aware datetime, UTC↔KST 변환과 날짜 변경을 연습합니다.
- [`05-7-numpy-array.ipynb`](05-7-numpy-array.ipynb): 결측값·조건 마스크·벡터 집계를 연습합니다.
- [`05-8-pandas-dataframe.ipynb`](05-8-pandas-dataframe.ipynb): 숫자 변환 오류 보존, DataFrame 집계, `chunksize` 처리를 연습합니다.
- [`05-9-web-log-analysis.ipynb`](05-9-web-log-analysis.ipynb): strict 디코딩, IP·URL 검증, 5분 특징, NumPy 후보 마스크, 민감정보 가명처리를 통합합니다.

05장의 절별 Notebook은 함수 시그니처·TODO·공개 경계 검증을 담은 **학습자용** 파일입니다. 실습 입력은 [`../fixtures/05-text-processing/`](../fixtures/05-text-processing/README.md)에 있으며, 자신의 구현을 먼저 완성한 뒤 [`solutions/`](solutions/README.md)의 풀이 검증용 Notebook과 비교합니다. 공개 저장소의 풀이는 평가 정답을 숨기지 못하므로 실제 평가에서는 교수자용 비공개 테스트를 별도로 사용합니다.

## 06장 네트워크 프로그래밍 예제

- [`06-1-network-socket-basics.ipynb`](06-1-network-socket-basics.ipynb): IP·포트·주소 체계와 루프백 작업 범위를 검증합니다.
- [`06-2-tcp-client.ipynb`](06-2-tcp-client.ipynb): 부분 수신과 연결 종료를 가짜 소켓으로 재현합니다.
- [`06-3-tcp-server.ipynb`](06-3-tcp-server.ipynb): 외부 포트 없이 한 요청을 처리하는 서버 경계를 확인합니다.
- [`06-4-message-framing.ipynb`](06-4-message-framing.ipynb): 길이 접두사 프레임과 불완전 버퍼를 처리합니다.
- [`06-5-udp.ipynb`](06-5-udp.ipynb): 데이터그램 단위 크기·인코딩 오류를 분리합니다.
- [`06-6-dns-address-resolution.ipynb`](06-6-dns-address-resolution.ipynb): localhost의 IPv4·IPv6 결과와 허용 범위를 확인합니다.
- [`06-7-timeouts-errors.ipynb`](06-7-timeouts-errors.ipynb): 제한된 재시도와 지수형 대기 계획을 검증합니다.
- [`06-8-echo-project.ipynb`](06-8-echo-project.ipynb): 제공 프로토콜 모듈로 로컬 Echo 왕복을 검증합니다.

실제 `bind()`·`listen()`·클라이언트 연결은 터미널 예제에서 수행합니다. Notebook은 외부 주소에 연결하거나 포트 스캔을 수행하지 않습니다.

## 07장 HTTP와 API 예제

- [`07-1-url-http-messages.ipynb`](07-1-url-http-messages.ipynb): URL 구성요소와 HTTP 요청 대상을 구분합니다.
- [`07-2-requests-basics.ipynb`](07-2-requests-basics.ipynb): 가짜 응답으로 상태·Content-Type·응답 크기 제한을 확인합니다.
- [`07-3-json-api.ipynb`](07-3-json-api.ipynb): JSON 문법·중복 키·응답 계약 오류를 구분합니다.
- [`07-4-sessions-cookies-auth.ipynb`](07-4-sessions-cookies-auth.ipynb): 쿠키 속성과 인증 헤더 마스킹을 연습합니다.
- [`07-5-errors-timeouts-retries.ipynb`](07-5-errors-timeouts-retries.ipynb): 상태·메서드·횟수별 재시도 정책을 계산합니다.
- [`07-6-http-security-validation.ipynb`](07-6-http-security-validation.ipynb): 루프백 범위와 보안 헤더 관찰 결과를 검증합니다.
- [`07-7-local-web-security-project.ipynb`](07-7-local-web-security-project.ipynb): 고정된 가짜 응답으로 점검 보고서를 통합합니다.

Notebook은 외부 HTTP 요청을 보내지 않습니다. 실제 로컬 서버 점검은 `examples/07-local-web-security-lab`에서 수행합니다.

## 08장 시스템 자동화 예제

- [`08-1-cli-exit-status.ipynb`](08-1-cli-exit-status.ipynb): `main(argv)`와 종료 상태를 검증합니다.
- [`08-2-configuration-environment.ipynb`](08-2-configuration-environment.ipynb): 기본값·JSON·환경 변수·CLI 우선순위를 적용합니다.
- [`08-3-logging-observability.ipynb`](08-3-logging-observability.ipynb): 이벤트 중심 로그와 민감정보 비기록을 확인합니다.
- [`08-4-safe-subprocess.ipynb`](08-4-safe-subprocess.ipynb): 현재 Python을 인자 목록과 시간 제한으로 실행합니다.
- [`08-5-toolization-project.ipynb`](08-5-toolization-project.ipynb): 부작용 없는 dry-run 실행 계획을 만듭니다.

CLI 도움말·표준 출력·표준 오류·실제 종료 코드는 터미널 테스트가 기준입니다. Notebook은 분리된 핵심 함수의 이해와 경계값 검증을 보조합니다.

## 09~12장 통합 예제

- [`09-testing-debugging.ipynb`](09-testing-debugging.ipynb): 정상·오류·경계값 테스트를 `unittest`로 실행합니다.
- [`10-program-architecture.ipynb`](10-program-architecture.ipynb): 입력·검증·처리·출력 책임을 작은 함수로 분리합니다.
- [`11-concurrency.ipynb`](11-concurrency.ipynb): 제한된 스레드·비동기 작업과 부분 실패 보존을 확인합니다.
- [`12-capstone.ipynb`](12-capstone.ipynb): 임시 파일의 메타데이터·해시·JSON 저장을 하나의 파이프라인으로 통합합니다.

09~12장은 현재 장별 개요 교안이므로 절별 정답 노트북이 아니라 개념을 연결하는 장별 예제를 제공합니다.

## 13장 DFIR 자동화 예제

- [`13-1-automation-design.ipynb`](13-1-automation-design.ipynb): 분석 입력·출력·제외 범위를 계약으로 만듭니다.
- [`13-2-file-batch.ipynb`](13-2-file-batch.ipynb): manifest와 실제 파일을 대조해 처리·누락 상태를 구분합니다.
- [`13-3-web-collection.ipynb`](13-3-web-collection.ipynb): 아티팩트별 파서 명령 계획을 실행 없이 검증합니다.
- [`13-4-spreadsheet-documents.ipynb`](13-4-spreadsheet-documents.ipynb): 원문 시각·UTC·시각 의미를 공통 스키마로 보존합니다.
- [`13-5-scheduling-gui.ipynb`](13-5-scheduling-gui.ipynb): 완료 감지와 워커 상태 전이를 검증합니다.
- [`13-6-safe-file-organizer-project.ipynb`](13-6-safe-file-organizer-project.ipynb): 합성 KAPE 파서 CSV를 14개 공통 레코드로 정규화합니다.
- [`13-7-spreadsheet-report-project.ipynb`](13-7-spreadsheet-report-project.ipynb): 정규화 기록에서 근거 UID가 연결된 검토 항목을 생성합니다.

13장 Notebook은 실제 사건 자료나 외부 분석 엔진을 사용하지 않습니다. 제공 합성 자료를 임시 디렉터리에서 생성하고 결과 건수와 근거 연결을 검증합니다.

## 03장 통합 실습

`03_python_basic.ipynb`는 03장 전체 내용을 학습한 뒤 다음 순서로 진행합니다.

- 자료형과 연산자
- 문자열과 컬렉션
- 조건·반복·컴프리헨션
- 함수·파일·예외
- `str`과 `bytes`
- 인증 로그 미니 프로젝트

통합 실습은 함수, 자료구조, 조건문, 반복문, 예외 처리를 사용하므로 03-1 전용 입문 실습으로 사용하지 않습니다.

노트북에서 프로젝트 모듈을 import하려면 저장소 루트에서 Jupyter를 실행하세요.
