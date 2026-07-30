# Chapter 8 Metaclass Solutions Implementation

**For agentic workers:** REQUIRED SUB-SKILL: Use
`superpowers:subagent-driven-development` (recommended) or
`superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Deliver typed, import-safe, tested canonical answers and exercise
documentation for all three Chapter 8 metaclass exercises.

**Architecture:** Keep each exercise independent and expose the metaclass being
taught as its public API. Class-definition-time validation is deterministic:
required members allow inheritance, required bases allow indirect inheritance,
and method wrapping handles ordinary, static, and class methods without
touching dunder methods. Historical alternatives are not changed.

**Tech Stack:** Python 3.10, pytest, Ruff, Pyrefly, mypy, Pyright

---

## File map and public APIs

- `CH_08_metaclasses/exercise_01/solution_00.py`
  - `ExpectedAttrsMeta`
  - `Trade.buy()` and `Trade.sell()`
- `CH_08_metaclasses/exercise_02/solution_00.py`
  - `SomeBaseClass`
  - `ExpectedBasesMeta`
  - `Trade`
- `CH_08_metaclasses/exercise_03/solution_00.py`
  - `WrappingMeta`
  - `print_call`
  - `SomeClass`
- Every exercise gains `README.rst` and `test_solution_00.py`.
- `CH_08_metaclasses/README.rst` becomes a concise linked exercise index.
- Do not modify any `solution_01.py` file or another packet's files.

### Task 1: Validate required attributes and methods

**Files:**

- Modify: `CH_08_metaclasses/exercise_01/solution_00.py`
- Create: `CH_08_metaclasses/exercise_01/test_solution_00.py`
- Create: `CH_08_metaclasses/exercise_01/README.rst`

- [ ] **Step 1: Write the failing metaclass contract tests**

Create `CH_08_metaclasses/exercise_01/test_solution_00.py`:

```python
import pytest

from CH_08_metaclasses.exercise_01.solution_00 import (
    ExpectedAttrsMeta,
    Trade,
)


def test_trade_exposes_required_methods() -> None:
    trade: Trade = Trade()

    assert trade.buy() == "buy"
    assert trade.sell() == "sell"


def test_inherited_members_satisfy_requirement() -> None:
    class Parent:
        inherited_value: int = 3

    class Child(
        Parent,
        metaclass=ExpectedAttrsMeta,
        required_attributes=("inherited_value",),
    ):
        pass

    assert Child.inherited_value == 3


def test_missing_members_are_reported_together() -> None:
    with pytest.raises(
        AttributeError,
        match=r"Broken missing required attribute\(s\): buy, sell",
    ):

        class Broken(
            metaclass=ExpectedAttrsMeta,
            required_attributes=("buy", "sell"),
        ):
            pass


def test_empty_requirement_allows_plain_class() -> None:
    class Plain(metaclass=ExpectedAttrsMeta):
        value: int = 7

    assert Plain.value == 7
```

- [ ] **Step 2: Run the focused test and confirm the old implementation fails**

Run:

```bash
uv run pytest CH_08_metaclasses/exercise_01/test_solution_00.py -v
```

Expected: collection fails because the old module raises while defining its
empty `Trade`, or tests fail because `ExpectedAttrsMeta` does not accept
`required_attributes`.

- [ ] **Step 3: Replace the canonical implementation with the reusable API**

Replace `CH_08_metaclasses/exercise_01/solution_00.py` with:

```python
"""Validate required class members while a class is being created."""

from collections.abc import Mapping


class ExpectedAttrsMeta(type):
    """Require named attributes to be available on the resulting class."""

    def __new__(
        metaclass: type["ExpectedAttrsMeta"],
        name: str,
        bases: tuple[type, ...],
        namespace: Mapping[str, object],
        *,
        required_attributes: tuple[str, ...] = (),
    ) -> "ExpectedAttrsMeta":
        class_namespace: dict[str, object] = dict(namespace)
        created_class: ExpectedAttrsMeta = super().__new__(
            metaclass,
            name,
            bases,
            class_namespace,
        )
        missing: tuple[str, ...] = tuple(
            attribute
            for attribute in required_attributes
            if not hasattr(created_class, attribute)
        )
        if missing:
            missing_text: str = ", ".join(missing)
            raise AttributeError(
                f"{name} missing required attribute(s): {missing_text}"
            )
        return created_class


