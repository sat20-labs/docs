# STP 简介

STP 是 Satoshi Transcending Protocol，中文可称为聪穿越协议。它定义 BTC L1 资产如何进入聪网、在聪网中流动、再退出回 BTC L1。

STP 的核心不是“桥”，而是通道。

STP 必须和 indexer 一起理解。Indexer 说明 BTC L1 上的资产事实：哪个 UTXO 携带什么资产、是否确认、是否已花费、协议事件是否有效。STP 在这些资产事实之上建立通道控制权，让用户能进入聪网，也能在异常情况下退出。

## STP 做什么

| 动作 | 含义 |
| --- | --- |
| open | 打开用户与 Core Node 的通道 |
| splicing-in | 把 BTC L1 资产加入已有通道 |
| unlock | 把通道资产释放到聪网个人地址 |
| lock | 把聪网个人资产重新纳入通道 |
| lock-with-expand | 容量不足时恢复用户资产的通道保护 |
| splicing-out | 把通道资产退出到 BTC L1 |
| close | 关闭通道 |
| punish | 对旧承诺交易进行惩罚 |

这些动作不是孤立交易，而是协议状态机。它们可能涉及 BTC L1 交易、聪网交易、承诺状态更新、签名交换和链上确认。每一个跨层动作都需要 L1/L2 indexer 提供可复核证据，证明资产事实与通道状态一致。

## 普通用户不需要质押

普通用户连接 Core Node 打开私人通道时，不需要预先质押资产。质押只属于节点连接 bootstrap node，并准备升级为 Core Node 的路径。

普通用户通道与节点质押路径是两种不同场景。

## 对 Agent 的意义

STP 很适合被 AI Agent 操作，因为它有清晰的状态、交易、证据和恢复路径。Agent 可以把用户目标转换成可验证步骤：

1. 查询钱包和通道。
2. 检查安全快照。
3. 选择 open、splicing、unlock、lock 或 close。
4. 通过 indexer 轮询 L1/L2 交易和资产状态。
5. 遇到结果未知时进入恢复流程。

STP 的完整协议白皮书见 [STP 技术白皮书](../protocol/stp/readme.md)。
