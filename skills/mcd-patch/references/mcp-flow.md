# MCP 接入与实际工具

官方服务：`https://mcp.mcd.cn`，Streamable HTTP，Authorization Bearer Token。
依据：[官方 MCP 使用指南](https://github.com/M-China/mcd-mcp-server)，核对日期 2026-10-24。

| 阶段 | 官方 Tool | 用途 |
| --- | --- | --- |
| 当前时间 | now-time-info | 确认当前日期与时段 |
| 到店选店 | query-nearby-stores | 根据用户提供的地标/位置查可用门店 |
| 外送选店 | delivery-query-addresses、delivery-query-stores | 选择用户已有地址和可配送门店 |
| 选品 | query-meals、query-meal-detail | 查询当前门店菜单、套餐构成及替换项 |
| 用券 | query-store-coupons | 仅查询当前账户在当前门店可用的券 |
| 营养查询（按需） | list-nutrition-foods | 获取官方营养信息，不能据此证明无过敏风险 |
| 核价 | calculate-price | 对完整购物车核算商品、优惠、费用及实付 |

不要凭 README 推测工具参数。`tools/list` 返回的 schema 才是当次调用的参数依据。分别处理 protocol error、`isError`、以及结果正文中的业务失败；不把 HTTP 200 等同业务成功。

本技能带有一个最小只读客户端 `scripts/mcp_readonly.py`。从技能目录执行：

```bash
python3 scripts/mcp_readonly.py list
python3 scripts/mcp_readonly.py call now-time-info --args '{}'
```

Token 从 `MCD_MCP_TOKEN` 环境变量或 `MCD_MCP_TOKEN_FILE` 指定的私有文件读取；项目内默认查找根目录 `.local/mcd_token`。不要在命令行参数、提交记录、截图或输出中包含 Token。返回值可能含私人位置、券 ID 等，只保存至忽略的 `.local/` 目录，公开演示前人工核查脱敏。

`call` 会先获取工具 schema，验证工具存在并检查必填字段；完整参数类型和业务约束以服务器校验为准。客户端只允许表中列出的工具，禁用自动重试；遇到 401 停止并更新凭证，429 按服务器提示稍后重试。网络失败不虚构数据。它支持 JSON/SSE 请求响应及 session ID，不实现旧版 HTTP+SSE、后台推送、断线续传、服务端采样或通用 MCP 客户端功能。
