# 08-1. 명령줄 인터페이스와 종료 상태

명령줄 인터페이스(Command-Line Interface, CLI)는 터미널에서 프로그램의 입력을 전달하고 실행 결과를 받는 접점이다. CLI를 사용하면 소스 코드를 매번 수정하지 않고도 입력 파일, 처리 범위, 출력 형식을 바꿀 수 있다. 또한 사람이 직접 실행한 프로그램을 셸 스크립트, 예약 작업, 다른 프로그램에서도 같은 방식으로 호출할 수 있다.

이 절에서는 `argparse`로 사용법이 분명한 CLI를 만들고, `main(argv) -> int` 구조로 실행 흐름과 핵심 로직을 분리한다. 성공 결과는 표준 출력으로, 진단 정보는 표준 오류로 보내며 종료 상태로 성공과 실패를 전달한다.

{% hint style="info" %}
### 🧭 학습 목표

- 위치 인자, 선택 인자, 플래그를 구분한다.
- `argparse.ArgumentParser`로 도움말과 입력 규칙을 정의한다.
- 문자열로 들어온 CLI 입력을 자료형과 허용 범위에 맞게 검증한다.
- `main(argv) -> int`와 `raise SystemExit(main())`의 역할을 설명한다.
- 표준 출력과 표준 오류를 목적에 맞게 구분한다.
- 종료 코드 `0`, `1`, `2`가 호출자에게 전달하는 의미를 설명한다.
- 정상·오류·경계 입력으로 CLI 계약을 확인한다.
{% endhint %}

## 선행 지식과 연결

- 함수 인자·반환값과 `main()` 구조는 [03-5. 함수](../03-python-basics/03-5-functions.md)에서 학습했다.
- 예외를 구체적으로 처리하고 호출자에게 실패를 전달하는 방법은 [03-6. 예외 처리](../03-python-basics/03-6-exceptions.md)에서 학습했다.
- `if __name__ == "__main__"`의 의미는 [03-7. 모듈과 패키지](../03-python-basics/03-7-modules-packages.md)에서 학습했다.
- `Path`와 텍스트 파일 읽기는 [04-1](../04-file-io/04-1-paths-filesystem.md)과 [04-3](../04-file-io/04-3-text-files.md)에서 학습했다.

## 이 절의 핵심 질문

```text
사용자는 어떤 입력을 전달해야 하는가?
  ↓
문법과 자료형이 올바른가?
  ↓
현재 실행 환경에서 작업할 수 있는가?
  ↓
결과와 진단 메시지를 어디로 보낼 것인가?
  ↓
호출자에게 성공과 실패를 어떻게 알릴 것인가?
```

CLI는 단순히 문자열을 읽는 코드가 아니다. **입력 형식, 결과 형식, 오류 메시지, 종료 상태를 함께 약속하는 프로그램의 공개 인터페이스**다.

## 0. 학습 전 확인

다음 명령에서 프로그램 이름, 위치 인자, 선택 인자, 옵션값, 플래그를 구분해 본다.

```bash
python line_report.py sample.log --limit 20 --format json --verbose
```

다음 질문에 먼저 답한다.

1. `sample.log`와 `20`은 Python 프로그램에 어떤 자료형으로 들어오는가?
2. `--verbose` 뒤에 값이 없어도 되는 이유는 무엇인가?
3. 명령의 사용법이 틀렸을 때와 파일을 읽지 못했을 때 종료 코드는 같아야 하는가?
4. JSON 결과와 진행 메시지를 같은 출력 통로로 보내면 어떤 문제가 생기는가?
5. `main()` 안에서 `return 1`만 실행하면 운영체제에 종료 코드 `1`이 전달되는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. CLI 입력은 프로그램의 계약이다

CLI에서 자주 사용하는 입력은 다음 세 종류다.

| 종류 | 예 | 의미 |
| --- | --- | --- |
| 위치 인자 | `sample.log` | 위치와 순서로 의미를 구분하는 필수 입력 |
| 선택 인자 | `--limit 20` | 이름으로 의미를 드러내는 선택 입력 |
| 플래그 | `--verbose` | 지정 여부만으로 기능을 켜거나 끄는 입력 |

