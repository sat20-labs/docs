# SatoshiNet AI Agent Quickstart

本文面向 AI Agent 开发者。目标是让 Agent 能读取聪网文档、调用钱包 adapter、验证资产安全，并逐步扩展到 Community Builder Agent。

## 两条路径

| 路径 | 目标 |
| --- | --- |
| Agent Wallet & Safety | 帮用户安全操作钱包、STP 通道和资产跨层流动 |
| Community Builder Agent | 帮 BTC 社区设计和部署 DEX、DAO、Indexer、Explorer、钱包和合约模块 |

## Agent Wallet 最小流程

1. 用户安装 SAT20 PWA Wallet。
2. 用户在 PWA 内创建或导入钱包。
3. Agent 安装 SAT20 Agent skill。
4. Agent 调用 `wallet.status`。
5. Agent 调用 `stp.status`。
6. Agent 调用 `stp.safety_snapshot`。
7. Agent 只在 `READY_SAFE` 时发起价值移动。
8. PWA 钱包展示授权弹窗。
9. Agent 轮询 `stp.transaction`。
10. Agent 返回 txid、状态和验证链接。

## Community Builder Agent 最小流程

1. 用户描述社区目标。
2. Agent 选择 DEX、DAO、Indexer、Explorer、钱包等模块。
3. Agent 生成配置草案。
4. 用户确认关键参数。
5. Agent 生成测试网部署计划。
6. 部署工具执行，钱包或多签完成授权。
7. Agent 收集 Explorer、Indexer 和合约证据。
8. Agent 生成社区上线检查报告。

## 当前需要补齐

1. 模块参数 JSON Schema。
2. 合约模板机器可读描述。
3. 部署工具接口。
4. 错误码和下一步建议。
5. 测试网案例和示例输出。

**页面状态：开发中（In Development）**
