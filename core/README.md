# core

业务核心层，与 UI 解耦。

## 子模块

| 目录 | 职责 |
|------|------|
| `models/` | 工程元信息、树节点、计算参数数据模型 |
| `sopro/` | `.sopro` ZIP 打开、XML 清单解析、解压缓存 |
| `solver/` | 调用 `hydrodyn_newversion.exe`、生成 INPUT |
| `results/` | 解析 `bodyout/*.dat` 等结果文件 |
