# 04-8. 임시 파일과 원자적 저장

결과 파일에 직접 쓰다가 프로그램이 중단되면 기존 결과를 잃거나 불완전한 파일을 남길 수 있다. 이 절에서는 출력 파일과 같은 디렉터리에 고유한 임시 파일을 만들고, 쓰기와 검증을 모두 마친 결과만 최종 경로로 교체하는 절차를 학습한다.

{% hint style="info" %}
### 🧭 학습 목표

- 직접 덮어쓰기와 임시 파일 교체의 차이를 설명한다.
- `tempfile`로 충돌하지 않는 임시 파일을 만든다.
- 쓰기·버퍼 반영·검증·교체·실패 정리 단계를 구분한다.
- 입력과 출력이 같은 파일을 가리키는지 확인한다.
- 원자적 교체와 데이터 내구성의 차이를 설명한다.
{% endhint %}

## 학습 우선순위

| 구분 | 내용 |
| --- | --- |
| 필수 | 같은 디렉터리의 임시 파일, `finally` 정리, `os.replace()` |
| 권장 | 저장 전 구조 검증, 입력·출력 충돌 검사, 실패 테스트 |
| 심화 | 동시 실행 정책, 디렉터리 동기화, 백업·권한·보존 정책 |

## 선행 지식과 학습 연결

- 경로와 파일 모드는 04-1~04-3에서 학습했다.
- JSON 직렬화와 예외 처리는 04-6~04-7에서 학습했다.
- 04-7의 순차 출력도 이 절의 임시 파일에 기록해야 기존 결과를 보호할 수 있다.
- [04-9 파일 분석기](04-9-file-analyzer.md)는 완성된 JSON 보고서를 이 절의 절차로 저장한다.

