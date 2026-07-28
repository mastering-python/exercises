# Chapters 4–5 Collections and Functional Programming Implementation

**For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Deliver typed, tested canonical solutions for the three design-pattern exercises and three functional-programming exercises.

**Architecture:** Sorted mappings are mapping views over ordinary storage; the logarithmic-insertion sorted collection is a deterministic AVL multiset, not a bisected Python list. Functional exercises expose pure functions with deterministic output and no mutation of caller-owned inputs. Historical `solution_01.py` files remain byte-for-byte unchanged.

**Tech Stack:** Python 3.10 standard library, generics, pytest.

---

## Exact Canonical File Additions

Later tasks use shortened filenames within their stated exercise directory.
Their exact repository paths are:

- `CH_04_design_patterns/exercise_02/__init__.py`
- `CH_04_design_patterns/exercise_02/README.rst`
- `CH_04_design_patterns/exercise_02/solution_00.py`
- `CH_05_functional_programming/exercise_02/README.rst`
- `CH_05_functional_programming/exercise_02/solution_00.py`
- `CH_05_functional_programming/exercise_03/README.rst`
- `CH_05_functional_programming/exercise_03/solution_00.py`

## Scope and public APIs

- `CH_04_design_patterns/exercise_01`: `SortedDict`.
- `CH_04_design_patterns/exercise_02`: `SortedList`.
- `CH_04_design_patterns/exercise_03`: `Borg`.
- `CH_05_functional_programming/exercise_01`: `quicksort`, compatibility wrapper `qs`.
- `CH_05_functional_programming/exercise_02`: `groupby(func, seq)`.
- `CH_05_functional_programming/exercise_03`: `groupby(iterable, key=None)`.

For every exercise, create or update `README.rst`, `solution_00.py`, `test_solution_00.py`, and `__init__.py`. Modify both chapter READMEs into linked indexes only after their packet passes. Do not modify either existing `solution_01.py`.

Where the book examples inform an answer, cite the corresponding immutable source in that exercise README:

- `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_04_design_patterns/T_10_bisect.rst`
- `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_04_design_patterns/T_11_borg_and_singleton.rst`
- `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_05_functional_programming/T_14_groupby.rst`

## Task 1: SortedDict

**Files:** create `exercise_01/{README.rst,test_solution_00.py}`; rewrite `exercise_01/solution_00.py`; retain its initializer and `solution_01.py`.

- [ ] **Step 1: Write failing tests**

```python
from CH_04_design_patterns.exercise_01.solution_00 import SortedDict


def test_iteration_tracks_mutations_in_key_order() -> None:
    values: SortedDict[str, int, int] = SortedDict(
        {"bbb": 3, "a": 1}, keyfunc=len
    )
    values["cc"] = 2
    assert list(values) == ["a", "cc", "bbb"]
    assert list(values.items()) == [("a", 1), ("cc", 2), ("bbb", 3)]
    del values["cc"]
    assert repr(values) == "{'a': 1, 'bbb': 3}"
```

Also test empty construction, iterable pairs, replacement without duplicate keys, reverse key functions, normal `KeyError`, and equality through the `MutableMapping` contract.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_04_design_patterns/exercise_01/test_solution_00.py -v`

Expected: current canonical implementation fails mutation/mapping-contract tests.

- [ ] **Step 3: Implement**

Use `MutableMapping[K, V]` and sort keys at iteration:

```python
class SortedDict(MutableMapping[K, V], Generic[K, V, S]):
    def __init__(
        self,
        values: Mapping[K, V] | Iterable[tuple[K, V]] = (),
        keyfunc: Callable[[K], S] | None = None,
    ) -> None:
        self._values: dict[K, V] = dict(values)
        self._keyfunc: Callable[[K], S] = _identity if keyfunc is None else keyfunc

    def __getitem__(self, key: K) -> V:
        return self._values[key]

    def __setitem__(self, key: K, value: V) -> None:
        self._values[key] = value

    def __delitem__(self, key: K) -> None:
        del self._values[key]

    def __iter__(self) -> Iterator[K]:
        return iter(sorted(self._values, key=self._keyfunc))

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return repr(dict(self.items()))
```

Define a typed comparable protocol for `S` and a typed/cast identity helper; do not use an unbounded `object` sort key. Keeping `keyfunc` positional preserves the existing canonical constructor while also allowing keyword use.

- [ ] **Step 4: Document, verify, commit**

README repeats the exact question, states the key function receives keys, documents live mutation ordering and O(n log n) iteration, and lists module/test commands.

Run: `uv run pytest CH_04_design_patterns/exercise_01 -v`

Expected: pass.

```bash
git add CH_04_design_patterns/exercise_01/README.rst CH_04_design_patterns/exercise_01/solution_00.py CH_04_design_patterns/exercise_01/test_solution_00.py
git commit -m "feat(ch04): implement sorted mapping"
```

## Task 2: SortedList with logarithmic insertion

**Public API:** `SortedList(values: Iterable[T] = (), *, key: Callable[[T], S] | None = None)`, `add(value: T) -> None`, `insert(value: T) -> None`, iteration, length, membership, and repr. Duplicates are retained in insertion count.

- [ ] **Step 1: Write failing behavior and complexity tests**

```python
from CH_04_design_patterns.exercise_02.solution_00 import SortedList


