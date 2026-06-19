# 开发者快速开始

本文给出开发者进入 SAT20 / 聪网生态的最短路径。

## 先选择一个可运行目标

| 目标 | 指南 |
| --- | --- |
| 部署第一个 EVM 合约 | [EVM Quickstart](evm-quickstart.md) |
| 搭建社区 DEX / DAO | [Community DEX / DAO Quickstart](community-dex-quickstart.md) |
| 部署社区 DAO | [DAO Quickstart](dao-quickstart.md) |
| 部署 AMM 池 | [AMM Pool Quickstart](amm-pool-quickstart.md) |
| 部署 Launchpad | [Launchpad Quickstart](launchpad-quickstart.md) |
| 部署限价单模块 | [Limit Order Quickstart](limit-order-quickstart.md) |
| 运行 Core Node、Indexer、Explorer | [Infrastructure Quickstart](infrastructure-quickstart.md) |
| 集成 Wallet SDK | [Wallet SDK Quickstart](wallet-sdk-quickstart.md) |
| 搭建白标 DEX | [White-label DEX](white-label-dex.md) |
| 构建 SatoshiNet AI Agent | [AI Agent Quickstart](ai-agent-quickstart.md) |
| 查看合约模板状态 | [合约模板目录](contract-template-catalog.md) |
| 集成钱包或交易平台 | [交易平台与钱包接入](exchange-and-wallet.md) |

每个 quickstart 都会逐步补齐环境要求、当前支持版本、测试网 RPC、Chain ID、测试资产、命令行步骤、配置示例、预期输出、Explorer 验证方式、常见错误和生产环境注意事项。

## 选择你要构建什么

| 你要构建 | 起点 |
| --- | --- |
| STP 钱包或客户端 | `sat20-agent-wallet` skill 与 adapter contract |
| Indexer / 数据服务 | L1/L2 indexer、资产事实层和多协议资产状态 |
| 聪网应用 | 智能合约文档与测试网 |
| 交易平台接入 | Indexer、STP 状态和充值提现流程 |
| AI Agent | SAT20 Agent Wallet skill、PWA adapter、安全验证矩阵 |
| 区块浏览器或数据服务 | L1/L2 indexer 和交易状态模型 |

## 安装钱包与 Agent Skill

面向普通用户和主网场景，先安装并初始化 SAT20 PWA Wallet，再安装 SAT20 Agent Wallet skill。PWA 钱包是私钥、助记词、签名、授权弹窗和通道数据库的安全边界；skill 是 Agent 的操作知识和工作流。

安装 SAT20 PWA Wallet：

```text
https://sat20.org/pwa/?install=1
```

在 PWA 内创建或导入钱包、完成备份并解锁后，再安装 skill：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/install.sh | bash
```

安装后，Agent 应通过 `SAT20_ADAPTER_URL` 或 `SAT20_CLIENT_CMD` 调用钱包 adapter。

## 实现一个 Adapter

最小 adapter 应支持：

1. `wallet.status`
2. `stp.status`
3. `stp.safety_snapshot`
4. `stp.open`
5. `stp.splicing_in`
6. `stp.unlock`
7. `stp.lock`
8. `stp.splicing_out`
9. `stp.transaction`

完整契约见 [adapter contract](../ai/sat20-agent-wallet/skills/sat20-agent-wallet/references/adapter-contract.md)。

## 接入 Indexer

如果你构建钱包、交易平台、浏览器或 Agent，先阅读 [Indexer 接入与资产事实层](indexer.md)。最小实现应能查询 L1 UTXO 资产、交易确认、花费状态、L2 UTXO、ascend / descend 事件和通道相关状态。

当前接口仍在快速迭代，先使用 [API 源码地图](api-source-map.md) 定位权威源码入口。旧 Swagger 只覆盖早期 ORDX indexer 的一部分接口，不作为当前 SAT20 / 聪网完整 API 文档。

## 测试网验收

开发者至少应在测试网上验证：

1. 打开普通 client-core 通道。
2. splicing-in 一种协议资产。
3. unlock / lock 往返。
4. splicing-out 回 BTC L1。
5. 导出承诺交易。
6. 验证 punish coverage。
7. 处理未知网络结果。
8. 通过 indexer 复核 L1/L2 资产证据链。

验收清单见 [STP 第三方客户端实现验收清单](../protocol/stp/implementation-checklist.md)。

**页面状态：规划中（Planning）**
