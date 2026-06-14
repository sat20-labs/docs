# SAT20 协议体系

SAT20 不是单一协议，而是一组围绕比特币原生资产建立的协议、索引、通道和执行环境。它的目标是让 BTC、Ordinals、Runes、BRC20、ORDX 等资产在保持用户控制权的前提下，进入一个更适合流通、合约和 AI Agent 自动化操作的网络。

## 四个基础层

| 层级 | 作用 |
| --- | --- |
| Indexer | 将 BTC L1 和 SatoshiNet L2 上的交易解析为可查询、可复核的资产事实 |
| STP | 用 RSMC 通道、承诺交易、撤销和惩罚机制，让资产进入、流通和退出聪网 |
| SatoshiNet | 承载聪网交易、enUTXO、通道合约、智能合约和 GAS 经济 |
| 通道合约 | 管理公共资产池，协调用户发起的 L1/L2 跨层动作 |
| 资产发行协议 | BTC、Ordinals、Runes、BRC20、ORDX 等由 Indexer 统一解析和表达的资产协议族 |

这四层的关系可以概括为：

1. BTC、Ordinals、Runes、BRC20、ORDX 等协议定义或承载资产。
2. Indexer 把这些资产从链上交易中解析出来，形成统一资产事实。
3. STP 把资产纳入用户与 Core Node 共同控制的通道，并在聪网生成对应资产状态。
4. 通道合约作为公共设施，协调用户发起的 L1/L2 跨层动作和公共资产池状态。
5. SatoshiNet 让资产在 L2 上快速流通、进入智能合约、支付 GAS，并在需要时通过 STP 回到 BTC L1。

## 设计原则

SAT20 协议体系遵循以下原则：

1. 资产来自比特币主网。聪网不凭空创造与 BTC L1 无关的资产余额。
2. 用户保留退出能力。Core Node 失败或作恶时，用户仍应能依靠承诺交易、惩罚交易和强制关闭路径保护资产。
3. 资产事实可复核。钱包、交易平台、浏览器和 AI Agent 应能追溯每份资产的 L1/L2 证据。
4. 协议语言无关。STP 客户端、Indexer 客户端和合约工具都应能由任意开发语言实现。
5. 面向 Agent 可验证。协议结果不仅表现为余额变化，还提供 txid、UTXO、commit height、ascend/descend、punish coverage 等证据。

## 阅读顺序

如果你是协议实现者，建议按以下顺序阅读：

1. [Indexer：比特币资产事实层](../learn/indexer.md)
2. [STP 技术白皮书](stp/readme.md)
3. [SatoshiNet 协议概览](satoshinet/readme.md)
4. [通道合约](channel-contracts/readme.md)
5. [资产发行协议](indexer/asset-issuance.md)
6. [智能合约协议](contracts/readme.md)

如果你是钱包、交易平台或 AI Agent 开发者，建议先读 [开发者中心](../build/readme.md)，再进入具体协议文档。
