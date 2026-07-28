"""Test the task-batching LoggerAdapter with real logging records."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TextIO, cast

import pytest

from CH_10_testing_and_logging.exercise_01.solution_00 import (
    TaskBatchLoggerAdapter,
)


class RecordHandler(logging.Handler):
    """Capture emitted records for assertions."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class FailOnceHandler(RecordHandler):
    """Raise on the first emission and capture later emissions."""

    def __init__(self) -> None:
        super().__init__()
        self.fail: bool = True

    def emit(self, record: logging.LogRecord) -> None:
        if self.fail:
            self.fail = False
            raise RuntimeError("handler failed")
        super().emit(record)


class BrokenStream:
    """Fail every stream write."""

    def write(self, text: str) -> int:
        raise OSError("stream unavailable")

    def flush(self) -> None:
        pass


def _adapter(
    handler: logging.Handler,
    *,
    level: int = logging.DEBUG,
) -> TaskBatchLoggerAdapter:
    logger: logging.Logger = logging.getLogger(f"chapter-10-task-batches-{id(handler)}")
    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False
    logger.addHandler(handler)
    return TaskBatchLoggerAdapter(
        logger,
        {"component": "chapter-10", "task_id": "adapter-default"},
    )


def test_flush_combines_messages_in_insertion_order_and_isolates_tasks() -> None:
    handler: RecordHandler = RecordHandler()
    adapter: TaskBatchLoggerAdapter = _adapter(handler)

    adapter.record("task-a", logging.INFO, "first %s", "message")
    adapter.record("task-b", logging.WARNING, "other")
    adapter.record("task-a", logging.ERROR, "last")

    assert adapter.flush("task-a") is True
    assert adapter.flush("task-b") is True

    assert [record.getMessage() for record in handler.records] == [
        "first message\nlast",
        "other",
    ]
    assert [record.levelno for record in handler.records] == [
        logging.ERROR,
        logging.WARNING,
    ]
    assert [record.__dict__["task_id"] for record in handler.records] == [
        "task-a",
        "task-b",
    ]
    assert [record.__dict__["component"] for record in handler.records] == [
        "chapter-10",
        "chapter-10",
    ]


def test_formatting_failure_preserves_batch_until_explicit_discard() -> None:
    handler: RecordHandler = RecordHandler()
    adapter: TaskBatchLoggerAdapter = _adapter(handler)
    adapter.record("broken", logging.INFO, "number %d", "not-a-number")

    with pytest.raises(TypeError):
        adapter.flush("broken")

    assert adapter.pending_count("broken") == 1
    assert adapter.discard("broken") == 1
    assert adapter.pending_count("broken") == 0
    assert handler.records == []


def test_disabled_level_preserves_batch_for_later_flush() -> None:
    handler: RecordHandler = RecordHandler()
    adapter: TaskBatchLoggerAdapter = _adapter(handler, level=logging.WARNING)
    adapter.record("quiet", logging.INFO, "retained")

    assert adapter.flush("quiet") is False
    assert adapter.pending_count("quiet") == 1

    adapter.logger.setLevel(logging.INFO)

    assert adapter.flush("quiet") is True
    assert [record.getMessage() for record in handler.records] == ["retained"]


def test_handler_level_rejection_preserves_batch_for_later_flush() -> None:
    handler: RecordHandler = RecordHandler()
    handler.setLevel(logging.WARNING)
    adapter: TaskBatchLoggerAdapter = _adapter(handler)
    adapter.record("quiet-handler", logging.INFO, "retained")

    assert adapter.flush("quiet-handler") is False
    assert adapter.pending_count("quiet-handler") == 1

    handler.setLevel(logging.INFO)

    assert adapter.flush("quiet-handler") is True
    assert [record.getMessage() for record in handler.records] == ["retained"]


def test_stream_handler_error_propagates_and_preserves_batch() -> None:
    handler: logging.StreamHandler[TextIO] = logging.StreamHandler(
        cast(TextIO, BrokenStream())
    )
    adapter: TaskBatchLoggerAdapter = _adapter(handler)
    adapter.record("broken-stream", logging.ERROR, "retained")

    with pytest.raises(RuntimeError, match="logging handler failed"):
        adapter.flush("broken-stream")

    assert adapter.pending_count("broken-stream") == 1


def test_logging_failure_preserves_batch_for_retry() -> None:
    handler: FailOnceHandler = FailOnceHandler()
    adapter: TaskBatchLoggerAdapter = _adapter(handler)
    adapter.record("retry", logging.WARNING, "try again")

    with pytest.raises(RuntimeError, match="handler failed"):
        adapter.flush("retry")

    assert adapter.pending_count("retry") == 1
    assert adapter.flush("retry") is True
    assert [record.getMessage() for record in handler.records] == ["try again"]


def test_empty_and_unknown_task_ids_have_explicit_behavior() -> None:
    adapter: TaskBatchLoggerAdapter = _adapter(RecordHandler())

    with pytest.raises(ValueError, match="task_id must not be empty"):
        adapter.record("", logging.INFO, "message")
    with pytest.raises(TypeError, match="task_id must be a string"):
        adapter.record(42, logging.INFO, "message")  # type: ignore[arg-type]
    with pytest.raises(KeyError, match="unknown task_id"):
        adapter.flush("unknown")

    assert adapter.pending_count("unknown") == 0
    assert adapter.discard("unknown") == 0


def test_concurrent_tasks_remain_isolated_and_ordered() -> None:
    handler: RecordHandler = RecordHandler()
    adapter: TaskBatchLoggerAdapter = _adapter(handler)

    def record_task(task_number: int) -> None:
        task_id: str = f"task-{task_number}"
        for message_number in range(40):
            adapter.record(
                task_id,
                logging.INFO,
                "message %d",
                message_number,
            )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(record_task, range(8)))

    for task_number in range(8):
        assert adapter.flush(f"task-{task_number}") is True

    assert len(handler.records) == 8
    for task_number, record in enumerate(handler.records):
        assert record.__dict__["task_id"] == f"task-{task_number}"
        assert record.getMessage().splitlines() == [
            f"message {message_number}" for message_number in range(40)
        ]
