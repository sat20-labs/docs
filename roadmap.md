# 路线图

SAT20 / 聪网路线图围绕一个长期目标展开：建设开放的比特币原生执行网络，让 BTC 主网资产在保持用户控制权的前提下进入可编程、低成本、可自动化的应用环境。

路线图不是价格承诺，也不是固定日期表。每一项完成状态都需要尽量对应公开代码、文档、交易、合约地址、测试记录或外部部署案例。

## Now

| 事项                              | 状态  | 验收标准                                    | 外部贡献入口                                              |
| ------------------------------- | --- | --------------------------------------- | --------------------------------------------------- |
| Community Stack 真实部署文档          | 规划中 | 至少一个社区 DEX / DAO 测试网流程可复现               | [社区技术栈](community-stack/)                           |
| 首批 DEX / DAO 试点                 | 规划中 | 有测试网入口、合约或交易证据、用户指南                     | [Builder Program](ecosystem/builder-program.md)     |
| EVM 开发者预览                       | 开发中 | RPC、Chain ID、Faucet、示例仓库和 Explorer 验证明确 | [EVM 开发者预览](build/evm-quickstart.md)                |
| 测试网用户闭环                         | 规划中 | 钱包、测试资产、第一次 Swap、Explorer 验证、退出与恢复可走通   | [Use](use/)                                         |
| Mining / Core Node 与 GAS 经济规范草案 | 设计中 | 质押、费用、处罚、退出和开放问题公开                      | [网络经济](network-economics/)                          |
| Builder Program 申请入口            | 规划中 | 有可提交表单或 GitHub Issue Template           | [Builder Program](ecosystem/builder-program.md)     |
| 协议开发可持续支持                       | 规划中 | 支持方式、资金用途、交付物和责任实体清晰                    | [支持协议开发](governance-support/support-development.md) |

## Next

| 事项                      | 状态  | 验收标准                                                    | 外部贡献入口                                                   |
| ----------------------- | --- | ------------------------------------------------------- | -------------------------------------------------------- |
| 可复制白标 DEX 工具包           | 规划中 | 前端、后台、合约、Indexer、Explorer、钱包接入可部署                       | [白标 DEX](build/white-label-dex.md)                       |
| 第三方节点和 Indexer          | 规划中 | 外部团队能运行并提供公开证据                                          | [运行网络](run/)                                             |
| EVM SDK / RPC           | 开发中 | 最小合约部署、调用、事件和 Result TX 可验证                             | [EVM 合约](protocol/contracts/evm.md)                      |
| Community Builder Agent | 开发中 | 需求收集、配置草案、人工确认、测试网部署计划和证据报告                             | [Community Builder Agent](ai/community-builder-agent.md) |
| 首批外部生态案例                | 规划中 | Built on SatoshiNet 至少收录一个外部项目                          | [Built on SatoshiNet](ecosystem/built-on-satoshinet.md)  |
| 核心英文文档                  | 规划中 | 首页、Community Stack、Today、安全、节点、GAS、Builder Program 同步英文 | docs-en                                                  |

## Later

| 事项                       | 状态  | 验收标准                      | 外部贡献入口 |
| ------------------------ | --- | ------------------------- | ------ |
| 对话式半自动部署                 | 规划中 | Agent 可生成部署配置，管理员确认后执行    |        |
| 多社区共享流动性                 | 规划中 | AMM、限价单、聚合和跨社区路由可验证       |        |
| 更开放的节点准入                 | 设计中 | 节点注册、质押、退出、处罚和公开状态页明确     |        |
| 未来基金会与公开 Treasury Policy | 规划中 | 法律结构、治理、多签、资金来源和利益冲突政策公开  |        |
| SIP 协议改进流程               | 规划中 | 提案格式、讨论流程、版本管理和治理边界明确     |        |
| 更完整的开发者支持体系              | 规划中 | Grant、赞助、服务合同、审计和文档协作机制明确 |        |

## 原则

1. 计划和现实严格分开。
2. 安全用证据表达，不用绝对口号。
3. GAS 和节点经济不使用价格、固定收益或回购叙事。
4. AI Agent 是复杂基础设施的使用与自动化界面，不是聪网存在的根本理由。
5. 开放网络的目标是让社区、开发者、节点和基础设施团队都能独立参与。
