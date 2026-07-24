"""工程内部文件资源的引用合同。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath


@dataclass(frozen=True)
class ResourceRef:
    """文件资源的稳定身份和相对工程根目录的路径。

    资源只保存“文件在哪里、是什么类型、原始名称是什么”，不在模型中
    直接保存文件内容。这样保存工程时可以检查路径，读取大文件时也能
    延迟进行。
    """

    # id 用于工程内引用；resource_type 说明文件用途。
    id: str
    resource_type: str

    # 只持久化相对工程根目录的路径，工程移动到其他机器后仍可打开。
    relative_path: str
    original_name: str

    # 导入的历史资源默认只读，修改时应显式复制或由 Service 处理。
    read_only: bool = True

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("resource id must not be empty")
        if not self.resource_type.strip():
            raise ValueError("resource_type must not be empty")
        if not self.original_name.strip():
            raise ValueError("original_name must not be empty")
        _validate_relative_path(self.relative_path)

    def resolve_from(self, project_root: Path) -> Path:
        """把相对路径解析为 ``project_root`` 下的实际路径。"""

        return project_root / Path(self.relative_path)


def _validate_relative_path(relative_path: str) -> None:
    # 绝对路径和 .. 都可能让资源逃出工程目录，因此在合同层直接拒绝。
    if not relative_path.strip():
        raise ValueError("relative_path must not be empty")
    posix_path = PurePosixPath(relative_path)
    windows_path = PureWindowsPath(relative_path)
    if posix_path.is_absolute() or windows_path.is_absolute():
        raise ValueError("relative_path must be relative to the project root")
    if ".." in posix_path.parts or ".." in windows_path.parts:
        raise ValueError("relative_path must not escape the project root")
