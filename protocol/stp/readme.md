# STP 技术白皮书

STP（Satoshi Transcending Protocol）是连接比特币主网与聪网 SatoshiNet 的资产通道协议。它的目标不是建立托管桥，而是让用户把 BTC L1 上的资产纳入由用户和 Core Node 共同控制的通道，并在聪网上获得快速、低成本、可合约化的流动能力。

本文只描述协议语义，不绑定任何代码仓库、接口名称或开发语言。任何钱包、SDK、PWA、CLI 或 AI Agent 适配器，都可以依据本文实现 STP 客户端并接入兼容的 Core Node。

## 摘要

STP 的安全基础与闪电网络相同，来自 RSMC：2-of-2 通道、多版本承诺交易、撤销秘密、CSV 延迟和惩罚交易。用户不需要信任 Core Node 一定在线或诚实；用户需要持有最新承诺交易，并具备在 peer 广播旧状态时构造惩罚交易的能力。

STP 与传统闪电网络的区别在于：

1. STP 支持多资产：BTC、ORDX、Runes、BRC20 等 BTC L1 原生资产都可以进入通道。
2. STP 支持动态容量：通道可以通过 splicing-in、splicing-out、expand 和 lock-with-expand 调整资产集合。
3. STP 连接 SatoshiNet：资产进入聪网后可以在 L2 UTXO、合约和 GAS 经济中流通。
4. STP 依赖 indexer 作为资产事实层：L1 indexer 解析 BTC 主网资产，L2 indexer 解析聪网 ascend、descend、通道和合约状态。

SAT20 的资产基础应理解为 STP + Indexer。Indexer 告诉客户端资产是什么、在哪里、是否有效；STP 决定这些资产如何进入、流通、退出，以及用户如何在异常情况下保护控制权。

## 协议目标

STP 必须满足以下目标：

1. 用户最终控制权：通道资产由用户和 Core Node 共同控制，用户始终应持有可广播的最新承诺交易。
2. BTC L1 退出安全：Core Node 离线、拒绝服务或作恶时，用户可以通过强制关闭和后续清扫取回资产。
3. 旧状态惩罚：Core Node 广播旧承诺交易时，用户可以通过惩罚交易夺回违规输出。
4. 多资产一致性：白聪、ORDX、Runes、BRC20 等资产数量和协议规则在 L1、通道和 L2 之间保持一致。
5. 可复核资产事实：客户端必须通过 L1/L2 indexer 复核 UTXO、资产、ascend、descend、确认数和通道状态。
6. 语言无关互操作：客户端实现只需遵守消息、签名、交易、状态和恢复规则，不应依赖某个特定实现。

## 聪网节点角色

历史文档或接口中出现的 `STP Server`，在协议角色上应理解为 Core Node 对外提供的 STP 服务能力。聪网主要包括以下节点：

| 节点 | 职责 |
| --- | --- |
| Bootstrap Node | 辅助 Core Node 发现和准入 |
| Core Node | 提供 STP 服务，与钱包建立私人通道，协签通道交易，维护服务侧通道状态，并运行或配置 L1 indexer |
| Mining Node | 参与聪网出块，不提供 STP 通道服务 |
| Wallet Client | 用户钱包或客户端，连接 Core Node，持有私钥、通道状态、承诺交易和惩罚材料 |

普通用户连接 Core Node 打开私人通道，不需要质押资产。只有节点连接 Bootstrap Node 并准备以 Core Node 身份参与网络服务时，才涉及核心节点准入和质押要求。

## 通道模型

STP 通道是用户与 Core Node 之间的 2-of-2 资产控制关系。通道地址上的 BTC L1 UTXO 代表通道的链上控制边界；聪网中的 L2 状态代表通道资产在 SatoshiNet 中的流动状态。

一个通道至少包含：

| 对象 | 含义 |
| --- | --- |
| 通道地址 | 用户公钥与 Core Node 公钥生成的 2-of-2 地址 |
| Channel Point | 当前承诺交易花费的 L1 通道 outpoint |
| 承诺高度 | 通道状态更新次数，必须单调递增 |
| Local Commitment | 本方可在异常时广播的最新退出交易 |
| Remote Commitment | 对方持有的承诺交易版本，用于监控旧状态 |
| Revocation 材料 | 旧 remote commitment 被广播时构造惩罚交易所需的材料 |
| CSV 延迟 | 强制关闭后给对方惩罚的时间窗口 |
| Pending 事务 | 尚未收敛的 open、splicing、lock、unlock、close 等事务 |

客户端必须在每次承诺状态更新后持久化最新承诺交易、承诺高度、撤销材料、channel point 和 pending 事务。只保存余额不足以证明用户仍然控制资产。

