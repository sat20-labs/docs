# STP Agent 验证矩阵与数据缺口

> 本文面向 AI Agent、PWA adapter 和第三方 STP 客户端实现者。目标是回答两个问题：Agent 如何独立验证“用户仍掌控资产安全”；如果验证失败或缺少数据，系统还需要补充哪些接口、索引或证据。

## 验证原则

Agent 不能只根据余额、服务端口头状态或单个接口返回判断 STP 安全。每一次价值移动前，Agent 都应把以下四类证据组合起来：

1. BTC L1 证据：channel point、funding/splicing/commitment/punish tx 是否存在、是否确认、是否被花费。
2. SatoshiNet L2 证据：anchor/deAnchor、unlock/lock tx、L2 UTXO 是否可花费、资产数量是否一致。
3. 本地钱包证据：最新 local/remote commitment、commit height、CSV、punish coverage、pending reservation 是否持久化。
4. peer/core node 证据：peer 的 channel status、commit height、channel point 与本地是否一致。

只有这些证据互相一致，Agent 才能把通道标记为 `READY_SAFE`。

## 最小验证矩阵

| 场景 | Agent 要验证什么 | 必需数据 | 缺失时行为 |
| --- | --- | --- | --- |
| open 后 | funding tx 已确认，local/remote commitment 都指向 channel point | L1 funding tx、channel point、commitment tx、channel status | 标记 `READY_DEGRADED`，只轮询不移动资产 |
| splicing-in 后 | L1 funding/splicing tx 已确认，L2 anchor 已进入可花费 UTXO 或处于明确 pending | L1 tx 状态、L2 anchor tx、`pendingUtxosL2` / `UtxosL2` | 不 unlock 该资产，继续轮询 |
| expand 后 | 通道地址资产已被纳入最新 commitment，且未重复 anchor | L1 UTXO、L2 ascend ledger、commit height、asset roots | 停止 expand，要求 ledger 证据 |
| unlock 前 | 通道中有足够资产，目标资产在 `UtxosL2` 可花费，punish coverage 完整 | safety snapshot、L2 spendable UTXO、punish status | 不发起 unlock |
| lock 前 | 个人地址资产 UTXO 可花费，通道容量足够或可 lock-with-expand，punish coverage 完整 | personal L2 UTXO、capacity、safety snapshot | 不发起 lock，或规划 lock-with-expand |
| splicing-out 前 | 通道资产足够，L1 目标地址有效，adapter 能安全构造 L1 fee 输入和退出交易 | safety snapshot、adapter preflight、deAnchor plan、L1 tx plan | 不发起 splicing-out |
| peer 离线 | 用户持有最新 local commitment，可规划 force close 和 CSV sweep | local commitment、CSV、sweep plan | 停止协作操作，提示用户恢复或强制关闭 |
| remote commitment 上链 | 判断该 commitment 是最新状态还是旧状态 | L1 commitment txid、current remote commitment、revoked commitment index | 无法判断则标记 `UNSAFE` |
| old commitment 上链 | punish tx 可构造、可验证、可广播 | revoked commitment、punish tx set、L1 tx visibility | 优先 punish；缺数据则报告 `PUNISH_COVERAGE_MISSING` |
| punish 后 | punish tx 已在 L1 可见/确认，旧 channel 不再作为普通通道运行 | punish txids、channel point spent 状态、fresh channel safety | 不继续旧通道 value-moving |

## Agent 的验证步骤

### 1. 建立通道安全快照

Agent 首先调用 `stp.safety_snapshot`。最低返回应包含：

- `channel_id`
- `channel_address`
- `chan_point`
- `status`
- `commit_height`
- `csv_delay`
- `local_commitment_present`
- `remote_commitment_present`
- `local_balance`
- `remote_balance`
- `l2_spendable_balance`
- `l2_pending_balance`
- `merkle_roots`
- `punish_coverage`
- `state_backup`

