# STP 测试网演练总结：AI Agent 如何验证用户掌控资产安全

> 本文保留 2026-06-13 前后测试网演练沉淀出的 Agent 安全规则。由于 SatoshiNet 测试网后来发生回滚，旧 L2 交易和旧 evidence 文件不再作为当前可复核证据列出。当前可复核 txid 以 `testnet-validation.md` 和 `evidence/testnet-minimal-punish-evidence-2026-06-18.json` 为准。

## 演练目标

本轮演练验证三件事：

1. 普通 client 钱包可以连接 Core Node 打开私人 STP 通道，不需要质押资产。
2. BTC L1 原生资产，包括 sats、Runes、BRC20、ORDX，可以通过 splicing / expand 纳入通道，在聪网个人地址和通道之间 unlock / lock 流动。
3. 当测试网 Core Node 广播已经撤销的 Core Node 侧旧 commitment 时，client wallet 能构造并广播 punish tx，证明用户不需要信任 Core Node 才能保护资产。

## 演练过程抽象

### 1. 通道与多资产进入

Agent 先通过 `stp.status` 和 `stp.safety_snapshot` 确认通道安全状态，再执行资产纳入动作：

- sats 通过 open / expand 进入通道。
- Runes 通过 splicing-in 或 expand 进入通道。
- BRC20 通过 adapter 生成 transfer inscription，再用 reveal output 完成 splicing-in。
- ORDX 小额资产通过 stub 白聪满足 L1 输出约束；同一 UTXO 中的 Ordinals NFT 按当前协议忽略，不进入聪网。

关键经验：一个 L1 UTXO 可能携带多种资产，但当前 STP 只 ascend 请求明确指定的一种资产。Agent 不能把未指定资产计入 L2 守恒预期。

### 2. L2 unlock / lock

资产进入通道后，Agent 不直接按 commitment balance 操作，而是检查目标资产是否已经进入 `UtxosL2` / `l2_spendable_balance`。

这证明了一个核心技能：区分“承诺状态安全”和“UTXO 已可花费”。BRC20 / Runes 在聪网上可以由 `Value=0` 的 UTXO 携带，Agent 不能套用 BTC L1 dust 规则。

### 3. Core Node 侧旧 commitment 惩罚

测试网 fault 接口先保留 Core Node-side commitment，再通过一次小额状态更新推动 commit height 前进。此时被保留的 Core Node-side commitment 成为旧状态。

当 Core Node 广播旧 commitment 后，client wallet 使用本地保存的惩罚材料构造 punish package。Agent 的职责是验证 punish tx 是否花费已撤销 commitment 的输出，并在 BTC L1 上确认。

Agent 规则：

1. 旧 commitment 一旦被 peer 广播，优先进入 punish，不再执行普通通道操作。
2. `stp.punish_build` 必须先证明 punish tx 花费的是已撤销 commitment 的输出。
3. `stp.punish_broadcast` 返回后，Agent 必须逐笔查询所有 punish txid，直到 L1 可见或确认。

### 4. 惩罚后的恢复

惩罚确认后，旧通道不再作为普通运行通道继续使用。Agent 的恢复目标是让用户回到一个新的、可证明安全的通道状态：

1. 确认旧 channel point 已被链上交易消费，旧通道不能再作为普通 value-moving 通道使用。
2. 使用 ordinary `stp.open` fresh open，重新建立 client 和 Core Node 的 2-of-2 通道边界。
3. 等 funding 确认和 `READY_SAFE` 后，再推进一次小额状态变化。
4. 确认新的 revoked remote commitment 已有 verified / broadcastable punish coverage。

这说明 Agent 的恢复目标不是“尽量复用旧数据”，而是“让用户重新回到可证明安全的通道状态”。

## 已验证的 Agent 技能

| 技能 | 结论 |
| --- | --- |
| 普通 client open | 已验证，连接 Core Node 不需要质押资产 |
| `stp.safety_snapshot` | 已验证，可判断 `READY_SAFE`、commit height、channel point、commitments、punish coverage |
| sats unlock / lock | 已验证 |
| Runes splicing / unlock / lock | 已验证 |
| BRC20 splicing / unlock / lock | 已验证 |
| ORDX 小额 splicing / unlock / lock | 已验证，需遵守 bindingSat 和 Ordinals NFT 忽略规则 |
| 结果未知处理 | 已验证，必须查询 reservation、local/core channel 和 L1/L2 tx 可见性后再决定是否重试 |
| testnet old commitment drill | 已验证，只能测试网使用，主网必须拒绝 |
| punish build / broadcast | 已验证，支持多笔依赖 punish package |
| punish 后恢复 | 已验证，旧通道不能继续普通运行时 fresh open，重新建立可证明安全的控制边界 |

## Agent 必须内化的安全规则

1. `READY` 不等于安全可操作；普通价值移动必须要求 `READY_SAFE`。
2. `READY_SAFE` 不等于某个刚 ascend 的资产已经可花费；unlock/lock 还要检查 `l2_spendable_balance`。
3. `PUNISH_COVERAGE_UNKNOWN` 和 `PUNISH_COVERAGE_MISSING` 都必须阻止普通价值移动。
4. peer 广播旧 commitment 时，Agent 必须优先 punish。
5. timeout、连接中断或服务暂不可用是“结果未知”，不是明确失败。
6. 广播后结果未知时，先查 tx 可见性；不能立即复用 UTXO 重发。
7. 协议资产 splicing-out 需要普通 BTC L1 fee 资金；adapter 内部选择 fee 输入，且不能把通道地址 UTXO 或资产 UTXO 当普通 fee 输入。
8. BRC20 / Runes 在聪网上可以由 `Value=0` 的 UTXO 携带；Agent 不能套用 BTC L1 dust 规则。
9. ORDX 必然绑定聪，应按 `bindingSat` 判断所需 sats。
10. 旧通道不能继续普通运行时，不应为了节省 opening fee 强行 `reopen`；Agent 可以选择 ordinary `open` 重新建立安全边界，再用 `expand` 纳管通道地址中仍属于用户的资产。

## 文档和 skill 的落地要求

后续文档和 skill 的重点是让 Agent 实际证明安全：

1. 接入指南必须要求客户端保存 commitment、revoked state、punish material 和 pending reservation。
2. Agent skill 必须把 `stp.safety_snapshot` 作为价值移动前置门。
3. PWA adapter 必须把私钥、助记词、WASM 和通道数据库留在钱包安全边界内。
4. Agent 操作必须返回 txid、reservation、commit height、safety status、punish coverage 和下一步建议。
5. 真实测试网证据应作为白皮书的一部分，说明 STP 的安全机制不是理论描述，而是可被 Agent 操作和验证的流程。
