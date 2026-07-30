"""Tests for weak live-instance tracking."""

import gc
import warnings
import weakref

import pytest

from CH_12_performance.exercise_03.solution_00 import InstanceManager


class Resource:
    def __init__(self, name: str) -> None:
        self.name: str = name


def test_first_instance_at_limit_emits_no_warning() -> None:
    manager: InstanceManager[Resource] = InstanceManager(
        Resource,
        max_instances=1,
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)
        instance: Resource = manager.create("at-limit")

    assert manager.instances == (instance,)
    assert manager.live_count == 1


def test_warns_above_limit_and_releases_collected_instances() -> None:
    manager: InstanceManager[Resource] = InstanceManager(
        Resource,
        max_instances=1,
    )
    first: Resource = manager.create("first")
    with pytest.warns(ResourceWarning, match="2 live Resource instances"):
        second: Resource = manager.create("second")

    assert manager.live_count == 2
    assert isinstance(manager.instances, tuple)
    assert list(manager.instances) == [first, second]
    first_reference: weakref.ReferenceType[Resource] = weakref.ref(first)
    del first
    gc.collect()

    assert first_reference() is None
    assert manager.live_count == 1
    assert list(manager.instances) == [second]


def test_instances_remain_in_creation_order_after_collection() -> None:
    manager: InstanceManager[Resource] = InstanceManager(
        Resource,
        max_instances=3,
    )
    first: Resource = manager.create("first")
    second: Resource = manager.create("second")
    third: Resource = manager.create("third")

    del second
    gc.collect()

    assert manager.instances == (first, third)
    assert manager.live_count == 2


def test_equal_unhashable_instances_can_be_tracked() -> None:
    class EqualResource:
        def __eq__(self, other: object) -> bool:
            return isinstance(other, EqualResource)

    manager: InstanceManager[EqualResource] = InstanceManager(
        EqualResource,
        max_instances=2,
    )
    first: EqualResource = manager.create()
    second: EqualResource = manager.create()

    assert manager.instances == (first, second)


def test_managers_and_inherited_types_have_isolated_counts() -> None:
    class Child(Resource):
        """Resource subtype with a separate manager."""

    resources: InstanceManager[Resource] = InstanceManager(
        Resource,
        max_instances=2,
    )
    children: InstanceManager[Child] = InstanceManager(
        Child,
        max_instances=2,
    )
    resource: Resource = resources.create("base")
    child: Child = children.create("child")

    assert resources.instances == (resource,)
    assert children.instances == (child,)
    assert resources.live_count == 1
    assert children.live_count == 1


def test_manager_does_not_track_instances_created_elsewhere() -> None:
    manager: InstanceManager[Resource] = InstanceManager(
        Resource,
        max_instances=1,
    )
    outside: Resource = Resource("outside")

    assert manager.live_count == 0
    assert manager.instances == ()
    assert outside.name == "outside"


def test_invalid_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="max_instances must be positive"):
        InstanceManager(Resource, max_instances=0)


def test_non_weak_referenceable_instance_is_rejected_without_tracking() -> None:
    class Slotted:
        __slots__: tuple[str, ...] = ()

    manager: InstanceManager[Slotted] = InstanceManager(
        Slotted,
        max_instances=1,
    )

    with pytest.raises(
        TypeError,
        match="instances must support weak references",
    ):
        manager.create()

    assert manager.live_count == 0
    assert manager.instances == ()


def test_manager_can_be_collected_while_an_instance_remains_alive() -> None:
    manager: InstanceManager[Resource] = InstanceManager(
        Resource,
        max_instances=1,
    )
    instance: Resource = manager.create("kept")
    manager_reference: weakref.ReferenceType[InstanceManager[Resource]]
    manager_reference = weakref.ref(manager)

    del manager
    gc.collect()

    assert manager_reference() is None
    assert instance.name == "kept"
