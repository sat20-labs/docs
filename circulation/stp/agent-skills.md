# STP Agent 互操作技能规范

> 本文面向需要自动操作 STP 的 AI Agent。目标是让 Agent 能够安全地理解、查询和执行资产在 BTC L1 与聪网之间的迁移。本文不是运行时代码，也不是某个 Agent 本地安装的 `SKILL.md`，而是 STP 专栏中的协议操作规范草案。

## 技能目标

Agent 应掌握以下能力：

1. 判断资产当前位于 BTC L1、聪网个人地址还是 STP 通道。
2. 判断是否已有可用通道，以及通道是否 ready。
3. 根据用户目标选择 open、splicing-in、unlock、lock、lock-with-expand、splicing-out 或 close。
4. 发起操作后围绕 `txId` 和 `resvId` 追踪状态。
5. 遇到未确认、peer offline、UTXO locked、channel busy、insufficient fee 等情况时安全停止或重试。

## 优先接口

Agent 优先使用经过封装的 STP 客户端接口，避免直接拼装节点间底层协商消息。

原因：

- 高层客户端接口应自动选择 UTXO、构造交易、签名、保存事务、广播交易和发送 peer 消息。
- 底层协商消息需要手工构造签名、commitment、revocation 和中间消息，出错风险高。
- 只有在实现 STP 客户端库或调试协议兼容性时，才应直接处理底层消息。

## 前置检查

每次执行资产操作前，Agent 必须检查：

| 检查项 | 目的 |
| --- | --- |
| 钱包是否存在并已解锁 | 未解锁不能签名 |
| STP 服务是否 ready | L1/L2 同步和通道监控未就绪时不要操作 |
| 当前网络 `chain` / `env` | 防止 mainnet/testnet 混用 |
| L1/L2 indexer 是否可查询 | 资产和确认状态依赖 indexer |
| 服务节点是否在线 | 通道协作需要 peer |
| 是否已有 ready 通道 | 决定 open 还是直接操作 |
| 资产名称和 divisibility | 金额必须按 ticker 精度解析 |
| UTXO 是否已被 reservation 锁定 | 防止重复花费 |
| 操作是否涉及 BRC20/Runes | 这些资产可能需要 inscription 或长时间确认 |

### 价值移动前的安全门

STP 的核心安全性来自承诺交易和惩罚交易，而不是来自 core node 的信用声明。因此，Agent 在任何 open 之后的价值移动操作前，都必须先取得通道安全快照。

最低安全快照应包含：

| 字段 | Agent 判断 |
| --- | --- |
| `channelId` / `chanPoint` | 当前承诺交易输入必须指向最新通道点 |
| `commitHeight` | 必须单调递增，不能回退 |
| `localCommitment` | 用户必须持有可广播的最新本地承诺交易 |
| `remoteCommitment` | 必须能识别对方可能广播的承诺交易 |
| `localBalance` / `remoteBalance` | 余额必须与承诺交易输出和资产根一致 |
| `csvDelay` | 强制关闭后的清扫窗口必须可被用户接受 |
| `punishCoverage` | 已撤销的对方旧承诺必须有可构造或可广播的惩罚交易 |
| `stateBackup` | 最新通道状态和未完成事务必须已持久化 |

如果无法取得这些信息，Agent 应把通道标记为 `READY_DEGRADED`，停止 splicing、unlock、lock、close 等价值移动操作，并向用户报告 `SAFETY_SNAPSHOT_REQUIRED` 或 `PUNISH_COVERAGE_MISSING`。只有当钱包或 STP adapter 能重新证明最新承诺交易和惩罚覆盖后，才允许继续操作。

`punishCoverage` 应至少区分以下状态：

| 状态 | 含义 | Agent 行为 |
| --- | --- | --- |
| `NO_REVOKED_REMOTE_STATE` | 当前没有已撤销的对方旧承诺需要惩罚覆盖 | 可继续，但后续每次状态推进后必须再次检查 |
| `COVERED` | 已撤销 remote commitment 均有 verified / broadcastable punish tx | 可继续普通价值移动 |
| `PUNISH_COVERAGE_UNKNOWN` | adapter 无法给出可验证的惩罚覆盖结论 | 停止价值移动 |
| `PUNISH_COVERAGE_MISSING` | 已发现 revoked commitment，但缺少可验证惩罚交易 | 停止价值移动并进入安全恢复 |

