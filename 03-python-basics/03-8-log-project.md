# 03-8. 클래스 기초

클래스는 관련된 데이터와 동작을 하나의 개념으로 묶는 방법입니다. 함수와 딕셔너리만으로 표현하기 어려워질 때 사용합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 클래스와 인스턴스의 차이를 설명합니다.
- 속성과 메서드를 정의합니다.
- `__init__`과 `self`의 역할을 이해합니다.
- 단순 데이터에는 `dataclass`를 적용합니다.
{% endhint %}

## 선행 지식

변수, 함수, 자료구조를 이해해야 합니다.

## 1. 클래스와 인스턴스

```python
class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author

    def describe(self):
        return f"{self.title} / {self.author}"

book = Book("Python 기초", "교육팀")
print(book.describe())
```

`Book`은 설계도인 클래스이고 `book`은 실제로 생성된 인스턴스입니다.

## 2. 속성과 메서드

- 속성: 객체가 가진 데이터
- 메서드: 객체가 수행하는 함수
- `self`: 현재 인스턴스 자신

## 3. 상태 변경

```python
class Task:
    def __init__(self, title):
        self.title = title
        self.done = False

    def complete(self):
        self.done = True
```

메서드가 속성을 바꾸면 객체의 상태가 변경됩니다.

## 4. dataclass

```python
from dataclasses import dataclass

@dataclass
class Contact:
    name: str
    email: str
```

데이터 보관이 주목적이라면 `dataclass`가 반복 코드를 줄여줍니다.

{% hint style="success" %}
## 🧪 종합 실습

도서·연락처·작업 중 하나를 클래스로 표현하고 생성, 조회, 상태 변경 메서드를 작성합니다.
{% endhint %}

## 완료 기준

- [ ] 클래스와 인스턴스를 구분할 수 있습니다.
- [ ] 속성과 메서드가 있는 클래스를 작성할 수 있습니다.
- [ ] 클래스가 필요한 상황과 딕셔너리로 충분한 상황을 구분할 수 있습니다.

---

다음 절: [03-9. 문법 종합 실습](03-9-practical-syntax.md)
