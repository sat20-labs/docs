# 第三方 STP 客户端接入指南

> 本文面向希望自行实现 STP 客户端的钱包、交易工具、服务端程序和 AI Agent。目标是让任何开发语言实现的客户端都能接入兼容的 STP Server，也就是 core node。

## 接入目标

第三方 STP 客户端需要完成五件事：

1. 发现并校验 STP Server。
2. 管理用户密钥和通道状态。
3. 构造、签名、发送 STP 协议消息。
4. 校验 BTC L1、SatoshiNet 和 STP Server 返回的交易与状态。
5. 在 open、unlock、lock、lock-with-expand、splicing-in、splicing-out、close 等流程中安全推进事务。

客户端可以是浏览器钱包、命令行工具、后端服务、移动 App 或 AI Agent 适配器。协议不限定实现语言。

如果实现者需要判断自己的客户端是否已经达到互操作最低标准，应同时阅读 [STP 第三方客户端实现验收清单](implementation-checklist.md)。本文说明如何接入和暴露接口，验收清单说明实现必须保存什么、验证什么、如何处理结果未知，以及发布前必须通过哪些测试。

## 推荐接入形态：PWA Wallet + WASM Adapter

面向普通用户和 AI Agent 的最佳形态，是让用户安装 SAT20 PWA Wallet，由 PWA 作为钱包容器和权限边界，再由 PWA 内部加载 WASM 执行引擎：

| 层级 | 职责 |
| --- | --- |
| SAT20 PWA Wallet | 保存钱包状态、管理用户授权、展示交易确认、隔离私钥 |
| `sat20wallet.wasm` | 提供基础钱包、账户、签名和资产能力 |
| `stpd.wasm` | 提供 STP 通道、open、unlock、lock、lock-with-expand、splicing 和 close 能力 |
| PWA STP Adapter | 把外部 JSON 操作请求转换成受用户授权的 WASM 调用 |
| Agent Skill / AI Agent | 只表达用户目标、发起协议操作、轮询状态，不直接接触私钥 |

因此，第三方实现有两条路线：

1. 钱包团队可以直接实现完整 STP 客户端，自己管理密钥、交易构造和通道状态。
2. AI Agent 和自动化工具优先接入 PWA STP Adapter，让 PWA 负责私钥、用户确认、WASM 生命周期和本地状态。

Agent skill 不应直接加载 `sat20wallet.wasm` 或保存助记词。它应通过 PWA 暴露的受权限控制接口发起 `stp.open`、`stp.unlock`、`stp.lock`、`stp.lock_with_expand` 等 JSON 操作。PWA 在用户授权后调用内部 WASM 方法完成签名、交易构造、广播和状态持久化。

推荐的操作映射如下：

| JSON 操作 | PWA / WASM 能力 |
| --- | --- |
| `stp.status` | 查询钱包、core node、通道列表和当前通道状态 |
| `stp.open` | 打开 STP 通道 |
| `stp.unlock` | 从通道释放资产到聪网个人地址 |
| `stp.lock` | 把聪网个人地址资产回锁到通道 |
| `stp.lock_with_expand` | 通道容量不足时执行扩容回锁，恢复用户通道控制权 |
| `stp.splicing_in` | BTC L1 资产进入通道 |
| `stp.splicing_out` | 通道资产退出到 BTC L1 |
| `stp.close` | 协商关闭或强制关闭通道 |
| `stp.safety_snapshot` | 查询通道承诺交易、惩罚覆盖和强制退出安全状态 |
| `stp.punish_status` | 查询旧承诺交易的惩罚交易覆盖 |
| `stp.punish_build` / `stp.punish_broadcast` | 构造、验证和广播惩罚交易 |
| `stp.test_retain_server_commitment` / `stp.test_broadcast_retained_server_commitment` | 测试网惩罚能力演练，主网不可用 |

## 客户端架构

一个完整客户端至少包含以下模块：

