"""이벤트 한 건의 정규화와 검증을 담당한다."""

from dataclasses import dataclass


def parse_port(value):
    """정수 또는 정수 문자열을 1~65535 범위의 정수로 변환한다."""
    # 실습 과제 1: bool을 제외한 타입, 정수 변환, 범위를 검증한다.
    raise NotImplementedError("TODO 1: parse_port()를 구현하세요")


@dataclass
class SecurityEvent:
    """정규화되고 검증된 보안 이벤트 한 건을 나타낸다."""

    action: str
    ip: str
    port: int

    def __post_init__(self):
        """필드를 정규화하고 유효하지 않은 이벤트 생성을 막는다."""
        # 실습 과제 2: action, ip, port를 공개 동작 계약에 맞게 저장한다.
        raise NotImplementedError("TODO 2: SecurityEvent 검증을 구현하세요")

    def endpoint(self):
        """``IP:PORT`` 형식의 문자열을 반환한다."""
        # 실습 과제 2: 정규화된 ip와 port로 접속 지점을 표현한다.
        raise NotImplementedError("TODO 2: endpoint()를 구현하세요")
