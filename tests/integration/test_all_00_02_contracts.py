"""ALL-00-02 cross-owner calling and editor-registration tests."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from core.models.case import ComputeCase
from core.models.node import NodeKind, ProjectNode
from core.models.project import ProjectDocument
from core.models.result import ResultDataset
from core.solver.export_report import ExportReport, input_owner
from ui.editors.editor_registry import (
    EditorObjectNotFoundError,
    EditorRegistry,
    ReadOnlyNodeView,
)


@dataclass(frozen=True)
class FakeDomainObject:
    object_id: str
    owner: str


def _fake_codec(owner: str, object_id: str):
    def load(project: ProjectDocument) -> FakeDomainObject:
        return FakeDomainObject(object_id, owner)

    def save(
        project: ProjectDocument,
        value: FakeDomainObject,
    ) -> str:
        project.legacy_packets[f"{owner}:{value.object_id}"] = owner
        return value.object_id

    return load, save


def _fake_exporter(owner: str, file_name: str):
    def export(
        project: ProjectDocument,
        case: ComputeCase,
        output_dir: Path,
    ) -> ExportReport:
        assert project.cases[case.case_id] is case
        assert input_owner(file_name) == owner
        return ExportReport(created_paths=[output_dir / file_name])

    return export


def test_project_storage_can_call_a_b_c_codec_contracts(
    contract_project: ProjectDocument,
) -> None:
    """A's storage can orchestrate independent domain load/save functions."""

    for owner in ("A", "B", "C"):
        load, save = _fake_codec(owner, f"object-{owner.lower()}")
        value = load(contract_project)
        assert save(contract_project, value) == value.object_id

    assert set(contract_project.legacy_packets) == {
        "A:object-a",
        "B:object-b",
        "C:object-c",
    }


def test_calculation_service_combines_a_b_c_export_reports(
    contract_project: ProjectDocument,
    contract_case: ComputeCase,
) -> None:
    """B's calculation service can combine exporters without inheritance."""

    exporters = (
        _fake_exporter("A", "Environment_in.dat"),
        _fake_exporter("B", "config.dat"),
        _fake_exporter("C", "Mooringline_in.dat"),
    )
    reports = [
        exporter(contract_project, contract_case, Path("INPUT"))
        for exporter in exporters
    ]
    report = ExportReport.combine(reports)

    assert report.ok
    assert [path.name for path in report.created_paths] == [
        "Environment_in.dat",
        "config.dat",
        "Mooringline_in.dat",
    ]


def test_editor_registry_passes_object_and_view_keys_without_copying_data(
    contract_project: ProjectDocument,
) -> None:
    """Two hydro view nodes share one dataset and select different views."""

    dataset = FakeDomainObject("hydro-001", "B")
    contract_project.hydrodynamics[dataset.object_id] = dataset
    services = object()
    seen: list[tuple[Any, ...]] = []

    def hydro_editor(
        node: ProjectNode,
        project: ProjectDocument,
        passed_services: Any,
    ) -> tuple[str | None, str | None]:
        seen.append(
            (
                node.object_id,
                node.view_key,
                project.hydrodynamics[node.object_id],
                passed_services,
            ),
        )
        return node.object_id, node.view_key

    registry = EditorRegistry()
    registry.register(NodeKind.HYDRODYNAMICS, hydro_editor)
    registry.register(NodeKind.HYDRO_VIEW, hydro_editor)

    curves = ProjectNode(
        "hydro-curves",
        "curves",
        NodeKind.HYDRO_VIEW,
        object_id=dataset.object_id,
        view_key="curves",
    )
    matrices = ProjectNode(
        "hydro-matrices",
        "matrices",
        NodeKind.HYDRO_VIEW,
        object_id=dataset.object_id,
        view_key="matrices",
    )

    assert registry.create(curves, contract_project, services) == (
        dataset.object_id,
        "curves",
    )
    assert registry.create(matrices, contract_project, services) == (
        dataset.object_id,
        "matrices",
    )
    assert seen[0][2] is seen[1][2] is dataset
    assert seen[0][3] is seen[1][3] is services


def test_editor_registry_handles_unknown_missing_and_duplicate_nodes(
    contract_project: ProjectDocument,
) -> None:
    registry = EditorRegistry()
    unknown = ProjectNode("group", "group", NodeKind.GROUP)

    fallback = registry.create(unknown, contract_project, object())
    assert isinstance(fallback, ReadOnlyNodeView)
    assert fallback.read_only

    registry.register(NodeKind.CASE, lambda node, project, services: node)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(NodeKind.CASE, lambda node, project, services: node)

    missing = ProjectNode(
        "missing-case",
        "missing case",
        NodeKind.CASE,
        object_id="case-does-not-exist",
    )
    with pytest.raises(EditorObjectNotFoundError, match="case-does-not-exist"):
        registry.create(missing, contract_project, object())


def test_editor_registry_resolves_environment_nodes_from_collection(
    contract_project: ProjectDocument,
) -> None:
    environment = FakeDomainObject("environment-001", "A")
    contract_project.environments[environment.object_id] = environment
    node = ProjectNode(
        "environment-node",
        "environment",
        NodeKind.ENVIRONMENT,
        object_id=environment.object_id,
    )
    registry = EditorRegistry()
    registry.register(
        NodeKind.ENVIRONMENT,
        lambda node, project, services: (
            node.object_id,
            project.environments[node.object_id],
        ),
    )

    assert registry.create(node, contract_project, object()) == (
        "environment-001",
        environment,
    )


def test_result_locator_uses_compute_case_output_and_dataset_metadata(
    contract_case: ComputeCase,
    contract_result_dataset: ResultDataset,
) -> None:
    """C can locate a result through B's case without parsing private state."""

    assert contract_case.last_run is not None
    output_dir = (
        Path("workspace")
        / contract_case.case_id
        / (contract_case.last_run.output_relative_path or "OUTPUT")
    )
    result_path = output_dir / Path(contract_result_dataset.source_path or "")

    assert contract_result_dataset.case_id == contract_case.case_id
    assert result_path == Path(
        "workspace/case-001/OUTPUT/body-position.dat",
    )
