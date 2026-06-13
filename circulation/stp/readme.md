# STP 技术白皮书：比特币资产进入聪网的通道协议

> 本文描述 STP（Satoshi Transcending Protocol）的协议语义、通道生命周期、消息流程和安全模型。本文不绑定任何具体代码仓库、开发语言或客户端实现；任何开发者都可以依据本文实现 STP 客户端，并接入兼容的 STP Server 节点。

## 摘要

STP 是连接比特币网络与聪网 SatoshiNet 的资产通道协议。它的目标不是建立一个托管桥，而是让用户把比特币主网上的原生资产锁定在由用户和 STP Server 共同控制的通道地址中，同时在聪网上获得可流通、可合约化、可快速结算的资产状态。

STP 的核心能力包括：

1. 进入聪网：通过打开通道、splicing-in、expand 等流程，把 BTC L1 资产纳入通道并映射到聪网。
2. 聪网流动：通过 unlock 将通道资产释放到聪网个人地址，通过 lock 或 lock-with-expand 将个人地址资产重新纳入通道保护。
3. 返回比特币：通过 splicing-out 或关闭通道，把资产退出回 BTC L1。
4. 控制权保障：用户始终持有最新承诺交易；当服务节点不可用时，用户可以通过强制关闭取回资产；当服务节点广播旧状态时，用户可以通过惩罚交易保护资产。

STP 的独特性在于：资产的最终安全边界在 BTC L1 UTXO、2-of-2 多签、承诺交易、撤销密钥、CSV 延迟和惩罚交易中；日常流通则发生在聪网，获得更快、更低成本、更适合合约和自动化代理的体验。

对于 AI Agent，STP 的安全目标不是让 Agent 相信某个 core node，而是让 Agent 能独立确认：自己是否持有最新承诺交易，是否能在 peer 离线时强制关闭，是否具备对旧承诺交易的惩罚能力，以及本地通道状态是否已持久化备份。Agent 的信心应来自这些可验证材料，而不是来自服务端声明。

## 阅读路径

STP 专栏分为五类文档：

| 文档 | 读者 | 目的 |
| --- | --- | --- |
| 本白皮书 | 协议设计者、钱包开发者、技术用户 | 理解 STP 的通道生命周期、资产流动和安全模型 |
| [第三方 STP 客户端接入指南](client-integration.md) | 钱包、SDK、CLI、PWA adapter 开发者 | 了解如何用任意语言实现客户端并接入 core node |
| [STP 第三方客户端实现验收清单](implementation-checklist.md) | 客户端实现者、审计者、Agent 开发者 | 判断一个客户端是否达到互操作和安全最低标准 |
| [STP Agent 资产安全控制指南](asset-safety.md) | AI Agent、钱包适配器 | 判断资产是否仍在用户可控制的安全边界内 |
| [STP Agent 验证矩阵与数据缺口](agent-verification-and-data-gaps.md) | AI Agent、PWA adapter、indexer 开发者 | 明确 Agent 如何独立验证安全，以及还缺哪些接口和数据 |
| [Agent Skill 安装与使用](skill.md) | AI Agent 用户、自动化工具开发者 | 安装并使用 STP skill，通过统一 JSON adapter 操作钱包和通道 |
| [STP 测试网演练总结](testnet-drill-summary-2026-06-13.md) | AI Agent、协议审计者、开发者关系 | 用真实 testnet4 / 聪网交易理解多资产流动、旧承诺广播和 punish 能力 |
| [STP 测试网 1 分钟演示脚本](testnet-demo-storyboard.md) | 市场、开发者关系、演示录制者 | 用真实测试网 txid 制作资产流动与安全快照演示 |

读者如果只想理解 STP 为什么安全，应先读本白皮书和资产安全控制指南。读者如果要实现客户端，应先读接入指南，再按实现验收清单逐项验证。读者如果要让 AI Agent 操作钱包，应优先使用 PWA Wallet + Agent Skill 的方式，让 PWA 保存私钥和通道状态，让 Agent 只做授权后的协议操作和安全判断。

