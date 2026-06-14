# 第三方 STP 客户端接入指南

本文面向希望自行实现 STP 客户端的钱包、SDK、PWA adapter、CLI、后端服务和 AI Agent 工具。目标是让任何开发语言实现的客户端都能接入兼容的 Core Node。

本文只描述 STP 客户端互操作。钱包创建、助记词导入导出、密码修改、普通资产发送等能力属于 SAT20 Wallet 或 SAT20 Agent Wallet 适配器层，见 [SAT20 Agent Wallet](../../ai/sat20-agent-wallet/readme.md)。

## 接入目标

一个 STP 客户端需要完成六件事：

1. 发现并校验 Core Node。
2. 管理用户通道身份、签名和本地通道状态。
3. 构造、签名、发送和验证 STP 协议消息。
4. 查询 BTC L1 indexer 与 SatoshiNet L2 indexer。
5. 推进 open、splicing-in、unlock、lock、lock-with-expand、splicing-out、close、force close、punish 等流程。
6. 在网络异常、indexer 延迟、peer 离线和本地重启后恢复 pending 事务。

客户端把每次价值移动都回到交易、UTXO、commit height、承诺交易、ascend/descend 和 punish coverage 这些可复核证据，而不是把 Core Node 响应、余额显示或单个 indexer 响应当成最终安全证明。

## 推荐架构

| 模块 | 职责 |
| --- | --- |
| Wallet Boundary | 保存私钥、助记词和用户授权；可以是 PWA、硬件钱包、移动钱包或本地安全钱包 |
| STP Engine | 实现 STP 消息、承诺状态、通道动作和恢复流程 |
| Transaction Engine | 构造和验证 BTC L1、SatoshiNet、commitment、punish、sweep 交易 |
| Asset Engine | 解析 BTC、ORDX、Runes、BRC20 等资产协议和金额精度 |
| State Store | 持久保存通道、commit height、承诺交易、撤销材料和 pending 事务 |
| Chain Query | 查询 L1/L2 UTXO、资产、交易可见性、确认数、ascend/descend 和通道状态 |
| Safety Monitor | 生成 safety snapshot、commitment export、punish status、force close plan 和 sweep plan |

AI Agent 推荐通过 SAT20 PWA Wallet Adapter 使用 STP：PWA 保存私钥和数据库，Agent 只发起受用户授权的 JSON 操作并读取安全证据。

## Core Node 发现

客户端连接 Core Node 前必须确认：

1. 钱包、Core Node、BTC L1 indexer 和 SatoshiNet L2 indexer 位于同一网络。
2. Core Node 公钥来自可信发现流程或用户显式配置。
3. Core Node 声明的协议版本、CSV 参数、服务费和能力列表可被客户端接受。
4. 客户端可以独立查询 L1/L2 状态，不能只依赖 Core Node 单方返回。

普通用户连接 Core Node 打开私人通道，不需要质押资产。质押只属于节点连接 Bootstrap Node 并准备升级为 Core Node 的路径。

推荐发现响应：

```json
{
  "protocol": "stp",
  "version": "1",
  "chain": "testnet",
  "core_node_pubkey": "02...",
  "endpoint": "https://core-node.example/stp",
  "features": [
    "open",
    "splicing-in",
    "unlock",
    "lock",
    "lock-with-expand",
    "splicing-out",
    "close",
    "force-close",
    "punish"
  ],
  "csv_delay": 1000
}
```

## 消息信封

所有需要认证的 STP 消息建议使用统一信封：

```json
{
  "protocol": "stp",
  "version": "1",
  "chain": "testnet",
  "message_type": "unlock_request",
  "request_id": "uuid-or-monotonic-id",
  "timestamp": 1760000000,
  "channel_id": "tb1q...",
  "commit_height": 12,
  "sender_pubkey": "02...",
  "payload": {},
  "signature": "hex-signature"
}
```

签名规则：

1. `signature` 之外的所有字段参与签名。
2. 序列化必须确定性，推荐 canonical JSON 或等价固定编码。
3. 接收方必须校验发送方公钥、通道身份、链 ID 和消息类型。
4. 任一消息若改变承诺状态，必须携带当前 `commit_height`。
5. 客户端必须拒绝承诺高度回退、链 ID 不匹配、签名无效或资产数量不一致的消息。

