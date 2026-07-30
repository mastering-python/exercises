"""Spawn-safe echo request/reply protocol over a multiprocessing pipe."""

from __future__ import annotations

import multiprocessing
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import isfinite
from multiprocessing.connection import Connection
from multiprocessing.context import BaseContext
from numbers import Real
from time import monotonic
from typing import Protocol, cast

__all__: list[str] = [
    "EchoReply",
    "EchoRequest",
    "StopRequest",
    "echo_server",
    "run_echo_session",
]


@dataclass(frozen=True)
class EchoRequest:
    """One identified string sent to the echo server."""

    request_id: int
    message: str


@dataclass(frozen=True)
class EchoReply:
    """One identified string returned by the echo server."""

    request_id: int
    message: str


@dataclass(frozen=True)
class StopRequest:
    """Cooperative request for the echo server to exit."""


class _ProcessHandle(Protocol):
    @property
    def exitcode(self) -> int | None: ...

    def start(self) -> None: ...

    def join(self, timeout: float | None = None) -> None: ...

    def is_alive(self) -> bool: ...

    def terminate(self) -> None: ...


class _EchoContext(Protocol):
    def Pipe(self, duplex: bool = True) -> tuple[Connection, Connection]: ...

    def Process(
        self,
        *,
        target: Callable[[Connection], None],
        args: tuple[Connection],
        name: str,
    ) -> _ProcessHandle: ...


def _valid_request_id(request_id: object) -> bool:
    return type(request_id) is int and request_id >= 0


def echo_server(connection: Connection) -> None:
    """Serve typed echo requests until a cooperative stop request arrives."""

    try:
        while True:
            try:
                request: object = connection.recv()
            except EOFError:
                return
            if isinstance(request, StopRequest):
                return
            if not isinstance(request, EchoRequest):
                raise TypeError(
                    f"invalid echo request type: {type(request).__name__}",
                )
            if not _valid_request_id(request.request_id):
                raise ValueError(
                    "echo request identifier must be a nonnegative integer"
                )
            request_message: object = cast(object, request.message)
            if not isinstance(request_message, str):
                raise TypeError("echo request message must be a string")
            connection.send(EchoReply(request.request_id, request_message))
    finally:
        connection.close()


def _validated_messages(messages: Sequence[str]) -> tuple[str, ...]:
    validated: tuple[str, ...] = tuple(messages)
    for index, message in enumerate(validated):
        candidate: object = cast(object, message)
        if not isinstance(candidate, str):
            raise TypeError(f"messages[{index}] must be a string")
    return validated


def _validated_timeout(timeout: float) -> float:
    if isinstance(timeout, bool) or not isinstance(timeout, Real):
        raise TypeError("timeout must be a real number")
    if (isinstance(timeout, float) and not isfinite(timeout)) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    return float(timeout)


def _remaining(deadline: float) -> float:
    remaining: float = deadline - monotonic()
    if remaining <= 0.0:
        raise TimeoutError("echo session timed out")
    return remaining


def _validated_reply(reply: object, request: EchoRequest) -> EchoReply:
    if not isinstance(reply, EchoReply):
        raise RuntimeError(f"invalid echo reply type: {type(reply).__name__}")
    if (
        not _valid_request_id(reply.request_id)
        or reply.request_id != request.request_id
    ):
        raise RuntimeError("unexpected echo reply identifier")
    reply_message: object = cast(object, reply.message)
    if not isinstance(reply_message, str) or reply_message != request.message:
        raise RuntimeError("echo reply message did not match")
    return reply


def run_echo_session(
    messages: Sequence[str],
    *,
    timeout: float = 5.0,
    context: BaseContext | None = None,
) -> list[str]:
    """Echo ``messages`` through one bounded child-process session."""

    validated_messages: tuple[str, ...] = _validated_messages(messages)
    validated_timeout: float = _validated_timeout(timeout)
    runtime_context: BaseContext = (
        multiprocessing.get_context("spawn") if context is None else context
    )

    parent_connection: Connection
    child_connection: Connection
    echo_context: _EchoContext = cast(_EchoContext, runtime_context)
    parent_connection, child_connection = echo_context.Pipe(duplex=True)
    process: _ProcessHandle | None = None
    started: bool = False
    failed: bool = True
    deadline: float = monotonic() + validated_timeout
    replies: list[str] = []

    try:
        process = echo_context.Process(
            target=echo_server,
            args=(child_connection,),
            name="chapter-14-echo-server",
        )
        process.start()
        started = True
        child_connection.close()

        for request_id, message in enumerate(validated_messages):
            request: EchoRequest = EchoRequest(request_id, message)
            parent_connection.send(request)
            if not parent_connection.poll(_remaining(deadline)):
                raise TimeoutError("echo server reply timed out")
            try:
                raw_reply: object = parent_connection.recv()
            except EOFError as error:
                raise RuntimeError("echo server closed before replying") from error
            reply: EchoReply = _validated_reply(raw_reply, request)
            replies.append(reply.message)

        parent_connection.send(StopRequest())
        process.join(_remaining(deadline))
        if process.is_alive():
            raise TimeoutError("echo server did not stop")
        if process.exitcode != 0:
            raise ChildProcessError(
                f"echo server exited with code {process.exitcode}",
            )
        failed = False
        return replies
    finally:
        try:
            try:
                parent_connection.close()
            finally:
                child_connection.close()
        finally:
            if failed and process is not None and started:
                try:
                    if process.is_alive():
                        process.terminate()
                finally:
                    process.join(validated_timeout)


def _demonstrate() -> None:
    replies: list[str] = run_echo_session(["hello", "", "goodbye"])
    print(replies)


if __name__ == "__main__":
    _demonstrate()