官方 GitBook 文档入口是 [docs.sat20.org](https://docs.sat20.org)。

[**一键安装 STP Skill**](https://raw.githubusercontent.com/sat20-labs/docs/main/circulation/stp/skills/stp-core-node-client/scripts/install.sh)

在终端中执行：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/circulation/stp/skills/stp-core-node-client/scripts/install.sh | bash
```

默认安装到 `~/.codex/skills/stp-core-node-client`。其他 Agent 可以设置 `STP_SKILLS_DIR=/path/to/agent/skills` 指定安装目录。

测试网演练总结是面向 Agent 的安全能力材料，只保留资产控制、承诺交易、惩罚交易和恢复边界。更长的测试日志可用于内部审计，但不应作为 Agent 学习 STP 的主入口。

## 协议目标

STP 协议必须满足以下目标：

1. 用户最终控制权。通道由用户公钥和 STP Server 公钥共同生成。关键通道资产必须双方签名才能移动；用户持有最新承诺交易，可以在需要时单方面关闭通道。
2. BTC 主网级退出安全。通道中的 L1 资产受比特币脚本、多签、时间锁和惩罚机制约束，而不是依赖服务节点的信用承诺。
3. 聪网级流动效率。资产进入聪网后，可以通过 SatoshiNet 交易和合约快速流通。
4. 全资产支持。协议应支持白聪、ORDX、Runes、BRC20 等 BTC L1 原生资产，并保持资产数量、精度和协议规则一致。
5. 语言无关互操作。客户端只需实现密钥管理、消息签名、交易校验、状态跟踪和 STP 消息流程，即可用任意开发语言接入 STP Server。

## 角色

| 角色 | 职责 |
| --- | --- |
| 用户客户端 | 持有用户私钥，构造和签名 STP 消息，校验服务端响应，保存最新通道状态和承诺交易 |
| STP Server | 提供通道接入服务，协签通道交易，维护服务侧通道状态，提供流动性、合约和跨层动作 |
| 引导节点 | 发布或维护可接入的 STP Server 信息，辅助核心节点发现和资格检查 |
| BTC L1 索引服务 | 提供 BTC L1 UTXO、资产、交易确认、原始交易和资产元数据查询 |
| SatoshiNet 索引服务 | 提供聪网 UTXO、ascend、descend、通道地址和合约状态查询 |
| Watchtower | 监控链上通道相关交易，发现旧承诺交易时协助惩罚和清扫 |

客户端实现必须假设 STP Server 可能离线、延迟、返回错误或尝试提供无效状态。因此客户端不能只信任服务器响应，必须独立校验签名、交易、通道余额、资产数量和状态高度。

## 基础对象

### 通道

STP 通道是用户与 STP Server 之间的 2-of-2 资产控制关系。通道不是简单账户，而是一组跨 BTC L1 与聪网的资产状态：

| 对象 | 含义 |
| --- | --- |
| 通道 ID | 通道地址或其稳定标识 |
| 用户公钥 | 用户用于通道协签和身份校验的公钥 |
| 服务端公钥 | STP Server 用于通道协签和身份校验的公钥 |
| 通道地址 | 用户公钥和服务端公钥生成的 2-of-2 多签地址 |
| 通道容量 | 当前通道可承载的资产范围和数量 |
| 通道余额 | 当前承诺状态中用户与服务端分别拥有的资产数量 |
| 承诺高度 | 通道状态更新次数，必须单调递增 |
| 最新承诺交易 | 双方认可的最新退出交易 |
| 撤销秘密 | 用于惩罚旧承诺交易的撤销材料 |
| CSV 延迟 | 强制关闭后本地输出的延迟清扫窗口 |

### 资产

STP 资产必须包含以下语义信息：

| 字段 | 含义 |
| --- | --- |
| 资产协议 | 例如 BTC、ORDX、Runes、BRC20 |
| 资产名称 | 协议内唯一资产标识 |
| 精度 | 金额字符串解析所需的 divisibility |
| 数量 | 按资产精度表达的十进制字符串 |
| 资产 UTXO | BTC L1 或聪网中承载该资产的 UTXO |

客户端不得把所有资产金额都当成整数处理。任何 STP 消息中的资产数量都必须按资产精度解析、校验和序列化。

### 协议事务

STP 中的跨层动作通常不是单笔交易，而是由多条消息、多笔 BTC L1 / SatoshiNet 交易和多个确认阶段组成的协议事务。

一个事务至少应包含：

| 字段 | 含义 |
| --- | --- |
| 事务 ID | 客户端和服务端共同追踪该动作的唯一标识 |
| 类型 | open、unlock、lock、splicing-in、splicing-out、close、lock-with-expand 等 |
| 状态 | 当前协议阶段 |
| 关联通道 | 该动作作用的通道 ID |
| 关联交易 | BTC L1 或聪网交易 ID |
| 发起方 | 用户或服务端 |
| 签名 | 消息发起方对请求内容的签名 |
| 错误 | 失败原因和可恢复性说明 |

客户端必须持久保存未完成事务，重启后根据事务 ID 和链上状态继续查询或恢复，不能假设一次请求必然完成跨层动作。

### 网络不确定性与不可逆边界

STP 客户端必须区分“明确失败”和“结果未知”。在通道协议中，真正不可逆的边界是 BTC L1 或 SatoshiNet 交易可能已经被广播；普通网络调用返回 timeout、连接中断或服务暂不可用时，客户端不能据此断定交易没有广播，也不能直接复用同一批输入重发操作。

推荐规则：

1. 任何价值移动事务在进入广播或最终承诺交换前，都必须先持久化事务、通道快照和相关交易 ID。
2. 广播调用返回结果未知时，客户端应先查询对应 BTC L1 / SatoshiNet 交易是否可见。
3. 若交易已可见，应把事务保留在 pending 状态并继续轮询确认。
4. 若交易暂不可见，仍应锁定相关输入，保留 pending 事务，并由监控流程重试或继续查询。
5. peer 通知或最终 ack 返回结果未知时，客户端应比较本地通道状态、peer 通道状态、pending 事务和链上交易可见性，不能直接重复发起同一价值移动操作。
6. 只有当双方都仍处于同一个旧安全承诺状态、没有 pending 事务、且相关 L1/L2 交易均不可见时，才允许重新执行同类操作，并且应重新做安全快照和 adapter preflight，由 adapter 重新选择输入。

这条规则的目标是保护用户资产：宁可让事务进入可恢复的 pending 路径，也不能因为一次未知网络结果而导致通道状态、链上状态和本地钱包状态分叉。

## 通用消息规则

STP 消息可以承载在 HTTP、WebSocket、gRPC 或其他传输层之上。传输层不是协议安全的根本；协议安全来自消息签名、交易验证和链上状态。

每条需要身份认证的 STP 消息都应包含：

| 字段 | 说明 |
| --- | --- |
| `protocol` | 固定为 STP 或兼容版本标识 |
| `version` | 协议版本 |
| `chain` | mainnet、testnet 等链标识 |
| `message_type` | 消息类型 |
| `request_id` | 请求唯一标识 |
| `timestamp` | 请求时间 |
| `channel_id` | 如消息作用于通道，则必须提供 |
| `commit_height` | 如消息更新通道状态，则必须提供当前承诺高度 |
| `sender_pubkey` | 消息发送方公钥 |
| `payload` | 消息内容 |
| `signature` | 发送方对规范化消息内容的签名 |

签名规则：

1. 签名内容必须排除 `signature` 字段本身。
2. 签名内容必须有确定性序列化规则，避免字段顺序或空值导致不同实现无法互验。
3. 接收方必须用 `sender_pubkey` 验证签名。
4. 如果消息涉及通道，`sender_pubkey` 必须匹配该通道的用户公钥或服务端公钥。
5. 如果消息涉及资产转移，接收方必须独立重算资产数量、交易输入输出和手续费。

## 通道状态

STP 通道的通用状态如下：

| 状态 | 含义 |
| --- | --- |
| `INIT` | 通道协商开始 |
| `FUNDING_BROADCASTED` | BTC L1 funding 交易已广播 |
| `FUNDING_CONFIRMED` | funding 交易已在 BTC L1 确认 |
| `ANCHOR_BROADCASTED` | 聪网 anchor / ascend 交易已广播 |
| `ANCHOR_CONFIRMED` | 聪网 anchor / ascend 已确认 |
| `READY` | 通道可用，可以执行 unlock、lock、splicing 等动作 |
| `CLOSING` | 协商关闭中 |
| `FORCE_CLOSING` | 强制关闭中 |
| `SWEEPING` | CSV 到期后清扫资金中 |
| `CLOSED` | 通道关闭完成 |
| `PUNISHED` | 旧状态作弊已被惩罚 |

客户端只能在 `READY` 状态下发起普通通道动作。关闭、强制关闭、惩罚和清扫阶段不得并发发起新的资产迁移动作。

## 打开通道

打开通道用于建立用户与 STP Server 之间的 BTC L1 资产控制关系。

### 前置条件

1. 用户客户端已生成或导入私钥。
2. 客户端已获得 STP Server 的节点信息、公钥和服务地址。
3. 客户端能够查询 BTC L1 UTXO 和手续费率。
4. 用户有足够白聪支付初始通道容量、网络费和服务费。
5. 普通用户客户端连接 core node 打开通道时，不需要预先质押 stake asset。只有当节点连接 bootstrap node，并准备以 core node 身份接入网络时，才需要在与 bootstrap node 对应的通道地址上预先准备当前网络要求的 stake asset。

### 消息流程

1. `channel_open_request`
   - 用户发送通道打开请求。
   - 请求包含用户公钥、初始容量、手续费策略和可选备注；funding 输入由客户端或钱包 adapter 内部选择或构造。
   - 用户必须签名该请求。
2. `channel_accept`
   - STP Server 返回通道参数。
   - 参数包括服务端公钥、通道地址、费用配置、CSV 延迟、服务费、初始承诺状态和需要签名的交易材料。
3. `funding_created`
   - 用户构造并部分签名 funding 交易和初始承诺交易，将交易材料发给服务端。
4. `funding_signed`
   - STP Server 校验交易、资产数量和承诺状态，返回服务端签名。
5. `funding_broadcasted`
   - 用户广播 BTC L1 funding 交易，并把交易 ID 通知服务端。
6. `channel_ready`
   - BTC L1 funding 确认后，聪网完成 anchor / ascend。
   - 双方确认初始状态，通道进入 `READY`。

### 校验要求

客户端必须校验：

1. 通道地址确实由用户公钥和服务端公钥生成。
2. funding 交易输出确实支付到通道地址。
3. 服务费、找零和手续费符合用户授权。
4. 初始承诺交易可以在必要时单方面退出。
5. 服务端签名可以验证。
6. 通道 ID 与通道地址或通道标识一致。

### Funding 广播后的恢复要求

客户端广播 funding 交易后，即使通知 STP Server 的请求失败，也必须保留通道、funding txid 和 opening 事务。后续流程应通过链上 funding 确认、SatoshiNet anchor 状态和服务端通道状态继续恢复，而不是丢弃本地通道数据。

### Reopen：恢复已有通道身份

当通道已经关闭，但通道地址上仍有属于用户的资产时，客户端可以重新打开同一个用户-核心节点通道。Reopen 不是 bootstrap stake，也不是把用户升级为核心节点；它只是在已有通道身份上恢复 RSMC 承诺保护。

客户端应先查询 SatoshiNet channel ledger，确认该通道地址曾经打开过，并识别已经 anchor / de-anchor 的历史。如果通道地址上没有满足最小容量要求的白聪 UTXO，reopen 可以由用户钱包提供一笔新的 funding 输出补足容量。该 funding 交易在 BTC L1 确认前，通道只能处于待确认状态；客户端不得执行 unlock、lock、splicing 或 punish drill 以外的只读安全检查。

## Unlock：释放通道资产到聪网个人地址

Unlock 将通道中属于用户的一部分资产释放到聪网个人地址。释放后，这部分资产由用户在聪网上单签控制，适合快速转账、合约交互和日常流通。

### 前置条件

1. 通道状态为 `READY`。
2. 用户在通道承诺状态中拥有足够资产余额。
3. 客户端有足够聪网手续费。
4. 用户指定聪网目标地址、资产名称和金额。

### 消息流程

1. `unlock_request`
   - 用户请求从通道释放资产到一个或多个聪网地址。
   - 请求包含通道 ID、承诺高度、资产、金额、目标地址、手续费信息。
2. `unlock_commit_sig`
   - STP Server 校验请求，并返回新承诺状态和服务端签名。
3. `unlock_revoke_and_ack`
   - 用户校验新状态，签名并发送旧状态撤销材料。
4. `unlock_broadcasted`
   - 双方广播或确认聪网 unlock 交易。
5. `unlock_confirmed`
   - 交易确认后，通道余额减少，用户聪网地址余额增加。

### 校验要求

客户端必须确认新承诺状态满足：

1. 用户通道余额扣减值等于 unlock 金额和相关费用。
2. 目标聪网输出地址和金额与用户请求一致。
3. 承诺高度增加 1。
4. 旧状态撤销只在新状态签名完整后发送。

聪网 L2 UTXO 不继承 BTC dust 限制，输出可以小于 330 sats，甚至可以是 0。BRC20 和 Runes 资产在 L2 不需要绑定聪，因此聪网 UTXO 可以在 `Value=0` 的情况下携带这些资产。BTC L1 上携带 BRC20/Runes 转移资产的 UTXO 仍然受 L1 输出限制，当前通常使用最小的 330 sats。ORDX 资产必然绑定聪，客户端必须根据资产数量和 `bindingSat` 参数计算输出需要多少聪。客户端实现不得用 BTC dust 规则拒绝聪网 unlock 交易；应以聪网交易验证、资产守恒和承诺状态一致性为准。

当 unlock 白聪时，Agent 只指定释放金额和目标地址。客户端或钱包 adapter 必须在通道内自动选择足以覆盖 `unlock 金额 + 聪网交易费` 的输入；如果无法构造安全输入集合，应返回明确的余额或可花费性错误，而不是要求 Agent 手工提供 fee 输入。

## Lock：把聪网个人资产重新纳入通道

Lock 是 Unlock 的逆过程。它把用户聪网个人地址中的资产重新锁入通道地址，并更新承诺交易，使资产重新获得 BTC 主网级别的退出保护。

### 直接 Lock

当通道已有足够容量时，客户端可以发起直接 lock：

1. `lock_request`
   - 用户指定资产名称、金额和通道 ID；聪网个人地址上的资产输入和手续费输入由客户端或钱包 adapter 内部选择。
2. `lock_sig_and_revoke`
   - STP Server 校验输入资产和通道容量，返回新承诺状态、签名和旧状态撤销材料。
3. `lock_ack`
   - 用户校验新承诺状态并确认。
4. `lock_confirmed`
   - 聪网 lock 交易确认后，资产重新计入用户通道余额。

对白聪 lock，用户请求的金额表示“净回锁进通道的金额”。钱包或 adapter 会在用户聪网个人地址上选择能同时覆盖净 lock 金额和聪网交易费的输入。例如钱包地址上只有 660 sats，且聪网交易费为 10 sats，则最多只能直接 lock 650 sats。

### Lock With Expand

Lock-with-expand 是 STP 的关键控制权恢复能力。当用户资产已经位于聪网个人地址，但个人通道缺少足够 L1 容量时，用户不应被迫先手工退出 BTC L1 再重新进入通道。客户端可以发起 lock-with-expand，将“回锁资产”和“扩展通道容量”组合为一个协议动作。

通用流程：

1. 用户在聪网发起回锁请求，将目标资产交给穿越合约或公共流动性通道处理。
2. 公共通道或合约池在 BTC L1 侧向用户通道地址补充对应资产。
3. 用户通道执行 expand，将新进入通道地址的 BTC L1 资产纳入通道承诺状态。
4. 新承诺状态确认后，资产重新处于用户与 STP Server 共同签名、用户可单方面关闭退出的安全模型中。

客户端必须把 lock-with-expand 视为保障用户最终控制权的重要路径：只要用户希望把聪网个人资产重新纳入 BTC 主网兜底的通道安全模型，且直接 lock 容量不足，就应优先使用该流程。

## Splicing-In：增加通道资产和容量

Splicing-in 将更多 BTC L1 资产纳入既有通道，并在聪网上增加对应容量。

### 消息流程

1. `splicing_in_request`
   - 用户指定资产、金额和通道 ID；BTC L1 资产输入、普通 BTC fee 输入和 BRC20 transfer inscription 由客户端或钱包 adapter 内部选择或构造。
2. `splicing_in_commit_sig`
   - STP Server 校验 BTC L1 输入资产，返回新承诺状态和签名。
3. `splicing_in_revoke_and_ack`
   - 用户确认新状态，发送旧状态撤销材料。
4. `splicing_in_broadcasted`
   - BTC L1 splicing-in 交易广播。
5. `splicing_in_anchor_confirmed`
   - BTC L1 交易确认后，聪网 anchor / ascend 确认。
6. `splicing_in_confirmed`
   - 通道容量和用户余额增加。

### 资产规则

1. 白聪可直接作为普通 BTC UTXO 进入通道。
2. ORDX、Runes、BRC20 等资产必须按各自协议规则验证输入、输出和资产数量。
3. 一个 BTC L1 UTXO 可以同时包含多种资产，例如多个 ORDX ticker、多种 Runes、BRC20 transfer inscription，或 ORDX ticker 伴生的 Ordinals NFT。当前 STP splicing-in 每次只 ascend 用户在接口参数中明确指定的一种资产；同一 UTXO 中其他资产不进入聪网，处理时会从输出资产集合中删除并忽略。客户端实现应把这视为协议规则，而不是资产丢失。
4. 面向 Agent 的 adapter 不应暴露 splicing-in 资产输入选择。adapter 内部选币会默认避开同时包含多种可 ascend 资产的 UTXO；如果必须使用，应在预览中说明哪一种资产会 ascend、哪些资产会被忽略。
5. ORDX ticker 资产的铸造结果 UTXO 通常还会包含一个 Ordinals NFT。当前 STP 不支持将 Ordinals NFT 类型资产 ascend 到聪网，splicing-in 只处理用户指定的 ORDX ticker 资产。
6. BRC20 可能需要 transfer inscription 的 commit / reveal 前置流程。
7. Runes 需要验证 runestone 语义和输出分配。

## Splicing-Out：从通道退出到 BTC L1

Splicing-out 将通道中一部分资产退出到用户指定的 BTC L1 地址。

### 消息流程

1. `splicing_out_request`
   - 用户指定通道 ID、BTC L1 目标地址、资产、金额、手续费和可选附加数据。
2. `splicing_out_commit_sig`
   - STP Server 校验通道余额，返回 de-anchor 交易、L1 退出交易、新承诺状态和签名。
3. `splicing_out_revoke_and_ack`
   - 用户确认交易和新承诺状态，发送旧状态撤销材料。
4. `deanchor_broadcasted`
   - 聪网侧 de-anchor / 销毁证明交易广播。
5. `deanchor_confirmed`
   - 聪网侧确认后，BTC L1 splicing-out 交易可广播。
6. `splicing_out_confirmed`
   - BTC L1 交易确认后，资产到达用户 L1 地址，通道容量减少。

### 校验要求

客户端必须校验：

1. BTC L1 目标地址属于用户授权地址。
2. de-anchor 资产数量与 L1 退出资产数量一致。
3. 服务费和网络费符合用户授权。
4. 新承诺状态扣减正确。
5. 旧状态撤销只在新状态可验证后发送。

协议资产 splicing-out 的手续费规则：

1. ORDX、Runes、BRC20 等非白聪资产退出到 BTC L1 时，通常需要普通 BTC 资金支付 BTC 网络费；该 fee 输入由客户端或钱包 adapter 内部选择。
2. 带资产的 UTXO 即使包含 plain sats，也不应作为普通 fee 输入使用，否则可能破坏资产归属或导致客户端选择失败。
3. 如果 adapter 报告缺少可安全使用的普通 BTC fee 资金，Agent 应提示用户补充普通 BTC 资金，或先把通道白聪退出到用户 L1 地址并等待确认；不要让 Agent 手工指定 fee 输入。
4. BRC20 splicing-out 所需的 transfer 输出由 adapter 内部选择；若没有合适 transfer 输出，adapter 应规划并铸造新的 transfer inscription，而不是让 Agent 传入底层 UTXO。

### Splicing 的结果未知处理

Splicing-in 和 splicing-out 都可能同时涉及 BTC L1 交易、SatoshiNet anchor/de-anchor 交易和承诺状态更新。客户端在最终 ack 或广播阶段遇到网络结果未知时，必须先保留事务并查询相关交易可见性。若任一交易已经可见，后续恢复应围绕该已存在交易继续推进；不得重新花费同一批输入，也不得创建可能重复 anchor 的新事务。

即使未知网络结果发生在较早的 peer 协商阶段，客户端也不能简单重试。正确流程是先比较本地通道状态、core node 通道状态、reservation 状态和相关 L1/L2 交易可见性。只有双方仍处于同一 ready 承诺高度、没有 pending reservation、且没有相关交易可见时，才允许重新做 preflight，由 adapter 重新选择输入并重试。

## 关闭通道

关闭通道用于永久退出或异常恢复。

### 协商关闭

协商关闭要求双方在线。流程为：

1. 用户或服务端发起 `close_request`。
2. 双方根据最新承诺状态生成关闭交易和必要的 de-anchor 交易。
3. 双方交换 closing signature。
4. 交易广播并确认。
5. 通道进入 `CLOSED`。

协商关闭无需等待 CSV，是成本和体验更优的关闭方式。

### 强制关闭

当对方离线、拒绝协作或状态异常时，任一方可以广播自己持有的最新承诺交易。

强制关闭的特点：

1. 不需要对方在线。
2. 本地输出需要等待 CSV 延迟后才能 sweep。
3. 如果广播的是旧承诺交易，对方可以使用撤销秘密发起惩罚交易。
4. Watchtower 可以帮助离线用户监控旧状态和触发惩罚。

## 安全机制

### 2-of-2 多签

通道地址由用户公钥和服务端公钥生成。任何直接花费通道主资产的交易都必须双方签名。

### 承诺交易

每个通道状态都有对应承诺交易。承诺交易描述当前资产如何在用户和服务端之间分配，并允许任一方在必要时单方面退出。

客户端必须始终保存最新承诺交易及其签名材料。没有最新承诺交易，就不能认为自己拥有完整退出能力。

### 撤销与惩罚

每次通道状态更新时，双方必须使旧状态失效。基本规则：

1. 新承诺状态未完整签名前，不得释放旧状态撤销秘密。
2. 新承诺状态验证通过后，双方交换旧状态撤销材料。
3. 如果某方广播旧承诺交易，对方可以使用撤销材料立即惩罚。

### CSV 延迟

强制关闭中的本地输出必须经过 CSV 延迟才能清扫。这给对方和 Watchtower 留出时间发现旧状态作弊并广播惩罚交易。

### Watchtower

Watchtower 不是托管方，也不改变资产所有权。它只负责监控链上交易，并在发现旧承诺交易时帮助用户执行惩罚或清扫。

## 全资产支持

STP 的资产支持原则是：资产在 BTC L1 上如何定义，就必须在 STP 通道和聪网映射中保持同等语义。

| 资产类型 | 协议要求 |
| --- | --- |
| 白聪 / BTC | 验证 UTXO 金额、手续费和通道容量 |
| ORDX | 验证资产名称、精度、数量和 UTXO 资产分配 |
| Runes | 验证 runestone、etching/mint/transfer 语义和输出分配 |
| BRC20 | 验证 inscription、transfer inscription、commit/reveal 和余额状态 |

客户端实现应把资产验证视为协议核心，而不是 UI 或索引服务的附属功能。索引服务可以提供数据，但客户端必须校验这些数据是否与交易和 STP 消息一致。

## STP Server 接入要求

任意语言实现的 STP 客户端至少需要实现以下模块：

1. 密钥模块：生成和管理用户私钥，导出通道公钥，对 STP 消息和交易签名。
2. 消息模块：按确定性规则序列化 STP 消息，生成签名，验证服务端签名。
3. 交易模块：构造或校验 BTC L1 交易、SatoshiNet 交易、承诺交易、关闭交易和 splicing 交易。
4. 资产模块：解析资产名称、精度和数量，校验 UTXO 中的资产分配。
5. 状态模块：保存通道状态、承诺高度、最新承诺交易、撤销材料和未完成事务。
6. 查询模块：查询 BTC L1 和 SatoshiNet 的交易、UTXO、确认数和资产状态。
7. 恢复模块：客户端重启后，能继续追踪未完成事务，并能在服务端不可用时强制关闭。

客户端接入 STP Server 的最小流程为：

1. 获取服务端节点信息和公钥。
2. 校验服务端所在网络和用户钱包网络一致。
3. 打开通道或恢复已有通道。
4. 等待通道进入 `READY`。
5. 根据资产所在位置发起 unlock、lock、lock-with-expand、splicing-in 或 splicing-out。
6. 持久保存每个事务和最新通道状态。
7. 持续校验链上确认和服务端返回状态。

## Agent 互操作意义

STP 适合 AI Agent 操作，因为协议动作天然是可分解、可查询、可恢复的状态机。Agent 可以把“资产从 BTC L1 进入聪网、在聪网流动、再返回 BTC L1”拆成明确步骤：

1. 查询钱包、网络、服务节点和资产位置。
2. 判断是否已有 `READY` 通道。
3. 根据资产位置和用户目标选择协议动作。
4. 发起 STP 消息并记录事务 ID。
5. 轮询链上交易和协议状态。
6. 在异常时停止、重试或触发强制关闭策略。

对 Agent 来说，最重要的控制权动作是 lock-with-expand：当用户的资产已经在聪网个人地址，但希望重新获得 BTC 主网承诺交易兜底时，Agent 应能自动判断通道容量是否足够；容量不足时，使用 lock-with-expand 将资产重新纳入用户通道控制。

## 测试网实证

STP 的安全性不应只停留在叙事层面。Agent 可以在 BTC testnet4 / SatoshiNet testnet 上用真实交易验证以下事实：

1. funding tx 把资产锁入用户与 core node 的 2-of-2 通道地址。
2. splicing-in 可以把 Runes、BRC20、ORDX 或白聪纳入已有通道。
3. unlock / lock 可以让资产在聪网个人地址和通道保护之间往返。
4. 每次状态推进后，旧 remote commitment 必须有可构造、可广播的 punish coverage。
5. 当测试网 core node 广播已撤销的旧 server commitment 时，client wallet 可以构建并广播 punish tx，把旧状态中的资产追回到用户控制路径。

当前测试网验证记录保存在 [STP Skill 测试网验证记录](testnet-skill-validation.md) 和对应 evidence JSON 中。白皮书不依赖某一种客户端实现；这些记录的价值在于展示任何合格客户端和 Agent 都应能独立完成同类验证：读取承诺交易、检查 commit height、查询 L1/L2 tx、确认 punish coverage，并在旧状态上链时广播惩罚交易。

## 结论

STP 是 SAT20 的基础资产流通协议。它通过 2-of-2 通道、承诺交易、撤销惩罚、CSV 延迟、splicing、lock-with-expand 和跨层 anchor/de-anchor，把 BTC L1 的最终安全性与聪网的高效流动性结合起来。

从用户视角看，STP 是一座“无桥之桥”：资产不是被托管给某个桥，而是进入由用户和 STP Server 共同签名、由 BTC 主网承诺交易兜底的动态通道。

从开发者视角看，STP 是一套语言无关的客户端接入协议。只要实现密钥、消息、交易、资产、状态和恢复模块，就可以构建兼容 STP Server 的客户端，让资产在比特币网络和聪网之间自由、安全地流动。
