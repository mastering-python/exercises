# Chapter 14 Workers, RPC, and Parallel Sorting Implementation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver canonical, typed, tested solutions for Chapter 14 exercises 3 through 7 while retaining every historical specialized answer unchanged.

**Architecture:** Exercises 3 and 4 expose paired thread/process APIs for flat and recursively scheduled file work. Exercise 5 supplies a reusable persistent queue pool; exercise 6 narrows that transport into allowlisted RPC; exercise 7 performs deterministic parallel merge sort with bounded spawn workers.

**Tech Stack:** Python 3.10, `threading`, `multiprocessing`, `queue`, `concurrent.futures`, pytest, pytest-timeout, uv, Ruff, Pyrefly, mypy, Pyright.

---

## File map and immutable files

- Create canonical `solution_00.py`, `test_solution_00.py`, and `README.rst` in `exercise_03/` and `exercise_04/`.
- Rewrite `exercise_05/solution_00.py`; create its test and README.
- Rewrite `exercise_06/solution_00.py`; create its test and README.
- Rewrite `exercise_07/solution_00.py`; create its test and README.
- Modify `CH_14_multithreading_and_multiprocessing/README.rst` only to link exercises 3 through 7.
- Never modify:
  - `exercise_03/threading_solution_00.py`
  - `exercise_03/multiprocessing_solution_00.py`
  - `exercise_04/threading_solution_00.py`
  - `exercise_04/multiprocessing_solution_00.py`

### Task 1: Canonical non-recursive thread and process APIs

**Files:**
- Create: `CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py`
- Create: `CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py`

- [ ] **Step 1: Write failing parity and failure-propagation tests**

```python
from __future__ import annotations

import multiprocessing
from pathlib import Path

import pytest

from .solution_00 import multiprocessing_total_size, threaded_total_size


def write_file(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


@pytest.mark.timeout(15)
def test_thread_and_process_totals_match(tmp_path: Path) -> None:
    write_file(tmp_path / "a.bin", 2)
    write_file(tmp_path / "b.bin", 5)
    write_file(tmp_path / "nested" / "ignored.bin", 11)
    assert threaded_total_size(tmp_path, worker_count=2) == 7
    assert multiprocessing_total_size(
        tmp_path,
        worker_count=2,
        context=multiprocessing.get_context("spawn"),
    ) == 7


def test_both_apis_reject_non_directories(tmp_path: Path) -> None:
    path: Path = tmp_path / "file"
    write_file(path, 1)
    with pytest.raises(NotADirectoryError):
        threaded_total_size(path)
    with pytest.raises(NotADirectoryError):
        multiprocessing_total_size(path)


def test_worker_count_must_be_positive(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="worker_count"):
        threaded_total_size(tmp_path, worker_count=0)
```

- [ ] **Step 2: Run the tests and verify the canonical module is missing**

Run `uv run pytest CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py -vv`.

Expected: FAIL during import because `exercise_03/solution_00.py` does not exist.

- [ ] **Step 3: Implement the paired APIs**

Use a `queue.Queue[Path | None]` plus `threading.Thread` for `threaded_total_size`. Use a spawn-context `multiprocessing.Pool` for `multiprocessing_total_size`; map the top-level `_stat_size(path: Path) -> int` function so child failures are re-raised by `pool.map`. Both APIs validate `worker_count`, count only sorted immediate regular non-symlink files, return `0` for an empty directory, and expose:

```python
def threaded_total_size(directory: Path, *, worker_count: int = 4) -> int:
    """Return the total size of immediate files using raw threads."""


def multiprocessing_total_size(
    directory: Path,
    *,
    worker_count: int = 2,
    context: multiprocessing.context.BaseContext | None = None,
) -> int:
    """Return the total size of immediate files using a process pool."""
```

The thread worker must catch `Exception`, append the exception under a lock, call `task_done()` in `finally`, and the parent must re-raise the first exception after joining every worker. The process pool must use a context manager and `processes=min(worker_count, max(1, len(paths)))`.

- [ ] **Step 4: Run focused verification**

