# Indexer 接入与资产事实层

本文面向钱包、交易平台、浏览器、STP 客户端、AI Agent 和基础设施团队，说明如何理解 SAT20 indexer 的角色。

## Indexer 是什么

Indexer 是 BTC L1 与聪网 L2 的资产事实层。它不保管资产，不替用户签名，也不决定资产归属；它根据链上交易和协议规则，计算并提供可查询的资产状态。

SAT20 生态至少需要两类 indexer：

| 类型 | 主要数据 |
| --- | --- |
| BTC L1 Indexer | BTC UTXO、sat range、Ordinals、Runes、BRC20、ORDX、铭文、mempool、确认数、reorg 状态 |
| SatoshiNet L2 Indexer | 聪网 UTXO、ascend、descend、通道、合约、交易执行、资产状态 |

## 谁需要接入

| 角色 | 接入目的 |
| --- | --- |
| 钱包 | 展示资产、选择 UTXO、验证跨层操作结果 |
| STP 客户端 | 判断 splicing-in/out、open/close、lock/unlock 的资产输入和链上状态 |
| 交易平台 | 充值、提现、对账、风控和异常恢复 |
| 区块浏览器 | 展示 L1/L2 交易、资产、通道和合约状态 |
| AI Agent | 在价值移动前独立验证资产证据和安全边界 |

## 最低接入能力

一个合格客户端至少需要查询：

1. 地址 UTXO 列表。
2. 单个 UTXO 的资产详情。
3. 交易确认数、mempool 状态和是否被花费。
4. Ordinals、Runes、BRC20、ORDX 等协议资产状态。
5. L1 ascend / descend 相关交易。
6. L2 地址余额、UTXO、通道和合约交易。
7. reorg 或暂未索引时的明确错误状态。

对 STP 来说，关键不是“余额是多少”，而是“资产证据链是否完整”：L1 UTXO、L1 交易确认、ascend / descend 事件、L2 UTXO、通道承诺状态和钱包本地状态必须能互相解释。

## 接入原则

1. 单个余额字段不是资产安全证明。
2. 对 BTC L1 资产，必须关注 txid、vout、资产协议、确认数和花费状态。
3. 对 BRC20 transfer、Runes、ORDX、Ordinals 等资产，必须按协议规则判断有效性。
4. 对 STP 操作，必须能区分 L1 已确认、L2 已 ascend、L2 可花费、通道已更新这几个状态。
5. 对 mempool、网络错误、EOF、未索引和 reorg，客户端应返回明确状态，不应默认失败或默认成功。
6. 交易平台和 Agent 应保留可复核证据：txid、vout、asset、amount、height、confirmations、indexer source 和查询时间。

## 与 STP 的关系

STP 负责资产控制权，indexer 负责资产事实。

当用户发起 splicing-in 时，indexer 帮助客户端确认目标 UTXO 是否携带资产、资产是否有效、交易是否确认；STP 负责把该资产纳入通道并在聪网上生成对应状态。

当用户发起 splicing-out 或 close 时，STP 负责构造退出路径；indexer 帮助钱包和 Agent 确认 L2 descend 与 BTC L1 输出是否对应，资产是否已经回到用户可控制地址。

## 分布式 Indexer 方向

当前接入可以从官方 API 开始，但 indexer 的目标不是形成单点服务。它应逐步成为多方可独立运行、可交叉验证的资产事实网络。

L2 indexer 已经集成在聪网节点中。运行聪网节点的团队会随节点维护自己的 L2 UTXO、ascend、descend、通道、合约和交易状态，因此 L2 indexer 天然随着聪网节点网络分布。

L1 indexer 服务 BTC 主网资产事实。聪网 Core Node 要求配置并依赖自己的 L1 indexer，用来验证 L1 UTXO、资产协议事件、确认状态和跨层操作。也就是说，Core Node 网络本身会推动 L1 indexer 的事实分布式部署。

分布式 indexer 的建设重点包括：

1. 规则可公开复现。
2. 数据结果可交叉验证。
3. reorg、mempool 和异常状态可标准化表达。
4. 交易平台、钱包和 Agent 可以配置多个数据源。
5. 关键资产状态可以通过证明材料而不是单一 API 响应来解释。
6. Core Node、钱包、交易平台和浏览器可以独立运行或选择可信的 L1/L2 indexer。

这会让 BTC 主网上多协议资产拥有更安全、更统一的表达方式，也会让聪网成为更可信的比特币原生扩展网络。
