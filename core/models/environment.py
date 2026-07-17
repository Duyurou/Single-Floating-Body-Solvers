"""环境数据编辑模型。"""

from dataclasses import dataclass, field


@dataclass
class EnvironmentWaveRow:
    """风浪参数表格行。"""

    heading: str = "0"
    phase: str = "0"
    period: str = "0"
    amplitude: str = "0"
    source_x: str = "0"
    source_y: str = "0"
    stretching_model: str = "0"


@dataclass
class EnvironmentWindRow:
    """风参数表格行。"""

    direction: str = "0"
    speed: str = "0"
    height: str = "0"


@dataclass
class EnvironmentCurrentRow:
    """海流参数表格行。"""

    depth: str = "0"
    speed_x: str = "0"
    speed_y: str = "0"


@dataclass
class EnvironmentDataState:
    """环境数据对话框状态。"""

    name: str = "环境数据"
    description: str = ""
    wind_wave_index: int = 0
    wind_index: int = 0
    current_index: int = 0
    wave_rows: list[EnvironmentWaveRow] = field(
        default_factory=lambda: [EnvironmentWaveRow()],
    )
    wind_rows: list[EnvironmentWindRow] = field(
        default_factory=lambda: [EnvironmentWindRow()],
    )
    current_rows: list[EnvironmentCurrentRow] = field(
        default_factory=lambda: [EnvironmentCurrentRow()],
    )
    xml_path: str = ""
