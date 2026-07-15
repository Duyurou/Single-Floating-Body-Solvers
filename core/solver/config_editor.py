"""config.dat 与相关输入文件编辑。"""

import re
from pathlib import Path

_WAMIT_FILES = (
    "WAMIT_5S.1",
    "WAMIT_5S.3",
    "WAMIT_5S.4",
    "WAMIT_5S.8",
    "WAMIT_5S.9",
    "WAMIT_5S.11d",
    "WAMIT_5S.11s",
    "WAMIT_5S.hst",
    "WAMIT_5S.RAO",
)

_DYNAMIC_INPUT_FILES = (
    "risers_dynamic.in",
    "config.dat",
    "Mooringline_in.dat",
    "Environment_in.dat",
    *_WAMIT_FILES,
)


def replace_config_value(text: str, key: str, value: str) -> str:
    """替换 config.dat 中指定键的值行。"""
    pattern = re.compile(
        rf"^(\s*{re.escape(key)}\s*=\s*).*$",
        re.MULTILINE,
    )
    if not pattern.search(text):
        return text
    return pattern.sub(rf"\g<1>{value}", text)


def write_config_value(config_path: Path, key: str, value: str) -> None:
    """更新 config.dat 中单个键值。"""
    text = config_path.read_text(encoding="utf-8", errors="replace")
    config_path.write_text(
        replace_config_value(text, key, value),
        encoding="utf-8",
    )


def apply_static_config(config_path: Path) -> None:
    """将 config.dat 设置为静态分析参数。"""
    text = config_path.read_text(encoding="utf-8", errors="replace")
    replacements = {
        "sta_Type": "0",
        "yang_moor": "1",
        "wang_moor": "0",
        "cal_time": "1d0\t",
        "dt": "0.02d0\t",
        "out_step": "0.5",
    }
    for key, value in replacements.items():
        text = replace_config_value(text, key, value)
    config_path.write_text(text, encoding="utf-8")


def apply_dynamic_config(config_path: Path) -> None:
    """将 config.dat 设置为动态分析参数。"""
    text = config_path.read_text(encoding="utf-8", errors="replace")
    replacements = {
        "sta_Type": "1",
        "yang_moor": "0",
        "wang_moor": "1",
        "cal_time": "500.0d0\t",
        "dt": "0.02d0\t",
        "out_step": "0.5",
    }
    for key, value in replacements.items():
        text = replace_config_value(text, key, value)
    config_path.write_text(text, encoding="utf-8")


def patch_mooringline_for_dynamic(mooring_path: Path) -> None:
    """动态分析前更新系泊输入文件第 6 行。"""
    if not mooring_path.is_file():
        return
    lines = mooring_path.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines()
    if len(lines) < 6:
        return
    lines[5] = "3"
    mooring_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def wamit_file_names() -> tuple[str, ...]:
    """返回需要复制的水动力文件名。"""
    return _WAMIT_FILES


def dynamic_base_file_names() -> tuple[str, ...]:
    """返回动态分析需要复制的 INPUT 文件名。"""
    return _DYNAMIC_INPUT_FILES
