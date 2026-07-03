# 我运行基础设施

聪网需要基础设施团队参与运行 Core Node、Indexer、Explorer、RPC、监控和数据服务。

基础设施不是边缘角色。Indexer 和节点共同决定用户能否验证资产事实、交易状态、合约状态和跨层证据。

## 可参与方向

| 方向         | 价值                                           |
| ---------- | -------------------------------------------- |
| Core Node  | 提供 STP 服务、SatoshiNet 节点能力和网络基础服务             |
| L1 Indexer | 解析 BTC L1 上的 Ordinals、Runes、BRC20、ORDX 等资产事实 |
| L2 Indexer | 索引 SatoshiNet UTXO、ascend、descend、通道、合约和交易状态 |
| Explorer   | 为用户、社区和交易平台提供可视化验证入口                         |
| RPC / API  | 为钱包、DEX、Agent、交易平台和开发者提供稳定访问                 |
| 监控与告警      | 保障节点、Indexer、STP、合约和 API 长期运行                |

## 推荐路径

1. 阅读 [SatoshiNet 协议概览](../protocol/satoshinet/)。
2. 阅读 [Indexer：比特币资产事实层](../learn/indexer.md)。
3. 阅读 [运行基础设施 Quickstart](../build/infrastructure-quickstart.md)。
4. 在测试网运行一个节点或 Indexer。
5. 为钱包或社区项目提供只读 API。
6. 通过 Explorer 或监控面板公开运行状态。

## 关键原则

1. 单个服务返回不是最终事实，关键状态需要链上证据和跨源验证。
2. L1/L2 高度、reorg、mempool、未索引状态必须清晰表达。
3. 面向钱包和交易平台的 API 需要稳定错误码和下一步建议。
4. 运行者不应替用户保管私钥或绕过钱包授权。
