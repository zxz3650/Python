"""03-9 학습자 구현을 공개 동작만으로 단계별 검증한다."""

import runpy
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch


class CheckFailure(AssertionError):
    """관찰한 공개 동작이 계약과 다를 때 발생한다."""


def require(condition, message):
    """조건이 거짓이면 학습자가 확인할 동작을 설명한다."""
    if not condition:
        raise CheckFailure(message)


def expect_exception(expected_type, function, *args):
    """공개 호출이 계약에 맞는 예외를 발생시키는지 확인한다."""
    try:
        function(*args)
    except NotImplementedError:
        raise
    except expected_type as exc:
        return exc
    except Exception as exc:
        message = (
            f"{function.__name__}()이 {expected_type.__name__} 대신 "
            f"{type(exc).__name__}을 발생시켰습니다"
        )
        raise CheckFailure(message)

    message = (
        f"{function.__name__}()이 {expected_type.__name__}을 "
        "발생시키지 않았습니다"
    )
    raise CheckFailure(message)


def check_parse_port():
    from event_review.models import parse_port

    require(parse_port(1) == 1, "정수 포트 1을 그대로 반환해야 합니다")
    require(
        parse_port("443") == 443,
        "정수 문자열 포트를 정수로 변환해야 합니다",
    )
    require(parse_port(65535) == 65535, "포트 65535를 허용해야 합니다")

    expect_exception(TypeError, parse_port, True)
    expect_exception(TypeError, parse_port, 3.14)
    conversion_error = expect_exception(ValueError, parse_port, "https")
    require(
        "변환" in str(conversion_error),
        "정수 변환에 실패했다는 문맥을 ValueError 메시지에 포함해야 합니다",
    )
    expect_exception(ValueError, parse_port, 0)
    expect_exception(ValueError, parse_port, 65536)


def check_security_event():
    from event_review.models import SecurityEvent

    event = SecurityEvent(" allow ", " 192.0.2.10 ", "443")
    require(
        event.action == "ALLOW",
        "action을 공백 제거 후 대문자로 저장해야 합니다",
    )
    require(event.ip == "192.0.2.10", "IP의 앞뒤 공백을 제거해야 합니다")
    require(event.port == 443, "port를 정수로 저장해야 합니다")
    require(
        event.endpoint() == "192.0.2.10:443",
        "endpoint()는 'IP:PORT' 문자열을 반환해야 합니다",
    )
    require(
        event == SecurityEvent("ALLOW", "192.0.2.10", 443),
        "같은 필드의 SecurityEvent는 값 기준으로 같아야 합니다",
    )

    expect_exception(TypeError, SecurityEvent, 1, "192.0.2.10", 443)
    expect_exception(ValueError, SecurityEvent, "BLOCK", "192.0.2.10", 443)
    expect_exception(TypeError, SecurityEvent, "ALLOW", None, 443)
    expect_exception(ValueError, SecurityEvent, "ALLOW", "   ", 443)
    expect_exception(TypeError, SecurityEvent, "ALLOW", "192.0.2.10", True)
    expect_exception(ValueError, SecurityEvent, "ALLOW", "192.0.2.10", 0)


