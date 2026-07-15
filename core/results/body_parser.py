"""浮体时程结果文件解析。"""

from dataclasses import dataclass
from pathlib import Path


class BodyParserError(Exception):
    """浮体结果解析异常。"""


@dataclass(frozen=True)
class BodyTimeSeries:
    """浮体六自由度时程数据。"""

    time: tuple[float, ...]
    surge: tuple[float, ...]
    sway: tuple[float, ...]
    heave: tuple[float, ...]
    roll: tuple[float, ...]
    pitch: tuple[float, ...]
    yaw: tuple[float, ...]

    @property
    def point_count(self) -> int:
        """返回时程点数。"""
        return len(self.time)


def parse_output_disp(path: Path) -> BodyTimeSeries:
    """解析 output_disp.dat 浮体位移时程文件。"""
    if not path.is_file():
        raise BodyParserError(f"结果文件不存在: {path}")

    rows: list[tuple[float, float, float, float, float, float, float]] = []
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(),
        start=1,
    ):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) < 7:
            raise BodyParserError(
                f"{path.name} 第 {line_no} 行列数不足: {len(parts)}",
            )
        try:
            values = tuple(float(part) for part in parts[:7])
        except ValueError as exc:
            raise BodyParserError(
                f"{path.name} 第 {line_no} 行数值格式错误",
            ) from exc
        rows.append(values)

    if not rows:
        raise BodyParserError(f"{path.name} 未包含有效时程数据")

    return BodyTimeSeries(
        time=tuple(row[0] for row in rows),
        surge=tuple(row[1] for row in rows),
        sway=tuple(row[2] for row in rows),
        heave=tuple(row[3] for row in rows),
        roll=tuple(row[4] for row in rows),
        pitch=tuple(row[5] for row in rows),
        yaw=tuple(row[6] for row in rows),
    )