전용 실습은 [`notebooks/04-8-safe-output.ipynb`](../notebooks/04-8-safe-output.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

다음 질문에 먼저 답해 본다.

1. 쓰기 모드 `"w"`로 기존 파일을 열면 언제 내용이 사라지는가?
2. 임시 파일을 출력과 다른 파일 시스템에 만들면 `os.replace()`에 어떤 문제가 생길 수 있는가?
3. 임시 파일 쓰기에 실패했을 때 어떤 경로를 정리해야 하는가?
4. “원자적으로 보인다”와 “정전 후에도 반드시 남는다”는 같은 뜻인가?

## 1. 직접 덮어쓰기의 문제

```python
with output_path.open("w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False)
```

쓰기 모드로 기존 파일을 열면 파일을 먼저 비운다. 그 뒤 직렬화 오류, 디스크 공간 부족, 입출력 오류 또는 프로그램 중단이 발생하면 기존의 정상 결과는 이미 사라졌고 새 파일은 불완전할 수 있다.

다음 순서로 위험을 줄인다.

```text
출력 디렉터리 확인
→ 같은 디렉터리에 고유한 임시 파일 생성
→ 전체 내용 쓰기
→ 버퍼와 파일 데이터 반영 요청
→ 임시 파일 닫기
→ 임시 파일을 다시 읽어 검증
→ 최종 경로로 교체
→ 실패하면 임시 파일 정리
```

## 2. 고정된 임시 파일명의 문제

```python
temporary_path = output_path.with_suffix(".json.tmp")
```

고정 이름은 설명하기 쉽지만 프로그램을 동시에 실행하면 같은 임시 파일을 공유할 수 있다. 다른 프로세스가 먼저 만든 경로와 충돌할 수도 있다. 임시 파일을 직접 예측 가능한 이름으로 만들지 않고 표준 라이브러리 `tempfile`을 사용한다.

{% hint style="warning" %}
수업에서는 자신이 소유하거나 교사가 제공한 디렉터리에만 결과를 저장한다. 운영 시스템 경로와 다른 사용자의 파일을 대상으로 실습하지 않는다.
{% endhint %}

## 3. JSON 보고서의 구조 검증

저장할 보고서의 최소 계약을 함수로 분리한다.

```python
def validate_report(value):
    if not isinstance(value, dict):
        raise TypeError("보고서 최상위 값은 JSON 객체여야 한다")
    if "summary" not in value:
        raise ValueError("summary 필드가 없다")
    if not isinstance(value["summary"], dict):
        raise TypeError("summary는 JSON 객체여야 한다")
```

직렬화가 가능하다는 사실만으로 보고서가 요구사항을 만족하는 것은 아니다. 필요한 키와 값의 자료형을 별도로 검사한다.

## 4. 임시 파일에 쓰고 검증한 뒤 교체하기

```python
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


def save_json_safely(data, output_path, validator=None):
    output_path = Path(output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)

            json.dump(
                data,
                temporary,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())

        with temporary_path.open("r", encoding="utf-8") as file:
            restored = json.load(file)

        if validator is not None:
            validator(restored)

        os.replace(temporary_path, output_path)
        temporary_path = None
        return output_path
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
```

`temporary_path`는 임시 파일을 연 직후 기록한다. `json.dump()`나 `fsync()`가 실패하더라도 `finally`가 어느 파일을 지워야 하는지 알 수 있어야 하기 때문이다.

임시 파일은 출력과 같은 디렉터리에 만든다. 그래야 다른 파일 시스템 사이의 이동을 피하고 같은 파일 시스템 안에서 교체할 가능성을 높일 수 있다. 임시 파일은 반드시 닫은 뒤 교체하므로 Windows에서도 열린 임시 파일 때문에 교체가 실패할 가능성을 줄인다.

## 5. 각 단계의 책임

| 단계 | 목적 |
| --- | --- |
| `json.dump()` | Python 값을 JSON 텍스트로 직렬화한다. |
| `flush()` | Python의 사용자 공간 버퍼를 운영체제에 전달한다. |
| `os.fsync()` | 운영체제에 파일 데이터 반영을 요청한다. |
| 파일 닫기 | 출력 버퍼를 정리하고 파일 핸들을 해제한다. |
| `json.load()` | 임시 파일이 다시 읽히는지 확인한다. |
| 검증 함수 | 필수 키와 자료형 등 보고서 계약을 검사한다. |
| `os.replace()` | 검증된 임시 파일을 최종 경로로 교체한다. |
| `finally` 정리 | 실패 과정에서 남은 임시 파일을 제거한다. |

`os.replace()`는 같은 파일 시스템의 일반적인 로컬 파일에서 독자가 이전 파일이나 새 파일 중 하나를 보게 하는 원자적인 이름 교체를 제공한다. 중간 내용이 노출되는 위험을 줄이는 것이 핵심이다.

그러나 다음 항목까지 자동으로 보장하지는 않는다.

- 여러 프로세스가 동시에 쓸 때의 실행 순서와 마지막 작성자 정책
- 모든 네트워크 파일 시스템의 원자성
- 저장 장치와 운영체제 조합별 정전 후 내구성
- 파일 권한·소유자·확장 속성의 유지
- 백업 파일 생성과 보존 기간

POSIX 환경에서 정전 내구성을 더 엄격하게 요구한다면 교체 뒤 출력 디렉터리 자체를 동기화하는 절차가 추가로 필요할 수 있다. 이 과정에서는 플랫폼 공통의 핵심 절차와 그 한계를 구분하는 데 집중한다.

## 6. 입력과 출력이 같은 파일인지 확인하기

문자열이 달라도 심볼릭 링크나 하드 링크를 통해 같은 파일을 가리킬 수 있다. 먼저 정규화한 경로를 비교하고, 두 경로가 모두 존재하면 `samefile()`로 실제 파일도 비교한다.

```python
def ensure_different_paths(input_path, output_path):
    source = Path(input_path).expanduser().resolve()
    destination = Path(output_path).expanduser().resolve()

    if source == destination:
        raise ValueError("입력과 출력 경로는 달라야 한다")

    if source.exists() and destination.exists():
        if source.samefile(destination):
            raise ValueError("입력과 출력이 같은 파일을 가리킨다")
```

이 검사는 실수로 원본을 덮어쓰는 위험을 줄이지만 검사 직후 다른 프로세스가 경로를 바꾸는 경쟁 조건까지 제거하지는 않는다. 입력과 출력 디렉터리를 신뢰할 수 있는 학습 작업 공간으로 제한한다.

기본 출력 이름은 입력 파일과 구분되게 만든다.

```python
output_path = input_path.with_name(
    input_path.name + ".analysis.json"
)
```

## 7. 백업과 동시 실행 정책

원자적 교체는 기존 결과를 자동으로 백업하지 않는다. 백업이 필요하다면 다음 정책을 먼저 정한다.

- 백업 파일 이름에 시각 또는 버전을 포함할지 정한다.
- 최대 백업 개수와 보존 기간을 정한다.
- 민감정보가 있으면 원본과 같은 접근 권한·암호화·삭제 정책을 적용한다.
- 동시에 여러 실행이 같은 출력에 쓰는 것을 허용할지 정한다.
- 동시 쓰기를 허용한다면 마지막 작성자 우선인지 잠금이 필요한지 정한다.

```python
backup_path = output_path.with_suffix(output_path.suffix + ".bak")
```

위 코드는 백업 **경로 이름만 계산**한다. 실제 백업 생성·교체·정리 정책은 별도로 구현해야 한다.

## 8. 성공과 실패를 재현하는 실습

다음 코드는 별도의 임시 디렉터리에서 성공과 직렬화 실패를 검증하므로 기존 학습 파일을 변경하지 않는다.

```python
import json
from pathlib import Path
from tempfile import TemporaryDirectory


with TemporaryDirectory() as directory:
    folder = Path(directory)
    output = folder / "report.json"

    first_report = {"summary": {"valid": 2, "errors": 1}}
    save_json_safely(first_report, output, validate_report)

    with output.open("r", encoding="utf-8") as file:
        assert json.load(file) == first_report

    try:
        invalid_report = {
            "summary": {"valid": 3},
            "not_json": object(),
        }
        save_json_safely(invalid_report, output, validate_report)
    except TypeError:
        pass
    else:
        raise AssertionError("직렬화 실패가 발생해야 한다")

    with output.open("r", encoding="utf-8") as file:
        assert json.load(file) == first_report

    temporary_files = list(
        folder.glob(f".{output.name}.*.tmp")
    )
    assert temporary_files == []
```

검증할 결과는 세 가지다.

1. 정상 보고서는 다시 읽을 수 있다.
2. 새 보고서 저장이 실패해도 기존 정상 보고서는 유지된다.
3. 실패한 임시 파일이 남지 않는다.

## 흔한 실수와 점검법

| 실수 | 점검법 |
| --- | --- |
| 결과 파일에 직접 쓰면서 안전한 저장이라고 표현함 | 쓰기 대상이 임시 파일인지 확인한다. |
| 모든 실행이 같은 `.tmp` 이름을 사용함 | `NamedTemporaryFile`이 만든 고유 경로를 사용한다. |
| 임시 경로를 직렬화 뒤에 기록함 | 파일을 연 직후 `temporary_path`를 저장한다. |
| 임시 파일을 다른 파일 시스템에 생성함 | `dir=output_path.parent`를 지정한다. |
| 예외 뒤 임시 파일을 정리하지 않음 | `finally`와 실패 테스트로 검증한다. |
| 입력·출력 문자열만 비교함 | `resolve()`와 가능한 경우 `samefile()`을 사용한다. |
| 원자적 교체를 정전 내구성으로 오해함 | 원자성·내구성·동시성 정책을 따로 적는다. |
| 백업 경로만 만들고 백업했다고 표현함 | 실제 복사·교체·정리 절차를 검증한다. |

{% hint style="success" %}
### 🧪 종합 실습

1. 정상 보고서를 `save_json_safely()`로 저장한다.
2. 저장 전 임시 파일을 다시 읽어 필수 키를 검증한다.
3. 직렬화할 수 없는 값을 넣어 기존 결과가 유지되는지 확인한다.
4. 실패한 임시 파일이 정리되는지 확인한다.
5. 입력과 출력에 같은 경로를 전달했을 때 거부되는지 확인한다.
6. 기존 결과의 교체·백업·동시 실행 정책을 각각 한 문장으로 작성한다.
{% endhint %}

## 완료 기준

- [ ] 직접 덮어쓰기와 임시 파일 교체의 차이를 설명한다.
- [ ] 출력과 같은 디렉터리에 고유한 임시 파일을 만든다.
- [ ] 임시 경로를 쓰기 전에 기록하고 실패 시 정리한다.
- [ ] 임시 파일을 다시 읽어 JSON 문법과 구조를 검증한다.
- [ ] 입력과 출력이 같은 파일을 가리키는지 검사한다.
- [ ] 원자성·내구성·동시성·백업 정책을 구분한다.
- [ ] 성공과 실패 경로를 자동으로 재현한다.

## 핵심 정리

- 최종 경로가 아니라 같은 디렉터리의 고유한 임시 파일에 먼저 쓴다.
- 임시 파일을 닫고 검증한 뒤 `os.replace()`로 교체한다.
- 실패 가능성이 있는 첫 작업 전에 정리할 임시 경로를 기록한다.
- 원자적 교체는 불완전한 내용의 노출을 줄이지만 모든 내구성과 동시성 문제를 해결하지는 않는다.
- 저장 기능은 성공뿐 아니라 기존 결과 보존과 임시 파일 정리까지 실패 테스트로 확인한다.

---

다음 절: [04-9. 파일 분석기 종합 실습](04-9-file-analyzer.md)
