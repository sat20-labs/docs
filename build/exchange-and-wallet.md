# 交易平台与钱包接入

交易平台和钱包是聪网生态的重要入口。它们需要的不只是转账接口，还需要能解释资产处于 BTC L1、通道、聪网个人地址、合约或 pending 状态中的哪一种。

对交易平台和钱包来说，indexer 是资产事实层。充值、提现、splicing、unlock、lock、余额展示和风控都必须建立在 L1/L2 indexer 可复核的 txid、vout、资产协议、确认数和通道状态之上。

## 接入目标

| 角色 | 目标 |
| --- | --- |
| 钱包 | 管理私钥、授权、签名、通道状态和用户安全提示 |
| 交易平台 | 支持充值、提现、资产识别、确认数和异常处理 |
| Indexer | 提供 L1/L2 资产、交易、UTXO、通道和合约状态 |
| Agent | 读取证据，解释风险，调用钱包 adapter |

## 钱包必须保护什么

钱包必须保护：

1. 助记词和私钥。
2. 通道数据库。
3. 最新承诺交易。
4. 已撤销状态的惩罚材料。
5. 未完成 reservation。
6. 用户授权记录。

Agent 不直接接触这些秘密材料。

## 交易平台必须理解什么

交易平台接入聪网时，应区分：

1. BTC L1 确认。
2. 聪网 L2 确认。
3. STP 通道状态。
4. anchor / deAnchor 状态。
5. 资产是否可花费。
6. 是否存在 pending 操作。

如果只看余额，不看状态，容易在跨层过程中产生错误判断。

如果只看单个 indexer 响应，不看 txid、vout、确认数、reorg、mempool 和跨层对应关系，也容易产生错误判断。关键资产移动应保留可复核证据。

## 推荐接口

1. L1 / L2 地址 summary。
2. 交易详情。
3. UTXO 资产详情。
4. channel ledger。
5. anchor / deAnchor 记录。
6. STP transaction / reservation 查询。
7. safety snapshot。
8. reorg / mempool / not indexed 状态。

后续交易平台接入文档会在此基础上继续拆分为充值、提现、风控、对账和异常恢复章节。
