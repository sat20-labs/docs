# STP Agent 资产安全控制指南

> 本文面向 AI Agent、钱包适配器和第三方 STP 客户端。目标是让 Agent 不只是会操作 STP，还能持续判断“资产是否仍完全在用户可控制的安全边界内”。

## 核心原则

STP 的安全性不来自对 core node 的信任，而来自用户客户端掌握的链上退出能力：

1. 用户资产进入通道后，BTC L1 资产锁定在用户与 core node 的 2-of-2 通道地址中。
2. 每一次通道状态变化，都必须产生新的承诺状态。
3. 用户客户端必须持有最新可验证的承诺交易。
4. 用户客户端只应在新承诺交易完整可用后，才释放旧状态撤销材料。
5. 如果对手广播已撤销的旧承诺交易，用户客户端或 watchtower 必须能构造并广播惩罚交易。
6. 如果对手离线或拒绝协作，用户客户端必须能发起强制关闭，并在 CSV 延迟后清扫属于自己的资产。

因此，Agent 的职责不是替代钱包保管私钥，而是持续检查这些安全条件是否成立，并在风险出现时选择正确的恢复动作。

关于每个场景应检查哪些证据、缺少哪些数据时必须停止操作，以及 PWA adapter / indexer 还需要补齐哪些接口，见 [STP Agent 验证矩阵与数据缺口](agent-verification-and-data-gaps.md)。

## Agent 必须理解的安全材料

一个 Agent 要有信心控制自己的 STP 资产，至少要能读取或确认以下材料已经由钱包安全保存：

| 安全材料 | 用途 |
| --- | --- |
| channel id / channel address | 识别当前通道和 2-of-2 控制地址 |
| channel point | BTC L1 funding outpoint，是承诺交易的输入 |
| commit height | 当前承诺状态高度，必须单调递增 |
| local commitment tx | 本方可广播的最新承诺交易，用于强制关闭 |
| remote commitment tx | 对方可能广播的承诺交易，用于监控旧状态作弊 |
| local / remote balances | 当前状态下双方资产归属 |
| CSV delay | 强制关闭后本方输出可清扫的等待窗口 |
| revocation data | 已撤销旧状态的惩罚材料 |
| punish tx set | 对旧承诺交易的预签名或可构造惩罚交易 |
| sweep tx capability | 强制关闭后清扫本方输出的能力 |
| Merkle roots | 通道资产状态完整性校验材料 |

这些材料必须持久化保存。Agent 可以读取摘要和交易材料，但不应直接接触私钥、助记词或未授权的 revocation secret。

## Agent 安全状态机

Agent 应把每个通道分成以下安全状态：

| 状态 | 含义 | Agent 行为 |
| --- | --- | --- |
| `NO_CHANNEL` | 没有通道 | 可 open |
| `OPENING` | funding 已广播但未确认 | 记录 funding txid，轮询确认，不发起 splicing/lock/unlock |
| `READY_SAFE` | 通道可用，最新承诺和惩罚覆盖完整 | 可执行普通资产操作 |
| `READY_DEGRADED` | 通道可用，但本地缺少安全材料或备份不完整 | 停止价值移动，先修复备份或导出安全快照 |
| `PEER_OFFLINE` | peer 不可用 | 停止协作操作，准备 force close 路径 |
| `FORCE_CLOSING` | 本方承诺交易已广播 | 轮询 CSV，到期后 sweep |
| `REMOTE_COMMIT_SEEN` | 发现对方承诺交易上链 | 判断是否旧状态；若是旧状态，立即 punish |
| `PUNISH_REQUIRED` | 旧承诺交易已上链且存在惩罚材料 | 广播 punish tx |
| `UNSAFE` | 无法证明最新承诺或无法惩罚旧状态 | 停止操作并向用户报告风险 |

Agent 只有在 `READY_SAFE` 时才应主动执行 splicing、lock、unlock 或 close。任何无法解释的状态回退、签名异常、余额不一致、commit height 回退，都应进入 `UNSAFE`。

