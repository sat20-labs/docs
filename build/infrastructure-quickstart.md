# 运行基础设施 Quickstart

本文用于基础设施团队启动聪网节点、Indexer、Explorer、RPC 和监控服务。当前先定义路径，后续补充完整命令和配置。

## 你可以运行什么

1. SatoshiNet Core Node。
2. BTC L1 Indexer。
3. SatoshiNet L2 Indexer。
4. Explorer。
5. RPC / API 网关。
6. 监控和告警。

## 操作前准备

1. 服务器和持久化磁盘。
2. 网络端口和域名。
3. BTC L1 节点或可信数据源。
4. SatoshiNet 节点配置。
5. 数据备份和监控方案。

## 推荐步骤

1. 阅读 [SatoshiNet 协议概览](../protocol/satoshinet/readme.md)。
2. 阅读 [API 源码地图](api-source-map.md)。
3. 先在测试网启动节点或 Indexer。
4. 验证高度同步、交易查询、资产查询和错误处理。
5. 为钱包、DEX 或 Agent 提供只读 API。
6. 加入监控和告警。

## 验收标准

1. 节点高度正常同步。
2. L1/L2 Indexer 能查询交易、地址、UTXO 和资产。
3. Explorer 能通过 txid、address、asset 查询。
4. API 能表达 pending、not found、reorg、unindexed 等状态。
5. 服务重启后能恢复。

**页面状态：规划中（Planning）**
