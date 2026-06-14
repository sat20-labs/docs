# 比特币生态 AI Agent 资产安全评估规范

本文定义一套面向比特币生态项目的 AI Agent 资产安全评估规范。它不是 SAT20 专属规范，也不是投资评级。它的目标是让任何 AI Agent 在帮助用户使用比特币生态项目之前，能用同一套原则检查：用户资产是否仍由用户控制，项目是否能提供可验证证据，异常时用户是否能安全退出。

这套规范只关注资产安全，不评价价格、收益、市场热度或叙事强弱。

## 核心目标

一个用户可信赖的比特币生态 AI Agent，首先必须保护用户资产安全。它先问资产安全问题，再评估项目功能：

1. 用户是否仍持有私钥或最终控制权。
2. 资产是否托管给第三方。
3. 资产状态能否由 BTC L1、UTXO、交易、脚本、承诺交易、索引器或公开证明复核。
4. 项目方离线、失败、作恶或接口不可用时，用户是否仍能退出。
5. Agent 是否能在价值移动前自动发现风险并停止。

如果这些问题无法回答，Agent 停止替用户执行价值移动操作。

## 适用范围

本规范适用于比特币生态中的：

| 类型 | 示例 |
| --- | --- |
| 钱包 | 移动钱包、PWA 钱包、硬件钱包集成 |
| 跨层协议 | 通道、桥、侧链、L2、资产映射协议 |
| 资产协议 | Ordinals、Runes、BRC20、ORDX 等 |
| 交易平台接入 | 充值、提现、跨层入金和出金 |
| 智能合约网络 | 使用 BTC L1 资产作为入口或结算资产的应用网络 |
| AI Agent 钱包 | 通过 adapter 或 skill 操作钱包和协议的自动化代理 |

本规范不要求所有项目都采用同一种技术路线。它只要求项目能向 Agent 解释资产控制权、可验证证据和异常退出路径。

## 不可妥协原则

### 1. 私钥不进入 Agent

Agent 不保存用户助记词、私钥、硬件钱包种子或可直接转移资产的长期秘密。签名发生在钱包、硬件设备、PWA、受权限控制的本地 adapter 或用户明确授权的签名环境中。

### 2. 授权不可绕过

任何主网价值移动都必须经过用户可理解的授权。授权信息至少包括网络、资产、金额、目标地址、费用、操作类型和风险提示。

### 3. 余额不是安全证明

余额显示只是结果，不是资产安全证明。Agent 必须能追溯资产来自哪个 UTXO、交易、通道、承诺状态、合约状态或 indexer 证据。

### 4. 服务方状态不等于事实

项目方 API、Core Node、桥服务、交易平台或单个 indexer 的返回都不是最终事实。Agent 必须优先使用链上交易、可复算规则、签名、证明材料和多源查询来验证状态。

### 5. 退出路径必须可描述

如果用户资产进入某个协议、通道、L2 或合约，Agent 必须能说明用户如何退出：协商退出、强制退出、惩罚旧状态、等待时间锁、提交证明、提现到 BTC L1，或其他可验证路径。

### 6. 结果未知必须保守处理

当广播交易、跨层请求或协议协商返回 timeout、EOF、连接中断或状态未知时，Agent 不得直接重试同一价值移动操作。它必须先查询链上和协议状态，判断交易是否可能已经成功。

### 7. 主网和测试网必须隔离

故障注入、旧状态广播、惩罚演练、测试资产和不安全接口只能在测试网使用。Agent 必须拒绝在主网调用测试接口。

## 评分模型

Agent 可以按 100 分评估一个项目的资产安全成熟度：

| 维度 | 分值 | Agent 要检查什么 |
| --- | ---: | --- |
| 私钥与授权边界 | 15 | 私钥是否留在用户钱包；价值移动是否需要用户授权 |
| BTC L1 可验证性 | 15 | 资产入口、退出、UTXO、txid、确认数是否可复核 |
| 资产事实层 | 10 | 是否有 indexer、证明或可复算规则表达资产状态 |
| 退出能力 | 15 | 用户在对方离线或失败时是否能退出 |
| 作恶惩罚或风险限制 | 10 | 对旧状态、双花、无效证明、欺诈行为是否有惩罚或限制 |
| 网络不确定性处理 | 10 | timeout / EOF / reorg / mempool / 未索引时是否保守处理 |
| Agent 可操作接口 | 10 | 是否有稳定 adapter、只读查询、安全快照和事务轮询 |
| 证据可读性 | 10 | 是否能输出 txid、vout、承诺交易、状态高度、explorer/indexer 链接 |
| 测试网可验证演练 | 5 | 是否有用户和 Agent 可复现的测试网流程 |

评分解释：

| 分数 | 结论 |
| ---: | --- |
| 90-100 | Agent 可高度信任其资产安全模型，但仍需按操作逐项验证 |
| 75-89 | 安全模型较强，适合受控使用；需要补齐部分证据或接口 |
| 60-74 | 可测试或小额使用；主网大额操作需要额外人工审查 |
| 40-59 | Agent 只提供解释和风险提示，不自动执行主网价值移动 |
| 0-39 | 资产安全证据不足，Agent 应拒绝代表用户操作 |

## Agent 评估流程

Agent 评估一个项目时，应按以下步骤执行：

