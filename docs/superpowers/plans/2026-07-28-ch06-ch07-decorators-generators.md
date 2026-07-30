# Chapter 6–7 Descriptors, Dispatch, Validation, and Generators Implementation

**For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Complete Chapter 6 exercises 5–7 and all four Chapter 7 exercises with typed descriptors, multi-argument dispatch, constraints, slicing, and deterministic generators.

**Architecture:** The cached property stores values per instance and uses deletion for explicit recalculation. Dispatch binds calls against the base signature and selects registered functions by a configured tuple of runtime types. Generator utilities document one-shot/finite-input limits and otherwise match ordinary slice and numeric-sequence behavior.

**Tech Stack:** Python 3.10 standard library, pytest.

---

## Exact Canonical File Additions

The Chapter 7 exercise 3 and 4 tasks use shortened filenames within their
exercise directories. Their exact paths are:

- `CH_07_generators_and_coroutines/exercise_03/README.rst`
- `CH_07_generators_and_coroutines/exercise_03/solution_00.py`
- `CH_07_generators_and_coroutines/exercise_04/README.rst`
- `CH_07_generators_and_coroutines/exercise_04/solution_00.py`

## Scope and ownership

Modify canonical `solution_00.py` files and add `README.rst` plus `test_solution_00.py` in:

- `CH_06_decorators/exercise_05`, `exercise_06`, `exercise_07`
- `CH_07_generators_and_coroutines/exercise_01` through `exercise_04`

Preserve `CH_07_generators_and_coroutines/exercise_04/solution_01.py` unchanged. This packet owns the shared `CH_06_decorators/README.rst` and `CH_07_generators_and_coroutines/README.rst` linked indexes; the Chapter 6 exercises 1–4 packet must not edit the Chapter 6 index.

Exercise READMEs must cite the relevant immutable book source:

- `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_10_properties.rst`
- `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_13_single_dispatch.rst`
- `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_15_validation.rst`
- `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_07_generators_and_coroutines/T_07_islice.rst`

## Task 1: Recalculable cached property

**Public API:** generic `CachedProperty[T, R]` descriptor with `__get__`, `__set_name__`, and `__delete__`. `del instance.property` invalidates only that instance; the next access recalculates.

- [ ] **Step 1: Write failing descriptor tests**

```python
import pytest

from CH_06_decorators.exercise_05.solution_00 import CachedProperty


def test_property_caches_per_instance_and_recalculates_after_delete() -> None:
    class Counter:
        def __init__(self) -> None:
            self.calls: int = 0

        @CachedProperty
        def value(self) -> int:
            self.calls += 1
            return self.calls

    first: Counter = Counter()
    second: Counter = Counter()
    assert (first.value, first.value, second.value) == (1, 1, 1)
    del first.value
    assert first.value == 2
    assert second.value == 1


def test_delete_before_first_access_raises_attribute_error() -> None:
    class Value:
        @CachedProperty
        def answer(self) -> int:
            return 42

    with pytest.raises(AttributeError, match="answer"):
        del Value().answer
```

Also test class-level descriptor access, a `__slots__` instance without `__dict__`, and wrapped function metadata.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_06_decorators/exercise_05/test_solution_00.py -v`

Expected: current implementation shares its cache across instances and exposes a class-bound clear method.

- [ ] **Step 3: Implement**

```python
class CachedProperty(Generic[T, R]):
    def __init__(self, function: Callable[[T], R]) -> None:
        self.function: Callable[[T], R] = function
        self.__doc__: str | None = function.__doc__
        self.name: str | None = None

    def __set_name__(self, owner: type[T], name: str) -> None:
        if self.name is not None and self.name != name:
            raise TypeError("one CachedProperty cannot serve two names")
        self.name = name

    @overload
    def __get__(
        self, instance: None, owner: type[T] | None = None
    ) -> CachedProperty[T, R]: ...

    @overload
    def __get__(self, instance: T, owner: type[T] | None = None) -> R: ...

    def __get__(
        self, instance: T | None, owner: type[T] | None = None
    ) -> R | CachedProperty[T, R]:
        if instance is None:
            return self
        name: str = self._bound_name()
        namespace: dict[str, object] = vars(instance)
        if name not in namespace:
            namespace[name] = self.function(instance)
        return cast(R, namespace[name])

    def __delete__(self, instance: T) -> None:
        name: str = self._bound_name()
        try:
            del vars(instance)[name]
        except KeyError as error:
            raise AttributeError(name) from error