如果没有 `stp.safety_snapshot`，Agent 可以临时从 `stp.status` 和 channel detail 推导，但只能作为过渡方案；正式客户端必须提供标准化 safety snapshot。

### 2. 校验承诺交易

Agent 要验证：

1. local commitment 和 remote commitment 都存在。
2. commitment input 指向当前 `chan_point`。
3. commitment 中的资产归属与 `local_balance` / `remote_balance` 一致。
4. `commit_height` 没有回退。
5. CSV delay 与用户预期一致。

缺少 commitment tx 时，Agent 不能发起普通价值移动，因为用户无法证明 peer 离线时自己能退出。

### 3. 校验惩罚覆盖

Agent 要把 `punish_coverage` 归一化成以下状态：

| 状态 | 含义 | 行为 |
| --- | --- | --- |
| `NO_REVOKED_REMOTE_STATE` | 当前没有已撤销 remote commitment | 可继续，但状态推进后必须再检查 |
| `COVERED` | 每个 revoked remote commitment 都有 verified / broadcastable punish tx | 可继续普通价值移动 |
| `PUNISH_COVERAGE_UNKNOWN` | 查询失败、索引缺失、状态不一致 | 停止普通价值移动 |
| `PUNISH_COVERAGE_MISSING` | 已发现 revoked commitment 但缺少 punish tx | 停止普通价值移动并进入恢复 |

Agent 需要确认每个 revoked commitment 至少有：

- `commit_txid`
- `punish_txids`
- `verified=true`
- `broadcastable=true`
- `broadcasted` 或可广播状态

### 4. 校验 L1/L2 资产可花费性

Agent 必须分开看三种余额：

| 余额 | 含义 |
| --- | --- |
| commitment balance | 最新承诺状态中的资产归属 |
| `l2_pending_balance` | 已进入承诺或 anchor 流程，但 L2 UTXO 仍未可花费 |
| `l2_spendable_balance` | unlock/lock 可直接选择的 L2 UTXO 集合 |

刚 splicing-in 或 expand 的资产，可能已经出现在 commitment balance 中，但仍在 `pendingUtxosL2`。Agent 不能因为余额出现就 unlock，必须等它进入 `l2_spendable_balance`。

### 5. 校验结果未知

遇到 timeout、连接中断、服务暂不可用等未知网络结果时，Agent 不能直接判定失败。验证流程是：

1. 查询本地 reservation。
2. 查询 local/core commit height 是否变化。
3. 查询关联 L1/L2 tx 是否可见。
4. 如果 reservation 存在、tx 可见或任一方状态前进，进入轮询/恢复，不重发。
5. 只有无 reservation、无 tx 可见、双方仍在同一旧 `READY_SAFE` 状态，才允许重新做 adapter preflight 后重试。

## 需要补齐的数据和接口

以下缺口会直接影响 Agent 的独立验证能力。

