# 路线图

SAT20 / 聪网路线图围绕一个长期目标展开：建设比特币原生扩展网络，让 BTC 主网资产在保持用户控制权的前提下进入可编程、低成本、可自动化的应用环境。

路线图不是价格承诺，也不是固定日期表。它记录当前优先级、阶段目标和需要公开验证的里程碑。

## Now / Next / Later

| 阶段 | 当前重点 | 外部建设者可以参与什么 |
| --- | --- | --- |
| Now | Community Stack 文档、首批社区 DEX / DAO 试点、EVM Runtime 测试、SAT20 Agent Wallet、Builder Program 开放 | 申请社区试点、部署第一个合约、运行基础设施、提交钱包或 Agent 集成 |
| Next | Community Builder Agent、钱包通信机制、EVM SDK/RPC 工具链、完整自部署工具包、更多流动性和 Explorer 伙伴 | 贡献部署工具、合约模板、SDK、索引器、Explorer、教程和测试网案例 |
| Later | 对话式半自动部署、社区运营 Agent、多社区流动性协作、更完整的开发者支持和更高程度基础设施去中心化 | 成为长期生态项目、区域社区、节点网络、审计和治理参与者 |

每个公开里程碑都应尽量给出当前状态、参与方式、验收标准、公开证据和外部可贡献点。

## 阶段一：STP + Indexer 资产基础

目标：证明资产进入聪网不是托管桥，而是由统一资产索引和用户可验证通道共同支撑的跨层资产系统。Indexer 负责表达 BTC L1 上的资产事实，STP 负责让这些资产进入可退出、可惩罚旧状态的通道安全边界。

重点：

1. BTC L1 多协议资产的统一索引。
2. L1/L2 ascend、descend 和通道资产证据链。
3. STP 通道生命周期。
4. splicing-in / splicing-out。
5. unlock / lock / lock-with-expand。
6. commitment export。
7. punish coverage。
8. 测试网旧承诺广播和惩罚演练。
9. SAT20 Agent Wallet skill 和 PWA adapter。

当前文档：

- [Indexer：比特币资产事实层](learn/indexer.md)
- [Indexer 接入与资产事实层](build/indexer.md)
- [STP 技术白皮书](protocol/stp/readme.md)
- [SAT20 Agent Wallet 资产安全控制指南](ai/sat20-agent-wallet/asset-safety.md)
- [SAT20 Agent Wallet 安装与使用](ai/sat20-agent-wallet/readme.md)

## 阶段二：智能合约与 GAS

目标：让聪网从资产流通网络发展为应用网络。

重点：

1. 模板合约。
2. AMM、限价单、稳定币、支付等基础应用。
3. GAS 费用模型。
4. 合约 indexer 与 L2 状态索引。
5. 合约开发者工具。
6. EVM 兼容路径。
7. 自然语言合约和 AI Agent 合约探索。

当前文档：

- [智能合约与 GAS](learn/smart-contracts-and-gas.md)
- [智能合约协议](protocol/contracts/readme.md)
- [网络费用与 GAS](ecosystem/gas.md)

## 阶段三：开发者和基础设施

目标：降低外部团队接入成本，让钱包、交易平台、Indexer、浏览器、Agent 和应用开发者能参与建设。

重点：

1. 开发者快速开始。
2. 钱包与交易平台接入。
3. L1/L2 Indexer API、L2 节点内置索引和 L1 事实分布式验证路线。
4. PWA Wallet adapter。
5. 多语言 STP client。
6. 测试网工具和示例应用。

当前文档：

- [开发者中心](build/readme.md)
- [开发者快速开始](build/quickstart.md)
- [交易平台与钱包接入](build/exchange-and-wallet.md)

## 阶段四：生态增长

目标：吸引 BTC 社区、开发者、节点运营者、交易平台、钱包、流动性伙伴和 AI Agent 团队进入聪网生态。

重点：

1. Builder Program。
2. Community Stack。
3. 首批社区 DEX / DAO 试点。
4. 资产社区接入。
5. 交易平台、钱包和做市商合作。
6. Indexer / Explorer / Core Node 节点生态。
7. 官方内容、视频、教程和社区 FAQ。
8. X 与 Telegram 社区建设。

当前文档：

- [Ecosystem](ecosystem/readme.md)
- [Community Stack](community-stack/readme.md)
- [SatoshiNet Today](ecosystem/satoshinet-today.md)
- [Builder Program](ecosystem/builder-program.md)
- [当前生态需求](ecosystem/ecosystem-needs.md)

## 长期方向

聪网的长期方向是成为比特币资产的应用层：

1. 资产事实由 BTC L1 和 indexer 表达。
2. 资产控制权由 STP 保障。
3. 应用执行由聪网智能合约承载。
4. 网络资源由 GAS 定价。
5. 用户体验由钱包和 AI Agent 改善。
6. 生态增长由开发者、资产方、交易平台、Indexer 和社区共同推动。

每个阶段都必须有可验证证据：交易、代码、测试网演练、API、文档和用户可复现流程。
