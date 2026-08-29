# L1 / L2 Indexer

Indexer 是聪网资产事实层。L1 Indexer 负责 BTC 主网多协议资产事实，L2 Indexer 负责聪网交易、UTXO、通道、合约和跨层状态。

## 运行价值

1. 为钱包和交易平台提供资产查询。
2. 为 Explorer 提供可视化数据。
3. 为 STP 和 Agent 提供跨层证据。
4. 为 DEX、DAO 和合约应用提供状态查询。
5. 通过多方运行降低单点依赖。

## 当前实现边界

| 项目 | 当前实现 |
| --- | --- |
| L1入口 | `indexer`仓库根目录`main.go`；`cmd/main.go`是工具/测试入口，不是生产服务 |
| L1数据源 | 对应网络的bitcoind RPC；主网、testnet/testnet4配置和数据库必须隔离 |
| L1数据库 | 默认Pebble；Badger只通过明确build tag选择。某个测试网使用Badger不代表SDK、STP或所有节点都应切换 |
| L1协议 | 基础UTXO/sat range、Ordinals、ORDX、BRC-20、Runes、稀有聪等 |
| L1 reorg | 实时状态与延迟落库窗口配合，按链回退并重放；备份必须同时记录链tip与数据库高度 |
| L2 Indexer | 位于`satoshinet/indexer`并随聪网节点运行，索引L2 UTXO、ascend/descend、通道、合约和DKVS |
| 对外API | L1与L2分别通过配置的proxy暴露；调用方必须显式指定网络，不能通过txid格式猜链 |

源码入口见 [API源码地图](../build/api-source-map.md)。编译和启动前必须先核对当前仓库的`build.sh`、环境配置和build tags，文档不固定复制某台服务器的路径或凭据。

## 运行检查

1. 记录代码commit、dirty diff、Go版本、build tags和二进制SHA-256。
2. 核对chain、bitcoind、DB路径、RPC proxy和服务端口，禁止主网/测试网共用数据库。
3. 启动后比较链tip、indexer内部tip、对外best height和block hash，而不是只看进程存在。
4. 用已知地址和UTXO抽查资产摘要、UTXO详情、交易确认和mempool花费过滤。
5. reorg测试应证明错误块不会永久污染状态，回退后能从共同祖先重新处理。
6. 备份恢复后先只读校验高度/hash与DB自检，再恢复写入和公开流量。

## 多Indexer交叉验证

同一请求应比较网络、tip/hash、UTXO outpoint、资产协议、数量、确认状态和错误语义。高度不一致时先等待追平；同高不同hash或同outpoint资产不同属于数据分叉，不能用多数API返回成功掩盖。

**页面状态：已实现 / 运维文档持续完善（Implemented / Iterating）**