| 缺口 | 为什么重要 | 建议补充 |
| --- | --- | --- |
| 标准化 `stp.safety_snapshot` | Agent 需要一个统一入口判断 `READY_SAFE`，不能解析不同实现的 channel detail | PWA adapter 和第三方客户端都返回同一 JSON schema |
| commitment export 标准化 | Agent 需要检查 commitment input、output、txid 和资产归属 | `stp.commitment_export` 返回 local/remote commitment hex/json、txid、balances、roots |
| punish coverage 标准化 | Agent 需要知道每个 revoked commitment 是否有 verified punish tx | `stp.punish_status` 返回 `NO_REVOKED_REMOTE_STATE` / `COVERED` / `UNKNOWN` / `MISSING` |
| L2 anchor spendable 状态 | Agent 需要区分 pending anchor 与可花费 UTXO | safety snapshot 必须包含 `l2_spendable_balance` 和 `l2_pending_balance` |
| L2 channel ledger 查询 | rebuild/expand 需要判断 L1 UTXO 是否已 anchor 或来自 deAnchor 返回 | L2 indexer 提供 channel address 的 ascend/deAnchor 记录、L1 txid/outpoint、资产摘要 |
| deAnchor returned output 元数据 | splicing-out 后余额回到通道地址时，Agent 需要知道是否需要重新 anchor | descending v2 记录 L1 txid、返回通道地址的 output、资产和金额 |
| force-close plan | peer 离线时 Agent 需要向用户解释退出路径 | `stp.force_close_plan` 返回 local commitment、CSV、sweep earliest time/height |
| sweep dry-run | CSV 到期后 Agent 要验证 sweep 可构造但不一定立即广播 | 已拆成 build / sign / verify / optional broadcast，`broadcast:false` 不发交易 |
| transaction/reservation 轮询 | 网络不稳定时 Agent 需要持续跟踪 pending 事务 | PWA adapter 补齐 `wallet.transaction` / `stp.transaction` / reservation 查询 |
| explorer / indexer URL 标准化 | 视频、白皮书和 Agent 报告需要可点击证据 | adapter 返回每个 txid 的 L1/L2 explorer URL 和 indexer URL |
| safety backup 状态 | Agent 需要知道通道状态和惩罚材料是否已持久化 | safety snapshot 增加 `state_backup.present`、`last_updated`、`backup_id` |

## PWA Adapter 必须优先补齐

面向 AI Agent 的 PWA 钱包，应优先实现以下接口：

1. `wallet.status`：钱包、网络、地址、WASM ready 状态。
2. `stp.status`：core node、通道列表、reservation 列表。
3. `stp.safety_snapshot`：Agent 的价值移动前置门。
4. `stp.transaction`：返回 reservation、txid、L1/L2 可见性、确认数和下一步建议。
5. `stp.commitment_export`：只读导出承诺交易，不暴露私钥。
6. `stp.punish_status`：证明旧 remote commitment 的惩罚覆盖。
7. `stp.punish_build` / `stp.punish_broadcast`：保护性操作，广播需钱包授权。
8. `stp.force_close_plan`：peer 不可用时给出退出计划。

这些接口补齐后，Agent 才能在不接触私钥的情况下，对用户说清楚：

- 资产现在在哪一层、哪一个地址或哪一个通道中。
- 当前是否有最新承诺交易。
- 如果 core node 离线，用户如何退出。
- 如果 core node 广播旧状态，钱包如何惩罚。
- 哪些资产已经可花费，哪些仍在 pending。
- 下一步操作是否安全。

## Agent 面向用户的验证报告模板

Agent 完成一次 value-moving 前，应能生成类似报告：

```text
STP 安全检查结果：READY_SAFE

通道：tb1q...
channel point：<txid:vout>
commit height：8
local commitment：present
remote commitment：present
punish coverage：COVERED
L2 spendable：brc20:f:sgas=100, runes:f:BITCOIN•TESTNET=10
L2 pending：empty

结论：当前可以执行本次 unlock。用户钱包持有最新承诺交易；
如果 core node 广播旧状态，钱包已有可验证、可广播的 punish tx。
```

如果缺数据，应报告：

```text
STP 安全检查结果：PUNISH_COVERAGE_UNKNOWN

缺少数据：无法读取 revoked remote commitment 的 punish coverage。
本次不执行 splicing/unlock/lock。
需要钱包或 STP adapter 重新导出可验证的 punish coverage 后再继续。
```

## 当前优先级

1. 冻结 `stp.safety_snapshot`、`stp.commitment_export`、`stp.punish_status`、`stp.transaction` 的 v1 JSON schema。
2. 将测试网演练中的真实 txid 作为验收样例，要求新客户端能复现同类验证报告。
3. 让 L2 indexer 能完整返回 channel ledger、anchor/deAnchor 和 returned output 元数据。
4. 用真实测试网样例固化 `stp.sweep_build` 的 dry-run 和授权广播响应 schema。