```bash
uv run pytest CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py -vv
uv run ruff format --check CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py
uv run ruff check CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py
uv run pyrefly check CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py
uv run mypy CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py
uv run pyright CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py
```

Expected: every command exits 0 and pytest reports 3 passed.

- [ ] **Step 5: Commit**

```bash
git add CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py
git commit -m "feat: add canonical threaded and process file totals"
```

### Task 2: Recursive queue scheduling with explicit timeouts

**Files:**
- Create: `CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py`
- Create: `CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py`

- [ ] **Step 1: Write failing recursive parity, symlink, empty, and cleanup tests**

```python
from __future__ import annotations

import multiprocessing
from pathlib import Path

import pytest

from .solution_00 import multiprocessing_recursive_size, threaded_recursive_size


def write_file(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


@pytest.mark.timeout(20)
def test_recursive_apis_find_dynamically_enqueued_directories(tmp_path: Path) -> None:
    write_file(tmp_path / "root.bin", 2)
    write_file(tmp_path / "one" / "child.bin", 3)
    write_file(tmp_path / "one" / "two" / "deep.bin", 5)
    assert threaded_recursive_size(tmp_path, worker_count=3, timeout=5.0) == 10
    assert multiprocessing_recursive_size(
        tmp_path,
        worker_count=2,
        timeout=5.0,
        context=multiprocessing.get_context("spawn"),
    ) == 10


def test_recursive_apis_return_zero_for_empty_directory(tmp_path: Path) -> None:
    assert threaded_recursive_size(tmp_path) == 0
    assert multiprocessing_recursive_size(tmp_path) == 0


def test_timeout_must_be_positive(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timeout"):
        threaded_recursive_size(tmp_path, timeout=0.0)
```

- [ ] **Step 2: Run tests and verify the canonical module is missing**

Run `uv run pytest CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py -vv`.

Expected: FAIL during import because the canonical module does not exist.

- [ ] **Step 3: Implement a parent-owned dynamic scheduler**

Define picklable messages so the parent, not workers, owns the outstanding-work count:

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScanResult:
    directory: Path
    child_directories: tuple[Path, ...]
    byte_count: int


@dataclass(frozen=True)
class ScanFailure:
    directory: Path
    error_type: str
    message: str
```

Implement `_scan_directory(directory: Path) -> ScanResult`, skipping symlinks and sorting entries. Implement:

```python
def threaded_recursive_size(
    directory: Path,
    *,
    worker_count: int = 4,
    timeout: float = 5.0,
) -> int:
    """Traverse recursively with persistent raw-thread workers."""


def multiprocessing_recursive_size(
    directory: Path,
    *,
    worker_count: int = 2,
    timeout: float = 5.0,
    context: multiprocessing.context.BaseContext | None = None,
) -> int:
    """Traverse recursively with persistent spawn-process workers."""
```

For both variants:

1. enqueue the root and set `outstanding = 1`;
2. wait for `ScanResult | ScanFailure` with the supplied timeout;
3. decrement for the completed directory and increment for each newly queued directory;
4. stop when `outstanding == 0`;
5. send one stop sentinel per worker and join every worker with the same timeout;
6. raise `TimeoutError` for a missing result and `WorkerScanError` for `ScanFailure`;
7. terminate only process workers that remain alive during exceptional cleanup.

- [ ] **Step 4: Verify the recursive packet**

```bash
uv run pytest CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py -vv
uv run ruff format --check CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py
uv run ruff check CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py
uv run pyrefly check CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py
uv run mypy CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py
uv run pyright CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py
```

Expected: all commands exit 0; pytest reports 3 passed with no remaining child process.

- [ ] **Step 5: Commit**

```bash
git add CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py
git commit -m "feat: add recursive queue traversal exercise"
```

### Task 3: Persistent multiprocessing queue pool

**Files:**
- Modify: `CH_14_multithreading_and_multiprocessing/exercise_05/solution_00.py`
- Create: `CH_14_multithreading_and_multiprocessing/exercise_05/test_solution_00.py`

- [ ] **Step 1: Write tests proving persistence, order, exceptions, lifecycle, and cleanup**

```python
from __future__ import annotations

import multiprocessing

import pytest

