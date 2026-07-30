"""Tests for the spawn-safe pipe echo session."""

from __future__ import annotations

import multiprocessing
import sys
import time
from collections import deque
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from multiprocessing.connection import Connection
from multiprocessing.context import BaseContext
from pathlib import Path
from typing import Protocol, cast

import pytest

from . import solution_00
from .solution_00 import (
    EchoReply,
    EchoRequest,
    StopRequest,
    run_echo_session,
)

_REPOSITORY_ROOT: Path = Path(__file__).parents[2]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))


def _child_pids() -> set[int]:
    return {
        process.pid
        for process in multiprocessing.active_children()
        if process.pid is not None
    }


class _ChildProcess(Protocol):
    pid: int | None
    name: str

    def is_alive(self) -> bool: ...

    def terminate(self) -> None: ...

    def join(self, timeout: float | None = None) -> None: ...


def _new_children(existing: set[int]) -> list[_ChildProcess]:
    return [
        cast(_ChildProcess, process)
        for process in multiprocessing.active_children()
        if process.pid is not None and process.pid not in existing
    ]


def _assert_no_new_children(existing: set[int]) -> None:
    deadline: float = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if not _new_children(existing):
            return
        time.sleep(0.01)
    leaked: list[_ChildProcess] = _new_children(existing)
    leaked_names: list[str] = [process.name for process in leaked]
    for process in leaked:
        if process.is_alive():
            process.terminate()
        process.join(timeout=2.0)
    pytest.fail(f"child processes leaked and were cleaned up: {leaked_names}")


def _never_reply_server(connection: Connection) -> None:
    try:
        connection.recv()
        while True:
            time.sleep(1.0)
    finally:
        connection.close()


def _never_stop_server(connection: Connection) -> None:
    try:
        while True:
            request: object = connection.recv()
            if isinstance(request, EchoRequest):
                connection.send(EchoReply(request.request_id, request.message))
            elif isinstance(request, StopRequest):
                while True:
                    time.sleep(1.0)
    finally:
        connection.close()


def test_protocol_messages_are_frozen() -> None:
    request: EchoRequest = EchoRequest(1, "hello")
    reply: EchoReply = EchoReply(1, "hello")
    stop: StopRequest = StopRequest()
    attribute: str = "message"

    with pytest.raises(FrozenInstanceError):
        setattr(request, attribute, "changed")
    with pytest.raises(FrozenInstanceError):
        setattr(reply, attribute, "changed")
    with pytest.raises(FrozenInstanceError):
        setattr(stop, attribute, "changed")


def test_spawn_session_preserves_order_and_empty_strings() -> None:
    context: BaseContext = multiprocessing.get_context("spawn")
    existing: set[int] = _child_pids()

    result: list[str] = run_echo_session(
        ["first", "", "third", "first"],
        timeout=5.0,
        context=context,
    )

    assert result == ["first", "", "third", "first"]
    _assert_no_new_children(existing)


def test_spawn_session_handles_empty_input_without_leaking_child() -> None:
    context: BaseContext = multiprocessing.get_context("spawn")
    existing: set[int] = _child_pids()

    assert run_echo_session((), timeout=5.0, context=context) == []

    _assert_no_new_children(existing)


@pytest.mark.timeout(10)
def test_reply_timeout_cleans_up_real_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context: BaseContext = multiprocessing.get_context("spawn")
    existing: set[int] = _child_pids()
    monkeypatch.setattr(solution_00, "echo_server", _never_reply_server)

    try:
        with pytest.raises(TimeoutError, match=r"^echo server reply timed out$"):
            run_echo_session(["message"], timeout=1.0, context=context)
    finally:
        _assert_no_new_children(existing)


@pytest.mark.timeout(10)
def test_stop_timeout_cleans_up_real_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context: BaseContext = multiprocessing.get_context("spawn")
    existing: set[int] = _child_pids()
    monkeypatch.setattr(solution_00, "echo_server", _never_stop_server)

    try:
        with pytest.raises(TimeoutError, match=r"^echo server did not stop$"):
            run_echo_session(["message"], timeout=1.0, context=context)
    finally:
        _assert_no_new_children(existing)


