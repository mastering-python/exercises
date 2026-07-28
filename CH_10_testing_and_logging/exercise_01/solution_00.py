"""Find and run the doctests attached to a Python object."""

from __future__ import annotations

import doctest


def run_doctests(
    target: object,
    *,
    optionflags: int = doctest.ELLIPSIS,
) -> doctest.TestResults:
    """Run every doctest found recursively in *target*."""
    finder: doctest.DocTestFinder = doctest.DocTestFinder(recurse=True)
    runner: doctest.DocTestRunner = doctest.DocTestRunner(
        optionflags=optionflags,
    )

    tests: list[doctest.DocTest] = finder.find(target)
    for test in tests:
        runner.run(test)

    return runner.summarize()


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
