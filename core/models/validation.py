"""跨模块共享的校验问题和命令结果合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

IssueLevel = Literal["error", "warning"]


@dataclass(frozen=True)
class ValidationIssue:
    """一个可以定位到具体字段的稳定校验问题。"""

    # level 决定是否阻止操作；code 供程序稳定识别问题类型。
    level: IssueLevel
    code: str

    # path 指向具体对象/字段，message 是展示给用户的说明。
    path: str
    message: str

    def __post_init__(self) -> None:
        if self.level not in ("error", "warning"):
            raise ValueError("level must be 'error' or 'warning'")
        if not self.code.strip():
            raise ValueError("code must not be empty")
        if not self.message.strip():
            raise ValueError("message must not be empty")

    @property
    def is_error(self) -> bool:
        return self.level == "error"


@dataclass
class CommandResult:
    """用户操作或 Service 操作的统一结果。

    调用方通过 ``success`` 判断操作是否完成，通过 ``issues`` 展示错误
    和警告，通过 ``changed_ids``、``created_paths`` 刷新界面或后续流程。
    """

    success: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    # Service 用这两个列表告诉调用方：哪些对象改变、哪些文件已生成。
    changed_ids: list[str] = field(default_factory=list)
    created_paths: list[Path] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.success and self.has_errors:
            raise ValueError("a successful result cannot contain errors")

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.is_error]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if not issue.is_error]

    @property
    def has_errors(self) -> bool:
        return any(issue.is_error for issue in self.issues)