from .solution_00 import PersistentWorkerPool, WorkerError, square


@pytest.mark.timeout(20)
def test_pool_reuses_workers_and_preserves_map_order() -> None:
    with PersistentWorkerPool(square, worker_count=2) as pool:
        first_pids: tuple[int, ...] = pool.worker_pids
        assert pool.map([3, 1, 2], timeout=5.0) == [9, 1, 4]
        assert pool.map([4], timeout=5.0) == [16]
        assert pool.worker_pids == first_pids


def test_pool_propagates_worker_failure() -> None:
    with PersistentWorkerPool(square, worker_count=1) as pool:
        task_id: int = pool.submit("bad")  # type: ignore[arg-type]
        with pytest.raises(WorkerError, match="TypeError"):
            pool.result(task_id, timeout=5.0)


def test_closed_pool_rejects_submission() -> None:
    pool: PersistentWorkerPool[int, int] = PersistentWorkerPool(square, worker_count=1)
    pool.close()
    with pytest.raises(RuntimeError, match="closed"):
        pool.submit(2)
    assert all(process.pid is None or not process.is_alive() for process in pool.workers)
```

- [ ] **Step 2: Run tests and observe failure of the cross-reference-only answer**

Run `uv run pytest CH_14_multithreading_and_multiprocessing/exercise_05/test_solution_00.py -vv`.

Expected: FAIL because no pool class or runnable behavior exists.

- [ ] **Step 3: Implement the generic persistent pool**

Use `TypeVar`, `Generic`, and these public interfaces:

```python
class WorkerError(RuntimeError):
    """A task raised in a worker process."""


class PersistentWorkerPool(Generic[InputT, ResultT]):
    def __init__(
        self,
        function: Callable[[InputT], ResultT],
        *,
        worker_count: int = 2,
        context: multiprocessing.context.BaseContext | None = None,
        shutdown_timeout: float = 5.0,
    ) -> None:
        """Start persistent queue workers for one spawn-picklable function."""

    @property
    def workers(self) -> tuple[multiprocessing.Process, ...]:
        """Return workers for lifecycle inspection."""

    @property
    def worker_pids(self) -> tuple[int, ...]:
        """Return started worker PIDs."""

    def submit(self, value: InputT) -> int:
        """Queue one value and return a monotonic task ID."""

    def result(self, task_id: int, *, timeout: float = 5.0) -> ResultT:
        """Return one result, retaining out-of-order replies in a local cache."""

    def map(self, values: Iterable[InputT], *, timeout: float = 5.0) -> list[ResultT]:
        """Return results in input order."""

    def close(self) -> None:
        """Idempotently send sentinels and join workers."""
```

Back the API with frozen `Task`, `TaskSuccess`, and `TaskFailure` dataclasses. `_worker_main` catches `Exception`, sends the exception class name and message, and continues serving later tasks. `result` raises `TimeoutError` on `Queue.get(timeout=...)`. `close` joins each process and raises `TimeoutError` after terminating a worker that does not stop. Add top-level `square(value: int) -> int` for the demonstration and spawn-safe tests.

- [ ] **Step 4: Verify**

```bash
uv run pytest CH_14_multithreading_and_multiprocessing/exercise_05/test_solution_00.py -vv
uv run ruff format --check CH_14_multithreading_and_multiprocessing/exercise_05
uv run ruff check CH_14_multithreading_and_multiprocessing/exercise_05
uv run pyrefly check CH_14_multithreading_and_multiprocessing/exercise_05
uv run mypy CH_14_multithreading_and_multiprocessing/exercise_05
uv run pyright CH_14_multithreading_and_multiprocessing/exercise_05
```

Expected: all commands exit 0; pytest reports 3 passed, worker PIDs remain stable inside the context, and all workers are stopped afterward.

- [ ] **Step 5: Commit**

```bash
git add CH_14_multithreading_and_multiprocessing/exercise_05/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_05/test_solution_00.py
git commit -m "feat: add persistent queue worker pool"
```

### Task 4: Allowlisted RPC over persistent queues

**Files:**
- Modify: `CH_14_multithreading_and_multiprocessing/exercise_06/solution_00.py`
- Create: `CH_14_multithreading_and_multiprocessing/exercise_06/test_solution_00.py`

- [ ] **Step 1: Write failing safe-RPC tests**

```python
from __future__ import annotations

