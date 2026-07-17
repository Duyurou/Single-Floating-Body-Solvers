"""sopro 工程加载流程。"""

import shutil
from datetime import datetime
from pathlib import Path

from core.models.project import LoadedProject
from core.sopro.archive import SoproArchive, SoproArchiveError
from core.sopro.config_parser import (
    find_input_directories,
    summarize_input_directory,
)
from core.sopro.manifest import parse_manifest


class SoproLoadError(Exception):
    """工程加载异常。"""


def load_sopro_project(
    sopro_path: Path,
    workspace_root: Path,
) -> LoadedProject:
    """打开并解压 .sopro，汇总 INPUT 配置。"""
    sopro_path = sopro_path.resolve()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extract_dir = workspace_root / f"{sopro_path.stem}_{stamp}"

    if extract_dir.exists():
        shutil.rmtree(extract_dir)

    try:
        with SoproArchive(sopro_path) as archive:
            manifest = parse_manifest(archive.read_manifest_text())
            archive.extract_to(extract_dir)
    except SoproArchiveError as exc:
        raise SoproLoadError(str(exc)) from exc

    input_dirs = find_input_directories(extract_dir)
    if not input_dirs:
        raise SoproLoadError(
            "解压完成，但未找到 INPUT/config.dat 配置目录",
        )

    summaries = [
        summarize_input_directory(input_dir) for input_dir in input_dirs
    ]
    return LoadedProject(
        source_path=sopro_path,
        extract_dir=extract_dir,
        manifest=manifest,
        input_summaries=summaries,
    )