Agent 不能只因为通道是 `READY` 就执行操作。`READY_SAFE` 的最低标准是：承诺交易存在、commit height 单调、余额一致，并且 punish coverage 处于 `NO_REVOKED_REMOTE_STATE` 或 `COVERED`。

`READY_SAFE` 也不等于所有资产 UTXO 都已经可花费。刚 splicing-in 或 expand 的资产，可能已经出现在承诺资产集合中，但对应 SatoshiNet anchor 输出仍在 `pendingUtxosL2`。Agent 在 unlock/lock 前必须确认目标资产已经进入可花费 `UtxosL2`，或 adapter 的 `l2_spendable_balance` 已覆盖该资产；如果它仍在 `l2_pending_balance`，只能轮询等待，不能重试 unlock。

## 核心决策树

### 目标：把 BTC L1 资产带入聪网

1. 如果没有通道：
   - 发起 open 创建白聪通道。
   - 等待通道进入 ready 状态。
2. 如果资产已经在通道地址但未纳入管理：
   - 发起 expand 类 STP 纳管动作。
3. 如果资产在用户 L1 地址：
   - 发起 splicing-in。
4. 完成后查询事务状态和聪网资产摘要。

### 目标：恢复已经关闭但仍有资产的通道

1. 查询通道地址的 BTC L1 UTXO、SatoshiNet L2 资产和 channel ledger。
2. 如果 ledger 证明该通道地址曾经打开过，优先发起 `stp.reopen`，恢复同一个 client-core channel。
3. 如果通道地址上没有满足最小容量要求的白聪 UTXO，让 reopen 路径由用户钱包提供新的 L1 funding 输出。
4. funding 交易可见但未确认时，不重复 reopen，不执行 unlock / lock / splicing，只轮询 funding、reservation、local/core channel status。
5. 等待 funding 确认且双方进入 ready 后，立即运行 `stp.safety_snapshot`，再继续后续资产流转或 punish drill。

### 目标：在聪网自由使用通道资产

1. 查询通道是否 ready。
2. 查询通道中该资产余额是否足够，并确认目标资产已经在可花费 `UtxosL2` / `l2_spendable_balance` 中。
3. 发起 unlock。
4. 等待 unlock 事务确认。
5. 查询聪网个人地址资产余额。

### 目标：把聪网个人资产重新纳入通道保护

1. 查询通道是否 ready。
2. 查询聪网个人地址是否有足够资产余额；具体资产输入和手续费输入由 adapter 内部选择。
3. 如果通道容量足够：
   - 发起 lock。
4. 如果通道容量不足：
   - 发起 lock-with-expand。
   - 该路径通过穿越合约和 expand 将聪网个人资产重新纳入用户通道控制。
5. 等待 lock 或 lock-with-expand 相关 reservation 确认。

### 目标：把聪网资产退回 BTC L1

1. 如果资产仍在通道中：
   - 发起 splicing-out，目标地址必须是有效 BTC 地址。
2. 如果资产在聪网个人地址，应先通过 lock 或 lock-with-expand 重新纳入通道，再按通道退出路径处理。
3. 如果要永久退出通道：
   - 优先发起协商关闭。
   - peer 不在线或异常时才使用强制关闭。
4. 追踪聪网侧退出状态和 BTC L1 splicing-out/close 交易确认。

补充规则：

- Runes / BRC20 等协议资产 splicing-out 通常需要 BTC L1 fee。Agent 不选择 fee 输入；adapter 必须在内部选择合适的纯白聪输入，不能把带资产的 UTXO 当作普通 fee 输入。
- 如果 adapter 返回 fee 不足，Agent 应提示用户补充普通 BTC fee 资金，待确认后再重试；不要手工指定 fee 输入。
- BRC20 splicing-in / splicing-out 所需的 transfer 输出由 adapter 内部选择；没有合适 transfer 输出时，adapter 应自动铸造合适的 transfer inscription。
- BRC20 全量 splicing-out 后，如果安全快照显示该 BRC20 通道余额已为 `0`，Agent 可以继续；若余额非 `0` 且资产 UTXO 已不可验证，必须视为资产一致性风险并停止。
- BRC20 splicing-in 时，Agent 只提供资产名和金额，不传 transfer 输出；adapter 根据钱包资产状态选择已有 transfer 输出或自动生成新的 transfer inscription。
- 一个 L1 UTXO 可能同时携带多种资产。当前 STP splicing-in 只 ascend 请求参数明确指定的资产；同一 UTXO 中未指定的 ORDX、Runes、BRC20 transfer 或 Ordinals NFT 都不进入聪网。Agent 不应把这些未指定资产纳入 L2 余额守恒预期。
- Agent 不应要求用户指定 splicing-in 的资产输入。adapter 内部选币应默认避开多资产 UTXO；如果必须使用，应在预览里说明哪些资产会 ascend、哪些资产会被忽略。

