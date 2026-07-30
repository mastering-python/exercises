"""Count how often each source line in a callable's file executes."""

import inspect
import trace
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, ParamSpec, TypeAlias, TypeVar

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")
SourceLocation: TypeAlias = tuple[str, int]


@dataclass(frozen=True)
class ExecutionCounts(Generic[Result]):
    """A return value and line-number-to-count mapping."""

    result: Result
    counts: dict[int, int]


def count_executions(
    function: Callable[Parameters, Result],
    *args: Parameters.args,
    **kwargs: Parameters.kwargs,
) -> ExecutionCounts[Result]:
    """Run a callable and count lines from its source file."""
    try:
        filename: str | None = inspect.getsourcefile(function)
    except TypeError:
        filename = None
    if filename is None:
        raise ValueError("function has no inspectable source file")

    tracer: trace.Trace = trace.Trace(count=True, trace=False)
    result: Result = tracer.runfunc(function, *args, **kwargs)
    raw_counts: dict[SourceLocation, int] = tracer.results().counts
    counts: dict[int, int] = {
        line_number: count
        for (source_file, line_number), count in raw_counts.items()
        if source_file == filename
    }
    return ExecutionCounts(result=result, counts=counts)


def main() -> None:
    """Demonstrate line counts for a small loop."""

    def total(limit: int) -> int:
        result: int = 0
        for number in range(limit):
            result += number
        return result

    print(count_executions(total, 4))


if __name__ == "__main__":
    main()