```

`_bound_name()` raises `TypeError` if `__set_name__` was never called. A slots-only instance naturally raises a specific `TypeError` explaining that `__dict__` is required.

- [ ] **Step 4: Document, verify, commit**

README repeats question 5, documents per-instance storage/deletion, thread-lock non-guarantee, and module/test commands.

Run: `uv run pytest CH_06_decorators/exercise_05 -v`

Expected: pass.

```bash
git add CH_06_decorators/exercise_05/README.rst CH_06_decorators/exercise_05/solution_00.py CH_06_decorators/exercise_05/test_solution_00.py
git commit -m "feat(ch06): add recalculable cached property"
```

## Task 2: Configurable multi-argument dispatch

**Public API:** `fancysingledispatch(*ignored: str, dispatch_on: tuple[str, ...] | None = None, **ignored_by_name: bool)`. The returned dispatcher is callable and has `.register(function)`. `dispatch_on=None` dispatches on every parameter except legacy ignored names such as `last_name=True`; unmatched type tuples invoke the base implementation. Supplying `dispatch_on` together with either ignored form raises `TypeError`.

- [ ] **Step 1: Write failing tests**

```python
import pytest

from CH_06_decorators.exercise_06.solution_00 import fancysingledispatch


def test_dispatches_on_multiple_named_arguments_and_kwargs() -> None:
    @fancysingledispatch(dispatch_on=("left", "right"))
    def combine(left: object, right: object, separator: str = ":") -> str:
        return f"default{separator}{left}{separator}{right}"

    @combine.register
    def combine_int_str(left: int, right: str, separator: str = ":") -> str:
        return f"{left}{separator}{right.upper()}"

    assert combine(3, "eggs") == "3:EGGS"
    assert combine(left=3, right="eggs", separator="/") == "3/EGGS"
    assert combine("3", "eggs").startswith("default:")


def test_legacy_true_keyword_excludes_that_parameter() -> None:
    @fancysingledispatch(last_name=True)
    def greet(first_name: str, last_name: str) -> str:
        return f"{first_name} {last_name}"

    assert greet("Ada", "Lovelace") == "Ada Lovelace"
```

Also test dispatch on all parameters, omitted defaults after `apply_defaults`, unknown dispatch names, missing registration annotations, metadata preservation, and a registration with the wrong signature.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_06_decorators/exercise_06/test_solution_00.py -v`

Expected: current API cannot express `dispatch_on` and raises instead of using a base fallback.

- [ ] **Step 3: Implement**

The outer decorator first rejects false-valued compatibility keywords, conflicting configuration styles, and duplicate ignored names. Create a typed `_Dispatcher[P, R]`; at construction derive the selected names from the base signature, then validate them. Registration must have the exact same parameter names/kinds and concrete class annotations for selected names:

```python
def register(self, function: Callable[P, R]) -> Callable[P, R]:
    signature: inspect.Signature = inspect.signature(function)
    if _shape(signature) != self._shape:
        raise TypeError("registered function signature does not match base function")
    hints: dict[str, object] = typing.get_type_hints(function)
    key: tuple[type[object], ...] = tuple(
        _concrete_type(name, hints) for name in self._dispatch_on
    )
    self._registry[key] = function
    return function


def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
    bound: inspect.BoundArguments = self._signature.bind(*args, **kwargs)
    bound.apply_defaults()
    key: tuple[type[object], ...] = tuple(
        type(bound.arguments[name]) for name in self._dispatch_on
    )
    implementation: Callable[P, R] = self._registry.get(key, self._base)
    return implementation(*args, **kwargs)
```