## 资产模型

STP 不重新定义 BTC L1 资产协议，而是把它们纳入通道和聪网状态。

| 资产 | STP 处理原则 |
| --- | --- |
| 白聪 | BTC L1 受 dust 和 fee 约束；SatoshiNet L2 可以存在 0 聪 UTXO |
| ORDX | 必然绑定聪，进入聪网时按 `bindingSat` 计算承载关系；`ordx:o` 类型对象不 ascend |
| Runes | L2 不需要绑定聪，可以由 0 聪 enUTXO 携带；L1 输出仍遵守 BTC 规则 |
| BRC20 | L2 不需要绑定聪；L1 进入或退出可能需要 transfer inscription 和相关交易包 |

如果一个 L1 UTXO 同时携带多种可 ascend 资产，STP 只处理用户在操作中明确指定的一种资产。未指定资产不会进入聪网。客户端内部选币通常避开多资产 UTXO；如果必须使用，需要在用户授权前清楚提示哪些资产不会 ascend。

## 通道状态

通道状态可以抽象为：

| 状态 | 含义 |
| --- | --- |
| `INIT` | 通道协商开始 |
| `FUNDING_BROADCASTED` | BTC L1 funding 交易已广播 |
| `FUNDING_CONFIRMED` | funding 交易已确认 |
| `ANCHOR_BROADCASTED` | 聪网 ascend / anchor 交易已广播 |
| `ANCHOR_CONFIRMED` | ascend / anchor 已确认 |
| `READY` | 通道可执行普通价值移动 |
| `CLOSING` | 协商关闭中 |
| `FORCE_CLOSING` | 一方广播承诺交易强制关闭 |
| `SWEEPING` | CSV 到期后清扫资产 |
| `CLOSED` | 通道关闭完成 |
| `PUNISHED` | 旧状态被惩罚，通道终止 |

普通价值移动只能在 `READY` 状态发起。存在 pending 事务、承诺覆盖未知、链上状态不明或 indexer 未收敛时，客户端应停止新的 splicing、lock、unlock 或 close。

## 协议操作

### Open

Open 建立用户与 Core Node 的私人通道。普通用户不需要质押资产。流程包括通道参数协商、L1 funding、初始承诺交易签名、funding 确认、L2 ascend / anchor 和通道 ready。

客户端必须校验：

1. 通道地址由用户公钥和 Core Node 公钥生成。
2. funding 输出支付到正确通道地址。
3. 服务费、手续费和找零符合用户授权。
4. 初始承诺交易可被用户单方面广播。
5. Core Node 签名有效。
6. L1 funding 与 L2 ascend / anchor 可以通过 indexer 复核。

### Splicing-in / Expand

Splicing-in 将新的 BTC L1 资产纳入已有通道。它可能包含 L1 转入通道地址、L2 ascend / anchor、承诺状态更新和通道容量变化。

Expand 用于资产已经位于通道地址，但尚未纳入当前承诺状态的场景。典型情况包括：用户已经把资产转入通道地址、前序 splicing-in 被网络异常打断、或通道恢复时发现通道地址上存在尚未由当前承诺覆盖的资产。

客户端原则上不要求用户手动选择资产 UTXO 或 fee UTXO。钱包 adapter 应根据资产、金额、网络费和协议规则内部选择或构造合适输入。BRC20 如果没有合适 transfer UTXO，adapter 可以内部铸造 transfer inscription 再完成 splicing-in。

### Unlock

Unlock 将通道中属于用户的资产释放到聪网个人地址。释放后，资产由用户在 L2 上单签控制，可用于转账、合约或后续 lock。

Unlock 会推进承诺高度。客户端必须在操作前确认通道 ready、无 pending 事务、最新承诺交易存在、惩罚覆盖可证明，并在操作后复核 commit height 单调增加。

### Lock / Lock-with-expand

Lock 将聪网个人地址上的资产重新纳入通道保护。Lock 后，资产重新进入 RSMC 承诺安全边界。

Lock-with-expand 用于通道容量不足或当前通道资产集合不足以覆盖目标资产的场景。它应帮助用户把资产重新纳入通道控制权，是保障用户随时恢复资产控制的重要能力。

Lock 和 unlock 一样，原则上不要求用户提供输入 UTXO 或 fee UTXO。adapter 应内部选择 L2 资产输入，并返回可验证的事务证据。

### Splicing-out

Splicing-out 将通道资产退出到 BTC L1 地址。它通常包含通道承诺更新、L2 descend / de-anchor、L1 输出和后续 indexer 确认。

客户端必须校验：