def check_event_store():
    from event_review.models import SecurityEvent
    from event_review.store import EventStore

    first_store = EventStore()
    second_store = EventStore()
    expect_exception(IndexError, EventStore().remove, 1)
    allow_event = SecurityEvent("ALLOW", "192.0.2.10", 443)
    deny_event = SecurityEvent("DENY", "198.51.100.4", 22)

    require(
        first_store.summary() == {"total": 0, "ALLOW": 0, "DENY": 0},
        "빈 저장소 요약에도 total, ALLOW, DENY가 모두 필요합니다",
    )
    first_store.add(allow_event)
    snapshot = first_store.list_all()
    require(
        isinstance(snapshot, tuple),
        "list_all()은 튜플을 반환해야 합니다",
    )
    require(
        snapshot == (allow_event,),
        "등록된 이벤트를 등록 순서대로 반환해야 합니다",
    )
    require(
        second_store.list_all() == (),
        "EventStore 인스턴스끼리 이벤트 목록을 공유하면 안 됩니다",
    )

    first_store.add(deny_event)
    require(
        snapshot == (allow_event,),
        "반환한 목록 스냅샷이 이후 등록으로 바뀌면 안 됩니다",
    )
    require(
        first_store.find_by_action(" allow ") == (allow_event,),
        "find_by_action()은 공백과 대소문자를 정규화해야 합니다",
    )
    require(
        second_store.find_by_action("deny") == (),
        "일치하는 이벤트가 없으면 빈 튜플을 반환해야 합니다",
    )
    require(
        first_store.summary() == {"total": 2, "ALLOW": 1, "DENY": 1},
        "summary() 집계 결과가 등록 상태와 일치해야 합니다",
    )

    summary_store = EventStore()
    summary_store.add(SecurityEvent("ALLOW", "192.0.2.10", 80))
    summary_store.add(SecurityEvent("ALLOW", "192.0.2.11", 443))
    summary_store.add(SecurityEvent("DENY", "198.51.100.4", 22))
    require(
        summary_store.summary() == {"total": 3, "ALLOW": 2, "DENY": 1},
        "ALLOW 2건과 DENY 1건의 혼합 요약을 정확히 계산해야 합니다",
    )

    expect_exception(TypeError, first_store.add, "not an event")
    same_after_normalization = SecurityEvent(
        " allow ",
        " 192.0.2.10 ",
        "443",
    )
    expect_exception(ValueError, first_store.add, same_after_normalization)
    expect_exception(TypeError, first_store.find_by_action, 1)
    expect_exception(ValueError, first_store.find_by_action, "BLOCK")
    expect_exception(TypeError, first_store.remove, True)
    expect_exception(IndexError, first_store.remove, -1)
    expect_exception(IndexError, first_store.remove, 0)
    expect_exception(IndexError, first_store.remove, 3)

    removed = first_store.remove(2)
    require(
        removed == deny_event,
        "remove()는 삭제한 이벤트를 반환해야 합니다",
    )
    require(
        first_store.list_all() == (allow_event,),
        "remove() 뒤 저장소에서 해당 이벤트가 사라져야 합니다",
    )
    require(
        first_store.summary() == {"total": 1, "ALLOW": 1, "DENY": 0},
        "remove() 뒤 요약도 현재 저장소 상태를 반영해야 합니다",
    )


def check_command_parser():
    from event_review.commands import Command, parse_command

    require(
        parse_command(" ADD allow 192.0.2.10 443 ")
        == Command("add", ("allow", "192.0.2.10", "443")),
        "명령 이름은 소문자, 나머지는 인자 튜플이어야 합니다",
    )
    require(
        parse_command("list") == Command("list"),
        "list 명령을 해석해야 합니다",
    )
    require(
        parse_command("find deny") == Command("find", ("deny",)),
        "find 명령과 인자 한 개를 해석해야 합니다",
    )
    require(
        parse_command("summary") == Command("summary"),
        "summary 명령을 해석해야 합니다",
    )
    require(
        parse_command("remove 2") == Command("remove", ("2",)),
        "remove의 번호를 아직 문자열인 인자로 보관해야 합니다",
    )
    require(
        parse_command("quit") == Command("quit"),
        "quit 명령을 해석해야 합니다",
    )

    expect_exception(TypeError, parse_command, None)
    expect_exception(ValueError, parse_command, "   ")
    expect_exception(ValueError, parse_command, "unknown")
    missing_error = expect_exception(
        ValueError,
        parse_command,
        "add ALLOW 192.0.2.10",
    )
    extra_error = expect_exception(ValueError, parse_command, "summary extra")
    require(
        "인자" in str(missing_error) and "인자" in str(extra_error),
        "인자 부족·초과 오류 메시지에 인자 개수 문맥이 필요합니다",
    )


