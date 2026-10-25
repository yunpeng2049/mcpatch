# 验证记录

日期：2026-10-25。环境：Python 3.11.7。

| 项目 | 结果 |
| --- | --- |
| Python 单元测试 | 18 项通过，含系统证书校验和业务失败处理 |
| Skill 格式校验 quick_validate.py | 通过 |
| Python 语法编译检查 | 通过 |
| 离线演示 | 生成 A/B/C 三个互不支配修改方案；排除缺证据的 E |
| 官方声明原文校验 | Git blob SHA 与官方一致：136e76f3160317049f19f5ba03f4d0fedd70fc3c |
| 缺失 Token 行为 | 明确报错退出，无虚构查询结果 |
| 真实 MCP 连接、菜单和核价 | 已完成 6 种业务工具调用及 4 个完整购物车核价，详见 LIVE_VERIFICATION.md |
| 真实结果诊断 | 保留全部条件需增加 330 分，或仅放弃共享薯条；两种最小修改均验证通过 |
| 公开仓库 | https://github.com/yunpeng2049/mcpatch |
| 报名 Issue、系统回执 | 见 REGISTRATION.md，以官方回复为准 |

复现：

```bash
python3 -m unittest discover -s tests -v
python3 skills/mcd-patch/scripts/diagnose.py --demo skills/mcd-patch/examples/demo.json
git hash-object CONTEST_DECLARATION.md
```

单元测试使用本地虚构数据与内存 SSE 流，不涉及真实账户或订单。Skill 格式校验工具属于开发环境，依赖 PyYAML；运行作品本身不需要第三方 Python 依赖。
