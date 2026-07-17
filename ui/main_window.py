"""MOTC-时域模拟软件主窗口。"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QGroupBox,
    QMainWindow,
    QPlainTextEdit,
    QSplitter,
    QStyle,
    QTextEdit,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from app.bootstrap import get_project_root
from core.models.case import ComputeCaseRecord
from core.results.body_parser import BodyParserError, parse_output_disp
from ui.controllers.project_controller import ProjectController
from ui.controllers.run_controller import RunController
from ui.dialogs.compute_task_dialog import (
    ComputeTaskDialog,
    ComputeTaskFormData,
)
from ui.widgets.time_series_chart import DisplacementChartWidget


class MainWindow(QMainWindow):
    """主窗口：菜单栏、工具栏、管理窗口、图形窗口、日志与交互区。"""

    WINDOW_TITLE = "MOTC-时域模拟软件"
    DEFAULT_WIDTH = 1200
    DEFAULT_HEIGHT = 800
    LEFT_PANEL_WIDTH = 250
    BOTTOM_PANEL_HEIGHT = 200
    LOG_PRESET_TEXT = "等待打开工程文件..."

    def __init__(self) -> None:
        super().__init__()
        self._log_edit: QTextEdit | None = None
        self._interaction_edit: QPlainTextEdit | None = None
        self._management_tree: QTreeWidget | None = None
        self._compute_task_item: QTreeWidgetItem | None = None
        self._active_compute_dialog: ComputeTaskDialog | None = None
        self._displacement_chart: DisplacementChartWidget | None = None
        self._project_controller = ProjectController(
            self,
            get_project_root() / "workspace",
        )
        self._run_controller = RunController(self)
        self._init_window()
        self._init_menu_bar()
        self._init_tool_bar()
        self._init_central_graphics()
        self._init_left_dock()
        self._init_bottom_dock()
        self._init_status_bar()
        self._center_on_screen()

    def _init_window(self) -> None:
        """设置窗口标题、默认尺寸。"""
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

    def _init_menu_bar(self) -> None:
        """创建标准菜单栏。"""
        menu_names = [
            ("文件", ["新建", "打开", "保存", "退出"]),
            ("编辑", ["撤销", "重做", "剪切", "复制", "粘贴"]),
            ("导航", ["管理窗口", "图形窗口", "日志窗口"]),
            ("工具", ["选项", "插件管理"]),
            ("搜索", ["查找", "替换"]),
            ("帮助", ["用户手册", "关于"]),
        ]
        for title, actions in menu_names:
            menu = self.menuBar().addMenu(title)
            for action_text in actions:
                action = QAction(action_text, self)
                menu.addAction(action)
                if title == "文件" and action_text == "打开":
                    action.triggered.connect(self._on_open_project)
                if title == "文件" and action_text == "退出":
                    action.triggered.connect(self.close)

    def _init_tool_bar(self) -> None:
        """创建带占位图标的工具栏。"""
        tool_bar = QToolBar("主工具栏", self)
        tool_bar.setMovable(False)
        self.addToolBar(tool_bar)

        style = self.style()
        button_defs = [
            ("新建", QStyle.StandardPixmap.SP_FileIcon),
            ("打开", QStyle.StandardPixmap.SP_DialogOpenButton),
            ("保存", QStyle.StandardPixmap.SP_DialogSaveButton),
            ("剪切", QStyle.StandardPixmap.SP_DialogResetButton),
            ("复制", QStyle.StandardPixmap.SP_FileDialogDetailedView),
            ("粘贴", QStyle.StandardPixmap.SP_DialogApplyButton),
            ("删除", QStyle.StandardPixmap.SP_TrashIcon),
            ("撤销", QStyle.StandardPixmap.SP_ArrowBack),
            ("重做", QStyle.StandardPixmap.SP_ArrowForward),
            ("放大镜", QStyle.StandardPixmap.SP_FileDialogContentsView),
        ]
        for index, (tooltip, icon_enum) in enumerate(button_defs):
            action = QAction(
                style.standardIcon(icon_enum),
                tooltip,
                self,
            )
            action.setToolTip(tooltip)
            tool_bar.addAction(action)
            if tooltip == "打开":
                action.triggered.connect(self._on_open_project)
            if index in {2, 6, 8}:
                tool_bar.addSeparator()

    def _init_central_graphics(self) -> None:
        """中央图形窗口区域。"""
        chart = DisplacementChartWidget(self)
        self._displacement_chart = chart
        self.setCentralWidget(chart)

    def _init_left_dock(self) -> None:
        """左侧管理窗口停靠面板。"""
        dock = QDockWidget("管理窗口", self)
        dock.setObjectName("ManagementDock")
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )

        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.addTopLevelItem(self._build_management_tree())
        tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        self._management_tree = tree
        dock.setWidget(tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        dock.setMinimumWidth(self.LEFT_PANEL_WIDTH)

    def _build_management_tree(self) -> QTreeWidgetItem:
        """构建海工计算系统管理树。"""
        root = QTreeWidgetItem(["海工计算系统"])

        # 海工系统：环境与海域基础设定
        marine_system = QTreeWidgetItem(["海工系统"])
        env_setting = QTreeWidgetItem(["环境设置"])
        env_setting.addChild(QTreeWidgetItem(["环境数据"]))
        sea_area = QTreeWidgetItem(["海域设置"])
        sea_area.addChild(QTreeWidgetItem(["海面设置"]))
        sea_area.addChild(QTreeWidgetItem(["海底设置"]))
        marine_system.addChild(env_setting)
        marine_system.addChild(sea_area)

        # 水面平台系统：浮体与风电
        platform_system = QTreeWidgetItem(["水面平台系统"])
        platform_system.addChild(QTreeWidgetItem(["浮体"]))
        platform_system.addChild(QTreeWidgetItem(["风电系统"]))

        # 管缆系统：物理属性设置
        pipe_cable_system = QTreeWidgetItem(["管缆系统"])
        for name in ["端点设置", "截面设置", "线型设置", "管缆设置"]:
            pipe_cable_system.addChild(QTreeWidgetItem([name]))
        pipe_cable_system.addChild(QTreeWidgetItem(["其他参数设置"]))

        # 计算任务参数：计算工况
        task_params = QTreeWidgetItem(["计算任务参数"])
        task_params.addChild(QTreeWidgetItem(["静态计算"]))
        task_params.addChild(QTreeWidgetItem(["动态计算"]))
        task_params.addChild(QTreeWidgetItem(["其他参数"]))

        # 计算任务：流程终点操作节点
        compute_task = QTreeWidgetItem(["计算任务"])
        self._compute_task_item = compute_task

        for node in [
            marine_system,
            platform_system,
            pipe_cable_system,
            task_params,
            compute_task,
        ]:
            root.addChild(node)

        root.setExpanded(True)
        marine_system.setExpanded(True)
        env_setting.setExpanded(True)
        sea_area.setExpanded(True)
        platform_system.setExpanded(True)
        pipe_cable_system.setExpanded(True)
        task_params.setExpanded(True)
        compute_task.setExpanded(True)
        return root

    def _init_bottom_dock(self) -> None:
        """底部日志与交互停靠面板。"""
        dock = QDockWidget("日志与交互", self)
        dock.setObjectName("BottomDock")
        dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea
            | Qt.DockWidgetArea.TopDockWidgetArea
        )

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_log_panel())
        splitter.addWidget(self._create_interaction_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        dock.setWidget(splitter)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        dock.setMinimumHeight(self.BOTTOM_PANEL_HEIGHT)

    def _create_log_panel(self) -> QGroupBox:
        """构建日志窗口子面板。"""
        group = QGroupBox("日志窗口")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(4, 8, 4, 4)

        log_edit = QTextEdit()
        log_edit.setObjectName("LogTextEdit")
        log_edit.setReadOnly(True)
        log_edit.setPlainText(self.LOG_PRESET_TEXT)
        self._log_edit = log_edit
        layout.addWidget(log_edit)
        return group

    def _create_interaction_panel(self) -> QGroupBox:
        """构建交互窗口子面板。"""
        group = QGroupBox("交互窗口")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(4, 8, 4, 4)

        interaction_edit = QPlainTextEdit()
        interaction_edit.setObjectName("InteractionTextEdit")
        self._interaction_edit = interaction_edit
        layout.addWidget(interaction_edit)
        return group

    def _on_open_project(self) -> None:
        """打开 .sopro 工程并更新日志与交互窗口。"""
        success, log_text, interaction_text = (
            self._project_controller.open_project_dialog()
        )
        if not log_text:
            return
        self._append_log(log_text)
        if success and interaction_text and self._interaction_edit:
            self._interaction_edit.setPlainText(interaction_text)
            project = self._project_controller.loaded_project
            if project is not None:
                title = project.manifest.name or project.source_path.stem
                self.setWindowTitle(f"{self.WINDOW_TITLE} - {title}")
                self._run_controller.bind_project(project)
                self.statusBar().showMessage(
                    f"已打开工程: {project.source_path.name}",
                )
        elif not success:
            self._run_controller.bind_project(None)
            self.statusBar().showMessage("工程读入失败")

    def _append_log(self, text: str) -> None:
        """向日志窗口追加文本。"""
        if self._log_edit is None:
            return
        current = self._log_edit.toPlainText().strip()
        if current == self.LOG_PRESET_TEXT:
            current = ""
        if current:
            current += "\n"
        self._log_edit.setPlainText(current + text)

    def _on_tree_item_double_clicked(
        self,
        item: QTreeWidgetItem,
        column: int,
    ) -> None:
        """双击管理树节点时触发对应操作。"""
        del column
        if item.text(0) != "计算任务":
            return
        self._open_compute_task_dialog()

    def _open_compute_task_dialog(self) -> None:
        """打开计算任务对话框。"""
        dialog = ComputeTaskDialog(
            self,
            environment_options=self._environment_options(),
        )
        dialog.static_analysis_requested.connect(
            self._on_static_analysis_requested,
        )
        dialog.dynamic_analysis_requested.connect(
            self._on_dynamic_analysis_requested,
        )
        dialog.abort_requested.connect(self._on_abort_requested)
        self._active_compute_dialog = dialog
        dialog.exec()
        self._active_compute_dialog = None

    def _environment_options(self) -> list[str]:
        """获取环境下拉选项，默认至少包含环境数据。"""
        options = ["环境数据"]
        project = self._project_controller.loaded_project
        if project is None:
            return options
        if project.manifest.name and project.manifest.name not in options:
            return options
        return options

    def _add_case_branch(self, case_name: str) -> QTreeWidgetItem | None:
        """在计算任务节点下新建工况分支。"""
        if self._compute_task_item is None:
            return None
        name = case_name.strip() or ComputeTaskDialog.DEFAULT_CASE_NAME
        case_item = QTreeWidgetItem([name])
        self._compute_task_item.addChild(case_item)
        self._compute_task_item.setExpanded(True)
        if self._management_tree is not None:
            self._management_tree.setCurrentItem(case_item)
        return case_item

    def _start_analysis(
        self,
        form_data: ComputeTaskFormData,
        analysis_type: str,
    ) -> None:
        """启动静态或动态求解。"""
        case_item = self._add_case_branch(form_data.case_name)
        project = self._project_controller.loaded_project
        case = self._run_controller.start_analysis(
            form_data,
            analysis_type,
            project,
            on_progress=self._on_solver_progress,
            on_log=self._on_solver_log,
            on_success=self._on_solver_success,
            on_failure=self._on_solver_failure,
        )
        if case is None:
            return
        if case_item is not None:
            case_item.setData(0, Qt.ItemDataRole.UserRole, case.case_id)
        label = "静态" if analysis_type == "static" else "动态"
        self._append_log(
            f"[INFO] {label}分析任务已启动: {case.case_name}",
        )
        self.statusBar().showMessage(f"{label}分析运行中...")

    def _on_solver_progress(self, value: int) -> None:
        """更新对话框进度条。"""
        if self._active_compute_dialog is not None:
            self._active_compute_dialog.set_progress(value)

    def _on_solver_log(self, text: str) -> None:
        """追加求解日志。"""
        self._append_log(text)

    def _on_solver_success(self, case: ComputeCaseRecord) -> None:
        """求解成功后的界面更新。"""
        label = "静态" if case.analysis_type == "static" else "动态"
        self._append_log(
            "\n".join(
                [
                    f"[INFO] {label}分析完成: {case.case_name}",
                    f"[INFO] 工作目录: {case.work_dir}",
                    f"[INFO] INPUT: {case.input_dir}",
                    f"[INFO] OUTPUT: {case.output_dir}",
                ],
            ),
        )
        if self._interaction_edit is not None:
            self._interaction_edit.appendPlainText(
                f"\n=== {label}分析完成 ===\n"
                f"工况: {case.case_name}\n"
                f"OUTPUT/Body: {case.output_dir / 'Body'}\n"
                f"OUTPUT/Moorings: {case.output_dir / 'Moorings'}\n"
                f"OUTPUT/Risers: {case.output_dir / 'Risers'}\n"
                f"OUTPUT/Surface: {case.output_dir / 'Surface'}\n",
            )
        self._show_displacement_chart(case)
        self.statusBar().showMessage(f"{label}分析完成")

    def _show_displacement_chart(self, case: ComputeCaseRecord) -> None:
        """求解成功后展示浮体位移时程曲线。"""
        if self._displacement_chart is None:
            return
        disp_path = case.output_dir / "Body" / "output_disp.dat"
        if not disp_path.is_file():
            self._append_log(
                f"[WARN] 未找到位移时程文件: {disp_path}",
            )
            return
        try:
            series = parse_output_disp(disp_path)
        except BodyParserError as exc:
            self._append_log(f"[WARN] 位移曲线解析失败: {exc}")
            return
        chart_title = f"{case.case_name} - 浮体位移时程"
        self._displacement_chart.set_body_time_series(series, chart_title)
        self._append_log(
            f"[INFO] 已加载位移曲线: {series.point_count} 个时间点",
        )

    def _on_solver_failure(self, reason: str) -> None:
        """求解失败后的界面更新。"""
        self._append_log(f"[ERROR] 求解失败: {reason}")
        if self._active_compute_dialog is not None:
            self._active_compute_dialog.reset_progress()
        self.statusBar().showMessage("求解失败")

    def _on_static_analysis_requested(
        self,
        form_data: ComputeTaskFormData,
    ) -> None:
        """静态分析。"""
        self._start_analysis(form_data, "static")

    def _on_dynamic_analysis_requested(
        self,
        form_data: ComputeTaskFormData,
    ) -> None:
        """动态分析。"""
        self._start_analysis(form_data, "dynamic")

    def _on_abort_requested(self) -> None:
        """中止运算。"""
        aborted = self._run_controller.abort_running()
        if self._active_compute_dialog is not None:
            self._active_compute_dialog.reset_progress()
        if aborted:
            self._append_log("[WARN] 运算已中止")
            self.statusBar().showMessage("运算已中止")

    def _init_status_bar(self) -> None:
        """状态栏占位信息。"""
        self.statusBar().showMessage("就绪")

    def _center_on_screen(self) -> None:
        """将窗口居中显示。"""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())


def load_stylesheet(project_root: Path) -> str:
    """加载 QSS 样式文件内容。"""
    qss_path = project_root / "ui" / "styles" / "app.qss"
    return qss_path.read_text(encoding="utf-8")
