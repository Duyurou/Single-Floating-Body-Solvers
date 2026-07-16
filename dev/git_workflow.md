# Git 协作流程

## 分支类型

- `main`：稳定分支，只放已经确认可用的代码
- `dev`：开发集成分支，用于合并日常功能
- `feature/...`：新功能分支
- `fix/...`：问题修复分支
- `docs/...`：文档分支

分支名使用英文小写和短横线，例如：

```text
feature/result-chart
fix/config-parser
docs/development-guide
```

不要使用中文分支名，不强制添加 Issue 编号。

## 开发流程

1. 从 `dev` 拉出新分支
2. 一个分支只做一个任务
3. 修改前先确认任务目标和影响范围
4. 修改后运行本地检查
5. 推送分支并创建 PR
6. 至少一名组员 review 后再合并

## 提交前检查

```powershell
powershell -ExecutionPolicy Bypass -File .\dev\check_quality.ps1
```

如果已经安装 pre-commit，提交时会自动触发检查。检查失败时，提交会
被阻止。部分格式问题会被自动修复，修复后需要重新执行：

```powershell
git add <修改过的文件>
git commit
```

## PR 描述要求

PR 里必须写清楚：

- 改了什么
- 为什么这样改
- 怎么验证
- 影响哪些模块
- 还没做什么
- 需要别人重点看什么

项目已提供 `.github/pull_request_template.md` 作为 PR 模板。

## 合并前检查

合并前至少确认：

- 本地检查通过
- GitHub Actions 通过
- PR 描述完整
- review 意见已经处理
- 没有提交 `.venv`、缓存文件或临时工作区内容