def test_add_keeps_values_sorted_and_retains_duplicates() -> None:
    values: SortedList[int, int] = SortedList([3, 1, 2, 2])
    values.add(0)
    values.insert(4)
    assert list(values) == [0, 1, 2, 2, 3, 4]
    assert len(values) == 6


def test_tree_height_stays_logarithmic_for_sorted_input() -> None:
    values: SortedList[int, int] = SortedList()
    for value in range(1_024):
        values.add(value)
    assert values.tree_height <= 2 * 10
```

Also test an empty collection, reverse/custom keys, duplicate custom-key values, and membership. The public read-only `tree_height` diagnostic makes the asymptotic design testable without timing.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_04_design_patterns/exercise_02/test_solution_00.py -v`

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Implement the deterministic AVL multiset**

Use a private generic `_Node` with `value`, `sort_key`, `duplicates`, `height`, `left`, and `right`. `add()` performs ordinary BST insertion, appends equal-key values to `duplicates`, updates heights, and applies LL/LR/RR/RL rotations. Iteration is in-order:

```python
def _iter_node(node: _Node[T, S] | None) -> Iterator[T]:
    if node is None:
        return
    yield from _iter_node(node.left)
    yield node.value
    yield from node.duplicates
    yield from _iter_node(node.right)


class SortedList(Collection[T], Generic[T, S]):
    def add(self, value: T) -> None:
        sort_key: S = self._key(value)
        self._root = _insert(self._root, value, sort_key)
        self._length += 1

    def insert(self, value: T) -> None:
        self.add(value)

    @property
    def tree_height(self) -> int:
        return _height(self._root)
```

The default key is a typed identity helper. Never use randomness or a Python-list insertion internally.

- [ ] **Step 4: Document, verify, commit**

README explains the AVL choice, O(log n) insertion, O(n) iteration, duplicate ordering, public APIs, and `uv run` commands.

Run: `uv run pytest CH_04_design_patterns/exercise_02 -v`

Expected: pass.

```bash
git add CH_04_design_patterns/exercise_02
git commit -m "feat(ch04): add logarithmic sorted list"
```

## Task 3: Borg state per subclass

- [ ] **Step 1: Write failing tests**

```python
from CH_04_design_patterns.exercise_03.solution_00 import Borg


def test_state_is_shared_within_but_not_between_subclasses() -> None:
    class First(Borg):
        pass

    class Second(Borg):
        pass

    first_a: First = First()
    first_b: First = First()
    second: Second = Second()
    setattr(first_a, "answer", 42)
    assert getattr(first_b, "answer") == 42
    assert not hasattr(second, "answer")
```

Also test direct `Borg` instances and that a grandchild receives its own state.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_04_design_patterns/exercise_03/test_solution_00.py -v`

Expected: `ModuleNotFoundError` for canonical `solution_00.py`.

- [ ] **Step 3: Implement**

```python
BorgT = TypeVar("BorgT", bound="Borg")


