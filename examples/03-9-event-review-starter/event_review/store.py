"""여러 보안 이벤트의 상태와 집계를 관리한다."""

from dataclasses import dataclass, field

from .models import SecurityEvent


@dataclass
class EventStore:
    """이벤트를 등록 순서대로 보관하는 저장소다."""

    _events: list[SecurityEvent] = field(default_factory=list)

    def add(self, event):
        """유효한 고유 이벤트를 저장한다."""
        # 실습 과제 3: 타입과 중복을 확인한 뒤 상태를 변경한다.
        raise NotImplementedError("TODO 3: EventStore.add()를 구현하세요")

    def list_all(self):
        """전체 이벤트를 등록 순서의 튜플로 반환한다."""
        # 실습 과제 3: 호출자가 저장소 상태를 우회 변경하지 못하게 한다.
        raise NotImplementedError("TODO 3: EventStore.list_all()을 구현하세요")

    def find_by_action(self, action):
        """action이 같은 이벤트를 등록 순서의 튜플로 반환한다."""
        # 실습 과제 3: 검색값도 이벤트와 같은 action 규칙으로 검증한다.
        raise NotImplementedError(
            "TODO 3: EventStore.find_by_action()을 구현하세요"
        )

    def remove(self, number):
        """전체 list의 1부터 시작하는 번호로 삭제한 이벤트를 반환한다."""
        # 실습 과제 3: bool을 제외한 정수인지, 목록 범위 안인지 확인한다.
        raise NotImplementedError("TODO 3: EventStore.remove()를 구현하세요")

    def summary(self):
        """total, ALLOW, DENY 건수를 담은 딕셔너리를 반환한다."""
        # 실습 과제 3: 빈 저장소에서도 세 키를 모두 반환한다.
        raise NotImplementedError("TODO 3: EventStore.summary()를 구현하세요")
