"""工况领域模型与运行时路径合同。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Literal

AnalysisType = Literal["static", "dynamic"]


class CaseStatus(str, Enum):
    """工况的持久化状态。

    继承 ``str`` 是为了兼容旧代码：旧代码把状态和字符串比较时，
    例如 ``status == "success"``，仍然可以正常工作。
    """

    PENDING = "pending"
    PREPARING = "preparing"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def __str__(self) -> str:
        """把状态序列化为稳定的字符串值。"""
        return self.value

    @property
    def terminal(self) -> bool:
        """判断当前状态是否表示一次运行已经结束。"""
        return self in {
            CaseStatus.SUCCESS,
            CaseStatus.FAILED,
            CaseStatus.CANCELLED,
        }

    def can_transition_to(self, target: "CaseStatus | str") -> bool:
        """判断状态机是否允许转到目标状态。"""
        target_status = _coerce_status(target)
        return (
            target_status == self
            or target_status in _ALLOWED_TRANSITIONS[self]
        )


_ALLOWED_TRANSITIONS: dict[CaseStatus, frozenset[CaseStatus]] = {
    CaseStatus.PENDING: frozenset(
        {CaseStatus.PREPARING, CaseStatus.CANCELLED},
    ),
    CaseStatus.PREPARING: frozenset(
        {
            CaseStatus.RUNNING,
            CaseStatus.FAILED,
            CaseStatus.CANCELLED,
        },
    ),
    CaseStatus.RUNNING: frozenset(
        {
            CaseStatus.SUCCESS,
            CaseStatus.FAILED,
            CaseStatus.CANCELLED,
        },
    ),
    # 已完成的工况允许重新进入准备状态。旧的 INPUT/OUTPUT 是否保留，
    # 由 Service 决定；这个模型只记录新的生命周期。
    CaseStatus.SUCCESS: frozenset({CaseStatus.PREPARING}),
    CaseStatus.FAILED: frozenset({CaseStatus.PREPARING}),
    CaseStatus.CANCELLED: frozenset({CaseStatus.PREPARING}),
}

# 供 Service 校验和测试使用的公开只读约定视图。
ALLOWED_STATUS_TRANSITIONS = _ALLOWED_TRANSITIONS


def _coerce_status(value: CaseStatus | str) -> CaseStatus:
    """把持久化字符串或枚举值转换为 :class:`CaseStatus`。"""
    if isinstance(value, CaseStatus):
        return value
    try:
        return CaseStatus(value)
    except ValueError as exc:
        raise ValueError(f"未知工况状态: {value!r}") from exc


def can_transition_status(
    current: CaseStatus | str,
    target: CaseStatus | str,
) -> bool:
    """判断 ``current`` 是否可以转到 ``target``。"""
    return _coerce_status(current).can_transition_to(target)


def transition_status(
    current: CaseStatus | str,
    target: CaseStatus | str,
) -> CaseStatus:
    """校验并返回一次状态转换。

    非法的生命周期跳转会抛出 ``ValueError``，不会被静默接受。Calculation
    Service 可以把这个异常转换成普通的校验问题。
    """
    current_status = _coerce_status(current)
    target_status = _coerce_status(target)
    if not current_status.can_transition_to(target_status):
        raise ValueError(
            f"不允许的工况状态转换: {current_status.value}"
            f" -> {target_status.value}",
        )
    return target_status


@dataclass(frozen=True)
class StaticSettings:
    """静态分析的最小设置合同。"""

    iteration_count: int
    calculation_time: float
    time_step: float
    output_step: float

    def __post_init__(self) -> None:
        if self.iteration_count <= 0:
            raise ValueError("iteration_count 必须大于 0")
        _require_positive("calculation_time", self.calculation_time)
        _require_positive("time_step", self.time_step)
        _require_positive("output_step", self.output_step)


@dataclass(frozen=True)
class RegularWaveDynamicSettings:
    """规则波动态分析设置。"""

    period_count: int
    steps_per_period: int
    calculate_wave_force: bool
    body_motion_mode: str

    def __post_init__(self) -> None:
        if self.period_count <= 0:
            raise ValueError("period_count 必须大于 0")
        if self.steps_per_period <= 0:
            raise ValueError("steps_per_period 必须大于 0")
        if not self.body_motion_mode.strip():
            raise ValueError("body_motion_mode 不能为空")


@dataclass(frozen=True)
class IrregularWaveDynamicSettings:
    """不规则波动态设置的保留合同。

    当前求解器范围未必支持此模式；模型可以保存它，但 exporter 必须
    由业务层明确判断后再决定是否导出。
    """

    simulation_time: float
    time_step: float
    wave_seed: int
    wind_seed: int
    generation_duration: float
    generation_time_step: float

    def __post_init__(self) -> None:
        _require_positive("simulation_time", self.simulation_time)
        _require_positive("time_step", self.time_step)
        _require_positive("generation_duration", self.generation_duration)
        _require_positive("generation_time_step", self.generation_time_step)


@dataclass(frozen=True)
class OutputSelection:
    """工况输出选择，保持不同结果域的变量集合分开。"""

    output_step: float
    body_variables: frozenset[str] | set[str] = field(
        default_factory=frozenset,
    )
    mooring_variables: frozenset[str] | set[str] = field(
        default_factory=frozenset,
    )
    riser_variables: frozenset[str] | set[str] = field(
        default_factory=frozenset,
    )
    surface_enabled: bool = False

    def __post_init__(self) -> None:
        _require_positive("output_step", self.output_step)
        object.__setattr__(
            self,
            "body_variables",
            frozenset(self.body_variables),
        )
        object.__setattr__(
            self,
            "mooring_variables",
            frozenset(self.mooring_variables),
        )
        object.__setattr__(
            self,
            "riser_variables",
            frozenset(self.riser_variables),
        )


@dataclass(frozen=True)
class DynamicSettings:
    """动态分析设置及其静态工况依赖。"""

    wave_mode: Literal["regular", "irregular"]
    regular: RegularWaveDynamicSettings | None
    irregular: IrregularWaveDynamicSettings | None
    output: OutputSelection
    static_case_id: str

    def __post_init__(self) -> None:
        if self.wave_mode not in {"regular", "irregular"}:
            raise ValueError(f"不支持的 wave_mode: {self.wave_mode!r}")
        if not self.static_case_id.strip():
            raise ValueError("动态工况必须引用 static_case_id")
        if self.wave_mode == "regular":
            if self.regular is None or self.irregular is not None:
                raise ValueError("regular 模式必须只提供 regular 设置")
        elif self.irregular is None or self.regular is not None:
            raise ValueError("irregular 模式必须只提供 irregular 设置")


@dataclass
class CaseRunSummary:
    """一次运行的可持久化摘要；路径只能相对工况工作区。"""

    # 这些路径会随工程保存，只能相对于工况工作目录。
    input_relative_path: str | None = None
    output_relative_path: str | None = None
    log_relative_path: str | None = None
    exit_code: int | None = None
    message: str = ""

    def __post_init__(self) -> None:
        for name in (
            "input_relative_path",
            "output_relative_path",
            "log_relative_path",
        ):
            _validate_relative_path(name, getattr(self, name))


@dataclass(frozen=True)
class CasePaths:
    """一次运行使用的绝对路径，不属于工程持久化数据。"""

    # 这些是当前机器的一次运行路径，只在运行期计算，不写入工程文件。
    work_dir: Path
    input_dir: Path
    output_dir: Path
    log_path: Path

    @classmethod
    def for_case(
        cls,
        workspace_root: Path,
        case_id: str,
        log_name: str = "solver.log",
    ) -> "CasePaths":
        """根据工作区和稳定 case ID 计算运行路径，不创建目录。"""
        _validate_case_id(case_id)
        if not log_name or Path(log_name).name != log_name:
            raise ValueError("log_name 必须是单个文件名")
        root = Path(workspace_root).resolve()
        work_dir = root / "cases" / case_id
        return cls(
            work_dir=work_dir,
            input_dir=work_dir / "INPUT",
            output_dir=work_dir / "OUTPUT",
            log_path=work_dir / "logs" / log_name,
        )

    @classmethod
    def from_workspace(
        cls,
        workspace_root: Path,
        case_id: str,
        log_name: str = "solver.log",
    ) -> "CasePaths":
        """兼容更直观的工厂命名。"""
        return cls.for_case(workspace_root, case_id, log_name)

    @property
    def logs_dir(self) -> Path:
        """运行日志目录。"""
        return self.log_path.parent


@dataclass
class ComputeCase:
    """可持久化的工况配置和最近一次运行摘要。"""

    # 工况通过稳定 ID 引用环境，不复制完整 Environment 对象。
    case_id: str
    name: str
    environment_id: str

    # settings 的具体类型同时决定这是静态工况还是动态工况。
    settings: StaticSettings | DynamicSettings
    status: CaseStatus = CaseStatus.PENDING
    last_run: CaseRunSummary | None = None

    def __post_init__(self) -> None:
        _validate_case_id(self.case_id)
        if not self.name.strip():
            raise ValueError("工况名称不能为空")
        if not self.environment_id.strip():
            raise ValueError("environment_id 不能为空")
        if not isinstance(self.settings, (StaticSettings, DynamicSettings)):
            raise TypeError(
                "settings 必须是 StaticSettings 或 DynamicSettings",
            )
        self.status = _coerce_status(self.status)

    @property
    def analysis_type(self) -> AnalysisType:
        """从设置类型推导分析类型，避免重复保存不一致字段。"""
        if isinstance(self.settings, StaticSettings):
            return "static"
        return "dynamic"

    def transition_to(self, target: CaseStatus | str) -> CaseStatus:
        """校验并应用状态转换。"""
        self.status = transition_status(self.status, target)
        return self.status


@dataclass
class ComputeCaseRecord:
    """兼容现有求解器 UI 的单次静态或动态求解记录。"""

    case_id: str
    case_name: str
    analysis_type: AnalysisType
    work_dir: Path
    input_dir: Path
    output_dir: Path
    status: CaseStatus = CaseStatus.PENDING
    message: str = ""
    log_lines: list[str] = field(default_factory=list)


def _require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} 必须大于 0")


def _validate_case_id(case_id: str) -> None:
    if not case_id.strip() or case_id in {".", ".."}:
        raise ValueError("case_id 不能为空或为特殊路径")
    if Path(case_id).name != case_id or "/" in case_id or "\\" in case_id:
        raise ValueError("case_id 必须是单个路径片段")


def _validate_relative_path(name: str, value: str | None) -> None:
    if value is None:
        return
    if not value.strip():
        raise ValueError(f"{name} 不能是空字符串")
    path = Path(value)
    if path.is_absolute() or Path(path).name == "..":
        raise ValueError(f"{name} 必须是相对路径")
    if any(part == ".." for part in path.parts):
        raise ValueError(f"{name} 不能越出工况工作区")
