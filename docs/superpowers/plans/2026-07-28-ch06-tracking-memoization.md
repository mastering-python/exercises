# Chapter 6 Tracking and Memoization Implementation

**For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Rewrite Chapter 6 exercises 1–4 as deterministic, typed decorators with complete timing and cache contracts.

**Architecture:** Timing decorators accept injectable monotonic clocks and structured reporters, so tests never sleep. Memoization converts supported mutable containers into type-tagged immutable keys; exercise 3 deliberately stores those keys in a module cache, while exercise 4 advances the design to an independently inspectable cache per decorated function.

**Tech Stack:** Python 3.10 standard library, `ParamSpec`, pytest.

---

## Exact Canonical File Addition

The Chapter 6 exercise 4 task uses shortened filenames within its exercise
directory. Their exact paths are:

- `CH_06_decorators/exercise_04/README.rst`
- `CH_06_decorators/exercise_04/solution_00.py`

## Scope and ownership

Only modify:

- `CH_06_decorators/exercise_01/{README.rst,solution_00.py,test_solution_00.py}`
- `CH_06_decorators/exercise_02/{README.rst,solution_00.py,test_solution_00.py}`
- `CH_06_decorators/exercise_03/{README.rst,solution_00.py,test_solution_00.py}`
- `CH_06_decorators/exercise_04/{README.rst,solution_00.py,test_solution_00.py}`

Keep existing initializers. Do not modify `CH_06_decorators/README.rst`; the Chapter 6 exercises 5–7 packet owns that shared index. Do not add third-party runtime dependencies.

Exercise READMEs must cite the relevant immutable book source:

- `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_03_chaining_decorators.rst`
- `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_05_memoization.rst`

## Task 1: Track every function execution

**Public API:**

- `Timing(label: str, elapsed: float, failed: bool)`.
- `track(function=None, *, label=None, clock=time.perf_counter, reporter=print_timing)`.
- Decorated functions preserve signature metadata and return/raise exactly as the wrapped function.

- [ ] **Step 1: Write failing deterministic tests**

Create `test_solution_00.py`:

```python
from collections.abc import Iterator

import pytest

from CH_06_decorators.exercise_01.solution_00 import Timing, track


def clock(values: list[float]) -> Iterator[float]:
    yield from values


def test_track_reports_elapsed_time_and_preserves_result() -> None:
    readings: Iterator[float] = clock([10.0, 10.25])
    reports: list[Timing] = []

    @track(
        label="addition",
        clock=lambda: next(readings),
        reporter=reports.append,
    )
    def add(left: int, right: int) -> int:
        return left + right

    assert add(2, 3) == 5
    assert add.__name__ == "add"
    assert reports == [Timing("addition", 0.25, False)]


def test_track_reports_and_propagates_failure() -> None:
    readings: Iterator[float] = clock([1.0, 1.5])
    reports: list[Timing] = []

    @track(clock=lambda: next(readings), reporter=reports.append)
    def fail() -> None:
        raise LookupError("broken")

    with pytest.raises(LookupError, match="broken"):
        fail()
    assert reports == [Timing("fail", 0.5, True)]
```

Also test direct `@track` usage, default label selection, positional/keyword forwarding, and the default printable report format.

- [ ] **Step 2: Run and verify red**

Run: `uv run pytest CH_06_decorators/exercise_01/test_solution_00.py -v`

Expected: current `track` has no injectable clock/reporter or structured `Timing`.

- [ ] **Step 3: Implement the typed decorator**

Use overloads for direct and configured decorator forms. The core implementation is:

```python
@dataclass(frozen=True)
class Timing:
    label: str
    elapsed: float
    failed: bool


def print_timing(timing: Timing) -> None:
    status: str = "failed" if timing.failed else "completed"
    print(f"{timing.label} {status} in {timing.elapsed:.6f}s")


def _decorate(
    function: Callable[P, R],
    *,
    label: str | None,
    clock: Callable[[], float],
    reporter: Callable[[Timing], None],
) -> Callable[P, R]:
    selected_label: str = function.__name__ if label is None else label

    @functools.wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        started: float = clock()
        failed: bool = True
        try:
            result: R = function(*args, **kwargs)
            failed = False
            return result
        finally:
            reporter(Timing(selected_label, clock() - started, failed))

    return wrapped
```

`track` must call `_decorate` immediately when `function` is not `None`, otherwise return a decorator closure. Never catch the wrapped exception.

- [ ] **Step 4: Add README, verify, and commit**

README repeats question 1 exactly, explains monotonic timing, failure reporting, clock/reporter injection, no-sleep tests, no extra dependencies, and shows:

```console
uv run python -m CH_06_decorators.exercise_01.solution_00
uv run pytest CH_06_decorators/exercise_01 -v
```

