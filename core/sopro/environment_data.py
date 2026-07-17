"""环境数据 XML 与 Environment_in.dat 读写。"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from core.models.environment import (
    EnvironmentCurrentRow,
    EnvironmentDataState,
    EnvironmentWaveRow,
    EnvironmentWindRow,
)

WIND_WAVE_OPTIONS = (
    "无风浪",
    "规则波",
    "ITTC谱",
    "PM谱",
    "Jonswap双参数谱",
    "Jonswap三参数谱",
    "Jonswap六参数谱",
    "Jonswap双峰谱",
    "PM-ISSC谱",
    "PM跨零谱",
    "Ochi-Hubble谱",
    "用户自定义",
)

WIND_OPTIONS = ("无风", "均匀风", "常定风", "叶片相关风")

CURRENT_OPTIONS = ("无海流", "均匀海流", "剖面海流")

_WAVE_PREFIX_BY_INDEX = {
    1: "wave_data_w0",
    2: "wave_data_w1",
    3: "wave_data_w2",
    4: "wave_data_w3",
    5: "wave_data_w4",
    6: "wave_data_w5",
    7: "wave_data_w6",
    8: "wave_data_w7",
    9: "wave_data_w8",
    10: "wave_data_w9",
    11: "wave_data_w10",
}

_WIND_PREFIX_BY_INDEX = {
    1: "wind_data_w0",
    2: "wind_data_w1",
    3: "wind_data_w2",
}


class EnvironmentDataError(Exception):
    """环境数据处理异常。"""


def find_environment_data_file(root_dir: Path) -> Path | None:
    """在解压目录中查找环境数据 XML 文件。"""
    candidates = sorted(root_dir.rglob("环境数据.*"))
    if candidates:
        return candidates[0]
    for path in sorted(root_dir.rglob("*.4048")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "surgeIndex" in text and "wave_data_w0_amplitude" in text:
            return path
    return None


def load_environment_state(
    extract_dir: Path,
    input_dir: Path | None = None,
) -> EnvironmentDataState:
    """从工程目录加载环境数据状态。"""
    xml_path = find_environment_data_file(extract_dir)
    attrs: dict[str, str] = {}
    if xml_path is not None:
        attrs = _read_xml_attributes(xml_path)

    state = EnvironmentDataState(
        name=attrs.get("display_name", "环境数据"),
        description=attrs.get("description", ""),
        wind_wave_index=_safe_int(attrs.get("surgeIndex"), 0),
        wind_index=_safe_int(attrs.get("windIndex"), 0),
        current_index=_safe_int(attrs.get("oceanIndex"), 0),
        xml_path=str(xml_path) if xml_path is not None else "",
    )
    state.wave_rows = [_wave_row_from_attrs(attrs, state.wind_wave_index)]
    state.wind_rows = [_wind_row_from_attrs(attrs, state.wind_index)]
    state.current_rows = _current_rows_from_attrs(attrs, input_dir)
    _apply_environment_dat_fallback(state, input_dir)
    return state


def save_environment_state(
    extract_dir: Path,
    input_dir: Path | None,
    state: EnvironmentDataState,
) -> Path:
    """保存环境数据到 XML 与 Environment_in.dat。"""
    xml_path = (
        Path(state.xml_path)
        if state.xml_path
        else find_environment_data_file(extract_dir)
    )
    if xml_path is None or not xml_path.is_file():
        xml_path = _create_environment_data_file(extract_dir)

    attrs = _read_xml_attributes(xml_path)
    attrs["display_name"] = state.name
    attrs["description"] = state.description
    attrs["surgeIndex"] = str(state.wind_wave_index)
    attrs["windIndex"] = str(state.wind_index)
    attrs["oceanIndex"] = str(state.current_index)
    attrs["wave_data_selectIndex"] = str(max(state.wind_wave_index, 0))
    _wave_row_to_attrs(attrs, state.wind_wave_index, state.wave_rows[0])
    if state.wind_rows:
        _wind_row_to_attrs(attrs, state.wind_index, state.wind_rows[0])
    _current_rows_to_attrs(attrs, state.current_index, state.current_rows)
    _write_xml_attributes(xml_path, attrs)

    if input_dir is not None:
        env_path = input_dir / "Environment_in.dat"
        if env_path.is_file():
            _write_environment_dat(env_path, state)
        _sync_config_dat(input_dir / "config.dat", state)

    return xml_path


def _safe_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except ValueError:
        return default


def _safe_float_text(value: str | None, default: str = "0") -> str:
    if value is None or value == "":
        return default
    try:
        number = float(value)
    except ValueError:
        return default
    if number.is_integer():
        return str(int(number))
    return str(number)


def _read_xml_attributes(path: Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    attrs: dict[str, str] = {}
    for element in root:
        name = (element.findtext("AttributeName") or "").strip()
        if not name:
            continue
        attrs[name] = (element.findtext("AttributeInfo") or "").strip()
    return attrs


def _write_xml_attributes(path: Path, attrs: dict[str, str]) -> None:
    root = ET.parse(path).getroot()
    known = set(attrs)
    for element in root:
        name = (element.findtext("AttributeName") or "").strip()
        if name not in attrs:
            continue
        info = element.find("AttributeInfo")
        if info is None:
            info = ET.SubElement(element, "AttributeInfo")
        info.text = attrs[name]
        known.discard(name)

    if known:
        next_index = len(list(root)) + 1
        for name in sorted(known):
            element = ET.SubElement(root, f"Element_{next_index}")
            ET.SubElement(element, "AttributeType").text = "4"
            ET.SubElement(element, "AttributeName").text = name
            ET.SubElement(element, "AttributeInfo").text = attrs[name]
            next_index += 1

    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=False)


def _create_environment_data_file(extract_dir: Path) -> Path:
    folder = extract_dir / "environment_data"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "环境数据.4048"
    path.write_text(
        "<?xml version='1.0' encoding='utf-8'?>\n<RootElement/>\n",
        encoding="utf-8",
    )
    defaults = {
        "display_name": "环境数据",
        "description": "",
        "surgeIndex": "0",
        "windIndex": "0",
        "oceanIndex": "0",
        "wave_data_selectIndex": "0",
        "wave_data_w0_amplitude": "0",
        "wave_data_w0_frequency": "0",
        "wave_data_w0_wavedir": "0",
        "wave_data_w0_phase": "0",
        "wave_data_w0_XOrig": "0",
        "wave_data_w0_YOrig": "0",
        "wave_data_w0_StretchingModel": "0",
        "wind_data_w0_wind_dir": "0",
        "wind_data_w0_wind_speed": "0",
        "ocean_data_Ocean_dir": "0",
        "ocean_data_Ocean_Speed": "0",
        "ocean_datas_size": "0",
    }
    _write_xml_attributes(path, defaults)
    return path


def _wave_prefix(index: int) -> str | None:
    return _WAVE_PREFIX_BY_INDEX.get(index)


def _wave_row_from_attrs(
    attrs: dict[str, str],
    wave_index: int,
) -> EnvironmentWaveRow:
    prefix = _wave_prefix(wave_index)
    if prefix is None:
        return EnvironmentWaveRow()
    if wave_index == 1:
        return EnvironmentWaveRow(
            heading=_safe_float_text(attrs.get(f"{prefix}_wavedir")),
            phase=_safe_float_text(attrs.get(f"{prefix}_phase")),
            period=_safe_float_text(attrs.get(f"{prefix}_frequency")),
            amplitude=_safe_float_text(attrs.get(f"{prefix}_amplitude")),
            source_x=_safe_float_text(attrs.get(f"{prefix}_XOrig")),
            source_y=_safe_float_text(attrs.get(f"{prefix}_YOrig")),
            stretching_model=_safe_float_text(
                attrs.get(f"{prefix}_StretchingModel"),
            ),
        )
    return EnvironmentWaveRow(
        heading=_safe_float_text(attrs.get(f"{prefix}_wavedir")),
        phase="0",
        period=_safe_float_text(
            attrs.get(f"{prefix}_Tp", attrs.get(f"{prefix}_frequency")),
        ),
        amplitude=_safe_float_text(
            attrs.get(f"{prefix}_Hs", attrs.get(f"{prefix}_amplitude")),
        ),
        source_x=_safe_float_text(attrs.get(f"{prefix}_XOrig")),
        source_y=_safe_float_text(attrs.get(f"{prefix}_YOrig")),
        stretching_model=_safe_float_text(
            attrs.get(f"{prefix}_StretchingModel"),
        ),
    )


def _wave_row_to_attrs(
    attrs: dict[str, str],
    wave_index: int,
    row: EnvironmentWaveRow,
) -> None:
    prefix = _wave_prefix(wave_index)
    if prefix is None:
        return
    attrs[f"{prefix}_wavedir"] = row.heading
    attrs[f"{prefix}_XOrig"] = row.source_x
    attrs[f"{prefix}_YOrig"] = row.source_y
    attrs[f"{prefix}_StretchingModel"] = row.stretching_model
    if wave_index == 1:
        attrs[f"{prefix}_amplitude"] = row.amplitude
        attrs[f"{prefix}_frequency"] = row.period
        attrs[f"{prefix}_phase"] = row.phase
        return
    attrs[f"{prefix}_Hs"] = row.amplitude
    attrs[f"{prefix}_Tp"] = row.period


def _wind_row_from_attrs(
    attrs: dict[str, str],
    wind_index: int,
) -> EnvironmentWindRow:
    prefix = _WIND_PREFIX_BY_INDEX.get(wind_index)
    if prefix is None:
        return EnvironmentWindRow()
    if wind_index == 1:
        return EnvironmentWindRow(
            direction=_safe_float_text(attrs.get(f"{prefix}_wind_dir")),
            speed=_safe_float_text(attrs.get(f"{prefix}_wind_speed")),
            height="0",
        )
    if wind_index == 2:
        return EnvironmentWindRow(
            direction=_safe_float_text(attrs.get(f"{prefix}_wind_dir")),
            speed=_safe_float_text(attrs.get(f"{prefix}_wind_speed")),
            height=_safe_float_text(attrs.get(f"{prefix}_wind_height")),
        )
    return EnvironmentWindRow(
        direction="0",
        speed=_safe_float_text(attrs.get(f"{prefix}_share_exp")),
        height=_safe_float_text(attrs.get(f"{prefix}_rough_len")),
    )


def _wind_row_to_attrs(
    attrs: dict[str, str],
    wind_index: int,
    row: EnvironmentWindRow,
) -> None:
    prefix = _WIND_PREFIX_BY_INDEX.get(wind_index)
    if prefix is None:
        return
    if wind_index == 1:
        attrs[f"{prefix}_wind_dir"] = row.direction
        attrs[f"{prefix}_wind_speed"] = row.speed
        return
    if wind_index == 2:
        attrs[f"{prefix}_wind_dir"] = row.direction
        attrs[f"{prefix}_wind_speed"] = row.speed
        attrs[f"{prefix}_wind_height"] = row.height
        return
    attrs[f"{prefix}_share_exp"] = row.speed
    attrs[f"{prefix}_rough_len"] = row.height


def _current_rows_from_attrs(
    attrs: dict[str, str],
    input_dir: Path | None,
) -> list[EnvironmentCurrentRow]:
    rows = _current_rows_from_environment_dat(input_dir)
    if rows:
        return rows
    size = _safe_int(attrs.get("ocean_datas_size"), 0)
    if size <= 0:
        return [EnvironmentCurrentRow()]
    result: list[EnvironmentCurrentRow] = []
    for index in range(size):
        result.append(
            EnvironmentCurrentRow(
                depth=_safe_float_text(
                    attrs.get(f"ocean_data_depth_{index}"),
                ),
                speed_x=_safe_float_text(
                    attrs.get(f"ocean_data_speed_x_{index}"),
                ),
                speed_y=_safe_float_text(
                    attrs.get(f"ocean_data_speed_y_{index}"),
                ),
            ),
        )
    if not result:
        return [EnvironmentCurrentRow()]
    return result


def _current_rows_from_environment_dat(
    input_dir: Path | None,
) -> list[EnvironmentCurrentRow]:
    if input_dir is None:
        return []
    env_path = input_dir / "Environment_in.dat"
    if not env_path.is_file():
        return []
    lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    count = 0
    data_start = -1
    for index, line in enumerate(lines):
        label = line.strip()
        if label.startswith("海流剖面定义") and "个数" in label:
            if index + 1 < len(lines):
                count = _safe_int(lines[index + 1].strip(), 0)
            continue
        if label.startswith("海流剖面定义") and "速度关系" in label:
            data_start = index + 1
            break
    if count <= 0 or data_start < 0:
        return []
    rows: list[EnvironmentCurrentRow] = []
    for offset in range(count):
        line_index = data_start + offset
        if line_index >= len(lines):
            break
        parts = [
            item.strip()
            for item in re.split(r",|\s+", lines[line_index].strip())
            if item.strip()
        ]
        if len(parts) < 3:
            continue
        rows.append(
            EnvironmentCurrentRow(
                depth=parts[0],
                speed_x=parts[1],
                speed_y=parts[2],
            ),
        )
    return rows


def _current_rows_to_attrs(
    attrs: dict[str, str],
    current_index: int,
    rows: list[EnvironmentCurrentRow],
) -> None:
    if current_index == 0:
        attrs["ocean_datas_size"] = "0"
        attrs["ocean_data_Ocean_dir"] = "0"
        attrs["ocean_data_Ocean_Speed"] = "0"
        return
    active = rows[0] if rows else EnvironmentCurrentRow()
    attrs["ocean_data_Ocean_dir"] = active.speed_x
    attrs["ocean_data_Ocean_Speed"] = active.speed_y
    attrs["ocean_datas_size"] = str(len(rows))
    for index, row in enumerate(rows):
        attrs[f"ocean_data_depth_{index}"] = row.depth
        attrs[f"ocean_data_speed_x_{index}"] = row.speed_x
        attrs[f"ocean_data_speed_y_{index}"] = row.speed_y


def _apply_environment_dat_fallback(
    state: EnvironmentDataState,
    input_dir: Path | None,
) -> None:
    if input_dir is None:
        return
    env_path = input_dir / "Environment_in.dat"
    if not env_path.is_file():
        return
    lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
    wave_code = ""
    wave_params = ""
    index = 0
    while index < len(lines):
        label = lines[index].strip()
        if label.startswith("波浪类型") and index + 1 < len(lines):
            wave_code = lines[index + 1].strip()
        if label.startswith("波浪参数") and index + 1 < len(lines):
            wave_params = lines[index + 1].strip()
        index += 1

    if wave_code:
        code = _safe_int(wave_code, 0)
        if code == 1 and state.wind_wave_index == 0:
            state.wind_wave_index = 1
        elif code >= 2 and state.wind_wave_index < 2:
            state.wind_wave_index = 2

    if wave_params and state.wave_rows:
        parts = [
            item.strip()
            for item in re.split(r",|\s+", wave_params)
            if item.strip()
        ]
        if len(parts) >= 4:
            row = state.wave_rows[0]
            row.amplitude = parts[0]
            row.period = parts[1]
            row.heading = parts[2]
            row.phase = parts[3]

    current_rows = _current_rows_from_environment_dat(input_dir)
    if current_rows:
        state.current_rows = current_rows
        if state.current_index == 0:
            state.current_index = 2 if len(current_rows) > 1 else 1


def _write_environment_dat(path: Path, state: EnvironmentDataState) -> None:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    wave_code = "0"
    if state.wind_wave_index == 1:
        wave_code = "1"
    elif state.wind_wave_index >= 2:
        wave_code = "2"

    row = state.wave_rows[0] if state.wave_rows else EnvironmentWaveRow()
    wave_params = ",\t".join(
        [row.amplitude, row.period, row.heading, row.phase],
    )
    current_count = 0 if state.current_index == 0 else len(state.current_rows)

    updated: list[str] = []
    index = 0
    while index < len(lines):
        label = lines[index].strip()
        if label.startswith("波浪类型"):
            updated.append(lines[index])
            updated.append(wave_code)
            index += 2
            continue
        if label.startswith("波浪参数"):
            updated.append(lines[index])
            updated.append(wave_params)
            index += 2
            continue
        if label.startswith("海流剖面定义") and "个数" in label:
            updated.append(lines[index])
            updated.append(str(max(current_count, 0)))
            index += 2
            continue
        if label.startswith("海流剖面定义") and "速度关系" in label:
            updated.append(lines[index])
            if current_count > 0:
                for current_row in state.current_rows[:current_count]:
                    updated.append(
                        f"{current_row.depth}, {current_row.speed_x}, "
                        f"{current_row.speed_y}",
                    )
            index += 1
            while index < len(lines):
                next_label = lines[index].strip()
                if next_label.startswith("波浪类型"):
                    break
                index += 1
            continue
        updated.append(lines[index])
        index += 1

    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def _sync_config_dat(config_path: Path, state: EnvironmentDataState) -> None:
    if not config_path.is_file() or not state.wave_rows:
        return
    from core.solver.config_editor import replace_config_value

    row = state.wave_rows[0]
    text = config_path.read_text(encoding="utf-8", errors="replace")
    mapping = {
        "waveHeading": row.heading,
        "wavePer": row.period,
        "waveAmp": row.amplitude,
        "waveType": "0" if state.wind_wave_index == 0 else "1",
    }
    for key, value in mapping.items():
        text = replace_config_value(text, key, value)
    config_path.write_text(text, encoding="utf-8")
