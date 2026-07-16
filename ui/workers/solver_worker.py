"""求解器后台工作线程。"""

from PySide6.QtCore import QThread, Signal

from core.models.case import ComputeCaseRecord
from core.solver.input_builder import (
    InputBuilderError,
    prepare_dynamic_input,
    prepare_static_input,
)
from core.solver.result_archiver import archive_solver_output
from core.solver.runner import SolverRunError, SolverRunner


class SolverWorker(QThread):
    """在后台线程中执行求解任务。"""

    progress_changed = Signal(int)
    log_emitted = Signal(str)
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        case: ComputeCaseRecord,
        solver_runner: SolverRunner,
        source_input_dir,
        static_case: ComputeCaseRecord | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._case = case
        self._solver_runner = solver_runner
        self._source_input_dir = source_input_dir
        self._static_case = static_case

    def run(self) -> None:
        """执行 INPUT 准备、求解与结果归档。"""
        try:
            self.progress_changed.emit(10)
            self._case.status = "running"
            if self._case.analysis_type == "static":
                prepare_static_input(self._case, self._source_input_dir)
                self.log_emitted.emit(
                    f"[INFO] 静态 INPUT 已准备: {self._case.input_dir}",
                )
            else:
                if self._static_case is None:
                    raise InputBuilderError("未找到可用的静态工况")
                prepare_dynamic_input(self._case, self._static_case)
                self.log_emitted.emit(
                    f"[INFO] 动态 INPUT 已准备: {self._case.input_dir}",
                )

            self.progress_changed.emit(30)
            self.log_emitted.emit("[INFO] 正在调用求解器...")
            result = self._solver_runner.run(
                self._case.input_dir,
                self._case.output_dir,
                analysis_type=self._case.analysis_type,
            )
            self.progress_changed.emit(80)
            archived = archive_solver_output(
                self._case.input_dir,
                self._case.output_dir,
            )
            self._case.status = "success"
            self._case.message = result.message
            self.progress_changed.emit(100)
            self.log_emitted.emit(
                "[INFO] 结果已归档到 OUTPUT: " + ", ".join(archived.keys()),
            )
            self.succeeded.emit(self._case)
        except (InputBuilderError, SolverRunError) as exc:
            self._case.status = "failed"
            self._case.message = str(exc)
            self.failed.emit(str(exc))
        except Exception as exc:
            self._case.status = "failed"
            self._case.message = str(exc)
            self.failed.emit(f"未知错误: {exc}")
