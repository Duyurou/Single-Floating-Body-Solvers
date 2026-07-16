# 开发说明

本文档说明如何准备本地环境、启动项目、
运行检查和测试。

## 环境原则

项目使用项目内 `.venv`，不要求修改全局 Python 环境。这样做可以避免
不同项目之间的依赖互相污染，也方便随时重建环境。

运行依赖继续使用根目录已有的 `requirements.txt`。开发工具由
`dev/setup_dev.ps1` 安装到 `.venv`，包括 black、isort、ruff、pytest
和 pre-commit。

## 第一次配置

```powershell
cd C:\Users\lenovo\Desktop\SFBS\Single-Floating-Body-Solvers
powershell -ExecutionPolicy Bypass -File .\dev\setup_dev.ps1
```

执行完成后，项目根目录会出现 `.venv`。这个目录已经被 `.gitignore`
忽略，不要提交。

## 启动项目

```powershell
.\.venv\Scripts\python.exe -m app.main
```

如果尚未创建 `.venv`，请先运行 `dev/setup_dev.ps1`。

## 运行质量检查

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\check_quality.ps1
```

这个脚本会依次执行：

- `black --check`：检查代码格式
- `isort --check-only`：检查 import 顺序
- `ruff check`：执行静态检查
- `pytest`：运行测试

如果希望自动修复能修复的问题，可以运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\check_quality.ps1 -Fix
```

`-Fix` 会先执行 black、isort 和 `ruff check --fix`，然后再运行 pytest。
如果修复了文件，需要重新查看差异并执行 `git add`。

## 目录职责

- `app/`：应用入口和启动逻辑
- `core/`：业务核心，尽量不依赖 UI
- `ui/`：PySide6 界面、控件、控制器和样式
- `resources/`：图标、样例等静态资源
- `tests/`：pytest 测试
- `dev/`：开发流程文档和本地脚本

## pytest 和 tests 的关系

pytest 会自动发现 `tests/` 目录下命名为 `test_*.py` 的测试文件。
新增核心逻辑时，优先在 `tests/unit/` 中补单元测试。

## pre-commit 和 GitHub Actions

pre-commit 是本地提交前检查。安装 hook 后，在 VSCode 或命令行提交时
都会触发。如果检查失败，提交会被阻止。

GitHub Actions 是远程检查，在 push 或 PR 后运行。它不能替代本地检查，
但可以保证进入仓库的代码在统一环境中再跑一遍。