import pytest

from .solution_00 import RemoteCallError, RpcWorkerPool, UnknownMethodError


def test_rpc_calls_registered_methods() -> None:
    with RpcWorkerPool(worker_count=2) as rpc:
        assert rpc.call("add", 2, 5, timeout=5.0) == 7
        assert rpc.call("repeat", "ab", count=3, timeout=5.0) == "ababab"


def test_rpc_rejects_unknown_method_without_killing_worker() -> None:
    with RpcWorkerPool(worker_count=1) as rpc:
        with pytest.raises(UnknownMethodError, match="missing"):
            rpc.call("missing", timeout=5.0)
        assert rpc.call("add", 1, 1, timeout=5.0) == 2


def test_rpc_propagates_argument_errors() -> None:
    with RpcWorkerPool(worker_count=1) as rpc:
        with pytest.raises(RemoteCallError, match="TypeError"):
            rpc.call("add", "one", 2, timeout=5.0)
```

- [ ] **Step 2: Run tests and verify the current unsafe worker fails**

Expected: FAIL because the existing worker deadlocks on unknown methods, has no result channel, and terminates children rather than shutting down.

- [ ] **Step 3: Implement request IDs, allowlisting, replies, and cooperative shutdown**

Expose:

```python
def add(left: int, right: int) -> int:
    return left + right


def repeat(value: str, *, count: int) -> str:
    if count < 0:
        raise ValueError("count must not be negative")
    return value * count


RPC_METHODS: Mapping[str, Callable[..., object]] = MappingProxyType(
    {"add": add, "repeat": repeat}
)


class RpcWorkerPool:
    def call(
        self,
        method: str,
        *args: object,
        timeout: float = 5.0,
        **kwargs: object,
    ) -> object:
        """Invoke one allowlisted method and return its value."""
```

Use frozen `RpcRequest`, `RpcSuccess`, `RpcFailure`, and `StopRequest` messages and a request-ID cache for out-of-order responses. Workers look up names only in `RPC_METHODS`; they never use `eval`, `getattr`, imports, or client-supplied callables. Unknown names return a distinct failure kind mapped to `UnknownMethodError`; method exceptions map to `RemoteCallError`. Context-manager cleanup sends sentinels, joins with a timeout, and checks nonzero exit codes.

- [ ] **Step 4: Verify**

```bash
uv run pytest CH_14_multithreading_and_multiprocessing/exercise_06/test_solution_00.py -vv
uv run ruff format --check CH_14_multithreading_and_multiprocessing/exercise_06
uv run ruff check CH_14_multithreading_and_multiprocessing/exercise_06
uv run pyrefly check CH_14_multithreading_and_multiprocessing/exercise_06
uv run mypy CH_14_multithreading_and_multiprocessing/exercise_06
uv run pyright CH_14_multithreading_and_multiprocessing/exercise_06
```

Expected: every command exits 0; pytest reports 3 passed and the same worker handles a valid call after an unknown method.

- [ ] **Step 5: Commit**

```bash
git add CH_14_multithreading_and_multiprocessing/exercise_06/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_06/test_solution_00.py
git commit -m "feat: add allowlisted queue RPC exercise"
```

### Task 5: Bounded parallel merge sort

**Files:**
- Modify: `CH_14_multithreading_and_multiprocessing/exercise_07/solution_00.py`
- Create: `CH_14_multithreading_and_multiprocessing/exercise_07/test_solution_00.py`

- [ ] **Step 1: Write failing merge, split, and parallel-sort tests**

```python
from __future__ import annotations

import multiprocessing

import pytest

from .solution_00 import merge, merge_sort, parallel_merge_sort, split


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ([], [], []),
        ([1, 3], [2, 4], [1, 2, 3, 4]),
        ([1, 1], [1], [1, 1, 1]),
    ],
)
def test_merge(left: list[int], right: list[int], expected: list[int]) -> None:
    assert merge(left, right) == expected