`READY_SAFE` 证明的是承诺交易和惩罚能力安全，不直接证明某个刚 ascend 的 L2 输出已经可花费。Agent 必须把承诺资产余额和 SatoshiNet UTXO 可花费性分开检查：`local_balance` / `remote_balance` 用于证明承诺状态，`UtxosL2` / `l2_spendable_balance` 用于证明 unlock/lock 可使用的输入。仍在 `pendingUtxosL2` / `l2_pending_balance` 的资产不能发起 unlock。

## 安全检查清单

Agent 在每次价值移动前应执行：

1. 调用 `stp.safety_snapshot` 或 `stp.status`。
2. 确认 channel status 是可操作状态。
3. 确认 `commit_height` 没有回退。
4. 确认 local commitment tx 和 remote commitment tx 都存在。
5. 确认 local commitment tx 输入等于 channel point。
6. 确认承诺交易输出余额与通道资产余额一致。
7. 确认 CSV delay 在用户可接受范围内。
8. 确认所有已撤销 remote commitment 都有 punish coverage。
9. 确认 channel state 已持久化备份。
10. 对 unlock/lock，确认目标资产对应的 L2 UTXO 已经可花费，而不是仍在 pending。
11. 如果任何检查失败，不执行新的价值移动。

如果 `punish_status` 无法给出可验证结论，Agent 不能把它解释成“没有风险”。正确状态是 `PUNISH_COVERAGE_UNKNOWN`：当前钱包或 STP adapter 不能证明已撤销状态都有惩罚覆盖。此时应停止普通 splicing、unlock、lock、close 等价值移动操作，等待钱包重新导出可验证的 punish coverage。

如果 `punish_status` 返回空列表，并且 adapter 明确表示当前没有 revoked remote commitment，Agent 可以把该状态记录为 `NO_REVOKED_REMOTE_STATE`。这通常发生在通道刚恢复或当前还没有可惩罚旧状态时。该状态不是错误；但下一次 unlock、lock、splicing 或 close 推进 commit height 后，Agent 必须再次检查，确认新撤销的旧 remote commitment 已生成 punish coverage。

如果 `punish_status` 返回一组 revoked commitment，且每一项都满足 `verified=true`、`broadcastable=true`，Agent 可以把该状态记录为 `COVERED`。这才是普通运行中最强的安全证据：它证明用户不只是持有最新承诺交易，也持有对方旧状态作弊时可广播的惩罚交易。

每次价值移动完成后，Agent 应再次执行：

1. 确认 `commit_height` 增加。
2. 确认新 local commitment tx 可用。
3. 确认旧 remote commitment 的 punish tx 已保存或可构造。
4. 确认旧状态撤销材料只在新状态完整后释放。
5. 记录新的安全快照 hash。

## Agent 应该掌握的操作

### `stp.safety_snapshot`

读取单个通道的安全摘要。该操作不移动资产，不需要用户签名，但应限制在本地钱包授权范围内。

返回内容应包括：

```json
{
  "op": "stp.safety_snapshot",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "status": "READY_SAFE",
  "commit_height": 12,
  "chan_point": "txid:0",
  "csv_delay": 2,
  "local_commitment_txid": "...",
  "remote_commitment_txid": "...",
  "local_balance": [],
  "remote_balance": [],
  "punish_coverage": {
    "covered_revoked_commitments": 12,
    "missing": []
  },
  "state_backup": {
    "present": true,
    "last_updated": 1780000000000
  }
}
```

### `stp.commitment_export`

导出当前承诺交易和必要的只读校验材料，用于 Agent 审核或离线备份。该操作不能导出助记词、私钥或未授权的 revocation secret。

返回内容应包括：

- local commitment tx hex/json
- remote commitment tx hex/json
- channel point
- commit height
- CSV delay
- local/remote balance
- commitment txid
- Merkle roots

