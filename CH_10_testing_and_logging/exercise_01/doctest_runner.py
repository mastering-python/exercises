"""Discover and run doctests attached to Python objects and modules."""

from __future__ import annotations

import doctest
import keyword
import threading
from types import ModuleType

_RUN_LOCK: threading.RLock = threading.RLock()


def run_doctests(
    target: object,
    *,
    optionflags: int = doctest.ELLIPSIS,
) -> doctest.TestResults:
    """Run doctests found recursively in *target*."""
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


def run_module_doctests(
    target: ModuleType,
    *,
    optionflags: int = doctest.ELLIPSIS,
) -> doctest.TestResults:
    """Run and aggregate examples in a module and its discoverable members."""
    module: ModuleType = _require_module(target)
    return run_doctests(module, optionflags=optionflags)


def _require_module(target: object) -> ModuleType:
    if not isinstance(target, ModuleType):
        raise TypeError("target must be a module")
    return target