class Trade(
    metaclass=ExpectedAttrsMeta,
    required_attributes=("buy", "sell"),
):
    """Small valid example using the validation metaclass."""

    def buy(self) -> str:
        """Return the name of the demonstrated operation."""
        return "buy"

    def sell(self) -> str:
        """Return the name of the demonstrated operation."""
        return "sell"


def main() -> None:
    """Demonstrate that the canonical class satisfies its contract."""
    trade: Trade = Trade()
    print(trade.buy(), trade.sell())


if __name__ == "__main__":
    main()
```

The post-creation `hasattr` check is intentional: inherited attributes and
methods count as available. Preserve the existing public names
`ExpectedAttrsMeta` and `Trade`.

- [ ] **Step 4: Run the focused test and static checks**

Run:

```bash
uv run pytest CH_08_metaclasses/exercise_01/test_solution_00.py -v
uv run ruff format --check CH_08_metaclasses/exercise_01
uv run ruff check CH_08_metaclasses/exercise_01
uv run pyrefly check CH_08_metaclasses/exercise_01/solution_00.py
uv run mypy CH_08_metaclasses/exercise_01/solution_00.py
uv run pyright CH_08_metaclasses/exercise_01/solution_00.py
```

Expected: four pytest tests pass and every quality command exits zero.

- [ ] **Step 5: Add the exercise README**

Create `CH_08_metaclasses/exercise_01/README.rst` with:

```rst
Exercise 1: required attributes
===============================

Question
--------

Create a metaclass that tests whether attributes and methods are available.

Answer
------

``ExpectedAttrsMeta`` validates the completed class at definition time. Members
inherited from a base class satisfy the requirement; all missing names are
reported in one ``AttributeError``. ``Trade`` demonstrates a valid class.

Dependencies
------------

Only the Python 3.10 standard library is required at runtime. Tests use pytest.

Run
---

.. code-block:: console

   uv run python -m CH_08_metaclasses.exercise_01.solution_00
   uv run pytest CH_08_metaclasses/exercise_01/test_solution_00.py -v

Upstream reference
------------------

The class-construction pattern is informed by
`T_01_basic_metaclass.rst <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_08_metaclasses/T_01_basic_metaclass.rst>`_.
The upstream material is MIT licensed; this answer is self-contained and does
not import it at runtime.
```

- [ ] **Step 6: Re-run the exercise test and commit**

Run:

```bash
uv run pytest CH_08_metaclasses/exercise_01/test_solution_00.py -v
git add CH_08_metaclasses/exercise_01/solution_00.py CH_08_metaclasses/exercise_01/test_solution_00.py CH_08_metaclasses/exercise_01/README.rst
git commit -m "feat: complete metaclass attribute exercise"
```

Expected: tests pass; the commit contains only Exercise 1 files.

### Task 2: Validate required base classes

**Files:**

- Modify: `CH_08_metaclasses/exercise_02/solution_00.py`
- Create: `CH_08_metaclasses/exercise_02/test_solution_00.py`
- Create: `CH_08_metaclasses/exercise_02/README.rst`

- [ ] **Step 1: Write the failing inheritance contract tests**

Create `CH_08_metaclasses/exercise_02/test_solution_00.py`:

```python
import pytest

from CH_08_metaclasses.exercise_02.solution_00 import (
    ExpectedBasesMeta,
    SomeBaseClass,
    Trade,
)


def test_trade_inherits_required_base() -> None:
    assert issubclass(Trade, SomeBaseClass)


def test_indirect_inheritance_is_accepted() -> None:
    class Intermediate(SomeBaseClass):
        pass

    class Indirect(
        Intermediate,
        metaclass=ExpectedBasesMeta,
        expected_bases=(SomeBaseClass,),
    ):
        pass

    assert issubclass(Indirect, SomeBaseClass)


def test_missing_required_base_raises_type_error() -> None:
    with pytest.raises(
        TypeError,
        match="Broken must inherit from SomeBaseClass",
    ):

        class Broken(
            metaclass=ExpectedBasesMeta,
            expected_bases=(SomeBaseClass,),
        ):
            pass


def test_multiple_requirements_report_every_missing_base() -> None:
    class OtherBase:
        pass

    with pytest.raises(
        TypeError,
        match="Partial must inherit from OtherBase",
    ):

        class Partial(
            SomeBaseClass,
            metaclass=ExpectedBasesMeta,
            expected_bases=(SomeBaseClass, OtherBase),
        ):
            pass