### `stp.punish_status`

列出本地已保存的 punish coverage：

```json
{
  "op": "stp.punish_status",
  "channel_id": "tb1q...",
  "revoked_commitments": [
    {
      "commit_txid": "...",
      "punish_txids": ["..."],
      "broadcastable": true,
      "verified": true
    }
  ]
}
```

### `stp.punish_build`

在发现某个 remote commitment 上链时，构造并验证惩罚交易。该操作应只返回已签名 punish tx 或待广播摘要，不暴露 revocation secret。

输入：

```json
{
  "op": "stp.punish_build",
  "chain": "testnet",
  "channel_id": "tb1q...",
  "commit_txid": "...",
  "broadcast": false
}
```

### `stp.punish_broadcast`

广播已经验证的惩罚交易。该操作是价值保护动作，不是普通支付动作；当旧承诺交易已上链且 punish coverage 完整时，Agent 应优先执行。

### `stp.force_close_plan`

当 peer 离线或拒绝协作时，生成强制关闭计划：

- 可广播的 local commitment tx
- 预计 CSV delay
- sweep earliest height/time
- sweep tx 构造条件
- 风险提示

### `stp.sweep_build`

在 CSV 到期后构造 sweep tx，把强制关闭输出清扫到用户地址。

## 对 STP 模块的接口要求

为了让 AI Agent 真正有能力证明资产安全，STP adapter / PWA 钱包应提供以下授权能力。它们可以由 HTTP、CLI、SDK 或 PWA bridge 暴露，协议不限定具体传输方式。

| 能力 | 目的 | 当前能力判断 |
| --- | --- | --- |
| `stp.status` | 返回通道、承诺交易摘要、余额、CSV、Merkle root | 已有，可作为基础 |
| `stp.safety_snapshot` | 返回 Agent 友好的安全摘要 | 需要标准化 |
| `stp.commitment_export` | 导出当前承诺交易和 txid | 需要标准化 |
| `stp.punish_status` | 枚举本地 punish coverage | 已具备基础能力 |
| `stp.punish_build` | 根据 commit txid 构造并验证 punish tx | 已具备基础能力 |
| `stp.punish_broadcast` | 广播 punish tx | 已具备基础能力 |
| `stp.force_close_plan` | 生成强制关闭和 sweep 计划 | 已具备基础能力 |
| `stp.sweep_build` | CSV 到期后构造并验证 sweep tx，可选广播 | 已具备基础能力 |
| `stp.backup_export` | 导出不含私钥的通道安全备份 | 需要新增 |

`sweep_build` 需要特别谨慎：Agent 默认应使用 `broadcast:false` 做 dry-run，只要求 adapter 完成 `build -> sign -> verify` 并返回 tx hex、txid、commit txid、fee 和 `broadcastable`。只有钱包侧完成授权且请求明确设置 `broadcast:true` 时，才进入 broadcast 阶段。

## 测试网惩罚能力演练

为了让 AI Agent 在测试环境中真正验证“自己有能力惩罚旧承诺交易”，STP core node 可以在测试网开放故障注入接口。该接口只用于安全演练，不属于主网协议面。

演练目标是模拟 core node 广播一个已经被撤销的 server 端旧承诺交易，然后让 client wallet / Agent 检测、构造并广播惩罚交易。

### 测试网隔离要求

测试网故障注入接口必须满足以下条件：

1. 接口只允许在测试网运行；运行时必须检查当前 chain/network，不是测试网必须直接返回错误。
2. 主网配置、主网数据库和主网 RPC 入口不得允许执行这些接口。
3. 接口必须要求 `confirm_unsafe_test_only=true`，避免被普通客户端误触发。
4. wasm / PWA 钱包构建不得包含 server 端故障注入逻辑。
5. 文档、skill 和 UI 必须明确标注这些接口是测试网安全演练工具，不是主网协议能力。

