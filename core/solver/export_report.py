"""INPUT 导出报告和文件所有权合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Literal

if TYPE_CHECKING:
    from core.models.validation import ValidationIssue


InputOwner = Literal["A", "B", "C"]

# 每个具体 INPUT 文件只有一个最终写入者。共享字段先由领域 exporter
# 生成片段，最终组装仍归 config.dat 的唯一 owner B。
INPUT_FILE_OWNERS: dict[str, InputOwner] = {
    "Environment_in.dat": "A",
    "config.dat": "B",
    "Mooringline_in.dat": "C",
    "risers_static.in": "C",
    "risers_dynamic.in": "C",
}

INPUT_PATTERN_OWNERS: dict[str, InputOwner] = {
    "WAMIT*": "B",
}

# 两个语义等价的公开名称，便于任务文档和服务层按自己的命名习惯
# 引用同一份所有权合同。
INPUT_FILE_OWNERSHIP = INPUT_FILE_OWNERS
INPUT_OWNERSHIP = INPUT_FILE_OWNERS

# 发生 exporter 错误时保留已创建文件，便于诊断；调度器不得把它们当作
# 可运行 INPUT，除非 errors 为空。
KEEP_CREATED_PATHS_ON_ERROR = True


@dataclass
class ExportReport:
    """一个或多个 exporter 的可合并结果。"""

    # created_paths 让调度器知道生成了哪些文件；warnings 不阻止运行；
    # errors 存在时禁止启动求解器，但保留已生成文件用于定位问题。
    created_paths: list[Path] = field(default_factory=list)
    warnings: list["ValidationIssue"] = field(default_factory=list)
    errors: list["ValidationIssue"] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.created_paths = [Path(path) for path in self.created_paths]
        self.warnings = list(self.warnings)
        self.errors = list(self.errors)

    @property
    def has_errors(self) -> bool:
        """是否存在阻止求解器启动的导出错误。"""
        return bool(self.errors)

    @property
    def ok(self) -> bool:
        """导出是否没有 error（warning 不阻止调度）。"""
        return not self.has_errors

    @property
    def successful(self) -> bool:
        """``ok`` 的可读别名，方便服务层表达意图。"""
        return self.ok

    def merge(self, *reports: "ExportReport") -> "ExportReport":
        """返回合并后的新报告，不修改参与合并的原报告。"""
        created = list(self.created_paths)
        warnings = list(self.warnings)
        errors = list(self.errors)
        for report in reports:
            created.extend(report.created_paths)
            warnings.extend(report.warnings)
            errors.extend(report.errors)
        return ExportReport(created, warnings, errors)

    @classmethod
    def combine(cls, reports: Iterable["ExportReport"]) -> "ExportReport":
        """按调用顺序合并报告。"""
        combined = cls()
        for report in reports:
            combined = combined.merge(report)
        return combined

    def __bool__(self) -> bool:
        return self.ok


def input_owner(file_name: str) -> InputOwner | None:
    """按精确文件名或受控模式返回唯一写入者。"""
    # 先检查确定文件名，再检查经过合同允许的 WAMIT 前缀模式。
    if file_name in INPUT_FILE_OWNERS:
        return INPUT_FILE_OWNERS[file_name]
    if file_name.startswith("WAMIT"):
        return INPUT_PATTERN_OWNERS["WAMIT*"]
    return None


def input_file_owner(file_name: str) -> InputOwner | None:
    """``input_owner`` 的语义别名。"""
    return input_owner(file_name)