| 模块 | 职责 |
| --- | --- |
| Keyring | 生成、导入和保护用户私钥；对 STP 消息和交易签名 |
| Transport | 与 STP Server 通信，可使用 HTTP、WebSocket、gRPC 或其他传输 |
| Message Codec | 按确定性规则序列化/反序列化 STP 消息，验证签名 |
| Transaction Engine | 构造和校验 BTC L1、SatoshiNet、承诺交易、关闭交易和 splicing 交易 |
| Asset Engine | 解析资产名称、精度、数量，验证 UTXO 中的资产分配 |
| State Store | 持久保存通道、承诺高度、最新承诺交易、撤销材料和未完成事务 |
| Chain Query | 查询 BTC L1 和 SatoshiNet 的 UTXO、交易、确认数和资产状态 |
| Recovery | 重启后恢复未完成事务；服务端不可用时发起强制关闭 |
| Safety Monitor | 验证承诺交易、惩罚交易覆盖、CSV 清扫窗口和本地备份完整性 |

## 连接 STP Server

客户端连接 core node 前必须确认：

1. 服务端网络与用户钱包网络一致，例如 mainnet/testnet。
2. 服务端公钥来自可信发现流程或用户显式配置。
3. 服务端声明的链、协议版本、费用策略和 CSV 参数可被客户端接受。
4. 客户端能独立查询 BTC L1 和 SatoshiNet 状态，不能只依赖 STP Server 的单方返回。

建议服务发现返回以下信息：

```json
{
  "protocol": "stp",
  "version": "1",
  "chain": "testnet",
  "server_pubkey": "02...",
  "server_node_id": "02...",
  "endpoint": "https://core-node.example/stp",
  "features": [
    "open",
    "unlock",
    "lock",
    "lock-with-expand",
    "splicing-in",
    "splicing-out",
    "close"
  ],
  "csv_delay": 1000
}
```

## 统一消息信封

所有需要认证的消息建议使用统一信封：

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

签名要求：

1. `signature` 之外的所有字段参与签名。
2. 序列化必须确定性，推荐 canonical JSON 或其他固定编码。
3. 接收方必须校验发送方公钥、通道身份、链 ID 和消息类型。
4. 任一消息若改变承诺状态，必须携带当前 `commit_height`。
5. 客户端必须拒绝承诺高度回退、链 ID 不匹配、签名无效或资产数量不一致的消息。

## 成功响应的证据字段

对于会移动资产或推进通道状态的操作，成功响应不能只返回 `ok:true`。客户端还应返回可追踪、可验证的证据字段：

| 字段 | 说明 |
| --- | --- |
| `transaction_id` / `reservation_id` | 后续轮询事务状态的稳定句柄 |
| `tx_ids` | 已知 BTC L1 / SatoshiNet / commitment / punish 交易 ID |
| `channel_id` | 本次操作作用的通道 |
| `status` | 标准化状态，例如 `BROADCASTED`、`READY_DEGRADED`、`CONFIRMED`、`FAILED` |
| `commit_height_before` / `commit_height_after` | 如果通道状态前进，应返回承诺高度变化 |
| `next_check` | Agent 下一步应调用的查询或等待条件 |
| `safety` | 本次操作后的安全摘要，或明确提示立即调用 `stp.safety_snapshot` |

Agent 应根据这些字段继续轮询和验证，不应只根据余额变化判断操作成功。

## 操作接口建议

为了让钱包、后端服务、CLI 和 AI Agent 能复用同一套能力，建议第三方客户端暴露一个语言无关的 JSON 操作接口。可以是 CLI、HTTP 或进程内函数，语义保持一致即可。

操作接口分为两组：

1. `wallet.*`：钱包生命周期、助记词导入/导出、密码修改、普通资产发送和普通交易追踪。
2. `stp.*`：STP 通道生命周期、open/close、splicing、lock/unlock、lock-with-expand、通道事务追踪和安全控制。

对 AI Agent 来说，安全控制接口必须和价值移动接口同等重要。Agent 在发起价值移动前，应先查询 `stp.safety_snapshot`；在发现 peer 离线、commit height 异常、旧承诺交易上链或本地状态缺失时，应停止普通操作，进入 force-close、punish 或备份恢复流程。

### `wallet.status`

查询钱包和 WASM 初始化状态。

```json
{
  "op": "wallet.status",
  "chain": "testnet"
}
```

### `wallet.create`

创建钱包。正式 PWA adapter 应在 PWA 内完成创建和备份确认；本地 testnet 开发 adapter 可以返回助记词，方便导入 PWA。

