"""INPUT 目录定位与配置文件解析。"""

from pathlib import Path

from core.models.project import InputConfigSummary
from core.sopro.manifest import parse_key_value_lines

_CONFIG_KEYS = (
    "mass",
    "waveType",
    "waveHeading",
    "wavePer",
    "waveAmp",
    "depth",
    "cal_time",
    "dt",
    "sta_Type",
    "out_step",
    "numRisers",
)

_ENV_LABELS = {
    "水深(m)": "water_depth",
    "海水密度（kg/m^3）": "water_density",
    "重力加速度(m/s^2)": "gravity",
}


def find_input_directories(root_dir: Path) -> list[Path]:
    """在解压目录中查找包含 config.dat 的 INPUT 目录。"""
    found: list[Path] = []
    for config_path in root_dir.rglob("config.dat"):
        if config_path.parent.name.upper() == "INPUT":
            found.append(config_path.parent)
    return sorted(set(found))


def summarize_input_directory(input_dir: Path) -> InputConfigSummary:
    """汇总单个 INPUT 目录中的配置信息。"""
    config_path = input_dir / "config.dat"
    config_text = config_path.read_text(encoding="utf-8", errors="replace")
    all_values = parse_key_value_lines(config_text)
    selected = {
        key: all_values[key]
        for key in _CONFIG_KEYS
        if key in all_values
    }

    env_path = input_dir / "Environment_in.dat"
    env_values: dict[str, str] = {}
    if env_path.is_file():
        env_values = _parse_environment_file(env_path)

    config_files = sorted(
        item.name
        for item in input_dir.iterdir()
        if item.is_file()
    )
    return InputConfigSummary(
        input_dir=input_dir,
        config_values=selected,
        environment_values=env_values,
        config_files=config_files,
    )


def _parse_environment_file(env_path: Path) -> dict[str, str]:
    """解析 Environment_in.dat 中的关键环境参数。"""
    lines = env_path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines()
    result: dict[str, str] = {}
    index = 0
    while index < len(lines):
        label = lines[index].strip()
        if label in _ENV_LABELS and index + 1 < len(lines):
            result[_ENV_LABELS[label]] = lines[index + 1].strip()
            index += 2
            continue
        if label.startswith("波浪类型"):
            if index + 1 < len(lines):
                wave_type = lines[index + 1].strip()
                result["wave_type_code"] = wave_type
                result["wave_type_name"] = _wave_type_name(wave_type)
            index += 2
            continue
        if label.startswith("波浪参数"):
            if index + 1 < len(lines):
                result["wave_params"] = lines[index + 1].strip()
            index += 2
            continue
        index += 1
    return result


def _wave_type_name(code: str) -> str:
    """将环境文件中的波浪类型编码转为名称。"""
    mapping = {
        "0": "无波浪",
        "1": "规则波(AIRY)",
        "2": "不规则波(JONSWAP)",
    }
    return mapping.get(code, f"未知({code})")
