"""B-00-01 工况合同测试。"""

from pathlib import Path

import pytest

from core.models.case import (
    CasePaths,
    CaseRunSummary,
    CaseStatus,
    ComputeCase,
    ComputeCaseRecord,
    DynamicSettings,
    OutputSelection,
    RegularWaveDynamicSettings,
    StaticSettings,
    can_transition_status,
    transition_status,
)


def _static() -> StaticSettings:
    return StaticSettings(10, 100.0, 0.5, 1.0)


def _dynamic() -> DynamicSettings:
    return DynamicSettings(
        wave_mode="regular",
        regular=RegularWaveDynamicSettings(10, 20, True, "free"),
        irregular=None,
        output=OutputSelection(1.0, {"x"}),
        static_case_id="static-1",
    )


def test_existing_record_remains_compatible() -> None:
    record = ComputeCaseRecord(
        "case-1",
        "legacy",
        "static",
        Path("work"),
        Path("work/INPUT"),
        Path("work/OUTPUT"),
    )

    assert record.status == "pending"
    record.status = "running"
    assert record.status == CaseStatus.RUNNING


def test_compute_case_derives_analysis_type_and_allows_rerun() -> None:
    case = ComputeCase("case-1", "静态", "env-1", _static())

    assert case.analysis_type == "static"
    assert case.status is CaseStatus.PENDING
    case.transition_to("preparing")
    case.transition_to("running")
    case.transition_to("failed")
    case.transition_to("preparing")
    assert case.status == "preparing"


def test_dynamic_settings_require_matching_wave_settings() -> None:
    with pytest.raises(ValueError, match="regular 模式"):
        DynamicSettings(
            "regular",
            None,
            None,
            OutputSelection(1.0),
            "static-1",
        )


def test_status_transition_rejects_running_to_pending() -> None:
    assert can_transition_status("running", "success")
    assert not can_transition_status("running", "pending")
    with pytest.raises(ValueError, match="不允许"):
        transition_status("running", "pending")


def test_case_run_summary_rejects_absolute_or_parent_path() -> None:
    with pytest.raises(ValueError, match="相对路径"):
        CaseRunSummary(input_relative_path=str(Path("C:/old/INPUT")))
    with pytest.raises(ValueError, match="不能越出"):
        CaseRunSummary(output_relative_path="../OUTPUT")


def test_case_paths_are_runtime_paths_under_case_id() -> None:
    root = Path("workspace") / "test-case-root"
    paths = CasePaths.for_case(root, "case-1")

    assert paths.work_dir == root.resolve() / "cases" / "case-1"
    assert paths.input_dir == paths.work_dir / "INPUT"
    assert paths.output_dir == paths.work_dir / "OUTPUT"
    assert paths.log_path == paths.work_dir / "logs" / "solver.log"
    assert not paths.work_dir.exists()
