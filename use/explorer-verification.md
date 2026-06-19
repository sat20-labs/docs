# 使用 Explorer 验证交易和资产

Explorer 是普通用户验证交易、资产和合约状态的入口。它不替代钱包授权，也不替代 Indexer 的底层 API，但它能把链上证据变成可读页面。

## 你可以验证什么

1. BTC L1 funding、splicing、close、punish 等交易。
2. SatoshiNet unlock、lock、anchor、deAnchor 等交易。
3. UTXO 是否存在、是否花费。
4. 资产数量和协议状态。
5. 合约部署、调用和 Result TX。
6. 通道地址、交易历史和跨层证据。

## 标准验证流程

1. 从钱包、DEX 或 Agent 复制 txid。
2. 判断它属于 BTC L1 还是 SatoshiNet L2。
3. 打开对应 Explorer。
4. 查询 txid、地址或 UTXO。
5. 确认高度、确认数、输入、输出和资产变化。
6. 如果状态和钱包不一致，等待 Indexer 收敛或停止继续操作。

## 对 STP 操作的验证

| 操作 | 需要验证 |
| --- | --- |
| open | L1 funding、L2 anchor、channel ready |
| splicing-in | L1 资产进入通道地址、L2 anchor、commit height 前进 |
| unlock | L2 个人地址获得可花费资产 |
| lock | L2 个人资产重新进入通道保护 |
| splicing-out | L2 deAnchor、L1 输出到目标地址 |
| punish | 旧 commitment 上链、punish tx 上链、旧通道关闭 |

## 下一步

后续应为每类操作补充真实截图、Explorer URL 模板和 Indexer API 示例。

**页面状态：规划中（Planning）**
