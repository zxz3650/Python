# 주피터 실습

03장과 04장 노트북은 Python 3.10 이상에서 실행하며 Python 3.12를 권장합니다. 커널 버전은 첫 셀을 실행하기 전에 `import sys; print(sys.version)`으로 확인하세요.

## 절별 기초 실습

- [`03-1-data-types.ipynb`](03-1-data-types.ipynb): 변수, 기본 자료형, 명시적 형변환, 형식과 범위 검증의 차이를 외부 모듈 없이 연습합니다.
- [`03-2-strings-collections.ipynb`](03-2-strings-collections.ipynb): 문자열 처리, 자료구조 선택, 중첩 구조, 별칭과 복사를 조건문·반복문 없이 연습합니다.
- [`03-3-conditions-logic.ipynb`](03-3-conditions-logic.ipynb): 비교·논리 연산자, 우선순위, 단락 평가, truthy/falsey, 결정표 기반 단일 이벤트 분류를 연습합니다.
- [`03-4-loops.ipynb`](03-4-loops.ipynb): `for`·`while`, 반복 종료, 카운트·누적·필터·검색·집계 패턴, 안전한 컬렉션 순회, 이벤트 목록 분석을 연습합니다.
- [`03-5-functions-scope.ipynb`](03-5-functions-scope.ipynb): 함수 계약, 인자 전달, 반환값, 변경 가능한 기본값, 객체 변경, 스코프, 콜백, 이벤트 분석 함수 분리를 연습합니다.
- [`03-6-exceptions.ipynb`](03-6-exceptions.ipynb): traceback, 예외 전파, `try` 흐름, 예외 연결, 입력 검증, 배치 처리 정책을 연습합니다.
- [`03-7-modules-packages.ipynb`](03-7-modules-packages.ipynb): 과정별 모듈 지도, import 이름, 모듈 캐시·검색 경로, 일반 패키지, 상대 import, `python -m`, import 오류 진단을 연습합니다.
- [`03-8-classes-dataclasses.ipynb`](03-8-classes-dataclasses.ipynb): 클래스·인스턴스, 메서드 바인딩, 클래스 변수, 상태 전이, property, dataclass, 상속·합성, 이벤트 객체 모델을 연습합니다.
- [`03-9-syntax-project.ipynb`](03-9-syntax-project.ipynb): 03-1~03-8의 문법을 이벤트 검토 큐에 통합하고 값 객체, 저장소, 명령 파서, 오류 복구 세션, 입출력 주입 테스트를 단계별로 완성합니다.

처음 Python 문법을 학습한다면 번호 순서대로 실행하세요. 각 셀은 결과를 먼저 예측하고, 실행 결과를 설명한 뒤 값을 변경하는 순서로 구성되어 있습니다.

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
