# 开发协作配置说明

这个目录集中放项目工程化文档和本地开发脚本。项目主
`README.md` 保持不变，运行依赖继续使用根目录已有的
`requirements.txt`。

## 快速开始

在 Windows PowerShell 中进入项目根目录：

```powershell
cd C:\Users\lenovo\Desktop\SFBS\Single-Floating-Body-Solvers
powershell -ExecutionPolicy Bypass -File .\dev\setup_dev.ps1
```

脚本会在项目内创建 `.venv`，安装 `requirements.txt` 中的运行依赖，
再安装开发检查工具，并启用 pre-commit。

## 常用命令

启动应用：

```powershell
.\.venv\Scripts\python.exe -m app.main
```

运行本地质量检查：

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\check_quality.ps1
```

自动修复可修复的问题，并运行测试：

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\check_quality.ps1 -Fix
```

只运行测试：

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## 文档索引

- `development_guide.md`：开发环境、启动和检查流程
- `code_style.md`：代码规范和测试要求
- `commit_convention.md`：提交命名规范
- `git_workflow.md`：分支和 PR 协作流程

## 配置文件位置

有些配置必须放在工具约定的位置：

- `pyproject.toml`：black、isort、ruff、pytest 会自动读取
- `.pre-commit-config.yaml`：pre-commit 默认从项目根目录读取
- `.github/workflows/ci.yml`：GitHub Actions 必须放在这里
- `.github/pull_request_template.md`：GitHub PR 模板必须放在这里
