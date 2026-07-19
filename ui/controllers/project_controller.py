"""工程打开与信息展示控制器。"""

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from core.models.environment import EnvironmentDataState
from core.models.project import LoadedProject
from core.sopro.environment_data import (
    EnvironmentDataError,
    load_environment_state,
    save_environment_state,
)
from core.sopro.loader import SoproLoadError, load_sopro_project


class ProjectController:
    """负责打开 .sopro 并生成日志/交互展示文本。"""

    SOPRO_FILTER = "海工工程文件 (*.sopro)"

    def __init__(
        self,
        parent: QWidget,
        workspace_root: Path,
    ) -> None:
        self._parent = parent
        self._workspace_root = workspace_root
        self._loaded_project: LoadedProject | None = None

    @property
    def loaded_project(self) -> LoadedProject | None:
        """当前已加载工程。"""
        return self._loaded_project

    def get_primary_input_dir(self) -> Path | None:
        """返回首个 INPUT 目录。"""
        project = self._loaded_project
        if project is None or not project.input_summaries:
            return None
        return project.input_summaries[0].input_dir

    def load_environment_data(self) -> EnvironmentDataState:
        """加载当前工程的环境数据。"""
        project = self._loaded_project
        if project is None:
            return EnvironmentDataState()
        input_dir = self.get_primary_input_dir()
        return load_environment_state(project.extract_dir, input_dir)

    def save_environment_data(
        self,
        state: EnvironmentDataState,
    ) -> tuple[bool, str]:
        """保存环境数据并刷新工程摘要。"""
        project = self._loaded_project
        if project is None:
            return False, "尚未打开工程，无法保存环境数据。"
        try:
            xml_path = save_environment_state(
                project.extract_dir,
                self.get_primary_input_dir(),
                state,
            )
        except EnvironmentDataError as exc:
            return False, str(exc)
        except OSError as exc:
            return False, f"写入环境数据失败: {exc}"

        input_dir = self.get_primary_input_dir()
        if input_dir is not None:
            from core.sopro.config_parser import summarize_input_directory

            summary = summarize_input_directory(input_dir)
            if project.input_summaries:
                project.input_summaries[0] = summary
        state.xml_path = str(xml_path)
        return True, self._format_interaction(project)

    def open_project_dialog(self) -> tuple[bool, str, str]:
        """
        弹出打开对话框并加载工程。

        返回 (是否成功, 日志文本, 交互文本)。
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self._parent,
            "打开工程",
            "",
            self.SOPRO_FILTER,
        )
        if not file_path:
            return False, "", ""
        return self.open_project(Path(file_path))

    def open_project(
        self,
        sopro_path: Path,
    ) -> tuple[bool, str, str]:
        """加载指定 .sopro 工程文件。"""
        try:
            project = load_sopro_project(
                sopro_path,
                self._workspace_root,
            )
        except SoproLoadError as exc:
            QMessageBox.warning(
                self._parent,
                "打开工程失败",
                str(exc),
            )
            log_text = self._format_failure_log(sopro_path, str(exc))
            return False, log_text, ""

        self._loaded_project = project
        return (
            True,
            self._format_log(project),
            self._format_interaction(
                project,
            ),
        )

    def _format_log(self, project: LoadedProject) -> str:
        """生成日志窗口文本。"""
        manifest = project.manifest
        lines = [
            "[INFO] 工程文件读入成功",
            f"[INFO] 源文件: {project.source_path}",
            f"[INFO] 解压目录: {project.extract_dir}",
            f"[INFO] 工程名称: {manifest.name or '未命名'}",
            f"[INFO] 版本: {manifest.version or '-'}",
            f"[INFO] 作者: {manifest.author or '-'}",
            ("[INFO] 发现 INPUT 目录数量: " f"{len(project.input_summaries)}"),
        ]
        for index, summary in enumerate(project.input_summaries, start=1):
            rel = summary.input_dir.relative_to(project.extract_dir)
            lines.append(f"[INFO] INPUT#{index}: {rel}")
            lines.append(
                "[INFO] 配置文件: " + ", ".join(summary.config_files),
            )
        return "\n".join(lines)

    def _format_interaction(self, project: LoadedProject) -> str:
        """生成交互窗口配置摘要文本。"""
        manifest = project.manifest
        lines = [
            "=== 工程读入成功 ===",
            "",
            f"工程名称: {manifest.name or '未命名'}",
            f"工程信息: {manifest.info or '-'}",
            f"源文件: {project.source_path.name}",
            "",
        ]
        for index, summary in enumerate(project.input_summaries, start=1):
            lines.extend(
                self._format_input_summary(index, summary, project),
            )
        return "\n".join(lines).strip() + "\n"

    def _format_input_summary(
        self,
        index: int,
        summary,
        project: LoadedProject,
    ) -> list[str]:
        """格式化单个 INPUT 目录摘要。"""
        rel = summary.input_dir.relative_to(project.extract_dir)
        lines = [
            f"--- INPUT 目录 #{index} ---",
            f"路径: {rel}",
            "",
            "[config.dat 关键参数]",
        ]
        labels = {
            "mass": "浮体质量(kg)",
            "waveType": "波浪类型编码",
            "waveHeading": "浪向(deg)",
            "wavePer": "波浪周期(s)",
            "waveAmp": "波幅(m)",
            "depth": "水深(m)",
            "cal_time": "计算时长(s)",
            "dt": "时间步长(s)",
            "sta_Type": "分析类型(0静态/1动态)",
            "out_step": "输出步长(s)",
            "numRisers": "立管数量",
        }
        for key, label in labels.items():
            if key in summary.config_values:
                lines.append(
                    f"  {label}: {summary.config_values[key]}",
                )
        if summary.environment_values:
            lines.append("")
            lines.append("[Environment_in.dat 环境参数]")
            env_labels = {
                "water_depth": "水深(m)",
                "water_density": "海水密度(kg/m^3)",
                "gravity": "重力加速度(m/s^2)",
                "wave_type_name": "波浪类型",
                "wave_params": "波浪参数",
            }
            for key, label in env_labels.items():
                if key in summary.environment_values:
                    lines.append(
                        "  " f"{label}: {summary.environment_values[key]}",
                    )
        lines.append("")
        return lines

    def _format_failure_log(
        self,
        sopro_path: Path,
        reason: str,
    ) -> str:
        """生成失败日志。"""
        return "\n".join(
            [
                "[ERROR] 工程文件读入失败",
                f"[ERROR] 源文件: {sopro_path}",
                f"[ERROR] 原因: {reason}",
            ],
        )