def check_command_execution():
    from event_review.app import (
        execute_command,
        format_event,
        format_events,
        format_matches,
        format_summary,
    )
    from event_review.commands import Command, parse_command
    from event_review.models import SecurityEvent
    from event_review.store import EventStore

    event = SecurityEvent("ALLOW", "192.0.2.10", 443)
    require(
        format_event(1, event) == "1. ALLOW 192.0.2.10 443",
        "format_event()의 출력 형식을 확인하세요",
    )
    require(
        format_events(()) == ["목록이 비어 있습니다"],
        "빈 이벤트 컬렉션의 안내 문구를 반환해야 합니다",
    )
    require(
        format_events((event,)) == ["1. ALLOW 192.0.2.10 443"],
        "format_events()는 1부터 번호를 붙여야 합니다",
    )
    require(
        format_matches(()) == ["검색 결과가 없습니다"],
        "검색 결과가 없을 때 전용 안내 문구를 반환해야 합니다",
    )
    require(
        format_matches((event,)) == ["ALLOW 192.0.2.10 443"],
        "검색 결과에는 삭제 번호를 붙이지 않아야 합니다",
    )
    require(
        format_summary({"total": 1, "ALLOW": 1, "DENY": 0})
        == "total=1 ALLOW=1 DENY=0",
        "format_summary()의 키 순서와 출력 형식을 확인하세요",
    )

    store = EventStore()
    keep_running, messages = execute_command(
        store,
        parse_command("add allow 192.0.2.10 443"),
    )
    require(keep_running is True, "add 뒤에는 세션을 계속해야 합니다")
    require(
        messages == ["추가: ALLOW 192.0.2.10:443"],
        "add의 반환 메시지를 확인하세요",
    )
    require(
        store.list_all() == (event,),
        "execute_command(add)가 저장소 상태를 변경해야 합니다",
    )

    _, list_messages = execute_command(store, parse_command("list"))
    require(
        list_messages == ["1. ALLOW 192.0.2.10 443"],
        "list는 현재 저장소를 형식화해 반환해야 합니다",
    )
    _, find_messages = execute_command(store, parse_command("find allow"))
    require(
        find_messages == ["ALLOW 192.0.2.10 443"],
        "find는 삭제 번호 없이 검색 결과를 반환해야 합니다",
    )
    _, no_match_messages = execute_command(store, parse_command("find deny"))
    require(
        no_match_messages == ["검색 결과가 없습니다"],
        "find 무결과 메시지를 확인하세요",
    )
    _, summary_messages = execute_command(store, parse_command("summary"))
    require(
        summary_messages == ["total=1 ALLOW=1 DENY=0"],
        "summary는 집계 한 줄을 메시지 목록으로 반환해야 합니다",
    )

    keep_running, quit_messages = execute_command(store, Command("quit"))
    require(
        keep_running is False,
        "quit은 계속 여부를 False로 반환해야 합니다",
    )
    require(
        quit_messages == ["종료합니다"],
        "quit 종료 메시지를 확인하세요",
    )

    expect_exception(TypeError, execute_command, object(), Command("list"))
    expect_exception(TypeError, execute_command, store, object())
    expect_exception(RuntimeError, execute_command, store, Command("unsupported"))
    remove_conversion_error = expect_exception(
        ValueError,
        execute_command,
        store,
        parse_command("remove abc"),
    )
    require(
        "삭제 번호" in str(remove_conversion_error),
        "remove 변환 오류 메시지에 삭제 번호 문맥이 필요합니다",
    )

    execute_command(store, parse_command("add DENY 198.51.100.4 22"))
    _, numbered_list = execute_command(store, parse_command("list"))
    require(
        numbered_list[-1] == "2. DENY 198.51.100.4 22",
        "list 번호는 전체 저장소 순서를 나타내야 합니다",
    )
    _, remove_messages = execute_command(store, parse_command("remove 2"))
    require(
        remove_messages == ["삭제: DENY 198.51.100.4:22"],
        "remove는 전체 list 번호의 이벤트를 삭제해야 합니다",
    )
    require(
        store.list_all() == (event,),
        "remove 뒤 전체 목록의 나머지 상태를 확인하세요",
    )
    _, renumbered_list = execute_command(store, parse_command("list"))
    require(
        renumbered_list == ["1. ALLOW 192.0.2.10 443"],
        "remove 뒤 list 번호는 다시 1부터 이어져야 합니다",
    )

    numbering_store = EventStore()
    execute_command(
        numbering_store,
        parse_command("add ALLOW 192.0.2.10 80"),
    )
    execute_command(
        numbering_store,
        parse_command("add DENY 198.51.100.4 22"),
    )
    execute_command(
        numbering_store,
        parse_command("add ALLOW 192.0.2.11 443"),
    )
    execute_command(numbering_store, parse_command("remove 2"))
    _, three_event_list = execute_command(
        numbering_store,
        parse_command("list"),
    )
    require(
        three_event_list == [
            "1. ALLOW 192.0.2.10 80",
            "2. ALLOW 192.0.2.11 443",
        ],
        "세 이벤트 중 2번을 삭제하면 남은 번호가 1부터 이어져야 합니다",
    )

    regression_store = EventStore()
    execute_command(
        regression_store,
        parse_command("add DENY 198.51.100.4 22"),
    )
    execute_command(
        regression_store,
        parse_command("add ALLOW 192.0.2.10 443"),
    )
    _, regression_matches = execute_command(
        regression_store,
        parse_command("find allow"),
    )
    require(
        regression_matches == ["ALLOW 192.0.2.10 443"],
        "find 결과에는 전체 목록 번호처럼 보이는 번호가 없어야 합니다",
    )
    _, regression_removed = execute_command(
        regression_store,
        parse_command("remove 1"),
    )
    require(
        regression_removed == ["삭제: DENY 198.51.100.4:22"],
        "remove 1은 find가 아닌 전체 list의 첫 이벤트를 삭제해야 합니다",
    )
    require(
        regression_store.list_all() == (event,),
        "삭제 뒤 ALLOW 이벤트만 남아야 합니다",
    )