```

- [ ] **Step 2: Run the test and confirm the current direct-base check fails**

Run:

```bash
uv run pytest CH_08_metaclasses/exercise_02/test_solution_00.py -v
```

Expected: collection or assertions fail because the existing module defines an
invalid class at import time and checks only direct bases.

- [ ] **Step 3: Implement indirect required-base validation**

Replace `CH_08_metaclasses/exercise_02/solution_00.py` with:

```python
"""Validate required inheritance while a class is being created."""

from collections.abc import Mapping


class SomeBaseClass:
    """Base class required by the canonical example."""


class ExpectedBasesMeta(type):
    """Require the resulting class to inherit from specified classes."""

    def __new__(
        metaclass: type["ExpectedBasesMeta"],
        name: str,
        bases: tuple[type, ...],
        namespace: Mapping[str, object],
        *,
        expected_bases: tuple[type, ...] = (),
    ) -> "ExpectedBasesMeta":
        class_namespace: dict[str, object] = dict(namespace)
        created_class: ExpectedBasesMeta = super().__new__(
            metaclass,
            name,
            bases,
            class_namespace,
        )
        missing: tuple[type, ...] = tuple(
            base
            for base in expected_bases
            if not issubclass(created_class, base)
        )
        if missing:
            missing_text: str = ", ".join(base.__name__ for base in missing)
            raise TypeError(f"{name} must inherit from {missing_text}")
        return created_class


class Trade(
    SomeBaseClass,
    metaclass=ExpectedBasesMeta,
    expected_bases=(SomeBaseClass,),
):
    """Valid example inheriting the required base."""


def main() -> None:
    """Demonstrate successful inheritance validation."""
    print(issubclass(Trade, SomeBaseClass))


if __name__ == "__main__":
    main()
```

Use `issubclass` on the completed class so indirect inheritance is valid. Do
not restore the old import-time `BrokenTrade` example.

- [ ] **Step 4: Run tests and strict checks**

Run:

```bash
uv run pytest CH_08_metaclasses/exercise_02/test_solution_00.py -v
uv run ruff format --check CH_08_metaclasses/exercise_02
uv run ruff check CH_08_metaclasses/exercise_02
uv run pyrefly check CH_08_metaclasses/exercise_02/solution_00.py
uv run mypy CH_08_metaclasses/exercise_02/solution_00.py
uv run pyright CH_08_metaclasses/exercise_02/solution_00.py
```

Expected: four tests pass and all quality commands exit zero.

- [ ] **Step 5: Document the behavioral choice and provenance**

Create `CH_08_metaclasses/exercise_02/README.rst`:

```rst
Exercise 2: required base classes
=================================

Question
--------

Create a metaclass that tests whether specific classes are inherited.

Answer
------

``ExpectedBasesMeta`` checks the completed class with ``issubclass``. Direct
and indirect inheritance satisfy the contract. A missing required base raises a
``TypeError`` during class definition and names every missing base.

Dependencies
------------

Only the Python 3.10 standard library is required at runtime. Tests use pytest.

Run
---

.. code-block:: console

   uv run python -m CH_08_metaclasses.exercise_02.solution_00
   uv run pytest CH_08_metaclasses/exercise_02/test_solution_00.py -v

Upstream reference
------------------

The inheritance checks are informed by
`T_05_custom_type_checks.rst <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_08_metaclasses/T_05_custom_type_checks.rst>`_.
The upstream material is MIT licensed; this answer remains offline and
self-contained.
```

- [ ] **Step 6: Re-run and commit Exercise 2**

Run:

```bash
uv run pytest CH_08_metaclasses/exercise_02/test_solution_00.py -v
git add CH_08_metaclasses/exercise_02/solution_00.py CH_08_metaclasses/exercise_02/test_solution_00.py CH_08_metaclasses/exercise_02/README.rst
git commit -m "feat: complete metaclass inheritance exercise"
```

Expected: tests pass; only Exercise 2 files are staged.

### Task 3: Wrap ordinary, static, and class methods

**Files:**

- Modify: `CH_08_metaclasses/exercise_03/solution_00.py`
- Create: `CH_08_metaclasses/exercise_03/test_solution_00.py`
- Create: `CH_08_metaclasses/exercise_03/README.rst`
- Modify: `CH_08_metaclasses/README.rst`

- [ ] **Step 1: Write failing descriptor-aware wrapping tests**

Create `CH_08_metaclasses/exercise_03/test_solution_00.py`:

```python
from collections.abc import Callable

