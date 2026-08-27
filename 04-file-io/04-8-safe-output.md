# 04-8. 임시 파일과 원자적 저장

결과 파일에 직접 쓰다가 프로그램이 중단되면 기존 결과가 사라지거나 불완전한 파일이 남을 수 있습니다. 이 절에서는 출력 파일과 같은 디렉터리에 임시 파일을 만든 뒤 완성된 결과만 교체하는 저장 절차를 학습합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 직접 덮어쓰기와 임시 파일 교체의 차이를 설명합니다.
- `tempfile`로 충돌하지 않는 임시 파일을 만듭니다.
- 쓰기·동기화·교체·실패 정리 단계를 구분합니다.
- 입력과 출력 경로가 같은지 확인합니다.
- 원자적 교체가 보장하는 범위와 한계를 설명합니다.
{% endhint %}

## 선행 지식

04-1부터 04-7까지의 경로, 파일 모드, JSON 직렬화, 예외 처리를 이해해야 합니다.

## 1. 직접 덮어쓰기의 문제

```python
output.write_text(text, encoding="utf-8")
```

`write_text()`는 기존 파일을 먼저 비웁니다. 직렬화, 디스크 쓰기 또는 프로그램 실행이 중간에 실패하면 기존의 정상 결과까지 잃을 수 있습니다.

다음 순서로 위험을 줄입니다.

```text
출력 디렉터리 확인
→ 같은 디렉터리에 고유한 임시 파일 생성
→ 전체 내용 쓰기
→ 버퍼 반영
→ 임시 파일 닫기
→ 최종 경로로 교체
→ 실패한 임시 파일 정리
```

## 2. 고정된 임시 파일명의 문제

```python
temporary = output.with_suffix(".json.tmp")
```

설명하기는 쉽지만 프로그램을 동시에 실행하면 같은 임시 파일을 사용할 수 있습니다. 공격자가 미리 같은 경로를 만들거나 링크로 바꾸는 상황도 고려해야 합니다. 고유한 임시 파일은 `tempfile`로 생성합니다.

## 3. JSON을 임시 파일에 저장하기

```python
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


def save_json_safely(data, output_path):
    output_path = Path(output_path).resolve()
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
            temporary_path = Path(temporary.name)

        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
```

임시 파일을 출력과 같은 디렉터리에 만드는 이유는 다른 파일시스템 사이의 이동을 피하고 교체 가능성을 높이기 위해서입니다.

## 4. 각 단계의 책임

| 단계 | 목적 |
| --- | --- |
| `json.dump()` | Python 값을 JSON 텍스트로 직렬화 |
| `flush()` | Python 버퍼를 운영체제에 전달 |
| `os.fsync()` | 파일 데이터 반영을 운영체제에 요청 |
| 파일 닫기 | 다른 프로세스와 운영체제가 파일을 다룰 수 있게 함 |
| `os.replace()` | 완성된 임시 파일을 최종 경로로 교체 |
| `finally` 정리 | 실패한 임시 파일 제거 |

`os.replace()`는 같은 파일시스템의 일반적인 로컬 파일에서 원자적인 이름 교체를 제공합니다. 모든 네트워크 파일시스템의 내구성이나 정전 뒤의 완전한 보존까지 자동으로 보장하는 것은 아닙니다.

## 5. 입력과 출력이 같은지 확인하기

변환 프로그램은 원본을 결과 파일로 덮어쓰지 않도록 확인합니다.

```python
def ensure_different_paths(input_path, output_path):
    source = Path(input_path).resolve()
    destination = Path(output_path).resolve()

    if source == destination:
        raise ValueError("입력과 출력 경로는 달라야 합니다")
```

기본 출력 이름을 입력 파일 옆에 만들더라도 충돌 정책을 문서화합니다.

```python
output_path = input_path.with_name(
    input_path.name + ".analysis.json"
)
```

## 6. 기존 결과의 백업 정책

교체 전 기존 결과를 보존해야 한다면 백업 이름과 보존 기간을 먼저 정합니다.

```python
backup_path = output_path.with_suffix(output_path.suffix + ".bak")
```

백업을 무제한 생성하지 않습니다. 민감한 데이터가 포함된 결과라면 백업 파일에도 같은 접근 권한과 삭제 정책을 적용합니다.

## 7. 저장 후 다시 검증하기

저장 성공은 파일이 존재한다는 뜻만이 아니라 다시 읽고 필요한 구조를 확인할 수 있다는 뜻이어야 합니다.

```python
with output_path.open("r", encoding="utf-8") as file:
    restored = json.load(file)

if not isinstance(restored, dict):
    raise TypeError("보고서 최상위 값은 object여야 합니다")
if "summary" not in restored:
    raise ValueError("summary 필드가 없습니다")
```

## 흔한 실수

- 결과 파일에 직접 쓰면서 안전한 저장이라고 표현함
- 모든 실행이 같은 `.tmp` 파일명을 사용함
- 임시 파일을 다른 파일시스템에 생성함
- 예외가 발생한 뒤 임시 파일을 정리하지 않음
- 입력 파일과 출력 파일을 같은 경로로 지정함
- 저장한 JSON을 다시 읽어보지 않음

{% hint style="success" %}
## 🧪 종합 실습

1. 정상 보고서를 `save_json_safely()`로 저장합니다.
2. 저장한 JSON을 다시 읽어 필수 키를 검증합니다.
3. 직렬화할 수 없는 값을 넣어 실패한 임시 파일이 정리되는지 확인합니다.
4. 입력과 출력에 같은 경로를 전달했을 때 거부되는지 확인합니다.
5. 기존 결과를 유지할지 교체할지 정책을 한 문장으로 작성합니다.
{% endhint %}

## 완료 기준

- [ ] 직접 덮어쓰기와 임시 파일 교체의 차이를 설명할 수 있습니다.
- [ ] 같은 디렉터리에 고유한 임시 파일을 만들 수 있습니다.
- [ ] 실패한 임시 파일을 `finally`에서 정리할 수 있습니다.
- [ ] 입력과 출력 경로의 충돌을 검사할 수 있습니다.
- [ ] 저장 결과를 다시 읽어 구조를 검증할 수 있습니다.

---

다음 절: [04-9. 파일 분석기 종합 실습](04-9-file-analyzer.md)
