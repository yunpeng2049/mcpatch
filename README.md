# McPatch · 麦麦需求编译器

**把「两个人都想吃好，预算又不能超」编译成可核价的方案；遇到冲突，给需求打一张最小补丁。**

面向程序员、同事和朋友的麦当劳多人点餐 Skill。它把自然语言需求拆成条件，使用麦当劳中国 MCP 查询门店、菜单、套餐及优惠券，对完整购物车核价，再用确定性程序找出可行候选或最小修改建议。

> 当前状态：2026-10-25 已完成真实 MCP 工具发现、选店、菜单、套餐详情、门店券查询及四个完整购物车核价，并将真实结果送入诊断器。18 项自动化测试通过。[查看脱敏实测记录](docs/LIVE_VERIFICATION.md)。非麦当劳官方产品。

**已成功参赛**：[官方报名 Issue #1337](https://github.com/M-China/mcd-developer-innovation-challenge/issues/1337)，官方账号 `M-China-Official` 于 2026-10-25 09:59（北京时间）[回复确认](https://github.com/M-China/mcd-developer-innovation-challenge/issues/1337#issuecomment-6392210436)。详见[报名记录](docs/REGISTRATION.md)。

## 一个有用的区别

普通推荐容易在超预算时悄悄删掉某个人的饮料。McPatch 保留每个人的条件，回答三个问题：

1. 哪些已经核价的组合满足所有需求？
2. 哪个条件造成冲突，哪里还缺证据？
3. 如果允许调整，最少需要改哪些条件，或增加多少预算？

不把「便宜」等同于「符合需求」，不把信息未知等同于满足条件。

```mermaid
flowchart LR
  A[大家的点餐需求] --> B[人数 / 预算 / 每人条件]
  B --> C[麦当劳 MCP：选店 / 菜单 / 套餐 / 券]
  C --> D[完整购物车官方核价]
  D --> E[条件检查 + 最小修改诊断]
  E --> F[可行方案或最小补丁]
  F --> G[用户选择后重新核价]
```

## 目标用户与适用场景

- 两到几位同事、朋友一起点餐，需要照顾每个人的需求。
- 有明确预算，想知道差多少钱，以及能否调整配餐。
- 希望了解推荐依据，而非得到无法核价的套餐名称。

首版不承诺穷举全菜单最优，不提供配送到达时间预测，不推断过敏安全，不自动下单或代付。

## 30 秒离线体验

依赖 Python 3.10+，核心脚本只用标准库。

```bash
python3 skills/mcd-patch/scripts/diagnose.py --demo skills/mcd-patch/examples/demo.json
python3 -m unittest discover -s tests -v
```

演示需求：预算 40 元，甲乙各一份主食、各一杯饮料、共享一份小食。主食不可调整，饮料和共享小食允许提出修改建议。

| 虚构候选 | 虚构总价 | 诊断 |
| --- | ---: | --- |
| A：保留全部需求 | ¥46 | 保留需求，预算需增加 ¥6 |
| B：去掉共享小食 | ¥39 | 修改一个条件，仍在预算内 |
| C：不配两杯饮料 | ¥41 | 修改另一个条件，预算需增加 ¥1 |
| D：去掉饮料及小食 | ¥36 | 被 B 支配：B 已在预算内且少改一个条件 |
| E：套餐组成未知 | ¥38 | 信息不足，不能作为满足需求的候选 |

A、B、C 代表不同取舍；程序不会替用户假定哪个人的偏好更不重要。这里“最小”指条件删除集合与额外预算的 Pareto 最小，不是总价最低。

## 真实 MCP 实测

2026-10-25 09:14（北京时间），使用上海人民广场附近的公共门店，以当天 12:00 到店自取为测试场景：

| 候选 | 官方返回总价 | 40 元预算下的诊断 |
| --- | ---: | --- |
| 两份人气经典随心配 + 中薯条 | ¥43.30 | 保留全部需求，预算增加 ¥3.30 |
| 两份人气经典随心配 | ¥29.80 | 仅去掉共享薯条 |
| 两份麦香鸡 + 中薯条 | ¥47.50 | 被第一项支配，不推荐为最小修改 |
| 两份麦香鸡 | ¥34.00 | 被第二项支配，不推荐为最小修改 |

随心配使用当次详情接口返回的默认组合：双层吉士汉堡 + 可乐麦炫酷。每人一套，主食要求完整保留。以上是一次实测快照，价格与供应会变化；没有创建订单或支付。

可离线回放这次脱敏的真实历史结果：

```bash
python3 skills/mcd-patch/scripts/diagnose.py --demo skills/mcd-patch/examples/live-replay.json
```

这里显式使用 demo 模式固定历史时间，不能当作当前报价。原始虚构演示仍为 `examples/demo.json`。

## 安装 Skill

将 `skills/mcd-patch` 整个目录导入支持 `SKILL.md` 的智能体客户端。对于从 `~/.codex/skills` 发现技能的环境，可复制为 `~/.codex/skills/mcd-patch`。在支持显式技能调用的宿主中使用 `$mcd-patch`；其他宿主按其技能安装方式加载 `SKILL.md`。只复制入口文件会丢失诊断脚本与参考资料。

示例需求：

> 使用 mcd-patch。我们两人外带，预算 40 元，在我指定的麦当劳门店。两人各一份主食、各一杯饮料，再要一份共享小食。主食必须保留，饮料和小食可以提调整建议。先比较方案，不下单。

## 接入真实麦当劳 MCP

1. 在 [麦当劳 MCP 开放平台](https://open.mcd.cn/mcp) 登录，按官方流程激活 Token。
2. 在本地运行 `python3 scripts/setup_token.py`，以隐藏输入保存到 `.local/mcd_token`；也可以通过宿主的凭证管理设置环境变量 `MCD_MCP_TOKEN`。
3. 参考 `mcp-config.example.json` 配置宿主。该文件仅使用环境变量占位符；不同宿主的类型名称与变量展开语法可能不同，导入后需确认是否支持，不能把字面 `${MCD_MCP_TOKEN}` 当成真实凭证发送。
4. 运行下列命令获取真实工具 schema 并进行只读验证：

```bash
python3 skills/mcd-patch/scripts/mcp_readonly.py list
python3 skills/mcd-patch/scripts/mcp_readonly.py call now-time-info --args '{}'
```

进一步查询菜单或核价时，由智能体依据当前 schema 构造参数。包含位置、门店或账户字段的参数文件及原始响应只留在 `.local/`。例如：

```bash
python3 skills/mcd-patch/scripts/mcp_readonly.py call calculate-price --args-file .local/cart-args.json
python3 skills/mcd-patch/scripts/diagnose.py .local/quoted-candidates.json
```

第二条命令处理由真实响应映射而来的本地数据，映射约定在 [contract.md](skills/mcd-patch/references/contract.md)。不提供猜测的麦当劳参数示例。

## 实现与验证边界

- 智能体：理解需求、调用 MCP、组合候选、记录每个条件的证据。
- `mcp_readonly.py`：固定官方 HTTPS 主机、工具发现、JSON/SSE 响应、只读工具允许列表。
- `diagnose.py`：整数金额、报价新鲜度、条件检查、最小修改集合。
- `tests/`：覆盖需求不可擅改、未知信息排除、预算边界、不同门店、过期核价、Pareto 建议、SSE 与写操作阻断。

`mode=live` 只是输入来源声明，诊断器本身不能证明响应真实。正式接入需要查看实际 MCP 响应并完成完整业务链验证。300 秒新鲜度窗口是本项目策略，非官方锁价承诺；提交订单前仍需重新核价。

## 参赛材料

[MCP_INTEGRATION.md](MCP_INTEGRATION.md) 说明接入与验证状态；[CONTEST_DECLARATION.md](CONTEST_DECLARATION.md) 为赛事官方原文；[报名准备](docs/REGISTRATION.md) 记录提交格式与待完成事项。

本项目在 Codex 中开发，未使用 WorkBuddy，不提供或伪造 `workbuddy.md`。是否符合参赛资格以官方审核为准。

## 使用与授权

原创代码与文档采用 MIT 许可；官方声明原文及麦当劳服务、商标、内容受各自权利与服务规则约束，不因本项目许可获得额外授权。项目为个人非商业参赛作品。价格、供应及优惠规则以官方实时结果为准。
