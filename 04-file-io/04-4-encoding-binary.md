# 04-4. 인코딩·bytes와 바이너리 구조

컴퓨터는 텍스트를 저장할 때 문자를 정해진 규칙에 따라 바이트로 바꾼다. **인코딩(encoding)**은 `str`을 `bytes`로 변환하는 과정이고, **디코딩(decoding)**은 `bytes`를 `str`로 해석하는 과정이다.

바이너리 파일은 바이트의 위치·길이·순서 자체가 의미를 가진다. 따라서 내용을 읽는 것만으로 끝내지 않고 형식이 요구하는 길이, 식별자, 바이트 순서와 오프셋을 함께 검증해야 한다.

{% hint style="info" %}
### 🧭 학습 목표

- `str`과 `bytes`의 차이를 설명한다.
- UTF-8로 문자열을 인코딩하고 바이트를 디코딩한다.
- 텍스트 모드와 바이너리 모드를 목적에 맞게 선택한다.
- 디코딩 오류가 발생했을 때 원본 보존과 처리 정책을 선택한다.
- `tell()`, `seek()`, `read(size)`로 필요한 바이트를 읽는다.
- 바이트 순서와 `struct` 형식에 따라 숫자 필드를 해석한다.
- 파일 크기·필드 길이·식별자·오프셋을 검증한다.
{% endhint %}

## 선행 지식

기본 자료형과 [04-3. 텍스트 파일](04-3-text-files.md)의 파일 모드·인코딩 개념을 이해해야 한다.

전용 실습은 [`notebooks/04-4-encoding-binary.ipynb`](../notebooks/04-4-encoding-binary.ipynb)에서 진행할 수 있다.

## 0. 학습 전 확인

다음 코드의 출력 결과를 예상한다.

```python
text = "가"
raw = text.encode("utf-8")

print(type(text), len(text))
print(type(raw), len(raw))
print(raw[0])
print(raw[:1])
```

다음 질문에 답해 본다.

1. 인코딩과 디코딩은 각각 어느 방향의 변환인가?
2. `len("가")`와 `len("가".encode("utf-8"))`는 왜 다른가?
3. 바이너리 파일에서 `read(4)`가 항상 4바이트를 반환하는가?
4. 같은 네 바이트를 리틀 엔디언과 빅 엔디언으로 해석하면 왜 값이 달라지는가?

절의 마지막에서 같은 질문에 다시 답한다.

## 1. str과 bytes

Python의 `str`은 유니코드 문자열이고, `bytes`는 0부터 255까지의 정숫값으로 이루어진 불변 바이트 시퀀스다.

```python
text = "Python 한글"
raw = text.encode("utf-8")

print(type(text))  # <class 'str'>
print(type(raw))   # <class 'bytes'>
print(raw)
```

같은 인코딩 규칙으로 디코딩하면 원래 문자열을 복원할 수 있다.

```python
restored = raw.decode("utf-8")

print(restored)
print(restored == text)  # True
```

```text
str --encode("utf-8")--> bytes
str <--decode("utf-8")-- bytes
```

문자열과 바이트를 `+`로 직접 결합할 수는 없다. 처리 경계에서 어느 자료형을 사용할지 정하고 명시적으로 변환한다.

바이트 리터럴에는 ASCII 문자만 직접 적을 수 있다. 한글처럼 비ASCII 문자를 `b"한글"` 형태로 작성하지 않고 문자열을 필요한 인코딩으로 변환한다.

```python
korean_bytes = "한글".encode("utf-8")
print(korean_bytes)
```

## 2. 문자 수와 바이트 수

문자 수와 저장 바이트 수는 같지 않을 수 있다. 바이트 수는 선택한 인코딩과 문자에 따라 달라진다.

```python
for text in ["A", "가", "😊"]:
    raw = text.encode("utf-8")
    print(repr(text), len(text), len(raw), raw.hex())
```