这些测试网能力必须由 adapter 在运行时检查网络，并在主网上直接拒绝。

### `stp.test_retain_server_commitment`

client 要求 core node 保留当前 server-local commitment 快照。该操作不广播交易，只保存演练材料。

输入：

```json
{
  "op": "stp.test_retain_server_commitment",
  "chain": "testnet",
  "server": "https://apiprd.ordx.market/stp/testnet",
  "channel_id": "tb1q...",
  "commit_height": 0,
  "label": "agent-punish-drill-001",
  "confirm_unsafe_test_only": true
}
```

约束：

- `commit_height` 必须等于 server 当前通道高度；高度 `0` 是合法起点。
- server 只保存自己的 local commitment，因为这正是 client 视角下的 remote commitment。
- 如果通道不存在、承诺交易不存在、链不是 testnet、构建未启用测试 tag，必须失败。

### `stp.test_broadcast_retained_server_commitment`

在通道高度已经前进后，client 要求 core node 广播之前保留的旧 server commitment。

输入：

```json
{
  "op": "stp.test_broadcast_retained_server_commitment",
  "chain": "testnet",
  "server": "https://apiprd.ordx.market/stp/testnet",
  "channel_id": "tb1q...",
  "commit_height": 0,
  "fee_rate": 1,
  "confirm_unsafe_test_only": true
}
```

约束：

- 必须先调用 `stp.test_retain_server_commitment`。
- 当前 server commit height 必须大于保留高度。
- 当前通道必须仍是 ready 状态。
- 该接口广播的是已撤销旧状态，预期 client/watchtower 应立即进入 `PUNISH_REQUIRED`。

### Agent 演练流程

1. Agent 调用 `stp.safety_snapshot`，确认当前通道处于 `READY_SAFE`。
2. Agent 调用 `stp.test_retain_server_commitment`，让 core node 保留当前 server commitment。
3. Agent 发起一次普通通道状态变化，例如小额 `lock`、`unlock` 或测试 splicing，使 commit height 前进。
4. Agent 再次调用 `stp.safety_snapshot`，确认新承诺交易可用，并确认旧 remote commitment 有 punish coverage。
5. Agent 调用 `stp.test_broadcast_retained_server_commitment`，触发 core node 广播旧 server commitment。
6. Agent 监控 BTC L1，发现旧 remote commitment 上链。
7. Agent 调用 `stp.punish_build` 验证惩罚交易，再调用 `stp.punish_broadcast` 广播。
8. Agent 轮询惩罚交易确认，并向用户报告“已验证旧状态惩罚能力”。

如果第 4 步无法证明 punish coverage，Agent 不应进入第 5 步；这说明钱包还没有足够能力保护用户资产。

## Agent 的安全信心标准

Agent 可以向用户报告“资产仍在自己控制之下”的最低条件是：

1. 钱包私钥在用户钱包或 PWA 授权边界内。
2. channel point 存在并能被独立查询。
3. 本地持有最新 local commitment tx。
4. local commitment tx 能花费 channel point，并把用户余额返回到受用户控制的脚本路径。
5. commit height 没有回退。
6. 所有旧 remote commitment 都有可验证 punish coverage，或 watchtower 已保存等价惩罚材料。
7. 强制关闭路径和 CSV 后 sweep 路径可构造。
8. 本地通道状态已持久化备份。

如果以上任一条件不成立，Agent 必须降低信心级别，并停止执行新的价值移动。

## 面向用户的解释

Agent 最终应能用简单语言告诉用户：

“你的资产不是托管在 core node。它们锁在你和 core node 共同控制的 BTC 通道地址里。你的钱包持有最新承诺交易；如果 core node 离线，你可以单方面关闭通道；如果 core node 试图用旧状态作弊，钱包或 watchtower 可以用惩罚交易把旧状态中的资产追回。因此，只要承诺交易、惩罚材料和本地备份完整，你的资产仍在你自己的控制之下。”
