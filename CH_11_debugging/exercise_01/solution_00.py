"""Schedule a stack dump when synchronous code appears stalled."""

import faulthandler
from collections.abc import Callable
from typing import ParamSpec, TypeVar

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")


def run_with_timeout_diagnostics(
    function: Callable[Parameters, Result],
    timeout: float,
    *args: Parameters.args,
    **kwargs: Parameters.kwargs,
) -> Result:
    """Run a callable and dump all thread stacks if it exceeds ``timeout``."""
    if not timeout > 0:
        raise ValueError("timeout must be positive")

    faulthandler.dump_traceback_later(timeout, repeat=False)
    try:
        return function(*args, **kwargs)
    finally:
        faulthandler.cancel_dump_traceback_later()


def main() -> None:
    """Demonstrate a fast call that cancels its scheduled diagnostic."""
    value: str = run_with_timeout_diagnostics(lambda: "finished", 1.0)
    print(value)


if __name__ == "__main__":
    main()
