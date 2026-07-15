# Single Floater UI

单浮体求解器工作台项目骨架。当前仅包含目录结构，具体实现代码尚未生成。

## 目录说明

```text
project/
├── app/                    # 应用入口（main.py、bootstrap.py）
├── config/                 # 应用级配置（窗口、最近文件、求解器路径）
├── core/                   # 业务核心（与 UI 解耦）
│   ├── models/             # 数据模型（工程、树节点、计算参数）
│   ├── sopro/              # .sopro 读写（ZIP + XML 清单）
│   ├── solver/             # 求解器调用与 INPUT 生成
│   └── results/            # 结果解析与缓存
├── ui/                     # 界面层
│   ├── styles/             # 样式（QSS）
│   ├── widgets/            # 可复用控件（工程树、属性面板、占位视图）
│   ├── dialogs/            # 对话框（打开工程、关于）
│   └── controllers/        # UI 与 core 桥接
├── resources/              # 静态资源（图标、样例说明）
├── tests/                  # 单元测试
├── workspace/              # 运行时工作区（解压 .sopro、生成 INPUT）
└── vendor/                 # 第三方/求解器依赖（指向集成包 solver）
```

## 代码规范

`project/` 目录下所有 Python 代码**必须遵循 [PEP 8](https://peps.python.org/pep-0008/)**。

基本要求：

- 缩进 4 个空格，不使用 Tab
- 行宽不超过 79 字符（注释与文档字符串建议 72 字符）
- 导入顺序：标准库 → 第三方库 → 本地模块，组间空一行
- 顶层函数、类定义之间空两行；类内方法之间空一行
- 命名：`snake_case`（函数/变量）、`PascalCase`（类）、`UPPER_CASE`（常量）
- 使用有意义的名称，避免单字母变量（循环变量除外）

建议工具（后续可选）：

- `ruff` 或 `flake8` — 静态检查
- `black` — 自动格式化（行宽 79，与 PEP 8 一致）

## 开发顺序（建议）

1. `app/` + `ui/main_window.py`：主窗口框架
2. `core/sopro/`：打开并解析 `.sopro`
3. `ui/widgets/project_tree.py`：工程树展示
4. `core/solver/` + `core/results/`：求解与结果（后续）
5. 曲线 / 3D 视图（后续）

## 相关资源

- 求解器集成包：`../单浮体求解器集成包/`
- 样例工程：`../单浮体求解器集成包/reference/example-project/single-floater-ten-riser.sopro`
