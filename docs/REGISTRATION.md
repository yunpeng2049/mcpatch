# 报名准备与提交

核对日期：2026-10-25（北京时间）。

官方活动：[M-China/mcd-developer-innovation-challenge](https://github.com/M-China/mcd-developer-innovation-challenge)

官方截止：2026-10-25 23:59；最终排行榜数据采集时间：2026-10-26 00:00。

## 当前状态

- 已准备：README.md、官方原文 CONTEST_DECLARATION.md、MCP_INTEGRATION.md、环境变量占位符配置、完整 Skill、可运行脚本及离线测试。
- 已完成：Token 本地配置；真实 MCP 查询、核价和本地诊断验证；完整源码已发布到个人公开仓库 https://github.com/yunpeng2049/mcpatch ，远端 19 个文件已逐项核对。
- 已提交：北京时间 2026-10-25 09:27:43，通过 `yunpeng2049` 账号提交 [报名 Issue #1337](https://github.com/M-China/mcd-developer-innovation-challenge/issues/1337)。
- 报名成功：北京时间 2026-10-25 09:59:09，官方账号 `M-China-Official` 回复「您的作品已成功参赛，您可以通过官方项目的排行榜.md查看排名」。[查看官方确认回执](https://github.com/M-China/mcd-developer-innovation-challenge/issues/1337#issuecomment-6392210436)。
- 排名快照：2026-10-25 15:12 核验时仓库为 0 Star，尚未出现在 [15:00:59 更新的官方排行榜](https://github.com/M-China/mcd-developer-innovation-challenge/blob/main/RANKING.md)中。参赛成功与排行榜名次是两个状态，当前没有已确认名次。

## 官方要求

按照 [activityGuidelines.md](https://github.com/M-China/mcd-developer-innovation-challenge/blob/main/activityGuidelines.md)：真实使用麦当劳 MCP；个人 GitHub Public 仓库；规定文件；项目创建时间在 2025-12-25 00:00 至 2026-10-25 23:59。参赛者须为中国大陆合法居民，年满 18 岁或已获监护人同意。提交参赛申请包含对活动规则及相关信息处理的声明。

GitHub 账号为 `yunpeng2049`，公开仓库为 `mcpatch`，创建于 2026-10-24。实测记录见 LIVE_VERIFICATION.md。

## 已提交的报名 Issue

标题：`【参赛申请】McPatch · 麦麦需求编译器`

以下为已提交的报名正文：

```text
【参赛申请】
项目名称：McPatch · 麦麦需求编译器
项目地址：https://github.com/yunpeng2049/mcpatch
项目简介：基于麦当劳 MCP 的多人点餐需求编译 Skill，将人数、预算和每人偏好转化为完整购物车候选，使用官方门店、菜单、套餐详情、优惠券查询和核价工具检查可行性；条件冲突时保留每个人不可调整的需求，给出最小修改建议与预算差额。已完成真实 MCP 查询及四个购物车核价，附脱敏实测记录、可回放示例和18项自动化测试。
```

字段名称和内容放在同一行，项目 URL 使用纯文本；不得把整个正文挤成一行。提交前再次检查官方模板有无更新。

系统已回复参赛成功，无需重复提交。官方按公开真实 Star 排名；Star 数为 0 的项目不进入排行榜，原则上前 100 个项目及第 100 个项目的并列项目入榜，不进行刷星或虚假互动。

## WorkBuddy

官方推荐使用 WorkBuddy，但它不是普通参赛的强制条件。本项目当前使用 Codex 开发；若以后真实使用 WorkBuddy 调试，应导出真实上下文后再考虑专项奖励，不伪造历史。

## 原文校验

官方参赛声明 Git blob SHA：`136e76f3160317049f19f5ba03f4d0fedd70fc3c`。提交前用 `git hash-object CONTEST_DECLARATION.md` 核对一致，文件名与内容不能更改。
