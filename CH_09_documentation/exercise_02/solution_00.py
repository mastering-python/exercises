"""Flatten measurements stored in explicitly typed nested containers."""

from typing import TypeAlias

NestedMeasurements: TypeAlias = dict[str, list[tuple[int, float]]]


def flatten_measurements(values: NestedMeasurements) -> list[float]:
    """Return measurement values in mapping and row insertion order."""
    flattened: list[float] = []
    rows: list[tuple[int, float]]
    row: tuple[int, float]
    for rows in values.values():
        for row in rows:
            flattened.append(row[1])
    return flattened


def main() -> None:
    """Print a canonical nested-measurement demonstration."""
    values: NestedMeasurements = {
        "north": [(1, 1.5), (2, 2.5)],
    }
    print(flatten_measurements(values))


if __name__ == "__main__":
    main()
