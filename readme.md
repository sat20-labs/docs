# SAT20 与聪网

SAT20 是围绕比特币原生资产建立的协议与网络体系。它的核心目标是让 BTC、Ordinals、Runes、BRC20、ORDX 等资产在保持用户控制权的前提下，获得更低成本、更快确认、更适合应用和合约的流动环境。

聪网 SatoshiNet 是 SAT20 生态的比特币原生扩展网络。它不是托管桥，也不是独立发行一套与比特币无关的新资产系统。聪网的资产入口来自比特币主网，资产事实由 indexer 统一表达，安全边界由 STP 通道、承诺交易、惩罚交易、强制关闭和 BTC L1 可验证交易共同构成。

## 核心判断

比特币生态长期缺少一个同时满足三件事的网络：

1. 资产来自比特币主网，而不是由中心化桥托管或凭空发行。
2. 用户始终保留退出能力，Core Node 失败或作恶时仍能保护资产。
3. 网络足够便宜、快速、可编程，可以承载交易、合约、AI Agent 和更复杂的应用。

聪网要解决的就是这个问题。

## 四个基础

| 基础 | 作用 |
| --- | --- |
| STP | 让 BTC L1 资产进入、流通和退出聪网，同时保持用户控制权 |
| Indexer | 将 BTC、Ordinals、Runes、BRC20、ORDX 等主网资产统一表达为可查询、可验证的资产事实 |
| 智能合约 | 让聪网从资产流通层发展为应用网络 |
| GAS | 为聪网合约执行、交易处理和生态激励提供经济入口 |

STP 和 indexer 是资产进入聪网的基础。Indexer 说明主网上有哪些资产、在哪些 UTXO 中、状态是否确认；STP 负责把这些资产纳入用户可退出、可惩罚旧状态的通道安全边界。智能合约和 GAS 是聪网应用生态的助推器：它们让资产进入聪网之后可以参与交易、做市、支付、合约和更复杂的应用。

AI Agent 是新的使用界面。STP 的通道安全、承诺交易、惩罚交易和跨层状态对普通用户很复杂，但 Agent 可以读取证据、执行检查、调用钱包 adapter，并向用户解释下一步是否安全。

## 从哪里开始

如果你是第一次了解 SAT20：

1. 阅读 [为什么需要比特币原生扩展网络](learn/bitcoin-native.md)。
2. 阅读 [资产安全模型](learn/security-model.md)。
3. 阅读 [Indexer：比特币资产事实层](learn/indexer.md)。
4. 阅读 [STP 简介](learn/stp.md)。
5. 阅读 [智能合约与 GAS](learn/smart-contracts-and-gas.md)。
6. 阅读 [AI Agent 与用户资产控制](learn/ai-agent.md)。

如果你要构建应用：

1. 从 [开发者中心](build/readme.md) 开始。
2. 阅读 [开发者快速开始](build/quickstart.md)。
3. 选择 STP、Indexer、智能合约或 PWA adapter 的接入路径。

如果你要让 AI Agent 操作 STP：

1. 阅读 [比特币生态 AI Agent 资产安全评估规范](ai/bitcoin-agent-safety-standard.md)。
2. 阅读 [SAT20 Agent Wallet 安装与使用](ai/sat20-agent-wallet/readme.md)。
3. 安装 skill：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/install.sh | bash
```

4. 阅读 [SAT20 Agent Wallet 验证矩阵与数据缺口](ai/sat20-agent-wallet/verification-and-data-gaps.md)。

## 官方入口

- 官方文档：[docs.sat20.org](https://docs.sat20.org)
- 官网：[sat20.org](https://sat20.org)
- X：[SAT20Labs](https://x.com/SAT20Labs)
- GitHub：[sat20-labs](https://github.com/sat20-labs)

## 文档结构

| 入口 | 内容 |
| --- | --- |
| Learn | 面向所有读者，解释聪网、STP、Indexer、安全模型、智能合约、GAS 和 AI Agent |
| Use | 面向用户，说明钱包、跨层流动、资产验证和风险边界 |
| Build | 面向开发者、钱包、交易平台和基础设施团队 |
| Protocol | 面向实现者和审计者，记录 STP、SatoshiNet、ORDX、Indexer 和合约协议 |
| AI Agent | 面向 Agent 开发者和钱包 adapter，实现可验证的资产控制 |
| Ecosystem | 面向建设者、资产方、交易平台、投资机构和社区成员 |
| Roadmap | 说明聪网生态的阶段目标、公开里程碑和长期方向 |

这份文档会持续演进。我们优先保证协议事实准确、测试网证据可复核、开发者路径可执行，然后再逐步完善英文文档、官网内容和社区材料。
