# 开发者中心

Build 部分面向开发者、钱包、交易平台、Indexer、智能合约开发者和 AI Agent 构建者。

聪网生态需要的不只是一个协议，还需要完整的开发者系统：钱包、SDK、Indexer、合约模板、测试网、文档、示例和社区支持。STP 和 indexer 共同构成资产进入聪网的基础：前者保障控制权，后者提供资产事实。

## 快速开始

| 你要完成的第一件事 | 入口 |
| --- | --- |
| 理解 EVM 开发者预览 | [EVM 开发者预览](evm-quickstart.md) |
| 查看 EVM 样本合约 | [EVM 样本合约](evm-sample-contracts.md) |
| 搭建社区 DEX / DAO | [社区 DEX / DAO Quickstart](community-dex-quickstart.md) |
| 部署社区 DAO | [DAO Quickstart](dao-quickstart.md) |
| 部署智能合约模板 AMM 池 | [AMM Pool Quickstart](amm-pool-quickstart.md) |
| 部署 Launchpad | [Launchpad Quickstart](launchpad-quickstart.md) |
| 部署智能合约模板限价单模块 | [Limit Order Quickstart](limit-order-quickstart.md) |
| 运行核心节点、Indexer 或 Explorer | [基础设施 Quickstart](infrastructure-quickstart.md) |
| 集成 Wallet SDK | [Wallet SDK Quickstart](wallet-sdk-quickstart.md) |
| 搭建白标 DEX | [White-label DEX](white-label-dex.md) |
| 构建 SatoshiNet AI Agent | [AI Agent Quickstart](ai-agent-quickstart.md) |
| 查看合约模板状态 | [合约模板目录](contract-template-catalog.md) |
| 集成钱包或交易平台 | [交易平台与钱包接入](exchange-and-wallet.md) |
| 查询当前权威 API 源码入口 | [API 源码地图](api-source-map.md) |

带状态标签的页面表示内容仍在规划或对应系统仍在开发，保留入口便于后续逐步补齐。独立 Quickstart 需要补齐环境要求、测试网地址、示例代码、预期输出、Explorer 验证和常见错误。

## 开发者路径

| 目标 | 路径 |
| --- | --- |
| 构建 STP 客户端 | 阅读 STP 客户端接入指南，实现 JSON adapter，并用测试网验收清单验证 |
| 接入钱包 | 使用 PWA Wallet adapter 或实现自己的安全钱包边界 |
| 接入交易平台 | 关注充值提现、L1/L2 状态、通道状态和 indexer |
| 查找 API 入口 | 使用 API 源码地图定位 L1 indexer、聪网 RPC、L2 indexer 和钱包 WASM/PWA adapter |
| 接入 Indexer | 理解 BTC L1 与聪网 L2 的资产事实层，处理多协议资产、确认数、reorg 和跨层证据 |
| 构建合约应用 | 从模板合约和 GAS 模型开始 |
| 构建 AI Agent | 先接入 PWA 钱包安全边界，再安装 SAT20 Agent Wallet skill，实现安全验证和授权流程 |
| 运行基础设施 | 了解 Core Node、indexer、explorer 和测试网 |

## 开始

1. 阅读 [开发者快速开始](quickstart.md)。
2. 选择一个可运行 quickstart，先在测试网完成一次真实操作。
3. 阅读 [API 源码地图](api-source-map.md)，确认当前权威源码入口。
4. 阅读 [Indexer 接入与资产事实层](indexer.md)。
5. 阅读 [STP 第三方客户端接入指南](../protocol/stp/client-integration.md)。
6. 阅读 [STP 第三方客户端实现验收清单](../protocol/stp/implementation-checklist.md)。
7. 如果你要做交易平台或钱包，阅读 [交易平台与钱包接入](exchange-and-wallet.md)。

## 原则

1. Core Node 状态不是最终事实。
2. 单个 indexer 响应不是不可质疑的最终事实；关键操作需要 txid、vout、height、confirmations 和跨源证据。
3. 余额显示不是资产安全证明。
4. 主网操作保留用户授权。
5. 缺少承诺交易或惩罚覆盖时停止价值移动。
6. 对结果未知的网络错误，按“可能已经成功”处理。
