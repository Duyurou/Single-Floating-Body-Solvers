"""工程树节点合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePosixPath, PureWindowsPath


class NodeKind(str, Enum):
    """工程树和 EditorRegistry 使用的稳定节点类型。"""

    GROUP = "group"
    ENVIRONMENT = "environment"
    SEA_AREA = "sea_area"
    FLOATING_BODY = "floating_body"
    HYDRODYNAMICS = "hydrodynamics"
    HYDRO_VIEW = "hydro_view"
    CONNECTION = "connection"
    SECTION = "section"
    LINE_TYPE = "line_type"
    CABLE = "cable"
    CASE = "case"
    RESULT = "result"
    LEGACY = "legacy"

    def __str__(self) -> str:
        return self.value


@dataclass
class ProjectNode:
    """工程树中的一个位置，可选地引用一个领域对象。

    节点只保存稳定 ID、父子关系和视图定位信息，不复制完整领域对象。
    因此工程树、Editor 和领域模型可以分别维护。
    """

    # 工程树节点自己的身份、显示名称和稳定类型。
    node_id: str
    name: str
    kind: NodeKind

    # 树结构只用 ID 连接，避免父子节点互相持有造成循环引用。
    parent_id: str | None = None
    children_ids: list[str] = field(default_factory=list)

    # object_id 指向 ProjectDocument 中的领域对象；view_key 表示同一个
    # 对象的不同页面，例如同一水动力数据集的附加质量和辐射阻尼视图。
    object_id: str | None = None
    view_key: str | None = None

    # source_type/source_path 保存旧 .sopro 清单中的来源信息，供 codec
    # 保存往返使用；它们不等同于新的领域类型和机器绝对路径。
    source_type: str | None = None
    source_path: str | None = None

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        if self.parent_id == self.node_id:
            raise ValueError("a node cannot be its own parent")
        if self.node_id in self.children_ids:
            raise ValueError("a node cannot be its own child")
        if len(self.children_ids) != len(set(self.children_ids)):
            raise ValueError("children_ids must not contain duplicates")
        if self.view_key is not None and self.object_id is None:
            raise ValueError("view_key requires object_id")
        if self.kind is NodeKind.HYDRO_VIEW:
            if self.object_id is None or self.view_key is None:
                raise ValueError(
                    "hydro view nodes require object_id and view_key",
                )
        if self.source_path is not None:
            _validate_relative_source_path(self.source_path)


def _validate_relative_source_path(source_path: str) -> None:
    # 同时按 POSIX 和 Windows 规则检查，避免跨平台时接受危险路径。
    if not source_path.strip():
        raise ValueError("source_path must not be empty")
    posix_path = PurePosixPath(source_path)
    windows_path = PureWindowsPath(source_path)
    if posix_path.is_absolute() or windows_path.is_absolute():
        raise ValueError("source_path must be relative to the project root")
    if ".." in posix_path.parts or ".." in windows_path.parts:
        raise ValueError("source_path must not escape the project root")