다음 명령은 `sample.log`의 앞부분을 확인하고 JSON 형식으로 결과를 출력하며, 진행 정보도 표시하라는 뜻이다.

```bash
python line_report.py sample.log --limit 20 --format json --verbose
```

좋은 CLI는 소스 코드를 읽지 않아도 다음 질문에 답할 수 있어야 한다.

- 무엇이 필수 입력인가?
- 어떤 선택지를 사용할 수 있는가?
- 기본값은 무엇인가?
- 잘못된 입력은 왜 거부되었는가?
- 성공 결과와 오류를 어떻게 구분하는가?

{% hint style="warning" %}
CLI 인자는 운영체제의 프로세스 목록이나 셸 기록에 남을 수 있다. 비밀번호, API 토큰, 개인키 같은 비밀값을 `--password ...`처럼 전달하지 않는다. 비밀값 분리와 검증은 [08-2](08-2-configuration-environment.md)에서 다룬다.
{% endhint %}

## 2. `sys.argv`와 `argparse`

Python은 실행 인자를 `sys.argv` 리스트로 제공한다.

```python
import sys

print(sys.argv)
```

다음과 같이 실행하면 첫 번째 원소에는 실행한 파일 이름이 들어간다.

```bash
python show_args.py sample.log --limit 20
```

대표적인 출력은 다음과 같다.

```text
['show_args.py', 'sample.log', '--limit', '20']
```

모든 원소는 문자열이다. `20`도 자동으로 정수가 되지 않는다. `sys.argv`를 직접 순회하며 옵션을 해석할 수도 있지만 다음 기능을 매번 다시 만들어야 한다.

- 필수 입력 누락 검사
- 옵션값과 자료형 변환
- 허용 값 검사
- `-h`, `--help` 도움말
- 일관된 오류 메시지와 종료 코드

표준 라이브러리 `argparse`는 이러한 공통 작업을 맡는다.

## 3. 가장 작은 `argparse` 프로그램

```python
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="이름을 받아 인사말을 출력한다."
    )
    parser.add_argument("name", help="인사할 이름")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print(f"안녕하세요, {args.name}님")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

정상 실행:

```bash
python greet.py student
```

```text
안녕하세요, student님
```

도움말 확인:

```bash
python greet.py --help
```

```text
usage: greet.py [-h] name

이름을 받아 인사말을 출력한다.

positional arguments:
  name        인사할 이름

options:
  -h, --help  show this help message and exit
```

Python과 `argparse` 버전에 따라 도움말의 구역 이름이나 줄바꿈은 조금 다를 수 있다. 중요한 것은 사용법, 설명, 필수 인자, 도움말 옵션이 자동으로 제공된다는 점이다.

필수 인자를 생략하면 `argparse`는 사용법과 오류를 표준 오류에 출력하고 종료 코드 `2`로 프로그램을 끝낸다.

```bash
python greet.py
```

```text
usage: greet.py [-h] name
greet.py: error: the following arguments are required: name
```

## 4. 위치 인자·선택 인자·플래그 정의

```python
from pathlib import Path
import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="텍스트 파일의 일부를 검사해 요약한다."
    )
    parser.add_argument(
        "input",
        type=Path,
        metavar="FILE",
        help="읽을 UTF-8 텍스트 파일",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        metavar="N",
        help="검사할 최대 줄 수, 기본값: 20",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="출력 형식, 기본값: text",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="진행 정보를 표준 오류에 출력",
    )
    return parser
