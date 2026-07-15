"""MOTC-时域模拟软件入口。"""

import sys
from pathlib import Path

# 确保 project 根目录在导入路径中（支持直接运行本文件）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_root_str = str(_PROJECT_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow, load_stylesheet


def main() -> int:
    """启动主窗口应用。"""
    project_root = _PROJECT_ROOT
    app = QApplication(sys.argv)
    app.setApplicationName("MOTC-时域模拟软件")

    stylesheet = load_stylesheet(project_root)
    app.setStyleSheet(stylesheet)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
