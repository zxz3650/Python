# 04-2. 텍스트 파일과 with

텍스트 파일 입출력은 파일의 내용을 문자열로 읽거나 문자열을 파일에 저장하는 작업입니다. 파일을 열 때는 모드와 인코딩을 명시하고 `with`로 자원 수명을 관리합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 읽기·쓰기·추가 모드를 구분합니다.
- `with`를 사용해 파일을 안전하게 닫습니다.
- 전체 읽기와 한 줄씩 읽기를 선택합니다.
- 덮어쓰기와 줄바꿈 관련 실수를 방지합니다.
{% endhint %}

## 선행 지식

04-1의 경로와 `Path`를 이해해야 합니다.

## 1. 파일 모드

| 모드 | 의미 | 파일이 없을 때 | 파일이 있을 때 |
|---|---|---|---|
| `r` | 읽기 | 오류 | 기존 내용 읽기 |
| `w` | 쓰기 | 새로 생성 | 기존 내용 삭제 후 쓰기 |
| `a` | 추가 | 새로 생성 | 기존 내용 뒤에 추가 |
| `x` | 새 파일 생성 | 새로 생성 | `FileExistsError` |

## 2. with로 파일 열기

```python
from pathlib import Path

path = Path("message.txt")

with path.open("w", encoding="utf-8") as file:
    file.write("첫 번째 줄\n")
    file.write("두 번째 줄\n")
```

`with` 블록이 끝나면 정상 실행과 예외 발생 여부에 관계없이 파일이 닫힙니다.

## 3. 전체 내용 읽기

```python
with path.open("r", encoding="utf-8") as file:
    text = file.read()

print(text)
print(type(text))  # str
```

작은 설정 파일처럼 전체 크기가 충분히 작을 때 사용합니다.

`Path`의 편의 메서드도 사용할 수 있습니다.

```python
text = path.read_text(encoding="utf-8")
path.write_text("새 내용\n", encoding="utf-8")
```

`write_text()`도 기존 내용을 덮어씁니다.

## 4. 한 줄씩 읽기

```python
with path.open("r", encoding="utf-8") as file:
    for line_number, line in enumerate(file, start=1):
        clean = line.rstrip("\n")
        print(line_number, clean)
```

파일 객체는 반복 가능한 객체입니다. 한 줄씩 처리하면 전체 파일을 한꺼번에 메모리에 올리지 않습니다.

`strip()`은 앞뒤 공백까지 제거하지만 `rstrip("\n")`은 줄바꿈만 제거합니다. 원문의 공백이 중요하다면 차이를 구분합니다.

## 5. 여러 줄 쓰기

```python
lines = ["alpha\n", "beta\n", "gamma\n"]

with Path("items.txt").open("w", encoding="utf-8") as file:
    file.writelines(lines)
```

`writelines()`는 줄바꿈을 자동으로 추가하지 않습니다. 각 문자열에 `\n`을 포함해야 합니다.

다른 방법은 `join()`입니다.

```python
items = ["alpha", "beta", "gamma"]
Path("items.txt").write_text(
    "\n".join(items) + "\n",
    encoding="utf-8",
)
```

## 6. 파일 끝에 추가

```python
with Path("history.log").open("a", encoding="utf-8") as file:
    file.write("프로그램 실행\n")
```

기존 내용을 유지해야 하는 이력 파일에는 `a` 모드를 사용합니다.

## 7. 오류 처리

```python
try:
    text = Path("missing.txt").read_text(encoding="utf-8")
except FileNotFoundError as exc:
    print("파일을 찾을 수 없습니다:", exc)
except PermissionError as exc:
    print("파일을 읽을 권한이 없습니다:", exc)
```

파일 없음과 권한 부족은 해결 방법이 다르므로 구분합니다.

## 흔한 실수

- 기존 파일에 `w` 모드를 사용해 내용을 잃음
- 인코딩을 생략해 실행환경마다 결과가 달라짐
- `writelines()`가 줄바꿈을 추가한다고 생각함
- 파일 전체를 읽은 뒤 다시 줄 단위로 처리함
- `strip()`으로 의미 있는 공백까지 제거함

{% hint style="success" %}
## 🧪 종합 실습

1. 작업 목록 세 줄을 UTF-8 파일에 저장합니다.
2. 행 번호와 함께 한 줄씩 읽습니다.
3. 실행 이력을 별도 파일 끝에 추가합니다.
4. 없는 파일을 읽었을 때 사용자에게 원인을 출력합니다.
{% endhint %}

## 완료 기준

- [ ] 파일 모드별 기존 파일 처리 차이를 설명할 수 있습니다.
- [ ] `with`를 사용해 파일을 읽고 쓸 수 있습니다.
- [ ] 파일 크기에 따라 전체 읽기와 줄 단위 읽기를 선택할 수 있습니다.

---

다음 절: [04-3. 인코딩, str, bytes](04-3-encoding-bytes.md)
