# AI Agent 与用户资产控制

AI Agent 不是 SAT20 的附属功能。它可能成为普通用户使用 STP、聪网和智能合约的重要入口。

STP、RSMC、承诺交易、惩罚交易、indexer 资产证据和跨层资产状态对多数用户都很复杂。Agent 的价值在于，它可以读懂这些证据，并把复杂协议转换成可执行、可解释、可验证的用户操作。

## Agent 的职责

Agent 负责：

1. 理解用户目标。
2. 查询钱包、通道、L1/L2 交易和 indexer。
3. 复核资产事实、确认数、花费状态和跨层证据。
4. 判断当前安全状态。
5. 调用钱包 adapter。
6. 解释每一步操作的作用。
7. 在不安全时停止。

Agent 的边界：

1. 不保存用户助记词。
2. 不绕过钱包授权。
3. 无法证明惩罚覆盖时停止移动资产。
4. 不把Core Node 口头状态当成安全证明。

## Skill 模型

SAT20 提供 SAT20 Agent Wallet skill，让 Agent 能通过统一 JSON adapter 操作钱包和 Core Node。

推荐顺序：

1. 用户先安装 [SAT20 PWA Wallet](https://sat20.org/pwa/?install=1)。
2. 用户在 PWA 内创建或导入钱包，完成备份、解锁和网络选择。
3. Agent 再安装 SAT20 Agent Wallet skill，并通过 PWA adapter 调用钱包。
4. Agent 先执行 `wallet.status`、`stp.status` 和 `stp.safety_snapshot`，验证安全状态后再移动资产。

安装 skill：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/install.sh | bash
```

更多说明见 [SAT20 Agent Wallet 安装与使用](../ai/sat20-agent-wallet/readme.md)。