def test_split_never_creates_empty_chunks() -> None:
    assert split([], 4) == []
    assert split([3, 2], 8) == [[3], [2]]


@pytest.mark.timeout(20)
def test_parallel_merge_sort_matches_builtin() -> None:
    values: list[int] = [5, -1, 5, 0, 9, 2, -7]
    assert parallel_merge_sort(
        values,
        max_workers=3,
        context=multiprocessing.get_context("spawn"),
    ) == sorted(values)
    assert values == [5, -1, 5, 0, 9, 2, -7]


def test_sequential_merge_sort_handles_boundaries() -> None:
    assert merge_sort([]) == []
    assert merge_sort([1]) == [1]
```

- [ ] **Step 2: Run tests and expose the zero-chunk and empty-input bugs**

Run `uv run pytest CH_14_multithreading_and_multiprocessing/exercise_07/test_solution_00.py -vv`.

Expected: FAIL for empty input and when worker count exceeds input length.

- [ ] **Step 3: Implement deterministic bounded parallelism**

Preserve `merge`, `split`, `merge_sort`, and `multiprocessing_merge_sort`, and add:

```python
def parallel_merge_sort(
    values: Sequence[int],
    *,
    max_workers: int | None = None,
    context: multiprocessing.context.BaseContext | None = None,
) -> list[int]:
    if max_workers is not None and max_workers < 1:
        raise ValueError("max_workers must be positive")
    if not values:
        return []
    requested_workers: int = max_workers or multiprocessing.cpu_count()
    worker_count: int = min(requested_workers, len(values))
    chunks: list[list[int]] = split(values, worker_count)
    process_context: multiprocessing.context.BaseContext = (
        context if context is not None else multiprocessing.get_context("spawn")
    )
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=worker_count,
        mp_context=process_context,
    ) as executor:
        sorted_chunks: list[list[int]] = list(executor.map(merge_sort, chunks))
        while len(sorted_chunks) > 1:
            pairs: list[tuple[list[int], list[int]]] = list(
                zip(sorted_chunks[::2], sorted_chunks[1::2])
            )
            merged: list[list[int]] = list(executor.map(_merge_pair, pairs))
            if len(sorted_chunks) % 2:
                merged.append(sorted_chunks[-1])
            sorted_chunks = merged
    return sorted_chunks[0]


def multiprocessing_merge_sort(data: Sequence[int]) -> list[int]:
    return parallel_merge_sort(data)
```

`split` distributes the remainder across the first chunks and rejects non-positive sizes. `merge` must not mutate either input. `_merge_pair` is top-level and spawn-picklable.

- [ ] **Step 4: Verify**

```bash
uv run pytest CH_14_multithreading_and_multiprocessing/exercise_07/test_solution_00.py -vv
uv run ruff format --check CH_14_multithreading_and_multiprocessing/exercise_07
uv run ruff check CH_14_multithreading_and_multiprocessing/exercise_07
uv run pyrefly check CH_14_multithreading_and_multiprocessing/exercise_07
uv run mypy CH_14_multithreading_and_multiprocessing/exercise_07
uv run pyright CH_14_multithreading_and_multiprocessing/exercise_07
```

Expected: every command exits 0 and pytest reports 6 parameterized cases/tests passing.

- [ ] **Step 5: Commit**

```bash
git add CH_14_multithreading_and_multiprocessing/exercise_07/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_07/test_solution_00.py
git commit -m "feat: add bounded parallel merge sort"
```

### Task 6: Per-exercise documentation and chapter links

**Files:**
- Create: `CH_14_multithreading_and_multiprocessing/exercise_03/README.rst`
- Create: `CH_14_multithreading_and_multiprocessing/exercise_04/README.rst`
- Create: `CH_14_multithreading_and_multiprocessing/exercise_05/README.rst`
- Create: `CH_14_multithreading_and_multiprocessing/exercise_06/README.rst`
- Create: `CH_14_multithreading_and_multiprocessing/exercise_07/README.rst`
- Modify: `CH_14_multithreading_and_multiprocessing/README.rst`

- [ ] **Step 1: Write all five READMEs**

Each README repeats its exact chapter question, documents public APIs and boundary choices, lists no third-party runtime dependency, and provides its matching command pair:

```rst
.. code-block:: console

   uv run python -m CH_14_multithreading_and_multiprocessing.exercise_03.solution_00
   uv run pytest CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py -vv
   uv run python -m CH_14_multithreading_and_multiprocessing.exercise_04.solution_00
   uv run pytest CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py -vv
   uv run python -m CH_14_multithreading_and_multiprocessing.exercise_05.solution_00
   uv run pytest CH_14_multithreading_and_multiprocessing/exercise_05/test_solution_00.py -vv
   uv run python -m CH_14_multithreading_and_multiprocessing.exercise_06.solution_00
   uv run pytest CH_14_multithreading_and_multiprocessing/exercise_06/test_solution_00.py -vv
   uv run python -m CH_14_multithreading_and_multiprocessing.exercise_07.solution_00
   uv run pytest CH_14_multithreading_and_multiprocessing/exercise_07/test_solution_00.py -vv