from CH_08_metaclasses.exercise_03.solution_00 import WrappingMeta


def test_wraps_supported_method_descriptors_once() -> None:
    calls: list[str] = []

    def wrapper(
        function: Callable[..., object],
    ) -> Callable[..., object]:
        def wrapped(*args: object, **kwargs: object) -> object:
            calls.append(function.__name__)
            return function(*args, **kwargs)

        return wrapped

    class Example(metaclass=WrappingMeta, wrapper=wrapper):
        label: str = "kept"

        def instance_method(self, value: int) -> int:
            return value + 1

        @staticmethod
        def static_method(value: int) -> int:
            return value + 2

        @classmethod
        def class_method(cls, value: int) -> tuple[str, int]:
            return cls.__name__, value + 3

    example: Example = Example()

    assert example.label == "kept"
    assert example.instance_method(1) == 2
    assert Example.static_method(1) == 3
    assert Example.class_method(1) == ("Example", 4)
    assert calls == ["instance_method", "static_method", "class_method"]


def test_dunder_methods_are_not_wrapped() -> None:
    calls: list[str] = []

    def wrapper(
        function: Callable[..., object],
    ) -> Callable[..., object]:
        def wrapped(*args: object, **kwargs: object) -> object:
            calls.append(function.__name__)
            return function(*args, **kwargs)

        return wrapped

    class Example(metaclass=WrappingMeta, wrapper=wrapper):
        def __init__(self) -> None:
            self.value: int = 4

        def read(self) -> int:
            return self.value

    example: Example = Example()

    assert calls == []
    assert example.read() == 4
    assert calls == ["read"]


def test_missing_wrapper_leaves_methods_unchanged() -> None:
    class Example(metaclass=WrappingMeta):
        def read(self) -> int:
            return 5

    assert Example().read() == 5
```

- [ ] **Step 2: Run the focused test and observe descriptor failures**

Run:

```bash
uv run pytest CH_08_metaclasses/exercise_03/test_solution_00.py -v
```

Expected: tests fail because the old implementation is not import-safe and
does not preserve `staticmethod` and `classmethod` descriptors.

- [ ] **Step 3: Implement descriptor-aware method wrapping**

Replace `CH_08_metaclasses/exercise_03/solution_00.py` with:

```python
"""Wrap methods supplied in a class namespace through a metaclass."""

import functools
import inspect
from collections.abc import Callable, Mapping
from typing import ParamSpec, TypeVar, cast

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")
Method = Callable[..., object]
Wrapper = Callable[[Method], Method]


class WrappingMeta(type):
    """Apply a wrapper to each non-dunder method defined by a class."""

    def __new__(
        metaclass: type["WrappingMeta"],
        name: str,
        bases: tuple[type, ...],
        namespace: Mapping[str, object],
        *,
        wrapper: Wrapper | None = None,
    ) -> "WrappingMeta":
        wrapped_namespace: dict[str, object] = dict(namespace)
        if wrapper is not None:
            for attribute_name, attribute in namespace.items():
                if attribute_name.startswith("__"):
                    continue
                if isinstance(attribute, staticmethod):
                    static_function: Method = cast(Method, attribute.__func__)
                    wrapped_namespace[attribute_name] = staticmethod(
                        wrapper(static_function)
                    )
                elif isinstance(attribute, classmethod):
                    class_function: Method = cast(Method, attribute.__func__)
                    wrapped_namespace[attribute_name] = classmethod(
                        wrapper(class_function)
                    )
                elif inspect.isfunction(attribute):
                    method: Method = cast(Method, attribute)
                    wrapped_namespace[attribute_name] = wrapper(method)
        return super().__new__(
            metaclass,
            name,
            bases,
            wrapped_namespace,
        )


def print_call(
    function: Callable[Parameters, Result],
) -> Callable[Parameters, Result]:
    """Print a method name before delegating to it."""

    @functools.wraps(function)
    def wrapped(
        *args: Parameters.args,
        **kwargs: Parameters.kwargs,
    ) -> Result:
        print(f"calling {function.__name__}")
        return function(*args, **kwargs)

    return wrapped


class SomeClass(metaclass=WrappingMeta, wrapper=cast(Wrapper, print_call)):
    """Demonstrate wrapping an ordinary method."""

    def some_method(self) -> str:
        """Return a deterministic demonstration value."""
        return "wrapped"


