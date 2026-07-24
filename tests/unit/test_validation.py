"""Tests for shared validation and operation results."""

from pathlib import Path

import pytest

from core.models.validation import CommandResult, ValidationIssue


def test_warning_can_be_returned_by_a_successful_command() -> None:
    warning = ValidationIssue(
        level="warning",
        code="RESOURCE_UNUSED",
        path="resources.mesh-1",
        message="The resource is not referenced.",
    )
    result = CommandResult(
        success=True,
        issues=[warning],
        changed_ids=["body-1"],
        created_paths=[Path("cases/case-1/INPUT/config.dat")],
    )

    assert result.success is True
    assert result.warnings == [warning]
    assert result.errors == []
    assert result.has_errors is False


def test_failed_command_exposes_errors() -> None:
    error = ValidationIssue(
        level="error",
        code="CABLE_START_MISSING",
        path="cables.line-1.start_point_id",
        message="The start point does not exist.",
    )
    result = CommandResult(success=False, issues=[error])

    assert result.success is False
    assert result.errors == [error]
    assert result.has_errors is True


def test_successful_command_cannot_hide_an_error() -> None:
    error = ValidationIssue(
        level="error",
        code="INVALID_ENVIRONMENT",
        path="environment.wave.period",
        message="Wave period must be positive.",
    )

    with pytest.raises(ValueError):
        CommandResult(success=True, issues=[error])


def test_validation_issue_rejects_unknown_level() -> None:
    with pytest.raises(ValueError):
        ValidationIssue(
            level="info",  # type: ignore[arg-type]
            code="INFO",
            path="",
            message="Informational message.",
        )
