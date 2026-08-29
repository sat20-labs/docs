# Built on SatoshiNet

本文集中展示已经可访问或正在测试网验证的项目、工具和案例。状态只说明当前可验证范围，不代表第三方审计、流动性或长期SLA。

## 展示对象

可以进入本页的内容包括：

1. 官方参考 DEX。
2. AMM、限价单、Launchpad、DAO 等合约或模板。
3. 钱包、Wallet SDK、PWA adapter。
4. Indexer、Explorer、RPC 和节点工具。
5. 社区合作项目。
6. AI Agent Demo。
7. 测试网演练案例。
8. 外部贡献者项目。

## 案例模板

每个项目应使用统一模板：

| 字段 | 说明 |
| --- | --- |
| 项目名称 | 项目或社区名称 |
| 解决的问题 | 用户或社区得到什么能力 |
| 使用的聪网模块 | STP、Indexer、合约、GAS、Wallet SDK、Explorer、Agent 等 |
| 当前状态 | Available / Testnet / In Development / Experimental / Planned |
| 在线体验 | 网站、测试网、Demo 或视频 |
| 开源地址 | GitHub 或其他公开代码 |
| 链上证据 | 合约地址、txid、Explorer、Indexer API |
| 团队 / 联系方式 | 维护者、社区或合作入口 |
| 希望获得的合作 | 开发、流动性、测试用户、审计、内容、节点等 |

## 当前参考实现

| 类型 | 项目 | 状态与入口 |
| --- | --- | --- |
| 钱包 | SAT20 PWA Wallet | [主入口](https://sat20.org/pwa/)；主网/测试网、L1/L2/Channel、市场、工具与账户管理持续迭代 |
| L2市场 | SAT20 / SatoshiNet Market | [主网](https://satsnet.ordx.market/swap/?network=mainnet)；[测试网](https://test-satsnet.ordx.market/swap/?network=testnet)；当前文档验收AMM与限价单 |
| Indexer | SAT20 L1 Indexer / SatoshiNet L2 Indexer | 已实现；见 [源码地图](../build/api-source-map.md) 与 [运行说明](../run/indexer.md) |
| Explorer | SatoshiNet Explorer | [主网](https://mempool.sat20.org/)；[主网应用浏览器](https://mainnet.sat20.org/browser/app/)；[测试网应用浏览器](https://testnet.sat20.org/browser/app/) |
| 智能合约 | Template / Agent / EVM Runtime | 公开测试网迭代；通过PWA `工具 -> 智能合约`部署或调用，见 [合约目录](../build/contract-template-catalog.md) |
| Agent | SAT20 Agent Wallet | 测试网演练与安全证据已归档，见 [验证记录](../ai/sat20-agent-wallet/testnet-validation.md) |

Launchpad、DAO、社区基金等底层历史运行时不在此表中自动标为公开产品；只有具备当前入口、登记合约和可复核证据后才加入。

## 收录原则

1. 优先收录有可验证证据的项目。
2. 不展示无法复核的宣传信息。
3. 不承诺收益、价格或投资回报。
4. 对测试网、实验性和生产可用状态做明确区分。
5. 对涉及用户资产的项目，必须提供风险边界和验证路径。

**最后核对：2026-08-29。页面状态：持续维护（Maintained）**
