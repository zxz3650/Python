"""사용자가 입력한 문자열 명령을 구조화한다."""

from dataclasses import dataclass


@dataclass
class Command:
    """명령 이름과 인자 튜플을 보관한다."""

    name: str
    arguments: tuple[str, ...] = ()


def parse_command(text):
    """원문 문자열을 검증된 ``Command``로 변환한다."""
    # 실습 과제 4: 타입, 빈 입력, 이름, 명령별 인자 개수를 검증한다.
    # 지원 명령과 인자 수: add 3, list 0, find 1, summary 0,
    # 이어서 remove 1, quit 0이다.
    raise NotImplementedError("TODO 4: parse_command()를 구현하세요")