```

각 설정의 역할은 다음과 같다.

| 설정 | 역할 |
| --- | --- |
| `type=Path` | 문자열을 `Path` 객체로 변환 |
| `type=int` | 문자열을 정수로 변환하고 실패 시 사용법 오류 처리 |
| `default=20` | 옵션을 생략했을 때 사용할 값 |
| `choices=(...)` | 허용된 값만 통과 |
| `metavar="N"` | 도움말에 표시할 값의 이름 |
| `action="store_true"` | 옵션이 있으면 `True`, 없으면 `False` |

`type=Path`는 문자열을 경로 객체로 바꿀 뿐이다. 파일의 존재, 종류, 읽기 권한까지 검사하지 않는다. 이 검사는 실제 작업 직전에 별도로 수행한다.

### 4.1 `type=bool`을 사용하지 않는다

다음 코드는 `--enabled false`를 `False`로 바꿔 줄 것처럼 보이지만 그렇지 않다.

```python
parser.add_argument("--enabled", type=bool)
```

Python에서 비어 있지 않은 문자열은 참이므로 `bool("false")`도 `True`다. 켜고 끄는 옵션에는 플래그를 사용한다.

```python
parser.add_argument("--verbose", action="store_true")
```

명시적으로 두 상태를 제공하려면 다음처럼 상호 배타적인 플래그를 사용할 수 있다.

```python
group = parser.add_mutually_exclusive_group()
group.add_argument("--color", dest="color", action="store_true")
group.add_argument("--no-color", dest="color", action="store_false")
parser.set_defaults(color=None)
```

여기서 `None`은 사용자가 어느 옵션도 지정하지 않았다는 뜻이다. 이 구분은 설정 우선순위를 다루는 08-2에서 중요하다.

## 5. 값의 의미까지 검증하기

`type=int`는 `"abc"`를 거부하지만 `-1`도 정수로는 올바르다. 프로그램이 양의 정수만 허용한다면 의미 범위를 추가로 검사해야 한다.

```python
import argparse


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("정수를 입력해야 합니다") from exc

    if number <= 0:
        raise argparse.ArgumentTypeError("1 이상의 정수를 입력해야 합니다")

    return number
```

```python
parser.add_argument(
    "--limit",
    type=positive_int,
    default=20,
    metavar="N",
    help="검사할 최대 줄 수, 기본값: 20",
)
```

```bash
python line_report.py sample.log --limit 0
```

```text
line_report.py: error: argument --limit: 1 이상의 정수를 입력해야 합니다
```

CLI 검증은 다음 세 층으로 나누면 판단이 쉬워진다.

| 검증 층 | 예 | 처리 위치 |
| --- | --- | --- |
| 문법 | 옵션 이름, 필수 인자 수 | `argparse` |
| 단일 값 | 정수 변환, 양수 범위, 선택지 | `type`, `choices` |
| 실행 상태 | 파일 존재, 접근 권한, 네트워크 연결 | 핵심 실행 함수 |

둘 이상의 인자 관계도 파싱 직후 검사할 수 있다.

```python
args = parser.parse_args(argv)

if args.start > args.end:
    parser.error("--start는 --end보다 클 수 없습니다")
```

`parser.error()`는 사용법 오류를 표준 오류에 출력하고 종료 코드 `2`를 발생시킨다. 반면 파일이 실행 중 삭제되거나 권한이 없는 상황은 올바른 명령 형식으로도 생길 수 있는 운영 실패이므로 핵심 실행 단계에서 처리한다.

{% hint style="info" %}
입력 검증의 목표는 모든 실패를 파서에 넣는 것이 아니다. **명령 사용법이 틀린 실패와, 사용법은 맞지만 현재 환경에서 작업할 수 없는 실패를 구분하는 것**이 핵심이다.
{% endhint %}

## 6. `main(argv) -> int`로 실행 경계 만들기

`main()`이 전역 변수인 `sys.argv`를 직접 읽도록 고정하면 다른 코드에서 호출하거나 테스트하기 어렵다. 다음처럼 `argv`를 인자로 받으면 실제 CLI와 함수 호출에 같은 코드를 사용할 수 있다.

```python
def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)
```

- 실제 실행에서 `argv`가 `None`이면 `argparse`가 `sys.argv[1:]`를 읽는다.
- 코드나 테스트에서 `main(["sample.log", "--limit", "5"])`처럼 원하는 인자를 전달할 수 있다.
- 전달하는 목록에는 프로그램 파일 이름을 넣지 않는다.

핵심 로직은 `argparse.Namespace`나 `sys.argv`에 직접 의존하지 않는 함수로 더 분리할 수 있다.

```python
def inspect_lines(path: Path, limit: int) -> tuple[int, int]:
    examined = 0
    nonempty = 0

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if examined >= limit:
                break
            examined += 1
            if line.strip():
                nonempty += 1

    return examined, nonempty
