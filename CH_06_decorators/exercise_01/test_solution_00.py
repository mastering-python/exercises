from collections.abc import Callable, Iterator
from functools import partial
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


def test_reporter_failure_cannot_mask_target_exception() -> None:
    readings: Iterator[float] = iter((3.0, 4.5))
    reports: list[Timing] = []
    target_error: RuntimeError = RuntimeError("target failed")
    reporter_error: ValueError = ValueError("reporter failed")

    def failing_reporter(timing: Timing) -> None:
        reports.append(timing)
        raise reporter_error

    @track(
        label="explosion",
        clock=readings.__next__,
        reporter=failing_reporter,
    )
    def explode() -> None:
        raise target_error

    with pytest.raises(RuntimeError) as caught:
        explode()

    assert caught.value is target_error
    assert reports == [Timing(label="explosion", elapsed=1.5, failed=True)]


def test_ending_clock_failure_cannot_mask_target_exception() -> None:
    clock_calls: list[int] = []
    reports: list[Timing] = []
    target_error: RuntimeError = RuntimeError("target failed")
    clock_error: ValueError = ValueError("clock failed")

    def failing_ending_clock() -> float:
        clock_calls.append(len(clock_calls) + 1)
        if len(clock_calls) == 1:
            return 3.0
        raise clock_error

    @track(clock=failing_ending_clock, reporter=reports.append)
    def explode() -> None:
        raise target_error

    with pytest.raises(RuntimeError) as caught:
        explode()

    assert caught.value is target_error
    assert clock_calls == [1, 2]
    assert reports == []


def test_starting_clock_failure_prevents_target_execution() -> None:
    target_calls: list[None] = []
    clock_error: ValueError = ValueError("clock failed")

    def failing_starting_clock() -> float:
        raise clock_error

    @track(clock=failing_starting_clock)
    def target() -> None:
        target_calls.append(None)

    with pytest.raises(ValueError) as caught:
        target()

    assert caught.value is clock_error
    assert target_calls == []


def test_reporter_failure_after_success_propagates() -> None:
    readings: Iterator[float] = iter((3.0, 4.5))
    reporter_error: ValueError = ValueError("reporter failed")

    def failing_reporter(timing: Timing) -> None:
        raise reporter_error

    @track(clock=readings.__next__, reporter=failing_reporter)
    def target() -> str:
        return "result"

    with pytest.raises(ValueError) as caught:
        target()

    assert caught.value is reporter_error


def test_ending_clock_failure_after_success_propagates() -> None:
    clock_calls: list[int] = []
    clock_error: ValueError = ValueError("clock failed")

    def failing_ending_clock() -> float:
        clock_calls.append(len(clock_calls) + 1)
        if len(clock_calls) == 1:
            return 3.0
        raise clock_error

    @track(clock=failing_ending_clock)
    def target() -> str:
        return "result"

    with pytest.raises(ValueError) as caught:
        target()

    assert caught.value is clock_error
    assert clock_calls == [1, 2]


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


def test_track_accepts_direct_call_with_configuration() -> None:
    readings: Iterator[float] = iter((10.0, 10.25))
    reports: list[Timing] = []

    def add(left: int, right: int) -> int:
        return left + right

    tracked_add: Callable[[int, int], int] = track(
        add,
        label="addition",
        clock=readings.__next__,
        reporter=reports.append,
    )

    assert tracked_add(2, 3) == 5
    assert reports == [Timing(label="addition", elapsed=0.25, failed=False)]


def test_track_uses_function_name_as_default_label() -> None:
    readings: Iterator[float] = iter((7.0, 9.0))
    reports: list[Timing] = []

    @track(clock=readings.__next__, reporter=reports.append)
    def calculate() -> str:
        return "done"

    calculate()

    assert reports == [Timing(label="calculate", elapsed=2.0, failed=False)]


