# core/sopro

`.sopro` 工程文件读写层（第一版重点）。

主要文件：

- `archive.py` — ZIP 打开/列举/读取条目
- `manifest.py` — 解析根目录 XML 工程清单
- `extractor.py` — 解压到 `workspace/` 临时目录
- `validator.py` — 检查必需节点与文件

`environment_data.py` 会枚举全部 `.4048` 环境文件。兼容函数
`find_environment_data_file()` 仍返回首个文件，但工程加载和新代码应使用
`find_environment_data_files()` / `load_environment_states()`，或把明确的
`environment_path` 传给 `load_environment_state()`，不能在多环境工程中静默取第一个。
