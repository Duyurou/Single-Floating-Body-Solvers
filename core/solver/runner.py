"""单浮体求解器进程调用。"""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from core.models.case import AnalysisType


class SolverRunError(Exception):
    """求解器运行异常。"""


@dataclass
class SolverResult:
    """求解器执行结果。"""

    success: bool
    exit_code: int
    message: str
    input_dir: Path
    output_dir: Path


class SolverRunner:
    """封装 hydrodyn_newversion.exe 调用。"""

    STATIC_BODY_FILES = ("static_result.dat",)
    DYNAMIC_BODY_FILES = (
        "output_disp.dat",
        "output_force_total.dat",
    )

    def __init__(self, solver_root: Path) -> None:
        self.solver_root = solver_root.resolve()
        self.exe_path = self.solver_root / "hydroMod" / "hydrodyn_newversion.exe"
        self.fortran_dir = self.solver_root / "Fortran"

    def validate(self) -> None:
        """检查求解器可执行文件是否存在。"""
        if not self.exe_path.is_file():
            raise SolverRunError(f"未找到求解器: {self.exe_path}")

    def run(
        self,
        input_dir: Path,
        output_dir: Path,
        analysis_type: AnalysisType = "static",
    ) -> SolverResult:
        """调用求解器并校验关键输出。"""
        self.validate()
        input_dir = input_dir.resolve()
        output_dir = output_dir.resolve()
        if not (input_dir / "config.dat").is_file():
            raise SolverRunError(f"INPUT 缺少 config.dat: {input_dir}")

        for subdir in ("bodyout", "output", "res", "surface"):
            (input_dir / subdir).mkdir(parents=True, exist_ok=True)
        config_path = input_dir / "config.dat"
        bodyout_config = input_dir / "bodyout" / "config.dat"
        if config_path.is_file():
            shutil.copy2(config_path, bodyout_config)

        env = os.environ.copy()
        path_parts = [
            str(self.solver_root / "hydroMod"),
            str(self.fortran_dir),
            str(self.solver_root),
            env.get("PATH", ""),
        ]
        env["PATH"] = ";".join(path_parts)

        completed = subprocess.run(
            [str(self.exe_path), self._format_input_arg(input_dir)],
            cwd=str(self.solver_root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        process_error = self._extract_process_error(stdout, stderr)
        if completed.returncode != 0:
            detail = process_error or stderr.strip() or "无错误输出"
            raise SolverRunError(
                f"求解器退出码 {completed.returncode}: {detail}",
            )
        if process_error:
            raise SolverRunError(process_error)

        missing = self._missing_required_files(input_dir, analysis_type)
        if missing:
            raise SolverRunError(
                "求解器未生成必需结果: " + ", ".join(missing),
            )
        return SolverResult(
            success=True,
            exit_code=completed.returncode,
            message="求解完成",
            input_dir=input_dir,
            output_dir=output_dir,
        )

    def _format_input_arg(self, input_dir: Path) -> str:
        """按旧软件约定格式化 INPUT 目录参数。"""
        path_text = str(input_dir.resolve())
        if os.name == "nt":
            return path_text if path_text.endswith("\\") else f"{path_text}\\"
        return path_text if path_text.endswith("/") else f"{path_text}/"

    def _extract_process_error(self, stdout: str, stderr: str) -> str | None:
        """从求解器输出中提取 HandProcess 失败信息。"""
        for text in (stdout, stderr):
            for line in reversed(text.splitlines()):
                normalized = line.strip()
                if re.search(r"HandProcess:failures:", normalized, re.IGNORECASE):
                    return normalized
        return None

    def _missing_required_files(
        self,
        input_dir: Path,
        analysis_type: AnalysisType,
    ) -> list[str]:
        """按分析类型检查关键结果文件。"""
        missing: list[str] = []
        body_dir = input_dir / "bodyout"
        required = (
            self.STATIC_BODY_FILES
            if analysis_type == "static"
            else self.DYNAMIC_BODY_FILES
        )
        for name in required:
            target = body_dir / name
            if not target.is_file() or target.stat().st_size == 0:
                missing.append(name)
        return missing
