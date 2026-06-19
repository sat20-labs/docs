# 使用聪网

Use 部分面向普通用户、资产玩家和社区成员。目标是让用户知道如何进入聪网、如何使用资产、如何退出，以及如何判断自己的资产仍在自己控制之下。

## 用户路径

| 目标 | 指南 |
| --- | --- |
| 安装钱包、连接聪网、理解资产位置 | [钱包与资产](wallet-and-assets.md) |
| 获取测试资产和测试 GAS | [获取测试资产和测试 GAS](test-assets-and-gas.md) |
| 完成第一次 DEX Swap | [完成第一次 Swap](first-swap.md) |
| 提供 AMM 流动性 | [提供 AMM 流动性](amm-liquidity.md) |
| 使用限价单 | [使用限价单](limit-order.md) |
| 参与 Launchpad | [参与 Launchpad](launchpad.md) |
| 注册 DAO UID | [注册 DAO UID](dao-uid.md) |
| 向社区基金捐献 | [向社区基金捐献](community-fund-donation.md) |
| 申请与审核空投 | [申请与审核空投](airdrop.md) |
| 加入社区 DEX | [加入社区 DEX](community-dex.md) |
| 用 Explorer 和 Indexer 验证交易 | [使用 Explorer 验证交易](explorer-verification.md) |
| 让 AI Agent 帮你查询和操作 | [使用 AI Agent 查询和操作](ai-agent.md) |
| 退出聪网和故障恢复 | [退出聪网与故障恢复](exit-and-recovery.md) |
| 常见问题 | [常见问题](faq.md) |

带状态标签的页面表示内容仍在规划或对应系统仍在开发，保留入口便于后续逐步补齐。

## 基础资产路径

1. 安装 [SAT20 PWA Wallet](https://sat20.org/pwa/?install=1)，创建或导入钱包并完成备份。
2. 连接默认 Core Node。
3. 打开 STP 通道。
4. 通过 Indexer 确认 BTC L1 资产 UTXO、确认数和协议状态。
5. 将 BTC L1 资产 splicing-in 到通道。
6. 使用 unlock 将资产释放到聪网个人地址。
7. 在聪网中转账、交易或使用合约。
8. 需要回到 BTC L1 时，使用 lock、splicing-out 或 close。

## 用户最需要理解的三件事

1. 聪网资产不是中心化桥托管资产。
2. Indexer 是资产事实层，帮助用户验证资产位于 BTC L1、通道还是聪网。
3. 用户需要能验证自己持有最新承诺交易和退出路径。
4. 任何主网价值移动都应通过钱包授权确认。

## 每篇指南的标准结构

每一篇用户指南都会尽量包含：

1. 操作前准备。
2. 具体步骤。
3. 成功结果。
4. 如何通过 Explorer / Indexer / 钱包验证。
5. 风险提醒。
6. 下一步。

## 常见场景

| 场景 | 应阅读 |
| --- | --- |
| 我想把资产进入聪网 | [钱包与资产](wallet-and-assets.md) |
| 我想第一次交易 | [完成第一次 Swap](first-swap.md) |
| 我想提供流动性 | [提供 AMM 流动性](amm-liquidity.md) |
| 我想用订单簿交易 | [使用限价单](limit-order.md) |
| 我想参与社区活动 | [参与 Launchpad](launchpad.md) |
| 我想理解资产如何被识别 | [Indexer：比特币资产事实层](../learn/indexer.md) |
| 我想确认资产安全 | [资产安全模型](../learn/security-model.md) |
| 我想让 Agent 帮我操作 | [AI Agent 与用户资产控制](../learn/ai-agent.md) |
| 我想退出或恢复 | [退出聪网与故障恢复](exit-and-recovery.md) |
| 我想了解测试网演练 | [SAT20 Agent Wallet 测试网验证记录](../ai/sat20-agent-wallet/testnet-validation.md) |

## 风险边界

主网操作前，用户需要确认：

1. 网络是 mainnet 还是 testnet。
2. 资产名称和金额。
3. 目标地址。
4. 费用。
5. L1/L2 indexer 是否能查询到相关交易和资产状态。
6. 通道状态是否安全。
7. 钱包是否展示了授权弹窗。

如果钱包或 Agent 无法证明通道安全，就停止操作。

**页面状态：规划中（Planning）**