`len(text)`는 Python 문자열의 코드 포인트 수를 세고, `len(raw)`는 바이트 수를 센다. 화면에서 한 글자로 보이는 조합 문자는 여러 코드 포인트일 수도 있으므로 `len(str)`을 항상 사용자가 보는 글자 수라고 단정하지 않는다.

## 3. 텍스트 모드와 바이너리 모드

텍스트 모드는 바이트와 문자열 사이의 인코딩·디코딩과 줄바꿈 변환을 처리한다. 바이너리 모드는 파일의 바이트를 변환하지 않고 그대로 읽고 쓴다.

```python
from pathlib import Path

lab_dir = Path("file-lab/binary").resolve()
lab_dir.mkdir(parents=True, exist_ok=True)

text_path = lab_dir / "hello.txt"
binary_path = lab_dir / "sample.bin"

text_path.write_text("안녕하세요", encoding="utf-8")
text = text_path.read_text(encoding="utf-8")

binary_path.write_bytes(b"\x4d\x5a\x90\x00")
raw = binary_path.read_bytes()

print(type(text), text)
print(type(raw), raw.hex())
```

텍스트의 의미를 다루면 텍스트 모드를, 파일 헤더·이미지·압축 파일처럼 원본 바이트가 중요하면 바이너리 모드를 선택한다. 바이너리 데이터를 임의로 디코딩해 텍스트처럼 처리하지 않는다.

## 4. bytes 조회·슬라이싱과 bytearray

`bytes`를 인덱싱하면 한 바이트의 정숫값이 나오고, 슬라이싱하면 새로운 `bytes`가 나온다.

```python
header = b"MZ\x90\x00"

print(header[0])      # 77
print(header[:2])     # b'MZ'
print(header.hex())   # 4d5a9000
```

`bytes`는 불변 객체다. 바이트를 제자리에서 수정해야 하면 가변 객체인 `bytearray`를 사용한다.

```python
data = bytearray(b"ABC")
data[0] = 90

print(data)         # bytearray(b'ZBC')
print(bytes(data))  # b'ZBC'
```

`bytearray`도 인덱스에 0부터 255 사이의 정수만 대입할 수 있다.

## 5. 디코딩 오류와 손실 정책

바이트가 지정한 인코딩 규칙에 맞지 않으면 `UnicodeDecodeError`가 발생한다.

```python
invalid = b"\xff\xfe"

try:
    text = invalid.decode("utf-8")
except UnicodeDecodeError as exc:
    print("UTF-8 디코딩 실패:", exc)
```

반대로 선택한 인코딩이 특정 문자를 표현할 수 없으면 `UnicodeEncodeError`가 발생한다.

```python
try:
    "😊".encode("cp949")
except UnicodeEncodeError as exc:
    print("CP949 인코딩 실패:", exc)
```

오류를 무시하기 전에 파일을 만든 시스템, 프로토콜 문서, 명시된 메타데이터로 실제 인코딩을 확인한다. 바이트 내용만 보고 인코딩을 항상 확정할 수는 없다.

```python
display_text = invalid.decode("utf-8", errors="replace")
print(display_text)
```

`errors="replace"`는 해석할 수 없는 부분을 대체 문자 `�`로 바꾸므로 원본 정보가 손실된다. 화면 미리보기처럼 손실을 허용하는 목적에만 사용하고, 조사·재처리가 필요하면 원본 `bytes`를 별도로 보존한다. `errors="ignore"`는 데이터가 사라진 사실조차 눈에 띄지 않을 수 있으므로 검증 용도로 사용하지 않는다.

### BOM과 utf-8-sig

일부 프로그램이 만든 UTF-8 텍스트는 파일 앞에 BOM을 포함한다. 입력 계약이 BOM을 허용한다면 `utf-8-sig`로 읽을 수 있다.

```python
from pathlib import Path

bom_path = lab_dir / "input-with-bom.txt"
bom_path.write_text("BOM이 있는 UTF-8", encoding="utf-8-sig")
text = bom_path.read_text(encoding="utf-8-sig")

print(text)
```

