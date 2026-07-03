# 我是 AI Agent 开发者

AI Agent 在聪网生态中有两条产品线。

第一条是 Agent Wallet & Safety：帮助用户安全操作钱包、STP 通道和资产跨层流动。

第二条是 Community Builder Agent：帮助 BTC 社区通过对话设计并逐步部署自己的 DEX、DAO、Indexer、Explorer、钱包入口和合约模块。

## Agent Wallet & Safety

这条路径已经有较完整的安全基础：

1. Agent 不保存私钥、助记词或钱包密码。
2. Agent 通过 PWA Wallet adapter 调用钱包。
3. Agent 在价值移动前读取 `stp.safety_snapshot`。
4. Agent 检查 commitment、punish coverage、L1/L2 indexer 证据和 pending 事务。
5. Agent 在未知网络结果、缺少惩罚覆盖或通道降级时停止操作。

入口：

* [SAT20 Agent Wallet 安装与使用](../ai/sat20-agent-wallet/)
* [资产安全控制指南](../ai/sat20-agent-wallet/asset-safety.md)
* [验证矩阵与数据缺口](../ai/sat20-agent-wallet/verification-and-data-gaps.md)

## Community Builder Agent

这条路径是后续生态建设重点。目标是：

> 让任何 BTC 社区通过几轮对话，设计并逐步部署自己的 DAO、DEX、钱包、Indexer 和 Explorer。

它需要文档和工具逐步具备：

1. 每个模块有明确输入和输出。
2. 参数能用 JSON Schema 表达。
3. API 和错误码稳定。
4. 配置示例可复制。
5. 合约模板有机器可读描述。
6. 部署步骤能对应具体工具调用。
7. 每一步都需要钱包签名确认和链上证据。

## 推荐路径

1. 从 [SatoshiNet AI Agent Quickstart](../build/ai-agent-quickstart.md) 开始。
2. 使用 [Community Stack](../community-stack/) 理解社区完整方案。
3. 将每个模块的用户输入、配置输出、部署结果和验证证据结构化。
4. 优先在测试网完成只读查询、配置生成和人工确认部署。
