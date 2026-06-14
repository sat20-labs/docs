# STP 测试网演练总结：AI Agent 如何验证用户掌控资产安全

> 本文总结 2026-06-13 前后围绕同一 client 钱包、103 Core Node 和 BTC testnet4 / SatoshiNet testnet 完成的 STP 真实演练。目标不是记录调试过程，而是把真实链上过程沉淀成 AI Agent 可以复用的 STP 安全技能：如何判断资产在谁的控制下，如何验证承诺交易，如何确认惩罚能力，以及何时可以或不可以移动资产。

## 演练目标

本轮演练验证三件事：

1. 普通 client 钱包可以连接 Core Node 打开私人 STP 通道，不需要质押资产。
2. BTC L1 原生资产，包括 sats、Runes、BRC20、ORDX，可以通过 splicing / expand 纳入通道，在聪网个人地址和通道之间 unlock / lock 流动。
3. 当测试网 Core Node 广播已经撤销的 Core Node 侧旧 commitment 时，client wallet 能构造并广播 punish tx，证明用户不需要信任 Core Node 才能保护资产。

## 核心证据

| 类型 | 证据 |
| --- | --- |
| 通道 | `tb1q9kf9jpmh92e8gxp4sk3mrmax28726qurl04j6x70457vzu46fzdqhe9hzu` |
| client 地址 | `tb1pxvm0c5gt6jcjg9el8fnnjuxwsn3yme9e0zkjnp0g4658suvkw0cq4mprqc` |
| Core Node pubkey | `0367f26af23dc40fdad06752c38264fe621b7bbafb1d41ab436b87ded192f1336e` |
| BRC20 anchor spendable | `440828e1b6ef36a3136021b40d9f8940cf0f866f93ee3b1c95a3c9758432d531:0`，聪网 height `3492` |
| BRC20 unlock / lock | `2e5e0fe1f44a8a6e1754558c5a9829a2b78bd6b661c7ba10f215e755888cd862` / `63fd7bf150e2678956fa765b4780c2ff5cf07cd203d0d04e7eb3ae31f7e3c289` |
| retained old Core Node-side commitment | `151226853632d61d177b3279fcf99a7c144beaa3d018abd55f00f5b2adc24909` |
| state advance after retain | `86310825ffa2d7d229d95b175c164ed2e32cefa354459f2060d68fb65ea326d7`，commit height `7 -> 8` |
| punish package | `459877810aa391f4da5ce6a7b0a817daee0dd63f4a24b8d77062dee7ef47fbee`, `23b3e6809eb5277ff9da7fb767ca8dc54e75f034104069f8c8a873b5e7c41451`, `c80dd18b79bbf1600a1a630be953de7e9f698d96c5b6a1d20eecf8f27dbb6859`, `22643d7c0b8f4a6aee93bcafceecc318ca56b9d31196e17b87fda43a9ee845d5` |
| punish confirmation | 四笔 punish tx 均在 BTC testnet4 height `139387` 确认 |
| fresh open close-out | funding `e9c283cc9979bafa4f32f872dc2d0c910b89d810ef6801a1ad55bbeb5e585782`，BTC testnet4 height `139406` 确认 |
| fresh channel safety | final unlock `b88653f646e192765acaecbf338138c057c4ae420cbfddf7476f3cf5ea7994a8` 推进到 commit height `1`，新 punish tx `84524f5aaa367f6ff7bcb15e1d01f8f7fa97fa93779c04cb96bc5ec58afa31a4` 已 verified / broadcastable |

完整 JSON 证据见 `evidence/testnet-punish-evidence-2026-06-13.json`。

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

本轮 BRC20 流程证明：

1. BRC20 已进入 commitment 不等于可以立刻 unlock。
2. 必须等待 L2 anchor 从 `pendingUtxosL2` 进入可花费集合。
3. 进入可花费集合后，BRC20 可以 unlock 到聪网个人地址，再 lock 回通道。

这是 Agent 的一个核心技能：区分“承诺状态安全”和“UTXO 已可花费”。

### 3. Core Node 侧旧 commitment 惩罚

测试网 fault 接口先保留 Core Node-side commitment，再通过一次小额状态更新推动 commit height 前进。此时被保留的 Core Node-side commitment 成为旧状态。

当 Core Node 广播旧 commitment 后，client wallet 使用本地保存的惩罚材料构造 punish package。由于旧 commitment 中包含 BRC20 相关路径，本轮 punish 包不是简单单笔交易，而是包含四笔依赖交易。Agent 的职责不是理解某个Core Node 内部实现，而是验证每一笔 punish tx 是否能把旧 commitment 的资产追回到用户控制路径，并在 BTC L1 上确认。

Agent 规则：

1. 旧 commitment 一旦被 peer 广播，优先进入 punish，不再执行普通通道操作。
2. `stp.punish_build` 必须先证明 punish tx 花费的是已撤销 commitment 的输出。
3. `stp.punish_broadcast` 返回后，Agent 必须逐笔查询所有 punish txid，直到 L1 可见或确认。

### 4. 惩罚后的恢复

惩罚确认后，旧通道不再作为普通运行通道继续使用。Agent 的恢复目标是让用户回到一个新的、可证明安全的通道状态：

1. 确认旧 channel point 已被链上交易消费，旧通道不能再作为普通 value-moving 通道使用。
2. 使用 ordinary `stp.open` fresh open，重新建立 client 和 Core Node 的 2-of-2 通道边界。
3. 等 funding 确认和 `READY_SAFE` 后，用一笔小额 sats unlock 推进 commit height。
4. 确认新的 revoked remote commitment 已有 verified / broadcastable punish coverage。

这说明 Agent 的恢复目标不是“尽量复用旧数据”或“节省某一笔开通成本”，而是“让用户重新回到可证明安全的通道状态”。

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
| punish build / broadcast | 已验证，包含多笔依赖 punish package |
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

## Skill 应输出的用户安全解释

当 Agent 面向普通用户解释 STP 时，应围绕以下事实表达：

1. 资产进入的是用户和 Core Node 的 2-of-2 通道地址，不是托管账户。
2. 每次状态更新都会产生新的承诺状态；用户钱包保存可用于退出的承诺交易。
3. 旧状态被撤销后，钱包保存对应的惩罚能力。
4. Core Node 如果广播旧 commitment，Agent 可以识别它不是最新状态，并用钱包构造 punish tx。
5. punish tx 在 BTC L1 上花费旧 commitment 的输出，把资产追回用户控制路径。
6. 因此 STP 的信任基础不是“Core Node 会诚实”，而是“用户钱包持有承诺交易和惩罚旧状态的能力”。

## 当前收口状态

聪网测试网即将因 contract 模块重构回滚。本轮链上演练已经完成必要闭环：多资产流动、旧 commitment 广播、punish package 广播确认、fresh open 后 `READY_SAFE` close-out。后续不再继续制造新的测试网链上状态，工作重心转为：

1. 整理白皮书和接入文档。
2. 校准 `sat20-agent-wallet` skill 的操作规则和 adapter contract。
3. 完成 PWA adapter 缺口清单。
4. 在新测试网稳定后，再补做需要长期素材的演示或视频录制。

调试细节、临时修复、Core Node 日志排查和环境问题不进入本文主线；它们只应保留在内部验证记录中。Agent 学习 STP 时，应学习上述资产控制和安全验证流程，而不是学习某一次测试网调试过程。