Apply `functools.update_wrapper(self, base)`. Reject empty `dispatch_on`, duplicate names, `typing.Any`, unions, and missing annotations with precise `TypeError`s.

- [ ] **Step 4: Document, verify, commit**

README states exact-type rather than subclass/MRO dispatch, base fallback, registration validation, and commands.

Run: `uv run pytest CH_06_decorators/exercise_06 -v`

Expected: pass.

```bash
git add CH_06_decorators/exercise_06/README.rst CH_06_decorators/exercise_06/solution_00.py CH_06_decorators/exercise_06/test_solution_00.py
git commit -m "feat(ch06): dispatch across selected arguments"
```

## Task 3: Type and numeric constraints

**Public API:** `Constraint` protocol; `GreaterThan`, `LessThan`, `Between`; compatibility names `Gt`; `type_check(**constraints)`; compatibility alias `enforce_type_hints`.

**Behavioral decisions:** The decorator validates but never coerces. Wrong runtime types raise `TypeError`; violated numeric constraints raise `ValueError`; `Between(lower, upper, inclusive=False)` is exclusive by default, matching the old solution.

- [ ] **Step 1: Write failing tests**

```python
import pytest

from CH_06_decorators.exercise_07.solution_00 import (
    Between,
    GreaterThan,
    type_check,
)


def test_validates_types_and_constraints_without_coercion() -> None:
    @type_check(count=GreaterThan(0), ratio=Between(0.0, 1.0))
    def scale(count: int, ratio: float = 0.5) -> float:
        return count * ratio

    assert scale(4, 0.25) == 1.0
    with pytest.raises(TypeError, match="count"):
        scale("4", 0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="greater than 0"):
        scale(0, 0.25)
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        scale(4, 1.0)
```

Also test `LessThan`, inclusive `Between`, defaults, unknown constraint names, unconstrained annotated parameters, return-value non-validation, and `Gt`/`enforce_type_hints` compatibility.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_06_decorators/exercise_07/test_solution_00.py -v`

Expected: current decorator coerces values and invokes pytest from production code.

- [ ] **Step 3: Implement**

```python
@dataclass(frozen=True)
class GreaterThan:
    threshold: Real

    def validate(self, name: str, value: object) -> None:
        if not isinstance(value, Real) or value <= self.threshold:
            raise ValueError(f"{name} must be greater than {self.threshold}")


