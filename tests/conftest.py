"""Shared contract fixtures; these are synthetic, not golden solver data."""

from pathlib import Path

import pytest

from core.models.case import (
    CaseRunSummary,
    CaseStatus,
    ComputeCase,
    StaticSettings,
)
from core.models.node import NodeKind, ProjectNode
from core.models.project import ProjectDocument
from core.models.result import AxisInfo, ResultDataset, VariableInfo


@pytest.fixture
def contract_case() -> ComputeCase:
    """Small persisted case used only to exercise public contracts."""

    return ComputeCase(
        case_id="case-001",
        name="contract static case",
        environment_id="environment-001",
        settings=StaticSettings(
            iteration_count=10,
            calculation_time=100.0,
            time_step=0.5,
            output_step=1.0,
        ),
        status=CaseStatus.SUCCESS,
        last_run=CaseRunSummary(
            input_relative_path="INPUT",
            output_relative_path="OUTPUT",
            log_relative_path="logs/solver.log",
            exit_code=0,
        ),
    )


@pytest.fixture
def contract_project(contract_case: ComputeCase) -> ProjectDocument:
    """Project/case/node fixture shared by ALL-00-02 contract tests."""

    node = ProjectNode(
        node_id="node-case-001",
        name="contract static case",
        kind=NodeKind.CASE,
        object_id=contract_case.case_id,
    )
    return ProjectDocument(
        project_id="project-001",
        name="contract project",
        cases={contract_case.case_id: contract_case},
        nodes={node.node_id: node},
    )


@pytest.fixture
def contract_result_dataset() -> ResultDataset:
    """Metadata-only result fixture; it is not verified OUTPUT evidence."""

    return ResultDataset(
        dataset_id="body-position",
        case_id="case-001",
        source_resource_id="OUTPUT/body-position.dat",
        axes=(
            AxisInfo(
                axis_key="time",
                values=(0.0, 1.0),
                kind="time",
                unit="s",
            ),
        ),
        variables=(VariableInfo(name="surge", unit="m"),),
        result_kind="body",
        source_path=str(Path("body-position.dat")),
    )