def test_track_uses_callable_type_as_default_label_without_name() -> None:
    readings: Iterator[float] = iter((7.0, 9.0))
    reports: list[Timing] = []

    def add(left: int, right: int) -> int:
        return left + right

    add_ten: Callable[[int], int] = partial(add, 10)
    tracked_add_ten: Callable[[int], int] = track(
        add_ten,
        clock=readings.__next__,
        reporter=reports.append,
    )

    result: int = tracked_add_ten(5)

    assert result == 15
    assert reports == [Timing(label="partial", elapsed=2.0, failed=False)]
    assert getattr(tracked_add_ten, "__wrapped__", None) is add_ten
    assert signature(tracked_add_ten) == signature(add_ten)


def test_track_uses_callable_type_when_name_is_not_a_string() -> None:
    readings: Iterator[float] = iter((7.0, 9.0))
    reports: list[Timing] = []

    class Increment:
        __name__: int = 42

        def __call__(self, value: int) -> int:
            return value + 1

    increment: Increment = Increment()
    tracked_increment: Callable[[int], int] = track(
        increment,
        clock=readings.__next__,
        reporter=reports.append,
    )

    result: int = tracked_increment(5)

    assert result == 6
    assert reports == [Timing(label="Increment", elapsed=2.0, failed=False)]
    assert getattr(tracked_increment, "__wrapped__", None) is increment
    assert signature(tracked_increment) == signature(increment)


def test_track_ignores_non_string_qualname_metadata() -> None:
    readings: Iterator[float] = iter((7.0, 9.0))
    reports: list[Timing] = []

    class Increment:
        def __call__(self, value: int) -> int:
            return value + 1

    increment: Increment = Increment()
    increment.__dict__["__qualname__"] = 42

    tracked_increment: Callable[[int], int] = track(
        increment,
        clock=readings.__next__,
        reporter=reports.append,
    )
    result: int = tracked_increment(5)

    assert result == 6
    assert reports == [Timing(label="Increment", elapsed=2.0, failed=False)]
    assert getattr(tracked_increment, "__wrapped__", None) is increment
    assert signature(tracked_increment) == signature(increment)


def test_track_ignores_non_dict_annotations_with_explicit_label() -> None:
    readings: Iterator[float] = iter((7.0, 9.0))
    reports: list[Timing] = []

    class Increment:
        def __call__(self, value: int) -> int:
            return value + 1

    increment: Increment = Increment()
    annotations_attribute: str = "__annotations__"
    setattr(increment, annotations_attribute, 42)

    tracked_increment: Callable[[int], int] = track(
        increment,
        label="increment",
        clock=readings.__next__,
        reporter=reports.append,
    )
    result: int = tracked_increment(5)

    assert result == 6
    assert reports == [Timing(label="increment", elapsed=2.0, failed=False)]
    assert getattr(tracked_increment, "__wrapped__", None) is increment
    assert signature(tracked_increment) == signature(increment)


def test_track_ignores_non_mapping_wrapper_updates() -> None:
    readings: Iterator[float] = iter((7.0, 9.0))
    reports: list[Timing] = []

    class Increment:
        def __getattribute__(self, attribute: str) -> object:
            if attribute == "__dict__":
                return 42
            return super().__getattribute__(attribute)

        def __call__(self, value: int) -> int:
            return value + 1

    increment: Increment = Increment()
    tracked_increment: Callable[[int], int] = track(
        increment,
        clock=readings.__next__,
        reporter=reports.append,
    )
    result: int = tracked_increment(5)

    assert result == 6
    assert reports == [Timing(label="Increment", elapsed=2.0, failed=False)]
    assert getattr(tracked_increment, "__wrapped__", None) is increment
    assert signature(tracked_increment) == signature(increment)


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

    greet.__dict__["category"] = "salutation"
    tracked_greet: Callable[[str, str], str] = track(
        clock=readings.__next__,
        reporter=reports.append,
    )(greet)

    assert tracked_greet.__name__ == "greet"
    assert tracked_greet.__module__ == greet.__module__
    assert tracked_greet.__qualname__ == greet.__qualname__
    assert tracked_greet.__doc__ == "Return a greeting."
    assert tracked_greet.__annotations__ == greet.__annotations__
    assert getattr(tracked_greet, "__wrapped__", None) is greet
    assert signature(tracked_greet) == signature(greet)
    assert getattr(tracked_greet, "category", None) == "salutation"


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
