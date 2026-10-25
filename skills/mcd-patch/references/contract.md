# 本地诊断输入约定 v1

本地 Python 诊断器接收完整购物车候选，由宿主智能体从真实 MCP 结果映射。它不代替参数发现、菜单检索、套餐展开或条件语义检查。字段映射必须保留证据，不能猜测价格单位或把省略字段补成零。

参考 `../examples/demo.json`。根对象：

- `schema_version`: 1。
- `mode`: `demo` 或 `live`；demo 必须显式加 `--demo`，不能生成真实接入证据。
- `context`: `store_id`、`dining_mode`、`currency`（CNY）。预约场景还须包含 `reservation_time`（带时区 ISO 8601）；即时场景可省略。所有候选必须与其完整一致。
- `budget_cents`: 非负整数，包含必需费用的总预算。
- `constraints`: 条件数组，含唯一 `id`、`label`、布尔 `relaxable`。缺少用户变通授权时为 false。
- `candidates`: 完整购物车候选数组，含唯一 `id`、`label`、`allocation`（每人餐品分配文本）、`context`、`quote` 和 `checks`。
- `quote`: `total_cents`（非负整数）、`source`（calculate-price）、`observed_at`（带时区 ISO 8601）、`evidence`（该次响应的本地引用或调用 ID）。包含当前币种全部必需费用；任何费用不明时不构建有效 quote。
- `checks`: 每个条件 ID 映射 `{status: pass|fail|unknown, evidence: 非空文字}`。不认识的额外条件 ID 视为数据错误；缺失的检查视为 unknown。

所有候选都须说明每个人拿到什么；这不能靠总件数推断。对共享餐品，记录用户同意的分配。检查证据可以是菜单/套餐详情、用户明确偏好，以及引用的真实工具响应。`live` 是调用者声明的数据来源模式，不是数字签名；诊断器检查格式和新鲜度，不能独立证明数据确来自服务器。

默认 300 秒是本项目的报价新鲜度策略，**不是官方锁价承诺**；切换门店、就餐方式、商品、券或数量后必须重新核价。时间超过当前时间 30 秒也拒绝接受。

结果状态：`feasible`、`needs_change`、`insufficient_data`、`no_candidate`。unknown、不可调整条件失败、失效报价均不会生成修改建议；需要更多数据或新候选。`patches` 使用集合包含关系与预算差额作 Pareto 比较，不把两个不同偏好视为等价，保留同等修改下更便宜的代表候选。
