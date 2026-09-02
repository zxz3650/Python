# 08-5. 로컬 HTTP 점검기 도구화 프로젝트

07장에서 만든 로컬 HTTP 점검기는 한 번 실행해 결과를 확인하는 스크립트였다. 이번 프로젝트에서는 점검 로직에 설정, CLI, 종료 코드, 실행 로그와 JSON 보고서를 연결해 **다른 사람과 다른 프로그램도 반복해서 사용할 수 있는 도구**로 발전시킨다.

새로운 공격 기능을 만드는 프로젝트가 아니다. 점검 대상은 `localhost`와 loopback IP 주소로 제한하고, 07장에서 사용한 연결성·응답 계약·보안 헤더·리다이렉트 검사만 자동화한다.

{% hint style="info" %}
### 🧭 종합 실습 목표

- CLI·환경 변수·JSON 설정의 역할과 우선순위를 구현한다.
- 실행 전 계획을 확인하는 `--dry-run`을 구현한다.
- 정상 결과, 점검 실패, 설정 오류와 실행 오류를 종료 코드로 구분한다.
- 실행 사건은 로그로, 점검 결과는 JSON 보고서로 분리한다.
- 외부 주소를 요청 전에 거부하고 비밀정보를 어디에도 기록하지 않는다.
- `main(argv) -> int` 구조로 CLI 흐름을 테스트할 수 있게 만든다.
{% endhint %}

## 1. 프로젝트가 연결하는 학습 내용

| 학습 내용 | 프로젝트 적용 지점 |
| --- | --- |
| [08-1 CLI와 종료 상태](08-1-cli-exit-status.md) | `argparse`, `main(argv)`, 종료 코드 |
| [08-2 설정 우선순위와 환경 변수](08-2-configuration-environment.md) | 기본값·JSON·환경 변수·CLI 우선순위 |
| [08-3 실행 로그](08-3-logging-observability.md) | 로그 수준, handler, 민감정보 제외 |
| [08-4 안전한 외부 프로세스](08-4-safe-subprocess.md) | 핵심 구현에는 불필요하며 선택 자기점검에서만 사용 |
| [07-7 로컬 웹 보안 점검](../07-http-api/07-7-local-web-security-project.md) | TCP·HTTP·JSON·헤더·리다이렉트 검사 |

`subprocess`는 배웠다고 해서 모든 자동화에 사용하지 않는다. 이번 도구의 HTTP 요청과 파일 저장은 Python 라이브러리로 직접 처리하는 편이 책임과 오류를 더 명확하게 제어할 수 있다.

### 완성 예제