## 操作接口

面向上层钱包、CLI 或 Agent，建议 STP 客户端暴露语言无关的 JSON 操作接口。接口隐藏资产 UTXO、fee UTXO 和通道内部输入；选币和交易包构造由客户端内部完成。

### `stp.status`

查询 Core Node、通道列表、commit height、pending 事务和 indexer 同步状态。

```json
{
  "op": "stp.status",
  "chain": "testnet"
}
```

### `stp.open`

打开用户与 Core Node 的私人通道。

```json
{
  "op": "stp.open",
  "chain": "testnet",
  "core_node": "https://core-node.example/stp",
  "amount_sats": 50000,
  "memo": "optional"
}
```

客户端内部选择或构造 L1 funding 输入。普通用户 open 不需要质押资产。

### `stp.splicing_in`

把 BTC L1 资产纳入通道。

```json
{
  "op": "stp.splicing_in",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "runes:EXAMPLE",
  "amount": "1000"
}
```

客户端内部选择资产输入、普通 BTC 费用输入，并在需要时构造 BRC20 transfer inscription。Agent 只传资产、金额和目标，不直接传入原始输入列表。

### `stp.expand`

把已经位于通道地址、但尚未纳入当前承诺状态的资产纳入通道管理。

```json
{
  "op": "stp.expand",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "brc20:demo",
  "amount": "100"
}
```

Expand 适用于 interrupted splicing-in、rebuild 后补齐资产、或用户已把资产转入通道地址的场景。客户端必须通过 L1/L2 indexer 判断是否需要 ascend，不能重复发行聪网资产。

### `stp.unlock`

把通道资产释放到聪网个人地址。

```json
{
  "op": "stp.unlock",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "ordx:demo",
  "amount": "100",
  "to": "tb1p..."
}
```

Unlock 不需要用户提供 fee rate 或 fee UTXO。SatoshiNet 没有 BTC L1 fee rate 语义；客户端内部按聪网规则处理交易费用。

### `stp.lock`

把聪网个人地址资产重新锁回通道。

```json
{
  "op": "stp.lock",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "ordx:demo",
  "amount": "100"
}
```

Lock 不要求用户提供 L2 输入 UTXO。客户端内部选择可花费 L2 UTXO，并确认资产已从 pending 状态进入 spendable 状态。

### `stp.lock_with_expand`

通道容量不足时，将资产重新纳入通道控制权。

```json
{
  "op": "stp.lock_with_expand",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "ordx:demo",
  "amount": "100"
}
```

这是保护用户资产控制权的重要能力。容量不足时，客户端通过 lock-with-expand 恢复通道控制权，而不是让用户手工退出 L1 再重新进入通道。

### `stp.splicing_out`

把通道资产退出到 BTC L1。

```json
{
  "op": "stp.splicing_out",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "brc20:demo",
  "amount": "100",
  "to_l1_address": "tb1p..."
}
```

客户端内部选择普通 BTC fee 输入。对 BRC20，客户端应在需要时构造 transfer inscription 和相关交易包；对 Runes 和 ORDX，客户端必须遵守对应 L1 协议转移规则。

### `stp.close`

协商关闭或强制关闭通道。

```json
{
  "op": "stp.close",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "mode": "cooperative"
}
```

`mode` 可以是 `cooperative` 或 `force`。强制关闭必须返回 commitment txid、CSV 延迟和后续 sweep 条件。

## 安全接口

上层 Agent 或钱包 UI 必须能读取安全证据，而不是只读取余额。

| 接口 | 用途 |
| --- | --- |
| `stp.safety_snapshot` | 返回 channel point、commit height、承诺交易、余额、CSV、punish coverage、pending 状态 |
| `stp.commitment_export` | 导出当前 local / remote commitment 的只读校验材料 |
| `stp.punish_status` | 查询已撤销 remote commitment 的惩罚覆盖 |
| `stp.punish_build` | 对指定旧 commitment 构造并 dry-run 验证惩罚交易 |
| `stp.punish_broadcast` | 经用户授权后广播惩罚交易 |
| `stp.force_close_plan` | 返回当前可广播 local commitment 和后续 sweep 条件 |
| `stp.sweep_build` | CSV 到期后构造 sweep 交易；默认 dry-run，授权后广播 |
| `stp.transaction` | 查询 pending STP 事务、相关 txid、下一步等待条件和错误状态 |