```json
{
  "op": "wallet.create",
  "chain": "testnet",
  "purpose": "agent-stp-testnet-wallet"
}
```

### `wallet.import`

导入助记词。生产环境不应在响应中回显助记词。

```json
{
  "op": "wallet.import",
  "chain": "testnet",
  "mnemonic": "twelve words..."
}
```

### `wallet.export_mnemonic`

导出助记词。该操作必须经过钱包侧授权和密码验证；推荐由 PWA 弹窗完成密码输入，Agent 只接收授权后的导出结果。

```json
{
  "op": "wallet.export_mnemonic",
  "chain": "testnet",
  "wallet_id": 1760000000000000
}
```

### `wallet.change_password`

修改钱包密码。旧密码和新密码应在 PWA 或本地安全提示中输入，不应通过 Agent JSON 明文传递。

```json
{
  "op": "wallet.change_password",
  "chain": "testnet",
  "wallet_id": 1760000000000000
}
```

### `wallet.send_assets`

从钱包地址直接发送 BTC L1 或聪网资产，不改变 STP 通道状态。

```json
{
  "op": "wallet.send_assets",
  "chain": "testnet",
  "layer": "satoshinet",
  "asset": "plain:sat",
  "amount": "1000",
  "to": "tb1p...",
  "fee_rate": 1
}
```

### `wallet.transaction`

查询普通钱包交易状态。

```json
{
  "op": "wallet.transaction",
  "chain": "testnet",
  "transaction_id": "wallet-tx-001"
}
```

### `stp.status`

查询客户端、链、服务端和通道状态。

请求：

```json
{
  "op": "stp.status",
  "chain": "testnet"
}
```

执行前，客户端必须确认：

- 钱包有足够白聪支付初始容量和 BTC L1 fee。
- 目标 peer 是 core node，而不是 bootstrap node。普通用户客户端连接 core node 打开通道不需要 stake asset。
- 只有当本节点准备升级为 core node、并连接 bootstrap node 建立准入通道时，才需要按当前网络规则在 bootstrap 通道地址上准备 stake asset。

响应：

```json
{
  "ok": true,
  "chain": "testnet",
  "wallet": {
    "ready": true,
    "address": "tb1p..."
  },
  "server": {
    "ready": true,
    "pubkey": "02..."
  },
  "channels": [
    {
      "channel_id": "tb1q...",
      "status": "READY",
      "commit_height": 12
    }
  ]
}
```

### `stp.open`

打开通道。

请求：

```json
{
  "op": "stp.open",
  "chain": "testnet",
  "server": "https://core-node.example/stp",
  "amount_sats": 50000,
  "fee_rate": 10,
  "utxos": [],
  "memo": "optional"
}
```

响应：

```json
{
  "ok": true,
  "channel_id": "tb1q...",
  "tx_ids": ["funding-txid"],
  "transaction_id": "stp-tx-001",
  "status": "FUNDING_BROADCASTED"
}
```

### 承诺余额与可花费 UTXO

STP 客户端必须区分两类状态：

1. **commitment balance**：最新承诺交易中已经分配给某一方的资产余额。
2. **spendable UTXO**：BTC L1 或 SatoshiNet indexer 已确认、客户端可以作为下一笔交易输入使用的 UTXO。

在 splicing-in、expand 或恢复流程中，资产可能已经进入最新 commitment 的资产分配，但对应的 L1 funding 交易还未确认，或对应的 L2 anchor 输出仍在 `pendingUtxosL2`。这种状态下，安全快照可以证明双方已经对新状态签名，也可以证明旧状态有 punish coverage，但客户端仍不能把该资产作为 unlock / lock 的输入。

第三方客户端应按以下规则处理：

1. 价值移动前先查询 channel 状态、pending reservation、L1/L2 tx 可见性和 safety snapshot。
2. 对刚 splicing-in 或 expand 的资产，必须等对应 L2 anchor 从 `pendingUtxosL2` 进入可花费 `UtxosL2` 后，才允许 unlock。
3. 如果 L1 splicing tx 仍是 `0` confirmation，不要重复发起同一 splicing，也不要使用相同 UTXO 发起新操作。
4. 如果 commitment balance 已经包含资产，但 indexer 还没有返回可花费 UTXO，客户端应返回 `ASSET_PENDING_CONFIRMATION` 或等价状态，而不是返回余额不足。
5. Agent 在该状态下的正确动作是继续轮询 reservation 和 L1/L2 indexer，直到原事务收敛或明确失败。