- [`local_http_tool.py`](https://github.com/zxz3650/Python/blob/master/examples/08-toolization-project/local_http_tool.py)
- [`config.example.json`](https://github.com/zxz3650/Python/blob/master/examples/08-toolization-project/config.example.json)
- [`test_local_http_tool.py`](https://github.com/zxz3650/Python/blob/master/examples/08-toolization-project/test_local_http_tool.py)
- [`README.md`](https://github.com/zxz3650/Python/blob/master/examples/08-toolization-project/README.md)

완성 코드를 먼저 복사하기보다 각 단계의 인수 조건을 구현한 다음 비교한다. 결과가 같아도 설정 우선순위, 안전 경계와 종료 코드가 다르면 같은 도구라고 볼 수 없다.

## 2. 문제 상황과 결과물

운영자는 07장 학습 서버의 상태를 반복해서 확인하려고 한다. 소스 코드 안의 URL과 저장 경로를 매번 수정하면 다음 문제가 생긴다.

- 실행할 때 어떤 설정이 적용됐는지 알기 어렵다.
- 사람이 실행한 결과와 자동화가 실행한 결과를 구분하기 어렵다.
- 실패했는데도 호출자는 성공으로 오해할 수 있다.
- 진단 메시지와 JSON 데이터가 섞여 후속 처리가 어려워진다.
- URL이나 로그 정책을 잘못 바꾸면 허용 범위를 벗어날 수 있다.

프로젝트가 완성되면 다음 네 결과물이 생긴다.

```text
local_http_tool.py        실행 가능한 CLI 도구
config.example.json      비밀값이 없는 예시 설정
web-security-report.json 다른 프로그램도 읽을 수 있는 점검 결과
http-tool.log            사람이 실행 흐름을 추적하는 사건 기록
```

JSON 보고서와 로그는 같은 내용을 중복 저장하는 파일이 아니다.

| 구분 | 답해야 하는 질문 | 포함하는 값 |
| --- | --- | --- |
| 표준 출력 | 이번 실행의 요약은 무엇인가? | pass·warning·fail 건수, 보고서 경로 |
| 표준 오류 | 왜 실행을 시작하지 못했는가? | 설정·범위·파일 기록 오류 |
| 실행 로그 | 어느 단계가 언제 실행됐는가? | 시작·종료, 검사 이름, 상태 |
| JSON 보고서 | 무엇을 관찰했고 어떻게 분류했는가? | 대상, 시각, 요약, 검사별 근거 |

## 3. 요구사항을 먼저 고정하기

### 3.1 기능 요구사항

| ID | 요구사항 | 확인 방법 |
| --- | --- | --- |
| F01 | `--help`로 입력과 옵션을 설명한다. | 도움말 실행 |
| F02 | JSON 설정 파일을 선택할 수 있다. | `--config` 실행 |
| F03 | CLI가 환경 변수와 설정 파일을 덮어쓴다. | 서로 다른 값을 전달해 확인 |
| F04 | `--dry-run`은 적용 설정과 실행 계획만 출력한다. | HTTP 요청·TCP 연결·파일 기록 함수가 호출되지 않는지 확인 |
| F05 | TCP·health·헤더·리다이렉트 검사를 수행한다. | 07장 서버로 실행 |
| F06 | 실행 사건을 지정한 로그 파일에 기록한다. | 로그의 단계와 수준 확인 |
| F07 | 점검 결과를 안정된 JSON 구조로 저장한다. | JSON 파싱과 필수 키 확인 |
| F08 | 호출자가 결과를 구분할 수 있게 종료 코드를 반환한다. | `$?` 확인 |

### 3.2 안전 요구사항

| ID | 요구사항 | 실패하면 생기는 문제 |
| --- | --- | --- |
| S01 | `http`와 loopback 대상만 허용한다. | 외부 시스템으로 범위가 확장됨 |
| S02 | 사용자정보·query·fragment가 있는 기준 URL을 거부한다. | 비밀값이나 입력값이 보고서·로그에 남을 수 있음 |
| S03 | 리다이렉트를 자동으로 따르지 않는다. | 검증하지 않은 목적지로 요청할 수 있음 |
| S04 | 프록시와 `.netrc` 설정을 요청에 자동 적용하지 않는다. | 의도하지 않은 경로·인증정보를 사용할 수 있음 |
| S05 | 연결·읽기 무응답 timeout과 응답 크기 상한을 둔다. | 무응답 대기가 길어지거나 메모리를 과도하게 사용함 |
| S06 | 로그에 환경 변수, 요청 헤더와 응답 본문을 기록하지 않는다. | 토큰·쿠키·개인정보가 노출될 수 있음 |
| S07 | `--dry-run`은 HTTP 요청·TCP 연결·보고서·로그 파일을 만들지 않는다. | 확인 명령이 실제 상태를 변경함 |

{% hint style="danger" %}
### 실습 범위

이 프로젝트는 제공된 07장 서버와 자신이 소유한 loopback 학습 환경에서만 실행한다. 외부 주소 허용, IP 대역 순회, 인증 추측, 공격 문자열 전송 기능을 추가하지 않는다. 실제 시스템 점검에는 별도의 승인과 범위 통제가 필요하다.
{% endhint %}

### 3.3 인수 조건

다음 조건은 점수로 대신할 수 없는 프로젝트 통과 조건이다.

1. 외부 URL은 HTTP 요청 함수가 실행되기 전에 거부된다.
2. `--dry-run`은 HTTP 요청·TCP 연결과 파일 생성을 수행하지 않는다.
3. 비밀번호·API 토큰·쿠키·Authorization 값이 표준 출력, 로그와 보고서에 없다.
4. 정상 실행 경로에서 `main(argv)`는 종료 코드를 반환하고 진입점은 이를 `SystemExit`로 전달한다. `argparse`의 도움말과 사용법 오류는 각각 `SystemExit(0)`과 `SystemExit(2)`로 종료된다.
5. 정상·오류·경계 시나리오를 다른 사람이 같은 명령으로 재현할 수 있다.

## 4. 프로그램 구조 설계

한 함수에서 인자 해석, HTTP 요청, 로그와 파일 저장을 모두 처리하면 일부 기능만 검사하기 어렵다. 책임을 다음과 같이 나눈다.

```mermaid
flowchart TD
    A["main(argv)"] --> B["CLI 해석"]
    B --> C["설정 병합·자료형 검증"]
    C --> D["loopback 범위 검증"]
    D --> E{"dry-run인가?"}
    E -- "예" --> P["계획만 표준 출력"]
    E -- "아니오" --> L["로깅 설정"]
    L --> V["HTTP 점검 실행"]
    V --> J["JSON 보고서 안전하게 저장"]
    J --> X["요약 출력·종료 코드 반환"]
```

### 함수 책임

| 함수 | 입력 | 반환·효과 |
| --- | --- | --- |
| `build_parser()` | 없음 | CLI 규칙을 가진 parser |
| `load_json_config(path)` | 설정 경로 | 허용된 키만 있는 딕셔너리 |
| `environment_settings(environ)` | 환경 변수 매핑 | 문서화된 비밀 아닌 설정만 반환 |
| `resolve_settings(args, environ)` | CLI와 환경 | 검증된 `Settings` |
| `validate_loopback_url(url)` | 기준 URL | host·port·정규화 URL 또는 오류 |
| `run_validation(settings)` | 검증된 설정 | 보고서 딕셔너리 |
| `write_json_report(report, path)` | 결과와 경로 | 임시 파일을 거친 보고서 저장 |
| `main(argv, environ=...)` | 문자열 인자 목록 | 종료 코드 정수 |

`main()`이 `argv`와 `environ`을 매개변수로 받으면 테스트가 실제 명령줄과 운영체제 환경을 바꾸지 않고도 여러 입력을 재현할 수 있다.

## 5. 사용자 인터페이스 계약

### 5.1 설정 우선순위

같은 설정이 여러 위치에 있으면 다음 순서에서 앞선 값을 사용한다.

```text
CLI > 환경 변수 > JSON 설정 파일 > 프로그램 기본값
```

| 설정 | CLI | 환경 변수 | 기본값 |
| --- | --- | --- | --- |
| 대상 | `--target` | `PYTHON_BASIC_TARGET` | `http://127.0.0.1:8080` |
| 보고서 | `--output` | `PYTHON_BASIC_OUTPUT` | `artifacts/web-security-report.json` |
| timeout | `--timeout` | `PYTHON_BASIC_TIMEOUT` | `3.0` |
| 로그 수준 | `--log-level` | `PYTHON_BASIC_LOG_LEVEL` | `INFO` |
| 로그 파일 | `--log-file` | `PYTHON_BASIC_LOG_FILE` | `artifacts/http-tool.log` |

`--verbose`는 이번 실행에서만 로그 수준을 `DEBUG`로 바꾼다. `--dry-run`은 실행 모드를 바꾸는 CLI 플래그이므로 설정 파일에 저장하지 않는다.

{% hint style="warning" %}
`PYTHON_BASIC_API_TOKEN`처럼 비밀값을 담는 환경 변수가 있더라도 이 프로젝트는 인증 기능이 필요하지 않으므로 읽지 않는다. 전체 `os.environ`이나 설정 딕셔너리를 로그로 출력해서도 안 된다. 필요한 키만 선택해 읽는 것이 비밀정보 비기록의 시작이다.
{% endhint %}

예시 설정은 비밀값 없이 작성한다.

```json
{
  "target": "http://127.0.0.1:8080",
  "output": "artifacts/web-security-report.json",
  "timeout": 3.0,
  "log_level": "INFO",
  "log_file": "artifacts/http-tool.log"
}
```

상대경로는 설정 파일의 위치가 아니라 **도구를 실행한 현재 작업 디렉터리**를 기준으로 해석한다. 예제 명령은 경로 기준을 일정하게 유지하기 위해 `Python` 디렉터리에서 실행한다.

### 5.2 종료 코드

| 종료 코드 | 의미 | 호출자의 다음 행동 |
| --- | --- | --- |
| `0` | 실행 완료, `fail` 없음 | 보고서를 사용함 |
| `1` | 실행 완료, 하나 이상의 검사가 `fail` | 보고서 근거를 확인함 |
| `2` | CLI·설정·대상 범위 오류 | 입력과 설정을 수정함 |
| `3` | 로그 초기화 또는 보고서 저장 같은 실행 오류 | 경로·권한·디스크 상태를 확인함 |

`warning`은 추가 검토가 필요한 관찰 결과이며 이 프로젝트에서는 종료 코드 `0`을 유지한다. 조직 정책에 따라 warning도 실패로 처리해야 한다면 새로운 옵션과 문서화된 정책으로 변경해야 한다.

표준 `logging`은 handler가 로그를 내보내는 도중 발생한 오류를 일반적으로 `handleError()`에서 처리하며 호출 코드로 다시 발생시키지 않는다. 따라서 이 예제의 종료 코드 `3`이 보장하는 범위는 `FileHandler` 생성 같은 **로그 초기화 실패**와 JSON 보고서 저장 실패다. 모든 로그 한 줄의 영구 저장까지 성공 조건으로 삼으려면 오류를 다시 발생시키는 전용 handler나 별도 기록 계층이 필요하며 이는 심화 설계에 해당한다.

### 5.3 보고서 계약

보고서에는 구조 버전을 둔다. 나중에 필드가 추가돼도 소비자가 어떤 형식인지 판단할 수 있다.

```json
{
  "schema_version": 1,
  "target": "http://127.0.0.1:8080",
  "checked_at": "2026-09-02T00:00:00+00:00",
  "scope": "loopback-only training lab",
  "summary": {"pass": 3, "warning": 1, "fail": 0},
  "checks": [
    {
      "check": "tcp_connection",
      "status": "pass",
      "evidence": "loopback TCP connection succeeded"
    }
  ]
}
```

응답 본문, 요청 헤더, 쿠키와 환경 변수는 보고서 계약에 포함하지 않는다. 리다이렉트 검사도 외부 목적지의 전체 문자열을 기록하지 않고 허용 출처를 벗어났는지만 기록한다.

## 6. 단계별 구현

### 6.1 1단계: 스타터 구조 만들기

다음 구조에서 TODO를 하나씩 구현한다. `main()` 안에 모든 코드를 넣지 않는다.

```python
from __future__ import annotations

import argparse
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path


EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_USAGE = 2
EXIT_RUNTIME = 3


class SettingsError(ValueError):
    """안전하게 실행할 설정을 만들 수 없을 때 사용한다."""


@dataclass(frozen=True)
class Settings:
    target: str
    output: Path
    timeout: float
    log_level: str
    log_file: Path
    dry_run: bool = False


def build_parser() -> argparse.ArgumentParser:
    # TODO: --config, --target, --output, --timeout,
    #       --log-level, --log-file, --verbose, --dry-run
    ...


def resolve_settings(args, environ: Mapping[str, str]) -> Settings:
    # TODO: defaults < JSON < environment < CLI
    ...


def run_validation(settings: Settings) -> dict[str, object]:
    # TODO: 07장 점검 로직을 함수 단위로 연결
    ...


def main(
    argv: Sequence[str] | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> int:
    # TODO: 설정 → 범위 → dry-run → 로그 → 점검 → 저장 → 종료 코드
    ...


if __name__ == "__main__":
    raise SystemExit(main())
```

`raise SystemExit(main())`는 반환한 정수를 운영체제 종료 상태로 전달한다. 설정 해석 이후의 정상·점검 실패·기록 실패 경로는 정수를 반환하므로 테스트가 프로세스를 종료하지 않고 결과를 확인할 수 있다. 다만 `parse_args()`는 `--help`에서 `SystemExit(0)`, 알 수 없는 옵션과 필요한 값 누락에서 `SystemExit(2)`를 직접 발생시킨다. 이는 08-1에서 학습한 `argparse`의 표준 동작이며 테스트에서는 `assertRaises(SystemExit)`로 별도로 확인한다.

### 6.2 2단계: 설정을 한 방향으로 병합하기

설정은 값을 읽는 함수와 검증하는 함수를 분리한다. 전체 환경을 복사해 출력하지 않고 문서화된 키만 선택한다.

```python
ENVIRONMENT_KEYS = {
    "target": "PYTHON_BASIC_TARGET",
    "output": "PYTHON_BASIC_OUTPUT",
    "timeout": "PYTHON_BASIC_TIMEOUT",
    "log_level": "PYTHON_BASIC_LOG_LEVEL",
    "log_file": "PYTHON_BASIC_LOG_FILE",
}


def environment_settings(environ):
    return {
        setting: environ[name]
        for setting, name in ENVIRONMENT_KEYS.items()
        if name in environ and environ[name] != ""
    }
```

병합은 낮은 우선순위부터 `update()`한다.

```python
values = dict(DEFAULTS)
values.update(load_json_config(args.config))
values.update(environment_settings(environ))
values.update(cli_values_without_none)
```

병합 뒤에는 timeout을 숫자로 변환하고 `0 < timeout <= 30`인지 확인한다. 보고서와 로그에 같은 경로를 지정한 경우도 거부한다. 설정을 읽었다는 사실과 설정값 전체를 로그에 남기는 것은 다르다.

### 6.3 3단계: 요청보다 앞에 범위 게이트 두기

범위 검증은 요청 함수 안쪽의 부가 조건이 아니라 모든 네트워크 작업 앞에 있는 게이트다.

```python
import ipaddress
import socket
from urllib.parse import urlsplit


def validate_loopback_url(base_url: str) -> tuple[str, int, str]:
    try:
        parts = urlsplit(base_url)
    except ValueError as exc:
        raise SettingsError("target URL is invalid") from exc

    if parts.scheme != "http":
        raise SettingsError("target must use the http scheme")
    if not parts.hostname:
        raise SettingsError("target URL needs a host")
    if parts.username is not None or parts.password is not None:
        raise SettingsError("target URL must not contain user information")
    if parts.query or parts.fragment:
        raise SettingsError("target base URL must not contain a query or fragment")
    if parts.path not in ("", "/"):
        raise SettingsError("target base URL path must be empty")

    try:
        parsed_port = parts.port
    except ValueError as exc:
        raise SettingsError("target URL contains an invalid port") from exc
    if parsed_port == 0:
        raise SettingsError("target port must be between 1 and 65535")
    port = 80 if parsed_port is None else parsed_port

    host = parts.hostname.lower()
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if host != "localhost":
            raise SettingsError("only localhost or a loopback IP is allowed")
        try:
            raw_addresses = {
                item[4][0]
                for item in socket.getaddrinfo(
                    host,
                    port,
                    type=socket.SOCK_STREAM,
                )
            }
        except OSError as exc:
            raise SettingsError("localhost could not be resolved") from exc

        addresses = {ipaddress.ip_address(item) for item in raw_addresses}
        if not addresses or not all(item.is_loopback for item in addresses):
            raise SettingsError("localhost resolved outside the loopback range")

        selected = min(
            addresses,
            key=lambda item: (item.version != 4, int(item)),
        )
        connection_host = selected.compressed
    else:
        if not address.is_loopback:
            raise SettingsError("only a loopback IP is allowed")
        connection_host = address.compressed

    url_host = f"[{connection_host}]" if ":" in connection_host else connection_host
    normalized = f"http://{url_host}:{port}"
    return connection_host, port, normalized
```

문자열이 `localhost`처럼 보이는지 확인하는 것만으로는 충분하지 않다. 이름 해석 결과가 모두 loopback인지 확인하고, 그중 하나의 IP 리터럴을 선택해 이후 TCP·HTTP 요청에도 같은 주소를 사용한다. 검증 뒤 `localhost`를 다시 이름 해석하지 않으므로 검사한 주소와 실제 연결 주소가 달라지는 틈을 줄인다. 반대로 `127.0.0.1.evil.example`처럼 이름에 숫자가 포함돼도 허용 호스트가 아니므로 거부한다.

Requests 세션에서는 다음 설정으로 운영체제의 프록시와 `.netrc` 인증정보를 자동 상속하지 않는다.

```python
with requests.Session() as session:
    session.trust_env = False
    session.headers.update({"User-Agent": "python-basic-local-tool/1.0"})
```

`requests`에 `(timeout, timeout)`을 전달하면 각각 연결 대기와 **응답 데이터를 읽는 동안의 무응답 대기**를 제한한다. 프로그램 전체의 총 실행 시간을 보장하는 값은 아니다. 서버가 제한 시간보다 짧은 간격으로 데이터를 조금씩 계속 보내면 전체 실행은 더 길어질 수 있다. 총 실행 기한이 필요한 운영 도구라면 단조 시계 기반의 전체 deadline이나 상위 실행기의 제한을 별도로 설계한다.

### 6.4 4단계: `dry-run`을 실제 무동작 경로로 만들기

`dry-run`은 “실행하지 않았습니다”라는 로그만 남기는 기능이 아니다. 범위와 설정을 검증한 뒤 HTTP 요청·TCP 연결 함수와 파일 handler를 만들기 전에 반환해야 한다. `localhost`를 입력하면 범위 검증을 위해 이름 해석이 한 번 수행될 수 있지만, 점검 대상에 연결하거나 HTTP 요청을 보내지는 않는다.

```python
def execute(args, environ):
    settings = resolve_settings(args, environ)
    _, _, normalized = validate_loopback_url(settings.target)

    if settings.dry_run:
        print(json.dumps(dry_run_plan(settings, normalized), indent=2))
        return EXIT_OK

    configure_logging(settings.log_level, settings.log_file)
    report = run_validation(replace(settings, target=normalized))
    write_json_report(report, settings.output)
    return EXIT_CHECK_FAILED if report["summary"]["fail"] else EXIT_OK
```

이 순서라면 `--dry-run`도 잘못된 외부 대상을 성공으로 표시하지 않으며, 동시에 로그와 보고서를 만들지 않는다.

### 6.5 5단계: 로그와 판정 근거 분리하기

로그는 다음 사건만 기록한다.

```text
run_started target=http://127.0.0.1:8080
check_complete name=tcp_connection status=pass
check_complete name=health_api status=pass
check_complete name=security_headers status=warning
check_complete name=redirect_origin status=pass
run_finished pass=3 warning=1 fail=0
```

다음 코드는 작성하지 않는다.

```python
# 금지 예: 환경·인증정보·응답 전체가 기록될 수 있다.
logger.debug("environment=%r", os.environ)
logger.info("request headers=%r", request.headers)
logger.info("response body=%s", response.text)
logger.info("settings=%r", settings_as_dict)
```

검사의 `evidence`도 로그에 복제하지 않는다. 보고서에는 제한된 판정 근거가 있고, 로그에는 검사 이름과 상태만 있다. 두 파일의 목적을 분리하면 운영 로그에 데이터가 과도하게 축적되는 일을 줄일 수 있다.

### 6.6 6단계: JSON을 임시 파일을 거쳐 저장하기

보고서를 대상 파일에 바로 쓰다가 중단되면 잘린 JSON이 남을 수 있다. 04-8에서 학습한 것처럼 출력과 같은 디렉터리에 고유한 임시 파일을 만들고, 다시 읽어 구조를 검증한 뒤 교체한다.

```python
def write_json_report(report, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(
                report,
                temporary,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())

        with temporary_path.open("r", encoding="utf-8") as saved:
            restored = json.load(saved)
        if not isinstance(restored, dict) or "summary" not in restored:
            raise ValueError("보고서 구조가 올바르지 않다")

        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
```

이 코드에는 `json`, `os`, `Path`, `NamedTemporaryFile` import가 필요하다. 고유한 임시 파일을 사용하므로 동시 실행이 같은 `.tmp` 이름을 공유하지 않으며, 실패하면 `finally`에서 해당 임시 파일만 정리한다. 다만 여러 프로세스가 같은 최종 출력 경로를 동시에 교체하는 순서까지 제어하지는 않으므로 실행별 파일명이나 잠금이 필요하면 별도의 정책을 설계한다.

### 6.7 7단계: 종료 상태를 한곳에서 결정하기

점검 함수는 결과를 딕셔너리로 반환하고, `main()`이 전체 실행의 종료 코드를 결정한다.

```python
def finish_run(settings):
    report = run_validation(settings)
    write_json_report(report, settings.output)

    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"Report: {settings.output}")

    if report["summary"]["fail"]:
        return EXIT_CHECK_FAILED
    return EXIT_OK
```

설정 오류와 실행 오류는 점검 결과의 `fail`과 의미가 다르다. 설정 오류는 점검 자체가 시작되지 않은 상태이고, `fail`은 점검을 실행해 기대 조건을 충족하지 못한 상태다.

## 7. 실행 실습

모든 명령은 저장소의 `Python` 디렉터리에서 실행한다.

### 7.1 의존성 준비

```bash
python -m pip install -r requirements.txt
```

### 7.2 07장 서버 실행

첫 번째 터미널에서 학습 서버를 실행한다.

```bash
python examples/07-local-web-security-lab/training_server.py
```

예상 출력은 다음과 같다.

```text
Training server: http://127.0.0.1:8080
Press Ctrl+C to stop
```

### 7.3 도움말과 실행 계획 확인

두 번째 터미널에서 인터페이스와 계획을 확인한다.

```bash
python examples/08-toolization-project/local_http_tool.py --help

python examples/08-toolization-project/local_http_tool.py \
  --config examples/08-toolization-project/config.example.json \
  --dry-run
```

`dry-run` 결과에는 다음 두 값이 있어야 한다.

```json
{
  "http_requests_sent": false,
  "tcp_connections_opened": false,
  "files_written": false
}
```

실행 전후에 `artifacts` 디렉터리를 비교해 실제로 파일이 만들어지지 않았는지 확인한다. 출력 문구만 믿지 않고 파일시스템 상태를 증거로 확인한다.

### 7.4 실제 점검 실행

```bash
python examples/08-toolization-project/local_http_tool.py \
  --config examples/08-toolization-project/config.example.json

echo $?
```

07장 학습 서버의 의도된 결과는 `pass=3`, `warning=1`, `fail=0`이며 종료 코드는 `0`이다.

```text
{"pass": 3, "warning": 1, "fail": 0}
Report: artifacts/web-security-report.json
0
```

### 7.5 설정 우선순위 확인

환경 변수와 CLI에 서로 다른 값을 지정한다.

```bash
PYTHON_BASIC_TIMEOUT=5 \
python examples/08-toolization-project/local_http_tool.py \
  --config examples/08-toolization-project/config.example.json \
  --timeout 2 \
  --dry-run
```

출력된 timeout이 `2.0`이면 CLI가 환경 변수와 JSON 설정보다 앞선다는 계약이 지켜진 것이다.

### 7.6 외부 주소 거부 확인

```bash
python examples/08-toolization-project/local_http_tool.py \
  --target https://example.com

echo $?
```

요청이나 파일 생성 없이 설정 오류가 표준 오류에 표시되고 종료 코드 `2`가 반환돼야 한다.

### 7.7 점검 실패 확인

첫 번째 터미널의 서버를 중지한 뒤 같은 명령을 다시 실행한다. 보고서는 생성되지만 TCP와 HTTP 검사가 `fail`이 되고 종료 코드 `1`이 반환돼야 한다. 이것은 설정 오류가 아니라 **허용된 점검을 수행해 실패를 관찰한 상태**다.

## 8. 검증 시나리오

| ID | 입력·상태 | 기대 결과 | 종료 코드 |
| --- | --- | --- | --- |
| V01 | `--help` | 옵션·설명이 출력됨 | `0` |
| V02 | 정상 설정 + `--dry-run` | HTTP 요청·TCP 연결·파일 생성 없음 | `0` |
| V03 | 07장 서버 실행 중 | pass 3, warning 1, fail 0 | `0` |
| V04 | 07장 서버 중지 | fail이 있는 JSON 보고서 생성 | `1` |
| V05 | CLI·환경·JSON에 서로 다른 timeout | CLI 값 적용 | `0` |
| V06 | `https://example.com` | scheme·외부 대상 거부 | `2` |
| V07 | `http://192.0.2.10` | loopback이 아니므로 거부 | `2` |
| V08 | `http://user:pass@127.0.0.1:8080` | 사용자정보 포함 URL 거부 | `2` |
| V09 | `http://127.0.0.1:8080?token=x` | query 포함 기준 URL 거부 | `2` |
| V10 | 보고서와 로그에 같은 경로 지정 | 설정 충돌 거부 | `2` |
| V11 | 잘못된 JSON 설정 | 줄·열 정보와 함께 거부 | `2` |
| V12 | 비밀 표식이 든 환경 변수 설정 후 정상 실행 | 로그·보고서에 표식이 없음 | `0` |
| V13 | 직렬화할 수 없는 보고서 저장 | 기존 결과 유지·임시 파일 정리 | 실행 오류 |

V06~V09는 오류 메시지만 확인해서는 부족하다. HTTP 실행 함수를 가짜 함수로 바꿔 호출 횟수가 0인지 확인해야 “요청 전에 거부”했다는 증거가 된다.

## 9. 자동 검증

09장에서 `pytest`를 배우기 전이므로 제공 예제는 표준 라이브러리 `unittest`로 핵심 계약을 확인한다.

```bash
python -m unittest discover \
  -s examples/08-toolization-project \
  -p 'test_*.py' \
  -v
```

테스트는 다음을 확인한다.

1. 외부 주소일 때 `run_validation()`이 한 번도 호출되지 않는다.
2. `dry-run`일 때 HTTP 세션·TCP 연결·보고서·로그 기록 함수가 호출되지 않는다.
3. CLI가 환경 변수와 JSON 설정을 올바르게 덮어쓴다.
4. 임시 loopback 서버 점검 결과가 예상 구조이며 비밀 표식이 저장되지 않는다.
5. 사용자정보·query·fragment·0번 포트가 있는 기준 URL을 거부한다.
6. `localhost`를 검증된 loopback IP 리터럴로 고정한다.
7. 프록시·`.netrc` 상속과 자동 리다이렉트를 끄고 연결·읽기 timeout을 전달한다.
8. 1 MiB를 넘는 응답을 거부한다.
9. 점검 실패와 로그 초기화·보고서 저장 실패가 각각 종료 코드 `1`과 `3`을 반환한다.
10. 직렬화 실패에도 기존 보고서가 유지되고 고유 임시 파일이 정리된다.
11. 보고서·로그 경로 충돌, 잘못된 JSON과 알 수 없는 설정 키를 거부한다.
12. 상세 로그 모드에서도 비밀 표식이 표준 출력·오류·로그·보고서에 나타나지 않는다.

`test_local_http_tool.py`는 `127.0.0.1`의 임의 포트에 임시 서버를 만들고 테스트가 끝나면 종료한다. 외부 네트워크와 고정 포트를 사용하지 않으므로 다른 학습자도 같은 시나리오를 재현하기 쉽다.

## 10. 평가 루브릭

| 평가 항목 | 배점 | 확인 기준 |
| --- | ---: | --- |
| CLI와 종료 상태 | 15 | 도움말, 옵션 검증, `main(argv)`, 코드 0·1·2·3 구분 |
| 설정 관리 | 15 | 기본값·JSON·환경·CLI 우선순위, 자료형·범위 검증 |
| 점검 기능 연결 | 20 | TCP·health·헤더·리다이렉트 검사와 안정된 요약 |
| 안전 경계 | 25 | loopback 제한, redirect·proxy 통제, 연결·읽기 무응답 timeout·크기 제한, dry-run 무동작 |
| 로그와 보고서 | 15 | 역할 분리, 비밀정보 제외, JSON 구조와 안전한 저장 |
| 검증과 문서화 | 10 | 정상·오류·경계 테스트, 실행·재현 방법 기록 |
| **합계** | **100** |  |

다음 중 하나라도 발생하면 총점과 관계없이 안전 경계 항목을 통과하지 못한다.

- 외부 주소로 실제 요청을 보낸다.
- `dry-run`이 HTTP 요청·TCP 연결이나 파일 쓰기를 수행한다.
- 비밀번호, API 토큰, Cookie 또는 Authorization 값이 로그나 보고서에 남는다.
- 응답 크기와 연결·읽기 무응답 timeout 제한이 없다.
- 사용자가 입력한 임의 명령을 `shell=True`로 실행한다.

## 11. 분석 질문

1. `warning`이 있어도 종료 코드 `0`을 사용하는 이유는 무엇인가?
2. 외부 주소를 요청 함수 안에서만 거부하면 테스트와 책임 분리가 왜 어려워지는가?
3. JSON 설정 파일 전체를 `DEBUG` 로그에 남기면 어떤 정보가 노출될 수 있는가?
4. 보고서 쓰기 실패와 HTTP 점검 실패는 호출자가 왜 구분해야 하는가?
5. `session.trust_env = False`가 로컬 전용 경계를 더 분명하게 만드는 이유는 무엇인가?
6. `dry-run`에서 로그 파일도 만들지 않는다는 조건은 어떻게 자동으로 증명할 수 있는가?
7. 검사별 `evidence`를 로그에도 모두 복제하지 않는 이유는 무엇인가?
8. 설정 우선순위가 문서와 코드에서 다르면 어떤 재현성 문제가 생기는가?

## 12. 선택 확장

기본 인수 조건을 모두 만족한 뒤 다음 중 하나를 선택한다.

1. 검사별 실행 시간을 밀리초로 보고서에 추가한다.
2. `--output -`일 때 JSON 전체를 표준 출력으로 보내고 로그는 표준 오류로만 보낸다.
3. 기존 보고서를 덮어쓰지 않는 `--no-clobber` 옵션을 추가한다.
4. 09장에서 같은 인수 조건을 `pytest`의 `tmp_path`, `monkeypatch`와 fixture로 다시 작성한다.
5. 08-4를 복습하려면 고정된 테스트 명령만 실행하는 별도 `self_check.py`를 작성한다.

선택 5는 다음처럼 실행 파일과 인자를 코드가 고정해야 한다.

```python
completed = subprocess.run(
    [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "examples/08-toolization-project",
        "-p",
        "test_*.py",
        "-v",
    ],
    shell=False,
    timeout=30,
    check=False,
    text=True,
    encoding="utf-8",
    capture_output=True,
)
```

사용자가 임의 명령 문자열을 입력하게 만들지 않는다. 장기 실행 서버를 자동으로 시작하는 기능은 프로세스 종료, 포트 충돌과 예외 시 정리 정책이 추가로 필요하므로 이 프로젝트의 기본 범위에 포함하지 않는다.

## 13. 완료 기준

- [ ] 07장 서버를 실행하고 점검 결과를 JSON으로 저장할 수 있다.
- [ ] `--help`만 보고도 다른 학습자가 옵션을 사용할 수 있다.
- [ ] CLI·환경 변수·JSON·기본값의 우선순위를 설명하고 재현할 수 있다.
- [ ] `--dry-run`에서 HTTP 요청·TCP 연결·보고서·로그가 생성되지 않음을 확인했다.
- [ ] 외부 주소와 사용자정보·query·fragment가 있는 URL이 요청 전에 거부된다.
- [ ] 정상 실행, 점검 실패, 설정 오류와 기록 오류의 종료 코드를 구분한다.
- [ ] 로그와 JSON 보고서의 목적과 포함 정보를 구분한다.
- [ ] 비밀 표식이 표준 출력, 로그와 보고서에 없는지 검사했다.
- [ ] `main(argv)`를 호출하는 자동 테스트를 모두 통과했다.
- [ ] 실행 명령과 기대 결과를 다른 사람이 재현할 수 있게 기록했다.

{% hint style="success" %}
### 핵심 정리

- 스크립트가 도구가 되려면 기능뿐 아니라 입력·출력·설정·오류 계약이 필요하다.
- 안전 경계는 설명문이 아니라 요청보다 먼저 실행되는 코드와 테스트로 강제한다.
- 로그는 실행 사건, JSON은 판정 결과를 기록하며 비밀정보는 두 곳 모두에서 제외한다.
- `dry-run`과 종료 코드는 사람이 쓰는 프로그램을 자동화가 신뢰할 수 있는 프로그램으로 바꾼다.
- 구현 완료는 정상 출력 한 번이 아니라 정상·오류·경계 조건의 재현으로 확인한다.
{% endhint %}

---

다음 장: [09. 테스트와 디버깅](../09-testing-debugging.md)
