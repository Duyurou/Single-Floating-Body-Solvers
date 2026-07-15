"""应用启动与环境初始化。"""

import sys
from pathlib import Path


def get_project_root() -> Path:
    """返回 project 根目录路径。"""
    return Path(__file__).resolve().parent.parent


def get_solver_root() -> Path:
    """返回单浮体求解器集成包中的 solver 目录。"""
    return get_project_root().parent / "单浮体求解器集成包" / "solver"


def get_cases_root() -> Path:
    """返回工况工作目录根路径。"""
    root = get_project_root() / "workspace" / "cases"
    root.mkdir(parents=True, exist_ok=True)
    return root


def setup_import_path() -> Path:
    """将 project 根目录加入 sys.path。"""
    project_root = get_project_root()
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return project_root
