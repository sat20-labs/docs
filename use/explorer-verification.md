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

## 当前入口

| 网络 | 入口 | 用途 |
| --- | --- | --- |
| Bitcoin mainnet | [mempool.space](https://mempool.space/) | L1交易、地址、UTXO和确认 |
| Bitcoin testnet4 | [mempool.space/testnet4](https://mempool.space/testnet4/) | 测试网L1交易与确认 |
| SatoshiNet mainnet | [mempool.sat20.org](https://mempool.sat20.org/) | 聪网主网交易与地址 |
| SatoshiNet mainnet应用浏览器 | [mainnet.sat20.org/browser/app](https://mainnet.sat20.org/browser/app/) | 资产、UTXO和应用视图 |
| SatoshiNet testnet应用浏览器 | [testnet.sat20.org/browser/app](https://testnet.sat20.org/browser/app/) | 测试网资产、UTXO和应用视图 |

入口可用不代表所有协议字段已经统一展示。浏览器缺少的合约、通道或资产细节，应继续通过PWA使用的L1/L2 Indexer API验证；不要拿BTC txid去查聪网，也不要让底层工具通过txid格式盲猜网络。

## 对 STP 操作的验证

| 操作 | 需要验证 |
| --- | --- |
| open | L1 funding、L2 anchor、channel ready |
| splicing-in | L1 资产进入通道地址、L2 anchor、commit height 前进 |
| unlock | L2 个人地址获得可花费资产 |
| lock | L2 个人资产重新进入通道保护 |
| splicing-out | L2 deAnchor、L1 输出到目标地址 |
| punish | 旧 commitment 上链、punish tx 上链、旧通道关闭 |

## 判定边界

- `not found`先确认网络、txid和Indexer高度；不能直接等同交易失败。
- 已广播但未确认属于pending；已确认但合约item未完成，应继续查invoke history和Result TX，不再标成“等L1确认”。
- reorg后旧L2证据可能失效；历史测试记录必须标明网络、高度和核对日期。
- Explorer只读展示不能替代钱包签名、客户端验证或通道安全快照。

**页面状态：已实现 / 持续完善展示（Implemented / Iterating），入口于2026-08-29核对**
