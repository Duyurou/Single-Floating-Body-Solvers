"""B-00-02 ExportReport 和 INPUT 所有权测试。"""

from pathlib import Path

from core.solver.export_report import (
    INPUT_FILE_OWNERS,
    KEEP_CREATED_PATHS_ON_ERROR,
    ExportReport,
    input_owner,
)


def test_reports_merge_without_mutating_inputs() -> None:
    first = ExportReport(created_paths=[Path("Environment_in.dat")])
    second = ExportReport(created_paths=[Path("config.dat")], errors=["bad"])

    merged = first.merge(second)

    assert merged.created_paths == [
        Path("Environment_in.dat"),
        Path("config.dat"),
    ]
    assert merged.errors == ["bad"]
    assert first.errors == []
    assert not merged.ok
    assert not bool(merged)


def test_combine_reports_in_order() -> None:
    reports = [
        ExportReport(warnings=["a"]),
        ExportReport(warnings=["b"]),
    ]

    merged = ExportReport.combine(reports)

    assert merged.warnings == ["a", "b"]


def test_input_ownership_has_one_owner_per_file() -> None:
    assert INPUT_FILE_OWNERS["config.dat"] == "B"
    assert INPUT_FILE_OWNERS["Mooringline_in.dat"] == "C"
    assert input_owner("WAMIT_5S.1") == "B"
    assert input_owner("unknown.dat") is None
    assert len(INPUT_FILE_OWNERS) == len(set(INPUT_FILE_OWNERS))


def test_created_paths_are_retained_when_export_has_errors() -> None:
    report = ExportReport(
        created_paths=[Path("partial.dat")],
        errors=["invalid field"],
    )

    assert KEEP_CREATED_PATHS_ON_ERROR
    assert report.created_paths == [Path("partial.dat")]
    assert report.has_errors