### 协议资产 splicing-out 剧本

Runes、BRC20、ORDX 等协议资产从通道退出到 BTC L1 时，Agent 应按以下顺序执行：

1. 运行 `stp.safety_snapshot`，确认通道是 `READY_SAFE`。
2. 查询本地和 core node 的 `commitHeight`、`chanPoint`、资产余额，确认双方一致。
3. 发起协议资产 `stp.splicing_out`，只传资产、金额和目标 BTC 地址；资产输入、transfer inscription 和 fee 输入都由 adapter 内部处理。
4. 如果 adapter 返回 fee 不足或资产输入不可构造，停止并按错误提示补充资金或等待资产状态收敛，不手工传入 UTXO。
5. 记录 reservation、L2 deAnchor tx、L1 splicing-out tx，以及可能的 commit/reveal 前置 tx。
6. 先确认聪网 deAnchor 是否完成，再异步轮询 BTC L1 splicing-out tx 确认。
7. 操作完成后再次运行 `stp.safety_snapshot`，确认 commit height 前进、承诺交易更新、旧 remote commitment 已有 punish coverage。

如果第 3 步返回 timeout、连接中断或未知网络结果，Agent 不得立即重发。应进入“未知网络结果后判断是否可重试”工作流，先比较双方通道状态、reservation 和 L1/L2 tx 可见性。

## 客户端操作参考

以下是 Agent 应使用的高层 STP 客户端操作。具体可以由本地服务、SDK、命令行工具或独立客户端库提供，协议不限定开发语言和传输方式。

| 操作 | 请求结构 | 返回重点 | 说明 |
| --- | --- | --- | --- |
| 创建钱包 | 钱包创建请求 | 钱包 ID、助记词、地址 | 创建后应进入可初始化状态 |
| 导入钱包 | 钱包导入请求 | 钱包 ID、地址 | 导入后应进入可初始化状态 |
| 解锁钱包 | 钱包解锁请求 | 钱包 ID、地址 | 解锁后才能签名 |
| 打开通道 | 通道打开请求 | 通道 ID | 初始容量通常为白聪 |
| 关闭通道 | 通道关闭请求 | 关闭交易 ID、退出交易 ID | 可协商关闭或强制关闭 |
| Unlock | 通道释放请求 | 交易 ID、事务 ID | 通道到聪网个人地址 |
| Lock | 通道回锁请求 | 交易 ID、事务 ID | 聪网个人地址到通道 |
| Lock With Expand | 回锁扩容请求 | 交易 ID、事务 ID | 通道容量不足时恢复资产通道控制权 |
| Splicing-In | 通道扩入请求 | 交易 ID、事务 ID | L1 资产进入通道 |
| Splicing-Out | 通道扩出请求 | 交易 ID、事务 ID | 通道资产退出到 L1 |
| Expand | 通道纳管请求 | anchor 交易 ID、金额 | 已在通道地址的资产纳入管理 |
| Expand All | 批量纳管请求 | anchor 交易 ID 列表、金额 | 批量纳入资产 |
| Deploy Runes | Runes 部署请求 | 交易 ID、事务 ID、动作结果 | 远端长耗时动作 |
| 查询通道 | 通道状态查询 | channel detail | 只读查询接口 |
| 查询 reservation | reservation 状态查询 | status/result | 只读查询接口 |

## 请求字段规范

### 通道打开请求

| 字段 | 含义 |
| --- | --- |
| `feeRate` | BTC L1 fee rate，sat/vB；为 0 时使用服务估算值 |
| `amt` | 初始通道金额，单位聪 |
| `memo` | 可选备注 |

