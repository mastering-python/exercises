from collections.abc import Callable, Iterator
from inspect import signature

import pytest

from .solution_00 import Timing, print_timing, track


def test_configured_track_reports_exact_timing_on_success() -> None:
    readings: Iterator[float] = iter((10.0, 10.25))
    reports: list[Timing] = []

    @track(label="addition", clock=readings.__next__, reporter=reports.append)
    def add(left: int, right: int) -> int:
        return left + right

    result: int = add(2, 3)

    assert result == 5
    assert reports == [Timing(label="addition", elapsed=0.25, failed=False)]


def test_track_reports_failure_and_propagates_original_exception() -> None:
    readings: Iterator[float] = iter((3.0, 4.5))
    reports: list[Timing] = []
    error: RuntimeError = RuntimeError("boom")

    @track(label="explosion", clock=readings.__next__, reporter=reports.append)
    def explode() -> None:
        raise error

    with pytest.raises(RuntimeError) as caught:
        explode()

    assert caught.value is error
    assert reports == [Timing(label="explosion", elapsed=1.5, failed=True)]


def test_track_can_be_used_directly(
    capsys: pytest.CaptureFixture[str],
) -> None:
    @track
    def answer() -> int:
        return 42

    result: int = answer()
    output: str = capsys.readouterr().out

    assert result == 42
    assert output.startswith("answer completed in ")
    assert output.endswith("s\n")


def test_track_uses_function_name_as_default_label() -> None:
    readings: Iterator[float] = iter((7.0, 9.0))
    reports: list[Timing] = []

    @track(clock=readings.__next__, reporter=reports.append)
    def calculate() -> str:
        return "done"

    calculate()

    assert reports == [Timing(label="calculate", elapsed=2.0, failed=False)]


def test_track_forwards_positional_and_keyword_arguments() -> None:
    readings: Iterator[float] = iter((1.0, 2.0))
    reports: list[Timing] = []

    @track(clock=readings.__next__, reporter=reports.append)
    def describe(number: int, *, prefix: str) -> str:
        return f"{prefix}: {number}"

    result: str = describe(7, prefix="value")

    assert result == "value: 7"


def test_track_preserves_function_metadata_and_signature() -> None:
    readings: Iterator[float] = iter((1.0, 2.0))
    reports: list[Timing] = []

    def greet(name: str, punctuation: str = "!") -> str:
        """Return a greeting."""
        return f"Hello, {name}{punctuation}"

    tracked_greet: Callable[[str, str], str] = track(
        clock=readings.__next__,
        reporter=reports.append,
    )(greet)

    assert tracked_greet.__name__ == "greet"
    assert tracked_greet.__doc__ == "Return a greeting."
    assert getattr(tracked_greet, "__wrapped__", None) is greet
    assert signature(tracked_greet) == signature(greet)


@pytest.mark.parametrize(
    ("timing", "expected"),
    (
        (
            Timing(label="lookup", elapsed=0.125, failed=False),
            "lookup completed in 0.125000s\n",
        ),
        (
            Timing(label="lookup", elapsed=0.125, failed=True),
            "lookup failed in 0.125000s\n",
        ),
    ),
)
def test_print_timing_uses_default_format(
    timing: Timing,
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_timing(timing)

    assert capsys.readouterr().out == expected
