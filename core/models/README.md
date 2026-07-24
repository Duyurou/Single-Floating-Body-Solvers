# core/models

数据模型。

主要文件：

- `project.py` — 公共工程文档；环境、浮体、水动力、工况等按稳定 ID 保存
- `node.py` — 工程树节点（对应 XML PACKET 的层级和来源信息）
- `resource.py` — 工程内文件资源引用
- `environment.py` — 环境编辑状态；每个环境具有独立 `environment_id`
- `case.py` — 计算工况；通过 `environment_id` 选择工程中的一份环境

一个工程可以包含多个环境对象：

```text
ProjectDocument.environments[environment_id] -> Environment
ComputeCase.environment_id                   -> 选择其中一个
ProjectNode.object_id                        -> 打开对应环境 Editor
```
