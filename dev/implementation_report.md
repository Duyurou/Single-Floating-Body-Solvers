# MOTC 时域模拟软件 — 核心功能实现说明

> 本文档用于汇报 **求解器集成**、**参数修改**、**结果展示** 三部分的实现思路与代码结构。

---

## 1. 总体架构

项目采用 **UI 与业务核心分离** 的分层设计：界面层（`ui/`）负责交互，业务层（`core/`）负责工程读写、参数编辑与求解调用，二者通过 Controller 桥接。

```text
┌─────────────────────────────────────────────────────────────┐
│  ui/  界面层                                                 │
│  ├── main_window.py          主窗口、树形导航、结果展示入口    │
│  ├── dialogs/                参数编辑对话框                   │
│  ├── controllers/            工程控制、求解控制                 │
│  └── workers/                后台求解线程                       │
├─────────────────────────────────────────────────────────────┤
│  core/  业务核心（不依赖 Qt 控件）                            │
│  ├── sopro/                  .sopro 工程读写                   │
│  ├── solver/                 求解器 INPUT 构建与进程调用        │
│  └── results/                求解结果解析                       │
├─────────────────────────────────────────────────────────────┤
│  外部依赖                                                    │
│  ├── 单浮体求解器集成包/solver/   hydrodyn_newversion.exe     │
│  └── workspace/              工程解压目录、工况工作目录          │
└─────────────────────────────────────────────────────────────┘
```

**设计原则：**

- 打开 `.sopro` 后解压到 `workspace/`，在解压目录上读写参数，不直接修改原始压缩包。
- 每次计算在 `workspace/cases/` 下创建独立工况目录（`INPUT/` + `OUTPUT/`），与工程源数据隔离。
- 求解在 `QThread` 后台执行，避免阻塞主界面。

---

## 2. 求解器集成

### 2.1 集成目标

将原 **hydrodyn_newversion.exe** 单浮体时域求解器嵌入 PySide6 桌面应用，实现：

1. 从 `.sopro` 工程自动生成求解 INPUT；
2. 支持 **静态分析** 与 **动态分析** 两种模式；
3. 调用求解器并归档输出到 OUTPUT 目录。

### 2.2 求解器路径与定位

求解器位于工程外部的集成包中，由 `app/bootstrap.py` 统一解析：

```python
def get_solver_root() -> Path:
    return get_project_root().parent / "单浮体求解器集成包" / "solver"
```

可执行文件路径：`solver/hydroMod/hydrodyn_newversion.exe`。

### 2.3 调用流程

```text
用户双击「计算任务」→ 填写工况 → 点击「静态/动态分析」
        │
        ▼
RunController.start_analysis()
  · 校验工程已打开、单浮体模式、无并发任务
  · create_case_record() 创建 workspace/cases/{工况名}_{类型}_{时间戳}/
        │
        ▼
SolverWorker (QThread 后台线程)
  ├─ 10%  prepare_static_input / prepare_dynamic_input
  ├─ 30%  SolverRunner.run()
  ├─ 80%  archive_solver_output()
  └─ 100% 通知 UI 成功/失败
```

### 2.4 INPUT 目录构建（`core/solver/input_builder.py`）

#### 静态分析

1. 从工程 `INPUT/` 目录 **完整复制** 到工况 `INPUT/`；
2. 重建求解器要求的子目录：`bodyout/`、`output/`、`res/`、`surface/`；
3. 调用 `apply_static_config()` 将 `config.dat` 设为静态参数（`sta_Type=0` 等）；
4. 将 `config.dat` 同步到 `bodyout/config.dat`。

#### 动态分析

动态分析 **依赖已成功的静态工况**，流程更复杂：

1. 从静态工况 INPUT 复制基础文件（含 `Environment_in.dat`、WAMIT 文件、系泊文件等）；
2. 从静态 OUTPUT 复制中间结果：
   - `OUTPUT/Risers/` → `INPUT/res/`（立管结果）
   - `OUTPUT/Moorings/` → `INPUT/output/`（系泊初值）
   - `OUTPUT/Body/static_result.dat` → `INPUT/bodyout/`
