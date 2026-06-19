# AI Agent

AI Agent 部分关注一个问题：如何让 Agent 在不接触私钥、不绕过授权的前提下，帮助用户安全操作 BTC L1 与聪网资产，并逐步帮助 BTC 社区规划和部署自己的基础设施。

SAT20 的判断是：越复杂的协议，越需要 Agent 帮用户理解和验证。STP 的承诺交易、惩罚交易、跨层状态和异常恢复，对 Agent 来说是可以读取和推理的证据。

## 两条产品线

| 产品线 | 目标 |
| --- | --- |
| Agent Wallet & Safety | 帮助用户在钱包安全边界内验证和操作资产 |
| Community Builder Agent | 帮助 BTC 社区通过对话规划 DEX、DAO、钱包、Indexer、Explorer 和合约模块 |

## 入口

1. [比特币生态 AI Agent 资产安全评估规范](bitcoin-agent-safety-standard.md)
2. [AI Agent 与用户资产控制](../learn/ai-agent.md)
3. [SAT20 Agent Wallet 安装与使用](sat20-agent-wallet/readme.md)
4. [SAT20 Agent Wallet 互操作技能规范](sat20-agent-wallet/interoperability.md)
5. [SAT20 Agent Wallet 资产安全控制指南](sat20-agent-wallet/asset-safety.md)
6. [SAT20 Agent Wallet 验证矩阵与数据缺口](sat20-agent-wallet/verification-and-data-gaps.md)
7. [SAT20 Agent Wallet 测试网验证记录](sat20-agent-wallet/testnet-validation.md)
8. [Community Builder Agent](community-builder-agent.md)

## 基本原则

1. Agent 不保存私钥。
2. Agent 不保存助记词。
3. Agent 不绕过钱包授权。
4. Agent 不只看余额。
5. Agent 必须检查承诺交易和惩罚覆盖。
6. Agent 发现安全证据缺失时必须停止价值移动。

## 长期方向

1. 钱包 Agent：帮助用户安全管理跨层资产。
2. 合约 Agent：解释和执行合约操作。
3. 风控 Agent：发现异常状态和旧承诺广播。
4. 社区 Agent：回答文档、测试网和开发者问题。
5. Community Builder Agent：帮助社区生成部署架构、配置、合约参数和验收报告。