def check_session():
    from event_review.app import process_input, run_session
    from event_review.store import EventStore

    direct_store = EventStore()
    keep_running, messages = process_input(
        direct_store,
        "add ALLOW 192.0.2.10 443",
    )
    require(
        keep_running is True,
        "process_input(add)는 세션을 계속해야 합니다",
    )
    require(
        messages == ["추가: ALLOW 192.0.2.10:443"],
        "process_input()은 파싱과 실행 결과를 연결해야 합니다",
    )

    _, recovery_outputs = run_session(["   ", "summary", "quit"])
    require(
        recovery_outputs[0].startswith("오류:")
        and recovery_outputs[1] == "total=0 ALLOW=0 DENY=0"
        and recovery_outputs[-1] == "종료합니다",
        "빈 명령 오류 뒤에도 summary와 quit을 계속 처리해야 합니다",
    )

    commands = [
        "add ALLOW 192.0.2.10 443",
        "add ALLOW 192.0.2.10 443",
        "add BLOCK 203.0.113.8 80",
        "add ALLOW 203.0.113.8 https",
        "unknown",
        "add DENY 198.51.100.4 22",
        "find allow",
        "summary",
        "list",
        "remove 2",
        "summary",
        "quit",
        "add DENY 203.0.113.9 53",
    ]
    supplied_store = EventStore()
    returned_store, outputs = run_session(commands, supplied_store)

    require(
        returned_store is supplied_store,
        "전달한 store 인스턴스를 그대로 사용해야 합니다",
    )
    require(
        returned_store.summary() == {"total": 1, "ALLOW": 1, "DENY": 0},
        "오류 뒤에는 계속하고 quit 뒤에는 멈춰야 합니다",
    )
    error_count = 0
    for output in outputs:
        if output.startswith("오류:"):
            error_count += 1
    require(
        error_count == 4,
        "네 입력 오류를 각각 '오류:' 메시지로 남겨야 합니다",
    )
    require(
        "total=2 ALLOW=1 DENY=1" in outputs,
        "세션 출력에 현재 상태의 요약이 포함되어야 합니다",
    )
    require(
        "ALLOW 192.0.2.10 443" in outputs
        and "2. DENY 198.51.100.4 22" in outputs
        and "삭제: DENY 198.51.100.4:22" in outputs
        and "total=1 ALLOW=1 DENY=0" in outputs,
        "통합 세션에서 검색·목록·삭제·삭제 후 요약을 확인해야 합니다",
    )
    require(
        outputs[-1] == "종료합니다",
        "quit에서 세션 출력을 끝내야 합니다",
    )
    post_quit_output_found = False
    for output in outputs:
        if "203.0.113.9" in output:
            post_quit_output_found = True
    require(
        not post_quit_output_found,
        "quit 뒤 입력의 출력이 생기면 안 됩니다",
    )
    expect_exception(TypeError, run_session, [None])


