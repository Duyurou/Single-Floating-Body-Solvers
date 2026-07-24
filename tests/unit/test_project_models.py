"""Tests for the shared project document and legacy loading summaries."""

from dataclasses import dataclass
from pathlib import Path

import pytest

from core.models.project import (
    InputConfigSummary,
    LoadedProject,
    ManifestInfo,
    ProjectDocument,
)


@dataclass
class ExampleBody:
    body_id: str


@dataclass
class ExampleEnvironment:
    environment_id: str


def test_project_document_has_independent_domain_collections() -> None:
    first = ProjectDocument(project_id="project-1", name="First")
    second = ProjectDocument(project_id="project-2", name="Second")

    first.floating_bodies["body-1"] = ExampleBody("body-1")
    first.mark_dirty()

    assert list(first.floating_bodies) == ["body-1"]
    assert second.floating_bodies == {}
    assert first.is_dirty is True
    assert second.is_dirty is False

    first.mark_saved()
    assert first.is_dirty is False


def test_project_document_supports_multiple_environments_by_id() -> None:
    project = ProjectDocument(project_id="project-1", name="First")
    calm = ExampleEnvironment("environment-calm")
    storm = ExampleEnvironment("environment-storm")

    project.environments[calm.environment_id] = calm
    project.environments[storm.environment_id] = storm

    assert list(project.environments) == [
        "environment-calm",
        "environment-storm",
    ]
    assert project.environments["environment-storm"] is storm


@pytest.mark.parametrize("field_name", ["project_id", "name"])
def test_project_document_rejects_empty_identity(field_name: str) -> None:
    values = {"project_id": "project-1", "name": "Demo"}
    values[field_name] = "  "

    with pytest.raises(ValueError):
        ProjectDocument(**values)


def test_legacy_loaded_project_contract_remains_usable() -> None:
    source_path = Path("demo.sopro")
    summary = InputConfigSummary(
        input_dir=source_path.parent / "INPUT",
        config_values={"mass": "1200"},
        environment_values={"water_depth": "100"},
        config_files=["config.dat"],
    )
    loaded = LoadedProject(
        source_path=source_path,
        extract_dir=source_path.parent / "extract",
        manifest=ManifestInfo(name="Demo", version="1.0"),
        input_summaries=[summary],
    )

    assert loaded.manifest.name == "Demo"
    assert loaded.input_summaries[0].config_values["mass"] == "1200"