```

이 함수는 입력 경로와 제한값을 받아 결과를 반환한다. CLI 파싱, 출력, 종료를 알지 못하므로 Jupyter Notebook이나 테스트에서도 재사용할 수 있다.

### 응용 인사이트: CLI는 얇은 어댑터다

CLI는 문자열 입력을 Python 값으로 바꾸고, 핵심 함수를 호출하며, 결과를 외부 형식으로 바꾸는 경계다. 분석 규칙이나 파일 처리 전체를 `main()` 안에 작성하면 다른 인터페이스에서 재사용하기 어렵다.

```text
문자열 인자 → 파싱·검증 → Python 값 → 핵심 함수 → 결과 객체 → 출력·종료 상태
```

핵심 함수가 CLI에서 독립되면 나중에 같은 기능을 HTTP API, GUI, 예약 작업에서 호출하더라도 분석 규칙을 다시 작성하지 않아도 된다.

## 7. 표준 출력과 표준 오류

명령줄 프로그램에는 기본적으로 서로 다른 두 출력 통로가 있다.

| 통로 | Python 코드 | 용도 |
| --- | --- | --- |
| 표준 출력(stdout) | `print(result)` | 프로그램이 약속한 정상 결과 |
| 표준 오류(stderr) | `print(message, file=sys.stderr)` | 오류, 경고, 진행 상태, 진단 정보 |

```python
import sys

print('{"examined": 20, "nonempty": 18}')
print("20줄을 검사했습니다", file=sys.stderr)
```

두 통로를 구분하면 정상 결과만 파일이나 다음 프로그램으로 전달할 수 있다.

```bash
python line_report.py sample.log --format json --verbose > result.json
```

이 명령에서 JSON 결과는 `result.json`에 저장되고 진행 메시지는 터미널에 남는다. 진행 메시지까지 stdout에 출력하면 JSON 파일이 깨진다.

{% hint style="warning" %}
오류 메시지와 진행 로그에 비밀번호, 토큰, 쿠키, 전체 인증 헤더, 민감한 원문을 넣지 않는다. 입력값을 보여 줘야 한다면 필요한 필드만 선택하거나 일부를 마스킹한다.
{% endhint %}

## 8. 종료 상태로 결과 전달하기

프로세스가 끝나면 운영체제는 호출자에게 종료 상태를 전달한다. 일반적으로 `0`은 성공, `0`이 아닌 값은 실패를 뜻한다.

이 교안의 예제에서는 다음처럼 단순한 규칙을 사용한다.

| 종료 코드 | 의미 | 예 |
| --- | --- | --- |
| `0` | 작업 성공 | 파일 검사와 결과 출력 완료 |
| `1` | 실행 중 작업 실패 | 파일 없음, 읽기 실패, 결과 생성 실패 |
| `2` | CLI 사용법 오류 | 필수 인자 누락, 잘못된 옵션값 |

`argparse`는 사용법 오류에 기본적으로 `2`를 사용한다. 프로젝트에서 종료 코드를 더 세분화할 수 있지만, 먼저 각 값의 의미를 문서화하고 일관되게 유지해야 한다.

```python
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.input.is_file():
        print("오류: 입력 파일을 찾을 수 없습니다", file=sys.stderr)
        return 1

    print("작업 완료")
    return 0
```

`return 1`은 `main()`의 호출자에게 정수값을 돌려줄 뿐이다. 운영체제까지 전달하려면 모듈 실행 경계에서 `SystemExit`로 바꾼다.

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

POSIX 셸에서는 직전 명령의 종료 상태를 `$?`로 확인한다.

```bash
python line_report.py missing.log
echo $?
```

PowerShell에서는 `$LASTEXITCODE`로 확인한다.

```powershell
python line_report.py missing.log
$LASTEXITCODE
```

### 응용 인사이트: 종료 코드는 자동화의 분기 조건이다

사람은 오류 문장을 읽을 수 있지만 다른 프로그램은 안정된 신호가 필요하다. 종료 코드를 제공하면 호출자는 성공했을 때만 다음 작업을 실행하거나 실패한 작업을 기록할 수 있다.

```bash
python line_report.py sample.log --format json > result.json
if [ $? -eq 0 ]; then
    echo "보고서 생성 완료"
