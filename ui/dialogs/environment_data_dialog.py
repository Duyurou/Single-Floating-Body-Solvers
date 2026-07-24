"""环境数据参数编辑对话框。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.models.environment import (
    EnvironmentCurrentRow,
    EnvironmentDataState,
    EnvironmentWaveRow,
    EnvironmentWindRow,
)
from core.sopro.environment_data import (
    CURRENT_OPTIONS,
    WIND_OPTIONS,
    WIND_WAVE_OPTIONS,
)


class EnvironmentDataDialog(QDialog):
    """环境数据编辑对话框。"""

    confirmed = Signal(EnvironmentDataState)

    WAVE_HEADERS = (
        "浪向(deg)",
        "相位(deg)",
        "周期(s)",
        "幅值(m)",
        "波浪源的X坐标",
        "波浪源的Y坐标",
        "波浪拉伸模型",
    )
    WIND_HEADERS = ("风向(deg)", "风速(m/s)", "参考高度(m)")
    CURRENT_HEADERS = ("水深(m)", "流速X(m/s)", "流速Y(m/s)")

    def __init__(
        self,
        parent: QWidget | None = None,
        initial_state: EnvironmentDataState | None = None,
    ) -> None:
        super().__init__(parent)
        self._state = initial_state or EnvironmentDataState()
        self._init_ui()
        self._load_state(self._state)

    def _init_ui(self) -> None:
        self.setWindowTitle("环境数据")
        self.setModal(True)
        self.resize(760, 620)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(10)

        self._name_edit = QLineEdit()
        self._description_edit = QPlainTextEdit()
        self._description_edit.setFixedHeight(90)

        root_layout.addWidget(self._create_label("名称："))
        root_layout.addWidget(self._name_edit)
        root_layout.addWidget(self._create_label("描述："))
        root_layout.addWidget(self._description_edit)

        self._wind_wave_combo = self._create_combo(WIND_WAVE_OPTIONS)
        self._wind_combo = self._create_combo(WIND_OPTIONS)
        self._current_combo = self._create_combo(CURRENT_OPTIONS)

        root_layout.addLayout(
            self._create_option_row("风浪：", self._wind_wave_combo),
        )
        root_layout.addLayout(
            self._create_option_row("风：", self._wind_combo),
        )
        root_layout.addLayout(
            self._create_option_row("海流：", self._current_combo),
        )

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._wave_table = self._create_table(self.WAVE_HEADERS)
        self._wind_table = self._create_table(self.WIND_HEADERS)
        self._current_table = self._create_table(self.CURRENT_HEADERS)
        self._tabs.addTab(self._wave_table, "风浪")
        self._tabs.addTab(self._wind_table, "风")
        self._tabs.addTab(self._current_table, "海流")
        root_layout.addWidget(self._tabs)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        confirm_button = QPushButton("确认")
        cancel_button = QPushButton("取消")
        confirm_button.clicked.connect(self._on_confirm)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        root_layout.addLayout(button_layout)

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        )
        return label

    def _create_combo(self, options: tuple[str, ...]) -> QComboBox:
        combo = QComboBox()
        combo.addItems(list(options))
        return combo

    def _create_option_row(
        self,
        label_text: str,
        combo: QComboBox,
    ) -> QHBoxLayout:
        layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(56)
        layout.addWidget(label)
        layout.addWidget(combo, 1)
        return layout

    def _create_table(self, headers: tuple[str, ...]) -> QTableWidget:
        table = QTableWidget(1, len(headers))
        table.setHorizontalHeaderLabels(list(headers))
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        for column in range(len(headers)):
            table.setItem(0, column, QTableWidgetItem("0"))
        return table

    def _load_state(self, state: EnvironmentDataState) -> None:
        self._name_edit.setText(state.name)
        self._description_edit.setPlainText(state.description)
        self._set_combo_index(self._wind_wave_combo, state.wind_wave_index)
        self._set_combo_index(self._wind_combo, state.wind_index)
        self._set_combo_index(self._current_combo, state.current_index)
        self._fill_wave_table(state.wave_rows)
        self._fill_wind_table(state.wind_rows)
        self._fill_current_table(state.current_rows)

    def _set_combo_index(self, combo: QComboBox, index: int) -> None:
        if 0 <= index < combo.count():
            combo.setCurrentIndex(index)

    def _fill_wave_table(self, rows: list[EnvironmentWaveRow]) -> None:
        row = rows[0] if rows else EnvironmentWaveRow()
        values = [
            row.heading,
            row.phase,
            row.period,
            row.amplitude,
            row.source_x,
            row.source_y,
            row.stretching_model,
        ]
        self._set_table_row(self._wave_table, values)

    def _fill_wind_table(self, rows: list[EnvironmentWindRow]) -> None:
        row = rows[0] if rows else EnvironmentWindRow()
        self._set_table_row(
            self._wind_table,
            [row.direction, row.speed, row.height],
        )

    def _fill_current_table(self, rows: list[EnvironmentCurrentRow]) -> None:
        self._current_table.setRowCount(max(len(rows), 1))
        if not rows:
            rows = [EnvironmentCurrentRow()]
        for row_index, row in enumerate(rows):
            values = [row.depth, row.speed_x, row.speed_y]
            for column, value in enumerate(values):
                self._current_table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem(value),
                )

    def _set_table_row(
        self,
        table: QTableWidget,
        values: list[str],
    ) -> None:
        for column, value in enumerate(values):
            table.setItem(0, column, QTableWidgetItem(value))

    def _read_table_row(self, table: QTableWidget, row: int) -> list[str]:
        values: list[str] = []
        for column in range(table.columnCount()):
            item = table.item(row, column)
            values.append(item.text().strip() if item else "0")
        return values

    def form_state(self) -> EnvironmentDataState:
        wave_values = self._read_table_row(self._wave_table, 0)
        wind_values = self._read_table_row(self._wind_table, 0)
        current_rows: list[EnvironmentCurrentRow] = []
        for row_index in range(self._current_table.rowCount()):
            values = self._read_table_row(self._current_table, row_index)
            if not any(values):
                continue
            current_rows.append(
                EnvironmentCurrentRow(
                    depth=values[0] or "0",
                    speed_x=values[1] or "0",
                    speed_y=values[2] or "0",
                ),
            )
        if not current_rows:
            current_rows = [EnvironmentCurrentRow()]

        return EnvironmentDataState(
            name=self._name_edit.text().strip() or "环境数据",
            environment_id=self._state.environment_id,
            description=self._description_edit.toPlainText().strip(),
            wind_wave_index=self._wind_wave_combo.currentIndex(),
            wind_index=self._wind_combo.currentIndex(),
            current_index=self._current_combo.currentIndex(),
            wave_rows=[
                EnvironmentWaveRow(
                    heading=wave_values[0] or "0",
                    phase=wave_values[1] or "0",
                    period=wave_values[2] or "0",
                    amplitude=wave_values[3] or "0",
                    source_x=wave_values[4] or "0",
                    source_y=wave_values[5] or "0",
                    stretching_model=wave_values[6] or "0",
                ),
            ],
            wind_rows=[
                EnvironmentWindRow(
                    direction=wind_values[0] or "0",
                    speed=wind_values[1] or "0",
                    height=wind_values[2] or "0",
                ),
            ],
            current_rows=current_rows,
            xml_path=self._state.xml_path,
        )

    def _on_confirm(self) -> None:
        state = self.form_state()
        self.confirmed.emit(state)
        self.accept()
