# 提交命名规范

项目提交信息参考 Conventional Commits。

## 格式

```text
<type>(<scope>): <中文描述>
```

`scope` 可以省略：

```text
<type>: <中文描述>
```

## 规则

- `type` 使用英文
- `scope` 使用英文模块名，例如 `ui`、`core`、`solver`
- `description` 使用中文
- `description` 末尾不加句号
- 分支名不使用中文
- 不强制绑定 Issue 编号
- 一次提交只表达一个相对完整的改动

## 常用 type

```text
feat      新功能
fix       修复问题
docs      文档修改
style     纯格式修改
refactor  重构
test      测试
chore     工程配置、依赖、脚本
ci        CI 配置
build     构建相关
```

## 示例

```text
feat(ui): 增加参数编辑面板
fix(validation): 修正输入文件校验逻辑
docs(workflow): 补充 Git 协作流程
test(core): 增加参数模型测试
chore(dev): 配置 pre-commit 检查
ci: 增加 GitHub Actions 检查流程
```

## 不推荐

```text
update
修改了一些东西
fix bug
feat: add ui.
```

这些写法要么范围不清楚，要么没有说明真实意图。