1. 识别资产类型：BTC、Ordinals、Runes、BRC20、ORDX 或其他协议资产。
2. 识别控制模型：自托管、多签、通道、托管桥、合约锁定、交易平台账户或其他模型。
3. 查询链上事实：txid、vout、地址、脚本、确认数、是否花费、协议事件是否有效。
4. 查询协议状态：通道、合约、L2、桥、订单或 pending 事务状态。
5. 检查用户控制权：私钥、签名权限、承诺交易、退出交易、惩罚材料或提现权限。
6. 检查异常路径：对方离线、接口不可用、reorg、交易未知、旧状态、无效证明。
7. 给出评分和阻断项：列出可以继续的操作、必须停止的操作和缺失证据。

## Agent 输出格式

Agent 应输出结构化评估，便于用户、钱包和其他 Agent 复核：

```json
{
  "standard": "bitcoin-agent-asset-safety",
  "version": "0.1",
  "project": "example",
  "network": "mainnet|testnet",
  "score": 0,
  "level": "BLOCKED|TEST_ONLY|CONTROLLED_USE|HIGH_CONFIDENCE",
  "dimensions": [
    {
      "name": "private_key_and_authorization",
      "score": 0,
      "max": 15,
      "evidence": [],
      "missing": [],
      "risk": ""
    }
  ],
  "must_stop": [],
  "allowed_actions": [],
  "next_checks": []
}
```

Agent 输出分数，同时附带证据和缺口。

## SAT20 / 聪网评估

以下评估使用同一套规范审视 SAT20 / 聪网。它不是最终结论，而是当前文档和测试网演练基础上的可更新评估。

| 维度 | 分值 | SAT20 当前评估 |
| --- | ---: | --- |
| 私钥与授权边界 | 14 / 15 | 推荐形态是 SAT20 PWA Wallet 保存私钥和授权，SAT20 Agent Wallet 只通过 adapter 发起请求，不保存助记词 |
| BTC L1 可验证性 | 14 / 15 | STP funding、splicing、close、punish 都能回到 BTC L1 txid、UTXO 和承诺交易验证 |
| 资产事实层 | 9 / 10 | BTC L1 indexer + 聪网 L2 indexer 共同表达资产事实；L2 indexer 随节点集成，Core Node 要求自己的 L1 indexer |
| 退出能力 | 14 / 15 | 用户持有最新承诺交易；Core Node 离线时可强制关闭；CSV 后可 sweep |
| 作恶惩罚或风险限制 | 10 / 10 | 对已撤销旧状态有 punish 机制，测试网已完成旧 Core Node commitment 惩罚演练 |
| 网络不确定性处理 | 8 / 10 | 文档和 skill 已明确未知结果必须按“可能成功”处理；仍需更多主网前长时间运行验证 |
| Agent 可操作接口 | 8 / 10 | `sat20-agent-wallet` 已定义 adapter contract、安全快照、commitment export、punish、transaction 轮询；PWA adapter 还需继续产品化 |
| 证据可读性 | 8 / 10 | 测试网已形成 txid、commit height、punish tx 和 indexer 证据；还需统一 explorer/indexer 链接包 schema |
| 测试网可验证演练 | 5 / 5 | 已完成 STP 通道、splicing、unlock/lock、旧 commitment 广播和 punish drill |

综合评分：`90 / 100`。

评估等级：`HIGH_CONFIDENCE`，含义是 SAT20 的资产安全模型具备较强的可验证基础，Agent 可以在证据完整、钱包授权明确、网络一致的前提下辅助用户操作；主网大额操作仍应逐项执行安全快照和用户确认。

## SAT20 的关键证据

SAT20 获得高分的原因不是“相信 Core Node”，而是以下证据可由 Agent 检查：

1. 资产进入用户与 Core Node 的 2-of-2 通道地址。
2. 用户钱包持有最新承诺交易。
3. 承诺高度单调前进。
4. 已撤销旧状态有 punish coverage。
5. Core Node 广播旧状态时，用户钱包可以构造并广播惩罚交易。
6. L1/L2 indexer 能把 BTC L1 UTXO、ascend、descend、通道状态和聪网 UTXO 串成证据链。
7. SAT20 Agent Wallet 不接触私钥，只通过钱包 adapter 操作。

## SAT20 仍需补齐的内容

为了让任何第三方 Agent 更稳定地使用这套规范评估 SAT20，还需要继续补齐：

1. PWA adapter 的完整 `wallet.transaction` / `stp.transaction` 轮询 schema。
2. 每个 txid 的 L1/L2 explorer URL、indexer URL 和状态字段标准化。
3. `stp.safety_snapshot` 在 PWA 中的产品化展示。
4. 更完整的主网前长时间运行、reorg、未索引、Core Node 离线和重复请求测试。
5. 面向普通用户的风险解释 UI：为什么当前可继续、为什么必须停止、缺失哪类证据。

## Agent 对 SAT20 的默认动作策略

当 Agent 使用 SAT20 Agent Wallet 操作 SAT20 / STP 时，应默认执行：

1. 先运行资产安全评估，再安装或调用 SAT20 Agent Wallet。
2. 价值移动前读取 `stp.safety_snapshot`。
3. 如果缺少最新承诺交易、punish coverage、L1/L2 indexer 证据或用户授权，停止操作。
4. 如果网络结果未知，进入轮询和恢复流程，不立即重试。
5. 如果 Core Node 离线，优先给出 force-close plan。
6. 如果 Core Node 广播旧状态，优先构造并广播 punish tx。

这就是 SAT20 Agent Wallet 应建立在本规范之上的原因：Agent 不是为了替用户冒险自动化，而是为了让用户资产安全变得可读、可验证、可执行。