3. 调用 `apply_dynamic_config()` 设置动态参数（`sta_Type=1`、`cal_time=500s` 等）；
4. 调用 `patch_mooringline_for_dynamic()` 修改系泊输入文件第 6 行。

### 2.5 求解器进程调用（`core/solver/runner.py`）

`SolverRunner` 封装了与原软件兼容的调用约定：

| 步骤 | 实现要点 |
|------|----------|
| 环境准备 | 将 `hydroMod/`、`Fortran/` 加入 `PATH` |
| 命令行 | `hydrodyn_newversion.exe {INPUT目录}\`（Windows 需末尾反斜杠） |
| 工作目录 | 设为 `solver/` 根目录 |
| 错误检测 | 解析 stdout/stderr 中的 `HandProcess:failures:` |
| 结果校验 | 静态检查 `bodyout/static_result.dat`；动态检查 `bodyout/output_disp.dat` 等 |

### 2.6 结果归档（`core/solver/result_archiver.py`）

求解器将结果写入 INPUT 下的子目录，归档模块将其复制到 OUTPUT 的标准结构：

| INPUT 子目录 | OUTPUT 子目录 | 内容 |
|-------------|--------------|------|
| `bodyout/`  | `Body/`      | 浮体位移、力时程 |
| `output/`   | `Moorings/`  | 系泊线结果 |
| `res/`      | `Risers/`    | 立管结果 |
| `surface/`  | `Surface/`   | 海面结果 |

### 2.7 UI 侧集成（`ui/controllers/run_controller.py` + `ui/workers/solver_worker.py`）

- **RunController**：负责工况创建、线程生命周期、静态/动态前置校验；
- **SolverWorker**：在后台线程串联 INPUT 准备 → 求解 → 归档，通过 Qt Signal 回传进度与日志；
- **MainWindow**：接收信号，更新进度条、日志窗口、交互窗口和图形窗口。

---

## 3. 参数修改

### 3.1 功能目标

在左侧管理树中，双击 **「环境数据」** 叶子节点，弹出参数编辑对话框，支持：

- 名称、描述编辑；
- 风浪 / 风 / 海流 类型下拉选择；
- 标签页切换查看风浪、风、海流参数表格；
- 点击「确认」将修改写回工程文件。

> 该模式为后续其他叶子节点（浮体、管缆、计算参数等）的参数编辑提供了可复用框架。

### 3.2 交互入口

`ui/main_window.py` 中监听树节点双击：

```text
双击「环境数据」 → ProjectController.load_environment_data()
                → EnvironmentDataDialog 显示
                → 用户确认 → ProjectController.save_environment_data()
                → 刷新交互窗口摘要
