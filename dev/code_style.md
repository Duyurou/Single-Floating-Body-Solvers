# 代码规范

本项目 Python 代码以 PEP8 为基础，并使用 black、isort、ruff 和 pytest
形成统一检查流程。

## 基本规则

- 缩进使用 4 个空格，不使用 Tab
- 行宽上限为 79
- 函数和变量使用 `snake_case`
- 类名使用 `PascalCase`
- 常量使用 `UPPER_CASE`
- import 顺序为标准库、第三方库、本地模块
- 新增逻辑优先写清楚函数边界，避免把业务逻辑塞进 UI 回调

## 工具分工

- black：统一 Python 格式
- isort：统一 import 排序
- ruff：检查常见错误和 PEP8 问题
- pytest：运行自动化测试
- pre-commit：提交前自动执行检查

配置集中在根目录 `pyproject.toml` 中。

## 什么时候需要写测试

以下改动必须优先补自动化测试：

- 修改数据模型
- 修改路径识别或文件查找逻辑
- 修改参数校验逻辑
- 修改文件生成、复制、写回逻辑
- 修改结果解析逻辑
- 修改 `.sopro`、XML、DAT 等文件解析逻辑
- 做跨模块集成并且可以稳定复现输入输出

以下改动可以以人工验证为主，但 PR 中必须写明验证步骤：

- UI 布局调整
- 文案调整
- 图标或样式调整
- 需要真实求解器环境才能完整验证的流程

## 本地检查命令

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\check_quality.ps1
```

## 自动修复命令

使用带修复模式的完整检查：

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\check_quality.ps1 -Fix
```

修复后要重新查看 Git diff，确认没有引入非预期变化。