```

Exercise 3 and 4 READMEs explicitly identify their historical specialized files as retained alternatives. Exercise 5 documents persistent PIDs and exception behavior. Exercise 6 documents the allowlist security boundary. Exercise 7 documents integer-only input, non-mutation, and bounded workers.

Use relevant immutable references:

- exercises 3-5:
  `https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_07_thread_batch_processing.py`
  and `T_08_process_batch_processing.py`;
- exercise 5 and 7:
  `T_09_multiprocessing_pool.py`;
- exercise 6:
  `T_17_remote_multiprocessing/server.py` and `functions.py`.

- [ ] **Step 2: Link chapter items 3 through 7**

Change only their RST presentation: retain exact question text and link each item to `exercise_03/` through `exercise_07/`. Accommodate concurrent edits to items 1 and 2.

- [ ] **Step 3: Run packet verification**

```bash
uv run pytest CH_14_multithreading_and_multiprocessing/exercise_03 CH_14_multithreading_and_multiprocessing/exercise_04 CH_14_multithreading_and_multiprocessing/exercise_05 CH_14_multithreading_and_multiprocessing/exercise_06 CH_14_multithreading_and_multiprocessing/exercise_07 -vv
uv run ruff format --check CH_14_multithreading_and_multiprocessing
uv run ruff check CH_14_multithreading_and_multiprocessing
uv run pyrefly check CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_05/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_06/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_07/solution_00.py
uv run mypy CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_05/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_06/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_07/solution_00.py
uv run pyright CH_14_multithreading_and_multiprocessing/exercise_03/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_05/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_06/solution_00.py CH_14_multithreading_and_multiprocessing/exercise_07/solution_00.py
```

Expected: every command exits 0; no worker remains in `multiprocessing.active_children()`.

- [ ] **Step 4: Confirm historical answers are byte-for-byte unchanged**

Run:

```bash
git diff --exit-code HEAD -- CH_14_multithreading_and_multiprocessing/exercise_03/threading_solution_00.py CH_14_multithreading_and_multiprocessing/exercise_03/multiprocessing_solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/threading_solution_00.py CH_14_multithreading_and_multiprocessing/exercise_04/multiprocessing_solution_00.py
```

Expected: exit 0 with no output.

- [ ] **Step 5: Commit documentation**

```bash
git add CH_14_multithreading_and_multiprocessing/README.rst CH_14_multithreading_and_multiprocessing/exercise_03/README.rst CH_14_multithreading_and_multiprocessing/exercise_04/README.rst CH_14_multithreading_and_multiprocessing/exercise_05/README.rst CH_14_multithreading_and_multiprocessing/exercise_06/README.rst CH_14_multithreading_and_multiprocessing/exercise_07/README.rst
git commit -m "docs: document chapter 14 worker exercises"
```

## Packet acceptance

- [ ] Run the packet on Python 3.10 and Python 3.14.
- [ ] Confirm every queue operation and process join has a bounded timeout.
- [ ] Confirm errors cross worker boundaries and no implementation silently drops them.
- [ ] Confirm no fixed ports, network access, or external files are required.
- [ ] Confirm the four historical alternatives remain unchanged.