```

### 3.3 数据模型（`core/models/environment.py`）

用 dataclass 描述对话框状态，与 UI 控件解耦：

- `EnvironmentDataState`：名称、描述、三个下拉索引、三组表格行；
- `EnvironmentWaveRow`：浪向、相位、周期、幅值、波源坐标、拉伸模型；
- `EnvironmentWindRow`：风向、风速、参考高度；
- `EnvironmentCurrentRow`：水深、流速 X/Y。

### 3.4 对话框实现（`ui/dialogs/environment_data_dialog.py`）

- 布局：单列垂直 `QVBoxLayout`，符合表单风格；
- 控件：`QLineEdit`（名称）、`QPlainTextEdit`（描述）、`QComboBox`（三类环境选项）、`QTabWidget` + `QTableWidget`（三组参数表）；
- 数据流：对话框只负责展示与收集 `EnvironmentDataState`，读写文件由 core 层完成。

### 3.5 文件读写（`core/sopro/environment_data.py`）

环境参数分散在两类文件中，读写模块统一封装：

#### 文件 A：`环境数据.4048`（XML，UI 元数据）

- 位置：`.sopro` 解压目录下的 `{UUID}/环境数据.4048`；
- 格式：`RootElement` 下多个 `Element_N`，每个含 `AttributeName` / `AttributeInfo`；
- 关键字段：

| 字段 | 含义 |
|------|------|
| `surgeIndex` | 风浪类型下拉索引（0=无风浪, 1=规则波, …） |
| `windIndex` | 风类型索引 |
| `oceanIndex` | 海流类型索引 |
| `wave_data_w0_wavedir` 等 | 各波浪类型的参数值 |

#### 文件 B：`INPUT/Environment_in.dat`（求解器输入）

- 标签-数值对格式，如「水深(m)」「波浪类型」「波浪参数」等；
- 「波浪参数」行格式：`幅值, 周期, 浪向, 相位`；
- 「海流剖面定义」段：个数 + 多行 `水深, 流速X, 流速Y`。

#### 文件 C：`INPUT/config.dat`（求解配置，保存时同步）

- 保存时同步更新 `waveHeading`、`wavePer`、`waveAmp`、`waveType` 等键值。

#### 读取策略

```text
1. 从 环境数据.4048 读取 UI 状态和表格初值
2. 从 Environment_in.dat 补充/覆盖波浪参数、海流剖面（以求解器输入为准）
3. 合并为 EnvironmentDataState 供对话框显示
```

#### 保存策略

```text
1. 写回 环境数据.4048 全部 UI 字段
2. 更新 Environment_in.dat 的波浪类型、波浪参数、海流剖面
3. 同步 config.dat 中相关键值
4. 刷新 ProjectController 中的 INPUT 摘要
```

### 3.6 与求解器的衔接

参数修改直接作用于工程解压目录中的 `INPUT/`，下次启动静态/动态分析时，`prepare_static_input()` 会将更新后的 INPUT **复制** 到工况目录，因此修改后的环境参数会进入求解流程。

---

## 4. 结果展示

### 4.1 展示内容

当前已实现 **动态分析完成后** 的浮体六自由度位移时程曲线展示：

- 纵荡（Surge）、横荡（Sway）、垂荡（Heave）
- 横摇（Roll）、纵摇（Pitch）、艏摇（Yaw）

静态分析完成后，在日志和交互窗口展示 OUTPUT 路径信息；动态分析 additionally 驱动中央图形窗口绘制曲线。

### 4.2 结果解析（`core/results/body_parser.py`）

解析 `OUTPUT/Body/output_disp.dat`：

- 每行 7 列：`时间, surge, sway, heave, roll, pitch, yaw`；
- 解析为不可变 dataclass `BodyTimeSeries`，供图表控件消费；
- 含格式校验（文件存在、列数、数值合法性）。

### 4.3 图表控件（`ui/widgets/time_series_chart.py`）

`DisplacementChartWidget` 基于 **PySide6 QtCharts** 实现：

- 默认显示「图形窗口」占位文字；
- 收到 `BodyTimeSeries` 后，为每个自由度创建 `QLineSeries`；
- 六条曲线共用时间轴，不同颜色区分，底部图例标注中文名称；
- 通过 `QStackedWidget` 在占位页与图表页之间切换。

### 4.4 展示触发流程

```text
SolverWorker 求解成功
        │
        ▼
MainWindow._on_solver_success()
  · 日志窗口：工况路径、INPUT/OUTPUT 目录
  · 交互窗口：Body/Moorings/Risers/Surface 子目录
        │
        ▼ (动态分析)
MainWindow._show_displacement_chart()
  · 定位 OUTPUT/Body/output_disp.dat
  · parse_output_disp() → BodyTimeSeries
  · DisplacementChartWidget.set_body_time_series()
  · 中央图形窗口显示六自由度时程曲线
