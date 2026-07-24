# ALL-00-01 本地 fixture

本目录只保存本地提取的、可追溯来源的 fixture。提取脚本是
`dev/extract_all_00_01_fixtures.py`，运行不会访问网络，也不会修改源 `.sopro`。

## 当前内容

- `projects/single-floater-ten-riser.sopro`：真实工程副本；用于 manifest、工程结构和历史 INPUT 盘点。
- `expected_project/`：ZIP 条目、manifest PACKET、Type 统计和资源哈希。
- `expected_input/historical_reference/`：从真实工程提取的历史 INPUT，仅作格式/兼容性参考。
- `catalog.json`：资产用途、限制和当前缺口。

历史 INPUT 不是模型生成的黄金 INPUT。当前工程的 OUTPUT 不完整，因此本目录不声明静态或动态结果已经通过工程验收。缺失资产见 `catalog.json` 的 `missing_for_full_m0`。
