# 04-4. 인코딩·bytes와 바이너리 구조

컴퓨터는 문자를 직접 저장하지 않고 숫자로 표현된 바이트를 저장합니다. 인코딩은 문자와 바이트 사이의 변환 규칙입니다.

{% hint style="info" %}
## 🧭 학습 목표

- `str`과 `bytes`의 차이를 설명합니다.
- UTF-8로 인코딩하고 디코딩합니다.
- 텍스트 모드와 바이너리 모드를 구분합니다.
- 디코딩 오류의 원인과 처리 방식을 이해합니다.
- 파일 위치를 이동해 필요한 바이트만 읽습니다.
- 바이트 순서에 따라 정수를 해석합니다.
{% endhint %}

## 선행 지식

기본 자료형과 04-3의 텍스트 파일 처리를 이해해야 합니다.

## 1. str과 bytes

```python
text = "Python 한글"
raw = text.encode("utf-8")

print(type(text))  # str
print(type(raw))   # bytes
print(raw)
```

- `str`: 사람이 읽는 문자 데이터
- `bytes`: 0~255 범위 정수로 구성된 바이트 데이터

```python
restored = raw.decode("utf-8")
print(restored)
print(restored == text)  # True
```

인코딩과 디코딩에 같은 규칙을 사용해야 원래 문자열을 복원할 수 있습니다.

## 2. 바이트의 길이

```python
text = "가"
raw = text.encode("utf-8")

print(len(text))  # 문자 1개
print(len(raw))   # UTF-8 바이트 3개
```

문자 수와 저장 바이트 수는 같지 않을 수 있습니다.

## 3. 텍스트 모드와 바이너리 모드

```python
from pathlib import Path

Path("hello.txt").write_text("안녕하세요", encoding="utf-8")
text = Path("hello.txt").read_text(encoding="utf-8")

Path("sample.bin").write_bytes(b"\x4d\x5a\x90\x00")
raw = Path("sample.bin").read_bytes()
```

텍스트 파일은 문자열과 인코딩을 다루고, 바이너리 파일은 원본 바이트를 그대로 다룹니다.

## 4. bytes 조회와 슬라이싱

```python
header = b"MZ\x90\x00"

print(header[0])      # 77
print(header[:2])     # b'MZ'
print(header.hex())   # 4d5a9000
```

bytes를 인덱싱하면 한 바이트의 정숫값이 나오고, 슬라이싱하면 bytes가 나옵니다.

## 5. bytearray

`bytes`는 불변 객체입니다. 내용을 수정해야 한다면 `bytearray`를 사용합니다.

```python
data = bytearray(b"ABC")
data[0] = 90

print(data)        # bytearray(b'ZBC')
print(bytes(data)) # b'ZBC'
```

## 6. 디코딩 오류

```python
invalid = b"\xff\xfe"

try:
    text = invalid.decode("utf-8")
except UnicodeDecodeError as exc:
    print("UTF-8 디코딩 실패:", exc)
```

오류를 무조건 무시하기 전에 실제 인코딩을 확인합니다.

```python
print(invalid.decode("utf-8", errors="replace"))
```

`errors="replace"`는 해석할 수 없는 데이터를 대체문자로 바꿉니다. 원본 분석이 필요하다면 원본 bytes도 별도로 보존합니다.

## 7. BOM과 utf-8-sig

일부 프로그램이 생성한 UTF-8 파일은 앞에 BOM을 포함할 수 있습니다.

```python
text = Path("input.txt").read_text(encoding="utf-8-sig")
```

`utf-8-sig`는 읽을 때 UTF-8 BOM을 제거합니다.

한글 레거시 파일에서 `cp949`를 만날 수 있지만, UTF-8 실패 후 무조건 재시도하면 손상된 파일을 정상 데이터로 오인할 수 있습니다. 파일을 만든 시스템이나 명시된 메타데이터처럼 신뢰할 근거가 있을 때만 다른 인코딩을 선택합니다.

