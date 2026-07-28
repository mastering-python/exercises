"""Thread-safe logging batches keyed by task ID."""

from __future__ import annotations

import logging
import threading
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, NoReturn, cast

if TYPE_CHECKING:

    class _LoggerAdapterBase(logging.LoggerAdapter[logging.Logger]):
        pass

else:
    _LoggerAdapterBase = logging.LoggerAdapter


@dataclass(frozen=True, slots=True)
class _PendingMessage:
    level: int
    message: object
    args: tuple[object, ...]


class TaskBatchLoggerAdapter(_LoggerAdapterBase):
    """Buffer messages per task and emit one record for each successful flush."""

    separator: str = "\n"

    def __init__(
        self,
        logger: logging.Logger,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(logger, dict(extra or {}))
        self._batches: dict[str, list[_PendingMessage]] = {}
        self._lock: threading.RLock = threading.RLock()

    def process(
        self,
        msg: object,
        kwargs: MutableMapping[str, Any],
    ) -> tuple[object, MutableMapping[str, Any]]:
        """Merge adapter and call-specific context for the combined record."""
        call_extra: object = kwargs.get("extra")
        if call_extra is not None and not isinstance(call_extra, Mapping):
            raise TypeError("extra must be a mapping")

        merged_extra: dict[str, object] = dict(self.extra or {})
        if call_extra is not None:
            merged_extra.update(cast(Mapping[str, object], call_extra))
        kwargs["extra"] = merged_extra
        return msg, kwargs

    def record(
        self,
        task_id: str,
        level: int,
        message: object,
        *args: object,
    ) -> None:
        """Append one lazily formatted message to *task_id*."""
        self._validate_task_id(task_id)
        pending: _PendingMessage = _PendingMessage(level, message, args)
        with self._lock:
            self._batches.setdefault(task_id, []).append(pending)

    def flush(self, task_id: str) -> bool:
        """Emit and remove one task batch, retaining it on any failure."""
        self._validate_task_id(task_id)
        with self._lock:
            batch: list[_PendingMessage] | None = self._batches.get(task_id)
            if not batch:
                raise KeyError(f"unknown task_id: {task_id}")

            pending: tuple[_PendingMessage, ...] = tuple(batch)
            level: int = max(message.level for message in pending)
            if not self.isEnabledFor(level):
                return False

            formatted: list[str] = [
                self._format_message(message) for message in pending
            ]
            record: logging.LogRecord = self._make_record(
                task_id,
                level,
                self.separator.join(formatted),
            )
            if not self._dispatch_record(record):
                return False

            del batch[: len(pending)]
            if not batch:
                del self._batches[task_id]
            return True

    def pending_count(self, task_id: str) -> int:
        """Return the number of buffered messages for *task_id*."""
        self._validate_task_id(task_id)
        with self._lock:
            return len(self._batches.get(task_id, ()))

    def discard(self, task_id: str) -> int:
        """Explicitly discard and return the size of one task batch."""
        self._validate_task_id(task_id)
        with self._lock:
            batch: list[_PendingMessage] | None = self._batches.pop(task_id, None)
            return len(batch) if batch is not None else 0

    @staticmethod
    def _format_message(message: _PendingMessage) -> str:
        rendered: str = str(message.message)
        return rendered % message.args if message.args else rendered

    def _make_record(
        self,
        task_id: str,
        level: int,
        message: str,
    ) -> logging.LogRecord:
        extra: dict[str, object] = dict(self.extra or {})
        extra["task_id"] = task_id
        file_name: str
        line_number: int
        function_name: str
        stack_info: str | None
        file_name, line_number, function_name, stack_info = self.logger.findCaller(
            stack_info=False,
            stacklevel=3,
        )
        return self.logger.makeRecord(
            self.logger.name,
            level,
            file_name,
            line_number,
            message,
            (),
            None,
            function_name,
            extra,
            stack_info,
        )

    def _dispatch_record(self, record: logging.LogRecord) -> bool:
        if not self.logger.filter(record):
            return False

        handlers: list[logging.Handler] = self._handlers_for()
        emitted: bool = False
        for handler in handlers:
            if record.levelno >= handler.level and self._emit(handler, record):
                emitted = True
        return emitted

    def _handlers_for(self) -> list[logging.Handler]:
        handlers: list[logging.Handler] = []
        logger: logging.Logger | None = self.logger
        while logger is not None:
            handlers.extend(logger.handlers)
            if not logger.propagate:
                break
            logger = logger.parent

        if not handlers and logging.lastResort is not None:
            handlers.append(logging.lastResort)
        return handlers

    @staticmethod
    def _emit(handler: logging.Handler, record: logging.LogRecord) -> bool:
        handler.acquire()
        sentinel: object = object()
        previous_handle_error: object = handler.__dict__.get(
            "handleError",
            sentinel,
        )

        def raise_handler_error(failed_record: logging.LogRecord) -> NoReturn:
            raise RuntimeError(f"logging handler failed for {failed_record.name}")

        try:
            if not handler.filter(record):
                return False
            handler.__dict__["handleError"] = raise_handler_error
            handler.emit(record)
            return True
        finally:
            if previous_handle_error is sentinel:
                handler.__dict__.pop("handleError", None)
            else:
                handler.__dict__["handleError"] = previous_handle_error
            handler.release()

    @staticmethod
    def _validate_task_id(task_id: object) -> None:
        if not isinstance(task_id, str):
            raise TypeError("task_id must be a string")
        if not task_id:
            raise ValueError("task_id must not be empty")
