# Single Floater UI

基于 PySide6 的单浮体时域求解器桌面工作台。项目正在从可运行原型演进为完整的工程建模、静态/动态计算和结果展示软件。

## 当前状态

当前原型已经具备：

- 打开并解压 `.sopro` 工程，读取清单和 INPUT 配置摘要；
- 枚举并编辑工程中的多份环境数据，按各自 `.4048` 路径保存；当前原型仍会把所编辑环境同步到首个历史 INPUT，正式 exporter 将按工况的 `environment_id` 生成 INPUT；
- 构建静态/动态工况目录，调用外部求解器并归档 OUTPUT；
- 在后台线程运行求解器，显示进度、日志和失败信息；
- 解析并显示浮体六自由度位移时程曲线；
- Black、isort、Ruff、pytest、pre-commit 和 GitHub Actions 质量配置；当前只运行本地检查。

完整目标尚未完成。`ProjectDocument`、真实工程树、模型驱动 INPUT exporter、完整保存往返、浮体/水动力/管缆建模、结果目录、系泊/立管结果和三维场景仍按项目任务文档推进。

正式并行功能开发前，团队先完成 M0 并行开发启动包：冻结共同基线、准备黄金样例、实现公共合同，并共同确认架构和任务边界。仓库内入口见 `dev/04-架构设计.md` 和 `dev/07-三人详细任务分配.md`。

## 本地开发约束（`LOCAL_ONLY`）

当前开发和多 Agent 演练只允许在本地进行。可以创建本地分支、本地 worktree 和本地 commit，可以运行已安装依赖支持的本地测试并生成本地报告；不得执行 `git push`、`git fetch`、`git pull`、`git clone`，不得创建或修改远程 GitHub Issue、Project、Pull Request、Actions、Release、Tag 或远程分支，也不得自动联网下载依赖。

如果某一步需要网络、依赖下载或任何远程操作，必须先停止并记录到团队约定的本地工作日志，等用户明确决定后再处理。默认情况下远程 GitHub 项目必须保持未触碰。

## 目录说明

```text
Single-Floating-Body-Solvers/
├── app/                    # 应用入口（main.py、bootstrap.py）
├── config/                 # 应用级配置（窗口、最近文件、求解器路径）
├── core/                   # 业务核心（与 UI 解耦）
│   ├── models/             # 工程、环境、工况等数据模型
│   ├── sopro/              # .sopro 解压、清单和环境数据读写
│   ├── solver/             # 工况 INPUT 准备、求解器调用和结果归档
│   └── results/            # 结果文件解析
├── ui/                     # 界面层
│   ├── styles/             # 样式（QSS）
│   ├── widgets/            # 可复用图表和视图控件
│   ├── dialogs/            # 环境数据和计算任务对话框
│   └── controllers/        # UI 与 core 桥接
├── resources/              # 静态资源（图标、样例说明）
├── tests/                  # 单元测试和 fixture
├── dev/                    # 环境配置、质量检查和协作说明
├── workspace/              # 运行时工作区（解压工程、工况 INPUT/OUTPUT）
└── vendor/                 # 第三方/求解器依赖（指向集成包 solver）
```

## 本地启动与检查

首次配置开发环境（注意：该脚本会调用 `pip install`；`LOCAL_ONLY` 模式下只有在依赖已存在于本机缓存且确认不会联网时才允许运行）：

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\setup_dev.ps1
```

启动应用：

```powershell
.\.venv\Scripts\python.exe -m app.main
```

运行格式、静态检查和测试：

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\check_quality.ps1
```

## 代码规范

项目中的 Python 代码必须遵循 [PEP 8](https://peps.python.org/pep-0008/) 和仓库现有工具配置。

基本要求：

- 缩进 4 个空格，不使用 Tab
- 行宽不超过 79 字符（注释与文档字符串建议 72 字符）
- 导入顺序：标准库 → 第三方库 → 本地模块，组间空一行
- 顶层函数、类定义之间空两行；类内方法之间空一行
- 命名：`snake_case`（函数/变量）、`PascalCase`（类）、`UPPER_CASE`（常量）
- 使用有意义的名称，避免单字母变量（循环变量除外）

质量工具：

- `black`：格式检查，行宽 79；
- `isort`：导入排序；
- `ruff`：静态检查；
- `pytest`：自动化测试；
- `pre-commit` 和 GitHub Actions：质量门禁配置；`LOCAL_ONLY` 模式只运行本地检查，不触发远程 Actions。

## 团队开发入口

开始任务前按以下顺序阅读：

1. `dev/04-架构设计.md`：项目分层、公共合同和调用方向；
2. `dev/07-三人详细任务分配.md`：负责人、依赖和任务边界；
3. `dev/development_guide.md`：本地开发环境和质量检查；
4. `dev/git_workflow.md`：分支、提交、评审和合并流程；
5. `tests/fixtures/golden/README.md`：已提取 fixture 的用途和限制。

正式功能任务必须从团队确认的共同 `dev` 基线创建分支。`M0-GATE` 未关闭前，只开展启动包范围内的基线、样例、合同、接线和验证工作。

## 相关资源

- 求解器集成包：`../单浮体求解器集成包/`
- 样例工程：`../单浮体求解器集成包/reference/example-project/single-floater-ten-riser.sopro`