def main() -> None:
    """Run the wrapped demonstration method."""
    print(SomeClass().some_method())


if __name__ == "__main__":
    main()
```

Keep the single generic-wrapper cast exactly at the dynamic metaclass boundary
shown above; do not introduce a repository-wide `Any` or missing-import
suppression.

- [ ] **Step 4: Run focused tests and quality checks**

Run:

```bash
uv run pytest CH_08_metaclasses/exercise_03/test_solution_00.py -v
uv run ruff format --check CH_08_metaclasses/exercise_03
uv run ruff check CH_08_metaclasses/exercise_03
uv run pyrefly check CH_08_metaclasses/exercise_03/solution_00.py
uv run mypy CH_08_metaclasses/exercise_03/solution_00.py
uv run pyright CH_08_metaclasses/exercise_03/solution_00.py
```

Expected: three tests pass and all quality commands exit zero.

- [ ] **Step 5: Add the exercise README and linked chapter index**

Create `CH_08_metaclasses/exercise_03/README.rst`:

```rst
Exercise 3: wrapping class methods
==================================

Question
--------

Build a metaclass that wraps every method with a decorator, for example:

.. code-block:: python

   class SomeClass(metaclass=WrappingMeta, wrapper=some_wrapper):
       pass

Answer
------

``WrappingMeta`` wraps ordinary methods, static methods, and class methods
defined directly in the class body. It preserves descriptor behavior and
leaves data attributes, inherited methods, and dunder methods unchanged.

Dependencies
------------

Only the Python 3.10 standard library is required at runtime. Tests use pytest.

Run
---

.. code-block:: console

   uv run python -m CH_08_metaclasses.exercise_03.solution_00
   uv run pytest CH_08_metaclasses/exercise_03/test_solution_00.py -v

Upstream references
-------------------

Metaclass keyword arguments and class namespace handling are informed by
`T_02_arguments_to_metaclasses.rst <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_08_metaclasses/T_02_arguments_to_metaclasses.rst>`_
and
`T_03_accessing_metaclass_attributes.rst <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_08_metaclasses/T_03_accessing_metaclass_attributes.rst>`_.
The upstream material is MIT licensed; no runtime import or download is used.
```

Replace `CH_08_metaclasses/README.rst` with:

```rst
Chapter 8 - metaclasses
=======================

1. `Required attributes <exercise_01/>`_
2. `Required base classes <exercise_02/>`_
3. `Wrapping class methods <exercise_03/>`_
```

- [ ] **Step 6: Run the complete Chapter 8 packet**

Run:

```bash
uv run pytest CH_08_metaclasses -v
uv run ruff format --check CH_08_metaclasses
uv run ruff check CH_08_metaclasses
uv run pyrefly check CH_08_metaclasses
uv run mypy CH_08_metaclasses
uv run pyright CH_08_metaclasses
```

Expected: all Chapter 8 tests pass with zero static-quality findings.

- [ ] **Step 7: Commit the final exercise and chapter index**

Run:

```bash
git add CH_08_metaclasses/exercise_03/solution_00.py CH_08_metaclasses/exercise_03/test_solution_00.py CH_08_metaclasses/exercise_03/README.rst CH_08_metaclasses/README.rst
git commit -m "feat: complete metaclass wrapping exercise"
```

Expected: the commit contains only Exercise 3 and the Chapter 8 index.

### Task 4: Packet self-review

**Files:**

- Review: `CH_08_metaclasses/README.rst`
- Review: `CH_08_metaclasses/exercise_01/`
- Review: `CH_08_metaclasses/exercise_02/`
- Review: `CH_08_metaclasses/exercise_03/`

- [ ] **Step 1: Verify directory-contract completeness**

Run:

```bash
find CH_08_metaclasses -maxdepth 2 -type f | sort
```

Expected: each `exercise_NN` contains `__init__.py`, `README.rst`,
`solution_00.py`, and `test_solution_00.py`; no historical alternative changed.

- [ ] **Step 2: Scan for plan-forbidden placeholders in implemented files**

Run:

```bash
```

Expected: no matches.

- [ ] **Step 3: Confirm the packet diff is isolated**

Run:

```bash
git status --short
git diff --stat master -- CH_08_metaclasses
```

Expected: no uncommitted Chapter 8 changes; the diff names no file outside the
owned packet and its plan.
