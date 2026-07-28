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
        self._next_sequence: int = 0
        self._references: dict[
            int,
            weakref.ReferenceType[Instance],
        ] = {}

    @property
    def instances(self) -> tuple[Instance, ...]:
        """Return live instances in deterministic creation order."""
        live: list[Instance] = []
        dead_sequences: list[int] = []
        reference_items: list[tuple[int, weakref.ReferenceType[Instance]]] = list(
            self._references.items()
        )
        for sequence, reference in reference_items:
            instance: Instance | None = reference()
            if instance is None:
                dead_sequences.append(sequence)
            else:
                live.append(instance)
        for sequence in dead_sequences:
            self._references.pop(sequence, None)
        return tuple(live)

    @property
    def live_count(self) -> int:
        """Return the number of tracked instances still alive."""
        return len(self.instances)

    def create(self, *args: object, **kwargs: object) -> Instance:
        """Construct, track, and return an instance."""
        instance: Instance = self._instance_type(*args, **kwargs)
        sequence: int = self._next_sequence
        manager_reference: weakref.ReferenceType[InstanceManager[Instance]]
        manager_reference = weakref.ref(self)

        def discard(
            reference: weakref.ReferenceType[Instance],
        ) -> None:
            del reference
            manager: InstanceManager[Instance] | None = manager_reference()
            if manager is not None:
                manager._references.pop(sequence, None)

        try:
            reference: weakref.ReferenceType[Instance] = weakref.ref(
                instance,
                discard,
            )
        except TypeError:
            raise TypeError(
                "instances must support weak references",
            ) from None

        self._references[sequence] = reference
        self._next_sequence += 1
        count: int = self.live_count
        if count > self._max_instances:
            warnings.warn(
                f"{count} live {self._instance_type.__name__} instances",
                ResourceWarning,
                stacklevel=2,
            )
        return instance


def main() -> None:
    """Demonstrate weak live-instance tracking."""

    class Resource:
        """A weak-referenceable demonstration resource."""

    manager: InstanceManager[Resource] = InstanceManager(
        Resource,
        max_instances=2,
    )
    first: Resource = manager.create()
    second: Resource = manager.create()
    print(manager.instances == (first, second))


if __name__ == "__main__":
    main()
