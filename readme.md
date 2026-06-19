# SAT20 / 聪网

## 聪网是一条开放的比特币原生执行网络

聪网 SatoshiNet 让 BTC 社区能够建设、拥有并运行自己的金融基础设施。Bitcoin L1 提供资产来源、最终结算和争议边界；Indexer 提供可查询、可复核的资产事实；STP 提供跨层资产控制、退出和旧状态惩罚路径；SatoshiNet 提供交易、智能合约和应用执行；钱包和 AI Agent 提供用户授权、安全检查和交互入口。

SAT20 是围绕比特币原生资产形成的协议和开源技术体系。聪网是 SAT20 体系中的开放执行网络。

- [为我的社区搭建 DEX / DAO](community-stack/readme.md)
- [查看当前能力与证据](ecosystem/satoshinet-today.md)
- [运行节点与基础设施](run/readme.md)
- [了解 GAS 与节点经济](network-economics/readme.md)
- [加入 Builder Program](ecosystem/builder-program.md)

## 名称与关系

| 名称 | 定位 |
| --- | --- |
| SAT20 | 围绕比特币原生资产形成的协议和开源技术体系 |
| SatoshiNet / 聪网 | 开放的比特币原生执行网络 |
| Indexer | BTC L1 与聪网资产事实层 |
| STP / Transcend | BTC L1 与聪网之间的跨层资产控制协议 |
| ORDX | SAT20 体系中的聪本位资产协议 |
| GAS | 聪网原生的网络费用与安全质押资产 |

## 为什么需要聪网

Bitcoin L1 适合承担稀缺资产、最终结算和长期安全，但不适合承载所有高频交易与复杂应用。扩展执行是比特币规模化发展的自然方向，关键问题是：如何在获得更高性能的同时，保留与比特币资产事实、用户控制权和退出路径的联系。

聪网探索的是一条开放路径：

1. 资产来自 Bitcoin L1。
2. 资产事实可以追溯和复核。
3. 用户保留异常情况下的退出与保护路径。
4. 应用在更快、成本更低、可编程的网络中执行。
5. 社区和第三方能够独立运行基础设施，而不是永久依赖 SAT20 Labs。

## 从 Bitcoin 事实到可编程执行

```text
Bitcoin L1
   ↓
Indexer：资产事实
   ↓
STP：控制与退出
   ↓
SatoshiNet：交易与合约执行
   ↓
DEX · DAO · 钱包 · Explorer · AI Agent
```

## 当前能做什么

| 能力 | 当前用途 | 入口 |
| --- | --- | --- |
| 社区基础设施 | 为 BTC 社区规划节点、Indexer、Explorer、钱包、DEX、DAO 和运营后台 | [社区技术栈](community-stack/readme.md) |
| 资产进入聪网 | 通过 Indexer 识别 BTC L1 资产事实，通过 STP 将资产纳入用户可退出的通道安全边界 | [STP 简介](learn/stp.md) |
| 用户使用 | 安装钱包、进入聪网、完成第一次 Swap、使用 Explorer 验证交易 | [Use](use/readme.md) |
| 开发者构建 | 接入 Indexer、钱包、STP、合约和社区 DEX / DAO | [Build](build/readme.md) |
| 节点运行 | 运行挖矿节点、核心节点、Indexer、Explorer、RPC 和监控服务 | [运行网络](run/readme.md) |
| 网络经济 | 理解 GAS、费用流、节点质押、激励和设计中参数 | [网络经济](network-economics/readme.md) |
| AI Agent 操作 | 让 Agent 在不持有私钥、不绕过钱包授权的前提下执行资产安全检查和操作 | [AI Agent](ai/readme.md) |
| 生态合作 | 申请试点、贡献工具、提供流动性、运行节点或支持协议开发 | [Ecosystem](ecosystem/readme.md) |

## 选择你的角色

| 你是谁 | 从这里开始 |
| --- | --- |
| 我运营一个 BTC 社区 | [社区路径](start-here/btc-community.md) |
| 我是 Solidity / EVM 开发者 | [开发者路径](start-here/developers.md) |
| 我运行基础设施 | [基础设施路径](start-here/infrastructure.md) |
| 我是钱包或交易平台 | [钱包与交易平台路径](start-here/wallet-exchange.md) |
| 我是 AI Agent 开发者 | [AI Agent 路径](start-here/ai-agent-builders.md) |
| 我想提供流动性 | [流动性路径](start-here/liquidity.md) |

## 安全用证据表达

聪网不采用中心化托管桥作为核心跨层模型。用户保护能力依赖 STP 通道状态、有效承诺交易、惩罚覆盖、钱包备份、Indexer 证据和 BTC L1 可执行路径。

用户和 Agent 需要能验证：

1. 资产位于 BTC L1、STP 通道、聪网个人地址还是合约地址。
2. 关键交易能追溯到 txid、vout、height 和 confirmations。
3. 钱包持有最新承诺交易和必要备份。
4. 旧状态有惩罚覆盖。
5. Core Node 离线、拒绝服务或作恶时，用户仍有退出或保护路径。

## 状态与证据

Docs 使用统一状态表达：

| 状态 | 含义 |
| --- | --- |
| 已实现（Implemented） | 代码与核心流程已经存在，但不自动代表完整生产成熟度 |
| 测试网（Testnet） | 已有可复现测试网流程 |
| 开发中（In Development） | 代码正在推进，尚不承诺完整可用 |
| 设计中（Design in Progress） | 规则、参数或治理尚未定稿 |
| 规划中（Planned） | 方向明确但未进入可验证实现 |
| 实验性（Experimental） | 研究性功能，可能改变或取消 |

每一项状态都应尽量链接到代码、文档、Demo、Explorer、合约地址、测试交易或验证记录。

## 官方入口

- 官方文档：[docs.sat20.org](https://docs.sat20.org)
- 官网：[sat20.org](https://sat20.org)
- X：[SAT20Labs](https://x.com/SAT20Labs)
- GitHub：[sat20-labs](https://github.com/sat20-labs)

这份文档服务用户、开发者、社区、节点运营者、钱包、交易平台、AI Agent、基础设施团队和战略合作伙伴。官网负责结果、机会和行动路径；Docs 负责协议事实、实现、证据和风险边界。
