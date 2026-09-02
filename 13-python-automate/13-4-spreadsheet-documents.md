# 13-4. 스프레드시트와 문서 자동화

스프레드시트와 문서 자동화의 핵심은 보이는 문자열이 아니라 셀·행·문단·페이지의 구조를 유지하는 것입니다. 원본은 보존하고 검증을 통과한 데이터만 새 출력에 반영합니다.

{% hint style="info" %}
## 🧭 학습 목표

- Excel 셀의 값, 자료형, 서식, 수식을 구분합니다.
- 필수 열·행 검증·요약을 시트로 분리합니다.
- PDF·Word에서 텍스트 추출과 시각적 레이아웃을 구분합니다.
- 손상·암호화·수식·매크로를 실패 조건으로 다룹니다.
{% endhint %}

## 1. 형식별 라이브러리

| 형식 | Python 라이브러리 | 적합한 작업 | 한계 |
| --- | --- | --- | --- |
| `.xlsx` | `openpyxl` | 셀, 서식, 수식, 차트 생성·수정 | Excel 계산 엔진이 아님 |
| `.pdf` | `pypdf` | 메타데이터, 페이지 병합·분할, 텍스트 추출 | 스캔 이미지는 OCR 필요 |
| `.docx` | `python-docx` | 문단, 표, 스타일, 문서 생성 | 레이아웃 재현은 렌더러에 의존 |
| 이미지 | `Pillow` | 크기 변경, 자르기, 포맷 변환, 로고 합성 | 벡터·고급 색상 워크플로우 제약 |

PDF와 Word를 다루는 라이브러리는 동일한 파일이라도 모든 레이아웃과 기능을 보존하지 못할 수 있습니다. 결과를 다시 열고 페이지 또는 시트 단위로 검증합니다.

## 2. Excel 입력 계약

먼저 헤더와 자료형을 정의합니다.

| 열 | 필수 | 자료형 | 검증 예시 |
| --- | --- | --- | --- |
| `date` | 예 | 날짜 | ISO `YYYY-MM-DD` |
| `category` | 예 | 문자열 | 공백 제외 1자 이상 |
| `item` | 예 | 문자열 | 공백 제외 1자 이상 |
| `amount` | 예 | 숫자 | 0 이상, `Decimal` 파싱 |

값을 읽자마자 셀에 쓰지 말고, 먼저 Python 객체로 검증한 후 정상 행과 오류 행을 나눕니다.

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Sale:
    date: date
    category: str
    item: str
    amount: Decimal
```

## 3. Workbook 구조

학습 프로젝트는 다음 세 시트를 사용합니다.

1. `요약`: 정상 건수, 오류 건수, 총액, 분류별 집계
2. `정상 데이터`: 검증을 통과한 입력 행
3. `검증 오류`: 원본 행 번호, 오류 사유, 원본 값

오류 행을 버리지 않으면 수정 후 재실행할 수 있고, 요약 값의 신뢰성을 판단할 수 있습니다.

## 4. `openpyxl`로 자료형 유지

```python
from openpyxl import Workbook

workbook = Workbook()
sheet = workbook.active
sheet.title = "정상 데이터"

sheet.append(["날짜", "분류", "항목", "금액"])
sheet.append([record.date, record.category, record.item, float(record.amount)])

sheet["A2"].number_format = "yyyy-mm-dd"
sheet["D2"].number_format = "#,##0.00"
```

날짜와 숫자를 포맷된 문자열로 쓰지 않고 자료형으로 저장합니다. 화면 표시 방식은 `number_format`으로 분리합니다.

## 5. 수식과 계산 값

`openpyxl`은 수식을 쓸 수 있지만 Excel처럼 수식을 계산하지는 않습니다.

```python
sheet["B2"] = "=SUM('정상 데이터'!D2:D100)"
```

- 자동화 출력을 다른 프로그램이 즉시 읽어야 한다면 Python으로 계산한 요약 값도 별도로 저장합니다.
- 사용자가 Excel에서 입력을 수정할 예정이면 수식을 유지하고 열었을 때 재계산되도록 설계합니다.
- 수식 범위와 요약 값을 실제 입력 합계와 대조합니다.

CSV 셀이 `=`, `+`, `-`, `@`로 시작하는 문자열을 포함하면 스프레드시트 프로그램이 수식으로 해석할 수 있습니다. 외부 입력은 의도된 수식인지 검증하고 텍스트로 강제할 정책을 둡니다.

## 6. PDF 처리

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages[:3]:
    writer.add_page(page)

with open("output.pdf", "wb") as output:
    writer.write(output)
```

확인할 사항:

- 암호화 여부와 열기 실패
- 예상 페이지 수와 실제 페이지 수
- 텍스트 추출 결과와 시각적 렌더링의 차이
- 폼, 서명, 첨부파일, 주석의 보존 여부
- 출력 PDF를 다시 열어 구조와 페이지 수 재검증

스캔된 PDF에서 텍스트가 나오지 않는 것은 파서 오류가 아니라 OCR 단계가 필요한 것일 수 있습니다.

## 7. Word 문서 생성

```python
from docx import Document

document = Document()
document.add_heading("주간 자동화 보고서", level=1)
document.add_paragraph("검증을 통과한 결과만 포함합니다.")

table = document.add_table(rows=1, cols=2)
table.rows[0].cells[0].text = "항목"
table.rows[0].cells[1].text = "값"

document.save("report.docx")
```

스타일 이름을 직접 사용하는 경우 대상 템플릿에 그 스타일이 있는지 확인합니다. 생성 후에는 문단·표 개수 검증과 실제 렌더링 검토를 모두 수행합니다.

## 8. 원본 보존과 안전 저장

```text
입력 원본
→ 읽기·구조 검증
→ 메모리에서 변환
→ 임시 출력에 저장
→ 임시 출력 재검증
→ 최종 경로로 교체
→ 최종 파일 재열기·시각 검토
```

원본을 제자리에서 덮어쓰는 기능은 기본 실습에서 제외합니다.

## 실습

1. CSV 필수 열과 행 검증 규칙을 정의합니다.
2. 정상 5건, 날짜 오류 1건, 금액 오류 1건을 준비합니다.
3. Excel에 요약·정상 데이터·검증 오류 시트를 생성합니다.
4. Excel을 다시 열어 시트 이름, 행 수, 합계를 검증합니다.
5. 수식처럼 보이는 문자열을 입력해 해석 정책을 확인합니다.

## 완료 기준

- [ ] 날짜·숫자를 문자열이 아닌 자료형으로 저장합니다.
- [ ] 오류 행을 버리지 않고 이유와 함께 보존합니다.
- [ ] 원본과 출력 경로를 분리합니다.
- [ ] 출력 파일을 다시 열어 구조와 값을 검증합니다.
- [ ] 텍스트 추출 성공과 레이아웃 보존을 구분합니다.

---

다음: [13-5. 예약·알림·이미지·GUI 자동화](13-5-scheduling-gui.md)
