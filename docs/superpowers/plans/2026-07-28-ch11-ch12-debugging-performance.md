# Chapters 11-12 Debugging and Performance Implementation

**For agentic workers:** REQUIRED SUB-SKILL: Use
`superpowers:subagent-driven-development` (recommended) or
`superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Deliver six deterministic, typed debugging/performance utilities with
focused tests that do not depend on machine speed or process RSS.

**Architecture:** Chapter 11 wraps standard-library diagnostics in reusable
APIs: delayed faulthandler dumps, injected-clock timing, and line-level trace
counts. Chapter 12 uses stateful callable objects for memory/runtime monitoring
and a compositional weak-reference instance manager. Clocks and memory samplers
are injected in unit tests; one bounded subprocess verifies the real
faulthandler path.

**Tech Stack:** Python 3.10 standard library, pytest, Ruff, Pyrefly, mypy,
Pyright

---

## File map and public APIs

- CH11 Exercise 1: `run_with_timeout_diagnostics`
- CH11 Exercise 2: `TimedResult`, `CallTimer`, `measure_call`
- CH11 Exercise 3: `SourceLocation`, `ExecutionCounts`, `count_executions`
- CH12 Exercise 1: `MemoryGrowthMonitor`, `monitor_memory_growth`
- CH12 Exercise 2: `RuntimeStats`, `RuntimeMonitor`, `monitor_runtime`
- CH12 Exercise 3: `InstanceManager`
- Every exercise gains the standard `__init__.py`, `README.rst`,
  `solution_00.py`, and `test_solution_00.py` contract.

### Task 1: Dump a stalled stack after a timeout

**Files:**

- Create: `CH_11_debugging/exercise_01/__init__.py`
- Create: `CH_11_debugging/exercise_01/solution_00.py`
- Create: `CH_11_debugging/exercise_01/test_solution_00.py`
- Create: `CH_11_debugging/exercise_01/README.rst`

- [ ] **Step 1: Write cancellation, validation, and real subprocess tests**

```python
# CH_11_debugging/exercise_01/test_solution_00.py
import faulthandler
import subprocess
import sys

import pytest

from CH_11_debugging.exercise_01.solution_00 import (
    run_with_timeout_diagnostics,
)


def test_diagnostic_is_cancelled_when_function_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def schedule(
        timeout: float,
        repeat: bool = False,
        file: object | None = None,
        exit: bool = False,
    ) -> None:
        del timeout, repeat, file, exit
        events.append("scheduled")

    def cancel() -> None:
        events.append("cancelled")

    monkeypatch.setattr(faulthandler, "dump_traceback_later", schedule)
    monkeypatch.setattr(faulthandler, "cancel_dump_traceback_later", cancel)

    def fail() -> None:
        raise LookupError("boom")

    with pytest.raises(LookupError, match="boom"):
        run_with_timeout_diagnostics(fail, 0.1)

    assert events == ["scheduled", "cancelled"]


def test_timeout_must_be_positive() -> None:
    with pytest.raises(ValueError, match="timeout must be positive"):
        run_with_timeout_diagnostics(lambda: None, 0.0)


def test_real_timeout_prints_stalled_function() -> None:
    source: str = """
import time
from CH_11_debugging.exercise_01.solution_00 import (
    run_with_timeout_diagnostics,
)

def stalled() -> None:
    time.sleep(0.10)

run_with_timeout_diagnostics(stalled, 0.01)
"""
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", source],
        text=True,
        capture_output=True,
        check=False,
        timeout=2,
    )

    assert completed.returncode == 0
    assert "Timeout" in completed.stderr
    assert "stalled" in completed.stderr
