# 03-9. 문법 종합 실습

03장에서 학습한 문법을 하나의 메모리 기반 프로그램으로 연결합니다. 파일 저장, 네트워크 통신, 보안 분석은 이후 장에서 다룹니다.

{% hint style="info" %}
## 🧭 실습 목표

- 리스트와 딕셔너리로 데이터를 표현합니다.
- 조건문과 반복문으로 검색·분류합니다.
- 기능을 함수와 모듈로 분리합니다.
- 잘못된 입력을 예외로 처리합니다.
{% endhint %}

## 선행 지식

03-1부터 03-8까지의 내용을 완료해야 합니다.

## 1. 프로젝트 선택

다음 중 하나를 선택합니다.

- 연락처 관리
- 도서 목록 관리
- 작업 목록 관리
- 간단한 재고 관리

## 2. 필수 기능

1. 항목 추가
2. 전체 목록 조회
3. 조건 검색
4. 항목 수정
5. 입력값 검증
6. 메뉴 반복과 종료
7. 기능별 함수 분리

## 3. 시작 구조

```python
items = []

def add_item(items, item):
    items.append(item)

def find_items(items, keyword):
    results = []
    for item in items:
        if keyword.lower() in item["name"].lower():
            results.append(item)
    return results

def main():
    while True:
        command = input("add/list/find/quit: ").strip().lower()

        if command == "quit":
            break
        if command not in {"add", "list", "find"}:
            print("지원하지 않는 명령입니다")
            continue

        # 선택한 프로젝트에 맞게 기능을 완성합니다.

if __name__ == "__main__":
    main()
```

## 4. 오류 사례

- 필수값이 비어 있음
- 숫자 필드에 문자가 입력됨
- 존재하지 않는 항목을 수정함
- 지원하지 않는 명령이 입력됨

오류를 무시하지 않고 사용자에게 원인을 설명합니다.

## 5. 확장 과제

- 딕셔너리 대신 클래스로 항목 표현
- 정렬 기능
- 중복 항목 방지
- 모듈 분리
- 타입 힌트와 docstring 추가

{% hint style="success" %}
## 🧪 최종 점검

정상 입력, 잘못된 입력, 빈 목록, 중복 데이터, 종료 명령을 각각 실행하고 예상 결과와 비교합니다.
{% endhint %}

## 완료 기준

- [ ] 프로그램이 종료 전까지 반복 실행됩니다.
- [ ] 자료구조와 함수의 역할을 설명할 수 있습니다.
- [ ] 잘못된 입력으로 프로그램이 비정상 종료되지 않습니다.
- [ ] 기능이 두 개 이상의 모듈로 분리되어 있습니다.

---

다음 장: [04. 파일 입출력과 데이터 형식](../04-file-io.md)