### `stp.unlock`

把通道资产释放到聪网个人地址。

```json
{
  "op": "stp.unlock",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "ordx:demo",
  "amount": "100",
  "to": "tb1p...",
  "fee_rate": 1
}
```

实现注意：

- 聪网 L2 UTXO 可以小于 330 sats，也可以是 0；不要套用 BTC dust 判断。
- BRC20 和 Runes 在 L2 不需要绑定聪，因此 L2 转账时可以由 `Value=0` 的聪网 UTXO 携带资产。
- BTC L1 上携带 BRC20/Runes 转移资产的 UTXO 仍然受 L1 输出限制，当前通常使用最小的 330 sats。
- ORDX 必须绑定聪；客户端必须根据 ORDX 资产数量和 `bindingSat` 计算输出需要的聪数量。
- ORDX ticker 铸造 UTXO 常伴生 Ordinals NFT。当前 STP 不支持将 Ordinals NFT ascend 到聪网，splicing-in 时会从输出 `TxAssets` 中删除并忽略这类资产；客户端不应要求 Ordinals NFT 在 L2 侧出现。
- 如果一个 BTC L1 UTXO 同时携带多种资产，`stp.splicing_in` 只 ascend 请求参数 `asset` / `assetName` 明确指定的那一种资产；同一 UTXO 中其他 ORDX、Runes、BRC20 transfer 或 Ordinals NFT 资产都按忽略处理。第三方客户端不得把未指定资产纳入 L2 守恒校验。
- 面向 Agent 的 adapter 不应暴露 splicing-in 资产输入选择。adapter 内部会优先排除同时包含多种可 ascend 资产的 UTXO；如果必须使用，应在预览中说明哪些资产会 ascend、哪些资产会被忽略。
- 白聪 unlock 只需要 Agent 指定释放金额；客户端或 adapter 应确保被选通道输入覆盖 `amount + SatoshiNet fee`。
- 如果返回 `no enough sats`，先检查 adapter preflight、可花费余额和请求金额，不要立即判断通道余额异常。

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

实现注意：

- 白聪 lock 的 `amount` 是净回锁进通道的数量。
- 钱包输入还需要额外覆盖 SatoshiNet fee；例如地址只有 660 sats 且 fee 为 10 sats 时，应 lock 650 sats。
- 容量不足时使用 `stp.lock_with_expand`，不要让用户手工绕回 BTC L1。

### `stp.lock_with_expand`

当通道容量不足时，通过穿越合约和 expand 恢复资产通道控制权。

```json
{
  "op": "stp.lock_with_expand",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "ordx:demo",
  "amount": "100",
  "fee_rate": 10
}
```

客户端应在直接 lock 容量不足时优先使用该能力，而不是让用户手工退出 L1 再重新进入通道。

### `stp.splicing_in`

把 BTC L1 资产纳入通道。

```json
{
  "op": "stp.splicing_in",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "runes:EXAMPLE",
  "amount": "1000",
  "utxos": [],
  "fee_rate": 10
}
```

### `stp.splicing_out`

把通道资产退出到 BTC L1。

```json
{
  "op": "stp.splicing_out",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "asset": "ordx:demo",
  "amount": "100",
  "to_l1_address": "tb1p...",
  "fee_rate": 10
}
```

实现注意：

- 白聪 splicing-out 可以用通道白聪支付退出所需费用和服务费。
- Runes、BRC20、ORDX 等协议资产 splicing-out 需要普通 BTC 资金支付 L1 网络费；fee 输入由 adapter 内部选择。
- 带资产 UTXO 中包含的 sats 不应作为普通 fee 输入使用。
- 如果 adapter 报告缺少安全的普通 BTC fee 资金，推荐补充外部普通 BTC，或先做一笔白聪 splicing-out 并等待确认；不要让 Agent 手工指定 fee 输入。
- BRC20 splicing-out 所需的 transfer 输出由 adapter 内部选择；没有合适 transfer 输出时，adapter 应自动规划并铸造新的 transfer inscription。

