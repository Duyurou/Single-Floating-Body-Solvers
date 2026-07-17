"""求解器输出归档。"""

import shutil
from pathlib import Path

_OUTPUT_MAPPINGS = {
    "bodyout": "Body",
    "output": "Moorings",
    "res": "Risers",
    "surface": "Surface",
}


def archive_solver_output(
    input_dir: Path,
    output_dir: Path,
) -> dict[str, Path]:
    """将 INPUT 下求解输出复制到 OUTPUT 目录。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    archived: dict[str, Path] = {}
    for src_name, dst_name in _OUTPUT_MAPPINGS.items():
        src = input_dir / src_name
        dst = output_dir / dst_name
        if not src.exists():
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        archived[dst_name] = dst
    return archived