1. 退出资产、金额和目标地址符合用户授权。
2. L2 descend 与 L1 输出可以被 indexer 关联。
3. L1 输出满足对应资产协议的转移规则。
4. 手续费输入来自合法来源；除白聪 unlock 的内部例外外，发起方 fee 不应使用通道地址 UTXO。

### Close / Force Close / Sweep

Close 是双方协商关闭通道。Force close 是一方广播最新承诺交易单方面关闭。Sweep 是 CSV 到期后清扫属于自己的延迟输出或通道地址上的可清扫资产。

当 Core Node 不可用时，客户端必须能给出 force close plan：可广播的 local commitment、CSV 延迟、后续 sweep 条件和预计风险。Agent 不应在缺少承诺交易或 sweep 路径时建议用户继续依赖该通道。

### Punish

如果 Core Node 广播旧 remote commitment，客户端应识别该 commitment 已被撤销，并使用对应撤销材料构造惩罚交易。惩罚交易的目标是让作恶方无法通过旧状态获利。

客户端应在每次承诺高度推进后更新 punish coverage，并向上层返回：

1. 是否存在已撤销 remote commitment。
2. 每个已撤销 remote commitment 是否有可验证、可广播的 punish tx 或构造材料。
3. 当前 CSV 窗口是否仍允许惩罚。
4. punish 广播后的通道终止状态。

主网客户端不得依赖测试网故障注入接口。测试网可以提供保留旧 commitment、广播旧 commitment 等接口，用于证明 Agent 确实能识别旧状态并广播 punish。

## 网络不确定性

STP 客户端必须区分“明确失败”和“结果未知”。Timeout、EOF、连接中断、服务重启或 indexer 暂未收敛，都不能直接被当作交易未发生。

推荐规则：

1. 进入广播或最终承诺交换前，先持久化 pending 事务、通道快照和相关交易 ID。
2. 广播调用结果未知时，先查询 L1/L2 交易是否可见。
3. 如果交易可见，继续轮询确认，不重复消费输入。
4. 如果交易暂不可见，也应锁定相关输入并保留 pending，等待监控流程收敛。
5. 只有双方仍处于同一旧安全状态、无 pending 事务、相关交易均不可见时，才允许重新发起同类操作。

这条规则适用于 open、splicing-in、splicing-out、unlock、lock、close 和 force close。

## 通道恢复

STP 客户端应支持以下恢复能力：

| 能力 | 场景 |
| --- | --- |
| Restore | 本地进程或数据库异常，但可从本地备份、peer 或持久化状态恢复最新通道 |
| Reopen | 通道已关闭，但通道地址仍有属于用户的资产，需要恢复同一 client-core 通道身份 |
| Rebuild | 通道状态丢失或 L1 channel point 变化，需要依赖 L1/L2 ledger 重新分配资产和承诺状态 |
| Expand | 已在通道地址的资产未纳入当前承诺状态，需要纳入通道管理 |
| Clean stale channel | 链上已经关闭或惩罚完成，本地仍残留旧 active channel，需要先清理再重新 open |

恢复流程不得重复发行聪网资产。判断某个 L1 UTXO 是否需要 ascend，应优先依据 L2 channel ledger 中的 ascend / descend 记录，以及 L1/L2 indexer 对通道地址资产的当前视图。无法证明的资产不应自动 anchor。

## 客户端最低要求

一个安全 STP 客户端至少要具备：

1. 密钥管理和消息签名。
2. Core Node 发现和身份校验。
3. BTC L1 与 SatoshiNet 查询能力。
4. L1/L2 交易构造、签名、验证和广播能力。
5. 通道状态、承诺交易、撤销材料和 pending 事务持久化。
6. 资产协议解析和金额精度校验。
7. 结果未知恢复。
8. Safety snapshot、commitment export、punish status、force close plan 和 sweep build 等安全接口。

第三方实现细节见 [第三方 STP 客户端接入指南](client-integration.md) 和 [STP 第三方客户端实现验收清单](implementation-checklist.md)。

## 面向 AI Agent 的可验证安全

STP 希望让 AI Agent 不只是“会调用接口”，而是能判断资产是否仍在用户控制下。Agent 在价值移动前至少应确认：

1. 通道处于 ready。
2. 本地持有最新 local commitment。
3. remote commitment 的旧状态均有 punish coverage。
4. commit height 单调增加，没有回退。
5. L1/L2 indexer 证据与钱包本地状态一致。
6. 不存在 pending 或结果未知的价值移动事务。
7. 用户私钥、助记词和签名始终留在钱包安全边界内。

如果这些条件不能成立，Agent 应停止普通操作，并进入恢复、强制关闭、惩罚或人工确认路径。
