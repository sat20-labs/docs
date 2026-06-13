# STP 第三方客户端实现验收清单

> 本文面向准备自行实现 STP 客户端的钱包团队、SDK 团队和 AI Agent 适配器。它不是某个代码库的实现说明，而是一份协议互操作验收清单：只要客户端满足这些能力，就可以用任意开发语言接入兼容的 STP Server / core node。

## 最小可用客户端

一个最小可用 STP 客户端必须具备以下能力：

| 能力 | 验收标准 |
| --- | --- |
| 钱包密钥 | 能生成或导入用户密钥，并用用户密钥签名 STP 消息和交易 |
| 服务发现 | 能获得 core node 的网络、服务地址、公钥、节点 ID 和能力列表 |
| 消息认证 | 能对 STP 请求和响应做确定性序列化、签名、验签和链 ID 校验 |
| L1 查询 | 能查询 BTC L1 UTXO、资产、交易可见性、确认数和原始交易 |
| L2 查询 | 能查询 SatoshiNet UTXO、资产、交易可见性、通道地址状态和 ascend / descend 记录 |
| 交易引擎 | 能构造、校验、签名和广播 BTC L1 交易、SatoshiNet 交易、承诺交易、惩罚交易和清扫交易 |
| 状态存储 | 能持久保存通道、承诺高度、最新承诺交易、已撤销状态惩罚材料和未完成事务 |
| 恢复流程 | 重启后能恢复 pending 事务，不因本地进程退出而丢失通道控制能力 |
| 安全接口 | 能向上层 Agent 返回安全快照、承诺交易、惩罚覆盖和强制关闭计划 |

如果客户端只能发起 open / unlock / lock，但不能导出安全快照、不能证明惩罚覆盖、不能恢复 pending 事务，则它不能被视为完整 STP 客户端。

## 必须持久化的数据

STP 客户端不能只保存钱包余额。每个通道至少要持久保存：

| 数据 | 用途 |
| --- | --- |
| channel id / channel address | 识别通道和 2-of-2 控制地址 |
| client pubkey / server pubkey | 校验消息身份、重建通道脚本 |
| channel point | 当前 BTC L1 通道 outpoint，承诺交易必须花费它 |
| funding / splicing UTXO 集合 | 判断哪些 L1 资产已由通道管理 |
| commit height | 判断状态是否单调推进，拒绝回退 |
| local commitment tx | peer 离线时本方可广播的最新退出交易 |
| remote commitment tx | 监控 peer 广播的承诺交易是否为旧状态 |
| local / remote balance | 当前承诺状态下双方资产归属 |
| CSV delay | 强制关闭后清扫本方输出的等待窗口 |
| revoked remote commitment 索引 | 识别 peer 旧状态作弊 |
| punish tx 或可构造材料 | 对旧 remote commitment 执行惩罚 |
| pending reservation | 结果未知或未确认事务的恢复入口 |
| 关联 L1 / L2 txid | 重启后继续轮询交易可见性和确认 |

持久化顺序也很重要。客户端在释放旧状态撤销材料前，必须已经保存新承诺状态、最新 local commitment、remote commitment 和对应的安全材料。否则进程崩溃会破坏用户的链上退出能力。

## 必须暴露给 Agent 的安全能力

AI Agent 不应该通过猜测判断通道安全。客户端或 PWA adapter 应提供以下只读或受控接口：

| 接口 | 最低返回内容 |
| --- | --- |
| `stp.status` | 钱包网络、core node 状态、通道列表、channel status、commit height |
| `stp.safety_snapshot` | channel point、commit height、承诺交易是否存在、余额、CSV、Merkle roots、punish coverage、`l2_spendable_balance`、`l2_pending_balance` |
| `stp.commitment_export` | 当前 local / remote commitment 的 txid、hex 或结构化交易、余额和校验材料 |
| `stp.punish_status` | 已撤销 remote commitment 的 punish tx 列表、是否 verified、是否 broadcastable |
| `stp.punish_build` | 给定旧 commitment txid，构造并验证惩罚交易，不暴露 revocation secret |
| `stp.punish_broadcast` | 广播已验证惩罚交易 |
| `stp.force_close_plan` | 当前可广播 local commitment、CSV delay、后续 sweep 条件 |
| `stp.sweep_build` | CSV 到期后构造、签名、验证 sweep tx；`broadcast:false` dry-run，`broadcast:true` 授权后广播 |

