# 04-3. 인코딩, str, bytes

컴퓨터는 문자를 직접 저장하지 않고 숫자로 표현된 바이트를 저장합니다. 인코딩은 문자와 바이트 사이의 변환 규칙입니다.

{% hint style="info" %}
## 🧭 학습 목표

- `str`과 `bytes`의 차이를 설명합니다.
- UTF-8로 인코딩하고 디코딩합니다.
- 텍스트 모드와 바이너리 모드를 구분합니다.
- 디코딩 오류의 원인과 처리 방식을 이해합니다.
{% endhint %}

## 선행 지식

기본 자료형과 04-2의 텍스트 파일 처리를 이해해야 합니다.

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

## 흔한 실수

- `str`과 `bytes`를 직접 결합함
- 인코딩을 추측한 뒤 오류를 무시함
- 바이트 길이를 문자 길이로 해석함
- 바이너리 파일을 텍스트 모드로 읽음
- 디코딩한 값만 보존하고 원본 bytes를 버림

{% hint style="success" %}
## 🧪 종합 실습

1. 한글과 영문 문자열의 문자 수와 UTF-8 바이트 수를 비교합니다.
2. 문자열을 파일에 쓰고 bytes로 다시 읽습니다.
3. 파일 앞 네 바이트를 16진수로 출력합니다.
4. 잘못된 UTF-8 데이터를 디코딩하고 오류 정보를 기록합니다.
{% endhint %}

## 완료 기준

- [ ] 인코딩과 디코딩의 방향을 설명할 수 있습니다.
- [ ] 텍스트와 바이너리 파일 처리 방법을 선택할 수 있습니다.
- [ ] 디코딩 오류가 발생했을 때 원본을 보존할 수 있습니다.

---

다음 절: [04-4. CSV 읽기와 쓰기](04-4-csv.md)
