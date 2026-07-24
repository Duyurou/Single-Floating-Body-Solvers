"""Tests for environment data parsing and persistence."""

import shutil
from pathlib import Path

from core.models.environment import EnvironmentDataState, EnvironmentWaveRow
from core.sopro.environment_data import (
    find_environment_data_file,
    find_environment_data_files,
    load_environment_state,
    load_environment_states,
    save_environment_state,
)

_FIXTURE_ROOT = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "environment_project"
    / "case001"
)


def _copy_fixture_to_temp(tmp_path: Path) -> Path:
    shutil.copytree(_FIXTURE_ROOT, tmp_path / "case001")
    return tmp_path


def _fixture_input_dir(root: Path) -> Path:
    return root / "case001" / "INPUT"


def test_find_environment_data_file_from_sample_project(
    tmp_path: Path,
) -> None:
    temp_dir = _copy_fixture_to_temp(tmp_path)
    env_file = find_environment_data_file(temp_dir)
    assert env_file is not None
    assert env_file.suffix == ".4048"


def test_load_environment_state_reads_wave_values(tmp_path: Path) -> None:
    temp_dir = _copy_fixture_to_temp(tmp_path)
    input_dir = _fixture_input_dir(temp_dir)
    state = load_environment_state(temp_dir, input_dir)

    assert state.name == "环境数据"
    assert state.environment_id == "case001"
    assert state.wind_wave_index == 1
    assert state.wave_rows[0].period == "5"
    assert state.wave_rows[0].heading == "180"
    assert len(state.current_rows) == 2


def test_save_environment_state_writes_xml_and_environment_dat(
    tmp_path: Path,
) -> None:
    temp_dir = _copy_fixture_to_temp(tmp_path)
    input_dir = _fixture_input_dir(temp_dir)
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


def test_default_environment_state_uses_zero_defaults() -> None:
    state = EnvironmentDataState()
    assert state.name == "环境数据"
    assert state.wind_wave_index == 0
    assert state.wind_index == 0
    assert state.current_index == 0
    assert state.wave_rows[0].amplitude == "0"


def test_environment_files_and_states_support_multiple_instances(
    tmp_path: Path,
) -> None:
    temp_dir = _copy_fixture_to_temp(tmp_path)
    second = EnvironmentDataState(
        name="台风环境",
        environment_id="environment-storm",
    )
    second_path = save_environment_state(temp_dir, None, second)

    paths = find_environment_data_files(temp_dir)
    states = load_environment_states(temp_dir)

    assert len(paths) == 2
    assert second_path in paths
    assert {state.environment_id for state in states} == {
        "case001",
        "environment-storm",
    }
    assert {state.name for state in states} == {"环境数据", "台风环境"}


def test_saving_new_environment_does_not_overwrite_existing_one(
    tmp_path: Path,
) -> None:
    temp_dir = _copy_fixture_to_temp(tmp_path)
    original_path = find_environment_data_file(temp_dir)
    assert original_path is not None
    original_text = original_path.read_text(encoding="utf-8")

    state = EnvironmentDataState(
        name="第二环境",
        environment_id="environment-002",
    )
    created_path = save_environment_state(temp_dir, None, state)

    assert created_path != original_path
    assert original_path.read_text(encoding="utf-8") == original_text
    assert state.xml_path == str(created_path)