`utf-8-sig`는 읽을 때 UTF-8 BOM을 제거한다. 한글 레거시 파일에서 `cp949`를 만날 수 있지만 UTF-8 디코딩이 실패했다는 이유만으로 무조건 `cp949`로 다시 읽지 않는다. 신뢰할 수 있는 생성 환경이나 형식 명세가 있을 때만 다른 인코딩을 선택한다.

## 6. 파일 위치: tell·seek·read

바이너리 형식은 특정 위치에 헤더와 필드를 저장하기도 한다.

```python
from pathlib import Path

path = lab_dir / "sample.bin"

with path.open("rb") as file:
    print(file.tell())     # 0
    first_four = file.read(4)
    print(file.tell())     # 4

    file.seek(0)
    first_two = file.read(2)

print(first_four.hex())
print(first_two)
```

- `tell()`은 현재 파일 위치를 반환한다.
- `seek(offset)`은 기본적으로 파일 시작에서 `offset`바이트 떨어진 위치로 이동한다.
- `read(size)`는 현재 위치에서 **최대** `size`바이트를 읽는다.

파일 끝에 도달하면 `read(size)`는 요청보다 짧은 `bytes`를 반환할 수 있다. 고정 길이 필드는 길이를 명시적으로 검사한다.

```python
def read_exact(file, size):
    if size < 0:
        raise ValueError("읽기 크기는 0 이상이어야 합니다")

    data = file.read(size)
    if len(data) != size:
        raise ValueError(
            f"필드 길이 부족: 필요={size}, 실제={len(data)}"
        )
    return data
```

`seek(offset, whence)`의 `whence`에 `0`, `1`, `2`를 지정하면 각각 파일 시작, 현재 위치, 파일 끝을 기준으로 이동한다. 임의 입력을 오프셋으로 사용할 때는 음수 여부와 파일 크기 범위를 먼저 검증한다.

## 7. 바이트 순서와 정수 변환

여러 바이트로 저장된 정수는 바이트 순서에 따라 값이 달라진다.

```python
raw = b"\x3c\x00\x00\x00"

little_value = int.from_bytes(
    raw,
    byteorder="little",
    signed=False,
)
big_value = int.from_bytes(
    raw,
    byteorder="big",
    signed=False,
)

print(little_value)  # 60
print(big_value)     # 1006632960
print(little_value.to_bytes(4, byteorder="little"))
```

- 리틀 엔디언은 낮은 자리 바이트를 먼저 저장한다.
- 빅 엔디언은 높은 자리 바이트를 먼저 저장한다.
- `signed`는 최상위 비트를 부호로 해석할지 정한다.

파일 형식이나 프로토콜 명세가 지정한 길이·바이트 순서·부호 여부를 확인한 뒤 해석한다.

## 8. 고정 구조와 struct

여러 필드를 같은 형식으로 묶어 읽고 쓸 때는 표준 `struct` 모듈을 사용한다. 다음은 `LB` 식별자와 리틀 엔디언 4바이트 길이 필드를 가진 학습용 헤더다.

```python
import struct

HEADER = struct.Struct("<2sI")
raw = HEADER.pack(b"LB", 60)

print(HEADER.size)  # 6

magic, payload_length = HEADER.unpack(raw)
print(magic)           # b'LB'
print(payload_length)  # 60
```

- `<`는 리틀 엔디언과 표준 크기를 지정한다.
- `2s`는 길이가 2인 바이트 문자열을 뜻한다.
- `I`는 4바이트 부호 없는 정수를 뜻한다.

`unpack()`에 전달하는 바이트 길이는 형식 크기와 정확히 같아야 한다. `struct.Struct`의 `size` 또는 `struct.calcsize()`로 필요한 길이를 구하고, 파일 형식에서는 `@`가 만드는 실행 환경 의존 네이티브 정렬보다 `<`, `>`, `!`처럼 명시적인 형식을 사용한다.

## 9. 바이너리 헤더 안전하게 검증하기