Agent 只有在 `stp.safety_snapshot` 返回 `READY_SAFE`，且 punish coverage 为 `NO_REVOKED_REMOTE_STATE` 或 `COVERED` 时，才应发起普通价值移动。`PUNISH_COVERAGE_UNKNOWN` 和 `PUNISH_COVERAGE_MISSING` 都必须阻止 splicing、unlock、lock 和 close。

`READY_DEGRADED` 只能用于只读跟踪。它可能表示承诺交易已经存在，但 L1 funding 尚未确认、peer 状态尚未收敛或 adapter 仍在恢复。第三方客户端不得把 `READY_DEGRADED` 当作 unlock、lock、splicing、close 或 punish drill 的许可。

## 价值移动前置检查

每次 open 之后的价值移动前，客户端必须完成以下检查：

1. 网络一致：钱包、core node、BTC L1 indexer、SatoshiNet indexer 都在同一网络。
2. 通道可用：channel status 为 ready，并且没有 pending reservation。
3. 承诺高度：本地 commit height 没有回退；如可查询 peer 状态，应确认双方高度一致或差异可解释。
4. 承诺交易：local commitment 和 remote commitment 都存在，并且输入指向当前 channel point。
5. 余额一致：承诺交易输出、资产根、local / remote balance 与请求后的资产变化一致。
6. 惩罚覆盖：已撤销 remote commitment 均有 verified / broadcastable punish tx，或当前明确没有已撤销 remote commitment。
7. 输入未锁定：adapter 内部选择的输入未被其他 pending 事务占用。
8. L2 可花费性：unlock/lock 的目标资产必须已经位于 `UtxosL2` / `l2_spendable_balance`；仍在 `pendingUtxosL2` / `l2_pending_balance` 的资产只能等待 adapter/indexer 收敛。
9. Fee 输入合法：协议资产 splicing-out 由 adapter 内部选择普通 BTC L1 fee 输入；除白聪 unlock 的内部例外外，不使用通道地址 UTXO 作为发起方 fee。
10. 用户授权：主网操作必须让用户确认资产、金额、目标地址、手续费和操作类型。
11. 事务持久化：在进入广播或最终承诺交换前，pending 事务和相关 txid 已持久化。

## 资产规则

STP 客户端必须按资产协议分别处理 UTXO 和金额：

| 资产 | 规则 |
| --- | --- |
| 白聪 | BTC L1 有 dust 和 fee 约束；SatoshiNet L2 没有 BTC dust 约束 |
| ORDX | 必然绑定聪，必须根据资产数量和 `bindingSat` 计算需要多少聪；Ordinals NFT 不 ascend 到聪网 |
| Runes | L2 不需要绑定聪，可以由 `Value=0` 的 SatoshiNet UTXO 携带；L1 转移输出仍受 BTC 输出规则约束 |
| BRC20 | L2 不需要绑定聪；L1 splicing-in/out 可能涉及 transfer inscription 和 commit/reveal，transfer UTXO 由 adapter 内部选择或构造 |

如果一个 L1 UTXO 中同时携带多种资产，STP splicing-in 只处理接口参数明确指定的资产。未指定资产不会进入聪网，第三方客户端不应要求它们在 L2 侧出现。

面向 Agent 的 splicing-in 接口不应暴露资产输入选择。当前客户端内部选币会优先避开包含多种可 ascend 资产的 UTXO；如果必须使用这类 UTXO，应在操作预览中提示未指定资产不会 ascend。

客户端不得把 wallet summary 中的余额直接当成可消费 UTXO。特别是 BRC20 和 Runes：余额存在不等于已经有可直接用于当前 STP 操作的 transfer UTXO。BRC20 splicing-in 应区分 adapter 创建 fresh transfer inscription 和直接消费已有 transfer UTXO 两种模式；没有明确支持 direct transfer UTXO 时，不应盲目把 existing transfer UTXO 传入。

