"""Tests for environment data parsing and persistence."""

import shutil
import tempfile
import zipfile
from pathlib import Path

from core.models.environment import EnvironmentDataState, EnvironmentWaveRow
from core.sopro.environment_data import (
    find_environment_data_file,
    load_environment_state,
    save_environment_state,
)

_SAMPLE_SOPRO = (
    Path(__file__).resolve().parents[2].parent
    / "单浮体求解器集成包"
    / "reference"
    / "example-project"
    / "single-floater-ten-riser.sopro"
)


def _extract_sample_project() -> Path:
    temp_dir = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(_SAMPLE_SOPRO) as archive:
        archive.extractall(temp_dir)
    return temp_dir


def test_find_environment_data_file_from_sample_project() -> None:
    temp_dir = _extract_sample_project()
    try:
        env_file = find_environment_data_file(temp_dir)
        assert env_file is not None
        assert env_file.suffix == ".4048"
    finally:
        shutil.rmtree(temp_dir)


def test_load_environment_state_reads_wave_values() -> None:
    temp_dir = _extract_sample_project()
    try:
        input_dirs = sorted(temp_dir.rglob("INPUT"))
        input_dir = next(path for path in input_dirs if path.is_dir())
        state = load_environment_state(temp_dir, input_dir)

        assert state.name == "环境数据"
        assert state.wind_wave_index == 1
        assert state.wave_rows[0].period == "5"
        assert state.wave_rows[0].heading == "180"
        assert len(state.current_rows) == 2
    finally:
        shutil.rmtree(temp_dir)


def test_save_environment_state_writes_xml_and_environment_dat() -> None:
    temp_dir = _extract_sample_project()
    try:
        input_dirs = sorted(temp_dir.rglob("INPUT"))
        input_dir = next(path for path in input_dirs if path.is_dir())
        state = load_environment_state(temp_dir, input_dir)
        state.description = "测试描述"
        state.wave_rows = [
            EnvironmentWaveRow(
                heading="90",
                phase="15",
                period="8",
                amplitude="3",
                source_x="1",
                source_y="2",
                stretching_model="1",
            ),
        ]
        state.current_index = 1
        state.current_rows[0].depth = "0"
        state.current_rows[0].speed_x = "1.2"
        state.current_rows[0].speed_y = "0.3"

        save_environment_state(temp_dir, input_dir, state)

        env_text = (input_dir / "Environment_in.dat").read_text(
            encoding="utf-8",
        )
        assert "3,\t8,\t90,\t15" in env_text.replace(" ", "")
        reloaded = load_environment_state(temp_dir, input_dir)
        assert reloaded.description == "测试描述"
        assert reloaded.wave_rows[0].amplitude == "3"
        assert reloaded.wave_rows[0].heading == "90"
    finally:
        shutil.rmtree(temp_dir)


def test_default_environment_state_uses_zero_defaults() -> None:
    state = EnvironmentDataState()
    assert state.name == "环境数据"
    assert state.wind_wave_index == 0
    assert state.wind_index == 0
    assert state.current_index == 0
    assert state.wave_rows[0].amplitude == "0"
