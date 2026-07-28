"""Describe a user record represented by nested typed dictionaries."""

from typing import TypedDict


class Contact(TypedDict):
    """Contact details stored in a user record."""

    email: str
    phone: str | None


class UserRecord(TypedDict):
    """A fixed, heterogeneous user record."""

    name: str
    age: int
    active: bool
    contact: Contact


def describe_user(user: UserRecord) -> str:
    """Return a compact description of *user*."""
    status: str = "active" if user["active"] else "inactive"
    return f"{user['name']} ({user['age']}) {status}: {user['contact']['email']}"


def main() -> None:
    """Print a demonstration user description."""
    user: UserRecord = {
        "name": "Ada",
        "age": 36,
        "active": True,
        "contact": {
            "email": "ada@example.test",
            "phone": None,
        },
    }
    print(describe_user(user))


if __name__ == "__main__":
    main()