fi
```

종료 코드는 오류 메시지의 대체물이 아니다. 사람에게는 원인을 설명하는 stderr 메시지를 제공하고, 자동화에는 분기 가능한 종료 코드를 제공한다.

## 9. 통합 예제: 줄 요약 CLI

다음 프로그램은 UTF-8 텍스트 파일에서 최대 N줄을 검사하고 전체 줄 수와 빈 줄이 아닌 줄 수를 출력한다. 분석 대상의 실제 내용을 출력하지 않아 불필요한 정보 노출도 줄인다.

```python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("정수를 입력해야 합니다") from exc

    if number <= 0:
        raise argparse.ArgumentTypeError("1 이상의 정수를 입력해야 합니다")

    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="UTF-8 텍스트 파일의 줄 수를 요약한다."
    )
    parser.add_argument(
        "input",
        type=Path,
        metavar="FILE",
        help="읽을 UTF-8 텍스트 파일",
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=20,
        metavar="N",
        help="검사할 최대 줄 수, 기본값: 20",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="출력 형식, 기본값: text",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="진행 정보를 표준 오류에 출력",
    )
    return parser


def inspect_lines(path: Path, limit: int) -> dict[str, int | str]:
    examined = 0
    nonempty = 0

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if examined >= limit:
                break
            examined += 1
            if line.strip():
                nonempty += 1

    return {
        "file": path.name,
        "examined": examined,
        "nonempty": nonempty,
    }