Run: `uv run pytest CH_06_decorators/exercise_01 -v`

Expected: pass.

```bash
git add CH_06_decorators/exercise_01/README.rst CH_06_decorators/exercise_01/solution_00.py CH_06_decorators/exercise_01/test_solution_00.py
git commit -m "feat(ch06): track deterministic call timing"
```

## Task 2: Aggregate min/max/average/count

**Public API:**

- Mutable `TimingStats(count, total, minimum, maximum)` with `average`.
- `TrackedCallable[P, R]` protocol exposing `stats`, `print_stats()`, and `__call__`.
- Exercise-local `track` with the same configuration arguments as Exercise 1.

Record failed calls as executions and propagate their exceptions. Before any call, min/max/average are `None`.

- [ ] **Step 1: Write failing tests**

```python
from collections.abc import Iterator

from CH_06_decorators.exercise_02.solution_00 import TimingStats, track


def test_track_aggregates_exact_injected_durations() -> None:
    readings: Iterator[float] = iter([0.0, 1.0, 10.0, 13.0])

    @track(clock=lambda: next(readings), reporter=lambda timing: None)
    def identity(value: int) -> int:
        return value

    assert identity(1) == 1
    assert identity(2) == 2
    assert identity.stats == TimingStats(
        count=2,
        total=4.0,
        minimum=1.0,
        maximum=3.0,
    )
    assert identity.stats.average == 2.0
```

Also test initial empty stats, one failed call, independent decorators, and exact `print_stats()` output through `capsys`.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_06_decorators/exercise_02/test_solution_00.py -v`

Expected: current implementation uses datetimes/random sleeps and does not expose a typed stats contract.

- [ ] **Step 3: Implement**

Reuse Exercise 1's `Timing`; define:

```python
@dataclass
class TimingStats:
    count: int = 0
    total: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    @property
    def average(self) -> float | None:
        return None if self.count == 0 else self.total / self.count

    def record(self, elapsed: float) -> None:
        self.count += 1
        self.total += elapsed
        self.minimum = elapsed if self.minimum is None else min(self.minimum, elapsed)
        self.maximum = elapsed if self.maximum is None else max(self.maximum, elapsed)
```

The wrapper's `finally` block creates one `Timing`, records it, and forwards it to the configured reporter. Attach `stats` and a zero-argument `print_stats` function to the wrapped callable, then `cast(TrackedCallable[P, R], wrapped)` instead of using broad ignores. Print all fields with six decimal places and print `n/a` for empty min/max/average.

- [ ] **Step 4: Document, verify, commit**

README states failed calls count, empty-stat semantics, units in seconds, and deterministic injection.

Run: `uv run pytest CH_06_decorators/exercise_02 -v`

Expected: pass.

```bash
git add CH_06_decorators/exercise_02/README.rst CH_06_decorators/exercise_02/solution_00.py CH_06_decorators/exercise_02/test_solution_00.py
git commit -m "feat(ch06): aggregate tracked call statistics"
```

## Task 3: Memoize mutable container arguments

**Public API:** module-level `cache`, `memoize(function)`, and private `_freeze(value)` used by the decorator.

**Behavioral decisions:** Support nested tuples, lists, dicts, sets, and frozensets; preserve type distinctions; dictionary/set order does not affect keys; cycles raise `ValueError("cyclic argument")`; unsupported unhashable objects raise `TypeError`; exceptions are never cached.

- [ ] **Step 1: Write failing cache-contract tests**

```python
import pytest

from CH_06_decorators.exercise_03.solution_00 import cache, memoize


def test_equivalent_unhashable_arguments_hit_one_cache_entry() -> None:
    cache.clear()
    calls: list[int] = []

    @memoize
    def total(values: list[int], *, weights: dict[str, int]) -> int:
        calls.append(1)
        return sum(values) + sum(weights.values())

    assert total([1, 2], weights={"a": 3, "b": 4}) == 10
    assert total([1, 2], weights={"b": 4, "a": 3}) == 10
    assert calls == [1]


def test_cyclic_arguments_fail_explicitly() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)

    @memoize
    def identity(value: object) -> object:
        return value

    with pytest.raises(ValueError, match="cyclic argument"):
        identity(cyclic)
```

Also test list versus tuple separation, unordered nested sets, different functions with equal arguments, kwargs, and a function that raises twice.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_06_decorators/exercise_03/test_solution_00.py -v`

Expected: current implementation still uses raw unhashable arguments as the cache key.

- [ ] **Step 3: Implement structural freezing and global caching**

Use type tags so structurally similar container types cannot collide:

