from collections.abc import Callable, Iterator
from inspect import signature

import pytest

from CH_06_decorators.exercise_01.solution_00 import Timing

from .solution_00 import TimingStats, TrackedCallable, track


def test_stats_are_initially_empty_and_print_as_documented(
    capsys: pytest.CaptureFixture[str],
) -> None:
    @track(label="lookup")
    def lookup() -> None:
        raise AssertionError("the decorated function must not run")

    assert lookup.stats == TimingStats()
    assert lookup.stats.average is None

    lookup.print_stats()

    assert capsys.readouterr().out == (
        "lookup stats: count=0, total=0.000000s, minimum=n/a, "
        "maximum=n/a, average=n/a\n"
    )


def test_two_calls_record_exact_aggregates_and_reports(
    capsys: pytest.CaptureFixture[str],
) -> None:
    readings: Iterator[float] = iter((10.0, 10.25, 20.0, 21.5))
    reports: list[Timing] = []

    @track(label="lookup", clock=readings.__next__, reporter=reports.append)
    def lookup(value: int) -> int:
        return value * 2

    assert lookup(3) == 6
    assert lookup(4) == 8
    assert lookup.stats == TimingStats(
        count=2,
        total=1.75,
        minimum=0.25,
        maximum=1.5,
    )
    assert lookup.stats.average == 0.875
    assert reports == [
        Timing(label="lookup", elapsed=0.25, failed=False),
        Timing(label="lookup", elapsed=1.5, failed=False),
    ]

    lookup.print_stats()

    assert capsys.readouterr().out == (
        "lookup stats: count=2, total=1.750000s, minimum=0.250000s, "
        "maximum=1.500000s, average=0.875000s\n"
    )


def test_failed_target_is_counted_reported_and_propagated() -> None:
    readings: Iterator[float] = iter((3.0, 4.5))
    reports: list[Timing] = []
    error: RuntimeError = RuntimeError("boom")

    @track(label="explosion", clock=readings.__next__, reporter=reports.append)
    def explode() -> None:
        raise error

    with pytest.raises(RuntimeError) as caught:
        explode()

    assert caught.value is error
    assert explode.stats == TimingStats(
        count=1,
        total=1.5,
        minimum=1.5,
        maximum=1.5,
    )
    assert reports == [Timing(label="explosion", elapsed=1.5, failed=True)]


def test_decorator_instances_have_independent_stats() -> None:
    first_readings: Iterator[float] = iter((0.0, 1.0))
    second_readings: Iterator[float] = iter((5.0, 7.0))

    @track(clock=first_readings.__next__, reporter=lambda timing: None)
    def first() -> None:
        pass

    @track(clock=second_readings.__next__, reporter=lambda timing: None)
    def second() -> None:
        pass

    first()

    assert first.stats == TimingStats(1, 1.0, 1.0, 1.0)
    assert second.stats == TimingStats()
    assert first.stats is not second.stats


def test_direct_form_accepts_configuration_and_exposes_typed_protocol() -> None:
    readings: Iterator[float] = iter((10.0, 10.25))
    reports: list[Timing] = []

    def add(left: int, right: int) -> int:
        return left + right

    tracked_add: TrackedCallable[[int, int], int] = track(
        add,
        label="addition",
        clock=readings.__next__,
        reporter=reports.append,
    )

    assert tracked_add(2, 3) == 5
    assert tracked_add.stats.count == 1
    assert reports == [Timing(label="addition", elapsed=0.25, failed=False)]


def test_configured_form_preserves_arguments_result_metadata_and_signature() -> None:
    readings: Iterator[float] = iter((1.0, 2.0))
    reports: list[Timing] = []

    def greet(name: str, *, punctuation: str = "!") -> str:
        """Return a greeting."""
        return f"Hello, {name}{punctuation}"

    tracked_greet: TrackedCallable[..., str] = track(
        label="greeting",
        clock=readings.__next__,
        reporter=reports.append,
    )(greet)

    assert tracked_greet("Ada", punctuation="?") == "Hello, Ada?"
    assert getattr(tracked_greet, "__name__", None) == "greet"
    assert getattr(tracked_greet, "__doc__", None) == "Return a greeting."
    assert getattr(tracked_greet, "__wrapped__", None) is greet
    assert signature(tracked_greet) == signature(greet)


def test_default_label_is_the_function_name() -> None:
    readings: Iterator[float] = iter((7.0, 9.0))
    reports: list[Timing] = []

    @track(clock=readings.__next__, reporter=reports.append)
    def calculate() -> str:
        return "done"

    calculate()

    assert reports == [Timing(label="calculate", elapsed=2.0, failed=False)]


def test_reporter_failure_after_success_propagates_after_recording() -> None:
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
    assert target.stats == TimingStats(1, 1.5, 1.5, 1.5)


def test_reporter_failure_cannot_mask_target_exception_and_stats_record() -> None:
    readings: Iterator[float] = iter((3.0, 4.5))
    reports: list[Timing] = []
    target_error: RuntimeError = RuntimeError("target failed")
    reporter_error: ValueError = ValueError("reporter failed")

    def failing_reporter(timing: Timing) -> None:
        reports.append(timing)
        raise reporter_error

    @track(clock=readings.__next__, reporter=failing_reporter)
    def target() -> None:
        raise target_error

    with pytest.raises(RuntimeError) as caught:
        target()

    assert caught.value is target_error
    assert target.stats == TimingStats(1, 1.5, 1.5, 1.5)
    assert reports == [Timing(label="target", elapsed=1.5, failed=True)]


def test_starting_clock_failure_prevents_target_and_stats() -> None:
    target_calls: list[None] = []
    clock_error: ValueError = ValueError("clock failed")

    def failing_clock() -> float:
        raise clock_error

    @track(clock=failing_clock)
    def target() -> None:
        target_calls.append(None)

    with pytest.raises(ValueError) as caught:
        target()

    assert caught.value is clock_error
    assert target_calls == []
    assert target.stats == TimingStats()


@pytest.mark.parametrize("target_fails", (False, True))
def test_ending_clock_failure_means_no_duration_or_stats(
    target_fails: bool,
) -> None:
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
    def target() -> str:
        if target_fails:
            raise target_error
        return "result"

    expected_error: BaseException = target_error if target_fails else clock_error
    with pytest.raises(type(expected_error)) as caught:
        target()

    assert caught.value is expected_error
    assert clock_calls == [1, 2]
    assert target.stats == TimingStats()
    assert reports == []


def test_timing_stats_are_mutable_and_record_exact_aggregates() -> None:
    stats: TimingStats = TimingStats()

    stats.record(2.0)
    stats.record(0.5)

    assert stats == TimingStats(
        count=2,
        total=2.5,
        minimum=0.5,
        maximum=2.0,
    )
    assert stats.average == 1.25

    stats.count = 5
    stats.total = 10.0

    assert stats.average == 2.0


def test_track_return_is_assignable_to_matching_callable() -> None:
    readings: Iterator[float] = iter((1.0, 2.0))

    def identity(value: int) -> int:
        return value

    tracked_identity: Callable[[int], int] = track(
        identity,
        clock=readings.__next__,
        reporter=lambda timing: None,
    )

    assert tracked_identity(42) == 42
