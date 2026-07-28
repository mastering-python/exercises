"""Public solutions for the Chapter 10 testing and logging exercises."""

from __future__ import annotations

import doctest

from CH_10_testing_and_logging.exercise_01.doctest_runner import (
    run_doctests,
    run_module_doctests,
)
from CH_10_testing_and_logging.exercise_01.file_documentation_plugin import (
    pytest_collect_file,
)
from CH_10_testing_and_logging.exercise_01.task_logging import (
    TaskBatchLoggerAdapter,
)

__all__: list[str] = [
    "TaskBatchLoggerAdapter",
    "pytest_collect_file",
    "run_doctests",
    "run_module_doctests",
]


def _double(value: int) -> int:
    """
    Return twice *value*.

    >>> _double(6)
    12
    """
    return value * 2


def main() -> None:
    """Demonstrate the runner and report its aggregate totals."""
    result: doctest.TestResults = run_doctests(_double)
    print(f"Attempted {result.attempted} doctest; {result.failed} failed.")


if __name__ == "__main__":
    main()