def check_main_and_package():
    import event_review
    from event_review.app import main

    expected_exports = {
        "EventStore",
        "SecurityEvent",
        "process_input",
        "run_session",
    }
    require(
        hasattr(event_review, "__all__"),
        "event_review.__init__.py에 __all__을 지정해야 합니다",
    )
    require(
        set(event_review.__all__) == expected_exports,
        "event_review.__all__에 공개 API 네 이름을 지정해야 합니다",
    )
    missing_exports = []
    for name in expected_exports:
        if not hasattr(event_review, name):
            missing_exports.append(name)
    require(
        not missing_exports,
        "__all__의 이름을 패키지에서 가져올 수 있어야 합니다",
    )

    imported = subprocess.run(
        [sys.executable, "-c", "import event_review"],
        check=False,
        capture_output=True,
        cwd=Path(__file__).resolve().parent,
        text=True,
        timeout=5,
    )
    require(
        imported.returncode == 0,
        "event_review 패키지를 오류 없이 import할 수 있어야 합니다",
    )
    require(
        imported.stdout == "" and imported.stderr == "",
        "패키지 import만으로 입력·출력이 발생하면 안 됩니다",
    )

    with patch(
        "builtins.input",
        side_effect=["add ALLOW 192.0.2.10 443", "summary", "quit"],
    ) as fake_input, patch("builtins.print") as fake_print:
        exit_code = main()

    require(exit_code == 0, "main()은 정상 종료 코드 0을 반환해야 합니다")
    require(fake_input.call_count == 3, "main()은 quit까지 세 번 입력해야 합니다")
    printed = []
    for call in fake_print.call_args_list:
        printed.append(call.args[0])
    require(
        printed[0] == "명령: add/list/find/summary/remove/quit",
        "main() 시작 안내 문구를 확인하세요",
    )
    require(
        "추가: ALLOW 192.0.2.10:443" in printed,
        "print()로 add 결과를 전달해야 합니다",
    )
    require(
        "total=1 ALLOW=1 DENY=0" in printed,
        "print()로 summary 결과를 전달해야 합니다",
    )
    require(
        printed[-1] == "종료합니다",
        "마지막 출력은 종료 메시지여야 합니다",
    )

    with patch("builtins.input", side_effect=["quit"]) as module_input, patch(
        "builtins.print"
    ) as module_print:
        try:
            runpy.run_module("event_review", run_name="__main__")
        except SystemExit as exc:
            require(
                exc.code == 0,
                "python -m 진입점은 main()의 종료 코드 0으로 끝나야 합니다",
            )
        else:
            raise CheckFailure(
                "event_review.__main__.py가 main()의 종료 코드를 전달해야 합니다"
            )

    require(
        module_input.call_count == 1,
        "python -m 진입점은 app.main()을 호출해 quit 입력을 처리해야 합니다",
    )
    module_messages = []
    for call in module_print.call_args_list:
        module_messages.append(call.args[0])
    require(
        module_messages[-1] == "종료합니다",
        "python -m 진입점의 마지막 출력은 종료 메시지여야 합니다",
    )


@dataclass
class Stage:
    title: str
    next_step: str
    check: object


STAGES = (
    Stage(
        "1/7 포트 변환",
        "event_review/models.py의 parse_port()를 먼저 구현하세요.",
        check_parse_port,
    ),
    Stage(
        "2/7 이벤트 데이터클래스",
        "event_review/models.py의 SecurityEvent와 endpoint()를 구현하세요.",
        check_security_event,
    ),
    Stage(
        "3/7 이벤트 저장소",
        "event_review/store.py의 EventStore 공개 메서드를 구현하세요.",
        check_event_store,
    ),
    Stage(
        "4/7 명령 파싱",
        "event_review/commands.py의 parse_command()를 구현하세요.",
        check_command_parser,
    ),
    Stage(
        "5/7 출력과 명령 실행",
        "event_review/app.py의 format_*()와 execute_command()를 구현하세요.",
        check_command_execution,
    ),
    Stage(
        "6/7 세션 처리",
        "event_review/app.py의 process_input()과 run_session()을 구현하세요.",
        check_session,
    ),
    Stage(
        "7/7 터미널 연결과 공개 API",
        "main(), __init__.py 공개 API, __main__.py 진입점을 확인하세요.",
        check_main_and_package,
    ),
)


def run():
    """첫 실패에서 멈추는 단계별 검증을 수행한다."""
    print("03-9 이벤트 검토 프로그램 공개 동작 검증")
    print("-" * 46)

    for stage in STAGES:
        print(f"[{stage.title}] 검사 중")
        try:
            stage.check()
        except NotImplementedError as exc:
            print(f"실패: 아직 구현되지 않은 동작입니다 ({exc})")
            print(f"다음 구현 단계: {stage.next_step}")
            return 1
        except CheckFailure as exc:
            print(f"실패: {exc}")
            print(f"다음 구현 단계: {stage.next_step}")
            return 1
        except Exception as exc:
            print(
                "실패: 검사 중 예상하지 못한 "
                f"{type(exc).__name__}이 발생했습니다: {exc}"
            )
            print(f"다음 구현 단계: {stage.next_step}")
            return 1
        else:
            print("통과")

    print("-" * 46)
    print("모든 공개 동작 검증을 통과했습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
