"""求解 INPUT 工作目录构建。"""

import re
import shutil
from datetime import datetime
from pathlib import Path

from core.models.case import AnalysisType, ComputeCaseRecord
from core.solver.config_editor import (
    apply_dynamic_config,
    apply_static_config,
    dynamic_base_file_names,
    patch_mooringline_for_dynamic,
)

WORK_SUBDIRS = ("bodyout", "output", "res", "surface")


class InputBuilderError(Exception):
    """INPUT 构建异常。"""


def _sanitize_name(name: str) -> str:
    """将工况名称转为安全目录名。"""
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", name.strip())
    return cleaned or "case"


def create_case_record(
    case_id: str,
    case_name: str,
    analysis_type: AnalysisType,
    cases_root: Path,
) -> ComputeCaseRecord:
    """创建工况工作目录记录。"""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = (
        f"{_sanitize_name(case_name)}_{analysis_type}_{stamp}"
    )
    work_dir = cases_root / folder
    input_dir = work_dir / "INPUT"
    output_dir = work_dir / "OUTPUT"
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    return ComputeCaseRecord(
        case_id=case_id,
        case_name=case_name,
        analysis_type=analysis_type,
        work_dir=work_dir,
        input_dir=input_dir,
        output_dir=output_dir,
    )


def ensure_solver_work_dirs(input_dir: Path) -> None:
    """创建求解器要求的工作子目录。"""
    input_dir.mkdir(parents=True, exist_ok=True)
    for subdir in WORK_SUBDIRS:
        path = input_dir / subdir
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)


def sync_config_to_bodyout(input_dir: Path) -> None:
    """将 config.dat 同步到 bodyout 目录。"""
    config_path = input_dir / "config.dat"
    if not config_path.is_file():
        raise InputBuilderError("INPUT 目录缺少 config.dat")
    shutil.copy2(config_path, input_dir / "bodyout" / "config.dat")


def _copy_files(source_dir: Path, target_dir: Path, names: list[str]) -> None:
    """按文件名列表复制文件。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        src = source_dir / name
        if src.is_file():
            shutil.copy2(src, target_dir / name)


def _copy_by_prefix(source_dir: Path, target_dir: Path, prefix: str) -> int:
    """复制指定前缀的文件，返回复制数量。"""
    if not source_dir.is_dir():
        return 0
    target_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in source_dir.iterdir():
        if item.is_file() and item.name.startswith(prefix):
            shutil.copy2(item, target_dir / item.name)
            count += 1
    return count


def prepare_static_input(
    case: ComputeCaseRecord,
    source_input_dir: Path,
) -> None:
    """为静态分析准备 INPUT 目录。"""
    if not source_input_dir.is_dir():
        raise InputBuilderError(
            f"源 INPUT 目录不存在: {source_input_dir}",
        )
    if case.input_dir.exists():
        shutil.rmtree(case.input_dir)
    shutil.copytree(source_input_dir, case.input_dir)
    ensure_solver_work_dirs(case.input_dir)
    config_path = case.input_dir / "config.dat"
    if not config_path.is_file():
        raise InputBuilderError("INPUT 目录缺少 config.dat")
    apply_static_config(config_path)
    sync_config_to_bodyout(case.input_dir)


def prepare_dynamic_input(
    case: ComputeCaseRecord,
    static_case: ComputeCaseRecord,
) -> None:
    """基于已完成静态工况准备动态 INPUT 目录。"""
    static_input = static_case.input_dir
    static_output = static_case.output_dir
    if static_case.status != "success":
        raise InputBuilderError("请先完成静态分析")
    if not static_input.is_dir():
        raise InputBuilderError("静态工况 INPUT 目录不存在")

    if case.input_dir.exists():
        shutil.rmtree(case.input_dir)
    case.input_dir.mkdir(parents=True, exist_ok=True)
    ensure_solver_work_dirs(case.input_dir)

    _copy_files(
        static_input,
        case.input_dir,
        list(dynamic_base_file_names()),
    )
    if not (case.input_dir / "risers_dynamic.in").is_file():
        static_risers = static_input / "risers_static.in"
        if static_risers.is_file():
            shutil.copy2(
                static_risers,
                case.input_dir / "risers_dynamic.in",
            )

    _copy_by_prefix(
        static_output / "Risers",
        case.input_dir / "res",
        "riser",
    )
    _copy_by_prefix(
        static_output / "Moorings",
        case.input_dir / "output",
        "Initial_Mooringline",
    )
    static_result = static_output / "Body" / "static_result.dat"
    if static_result.is_file():
        shutil.copy2(static_result, case.input_dir / "bodyout" / "static_result.dat")

    config_path = case.input_dir / "config.dat"
    if not config_path.is_file():
        raise InputBuilderError("动态 INPUT 缺少 config.dat")
    apply_dynamic_config(config_path)
    patch_mooringline_for_dynamic(case.input_dir / "Mooringline_in.dat")
    sync_config_to_bodyout(case.input_dir)
