# 챕터별 실행 실습 안내

노트북에서 시작하려면 [실습 자료 받기와 시작하기](../PRACTICE.md)를 사용한다. 이 페이지는 교안에서 터미널 실행을 안내할 때 사용할 현재 코드와 이전 참고 자료를 구분한다. 아래 경로는 저장소 루트를 기준으로 한다.

## 현재 교안에서 사용하는 자료

| 장 | 자료 | 역할 | 시작 위치 |
| --- | --- | --- | --- |
| 03-9 | `03-9-event-review-starter/` | 학습자가 TODO를 채우는 시작 코드 | [준비·구현 순서](03-9-event-review-starter/README.md) |
| 04-9 | `04-file-analyzer/` | 파일 분석기 참고 실행 코드 | [과제 요구사항](../04-file-io/04-9-file-analyzer.md) |
| 06-8 | `06-network-echo/` | 로컬 Echo 서버·클라이언트와 프로토콜 | [로컬 Echo 통신 프로젝트](../06-network-programming/06-8-echo-project.md) |
| 07-7 | `07-local-web-security-lab/` | 로컬 HTTP 서버와 응답 검증 코드 | [프로젝트 교안](../07-http-api/07-7-local-web-security-project.md) |
| 08-5 | `08-toolization-project/` | 07장 환경을 사용하는 CLI 도구화 코드 | [실행·검증 안내](08-toolization-project/README.md) |
| 13-6~13-7 | `13-kape-triage/` | 합성 CSV 생성·정규화·통합 분석 코드 | [현재 13장 프로젝트 안내](13-kape-triage/README.md) |

폴더 이름의 `starter`는 미완성 시작 코드, `lab`은 실습 환경, `project`는 여러 기능을 연결하는 프로젝트를 뜻한다. 같은 장이라도 노트북·입력 데이터·터미널 코드가 함께 필요하므로 해당 챕터의 교육자료 ZIP을 받아 폴더 구조를 유지한다. 08장 ZIP에는 의존하는 07장 로컬 서버 코드도 함께 포함된다.

## 현재 기본 실습 시작점과 구분할 자료

| 자료 | 현재 위치와 상태 |
| --- | --- |
| `03-9-auth-challenge/` | 현재 03-9의 이벤트 검토 프로그램과 다른 인증 실습 자료다. 기본과정 03-9의 시작 파일은 위 표를 따른다. |
| `13-python-automate/` | 이전 13장 파일 정리·보고서 예제다. [이전 자료 안내](13-python-automate/README.md)에 따라 참고용으로 사용한다. |

이전 자료에도 테스트와 경로 참조가 남아 있을 수 있다. 폴더 이름이나 위치를 바꿀 때는 교안 링크·노트북 import·샘플 생성 경로·검증 코드를 함께 갱신해야 한다.