这些接口不得导出私钥、助记词或未授权的 revocation secret。

## 成功响应

价值移动操作的成功响应不能只返回 `ok:true`。最低应包含：

| 字段 | 说明 |
| --- | --- |
| `transaction_id` | 后续轮询事务状态的稳定句柄 |
| `channel_id` | 操作作用的通道 |
| `status` | `BROADCASTED`、`READY_DEGRADED`、`CONFIRMED`、`FAILED` 等标准状态 |
| `tx_ids` | 已知 L1/L2/commitment/punish 交易 ID |
| `commit_height_before` / `commit_height_after` | 如果通道状态前进，应返回高度变化 |
| `next_check` | 下一步应等待的确认、indexer 状态或事务查询 |
| `safety` | 操作后的安全摘要，或要求立即调用 `stp.safety_snapshot` |

Agent 根据这些字段继续轮询和验证，而不是只根据余额变化判断操作成功。

## Commitment Balance 与 Spendable UTXO

客户端必须区分：

1. Commitment balance：最新承诺交易中已经分配给某一方的资产余额。
2. Spendable UTXO：L1 或 L2 indexer 已确认、当前可以作为下一笔交易输入使用的 UTXO。

刚 splicing-in 或 expand 的资产可能已经进入 commitment balance，但对应 L1 funding 或 L2 anchor 仍未确认。此时安全快照可以证明双方已经签署新状态，但客户端不能把资产作为 unlock / lock 的输入。

如果 commitment balance 已包含资产，而 indexer 尚未返回可花费 UTXO，客户端应返回 `ASSET_PENDING_CONFIRMATION` 或等价状态。Agent 的正确动作是继续轮询 reservation 和 L1/L2 indexer。

## 资产规则

| 资产 | 客户端要求 |
| --- | --- |
| 白聪 | 区分 L1 dust / fee 约束与 L2 0 聪 UTXO 能力 |
| ORDX | 按 `bindingSat` 计算绑定聪；`ordx:o` 类型对象不进入聪网 |
| Runes | L2 不需要绑定聪；L1 输出仍遵守 BTC 规则 |
| BRC20 | 支持 transfer inscription；没有可用 transfer UTXO 时由客户端内部构造 |

如果一个 UTXO 同时携带多种资产，STP 只 ascend 操作中明确指定的一种资产。未指定资产不进入本次 L2 守恒校验。

## 结果未知恢复

Timeout、EOF、连接中断、服务重启或 indexer 暂未收敛，都应视为结果未知。

统一流程：

1. 停止重发同一请求，锁定相关输入。
2. 保存请求、reservation、txid、channel id、asset、amount 和错误文本。
3. 查询 `stp.transaction`。
4. 查询相关 L1/L2 txid 是否可见。
5. 查询 Core Node channel status、commit height、channel point 和 pending 状态。
6. 如果任一交易可见、任一方状态前进或 reservation 存在，继续轮询原事务。
7. 只有双方仍在同一旧安全状态、无 pending、相关交易都不可见，才允许重新做 preflight 并重试。

这条规则适用于 open、splicing-in、splicing-out、unlock、lock、close、force close 和 punish。

## 发布前互操作测试

第三方客户端至少应在测试网完成：

1. Open 普通 client-core 通道。
2. Sats unlock / lock 推进 commit height。
3. Runes splicing-in、unlock、lock。
4. BRC20 splicing-in、unlock、lock。
5. ORDX 小额资产 splicing-in。
6. Splicing-out 至少一种协议资产。
7. 结果未知恢复，不重复消费输入。
8. Safety snapshot、commitment export、punish status、force close plan。
9. 测试网旧 commitment 广播与 punish 演练。
10. 客户端重启后恢复 pending 事务和安全材料。

验收细节见 [STP 第三方客户端实现验收清单](implementation-checklist.md)。
