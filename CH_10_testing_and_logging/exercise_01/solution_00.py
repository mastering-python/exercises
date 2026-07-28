"""Find and run the doctests attached to a Python object."""

from __future__ import annotations

import doctest
import keyword
import threading

_RUN_LOCK: threading.RLock = threading.RLock()


def run_doctests(
    target: object,
    *,
    optionflags: int = doctest.ELLIPSIS,
) -> doctest.TestResults:
    """Run every doctest found recursively in *target*."""
    finder: doctest.DocTestFinder = doctest.DocTestFinder(recurse=True)
    runner: doctest.DocTestRunner = doctest.DocTestRunner(
        verbose=False,
        optionflags=optionflags,
    )

    target_name: object = getattr(target, "__name__", None)
    finder_name: str = type(target).__name__
    extraglobs: dict[str, object] = {}
    if (
        isinstance(target_name, str)
        and target_name.isidentifier()
        and not keyword.iskeyword(target_name)
    ):
        finder_name = target_name
        extraglobs[target_name] = target

    with _RUN_LOCK:
        tests: list[doctest.DocTest] = finder.find(
            target,
            name=finder_name,
            extraglobs=extraglobs,
        )
        for test in tests:
            runner.run(test)

        return runner.summarize(verbose=False)


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
