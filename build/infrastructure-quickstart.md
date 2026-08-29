# 运行核心节点、Indexer 和 Explorer

本文用于基础设施团队启动聪网节点、Indexer、Explorer、RPC和监控服务。组件均已有实现，但第三方部署不能复制现有服务器的私有路径、密钥或生产配置；应从仓库内当前安装指南和示例配置生成自己的环境。

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

1. 阅读 [SatoshiNet 协议概览](../protocol/satoshinet/)。
2. 阅读 [API 源码地图](api-source-map.md)。
3. 从对应仓库固定commit和dirty diff，按当前build脚本编译；确认DB backend和build tags。
4. 使用独立域名、端口、数据目录和密钥在测试网启动节点或Indexer。
5. 验证共同高度/hash、Indexer内部tip与对外best height、交易/资产查询和错误处理。
6. 为钱包、DEX或Agent提供最小只读API；管理和测试故障接口不公开。
7. 加入监控、备份、证书更新和告警，再进行长期运行。

## 验收标准

1. 节点高度正常同步。
2. L1/L2 Indexer 能查询交易、地址、UTXO 和资产。
3. Explorer 能通过 txid、address、asset 查询。
4. API 能表达 pending、not found、reorg、unindexed 等状态。
5. 服务重启后能恢复。

详细边界见 [运行Indexer](../run/indexer.md)、[Explorer/RPC](../run/explorer-rpc.md) 和 [监控、备份与升级](../run/operations.md)。

**页面状态：组件已实现 / 第三方部署文档持续完善（Implemented / Integration Docs Iterating）**
