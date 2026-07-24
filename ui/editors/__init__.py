"""主窗口与各领域模块共享的 Editor 注册合同。"""

from ui.editors.editor_registry import (
    EditorObjectNotFoundError,
    EditorRegistry,
    ReadOnlyNodeView,
    build_default_registry,
)

__all__ = [
    "EditorObjectNotFoundError",
    "EditorRegistry",
    "ReadOnlyNodeView",
    "build_default_registry",
]