### `stp.close`

关闭通道。

```json
{
  "op": "stp.close",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "mode": "cooperative",
  "fee_rate": 10
}
```

`mode` 可以是 `cooperative` 或 `force`。客户端应优先协商关闭，只有 peer 不在线或状态异常时才强制关闭。

### `stp.safety_snapshot`

查询通道安全快照。Agent 应在任何价值移动前调用该接口。

```json
{
  "op": "stp.safety_snapshot",
  "chain": "testnet",
  "channel_id": "tb1q..."
}
```

响应应包含：

- channel point
- commit height
- local / remote commitment txid
- local / remote balance
- CSV delay
- force close readiness
- punish coverage
- state backup status

### `stp.commitment_export`

导出当前承诺交易和只读校验材料，供 Agent 审核和离线备份。

```json
{
  "op": "stp.commitment_export",
  "chain": "testnet",
  "channel_id": "tb1q..."
}
```

该接口可以返回承诺交易 hex/json、Merkle roots、余额和通道参数，但不得导出私钥、助记词或未授权的 revocation secret。

### `stp.punish_status`

查询旧承诺状态的惩罚覆盖。

```json
{
  "op": "stp.punish_status",
  "chain": "testnet",
  "channel_id": "tb1q..."
}
```

Agent 应确认每个已撤销 remote commitment 都有可验证、可广播的 punish tx。

### `stp.punish_build`

当发现某个 remote commitment 上链时，构造并验证惩罚交易。

```json
{
  "op": "stp.punish_build",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "commit_txid": "...",
  "broadcast": false
}
```

`broadcast:false` 用于 dry-run 验证，`broadcast:true` 用于立即保护资产。adapter 不应把 revocation secret 直接返回给 Agent；应返回已签名 punish tx 或广播结果。

### `stp.force_close_plan`

当 peer 离线或状态异常时，生成强制关闭计划。

```json
{
  "op": "stp.force_close_plan",
  "chain": "testnet",
  "channel_id": "tb1q..."
}
```

响应应说明可广播的 local commitment tx、CSV delay、预计 sweep 高度、sweep 构造条件和风险。

### 测试网旧承诺交易演练接口

为了让第三方客户端和 AI Agent 在测试网上验证惩罚能力，core node 可以提供测试专用接口：

- `stp.test_retain_server_commitment`
- `stp.test_broadcast_retained_server_commitment`

这些接口只允许在测试网执行。core node 必须在接口入口做运行时网络检查：非测试网请求必须直接返回错误；生产主网 RPC 配置不得允许这些接口执行。请求还必须携带 `confirm_unsafe_test_only=true`，避免普通客户端误触发。

演练流程：

1. client 通过 `stp.safety_snapshot` 记录当前 `commit_height`。
2. client 调用 `stp.test_retain_server_commitment`，要求 server 保留当前 server-local commitment。
3. client 执行一次正常通道状态更新，使 `commit_height` 前进。
4. client 确认旧 remote commitment 已有 punish coverage。
5. client 调用 `stp.test_broadcast_retained_server_commitment`，要求 server 广播之前保留的旧 server commitment。
6. client 检测该旧 commitment 上链后，调用 `stp.punish_build` 和 `stp.punish_broadcast`。

如果第 4 步失败，client 不应继续触发旧承诺广播，因为这说明本地还不能证明资产安全。

### `stp.transaction`

查询未完成事务。

```json
{
  "op": "stp.transaction",
  "chain": "testnet",
  "transaction_id": "stp-tx-001"
}
```

响应必须包含当前状态、关联交易、下一步建议和错误信息。

## 状态与恢复

客户端必须持久化：

1. 通道 ID、双方公钥、通道地址。
2. 通道状态、承诺高度、最新承诺交易。
3. 最新状态之前所有已撤销状态的惩罚材料。
4. 未完成事务 ID、类型、状态、关联交易。
5. 用户授权的目标地址、金额、手续费率和资产名称。

恢复流程：

1. 客户端启动后先读取本地状态。
2. 查询 BTC L1 和 SatoshiNet 链上交易状态。
3. 查询 STP Server 当前通道状态。
4. 若本地最新承诺状态比服务端返回更可信，不能盲目覆盖。
5. 若服务端不可用，客户端必须保留强制关闭能力。