```

- [ ] **Step 2: Run the missing-module test**

Run:

```bash
uv run pytest CH_11_debugging/exercise_01/test_solution_00.py -v
```

Expected: FAIL during collection with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the generic diagnostic wrapper**

```python
# CH_11_debugging/exercise_01/solution_00.py
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
    """Run a callable and dump all thread stacks if it exceeds timeout."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    faulthandler.dump_traceback_later(timeout, repeat=False)
    try:
        return function(*args, **kwargs)
    finally:
        faulthandler.cancel_dump_traceback_later()


def main() -> None:
    """Demonstrate a fast call that cancels its scheduled dump."""
    value: str = run_with_timeout_diagnostics(lambda: "finished", 1.0)
    print(value)


if __name__ == "__main__":
    main()
```

The function diagnoses but deliberately does not terminate the callable.
Aborting arbitrary threads would be unsafe; the README must make this boundary
explicit.

- [ ] **Step 4: Verify, document, and commit**

Run:

```bash
uv run pytest CH_11_debugging/exercise_01/test_solution_00.py -v
uv run ruff check CH_11_debugging/exercise_01
uv run pyrefly check CH_11_debugging/exercise_01
uv run mypy CH_11_debugging/exercise_01
uv run pyright CH_11_debugging/exercise_01
```

Expected: three tests pass and all checks exit zero.

README: repeat the timeout/stall question; explain diagnostic-only semantics,
positive timeout, exception propagation, stdlib/pytest dependencies, module
and test commands, and pinned upstream `T_06_stack.py` plus
`T_07_faulthandler.py`. Commit:

```bash
git add CH_11_debugging/exercise_01
git commit -m "feat: add stalled-call diagnostics exercise"
```

### Task 2: Measure one call with an injectable monotonic clock

**Files:**

- Create: `CH_11_debugging/exercise_02/__init__.py`
- Create: `CH_11_debugging/exercise_02/solution_00.py`
- Create: `CH_11_debugging/exercise_02/test_solution_00.py`
- Create: `CH_11_debugging/exercise_02/README.rst`

- [ ] **Step 1: Write deterministic timing and propagation tests**

```python
# CH_11_debugging/exercise_02/test_solution_00.py
from collections.abc import Callable, Iterator

import pytest

from CH_11_debugging.exercise_02.solution_00 import CallTimer, TimedResult


def clock_from(values: list[float]) -> Callable[[], float]:
    iterator: Iterator[float] = iter(values)
    return iterator.__next__


def test_measure_returns_value_and_elapsed_seconds() -> None:
    timer: CallTimer = CallTimer(clock_from([10.0, 10.25]))

    result: TimedResult[int] = timer.measure(lambda value: value + 1, 4)

    assert result == TimedResult(value=5, seconds=0.25)


def test_measure_propagates_function_failure() -> None:
    timer: CallTimer = CallTimer(clock_from([1.0]))

    def fail() -> None:
        raise RuntimeError("failed")

    with pytest.raises(RuntimeError, match="failed"):
        timer.measure(fail)


def test_measure_rejects_clock_moving_backwards() -> None:
    timer: CallTimer = CallTimer(clock_from([5.0, 4.0]))

    with pytest.raises(ValueError, match="clock moved backwards"):
        timer.measure(lambda: None)
```

- [ ] **Step 2: Confirm the missing implementation fails**

Run:

```bash
uv run pytest CH_11_debugging/exercise_02/test_solution_00.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the result and timer types**

```python
# CH_11_debugging/exercise_02/solution_00.py
"""Measure callable duration without coupling tests to wall-clock speed."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, ParamSpec, TypeVar

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")


@dataclass(frozen=True)
class TimedResult(Generic[Result]):
    """A callable's return value and elapsed monotonic seconds."""

    value: Result
    seconds: float


