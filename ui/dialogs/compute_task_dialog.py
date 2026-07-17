"""计算任务对话框。"""

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QWidget,
)


@dataclass
class ComputeTaskFormData:
    """计算任务表单数据。"""

    case_name: str
    environment: str
    mode: str
    description: str


class ComputeTaskDialog(QDialog):
    """计算任务参数与运算控制对话框。"""

    static_analysis_requested = Signal(ComputeTaskFormData)
    dynamic_analysis_requested = Signal(ComputeTaskFormData)
    abort_requested = Signal()

    MODE_OPTIONS = ("单浮体", "多浮体")
    DEFAULT_CASE_NAME = "新建工况"
    DEFAULT_ENVIRONMENT = "环境数据"
    DEFAULT_MODE = "单浮体"

    def __init__(
        self,
        parent: QWidget | None = None,
        environment_options: list[str] | None = None,
    ) -> None:
        super().__init__(parent)
        self._environment_options = environment_options or [
            self.DEFAULT_ENVIRONMENT,
        ]
        self._init_ui()
        self._init_defaults()

    def _init_ui(self) -> None:
        """初始化对话框布局与控件。"""
        self.setWindowTitle("计算任务")
        self.setModal(True)
        self.resize(540, 330)

        root_layout = QGridLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setHorizontalSpacing(12)
        root_layout.setVerticalSpacing(10)

        self._case_name_edit = QLineEdit()
        self._environment_combo = QComboBox()
        self._mode_combo = QComboBox()
        self._description_edit = QPlainTextEdit()
        self._description_edit.setFixedHeight(72)

        self._environment_combo.addItems(self._environment_options)
        self._mode_combo.addItems(self.MODE_OPTIONS)

        root_layout.addWidget(QLabel("工况名称"), 0, 0)
        root_layout.addWidget(self._case_name_edit, 0, 1, 1, 2)
        root_layout.addWidget(QLabel("环境选项"), 1, 0)
        root_layout.addWidget(self._environment_combo, 1, 1, 1, 2)
        root_layout.addWidget(QLabel("模式选择"), 2, 0)
        root_layout.addWidget(self._mode_combo, 2, 1, 1, 2)
        root_layout.addWidget(
            QLabel("描述说明"), 3, 0, Qt.AlignmentFlag.AlignTop
        )
        root_layout.addWidget(self._description_edit, 3, 1, 1, 2)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        root_layout.addWidget(self._progress_bar, 4, 0, 1, 3)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self._static_button = QPushButton("静态分析")
        self._dynamic_button = QPushButton("动态分析")
        self._abort_button = QPushButton("中止运算")
        button_layout.addWidget(self._static_button)
        button_layout.addWidget(self._dynamic_button)
        button_layout.addWidget(self._abort_button)
        root_layout.addLayout(button_layout, 5, 0, 1, 3)

        self._static_button.clicked.connect(self._on_static_analysis)
        self._dynamic_button.clicked.connect(self._on_dynamic_analysis)
        self._abort_button.clicked.connect(self._on_abort)

    def _init_defaults(self) -> None:
        """设置控件默认值。"""
        self._case_name_edit.setText(self.DEFAULT_CASE_NAME)
        env_index = self._environment_combo.findText(
            self.DEFAULT_ENVIRONMENT,
        )
        if env_index >= 0:
            self._environment_combo.setCurrentIndex(env_index)
        mode_index = self._mode_combo.findText(self.DEFAULT_MODE)
        if mode_index >= 0:
            self._mode_combo.setCurrentIndex(mode_index)

    def form_data(self) -> ComputeTaskFormData:
        """读取当前表单数据。"""
        return ComputeTaskFormData(
            case_name=self._case_name_edit.text().strip(),
            environment=self._environment_combo.currentText(),
            mode=self._mode_combo.currentText(),
            description=self._description_edit.toPlainText().strip(),
        )

    def set_progress(self, value: int) -> None:
        """设置进度条数值。"""
        self._progress_bar.setValue(max(0, min(100, value)))

    def reset_progress(self) -> None:
        """重置进度条。"""
        self._progress_bar.setValue(0)

    def _on_static_analysis(self) -> None:
        """触发静态分析请求。"""
        self.static_analysis_requested.emit(self.form_data())

    def _on_dynamic_analysis(self) -> None:
        """触发动态分析请求。"""
        self.dynamic_analysis_requested.emit(self.form_data())

    def _on_abort(self) -> None:
        """触发中止运算请求。"""
        self.reset_progress()
        self.abort_requested.emit()