### 通道扩入请求

| 字段 | 含义 |
| --- | --- |
| `channel` | 通道 ID |
| `assetName` | 资产名，如白聪、ORDX、Runes、BRC20 表达 |
| `amt` | 字符串金额，必须符合资产 divisibility |
| `feeRate` | BTC L1 fee rate |
| `reason` | 操作原因，用于上层流程关联 |

Agent-facing adapter 不应暴露底层资产输入或手续费输入参数。资产输入、BRC20 transfer inscription 和手续费输入都由 adapter 内部选择或构造。

### 通道扩出请求

| 字段 | 含义 |
| --- | --- |
| `channel` | 通道 ID |
| `address` | BTC L1 目标地址 |
| `assetName` | 资产名 |
| `amt` | 字符串金额 |
| `feeRate` | BTC L1 fee rate |
| `reason` | 操作原因 |
| `more` | 额外数据，用于上层流程关联 |

通道扩出前置检查：

1. 查询通道状态，必须为 ready。
2. 查询本地和 core node 的 `commitHeight`、`chanPoint`，必须一致。
3. Agent 不传 fee 输入。adapter 内部选择纯白聪 fee 输入；如果不足，返回明确错误和补充资金建议。
4. 若资产是 BRC20，transfer 输出选择或铸造由 adapter 内部完成。

### 通道释放请求

| 字段 | 含义 |
| --- | --- |
| `channel` | 通道 ID |
| `assetName` | 资产名 |
| `amt` | 字符串金额 |
| `address` | 聪网目标地址，空值时默认当前钱包地址 |

Agent-facing adapter 不应暴露 unlock 输入或 fee 输入参数。adapter 应在通道内自动选择可用输入，并处理聪网手续费。

### 通道回锁请求

| 字段 | 含义 |
| --- | --- |
| `channel` | 通道 ID |
| `assetName` | 资产名 |
| `amt` | 字符串金额 |

Agent-facing adapter 不应暴露 lock 输入或 fee 输入参数。adapter 应在用户聪网地址上自动选择资产输入和手续费输入；容量不足时返回 `INSUFFICIENT_CHANNEL_CAPACITY` 并建议 `lock-with-expand`。

## 状态追踪

Agent 不应只看发起接口是否返回成功，而应持续查询 reservation 和链上状态。

推荐规则：

1. 返回 `resvId` 时，以 `resvId` 为主跟踪。
2. 返回 `txId` 但没有 `resvId` 时，以链上确认和 wallet action status 为主跟踪。
3. `RS_CONFIRMED` 表示协议动作达到确认状态。
4. `RS_CLOSED` 表示 reservation 生命周期关闭，不一定表示通道关闭。
5. `RS_FAILED` 或 `RS_REMOTE_FAILED` 必须停止自动推进，并把错误暴露给用户。
6. `CS_READY` 是大多数通道动作的前置状态。
7. `CS_CLOSE_FORCELY_*` 期间不要再发起新的普通通道动作。

聪网 UTXO 规则：

1. 聪网 L2 UTXO 没有 BTC dust 限制，可以为 0。
2. BRC20 和 Runes 在 L2 不需要绑定聪，因此一个聪网 UTXO 可以携带 BRC20 或 Runes 资产，同时聪数量为 0。
3. 在 BTC L1 上，携带 BRC20/Runes 转移资产的 UTXO 仍然受 L1 输出限制，当前通常使用最小的 330 sats。
4. ORDX 必然绑定聪；Agent 必须根据资产数量和 `bindingSat` 参数计算需要多少聪，不能套用 BRC20/Runes 的 0-sat UTXO 规则。
5. 对白聪 unlock，Agent 只指定释放金额；adapter 必须在通道内选择足以覆盖 `unlock amount + SatoshiNet fee` 的输入。
6. 对白聪 lock，`amount` 是回锁进通道的净金额；钱包输入还需要额外覆盖 SatoshiNet fee。
7. Agent 不应因为聪网找零小于 330 sats 就判断交易非法；应以聪网交易验证和资产守恒为准。

## 安全护栏

Agent 必须遵守以下限制：

