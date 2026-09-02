"""명령 실행, 세션 처리, 터미널 입출력을 연결한다."""

from .commands import Command, parse_command
from .models import SecurityEvent
from .store import EventStore


def format_event(number, event):
    """이벤트를 ``번호. ACTION IP PORT`` 형식으로 만든다."""
    # 실습 과제 5: 공개 출력 형식을 구현한다.
    raise NotImplementedError("TODO 5: format_event()를 구현하세요")


def format_events(events):
    """전체 목록에 1부터 시작하는 삭제 번호를 붙인다."""
    # 실습 과제 5: 빈 목록 메시지와 전체 목록 번호를 처리한다.
    raise NotImplementedError("TODO 5: format_events()를 구현하세요")


def format_matches(events):
    """검색 결과를 삭제 번호가 없는 문자열 목록으로 만든다."""
    # 실습 과제 5: 무결과 메시지와 번호 없는 이벤트 형식을 처리한다.
    raise NotImplementedError("TODO 5: format_matches()를 구현하세요")


def format_summary(summary):
    """집계 딕셔너리를 한 줄 문자열로 만든다."""
    # 실습 과제 5: total, ALLOW, DENY를 정해진 순서로 표현한다.
    raise NotImplementedError("TODO 5: format_summary()를 구현하세요")


def execute_command(store, command):
    """명령을 실행하고 ``(계속 여부, 메시지 목록)``을 반환한다."""
    # 실습 과제 5: 여섯 명령을 저장소 동작과 연결한다. 직접 출력하지 않는다.
    raise NotImplementedError("TODO 5: execute_command()를 구현하세요")


def process_input(store, text):
    """원문 한 줄을 파싱하고 실행한다."""
    # 실습 과제 6: parse_command()와 execute_command()를 연결한다.
    raise NotImplementedError("TODO 6: process_input()을 구현하세요")


def run_session(commands, store=None):
    """여러 명령을 처리하고 ``(저장소, 전체 출력)``을 반환한다."""
    # 실습 과제 6: ValueError/IndexError 뒤에는 계속하고 quit 뒤에는 멈춘다.
    # TypeError 같은 프로그래밍 오류는 이 경계에서 숨기지 않는다.
    raise NotImplementedError("TODO 6: run_session()을 구현하세요")


def main():
    """내장 input()과 print()로 터미널 세션을 실행한다."""
    # 실습 과제 7: 안내, 프롬프트, 오류 복구, 정상 종료를 연결한다.
    raise NotImplementedError("TODO 7: main()을 구현하세요")