## 8. 파일 위치: tell과 seek

바이너리 형식은 필요한 값이 파일의 특정 위치에 저장되기도 합니다.

```python
from pathlib import Path

path = Path("sample.bin")

with path.open("rb") as file:
    print(file.tell())
    first_four = file.read(4)
    print(file.tell())

    file.seek(0)
    first_two = file.read(2)
```

- `tell()`: 현재 파일 위치를 반환
- `seek(offset)`: 파일 시작을 기준으로 지정한 위치로 이동
- `read(size)`: 지정한 바이트 수만 읽음

파일 크기 밖으로 이동하거나 헤더가 요구하는 길이보다 짧게 읽은 경우를 반드시 검사합니다.

## 9. 바이트 순서와 int.from_bytes

여러 바이트로 저장된 정수는 바이트 순서에 따라 값이 달라집니다.

```python
raw = b"\x3c\x00\x00\x00"

little_value = int.from_bytes(raw, byteorder="little")
big_value = int.from_bytes(raw, byteorder="big")

print(little_value)  # 60
print(big_value)     # 1006632960
```

- 리틀 엔디언: 낮은 자리 바이트를 먼저 저장
- 빅 엔디언: 높은 자리 바이트를 먼저 저장

파일 형식 문서가 지정한 길이와 바이트 순서를 확인한 뒤 해석합니다. 임의의 오프셋을 검증 없이 `seek()`에 전달하지 않습니다.

## 10. 고정 구조와 struct

여러 숫자 필드를 반복해서 읽을 때는 표준 `struct` 모듈을 사용할 수 있습니다.

```python
import struct

raw = b"\x4d\x5a\x3c\x00\x00\x00"
magic, offset = struct.unpack("<2sI", raw)

print(magic)   # b'MZ'
print(offset)  # 60
```

`<`는 리틀 엔디언, `2s`는 2바이트 문자열, `I`는 4바이트 부호 없는 정수를 뜻합니다. 이 절에서는 형식 문자열을 암기하기보다 파일 구조에 길이와 순서가 명시되어야 한다는 점에 집중합니다.

## 흔한 실수

- `str`과 `bytes`를 직접 결합함
- 인코딩을 추측한 뒤 오류를 무시함
- 바이트 길이를 문자 길이로 해석함
- 바이너리 파일을 텍스트 모드로 읽음
- 디코딩한 값만 보존하고 원본 bytes를 버림
- 파일 크기와 필드 길이를 확인하지 않고 `seek()`함
- 바이트 순서를 확인하지 않고 정수로 변환함

{% hint style="success" %}
## 🧪 종합 실습

1. 한글과 영문 문자열의 문자 수와 UTF-8 바이트 수를 비교합니다.
2. 문자열을 파일에 쓰고 bytes로 다시 읽습니다.
3. 파일 앞 네 바이트를 16진수로 출력합니다.
4. 잘못된 UTF-8 데이터를 디코딩하고 오류 정보를 기록합니다.
5. 4바이트 값을 리틀 엔디언과 빅 엔디언으로 각각 해석합니다.
6. 작은 바이너리 파일에서 `seek()`로 지정 위치의 바이트를 읽습니다.
{% endhint %}

## 완료 기준

- [ ] 인코딩과 디코딩의 방향을 설명할 수 있습니다.
- [ ] 텍스트와 바이너리 파일 처리 방법을 선택할 수 있습니다.
- [ ] 디코딩 오류가 발생했을 때 원본을 보존할 수 있습니다.
- [ ] `tell()`, `seek()`, `read(size)`로 필요한 바이트를 읽을 수 있습니다.
- [ ] 파일 형식에 맞는 바이트 순서를 선택할 수 있습니다.

---

다음 절: [04-5. CSV 읽기·검증·안전한 출력](04-5-csv.md)