```

### 4.5 结果目录结构（供后续扩展）

每次求解完成后，OUTPUT 目录按模块分类，便于扩展更多结果视图：

```text
OUTPUT/
├── Body/       ← 当前已展示：output_disp.dat
├── Moorings/   ← 待扩展：系泊力曲线
├── Risers/     ← 待扩展：立管响应
└── Surface/    ← 待扩展：海面高程
```

---

## 5. 端到端数据流（汇总）

```text
                    ┌──────────────┐
                    │  .sopro 工程  │
                    └──────┬───────┘
                           │ 打开/解压
                           ▼
                    ┌──────────────┐
         ┌─────────│ workspace/    │─────────┐
         │         │ 解压目录       │         │
         │         └──────────────┘         │
         │ 双击编辑                          │ 启动计算
         ▼                                    ▼
  ┌──────────────┐                    ┌──────────────┐
  │ 环境数据.4048 │                    │ cases/工况/   │
  │ Environment  │ ────复制 INPUT───▶│ INPUT/       │
  │ config.dat   │                    └──────┬───────┘
  └──────────────┘                           │ 调用 exe
                                             ▼
                                      ┌──────────────┐
                                      │ solver/       │
                                      │ hydrodyn.exe  │
                                      └──────┬───────┘
                                             │ 归档
                                             ▼
                                      ┌──────────────┐
                                      │ OUTPUT/       │
                                      │ Body/...      │──▶ 曲线展示
                                      └──────────────┘
```

---

## 6. 关键模块索引

| 模块 | 路径 | 职责 |
|------|------|------|
| 求解器路径 | `app/bootstrap.py` | 定位 solver 根目录、工况目录 |
| 工程加载 | `core/sopro/loader.py` | 解压 .sopro、汇总 INPUT |
| INPUT 构建 | `core/solver/input_builder.py` | 静态/动态 INPUT 准备 |
| 配置编辑 | `core/solver/config_editor.py` | config.dat 键值替换 |
| 求解调用 | `core/solver/runner.py` | 进程启动、错误检测 |
| 结果归档 | `core/solver/result_archiver.py` | INPUT → OUTPUT 复制 |
| 环境参数 | `core/sopro/environment_data.py` | 环境数据读写 |
| 结果解析 | `core/results/body_parser.py` | 位移时程解析 |
| 求解控制 | `ui/controllers/run_controller.py` | 工况管理与线程调度 |
| 工程控制 | `ui/controllers/project_controller.py` | 打开工程、环境数据存取 |
| 后台求解 | `ui/workers/solver_worker.py` | 后台执行完整求解流程 |
| 环境对话框 | `ui/dialogs/environment_data_dialog.py` | 环境参数 UI |
| 计算对话框 | `ui/dialogs/compute_task_dialog.py` | 计算任务 UI |
| 曲线控件 | `ui/widgets/time_series_chart.py` | 六自由度时程图 |
| 主窗口 | `ui/main_window.py` | 整体布局与事件编排 |

---

## 7. 当前进展与后续计划

### 已完成

- [x] `.sopro` 工程打开、解压与 INPUT 配置摘要展示
- [x] 静态/动态求解器调用全流程（INPUT 构建 → exe 调用 → OUTPUT 归档）
- [x] 后台线程求解，进度条与日志实时反馈
- [x] 「环境数据」参数双击编辑（读/写 XML + Environment_in.dat + config.dat）
- [x] 动态分析浮体六自由度位移时程曲线展示

### 待扩展

- [ ] 管理树其他叶子节点的参数编辑（浮体、管缆、计算参数等）
- [ ] 静态分析结果可视化
- [ ] 系泊力、立管响应等其他 OUTPUT 模块的曲线/3D 展示
- [ ] 参数修改后回写 `.sopro` 压缩包（当前仅写解压目录）
- [ ] 多浮体模式支持

---

## 8. 验证方式

```powershell
# 启动应用
.\.venv\Scripts\python.exe -m app.main

# 单元测试
.\.venv\Scripts\python.exe -m pytest tests/unit/ -v
```

**建议演示步骤：**

1. 打开样例工程 `single-floater-ten-riser.sopro`；
2. 双击「环境数据」，查看/修改风浪参数，点击确认；
3. 双击「计算任务」，先运行静态分析，再运行动态分析；
4. 动态分析完成后，查看中央图形窗口的六自由度位移曲线及日志/交互窗口的输出路径信息。
