"""Tests for a fixed, heterogeneous user-record type."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import NoneType
from typing import get_type_hints

from .solution_00 import Contact, UserRecord, describe_user, main


def test_describe_active_user() -> None:
    user: UserRecord = {
        "name": "Ada",
        "age": 36,
        "active": True,
        "contact": {
            "email": "ada@example.test",
            "phone": "+31 20 123 4567",
        },
    }

    assert describe_user(user) == "Ada (36) active: ada@example.test"


def test_describe_inactive_user() -> None:
    user: UserRecord = {
        "name": "Grace",
        "age": 40,
        "active": False,
        "contact": {
            "email": "grace@example.test",
            "phone": "+1 555 0100",
        },
    }

    assert describe_user(user) == "Grace (40) inactive: grace@example.test"


def test_contact_allows_a_nullable_phone() -> None:
    contact: Contact = {
        "email": "ada@example.test",
        "phone": None,
    }
    user: UserRecord = {
        "name": "Ada",
        "age": 36,
        "active": True,
        "contact": contact,
    }

    assert user["contact"]["phone"] is None
    assert describe_user(user) == "Ada (36) active: ada@example.test"


def test_typed_dict_field_hints_are_exact() -> None:
    assert get_type_hints(Contact) == {
        "email": str,
        "phone": str | None,
    }
    assert get_type_hints(UserRecord) == {
        "name": str,
        "age": int,
        "active": bool,
        "contact": Contact,
    }


def test_function_annotations_are_exact() -> None:
    assert get_type_hints(describe_user) == {
        "user": UserRecord,
        "return": str,
    }
    assert get_type_hints(main) == {"return": NoneType}


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_09_documentation.exercise_01.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_module_prints_demonstration() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_09_documentation.exercise_01.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == "Ada (36) active: ada@example.test\n"
    assert completed.stderr == ""