```python
def _freeze(value: object, active: set[int] | None = None) -> Hashable:
    seen: set[int] = set() if active is None else active
    if isinstance(value, (str, bytes, int, float, bool, type(None))):
        return ("scalar", type(value), value)
    if isinstance(value, Hashable) and not isinstance(
        value, (tuple, frozenset)
    ):
        return ("hashable", type(value), value)
    identity: int = id(value)
    if identity in seen:
        raise ValueError("cyclic argument")
    seen.add(identity)
    try:
        if isinstance(value, tuple):
            return ("tuple", tuple(_freeze(item, seen) for item in value))
        if isinstance(value, list):
            return ("list", tuple(_freeze(item, seen) for item in value))
        if isinstance(value, dict):
            return (
                "dict",
                frozenset(
                    (_freeze(key, seen), _freeze(item, seen))
                    for key, item in value.items()
                ),
            )
        if isinstance(value, (set, frozenset)):
            return (
                type(value).__name__,
                frozenset(_freeze(item, seen) for item in value),
            )
        raise TypeError(f"unsupported unhashable argument: {type(value).__name__}")
    finally:
        seen.remove(identity)
```

`memoize` computes `(function, _freeze(args), _freeze(kwargs))`, calls the function only when absent, and stores the result only after a successful return. Use a private sentinel so cached `None` is distinguishable from a miss.

- [ ] **Step 4: Document, verify, commit**

README lists supported containers, cycles/errors, global-cache lifetime, exception behavior, and `uv run` commands.

Run: `uv run pytest CH_06_decorators/exercise_03 -v`

Expected: pass.

```bash
git add CH_06_decorators/exercise_03/README.rst CH_06_decorators/exercise_03/solution_00.py CH_06_decorators/exercise_03/test_solution_00.py
git commit -m "feat(ch06): memoize unhashable arguments"
```

## Task 4: Give each function its own cache

**Public API:** `MemoizedCallable[P, R]` protocol exposing `cache`, `cache_clear()`, and call behavior; `memoize(function) -> MemoizedCallable[P, R]`.

- [ ] **Step 1: Write failing tests**

```python
from CH_06_decorators.exercise_04.solution_00 import memoize


def test_each_decorated_function_owns_and_clears_its_cache() -> None:
    calls: list[str] = []

    @memoize
    def first(values: list[int]) -> int:
        calls.append("first")
        return sum(values)

    @memoize
    def second(values: list[int]) -> int:
        calls.append("second")
        return sum(values)

    assert first([1, 2]) == second([1, 2]) == 3
    assert first.cache is not second.cache
    assert calls == ["first", "second"]
    first([1, 2])
    first.cache_clear()
    first([1, 2])
    assert calls == ["first", "second", "first"]
    assert first.__name__ == "first"
```

Also test kwargs/order, cached `None`, exception non-caching, and unsupported/cyclic arguments inherited from Exercise 3's freezer.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_06_decorators/exercise_04/test_solution_00.py -v`

Expected: current function-attached cache is lost through `functools.wraps` or has an incorrect key contract.

- [ ] **Step 3: Implement**

Import `_freeze` from Exercise 3 and keep the cache in the decorator closure:

```python
def memoize(function: Callable[P, R]) -> MemoizedCallable[P, R]:
    local_cache: dict[Hashable, R] = {}
    missing: object = object()

    @functools.wraps(function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        key: Hashable = (_freeze(args), _freeze(kwargs))
        cached: R | object = local_cache.get(key, missing)
        if cached is not missing:
            return cast(R, cached)
        result: R = function(*args, **kwargs)
        local_cache[key] = result
        return result

    wrapped.cache = local_cache
    wrapped.cache_clear = local_cache.clear
    return cast(MemoizedCallable[P, R], wrapped)
```

Define a private `_CacheAttributes[R]` protocol with writable `cache: dict[Hashable, R]` and `cache_clear: Callable[[], None]`, cast `wrapped` to that protocol for the two assignments, then cast it to `MemoizedCallable[P, R]` for the return. Do not add file-wide suppressions.

- [ ] **Step 4: Add README and run packet gates**

README explains per-decoration ownership, explicit clearing, supported keys, and exception behavior.

```bash
uv run ruff format --check CH_06_decorators/exercise_0{1,2,3,4}
uv run ruff check CH_06_decorators/exercise_0{1,2,3,4}
uv run pyrefly check CH_06_decorators/exercise_0{1,2,3,4}
uv run mypy CH_06_decorators/exercise_0{1,2,3,4}
uv run pyright CH_06_decorators/exercise_0{1,2,3,4}
uv run pytest CH_06_decorators/exercise_0{1,2,3,4} -v
```

Expected: all commands exit 0; tests contain no sleeps or nondeterministic timing.

- [ ] **Step 5: Commit**

```bash
git add CH_06_decorators/exercise_04
git commit -m "feat(ch06): isolate memoization caches"
```