def render_result(result: dict[str, int | str], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(result, ensure_ascii=False)

    return (
        f"파일: {result['file']}\n"
        f"검사한 줄: {result['examined']}\n"
        f"내용이 있는 줄: {result['nonempty']}"
    )


def run(args: argparse.Namespace) -> int:
    if not args.input.is_file():
        print(
            f"오류: 입력 파일을 찾을 수 없습니다: {args.input}",
            file=sys.stderr,
        )
        return 1

    try:
        result = inspect_lines(args.input, args.limit)
    except (OSError, UnicodeError) as exc:
        print(f"오류: 입력 파일을 읽지 못했습니다: {exc}", file=sys.stderr)
        return 1

    if args.verbose:
        print(
            f"진행: 최대 {args.limit}줄을 검사했습니다",
            file=sys.stderr,
        )

    print(render_result(result, args.format))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

예제 파일을 만든 뒤 여러 입력을 확인한다.

```text
ALLOW student01

DENY unknown
ALLOW student02
```

```bash
python line_report.py sample.log
python line_report.py sample.log --limit 2
python line_report.py sample.log --format json --verbose
python line_report.py sample.log --limit 0
python line_report.py missing.log
```

예상 결과를 외우기보다 다음을 직접 확인한다.

1. `--limit 2`에서 빈 줄도 검사한 줄 수에 포함되는가?
2. `--format json --verbose`의 stdout과 stderr는 섞이지 않는가?
3. `--limit 0`과 없는 파일의 종료 코드는 어떻게 다른가?
4. `--help`만 실행했을 때 파일을 읽으려 하지 않는가?

## 10. 대표적인 실패 사례

### 10.1 `sys.argv`의 위치를 직접 고정한다

```python
input_path = sys.argv[1]
limit = int(sys.argv[2])
```

입력 누락 시 `IndexError`가 발생하고 사용자는 올바른 사용법을 알기 어렵다. 옵션 순서를 바꾸거나 새 옵션을 추가하기도 어렵다. `argparse`로 계약을 선언한다.

### 10.2 모든 코드를 `main()`에 넣는다

파싱, 파일 읽기, 분석, 출력이 한 함수에 섞이면 Notebook이나 테스트에서 핵심 기능만 호출하기 어렵다. 입력 변환은 CLI 경계에서, 분석은 일반 함수에서, 출력 형식화는 별도 함수에서 맡는다.

### 10.3 핵심 함수에서 `sys.exit()`를 호출한다

```python
def inspect_lines(path, limit):
    if not path.exists():
        sys.exit(1)
```

재사용하는 코드가 프로세스 전체를 끝내 버린다. 핵심 함수는 결과를 반환하거나 구체적인 예외를 발생시키고, 종료 여부와 코드는 `main()`이 결정한다.

### 10.4 정상 결과와 진행 메시지를 stdout에 함께 출력한다

JSON, CSV처럼 다른 프로그램이 읽을 결과에 설명 문장이 섞이면 파싱할 수 없다. 정상 결과는 stdout, 진단과 진행 메시지는 stderr로 분리한다.

### 10.5 모든 실패를 같은 문장으로 숨긴다

```python
def main():
    try:
        run_task()
    except Exception:
        print("오류가 발생했습니다", file=sys.stderr)
        return 1
```

원인과 복구 기준을 알 수 없고 개발 중인 버그까지 감춘다. 예상 가능한 예외만 구체적으로 처리하고, 사용자가 조치할 수 있는 맥락을 제공한다. 단, 민감한 원문은 포함하지 않는다.

### 10.6 비밀값을 CLI 인자로 받는다

명령 기록과 프로세스 정보에 남을 수 있으므로 토큰과 비밀번호를 일반 옵션으로 설계하지 않는다. 비밀값은 코드와 일반 설정에서 분리하고, 실제 실행 환경이 안전한 방식으로 주입하도록 한다.

## 11. 연습문제

### 연습 1. CLI 요소 분류

다음 명령에서 위치 인자, 선택 인자, 옵션값, 플래그를 분류한다.

```bash
python report.py events.json --limit 50 --format text --verbose
```

### 연습 2. 범위 검증 함수 작성

`1`부터 `65535`까지의 값만 정수로 반환하고, 그 밖의 입력은 `argparse.ArgumentTypeError`를 발생시키는 `port_number()`를 작성한다.

### 연습 3. 잘못된 불리언 옵션 수정

다음 코드를 `--dry-run`이 있을 때만 `True`가 되도록 수정한다.

```python
parser.add_argument("--dry-run", type=bool, default=False)
```

### 연습 4. 출력 통로 분리

다음 요구사항을 만족하는 코드를 작성한다.

- 결과 `{"status": "ok"}`는 stdout에 출력한다.
- `검사를 시작합니다`는 `--verbose`일 때만 stderr에 출력한다.
- 성공 시 `0`을 반환한다.

### 연습 5. 종료 코드 결정

다음 상황에 이 절의 규칙상 어떤 종료 코드가 적합한지 설명한다.

1. `--limit abc`
2. 필수 위치 인자 누락
3. 올바른 경로 형식이지만 파일이 존재하지 않음
4. 파일 검사와 결과 출력 성공

### 연습 6. 미니 실습

09장의 테스트를 준비한다는 생각으로 다음 조건의 CLI를 만든다.

- `main(argv: list[str] | None = None) -> int` 구조를 사용한다.
- 위치 인자로 UTF-8 텍스트 파일을 받는다.
- `--contains TEXT`로 특정 문자열이 포함된 줄 수를 센다.
- `--ignore-case` 플래그를 지원한다.
- 결과는 stdout, 오류는 stderr에 출력한다.
- 정상, 파일 없음, 빈 검색어를 서로 구분한다.

## 12. 정답과 해설

<details>
<summary>연습 1 정답</summary>

- 위치 인자: `events.json`
- 선택 인자: `--limit`, `--format`
- 옵션값: `50`, `text`
- 플래그: `--verbose`
- `report.py`는 실행할 프로그램 이름이며 `parse_args()`가 반환하는 사용자 인자에는 포함되지 않는다.

</details>

<details>
<summary>연습 2 정답 예시</summary>

```python
import argparse


def port_number(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("포트는 정수여야 합니다") from exc

    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(
            "포트는 1부터 65535 사이여야 합니다"
        )

    return port
```

`type=int`만으로는 `0`, 음수, `65536`을 거부할 수 없으므로 업무 규칙에 해당하는 범위를 추가로 검사한다.

</details>

<details>
<summary>연습 3 정답</summary>

```python
parser.add_argument("--dry-run", action="store_true")
```

플래그가 없으면 기본적으로 `False`, 있으면 `True`가 된다. 설정 파일이나 환경 변수와 병합하며 “지정하지 않음”을 구분해야 한다면 `default=None`을 추가한다.

</details>

<details>
<summary>연습 4 정답 예시</summary>

```python
import json
import sys


def run(verbose: bool) -> int:
    if verbose:
        print("검사를 시작합니다", file=sys.stderr)

    print(json.dumps({"status": "ok"}))
    return 0
```

정상 결과에 진행 문장을 섞지 않아 stdout을 JSON으로 바로 읽을 수 있다.

</details>

<details>
<summary>연습 5 정답</summary>

1. `--limit abc`: CLI 값 변환 실패이므로 `argparse`의 종료 코드 `2`
2. 필수 위치 인자 누락: 사용법 오류이므로 종료 코드 `2`
3. 파일이 존재하지 않음: 실행 환경에서 작업할 수 없는 실패이므로 종료 코드 `1`
4. 파일 검사와 결과 출력 성공: 종료 코드 `0`

프로젝트마다 더 세분화할 수 있지만 같은 실패에 같은 의미를 유지해야 한다.

</details>

<details>
<summary>연습 6 구현 힌트</summary>

1. `non_empty_text()` 같은 사용자 정의 변환 함수로 빈 검색어를 거부한다.
2. `count_matching_lines(path, text, ignore_case)`는 CLI를 모르는 일반 함수로 작성한다.
3. 대소문자를 무시할 때 원문과 검색어 모두 `casefold()`를 적용한다.
4. 파일 관련 `OSError`와 디코딩 관련 `UnicodeError`를 실행 경계에서 처리한다.
5. `main(["sample.txt", "--contains", "ALLOW"])`처럼 직접 호출해 볼 수 있게 한다.

완성 후 정상 파일, 없는 파일, 빈 파일, 일치 항목이 없는 파일, 대소문자가 다른 입력을 확인한다.

</details>

## 13. 응용 인사이트 정리

### CLI 옵션 이름은 변경 비용이 있는 공개 API다

자동화 스크립트나 문서가 `--output`이라는 이름에 의존하기 시작하면 옵션 이름 변경은 호출자를 깨뜨릴 수 있다. 짧고 모호한 이름보다 목적이 드러나는 이름을 사용하고, 기본값과 출력 형식을 도움말에 명시한다.

### 파싱과 실행을 나누면 실패의 책임이 선명해진다

`argparse`는 잘못된 사용법을 거부하고 핵심 함수는 실제 작업의 성공과 실패를 결정한다. 이 경계를 유지하면 오류 메시지와 종료 코드가 원인에 맞게 대응한다.

### stdout은 데이터 계약이고 stderr는 관찰 통로다

stdout을 안정된 JSON이나 텍스트 결과로 유지하면 파이프라인에서 재사용할 수 있다. 진행 로그와 진단 메시지는 stderr로 보내되, 두 통로 모두 비밀값과 불필요한 원문을 노출하지 않아야 한다.

### `main(argv)`는 입력 의존성을 주입하는 가장 작은 구조다

전역 `sys.argv`에 고정하지 않고 목록을 전달할 수 있게 하면 같은 실행 흐름을 정상·오류·경계 인자로 반복 검증할 수 있다. 09장에서는 이 구조를 테스트에 연결한다.

## 14. 완료 기준

- [ ] 위치 인자, 선택 인자, 플래그를 구분할 수 있다.
- [ ] `argparse`로 `--help`, 자료형 변환, 선택지, 기본값을 제공할 수 있다.
- [ ] 단순 자료형 검증과 실행 환경 검증을 구분할 수 있다.
- [ ] `type=bool`의 문제를 설명하고 적절한 플래그를 선택할 수 있다.
- [ ] 핵심 로직을 CLI 파싱과 분리할 수 있다.
- [ ] `main(argv) -> int`와 `raise SystemExit(main())`를 연결할 수 있다.
- [ ] 정상 결과는 stdout, 오류·진행 정보는 stderr로 보낼 수 있다.
- [ ] 성공, 운영 실패, 사용법 오류를 종료 코드로 구분할 수 있다.
- [ ] 비밀값을 CLI 인자와 출력에 포함하지 않아야 하는 이유를 설명할 수 있다.
- [ ] 정상·오류·경계 입력으로 CLI 계약을 직접 확인할 수 있다.

---

다음 절: [08-2. 설정 우선순위와 환경 변수](08-2-configuration-environment.md)
