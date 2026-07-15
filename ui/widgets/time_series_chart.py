"""时程曲线图表控件。"""

from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from core.results.body_parser import BodyTimeSeries

_DOF_SERIES = (
    ("surge", "纵荡", "#e74c3c"),
    ("sway", "横荡", "#3498db"),
    ("heave", "垂荡", "#2ecc71"),
    ("roll", "横摇", "#f39c12"),
    ("pitch", "纵摇", "#9b59b6"),
    ("yaw", "艏摇", "#1abc9c"),
)


class DisplacementChartWidget(QWidget):
    """浮体位移时程曲线展示控件。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._stack = QStackedWidget(self)
        self._placeholder = QLabel("图形窗口", self)
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_font = QFont("Microsoft YaHei", 18)
        self._placeholder.setFont(placeholder_font)
        self._placeholder.setStyleSheet("color: #888888;")

        self._chart = QChart()
        self._chart.legend().setVisible(True)
        self._chart.legend().setAlignment(
            Qt.AlignmentFlag.AlignBottom,
        )
        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._chart_view)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)
        self._stack.setCurrentWidget(self._placeholder)

    def show_placeholder(self, text: str = "图形窗口") -> None:
        """显示占位提示。"""
        self._placeholder.setText(text)
        self._stack.setCurrentWidget(self._placeholder)

    def set_body_time_series(
        self,
        series: BodyTimeSeries,
        title: str,
    ) -> None:
        """绘制浮体六自由度位移时程曲线。"""
        self._chart.removeAllSeries()
        axis_x = QValueAxis()
        axis_x.setTitleText("时间 (s)")
        axis_x.setLabelFormat("%.1f")

        axis_y = QValueAxis()
        axis_y.setTitleText("位移 / 转角")

        for field_name, label, color in _DOF_SERIES:
            values = getattr(series, field_name)
            line = QLineSeries()
            line.setName(label)
            line.setColor(QColor(color))
            points = [
                QPointF(series.time[index], values[index])
                for index in range(series.point_count)
            ]
            line.replace(points)
            self._chart.addSeries(line)
            line.attachAxis(axis_x)
            line.attachAxis(axis_y)

        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        self._chart.setTitle(title)
        self._stack.setCurrentWidget(self._chart_view)