class CallTimer:
    """Measure calls with an injectable monotonic clock."""

    def __init__(
        self,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._clock: Callable[[], float] = clock

    def measure(
        self,
        function: Callable[Parameters, Result],
        *args: Parameters.args,
        **kwargs: Parameters.kwargs,
    ) -> TimedResult[Result]:
        """Run a callable once and return its value and duration."""
        started: float = self._clock()
        value: Result = function(*args, **kwargs)
        finished: float = self._clock()
        seconds: float = finished - started
        if seconds < 0:
            raise ValueError("clock moved backwards")
        return TimedResult(value=value, seconds=seconds)


def measure_call(
    function: Callable[Parameters, Result],
    *args: Parameters.args,
    **kwargs: Parameters.kwargs,
) -> TimedResult[Result]:
    """Measure a callable with `time.perf_counter`."""
    return CallTimer().measure(function, *args, **kwargs)


if __name__ == "__main__":
    print(measure_call(sum, [1, 2, 3]))
```

- [ ] **Step 4: Verify, document, and commit**

Run:

```bash
uv run pytest CH_11_debugging/exercise_02/test_solution_00.py -v
uv run ruff check CH_11_debugging/exercise_02
uv run pyrefly check CH_11_debugging/exercise_02
uv run mypy CH_11_debugging/exercise_02
uv run pyright CH_11_debugging/exercise_02
```

Expected: three tests pass with zero findings.

README: exact duration prompt, monotonic/injected clock decision, failed-call
behavior, dependencies and run commands, pinned upstream
`CH_11_debugging/T_02_selective_trace.py`. Commit:

```bash
git add CH_11_debugging/exercise_02
git commit -m "feat: add execution duration exercise"
```

### Task 3: Count executed source lines

**Files:**

- Create: `CH_11_debugging/exercise_03/__init__.py`
- Create: `CH_11_debugging/exercise_03/solution_00.py`
- Create: `CH_11_debugging/exercise_03/test_solution_00.py`
- Create: `CH_11_debugging/exercise_03/README.rst`
- Modify: `CH_11_debugging/README.rst`

- [ ] **Step 1: Write a line-frequency test that rejects call-only counters**

```python
# CH_11_debugging/exercise_03/test_solution_00.py
import inspect

import pytest

from CH_11_debugging.exercise_03.solution_00 import (
    ExecutionCounts,
    count_executions,
)


def repeated(total: int) -> int:
    value: int = 0
    for number in range(total):
        value += number
    return value


def test_count_executions_reports_loop_line_frequency() -> None:
    source_lines, first_line = inspect.getsourcelines(repeated)
    offset: int = next(
        index
        for index, line in enumerate(source_lines)
        if "value += number" in line
    )
    loop_line: int = first_line + offset

    profile: ExecutionCounts[int] = count_executions(repeated, 4)

    assert profile.result == 6
    assert profile.counts[loop_line] == 4


def test_count_executions_propagates_failure() -> None:
    def fail() -> None:
        raise LookupError("boom")

    with pytest.raises(LookupError, match="boom"):
        count_executions(fail)
```

- [ ] **Step 2: Run and confirm the module is absent**

Run:

```bash
uv run pytest CH_11_debugging/exercise_03/test_solution_00.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement source-file-filtered trace counts**

```python
# CH_11_debugging/exercise_03/solution_00.py
"""Count how often each source line in a callable's file executes."""

import inspect
import trace
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, ParamSpec, TypeVar, cast

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")
SourceLocation = tuple[str, int]


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
    filename: str | None = inspect.getsourcefile(function)
    if filename is None:
        raise ValueError("function has no inspectable source file")
    tracer: trace.Trace = trace.Trace(count=True, trace=False)
    result: Result = tracer.runfunc(function, *args, **kwargs)
    raw: dict[SourceLocation, int] = cast(
        dict[SourceLocation, int],
        tracer.results().counts,
    )
    counts: dict[int, int] = {
        line_number: count
        for (source_file, line_number), count in raw.items()
        if source_file == filename
    }
    return ExecutionCounts(result=result, counts=counts)
```

- [ ] **Step 4: Verify, document, index, and commit**

Run:

```bash
uv run pytest CH_11_debugging/exercise_03/test_solution_00.py -v
uv run ruff check CH_11_debugging/exercise_03
uv run pyrefly check CH_11_debugging/exercise_03
uv run mypy CH_11_debugging/exercise_03
uv run pyright CH_11_debugging/exercise_03
```

Expected: the loop line count is four and every command exits zero.

README: exact execution-count prompt, source-file filtering, exception
propagation, stdlib/pytest dependencies, commands, and pinned upstream
`T_02_selective_trace.py` plus `T_03_filename_trace.py`.

Replace `CH_11_debugging/README.rst` with:

```rst
Chapter 11 - debugging
======================

1. `Stalled-call diagnostics <exercise_01/>`_
2. `Execution duration <exercise_02/>`_
3. `Line execution counts <exercise_03/>`_
```

Commit:

```bash
git add CH_11_debugging/exercise_03 CH_11_debugging/README.rst
git commit -m "feat: add line execution count exercise"
```

### Task 4: Warn when sampled memory grows

**Files:**

- Create: `CH_12_performance/exercise_01/__init__.py`
- Create: `CH_12_performance/exercise_01/solution_00.py`
- Create: `CH_12_performance/exercise_01/test_solution_00.py`
- Create: `CH_12_performance/exercise_01/README.rst`

- [ ] **Step 1: Write deterministic sampler tests**

```python
# CH_12_performance/exercise_01/test_solution_00.py
from collections.abc import Callable, Iterator

import pytest

from CH_12_performance.exercise_01.solution_00 import monitor_memory_growth


def sampler(values: list[int]) -> Callable[[], int]:
    iterator: Iterator[int] = iter(values)
    return iterator.__next__


def test_warns_only_after_growth_above_tolerance() -> None:
    @monitor_memory_growth(
        sampler=sampler([100, 104, 120]),
        tolerance_bytes=5,
    )
    def value() -> int:
        return 7

    assert value() == 7
    assert value() == 7
    with pytest.warns(ResourceWarning, match="grew by 16 bytes"):
        assert value() == 7


def test_failed_call_does_not_consume_a_sample() -> None:
    samples: Callable[[], int] = sampler([10])

    @monitor_memory_growth(sampler=samples)
    def fail() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        fail()
```

- [ ] **Step 2: Run and observe missing module**

Run:

```bash
uv run pytest CH_12_performance/exercise_01/test_solution_00.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement the stateful decorator**

```python
# CH_12_performance/exercise_01/solution_00.py
"""Warn when a successful call's sampled memory grows."""

import tracemalloc
import warnings
from collections.abc import Callable
from typing import Generic, ParamSpec, TypeVar

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")


def _traced_bytes() -> int:
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    current: int
    current, _ = tracemalloc.get_traced_memory()
    return current


class MemoryGrowthMonitor(Generic[Parameters, Result]):
    """Callable wrapper retaining the previous successful sample."""

    def __init__(
        self,
        function: Callable[Parameters, Result],
        sampler: Callable[[], int],
        tolerance_bytes: int,
    ) -> None:
        self._function: Callable[Parameters, Result] = function
        self._sampler: Callable[[], int] = sampler
        self._tolerance_bytes: int = tolerance_bytes
        self._previous: int | None = None

    def __call__(
        self,
        *args: Parameters.args,
        **kwargs: Parameters.kwargs,
    ) -> Result:
        value: Result = self._function(*args, **kwargs)
        current: int = self._sampler()
        if self._previous is not None:
            growth: int = current - self._previous
            if growth > self._tolerance_bytes:
                warnings.warn(
                    f"sampled memory grew by {growth} bytes",
                    ResourceWarning,
                    stacklevel=2,
                )
        self._previous = current
        return value


def monitor_memory_growth(
    *,
    sampler: Callable[[], int] = _traced_bytes,
    tolerance_bytes: int = 0,
) -> Callable[
    [Callable[Parameters, Result]],
    MemoryGrowthMonitor[Parameters, Result],
]:
    """Create a monitor decorator with an injectable sampler."""
    if tolerance_bytes < 0:
        raise ValueError("tolerance_bytes must not be negative")

    def decorate(
        function: Callable[Parameters, Result],
    ) -> MemoryGrowthMonitor[Parameters, Result]:
        return MemoryGrowthMonitor(function, sampler, tolerance_bytes)

    return decorate
```

- [ ] **Step 4: Verify, document, and commit**

Run:

```bash
uv run pytest CH_12_performance/exercise_01/test_solution_00.py -v
uv run ruff check CH_12_performance/exercise_01
uv run pyrefly check CH_12_performance/exercise_01
uv run mypy CH_12_performance/exercise_01
uv run pyright CH_12_performance/exercise_01
```

Expected: both tests pass without real-memory assumptions.

README: exact memory decorator prompt, successful-call sampling, tolerance and
tracemalloc default, dependencies/commands, pinned upstream
`T_11_tracemalloc.py`, `T_12_memory_profiler.py`, and
`T_13_memory_leaks.py`. Commit:

```bash
git add CH_12_performance/exercise_01
git commit -m "feat: add memory growth monitor exercise"
```

### Task 5: Warn on runtime deviation and expose a running average

**Files:**

- Create: `CH_12_performance/exercise_02/__init__.py`
- Create: `CH_12_performance/exercise_02/solution_00.py`
- Create: `CH_12_performance/exercise_02/test_solution_00.py`
- Create: `CH_12_performance/exercise_02/README.rst`

- [ ] **Step 1: Write injected-clock deviation tests**

```python
# CH_12_performance/exercise_02/test_solution_00.py
from collections.abc import Callable, Iterator

import pytest

from CH_12_performance.exercise_02.solution_00 import monitor_runtime


def clock(values: list[float]) -> Callable[[], float]:
    iterator: Iterator[float] = iter(values)
    return iterator.__next__


def test_warns_against_previous_running_average() -> None:
    @monitor_runtime(clock=clock([0.0, 1.0, 2.0, 4.0]), max_deviation=0.25)
    def operation() -> str:
        return "ok"

    assert operation() == "ok"
    with pytest.warns(RuntimeWarning, match="deviated"):
        assert operation() == "ok"

    assert operation.stats.calls == 2
    assert operation.stats.average_seconds == pytest.approx(1.5)


def test_invalid_deviation_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_deviation must not be negative"):
        monitor_runtime(max_deviation=-0.1)
```

- [ ] **Step 2: Run and confirm failure**

Run:

```bash
uv run pytest CH_12_performance/exercise_02/test_solution_00.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement the running statistics monitor**

```python
# CH_12_performance/exercise_02/solution_00.py
"""Warn when call duration differs substantially from prior runs."""

import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, ParamSpec, TypeVar

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")


@dataclass(frozen=True)
class RuntimeStats:
    """Successful-call runtime statistics."""

    calls: int
    total_seconds: float

    @property
    def average_seconds(self) -> float:
        return self.total_seconds / self.calls if self.calls else 0.0


class RuntimeMonitor(Generic[Parameters, Result]):
    """Callable wrapper comparing each duration to the prior average."""

    def __init__(
        self,
        function: Callable[Parameters, Result],
        clock: Callable[[], float],
        max_deviation: float,
    ) -> None:
        self._function: Callable[Parameters, Result] = function
        self._clock: Callable[[], float] = clock
        self._max_deviation: float = max_deviation
        self.stats: RuntimeStats = RuntimeStats(0, 0.0)

    def __call__(
        self,
        *args: Parameters.args,
        **kwargs: Parameters.kwargs,
    ) -> Result:
        started: float = self._clock()
        value: Result = self._function(*args, **kwargs)
        duration: float = self._clock() - started
        if duration < 0:
            raise ValueError("clock moved backwards")
        previous_average: float = self.stats.average_seconds
        if (
            self.stats.calls > 0
            and previous_average > 0
            and abs(duration - previous_average)
            > previous_average * self._max_deviation
        ):
            warnings.warn(
                "runtime deviated from the previous average",
                RuntimeWarning,
                stacklevel=2,
            )
        self.stats = RuntimeStats(
            self.stats.calls + 1,
            self.stats.total_seconds + duration,
        )
        return value


def monitor_runtime(
    *,
    clock: Callable[[], float] = time.perf_counter,
    max_deviation: float = 0.25,
) -> Callable[
    [Callable[Parameters, Result]],
    RuntimeMonitor[Parameters, Result],
]:
    """Create a runtime monitor decorator."""
    if max_deviation < 0:
        raise ValueError("max_deviation must not be negative")

    def decorate(
        function: Callable[Parameters, Result],
    ) -> RuntimeMonitor[Parameters, Result]:
        return RuntimeMonitor(function, clock, max_deviation)

    return decorate
```

- [ ] **Step 4: Verify, document, and commit**

Run:

```bash
uv run pytest CH_12_performance/exercise_02/test_solution_00.py -v
uv run ruff check CH_12_performance/exercise_02
uv run pyrefly check CH_12_performance/exercise_02
uv run mypy CH_12_performance/exercise_02
uv run pyright CH_12_performance/exercise_02
```

Expected: two tests pass and all checks exit zero.
README: exact prompt, prior-average and successful-call semantics, injected
clock, dependencies/commands, pinned upstream `T_00_timeit.py` and
`T_06_selective_profiling.py`. Commit:

```bash
git add CH_12_performance/exercise_02
git commit -m "feat: add runtime deviation monitor exercise"
```

### Task 6: Track live instances without keeping them alive

**Files:**

- Create: `CH_12_performance/exercise_03/__init__.py`
- Create: `CH_12_performance/exercise_03/solution_00.py`
- Create: `CH_12_performance/exercise_03/test_solution_00.py`
- Create: `CH_12_performance/exercise_03/README.rst`
- Modify: `CH_12_performance/README.rst`

- [ ] **Step 1: Write live-count, warning, and collection tests**

```python
# CH_12_performance/exercise_03/test_solution_00.py
import gc

import pytest

from CH_12_performance.exercise_03.solution_00 import InstanceManager


class Resource:
    def __init__(self, name: str) -> None:
        self.name: str = name


def test_warns_above_limit_and_releases_collected_instances() -> None:
    manager: InstanceManager[Resource] = InstanceManager(
        Resource,
        max_instances=1,
    )
    first: Resource = manager.create("first")
    with pytest.warns(ResourceWarning, match="2 live Resource instances"):
        second: Resource = manager.create("second")

    assert manager.live_count == 2
    del first
    gc.collect()
    assert manager.live_count == 1
    assert second.name == "second"


def test_invalid_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_instances must be positive"):
        InstanceManager(Resource, max_instances=0)


def test_non_weak_referenceable_instance_is_rejected() -> None:
    class Slotted:
        __slots__: tuple[str, ...] = ()

    manager: InstanceManager[Slotted] = InstanceManager(
        Slotted,
        max_instances=1,
    )

    with pytest.raises(TypeError, match="instances must support weak references"):
        manager.create()
```

- [ ] **Step 2: Run and confirm failure**

Run:

```bash
uv run pytest CH_12_performance/exercise_03/test_solution_00.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement a compositional weak-reference manager**

```python
# CH_12_performance/exercise_03/solution_00.py
"""Track live instances created for one class without retaining them."""

import warnings
import weakref
from typing import Generic, TypeVar

Instance = TypeVar("Instance")


class InstanceManager(Generic[Instance]):
    """Construct and weakly track instances of one class."""

    def __init__(
        self,
        instance_type: type[Instance],
        *,
        max_instances: int,
    ) -> None:
        if max_instances <= 0:
            raise ValueError("max_instances must be positive")
        self._instance_type: type[Instance] = instance_type
        self._max_instances: int = max_instances
        self._references: list[weakref.ReferenceType[Instance]] = []

    def _discard_dead(self) -> None:
        self._references = [
            reference
            for reference in self._references
            if reference() is not None
        ]

    @property
    def live_count(self) -> int:
        """Return the number of tracked instances still alive."""
        self._discard_dead()
        return len(self._references)

    def create(self, *args: object, **kwargs: object) -> Instance:
        """Construct, track, and return an instance."""
        instance: Instance = self._instance_type(*args, **kwargs)
        try:
            reference: weakref.ReferenceType[Instance] = weakref.ref(instance)
        except TypeError:
            raise TypeError(
                "instances must support weak references"
            ) from None
        self._discard_dead()
        self._references.append(reference)
        count: int = len(self._references)
        if count > self._max_instances:
            warnings.warn(
                f"{count} live {self._instance_type.__name__} instances",
                ResourceWarning,
                stacklevel=2,
            )
        return instance
```

- [ ] **Step 4: Verify, document, index, and commit**

Run:

```bash
uv run pytest CH_11_debugging CH_12_performance -v
uv run ruff format --check CH_11_debugging CH_12_performance
uv run ruff check CH_11_debugging CH_12_performance
uv run pyrefly check CH_11_debugging CH_12_performance
uv run mypy CH_11_debugging CH_12_performance
uv run pyright CH_11_debugging CH_12_performance
```

Expected: all six exercise suites pass with no timing/RSS flakes and all
quality commands exit zero.

README: exact instance-manager prompt; manager-created-instance scope, weak
reference collection, positive limit and non-weakref error; dependencies and
commands; pinned upstream `T_13_memory_leaks.py`,
`T_15_garbage_collector_viewing.py`, and `T_16_weak_references.py`.

Replace `CH_12_performance/README.rst` with:

```rst
Chapter 12 - performance
========================

1. `Memory-growth monitor <exercise_01/>`_
2. `Runtime-deviation monitor <exercise_02/>`_
3. `Live-instance manager <exercise_03/>`_
```

Commit:

```bash
git add CH_12_performance/exercise_03 CH_12_performance/README.rst
git commit -m "feat: add live instance manager exercise"
```

### Task 7: Packet self-review

**Files:**

- Review: `CH_11_debugging/`
- Review: `CH_12_performance/`

- [ ] **Step 1: Verify directory contracts and placeholder absence**

Run:

```bash
find CH_11_debugging CH_12_performance -maxdepth 2 -type f | sort
```

Expected: each exercise contains all four contract files and placeholder scan
returns no matches.

- [ ] **Step 2: Verify failure propagation explicitly**

Run:

```bash
uv run pytest CH_11_debugging CH_12_performance -v -k "failure or raises or rejects"
```

Expected: all selected failure-path tests pass; no worker, sampler, clock, or
callable exception is swallowed.

- [ ] **Step 3: Confirm ownership isolation**

Run:

```bash
git status --short
git diff --stat master -- CH_11_debugging CH_12_performance
```

Expected: no uncommitted packet changes and no files outside the owned packet
or plan were modified.