### Reopen 恢复规则

当通道已经关闭，但通道地址仍持有属于 client 的资产时，第三方客户端应优先使用 `stp.reopen` 恢复同一个 client-core channel，而不是重新创建无关通道。

Reopen 前必须查询 SatoshiNet channel ledger：

1. 如果 ledger 能证明该通道地址有历史 open / ascending / descending / close 记录，客户端应把本次操作视为已有通道恢复。
2. 如果通道地址上已有满足最小容量要求的白聪 UTXO，可以直接以该 UTXO 作为新 channel point。
3. 如果找不到满足容量要求的白聪 UTXO，客户端可以让 reopen 路径由用户钱包创建新的 BTC L1 funding 输出。
4. 新 funding 交易未确认前，客户端只能查询 `stp.status`、`stp.transaction`、L1 tx 状态、L2 ledger 和 peer 状态，不能发起 unlock、lock、splicing 或 ordinary close。
5. 只有 L1 funding 已确认、SatoshiNet anchor 状态完成、local/core 双方均进入 ready 后，才允许继续普通价值移动操作。

### 结果未知的恢复规则

第三方客户端必须把网络错误分成两类：

| 类型 | 示例 | 行为 |
| --- | --- | --- |
| 明确失败 | 签名无效、余额不足、资产不匹配、地址非法 | 终止事务并暴露错误 |
| 结果未知 | timeout、连接中断、服务暂不可用、响应状态不确定 | 保留事务，查询链上和 peer 状态，不立即重发 |

当结果未知发生在广播之后，客户端应假设交易可能已经到达 BTC L1 或 SatoshiNet 节点。正确流程是：

1. 保存或恢复本地事务记录、通道快照、相关 txid 和 UTXO 锁定信息。
2. 查询 BTC L1 / SatoshiNet indexer，确认相关 txid 是否可见。
3. 查询本地和 STP Server 的通道状态、承诺高度和 pending reservation。
4. 若交易可见或 pending 事务存在，继续轮询/推进原事务。
5. 若双方状态都未前进、没有 pending 事务、相关交易也不可见，才允许重新执行，并由 adapter 重新做 preflight 和输入选择。

当结果未知发生在 final revoke-and-ack 或 peer notification 阶段，客户端也不能只根据 HTTP 错误回滚。它必须先确认 peer 是否已经接受新承诺、是否已广播 L1/L2 交易、以及本地是否仍持有足够的最新承诺和惩罚材料。否则，简单重试可能导致双花 UTXO、重复 anchor 或双方通道状态分叉。

Agent 适配器应把这类错误规范化为可行动错误，例如 `NETWORK_RESULT_UNKNOWN`，并返回当前 reservation、txid 和下一步查询建议。

### 惩罚覆盖查询不确定

客户端不能把 `punish_status` 的不可验证结果当成普通空结果。无法读取或验证某个 revoked commitment 的惩罚交易时，应规范化为：

```json
{
  "ok": false,
  "error": {
    "code": "PUNISH_COVERAGE_UNKNOWN",
    "message": "The wallet cannot prove punish coverage for revoked remote commitments."
  }
}
```

`PUNISH_COVERAGE_UNKNOWN` 与 `PUNISH_COVERAGE_MISSING` 一样，都会阻止新的价值移动操作。区别在于：前者表示安全可观测性失败，后者表示已经明确缺少惩罚材料。第三方客户端应先让钱包或 adapter 重新导出可验证证据，再继续 splicing、unlock、lock 或 close。

## 安全要求

第三方客户端必须遵守以下规则：

1. 主网转移前必须让用户确认资产、金额、目标地址、手续费率和操作类型。
2. 新承诺状态未完整验证前，不得释放旧状态撤销秘密。
3. 不接受承诺高度回退。
4. 不接受链 ID 不匹配的服务端响应。
5. 不接受目标地址被服务端替换的交易。
6. 不复用已锁定或未确认事务中的 UTXO。
7. BRC20 和 Runes 操作必须展示 commit/reveal 或长确认流程。
8. lock 容量不足时，应优先尝试 lock-with-expand。
9. peer 离线时不得发起普通协作动作，强制关闭除外。
10. 客户端必须能导出或广播最新强制关闭交易。
11. 客户端必须能向 Agent 证明当前 local commitment tx 可用。
12. 客户端必须能证明旧 remote commitment 有 punish coverage，或者明确报告缺失。
13. 客户端不得把 revocation secret 暴露给未授权的外部 Agent；应提供已签名 punish tx 或本地广播能力。
14. Agent 无法取得安全快照时，应停止新的价值移动。

