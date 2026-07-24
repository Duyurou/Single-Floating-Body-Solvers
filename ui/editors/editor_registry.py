"""不依赖 GUI 框架的 Editor 注册表。

注册表有意不理解 Qt 控件和具体 Editor 的布局。A/B/C 可以注册自己的
Editor 工厂，而不需要修改 ``MainWindow``，也不需要互相导入 UI 实现。
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from core.models.node import NodeKind, ProjectNode

EditorFactory = Callable[[ProjectNode, Any, Any], Any]


@dataclass(frozen=True)
class ReadOnlyNodeView:
    """节点没有注册 Editor 时返回的只读摘要。

    UI 可以把这个小对象显示为旧数据/只读摘要，避免在主窗口中不断增加
    大型 ``if/elif`` 分支。
    """

    node: ProjectNode
    reason: str = "no_editor_registered"
    read_only: bool = True

    @property
    def object_id(self) -> str | None:
        return self.node.object_id

    @property
    def view_key(self) -> str | None:
        return self.node.view_key


class EditorObjectNotFoundError(LookupError):
    """节点引用的工程领域对象不存在时抛出的异常。"""


class EditorRegistry:
    """把稳定的 :class:`NodeKind` 映射到独立 Editor 工厂。"""

    def __init__(self) -> None:
        self._factories: dict[NodeKind, EditorFactory] = {}

    @property
    def registered_kinds(self) -> tuple[NodeKind, ...]:
        """返回已注册类型，但不暴露内部可变字典。"""

        return tuple(self._factories)

    def register(
        self,
        node_kind: NodeKind | str,
        editor_factory: EditorFactory,
    ) -> None:
        """注册一个 Editor 工厂，并拒绝意外覆盖已有注册。"""

        kind = NodeKind(node_kind)
        if not callable(editor_factory):
            raise TypeError("editor_factory must be callable")
        if kind in self._factories:
            raise ValueError(f"editor already registered for {kind.value}")
        self._factories[kind] = editor_factory

    def factory_for(
        self,
        node_kind: NodeKind | str,
    ) -> EditorFactory | None:
        """返回节点类型对应的工厂；没有注册时返回 ``None``。"""

        return self._factories.get(NodeKind(node_kind))

    def create(
        self,
        node: ProjectNode,
        project: Any,
        services: Any,
    ) -> Any:
        """为节点创建 Editor；没有注册时返回只读摘要。

        完整的 ``ProjectNode`` 是跨模块传递的稳定边界。每个 Editor 都能
        从节点获得工程树选中的 ``object_id`` 和 ``view_key``。领域对象
        仍然保存在 ``ProjectDocument`` 中，不复制到视图节点里。
        """

        # 主窗口只需要调用这个入口，不需要知道具体 Editor 类。
        factory = self.factory_for(node.kind)
        if factory is None:
            return ReadOnlyNodeView(node)
        _ensure_referenced_object_exists(node, project)
        return factory(node, project, services)


def build_default_registry(
    factories: Mapping[NodeKind | str, EditorFactory] | None = None,
) -> EditorRegistry:
    """根据 A/B/C 所有的 Editor 工厂构建注册表。

    这里暂时不主动导入真实 Editor 模块：它们属于后续任务，有些还需要
    可选的 UI 依赖。等 Editor 实现完成后，由主窗口的组合根传入可用工厂。
    """

    registry = EditorRegistry()
    for node_kind, factory in (factories or {}).items():
        registry.register(node_kind, factory)
    return registry


_NODE_COLLECTIONS: dict[NodeKind, str] = {
    NodeKind.ENVIRONMENT: "environments",
    NodeKind.FLOATING_BODY: "floating_bodies",
    NodeKind.HYDRODYNAMICS: "hydrodynamics",
    NodeKind.HYDRO_VIEW: "hydrodynamics",
    NodeKind.CONNECTION: "connection_points",
    NodeKind.SECTION: "sections",
    NodeKind.LINE_TYPE: "line_types",
    NodeKind.CABLE: "cables",
    NodeKind.CASE: "cases",
}

_SINGLETON_ATTRIBUTES: dict[NodeKind, tuple[str, str]] = {
    NodeKind.SEA_AREA: ("sea_area", "sea_area_id"),
}


def _ensure_referenced_object_exists(node: ProjectNode, project: Any) -> None:
    # 在创建 Editor 前先检查 object_id，避免页面打开后才发现数据丢失。
    object_id = node.object_id
    if object_id is None:
        return

    collection_name = _NODE_COLLECTIONS.get(node.kind)
    if collection_name is not None:
        collection = getattr(project, collection_name, None)
        if collection is not None and object_id not in collection:
            raise EditorObjectNotFoundError(
                f"{node.kind.value} object not found: {object_id}",
            )
        return

    singleton = _SINGLETON_ATTRIBUTES.get(node.kind)
    if singleton is None:
        return
    attribute_name, id_name = singleton
    value = getattr(project, attribute_name, None)
    if value is None or getattr(value, id_name, None) != object_id:
        raise EditorObjectNotFoundError(
            f"{node.kind.value} object not found: {object_id}",
        )


__all__ = [
    "EditorFactory",
    "EditorObjectNotFoundError",
    "EditorRegistry",
    "ReadOnlyNodeView",
    "build_default_registry",
]