def type_check(
    **constraints: Constraint,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        signature: inspect.Signature = inspect.signature(function)
        hints: dict[str, object] = typing.get_type_hints(function)
        unknown: set[str] = constraints.keys() - signature.parameters.keys()
        if unknown:
            raise TypeError(f"unknown constrained parameters: {sorted(unknown)!r}")

        @functools.wraps(function)
        def checked(*args: P.args, **kwargs: P.kwargs) -> R:
            bound: inspect.BoundArguments = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            for name, value in bound.arguments.items():
                annotation: object = hints.get(name, inspect.Signature.empty)
                if isinstance(annotation, type) and not isinstance(value, annotation):
                    raise TypeError(f"{name} must be {annotation.__name__}")
                constraint: Constraint | None = constraints.get(name)
                if constraint is not None:
                    constraint.validate(name, value)
            return function(*args, **kwargs)

        return checked

    return decorate
```

Implement `LessThan` and `Between` as immutable dataclasses. Validate `lower < upper` during `Between` construction. Production code must not import pytest.

- [ ] **Step 4: Document, verify, commit**

README notes the prompt's `type_check` versus old `enforce_type_hints` naming mismatch and documents both aliases.

Run: `uv run pytest CH_06_decorators/exercise_07 -v`

Expected: pass.

```bash
git add CH_06_decorators/exercise_07/README.rst CH_06_decorators/exercise_07/solution_00.py CH_06_decorators/exercise_07/test_solution_00.py
git commit -m "feat(ch06): enforce typed numeric constraints"
```

## Task 4: Negative-step islice

**Public API:** `islice(iterable: Iterable[T], start: int, stop: int, step: int = 1) -> Iterator[T]`.

For positive steps, stream with `itertools.islice`. For negative steps, materialize the finite iterable once and apply ordinary list slicing. Reject step zero. Document that a negative step never terminates for an infinite iterable.

- [ ] **Step 1: Write failing tests**

```python
import pytest

from CH_07_generators_and_coroutines.exercise_01.solution_00 import islice


def test_negative_and_positive_steps_match_sequence_slices() -> None:
    values: list[int] = list(range(30))
    assert list(islice(iter(values), 20, 10, -1)) == values[20:10:-1]
    assert list(islice(iter(values), 2, 12, 3)) == values[2:12:3]


def test_zero_step_is_rejected() -> None:
    with pytest.raises(ValueError, match="step"):
        list(islice(range(5), 0, 3, 0))
```

Also test empty ranges, negative start/stop under a negative step, and that positive slicing consumes only as far as needed.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_07_generators_and_coroutines/exercise_01/test_solution_00.py -v`

Expected: current implementation yields iterator objects rather than sliced values.

- [ ] **Step 3: Implement**

```python
def islice(
    iterable: Iterable[T],
    start: int,
    stop: int,
    step: int = 1,
) -> Iterator[T]:
    if step == 0:
        raise ValueError("step must not be zero")
    if step > 0:
        yield from itertools.islice(iterable, start, stop, step)
        return
    values: list[T] = list(iterable)
    yield from values[slice(start, stop, step)]
```

- [ ] **Step 4: Document, verify, commit**

README includes the finite-materialization decision required by the design.

Run: `uv run pytest CH_07_generators_and_coroutines/exercise_01 -v`

Expected: pass.

```bash
git add CH_07_generators_and_coroutines/exercise_01/README.rst CH_07_generators_and_coroutines/exercise_01/solution_00.py CH_07_generators_and_coroutines/exercise_01/test_solution_00.py
git commit -m "feat(ch07): support negative generator slices"
```

## Task 5: Sliceable one-shot generator

**Public API:** `SliceableGenerator[T](iterable: Iterable[T])`, with `__getitem__(index: slice) -> list[T]`. Only non-negative slices and positive steps are supported; each access consumes the underlying iterator and indexes are relative to its current position.

- [ ] **Step 1: Write failing tests**

```python
import pytest

from CH_07_generators_and_coroutines.exercise_02.solution_00 import (
    SliceableGenerator,
)


def test_slices_consume_one_underlying_iterator() -> None:
    values: SliceableGenerator[int] = SliceableGenerator(iter(range(30)))
    assert values[2:6] == [2, 3, 4, 5]
    assert values[0:3] == [6, 7, 8]


def test_negative_slice_is_rejected() -> None:
    values: SliceableGenerator[int] = SliceableGenerator(range(5))
    with pytest.raises(ValueError, match="non-negative"):
        values[-1:3]
```

Also test step two, omitted start/stop, integer indexing rejection, zero step, empty/exhausted iterators.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_07_generators_and_coroutines/exercise_02/test_solution_00.py -v`

Expected: current implementation mishandles omitted bounds/steps and lacks validation.

- [ ] **Step 3: Implement**

```python
class SliceableGenerator(Generic[T]):
    def __init__(self, iterable: Iterable[T]) -> None:
        self._iterator: Iterator[T] = iter(iterable)

    def __getitem__(self, index: slice) -> list[T]:
        if not isinstance(index, slice):
            raise TypeError("SliceableGenerator accepts slices only")
        start: int = 0 if index.start is None else index.start
        stop: int | None = index.stop
        step: int = 1 if index.step is None else index.step
        if start < 0 or (stop is not None and stop < 0):
            raise ValueError("slice bounds must be non-negative")
        if step <= 0:
            raise ValueError("slice step must be positive")
        return list(itertools.islice(self._iterator, start, stop, step))
```

- [ ] **Step 4: Document, verify, commit**

README makes one-shot/current-position semantics explicit.

Run: `uv run pytest CH_07_generators_and_coroutines/exercise_02 -v`

Expected: pass.

```bash
git add CH_07_generators_and_coroutines/exercise_02/README.rst CH_07_generators_and_coroutines/exercise_02/solution_00.py CH_07_generators_and_coroutines/exercise_02/test_solution_00.py
git commit -m "feat(ch07): wrap generators with slicing"
```

## Task 6: Fibonacci generator

**Public API:** `fibonacci() -> Iterator[int]`, yielding `0, 1, 1, 2, ...` forever.

- [ ] **Step 1: Write failing tests**

```python
from collections.abc import Iterator
from itertools import islice
from typing import get_type_hints

from CH_07_generators_and_coroutines.exercise_03.solution_00 import fibonacci


def test_first_ten_fibonacci_numbers() -> None:
    assert list(islice(fibonacci(), 10)) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert get_type_hints(fibonacci)["return"] == Iterator[int]
```

Also assert two instances advance independently and a 100th value is an `int`.

- [ ] **Step 2: Verify red, implement, rerun**

Run: `uv run pytest CH_07_generators_and_coroutines/exercise_03/test_solution_00.py -v`

Expected before implementation: current file lacks complete typing/documentation tests.

```python
def fibonacci() -> Iterator[int]:
    current: int = 0
    following: int = 1
    while True:
        yield current
        current, following = following, current + following
```

Run the same command; expected: pass.

- [ ] **Step 3: Document and commit**

README specifies starting values, infinite behavior, no dependencies, and commands.

```bash
git add CH_07_generators_and_coroutines/exercise_03
git commit -m "feat(ch07): add Fibonacci generator"
```

## Task 7: Sieve of Eratosthenes prime generator

**Public API:** `generate_primes() -> Iterator[int]`, yielding primes from 2 forever.

- [ ] **Step 1: Write failing tests**

```python
from collections.abc import Iterator
from itertools import islice
from typing import get_type_hints

from CH_07_generators_and_coroutines.exercise_04.solution_00 import (
    generate_primes,
)


def test_first_twenty_primes() -> None:
    assert list(islice(generate_primes(), 20)) == [
        2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
        31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    ]
    assert get_type_hints(generate_primes)["return"] == Iterator[int]


def test_generators_do_not_share_sieve_state() -> None:
    first: Iterator[int] = generate_primes()
    second: Iterator[int] = generate_primes()
    assert [next(first), next(first), next(second)] == [2, 3, 2]
```

Also cross-check the first 200 values with a small trial-division oracle in the test.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_07_generators_and_coroutines/exercise_04/test_solution_00.py -v`

Expected: existing answer is untyped and uses an ever-growing list/trial division rather than a sieve.

- [ ] **Step 3: Implement an incremental sieve**

```python
def generate_primes() -> Iterator[int]:
    composites: dict[int, list[int]] = {}
    candidate: int = 2
    while True:
        factors: list[int] | None = composites.pop(candidate, None)
        if factors is None:
            yield candidate
            composites[candidate * candidate] = [candidate]
        else:
            for prime in factors:
                composites.setdefault(candidate + prime, []).append(prime)
        candidate += 1
```

Keep the demonstration bounded and guarded. Do not modify `solution_01.py`.

- [ ] **Step 4: Add READMEs/indexes and run packet gates**

Exercise README explains incremental sieve state, infinite behavior, deterministic output, and commands. Convert both chapter READMEs to numbered links; Chapter 6 must link all exercises 1–7, including files created by the other packet.

```bash
uv run ruff format --check CH_06_decorators CH_07_generators_and_coroutines
uv run ruff check CH_06_decorators CH_07_generators_and_coroutines
uv run pyrefly check CH_06_decorators CH_07_generators_and_coroutines
uv run mypy CH_06_decorators CH_07_generators_and_coroutines
uv run pyright CH_06_decorators CH_07_generators_and_coroutines
uv run pytest CH_06_decorators CH_07_generators_and_coroutines -v
```

Expected: all commands exit 0; `solution_01.py` remains unchanged.

- [ ] **Step 5: Commit**

```bash
git add CH_06_decorators/README.rst CH_07_generators_and_coroutines
git commit -m "feat(ch07): add deterministic prime sieve"
```