## 测试矩阵

第三方客户端至少应覆盖：

| 场景 | 预期 |
| --- | --- |
| 打开通道 | funding 确认后进入 `READY` |
| Unlock 白聪 | 通道余额减少，聪网个人地址余额增加 |
| Lock 白聪 | 聪网个人地址余额减少，通道余额增加 |
| Lock With Expand | 容量不足时能通过扩容恢复通道控制权 |
| Splicing-In ORDX/Runes/BRC20 | 资产按协议规则进入通道 |
| Splicing-Out | 资产从通道退出到 BTC L1 地址 |
| 协商关闭 | 无 CSV 等待，资产按最新状态退出 |
| 强制关闭 | 对方离线时可广播最新承诺交易 |
| 旧状态惩罚 | 广播旧承诺交易会被撤销秘密惩罚 |
| 重启恢复 | 未完成事务能继续追踪 |

## STP Skill 适配

为了让 AI Agent 能直接使用第三方客户端，建议实现统一的 JSON 适配器：

```bash
stp-client --json '{"op":"stp.status","chain":"testnet"}'
```

适配器可以由任何语言实现。Agent skill 只需要知道如何调用该适配器、解析 JSON 响应、执行安全确认和轮询事务。

对于面向用户的钱包场景，推荐适配器由 SAT20 PWA Wallet 提供。Agent 通过本地 HTTP、浏览器 postMessage 桥接或其他受权限控制的通道发送 JSON 请求；PWA 校验来源、网络、用户授权和请求有效期，然后调用内部 WASM 引擎执行协议操作。若操作需要用户确认，适配器应返回 `AUTH_REQUIRED` 或等待确认后的事务结果，而不是让 Agent 绕过钱包确认。

对于节点联调和 testnet 自动化，也可以使用运行中的 transcend/STP 节点作为 adapter 后端。此时 adapter 将统一 JSON 操作映射到节点本地管理 RPC，例如 open、close、splicing-in、splicing-out、unlock、lock 和 lock-with-expand。该形态适合开发者和 core node 运维者，不适合作为普通用户主网钱包的默认安全边界。

本目录提供一个可安装的 Agent skill 草案：

- `skills/stp-core-node-client/SKILL.md`

该 skill 当前包含三类脚本：

| 脚本 | 作用 |
| --- | --- |
| `install.sh` | 从 `https://github.com/sat20-labs/docs` 一键安装 `stp-core-node-client` skill |
| `stp_adapter.py` | 通用 JSON 转发器，根据 `STP_ADAPTER_URL` 或 `STP_CLIENT_CMD` 调用实际 adapter |
| `stp_workspace_wallet_adapter.py` | 本地 workspace testnet 钱包 bootstrap/status/send/tx 验证 |
| `stp_transcend_rpc_adapter.py` | 连接已运行的 transcend 本地管理 RPC，执行 STP 通道操作 |

推荐使用一键安装命令：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/circulation/stp/skills/stp-core-node-client/scripts/install.sh | bash
```

默认会安装到 `~/.codex/skills/stp-core-node-client`。其他 Agent 可以通过 `STP_SKILLS_DIR=/path/to/agent/skills` 指定安装目录：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/circulation/stp/skills/stp-core-node-client/scripts/install.sh | STP_SKILLS_DIR=/path/to/agent/skills bash
```

也可以把整个 `stp-core-node-client` 目录复制到目标 Agent 的 skills 目录，或通过团队/插件分发机制发布。安装后，Agent 可以按 skill 的流程使用任意兼容适配器与 core node 交互。

skill 本身不包含私钥、不保存资产状态，也不直接绑定某一种客户端实现。它只定义 Agent 工作流、安全护栏和适配器契约；真正的钱包签名、交易构造、状态持久化和网络通信由第三方 STP 客户端适配器完成。
