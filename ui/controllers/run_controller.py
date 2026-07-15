"""求解器运行控制器。"""

from uuid import uuid4

from PySide6.QtWidgets import QMessageBox, QWidget

from app.bootstrap import get_cases_root, get_solver_root
from core.models.case import ComputeCaseRecord
from core.models.project import LoadedProject
from core.solver.input_builder import create_case_record
from core.solver.runner import SolverRunner
from ui.dialogs.compute_task_dialog import ComputeTaskFormData
from ui.workers.solver_worker import SolverWorker


class RunController:
    """管理工况创建与求解器调用。"""

    def __init__(self, parent: QWidget) -> None:
        self._parent = parent
        self._solver_runner = SolverRunner(get_solver_root())
        self._cases: dict[str, ComputeCaseRecord] = {}
        self._active_worker: SolverWorker | None = None
        self._project_key: str | None = None

    @property
    def active_worker(self) -> SolverWorker | None:
        """当前运行中的后台求解线程。"""
        return self._active_worker

    def bind_project(self, project: LoadedProject | None) -> None:
        """绑定当前打开的工程。"""
        if project is None:
            self._project_key = None
            return
        self._project_key = str(project.extract_dir.resolve())

    def start_analysis(
        self,
        form_data: ComputeTaskFormData,
        analysis_type: str,
        project: LoadedProject | None,
        on_progress,
        on_log,
        on_success,
        on_failure,
    ) -> ComputeCaseRecord | None:
        """启动静态或动态分析。"""
        if project is None:
            QMessageBox.warning(self._parent, "无法计算", "请先打开工程文件。")
            return None
        if form_data.mode != "单浮体":
            QMessageBox.warning(
                self._parent,
                "无法计算",
                "当前仅支持单浮体模式。",
            )
            return None
        if self._active_worker is not None and self._active_worker.isRunning():
            QMessageBox.warning(
                self._parent,
                "无法计算",
                "已有计算任务正在运行，请先中止或等待完成。",
            )
            return None
        if not project.input_summaries:
            QMessageBox.warning(
                self._parent,
                "无法计算",
                "当前工程未找到 INPUT 配置目录。",
            )
            return None

        case_name = form_data.case_name.strip() or "新建工况"
        case_id = str(uuid4())
        case = create_case_record(
            case_id,
            case_name,
            analysis_type,
            get_cases_root(),
        )
        self._cases[case_id] = case

        static_case = None
        if analysis_type == "dynamic":
            static_case = self._find_latest_static_case()
            if static_case is None:
                QMessageBox.warning(
                    self._parent,
                    "无法计算",
                    "请先完成静态分析，再运行动态分析。",
                )
                return None

        source_input = project.input_summaries[0].input_dir
        worker = SolverWorker(
            case,
            self._solver_runner,
            source_input,
            static_case=static_case,
        )
        worker.progress_changed.connect(on_progress)
        worker.log_emitted.connect(on_log)
        worker.succeeded.connect(on_success)
        worker.failed.connect(on_failure)
        worker.finished.connect(self._clear_active_worker)
        self._active_worker = worker
        worker.start()
        return case

    def abort_running(self) -> bool:
        """尝试中止当前求解线程。"""
        if self._active_worker is None:
            return False
        if self._active_worker.isRunning():
            self._active_worker.requestInterruption()
            self._active_worker.terminate()
            self._active_worker.wait(3000)
        self._active_worker = None
        return True

    def get_case(self, case_id: str) -> ComputeCaseRecord | None:
        """按 ID 获取工况记录。"""
        return self._cases.get(case_id)

    def _find_latest_static_case(self) -> ComputeCaseRecord | None:
        """查找当前工程最近一次成功的静态工况。"""
        static_cases = [
            item
            for item in self._cases.values()
            if item.analysis_type == "static" and item.status == "success"
        ]
        if not static_cases:
            return None
        return sorted(static_cases, key=lambda item: item.work_dir)[-1]

    def _clear_active_worker(self) -> None:
        """求解线程结束后清理引用。"""
        self._active_worker = None
