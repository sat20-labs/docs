# Use：使用聪网

Use 部分面向普通用户、资产玩家和社区成员。目标是让用户知道如何进入聪网、如何使用资产、如何退出，以及如何判断自己的资产仍在自己控制之下。

## 推荐路径

1. 安装 SAT20 PWA Wallet。
2. 创建或导入钱包。
3. 连接默认 core node。
4. 打开 STP 通道。
5. 通过 indexer 确认 BTC L1 资产 UTXO、确认数和协议状态。
6. 将 BTC L1 资产 splicing-in 到通道。
7. 使用 unlock 将资产释放到聪网个人地址。
8. 在聪网中转账、交易或使用合约。
9. 需要回到 BTC L1 时，使用 lock、splicing-out 或 close。

## 用户最需要理解的三件事

1. 聪网资产不是中心化桥托管资产。
2. Indexer 是资产事实层，帮助用户验证资产位于 BTC L1、通道还是聪网。
3. 用户需要能验证自己持有最新承诺交易和退出路径。
4. 任何主网价值移动都应通过钱包授权确认。

## 常见场景

| 场景 | 应阅读 |
| --- | --- |
| 我想把资产进入聪网 | [STP 简介](../learn/stp.md) |
| 我想理解资产如何被识别 | [Indexer：比特币资产事实层](../learn/indexer.md) |
| 我想确认资产安全 | [资产安全模型](../learn/security-model.md) |
| 我想让 Agent 帮我操作 | [AI Agent 与用户资产控制](../learn/ai-agent.md) |
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
