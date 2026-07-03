# SatoshiNet Today：当前可用能力

本文展示聪网当前已经具备或正在建设的能力。它不是营销列表，而是公开状态索引。

## 状态维度

| 维度   | 说明                                                                  |
| ---- | ------------------------------------------------------------------- |
| 实现状态 | 已实现（Implemented）、开发中（In Development）、规划中（Planned）、实验性（Experimental） |
| 可用环境 | 公开测试网、有限测试、主网、未部署                                                   |
| 文档证据 | 完整、部分、缺失、协议规范                                                       |

## 能力矩阵

| 模块                        | 实现状态      | 可用环境     | 文档证据 | 公开证据 / 下一步                                                     |
| ------------------------- | --------- | -------- | ---- | -------------------------------------------------------------- |
| SatoshiNet 核心节点           | 已实现       | 公开测试网    | 部分   | 参考 [运行网络](../run/)                                             |
| L1 Indexer                | 已实现       | 可用       | 部分   | 参考 [Indexer 接入](../build/indexer.md)                           |
| L2 Indexer                | 已实现       | 公开测试网    | 部分   | 参考 [API 源码地图](../build/api-source-map.md)                      |
| Explorer                  | 已实现       | 测试网      | 部分   | 补充统一入口和验证案例                                                    |
| SAT20 PWA Wallet          | 已实现       | 测试网      | 部分   | [安装 PWA Wallet](https://sat20.org/pwa/?install=1)              |
| Wallet SDK                | 已实现       | 可用       | 部分   | 参考 [交易平台与钱包接入](../build/exchange-and-wallet.md)                |
| STP / Transcend           | 已实现       | 公开测试网    | 部分   | 参考 [STP 技术白皮书](../protocol/stp/)                               |
| AMM                       | 已实现       | 测试网      | 部分   | 补充 Demo、合约地址和部署指南                                              |
| 限价单                       | 已实现       | 测试网      | 部分   | 补充 Demo、合约地址和部署指南                                              |
| Launchpad                 | 已实现       | 测试网      | 部分   | 补充使用手册和案例                                                      |
| DAO / 社区基金                | 已实现       | 有限测试网    | 部分   | 补充模板、UID、捐献、空投和治理流程                                            |
| EVM Runtime               | 开发中       | 内部 / 测试网 | 协议规范 | 参考 [EVM 合约](../protocol/contracts/evm.md)                      |
| Natural Language Contract | 实验性       | 内部 / 测试网 | 协议规范 | 参考 [自然语言合约](../protocol/contracts/agent.md)                    |
| Community Builder Agent   | 规划中 / 实验性 | 未部署      | 缺失   | 参考 [Community Builder Agent](../ai/community-builder-agent.md) |
| 挖矿节点                      | 开发中       | 测试网      | 缺失   | 参考 [挖矿节点](../run/mining-node.md)                               |
| 核心节点                      | 开发中       | 测试网      | 缺失   | 参考 [核心节点](../run/core-node.md)                                 |
| GAS 经济                    | 设计中       | 未部署      | 草案   | 参考 [网络经济](../network-economics/)                               |

## 每项能力需要补齐的证据

1. GitHub Repo / commit / release。
2. Demo 或测试网入口。
3. 合约地址或 txid。
4. Explorer / Indexer 证据。
5. 测试记录。
6. 已知限制。
7. 最后验证日期。

**页面状态：规划中（Planning）**