## 结果未知恢复

STP 客户端必须把 timeout、连接中断、服务暂不可用等网络异常视为“结果未知”，而不是明确失败。

结果未知时的统一流程：

1. 停止重发同一请求，锁定相关 UTXO。
2. 保存请求 JSON、reservation、txid、channel id、asset、amount 和错误文本。
3. 查询 pending reservation；如果存在，继续轮询原事务。
4. 查询相关 BTC L1 / SatoshiNet txid 是否可见。
5. 查询 core node 的 channel status、commit height、channel point 和 pending 状态。
6. 如果 tx 可见、任一方状态前进或 reservation 存在，继续轮询和恢复原事务。
7. 只有双方仍在同一个旧安全状态、无 pending reservation、相关 tx 都不可见，才允许重新做 adapter preflight 并重试。

这条规则适用于 open、close、splicing-in、splicing-out、unlock 和 lock。广播之后的未知网络结果必须优先按“可能成功”处理；早期协商阶段的未知结果也要先比较双方状态和 tx 可见性，不能直接重试。

如果客户端在状态切换中遇到未知网络结果，并且无法证明新承诺状态已经完成，安全接口必须返回 `PUNISH_COVERAGE_UNKNOWN` 或 `READY_DEGRADED`，而不是让 Agent 继续普通价值移动。

## 通道恢复验收

客户端应支持以下恢复动作：

| 恢复动作 | 适用场景 | 验收标准 |
| --- | --- | --- |
| `stp.restore` | 本地丢失状态，但 peer 或备份仍有最新通道 | 恢复后 safety snapshot 可证明最新承诺和惩罚覆盖 |
| `stp.reopen` | 通道关闭或缺失，但 channel ledger 证明这是已有 client-core channel，通道地址仍有属于 client 的资产或需要补充新的 funding | 不要求质押资产；必要时由用户钱包创建新 L1 funding；funding 确认且 local/core 均 ready 后才能继续价值移动 |
| `stp.rebuild` | L1 channel point 已变化，但资产在 SatoshiNet ledger 中已有 anchor 证据 | 不重复创建 opening anchor，按 ledger 恢复通道 |
| `stp.expand` | L1 资产已在通道地址，但未纳入当前承诺状态 | 资产进入承诺状态，commit height 前进 |
| interrupted splicing-in recovery | L1 funding UTXO 已 ascended，但客户端/peer 没有正确完成 splicing-in | 复用已有 L2 anchor 输出，不重复 anchor |

No-anchor rebuild 必须依赖 SatoshiNet channel ledger。客户端要能判断某个 L1 UTXO 是否已经对应 ascend，或者是否来自 descending v2 返回通道地址的余额输出。无法判断时宁可拒绝自动恢复，也不能重复发行聪网资产。

## 当前主线状态

截至 2026-06-13，本轮测试网主线已完成一次 BRC20 unlock/lock 后的旧 server commitment 惩罚演练。四笔 punish 交易均已在 BTC testnet4 height `139387` 确认。惩罚确认后，旧 channel 数据不可安全复用，恢复策略改为清理 stale channel 并使用普通 `stp.open` 建立 fresh client-core channel。fresh funding `e9c283cc9979bafa4f32f872dc2d0c910b89d810ef6801a1ad55bbeb5e585782` 已确认，通道已进入 `READY_SAFE`，并完成一笔小额 sats `unlock` 推进到 commit height `1`，新的 revoked remote commitment 已有 verified / broadcastable punish coverage。

