"""计算工况数据模型。"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

AnalysisType = Literal["static", "dynamic"]
CaseStatus = Literal["pending", "running", "success", "failed"]


@dataclass
class ComputeCaseRecord:
    """单次静态或动态求解工况记录。"""

    case_id: str
    case_name: str
    analysis_type: AnalysisType
    work_dir: Path
    input_dir: Path
    output_dir: Path
    status: CaseStatus = "pending"
    message: str = ""
    log_lines: list[str] = field(default_factory=list)