@pytest.mark.parametrize(
    "timeout",
    [0.0, -1.0, float("nan"), float("inf")],
)
def test_invalid_timeout_is_rejected_before_spawning(timeout: float) -> None:
    existing: set[int] = _child_pids()

    with pytest.raises(ValueError, match=r"^timeout must be finite and positive$"):
        run_echo_session(["message"], timeout=timeout)

    _assert_no_new_children(existing)


def test_boolean_timeout_is_rejected_before_spawning() -> None:
    existing: set[int] = _child_pids()

    with pytest.raises(TypeError, match=r"^timeout must be a real number$"):
        run_echo_session(["message"], timeout=cast(float, True))

    _assert_no_new_children(existing)


@pytest.mark.parametrize(
    "messages",
    [
        cast(list[str], [1]),
        cast(list[str], ["valid", object()]),
    ],
)
def test_non_string_message_is_rejected_before_spawning(
    messages: list[str],
) -> None:
    existing: set[int] = _child_pids()

    with pytest.raises(
        TypeError,
        match=r"^messages\[\d+\] must be a string$",
    ):
        run_echo_session(messages)

    _assert_no_new_children(existing)


ReplyFactory = Callable[[EchoRequest], object]


class _FakeConnection:
    replies: deque[object]
    reply_factory: ReplyFactory | None
    sent: list[object]
    closed: bool
    send_error: Exception | None
    recv_error: Exception | None
    close_error: Exception | None

    def __init__(
        self,
        reply_factory: ReplyFactory | None = None,
        *,
        send_error: Exception | None = None,
        recv_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.replies = deque()
        self.reply_factory = reply_factory
        self.sent = []
        self.closed = False
        self.send_error = send_error
        self.recv_error = recv_error
        self.close_error = close_error

    def send(self, value: object) -> None:
        self.sent.append(value)
        if self.send_error is not None:
            raise self.send_error
        if isinstance(value, EchoRequest) and self.reply_factory is not None:
            self.replies.append(self.reply_factory(value))

    def poll(self, timeout: float) -> bool:
        assert timeout >= 0.0
        return bool(self.replies) or self.recv_error is not None

    def recv(self) -> object:
        if self.recv_error is not None:
            raise self.recv_error
        return self.replies.popleft()

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class _FakeProcess:
    configured_exitcode: int
    alive: bool
    started: bool
    joined: bool
    terminated: bool
    start_error: bool
    join_error: bool

    def __init__(
        self,
        exitcode: int,
        alive: bool,
        start_error: bool,
        join_error: bool,
    ) -> None:
        self.configured_exitcode = exitcode
        self.alive = alive
        self.started = False
        self.joined = False
        self.terminated = False
        self.start_error = start_error
        self.join_error = join_error

    @property
    def exitcode(self) -> int | None:
        if not self.started:
            return None
        return self.configured_exitcode

    def start(self) -> None:
        if self.start_error:
            raise RuntimeError("cannot start child")
        self.started = True

    def join(self, timeout: float | None = None) -> None:
        assert timeout is None or timeout >= 0.0
        self.joined = True
        if self.join_error:
            raise OSError("cannot join child")

    def is_alive(self) -> bool:
        return self.alive

    def terminate(self) -> None:
        self.terminated = True
        self.alive = False


class _FakeContext:
    parent: _FakeConnection
    child: _FakeConnection
    process: _FakeProcess
    process_name: str | None

    def __init__(
        self,
        reply_factory: ReplyFactory,
        *,
        exitcode: int = 0,
        alive: bool = False,
        start_error: bool = False,
        send_error: Exception | None = None,
        recv_error: Exception | None = None,
        parent_close_error: Exception | None = None,
        child_close_error: Exception | None = None,
        join_error: bool = False,
    ) -> None:
        self.parent = _FakeConnection(
            reply_factory,
            send_error=send_error,
            recv_error=recv_error,
            close_error=parent_close_error,
        )
        self.child = _FakeConnection(close_error=child_close_error)
        self.process = _FakeProcess(exitcode, alive, start_error, join_error)
        self.process_name = None

    def Pipe(
        self,
        duplex: bool = True,
    ) -> tuple[_FakeConnection, _FakeConnection]:
        assert duplex is True
        return self.parent, self.child

    def Process(
        self,
        *,
        target: Callable[..., object],
        args: tuple[object, ...],
        name: str | None = None,
    ) -> _FakeProcess:
        assert callable(target)
        assert args == (self.child,)
        self.process_name = name
        return self.process


def _run_with_fake_context(context: _FakeContext) -> list[str]:
    return run_echo_session(
        ["hello"],
        timeout=1.0,
        context=cast(BaseContext, context),
    )


def test_reply_identifier_must_match_request() -> None:
    context = _FakeContext(
        lambda request: EchoReply(request.request_id + 1, request.message),
        alive=True,
    )

    with pytest.raises(RuntimeError, match=r"^unexpected echo reply identifier$"):
        _run_with_fake_context(context)

    assert context.process.terminated is True
    assert context.process.joined is True
    assert context.parent.closed is True
    assert context.child.closed is True


def test_reply_must_have_expected_type() -> None:
    context = _FakeContext(lambda request: request.message, alive=True)

    with pytest.raises(RuntimeError, match=r"^invalid echo reply type: str$"):
        _run_with_fake_context(context)

    assert context.process.terminated is True


def test_reply_message_must_match_request() -> None:
    context = _FakeContext(
        lambda request: EchoReply(request.request_id, "different"),
        alive=True,
    )

    with pytest.raises(RuntimeError, match=r"^echo reply message did not match$"):
        _run_with_fake_context(context)

    assert context.process.terminated is True


def test_child_exitcode_must_be_zero() -> None:
    context = _FakeContext(
        lambda request: EchoReply(request.request_id, request.message),
        exitcode=3,
    )

    with pytest.raises(ChildProcessError, match=r"^echo server exited with code 3$"):
        _run_with_fake_context(context)

    assert context.process.terminated is False
    assert context.process.joined is True


def test_success_uses_cooperative_stop_without_termination() -> None:
    context = _FakeContext(
        lambda request: EchoReply(request.request_id, request.message),
    )

    assert _run_with_fake_context(context) == ["hello"]

    assert isinstance(context.parent.sent[-1], StopRequest)
    assert context.process.terminated is False
    assert context.process.joined is True
    assert context.process_name == "chapter-14-echo-server"
    assert context.parent.closed is True
    assert context.child.closed is True


def test_start_failure_closes_endpoints_without_joining_unstarted_process() -> None:
    context = _FakeContext(
        lambda request: EchoReply(request.request_id, request.message),
        start_error=True,
    )

    with pytest.raises(RuntimeError, match=r"^cannot start child$"):
        _run_with_fake_context(context)

    assert context.process.started is False
    assert context.process.terminated is False
    assert context.process.joined is False
    assert context.parent.closed is True
    assert context.child.closed is True


def test_send_failure_terminates_and_joins_child() -> None:
    context = _FakeContext(
        lambda request: EchoReply(request.request_id, request.message),
        alive=True,
        send_error=BrokenPipeError("cannot send request"),
    )

    with pytest.raises(BrokenPipeError, match=r"^cannot send request$"):
        _run_with_fake_context(context)

    assert context.process.terminated is True
    assert context.process.joined is True
    assert context.parent.closed is True
    assert context.child.closed is True


def test_recv_failure_terminates_and_joins_child() -> None:
    context = _FakeContext(
        lambda request: EchoReply(request.request_id, request.message),
        alive=True,
        recv_error=OSError("cannot receive reply"),
    )

    with pytest.raises(OSError, match=r"^cannot receive reply$"):
        _run_with_fake_context(context)

    assert context.process.terminated is True
    assert context.process.joined is True
    assert context.parent.closed is True
    assert context.child.closed is True


def test_endpoint_close_failure_still_closes_peer_and_cleans_child() -> None:
    context = _FakeContext(
        lambda request: EchoReply(request.request_id + 1, request.message),
        alive=True,
        parent_close_error=OSError("cannot close parent endpoint"),
    )

    with pytest.raises(OSError, match=r"^cannot close parent endpoint$"):
        _run_with_fake_context(context)

    assert context.parent.closed is True
    assert context.child.closed is True
    assert context.process.terminated is True
    assert context.process.joined is True


def test_join_failure_still_closes_endpoints_and_attempts_termination() -> None:
    context = _FakeContext(
        lambda request: EchoReply(request.request_id, request.message),
        alive=True,
        join_error=True,
    )

    with pytest.raises(OSError, match=r"^cannot join child$"):
        _run_with_fake_context(context)

    assert context.parent.closed is True
    assert context.child.closed is True
    assert context.process.terminated is True
    assert context.process.joined is True