식별자와 선언된 길이를 검증하지 않은 채 이후 위치를 읽으면 정상 파일을 잘못 해석하거나 과도한 자원을 사용할 수 있다. 다음 학습용 형식은 헤더 뒤에 페이로드(payload) 하나가 이어진다고 가정한다.

```python
import struct
from pathlib import Path

HEADER = struct.Struct("<2sI")
MAX_PAYLOAD_SIZE = 1024


def read_learning_packet(path):
    with path.open("rb") as file:
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        header = read_exact(file, HEADER.size)
        magic, payload_length = HEADER.unpack(header)

        if magic != b"LB":
            raise ValueError("알 수 없는 파일 식별자입니다")
        if payload_length > MAX_PAYLOAD_SIZE:
            raise ValueError("허용된 페이로드 크기를 초과했습니다")
        if HEADER.size + payload_length != file_size:
            raise ValueError("선언된 길이와 실제 파일 크기가 다릅니다")

        payload = read_exact(file, payload_length)

    return payload


packet_path = lab_dir / "packet.bin"
payload = "안전한 바이트".encode("utf-8")
packet_path.write_bytes(HEADER.pack(b"LB", len(payload)) + payload)

loaded = read_learning_packet(packet_path)
print(loaded.decode("utf-8"))
```

이 예제는 같은 파일 객체에서 실제 크기를 구하고 식별자, 상한, 선언 길이를 확인한 뒤 페이로드를 읽는다. 실제 형식에서는 체크섬, 버전, 필드별 범위 같은 명세도 추가로 검증한다.

## 흔한 실수

- 인코딩과 디코딩의 방향을 반대로 설명한다.
- `str`과 `bytes`를 직접 결합한다.
- 문자 수를 저장 바이트 수로 해석한다.
- 바이너리 파일을 텍스트 모드로 읽는다.
- 인코딩을 근거 없이 추측하거나 디코딩 오류를 무조건 무시한다.
- 손실 변환한 문자열만 남기고 원본 바이트를 버린다.
- `read(size)`가 항상 요청한 길이를 반환한다고 가정한다.
- 파일 크기·식별자·필드 길이를 확인하지 않고 `seek()`하거나 `unpack()`한다.
- 바이트 순서와 부호 여부를 확인하지 않고 숫자로 변환한다.
- 파일이 선언한 크기를 상한 없이 메모리에 할당하거나 읽는다.

{% hint style="success" %}
### 🧪 종합 실습: 학습용 바이너리 패킷

1. 식별자 2바이트, 페이로드 길이 4바이트, UTF-8 페이로드로 구성된 파일을 만든다.
2. `struct.Struct("<2sI")`로 헤더를 작성하고 읽는다.
3. 식별자, 최대 페이로드 크기, 선언 길이와 실제 파일 크기를 검증한다.
4. `read_exact()`로 페이로드를 읽고 UTF-8로 디코딩한다.
5. 잘못된 식별자, 잘린 헤더, 과도한 길이, 잘못된 UTF-8 파일을 각각 만들어 오류를 확인한다.
6. 디코딩 실패 시 원본 파일은 변경하지 않고 오류 원인만 기록한다.
{% endhint %}

## 완료 기준

- [ ] 인코딩과 디코딩의 방향을 설명할 수 있다.
- [ ] 텍스트와 바이너리 파일 처리 방법을 목적에 맞게 선택할 수 있다.
- [ ] 문자 수, 바이트 수, 화면에 보이는 글자 수가 항상 같지 않음을 설명할 수 있다.
- [ ] 디코딩 오류가 발생했을 때 원본을 보존하고 손실 정책을 선택할 수 있다.
- [ ] `tell()`, `seek()`, `read(size)`로 필요한 바이트를 읽고 짧은 읽기를 검사할 수 있다.
- [ ] 파일 형식에 맞는 바이트 순서·부호·구조 크기를 선택할 수 있다.
- [ ] 식별자·길이·파일 크기·상한을 검증한 뒤 페이로드를 처리할 수 있다.

---

다음 절: [04-5. CSV 읽기·검증·안전한 출력](04-5-csv.md)