class Borg:
    _shared_state: ClassVar[dict[str, object]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls._shared_state = {}

    def __new__(cls: type[BorgT]) -> BorgT:
        instance: BorgT = cast(BorgT, super().__new__(cls))
        instance.__dict__ = cls._shared_state
        return instance
```

Keep the demonstration guarded. Do not edit `solution_01.py`.

- [ ] **Step 4: Document, verify, commit**

README states instance identity remains distinct while `__dict__` is shared only inside the exact subclass.

Run: `uv run pytest CH_04_design_patterns/exercise_03 -v`

Expected: pass.

```bash
git add CH_04_design_patterns/exercise_03/README.rst CH_04_design_patterns/exercise_03/solution_00.py CH_04_design_patterns/exercise_03/test_solution_00.py
git commit -m "feat(ch04): isolate Borg state by subclass"
```

## Task 4: Functional quicksort

**Public API:** `quicksort(values: Iterable[T]) -> list[T]`; `qs` is a typed compatibility wrapper. Neither mutates caller data.

- [ ] **Step 1: Write failing tests**

```python
from CH_05_functional_programming.exercise_01.solution_00 import qs, quicksort


def test_quicksort_handles_duplicates_without_mutating_input() -> None:
    values: list[int] = [3, 1, 2, 1]
    assert quicksort(values) == [1, 1, 2, 3]
    assert qs(iter(values)) == [1, 1, 2, 3]
    assert values == [3, 1, 2, 1]
```

Also test empty/singleton input and comparable records.

- [ ] **Step 2: Verify red**

Run: `uv run pytest CH_05_functional_programming/exercise_01/test_solution_00.py -v`

Expected: current `qs` rejects a generator or lacks the typed compatibility contract.

- [ ] **Step 3: Implement**

```python
def quicksort(values: Iterable[T]) -> list[T]:
    items: list[T] = list(values)
    if len(items) < 2:
        return items
    pivot: T = items[0]
    lower: list[T] = [item for item in items[1:] if item < pivot]
    upper: list[T] = [item for item in items[1:] if not item < pivot]
    return [*quicksort(lower), pivot, *quicksort(upper)]


def qs(values: Iterable[T]) -> list[T]:
    return quicksort(values)
```

- [ ] **Step 4: Document, verify, commit**

README documents fresh-list behavior, comparison requirement, deterministic first-item pivot, and worst-case recursion trade-off.

Run: `uv run pytest CH_05_functional_programming/exercise_01 -v`

Expected: pass. Preserve `solution_01.py`.

```bash
git add CH_05_functional_programming/exercise_01/README.rst CH_05_functional_programming/exercise_01/solution_00.py CH_05_functional_programming/exercise_01/test_solution_00.py
git commit -m "feat(ch05): complete functional quicksort"
```

## Task 5: Group non-consecutive values

**Public API:** `groupby(func: Callable[[T], K], seq: Iterable[T]) -> dict[K, list[T]]`.

- [ ] **Step 1: Write failing tests**

```python
import pytest

from CH_05_functional_programming.exercise_02.solution_00 import groupby


def test_non_consecutive_values_share_one_group() -> None:
    assert groupby(lambda value: value % 2, [1, 2, 3, 4]) == {
        1: [1, 3],
        0: [2, 4],
    }


def test_rejects_non_callable_group_function() -> None:
    with pytest.raises(TypeError, match="func must be callable"):
        groupby(3, [1, 2])  # type: ignore[arg-type]
```

Also test empty input, generators, and first-key/in-group ordering.

- [ ] **Step 2: Verify red, implement, and rerun**

Run: `uv run pytest CH_05_functional_programming/exercise_02/test_solution_00.py -v`

Expected before implementation: type/iterator contract failures.

```python
def groupby(func: Callable[[T], K], seq: Iterable[T]) -> dict[K, list[T]]:
    if not callable(func):
        raise TypeError("func must be callable")
    groups: dict[K, list[T]] = {}
    for item in seq:
        groups.setdefault(func(item), []).append(item)
    return groups
```

Run the same command; expected: pass.

- [ ] **Step 3: Document and commit**

README contrasts this behavior with adjacency-based `itertools.groupby`, states ordering rules, and includes `uv run` commands.

```bash
git add CH_05_functional_programming/exercise_02
git commit -m "feat(ch05): group non-consecutive values"
```

## Task 6: Return list-valued groups

**Public API:** `groupby(iterable: Iterable[T], key: Callable[[T], K] | None = None) -> dict[K | T, list[T]]`.

- [ ] **Step 1: Write failing tests**

```python
import pytest

from CH_05_functional_programming.exercise_03.solution_00 import groupby


def test_groups_are_reusable_lists() -> None:
    groups: dict[str, list[str]] = groupby("ABACA")
    assert groups == {"A": ["A", "A", "A"], "B": ["B"], "C": ["C"]}
    assert list(groups["A"]) == list(groups["A"])


def test_rejects_non_callable_key() -> None:
    with pytest.raises(TypeError, match="key must be callable or None"):
        groupby([1, 2], key=3)  # type: ignore[arg-type]
```

Also test a key function, empty generator, first-key order, and input-list preservation.

- [ ] **Step 2: Verify red, implement, and rerun**

Run: `uv run pytest CH_05_functional_programming/exercise_03/test_solution_00.py -v`

Expected before implementation: current loose typing/`key=None` contract fails strict tests.

Implement with two overloads so identity grouping and keyed grouping have precise return types. The keyed implementation is:

```python
def groupby(
    iterable: Iterable[T],
    key: Callable[[T], K] | None = None,
) -> dict[K | T, list[T]]:
    if key is not None and not callable(key):
        raise TypeError("key must be callable or None")
    groups: dict[K | T, list[T]] = {}
    for item in iterable:
        group_key: K | T = item if key is None else key(item)
        groups.setdefault(group_key, []).append(item)
    return groups
```

Run the same command; expected: pass.

- [ ] **Step 3: Add README/indexes and run packet gates**

Document the list/reusability choice and `uv run` commands. Convert both chapter READMEs to numbered links without changing prompt meaning.

```bash
uv run ruff format --check CH_04_design_patterns CH_05_functional_programming
uv run ruff check CH_04_design_patterns CH_05_functional_programming
uv run pyrefly check CH_04_design_patterns CH_05_functional_programming
uv run mypy CH_04_design_patterns CH_05_functional_programming
uv run pyright CH_04_design_patterns CH_05_functional_programming
uv run pytest CH_04_design_patterns CH_05_functional_programming -v
```

Expected: every command exits 0; historical alternatives are not modified or included in static-check scope.

- [ ] **Step 4: Commit**

```bash
git add CH_04_design_patterns/README.rst CH_05_functional_programming
git commit -m "feat(ch05): return reusable grouped lists"
```