| 任务 | 状态 | 下一步 |
| --- | --- | --- |
| STP 协议白皮书 | 已形成中文专栏草稿 | 按后续演练结果继续补充真实证据，不同步 `docs-en` |
| 第三方客户端接入指南 | 已覆盖 wallet / channel / safety / recovery 接口 | 后续根据 PWA adapter 实现继续校准接口示例 |
| Agent skill | 已形成 `stp-core-node-client` skill 包 | 继续用真实测试网操作验证并补充 playbook |
| 当前通道恢复 | 本地 stale channel 已清理；fresh open funding `e9c283cc9979bafa4f32f872dc2d0c910b89d810ef6801a1ad55bbeb5e585782` 已确认；fresh channel `READY_SAFE`，commit height `1` | 测试网即将回滚，不再继续链上恢复；遗留资产 expand 作为后续新测试网任务 |
| unlock / lock 复演 | 上一轮 sats、Runes、BRC20 往返均已完成；本轮 fresh channel 已完成小额 sats unlock `b88653f646e192765acaecbf338138c057c4ae420cbfddf7476f3cf5ea7994a8` | 不再追加新 lock，避免回滚前引入新状态；将证据写入文档和视频素材 |
| Runes splicing 复演 | Runes L1 `4ab20f...06ed`、L2 anchor `491936...a1a` 已确认，已作为上一轮素材 | fresh channel expand 后复查 Runes 是否仍需重新纳入通道管理 |
| BRC20 splicing 复演 | BRC20 unlock `2e5e...d862`、lock `63fd...c289` 已完成；随后用于旧 commitment punish 演练 | fresh channel ready 后检查通道地址和 L2 ledger，再决定 expand 或重新 splicing-in |
| 旧 commitment / punish 演练 | 四笔 punish tx 均已确认，height `139387`，查询时 `17` confirmations | 将该完整链上证据纳入白皮书、skill 和视频素材；新通道 ready 后可再做一轮干净复演 |
| 短视频 | 已有脚本、历史素材、BRC20 punish 完整证据和 fresh open 收口素材 | 进入剪辑素材整理：1 分钟传播版使用已确认 punish 证据，长版补充 BRC20 四笔 punish 包细节 |

## 与 core node 的互操作验收

一个第三方客户端接入 core node 前，至少要在测试网完成：

| 测试 | 通过条件 |
| --- | --- |
| open | 普通 client 连接 core node 成功打开通道，不要求质押资产 |
| safety snapshot | open 后能读取 local / remote commitment、channel point、commit height 和 CSV |
| sats unlock / lock | commit height 单调增加，余额变化正确 |
| Runes splicing-in / unlock / lock | Runes 能进入通道，并能在 L2 个人地址和通道之间往返 |
| BRC20 splicing-in / unlock / lock | BRC20 能进入通道，并能在 L2 个人地址和通道之间往返 |
| splicing-out | 至少一种协议资产能退出到 BTC L1；fee 不足时 adapter 能返回明确错误，并引导用户补充普通 BTC fee 资金 |
| 结果未知恢复 | 在广播或 peer ack 返回未知网络结果时不重复消费 UTXO，轮询或恢复流程能收敛 |
| punish coverage | 每次状态推进后能证明旧 remote commitment 有惩罚覆盖 |
| force close plan | peer 离线时能给出可广播 local commitment 和 CSV 后 sweep 条件 |
| restart recovery | 客户端重启后 pending reservation、承诺交易和安全快照仍可恢复 |

完成以上测试后，客户端才能被视为具备基础互操作能力。正式主网发布前，还必须增加长时间运行、reorg、索引器延迟、peer 离线、重复请求、数据库恢复和 wallet 授权取消等测试。

## 主网发布门槛

主网客户端至少要满足：

1. 私钥和助记词永远在钱包安全边界内，不由 Agent 保存。
2. 主网价值移动需要用户逐项确认。
3. 每个通道状态更新前后都能生成安全快照。
4. 数据库崩溃或进程退出后，最新承诺交易和 pending 事务不丢失。
5. `PUNISH_COVERAGE_UNKNOWN`、`PUNISH_COVERAGE_MISSING`、commit height 回退、余额不一致、签名无效都会阻止新的价值移动。
6. 所有测试网故障注入接口都不会进入主网构建。
7. Agent 可以解释资产当前位置、可退出路径、惩罚覆盖和剩余风险。

STP 的主网用户体验可以很简单，但客户端内部不能简化安全模型。用户可以不理解 RSMC、承诺交易和惩罚交易；Agent 和钱包必须理解，并且能持续证明这些安全条件成立。
