"""工程加载摘要和所有模块共享的工程文档合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from core.models.node import ProjectNode
from core.models.resource import ResourceRef


# 这些 Protocol 只规定“领域对象必须提供哪个稳定 ID”。
# 浮体、管缆等完整模型属于后续任务；这里不提前导入或猜测它们的字段。
# 因此 ProjectDocument 可以先成为公共容器，各负责人再独立实现领域模型。
class _EnvironmentEntity(Protocol):
    environment_id: str


class _SeaAreaEntity(Protocol):
    sea_area_id: str


class _FloatingBodyEntity(Protocol):
    body_id: str


class _HydrodynamicEntity(Protocol):
    dataset_id: str


class _ConnectionPointEntity(Protocol):
    point_id: str


class _SectionEntity(Protocol):
    section_id: str


class _LineTypeEntity(Protocol):
    line_type_id: str


class _CableEntity(Protocol):
    cable_id: str


class _CableAccessoryEntity(Protocol):
    accessory_id: str


class _ComputeCaseEntity(Protocol):
    case_id: str


@dataclass
class ManifestInfo:
    """工程 manifest 的基本信息摘要。"""

    name: str = ""
    version: str = ""
    author: str = ""
    company: str = ""
    info: str = ""


@dataclass
class InputConfigSummary:
    """一个已解压 INPUT 目录的配置摘要。"""

    input_dir: Path
    config_values: dict[str, str] = field(default_factory=dict)
    environment_values: dict[str, str] = field(default_factory=dict)
    config_files: list[str] = field(default_factory=list)


@dataclass
class LoadedProject:
    """已经加载的 ``.sopro`` 工程以及解压后的配置摘要。"""

    source_path: Path
    extract_dir: Path
    manifest: ManifestInfo
    input_summaries: list[InputConfigSummary] = field(
        default_factory=list,
    )


@dataclass
class ProjectDocument:
    """所有工程模块共享的轻量内存根对象。

    这里的各个领域集合只保存领域对象和稳定引用。工程文档有意不保存
    UI 控件、求解器进程、机器相关的工作目录，也不常驻大型水动力或
    结果数组。后续模块通过这个对象协作，但不应把私有实现塞进来。
    """

    # 工程自身的稳定身份和用户可见名称。
    project_id: str
    name: str

    # 一个工程可以保存多个环境组合；计算工况通过 environment_id 选择其中一个。
    # 使用稳定 ID -> 对象的字典，避免把环境对象复制到每个工况里。
    environments: dict[str, _EnvironmentEntity] = field(
        default_factory=dict,
    )

    # 当前工程模型把海域作为单对象保存；它与可复用的环境组合不是同一概念。
    sea_area: _SeaAreaEntity | None = None

    # 下面的领域对象可能有多个，统一用“稳定 ID -> 对象”的字典保存。
    # 其他模块只保存 ID 引用，不复制整个对象。
    floating_bodies: dict[str, _FloatingBodyEntity] = field(
        default_factory=dict,
    )
    hydrodynamics: dict[str, _HydrodynamicEntity] = field(
        default_factory=dict,
    )
    connection_points: dict[str, _ConnectionPointEntity] = field(
        default_factory=dict,
    )
    sections: dict[str, _SectionEntity] = field(default_factory=dict)
    line_types: dict[str, _LineTypeEntity] = field(default_factory=dict)
    cables: dict[str, _CableEntity] = field(default_factory=dict)
    cable_accessories: dict[str, _CableAccessoryEntity] = field(
        default_factory=dict,
    )
    cases: dict[str, _ComputeCaseEntity] = field(default_factory=dict)

    # resources 记录工程文件资源；nodes 记录工程树结构。
    # 它们和领域对象分开，避免 UI 树变成真正的数据存储位置。
    resources: dict[str, ResourceRef] = field(default_factory=dict)
    nodes: dict[str, ProjectNode] = field(default_factory=dict)

    # 暂时不支持的旧 PACKET 先原样保留，保证打开再保存时不丢信息。
    legacy_packets: dict[str, str] = field(default_factory=dict)

    # dirty 只表示“内存内容是否有未保存修改”，不负责真正写文件。
    is_dirty: bool = False

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")

    def mark_dirty(self) -> None:
        """标记工程已经发生尚未保存的修改。"""

        self.is_dirty = True

    def mark_saved(self) -> None:
        """标记当前内存状态已经保存。"""

        self.is_dirty = False
