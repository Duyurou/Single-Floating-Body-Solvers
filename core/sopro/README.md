# core/sopro

`.sopro` 工程文件读写层（第一版重点）。

计划文件：

- `archive.py` — ZIP 打开/列举/读取条目
- `manifest.py` — 解析根目录 XML 工程清单
- `extractor.py` — 解压到 `workspace/` 临时目录
- `validator.py` — 检查必需节点与文件
