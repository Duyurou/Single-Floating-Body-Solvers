"""工程加载数据模型。"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ManifestInfo:
    """工程清单元信息。"""

    name: str = ""
    version: str = ""
    author: str = ""
    company: str = ""
    info: str = ""


@dataclass
class InputConfigSummary:
    """INPUT 目录配置摘要。"""

    input_dir: Path
    config_values: dict[str, str] = field(default_factory=dict)
    environment_values: dict[str, str] = field(default_factory=dict)
    config_files: list[str] = field(default_factory=list)


@dataclass
class LoadedProject:
    """已加载的 .sopro 工程。"""

    source_path: Path
    extract_dir: Path
    manifest: ManifestInfo
    input_summaries: list[InputConfigSummary] = field(
        default_factory=list,
    )