1. 不自动执行 mainnet 高价值转移，除非用户明确确认资产、金额、地址、fee rate 和操作类型。
2. 不在 `channel is busy` 时并发发起同一通道的新动作。
3. 不复用已有未完成 reservation 的 UTXO。
4. 不在 peer offline 时启动需要协作签名的普通动作；强制关闭除外。
5. 不手写底层协商消息，除非具备完整签名、commitment、revocation 构造能力。
6. BRC20 操作必须提示可能产生 commit/reveal 前置交易，且耗时更长。
7. Runes deploy 需要等待 commit tx 超过确认阈值后再 reveal，不能按普通单交易处理。
8. 所有目标地址必须按网络校验，避免 testnet/mainnet 混用。

## 典型 Agent 工作流

### 工作流 A：首次进入聪网

1. 查询钱包是否解锁。
2. 查询节点和 indexer 是否 ready。
3. 查询是否已有 ready 通道。
4. 没有通道时调用 open channel。
5. 轮询通道状态直到 `CS_READY`。
6. 对目标资产调用 splicing-in。
7. 轮询 reservation 到确认。
8. 如果用户要在聪网自由使用资产，调用 unlock。
9. 输出最终 L1 tx、L2 tx、通道 ID、reservation ID 和资产位置。

### 工作流 B：从聪网退回 BTC L1

1. 确认目标 BTC 地址网络正确。
2. 判断资产在通道中还是聪网个人地址。
3. 在通道中：调用 splicing-out。
4. 在个人地址：先调用 lock；容量不足时调用 lock-with-expand，然后再 splicing-out。
5. 如果 adapter 报告协议资产 splicing-out 的 BTC L1 fee 资金不足，提示用户补充普通 BTC fee 资金或等待资金确认，不让 Agent 手工指定 fee 输入。
6. 轮询聪网退出状态。
7. 轮询 L1 tx 确认。
8. 输出最终 L1 txid 和剩余通道状态。

### 工作流 D：未知网络结果后判断是否可重试

1. 记录失败操作、请求摘要、错误文本、channel id、asset、amount。
2. 查询本地 reservation；若存在 pending reservation，不重试，继续轮询原事务。
3. 查询 core node 端 channel 和 reservation。
4. 查询相关 L1/L2 tx 是否可见。
5. 若任一方 `commitHeight` 或 `chanPoint` 已变化，或任一 tx 可见，进入跟踪/恢复流程，不重试原操作。
6. 只有在双方仍处于同一 ready 状态、无 pending reservation、无相关 tx 可见时，才允许重新做 preflight，由 adapter 重新选择输入并重试。
7. 对早期协商阶段的未知网络结果，也必须执行上述比较；不能只因为“尚未广播”就直接重试。

### 工作流 C：恢复未完成操作

1. 查询 adapter 返回的 reservation 列表。
2. 找出非 `RS_CLOSED`、非 `RS_CONFIRMED`、非失败状态的 reservation。
3. 按类型分类：open、splicing、payment、remoteaction、localaction。
4. 查询关联 tx 是否已确认。
5. 等待钱包或 STP 服务继续推进；只在 adapter 明确要求时执行恢复动作。
6. 若 peer 已无法识别该 reservation，停止自动操作并提示用户确认链上资产位置。

## Agent 输出格式建议

每次操作完成或暂停时，Agent 应输出：

| 字段 | 说明 |
| --- | --- |
| `intent` | 用户目标 |
| `network` | mainnet/testnet |
| `asset` | 资产名和金额 |
| `from` / `to` | 资产迁移方向 |
| `channelId` | 相关通道 |
| `txIds` | 已广播交易 |
| `resvId` | reservation id |
| `currentStatus` | 当前 channel/reservation 状态 |
| `nextCheck` | 下一步应查询的对象 |
| `risk` | 是否需要用户确认或人工介入 |

## 与 Agent Skill 的关系

未来可以把本文沉淀为真正的 Agent skill。建议拆成三个层次：

1. `stp-inspect`：只读查询钱包、通道、reservation、余额、资产位置。
2. `stp-operate-testnet`：允许 testnet 自动 open、splicing、unlock、lock、lock-with-expand、splicing-out。
3. `stp-operate-mainnet`：mainnet 操作默认只生成计划和风险清单，执行前要求用户逐项确认。

这三个 skill 共享同一套状态模型，但权限和确认策略不同。这样既能让 Agent 真正操作 STP，又能避免在主网上出现不可逆误操作。
