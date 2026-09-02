# 08-5 로컬 HTTP 점검기 도구화 예제

이 디렉터리는 07장의 로컬 HTTP 점검기를 설정·CLI·로깅·JSON 보고서가 있는 도구로 확장한 완성 예제다. 모든 명령은 `Python` 디렉터리에서 실행한다.

의존성을 설치한다.

```bash
python -m pip install -r requirements.txt
```

첫 번째 터미널에서 07장 학습 서버를 실행한다.

```bash
python examples/07-local-web-security-lab/training_server.py
```

두 번째 터미널에서 실행 계획을 먼저 확인한 뒤 실제 점검을 실행한다.

```bash
python examples/08-toolization-project/local_http_tool.py \
  --config examples/08-toolization-project/config.example.json \
  --dry-run

python examples/08-toolization-project/local_http_tool.py \
  --config examples/08-toolization-project/config.example.json
```

테스트는 외부 주소를 사용하지 않고 임시 로컬 서버를 직접 생성한다. 09장에서 `pytest`를 배우기 전이므로 여기서는 표준 라이브러리 `unittest`만 사용한다.

```bash
python -m unittest discover \
  -s examples/08-toolization-project \
  -p 'test_*.py' \
  -v
```

종료 코드는 `0`(검사 완료, fail 없음), `1`(검사 결과 fail 있음), `2`(설정·범위 오류), `3`(로그 초기화·보고서 저장 오류)이다. 경고는 사람이 추가로 검토해야 하는 관찰 결과이며 종료 코드 `0`을 유지한다.

설정에는 비밀번호나 API 토큰을 넣지 않는다. 이 도구는 `PYTHON_BASIC_API_TOKEN`을 읽거나 전송하거나 기록하지 않으며, 로그에도 환경 변수·요청 헤더·응답 본문을 남기지 않는다.
