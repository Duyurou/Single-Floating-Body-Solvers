"""Tests for project nodes and resource references."""

from pathlib import Path

import pytest

from core.models.node import NodeKind, ProjectNode
from core.models.resource import ResourceRef


def test_group_node_does_not_require_an_object() -> None:
    node = ProjectNode(
        node_id="group-environment",
        name="Environment",
        kind=NodeKind.GROUP,
    )

    assert node.object_id is None
    assert str(node.kind) == "group"


def test_hydro_views_share_one_object_with_different_view_keys() -> None:
    damping = ProjectNode(
        node_id="view-damping",
        name="Radiation damping",
        kind=NodeKind.HYDRO_VIEW,
        object_id="hydro-1",
        view_key="radiation_damping",
    )
    rao = ProjectNode(
        node_id="view-rao",
        name="RAO",
        kind=NodeKind.HYDRO_VIEW,
        object_id="hydro-1",
        view_key="rao",
    )

    assert damping.object_id == rao.object_id
    assert damping.view_key != rao.view_key


def test_hydro_view_requires_an_object_and_view_key() -> None:
    with pytest.raises(ValueError):
        ProjectNode(
            node_id="view-invalid",
            name="Invalid",
            kind=NodeKind.HYDRO_VIEW,
        )


@pytest.mark.parametrize(
    "relative_path",
    ["../outside.stl", "/outside.stl", r"C:\outside.stl"],
)
def test_resource_reference_rejects_paths_outside_project(
    relative_path: str,
) -> None:
    with pytest.raises(ValueError):
        ResourceRef(
            id="mesh-1",
            resource_type="stl",
            relative_path=relative_path,
            original_name="body.stl",
        )


def test_resource_reference_resolves_under_project_root() -> None:
    resource = ResourceRef(
        id="mesh-1",
        resource_type="stl",
        relative_path="resources/body.stl",
        original_name="body.stl",
    )

    assert resource.resolve_from(Path("project")) == Path(
        "project/resources/body.stl",
    )
