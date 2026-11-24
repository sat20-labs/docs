# SatoshiNet Today：当前可用能力

本文展示聪网当前已经具备或正在建设的能力。它不是营销列表，而是公开状态索引。

## 状态维度

| 维度 | 说明 |
| --- | --- |
| 实现状态 | 已实现（Implemented）、开发中（In Development）、规划中（Planned）、实验性（Experimental） |
| 可用环境 | 公开测试网、有限测试、主网、未部署 |
| 文档证据 | 完整、部分、缺失、协议规范 |

## 能力矩阵

| 模块 | 实现状态 | 可用环境 | 文档证据 | 公开证据 / 下一步 |
| --- | --- | --- | --- | --- |
| SatoshiNet 核心节点 | 主网更新已完成 | 主网、公开测试网 | 部分 | 参考 [运行网络](../run/readme.md)；第三方准入与运维文档仍需完善 |
| L1 Indexer | 已实现 | 主网、testnet4 | 源码地图 | 参考 [Indexer 接入](../build/indexer.md) |
| L2 Indexer | 已实现 | 主网、公开测试网 | 源码地图 | 参考 [API 源码地图](../build/api-source-map.md) |
| Explorer | 已实现 / 迭代中 | 主网、测试网 | 用户指南 | 参考 [Explorer验证](../use/explorer-verification.md)；部分协议详情仍依赖Indexer API |
| SAT20 PWA Wallet | 已上线 | 主网、测试网 | 用户指南 / 源码 | [打开PWA Wallet](https://sat20.org/pwa/) |
| Wallet SDK | 已实现 / 迭代中 | 主网、测试网 | 接入边界 | 参考 [Wallet SDK接入](../build/wallet-sdk-quickstart.md) |
| STP / Transcend | 已实现 / 迭代中 | 主网、公开测试网 | 协议规范 / 测试证据 | 参考 [STP 技术白皮书](../protocol/stp/readme.md) |
| L2 市场 AMM 通道合约 | 已实现 | 主网、测试网 | 用户指南 | 参考 [提供 AMM 流动性](../use/amm-liquidity.md) |
| L2 市场限价单通道合约 | 已实现 | 主网、测试网 | 用户指南 | 参考 [使用限价单](../use/limit-order.md) |
| Launchpad | 已实现 | 测试网 | 部分 | 补充使用手册和案例 |
| DAO / 社区基金 | 已实现 | 有限测试网 | 部分 | 补充模板、UID、捐献、空投和治理流程 |
| 智能合约框架 | 测试网已开放，主网暂缓正式上线 | 公开测试网 | 部分 | 可通过 PWA 自行部署和调用，见 [智能合约协议](../protocol/contracts/readme.md) |
| EVM Runtime | 已实现 / 迭代中 | 公开测试网 | 协议规范 | 参考 [EVM 合约](../protocol/contracts/evm.md) |
| 模板 AMM 智能合约 | 已实现 / 测试中 | 公开测试网 | 部署指南 | 仅通过 PWA `工具 -> 智能合约` 交互，参考 [部署 AMM 池](../build/amm-pool-quickstart.md) |
| 模板限价单智能合约 | 已实现 / 测试中 | 公开测试网 | 部署指南 | 仅通过 PWA `工具 -> 智能合约` 交互，参考 [部署限价单模块](../build/limit-order-quickstart.md) |
| EVM ConstantProductAMM 样本 | 已实现 / 测试中 | 公开测试网 | 部分 | 参考 [EVM 样本合约](../build/evm-sample-contracts.md) |
| EVM LimitOrderBook 样本 | 已实现 / 测试中 | 公开测试网 | 部分 | 参考 [EVM 样本合约](../build/evm-sample-contracts.md) |
| Agent / Prediction 合约 | 已实现 / 测试中 | 公开测试网 | 用户指南 / 协议规范 | 参考 [Prediction 合约测试](../use/prediction-contract.md) 和 [自然语言合约](../protocol/contracts/agent.md) |
| DKVS | 已完成 | SAT20 PWA Wallet | 协议规范 / E2E | 已用于钱包账户管理与 RGB11 备份，见 [DKVS](../protocol/dkvs/readme.md) |
| RGB11 L1钱包闭环 | 已实现 / 迭代中 | Bitcoin L1测试流程 | 协议规范 / 钱包测试 | 发行、导入、invoice、发送、恢复已接入Wallet SDK/PWA；STP跨层仍未开放，参考 [RGB11](../protocol/rgb11/readme.md) |
| D-Indexer | 研发中 | 未作为独立公共产品部署 | 设计说明 | 与已实现DKVS分开表达 |
| Community Builder Agent | 规划中 / 实验性 | 未部署 | 缺失 | 参考 [Community Builder Agent](../ai/community-builder-agent.md) |
| 挖矿节点 | 已实现 / 准入规则设计中 | 主网、测试网 | 部分 | 节点软件已运行；开放准入、质押和处罚参数仍在设计，参考 [挖矿节点](../run/mining-node.md) |
| 核心节点 | 已实现 / 准入规则设计中 | 主网、测试网 | 部分 | 节点与STP服务已运行；第三方准入仍在设计，参考 [核心节点](../run/core-node.md) |
| Gas 计量 / 测试 SGAS | 测试网可用，正式 GAS 参数待定 | 公开测试网 | 草案 | 正式 GAS 资产名称、发行总量、质押和分配仍在设计，见 [网络经济](../network-economics/readme.md) |

## 每项能力需要补齐的证据

1. GitHub Repo / commit / release。
2. Demo 或测试网入口。
3. 合约地址或 txid。
4. Explorer / Indexer 证据。
5. 测试记录。
6. 已知限制。
7. 最后验证日期。

**发布状态更新：2026-11-23。页面状态：持续维护（Maintained）**
