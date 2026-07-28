from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import ClassVar

from .solution_00 import Borg

REPOSITORY_ROOT: Path = Path(__file__).resolve().parents[2]
SOLUTION_PATH: Path = Path(__file__).with_name("solution_00.py")
MODULE_NAME: str = "CH_04_design_patterns.exercise_03.solution_00"


def test_direct_borg_instances_share_mutations_and_deletions() -> None:
    first: Borg = Borg()
    second: Borg = Borg()
    attribute_name: str = "answer"

    setattr(first, attribute_name, 42)

    assert getattr(second, attribute_name) == 42

    delattr(second, attribute_name)

    assert not hasattr(first, attribute_name)


def test_instances_of_one_direct_subclass_share_state() -> None:
    class Feature(Borg):
        enabled: bool

    first: Feature = Feature()
    second: Feature = Feature()

    first.enabled = True

    assert second.enabled is True

    del second.enabled

    assert not hasattr(first, "enabled")


def test_sibling_subclasses_have_isolated_state() -> None:
    class Left(Borg):
        label: str

    class Right(Borg):
        label: str

    left: Left = Left()
    right: Right = Right()
    left.label = "left"

    assert not hasattr(right, "label")

    right.label = "right"

    assert left.label == "left"
    assert right.label == "right"


def test_parent_subclass_and_grandchild_have_isolated_state() -> None:
    class Parent(Borg):
        value: int

    class Grandchild(Parent):
        pass

    parent: Parent = Parent()
    grandchild: Grandchild = Grandchild()
    parent.value = 10

    assert not hasattr(grandchild, "value")

    grandchild.value = 20

    assert parent.value == 10
    assert grandchild.value == 20


def test_base_class_and_subclass_have_isolated_state() -> None:
    class Child(Borg):
        pass

    base: Borg = Borg()
    child: Child = Child()
    attribute_name: str = "base_only"
    setattr(base, attribute_name, "base")

    assert not hasattr(child, attribute_name)

    delattr(base, attribute_name)


def test_new_instances_see_existing_exact_class_state() -> None:
    class Settings(Borg):
        theme: str

    first: Settings = Settings()
    first.theme = "dark"

    later: Settings = Settings()

    assert later.theme == "dark"


def test_instances_keep_ordinary_identity_and_hash_semantics() -> None:
    class Service(Borg):
        pass

    first: Service = Service()
    second: Service = Service()

    assert first is not second
    assert first != second
    assert len({first, second}) == 2
    assert hash(first) == object.__hash__(first)
    assert hash(second) == object.__hash__(second)


def test_subclass_init_assignments_update_shared_state() -> None:
    class Configuration(Borg):
        value: int

        def __init__(self, value: int) -> None:
            self.value = value

    first: Configuration = Configuration(1)
    second: Configuration = Configuration(2)

    assert first.value == 2
    assert second.value == 2


def test_instantiation_does_not_reset_existing_state() -> None:
    class Persistent(Borg):
        marker: str

    first: Persistent = Persistent()
    first.marker = "kept"

    second: Persistent = Persistent()

    assert first.marker == "kept"
    assert second.marker == "kept"


def test_subclass_keywords_are_forwarded_to_cooperative_bases() -> None:
    class KeywordBase:
        tag: ClassVar[str]

        def __init_subclass__(cls, *, tag: str, **kwargs: object) -> None:
            super().__init_subclass__(**kwargs)
            cls.tag = tag

    class TaggedBorg(Borg, KeywordBase, tag="configured"):
        value: int

    first: TaggedBorg = TaggedBorg()
    second: TaggedBorg = TaggedBorg()
    first.value = 7

    assert TaggedBorg.tag == "configured"
    assert second.value == 7


def test_import_is_silent() -> None:
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", f"import {MODULE_NAME}"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_guarded_demo_runs_only_as_a_script() -> None:
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, str(SOLUTION_PATH)],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout == "False\nPython\n"
    assert result.stderr == ""
