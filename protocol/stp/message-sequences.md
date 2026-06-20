# STP 消息流程

本文按操作说明 STP 消息顺序、链上结果、状态推进和 Agent 验证点。它补充 [STP 消息与数据模型](messages-and-data-model.md)，用于第三方客户端实现、测试网演练和 AI Agent 自动化验证。

## 通用流程规则

每个会改变资产归属的 STP 操作都遵守以下规则：

1. 操作前读取 safety snapshot，确认通道处于可操作状态。
2. 客户端内部选择或构造输入，普通 Agent 不直接提供资产 UTXO 或 fee UTXO。
3. 双方先构造新承诺状态，再撤销旧承诺状态。
4. 进入广播或最终 ack 前，客户端必须持久化 pending 事务、相关 txid、承诺交易和撤销材料。
5. commit height 只能单调增加。
6. 广播后的网络异常视为结果未知，必须通过 L1/L2 indexer 和 peer 状态恢复。
7. 操作后重新读取 safety snapshot，确认 punish coverage 和资产事实。

## Open Channel

目标：建立 Client Wallet 与 Core Node 的私人 STP 通道。

| 步骤 | 消息 / 动作 | 验证点 |
| --- | --- | --- |
| 1 | Client Wallet 发现 Core Node | 校验网络、Core Node 公钥、能力列表、CSV、费用 |
| 2 | `ChannelOpenReq` | 请求打开普通 client-core 私人通道，普通用户不需要质押资产 |
| 3 | `ChannelOpenResp` | 校验 Core Node 签名、通道参数和初始 revocation / commitment point |
| 4 | 构造 BTC L1 funding | funding 输出必须支付到 2-of-2 通道地址 |
| 5 | `FundingCreatedReq` / `FundingCreatedResp` | 双方交换初始承诺交易、de-anchor 和相关签名 |
| 6 | 广播 funding | 结果未知时锁定输入并轮询 L1 |
| 7 | `FundingBroadcastedReq` / `FundingBroadcastedResp` | 双方进入等待确认和 anchor 阶段 |
| 8 | L1 funding 确认，L2 ascend / anchor 确认 | L1/L2 indexer 都可复核 |
| 9 | 通道 ready | safety snapshot 返回最新承诺交易和 punish coverage |

Agent 验证：通道地址由 client pubkey 与 core node pubkey 生成；funding outpoint、初始 commitment、L2 anchor 和 commit height 一致。

## Splicing-in

目标：把新的 BTC L1 资产加入已有通道。

| 步骤 | 消息 / 动作 | 验证点 |
| --- | --- | --- |
| 1 | 读取 safety snapshot | 通道 ready，无 pending，punish coverage 完整 |
| 2 | Adapter 选择或构造 L1 资产输入 | Agent 只提供资产、金额和授权，不直接选择 UTXO |
| 3 | `SplicingInReq` | 声明资产、金额、当前 commit height 和是否需要发送 splicing tx |
| 4 | `SplicingInResp` | 校验新容量、新余额、服务费和下一撤销材料 |
| 5 | `SplicingInCommitSigReq` / `SplicingInCommitSigResp` | 交换 splicing、anchor 和 commitment 签名 |
| 6 | 广播相关 L1/L2 交易 | BRC20 可能有 transfer inscription 和交易包 |
| 7 | `SplicingInRevokeAndAckReq` / `SplicingInRevokeAndAckResp` | 撤销旧状态，确认新承诺状态 |
| 8 | 等待 indexer 收敛 | L1 funding 与 L2 ascend / anchor 可复核 |

Agent 验证：新资产进入 commitment balance；如果 indexer 尚未返回 spendable UTXO，应标记为 pending，而不是继续 unlock/lock。

## Expand

目标：把已经位于通道地址、但未纳入当前承诺状态的资产加入通道管理。

Expand 常见于三种情况：

1. 用户已经把资产转入通道地址。
2. 前序 splicing-in 在网络异常后只完成了一部分。
3. 通道恢复后发现通道地址上有属于 client 的资产。

流程与 splicing-in 类似，但客户端必须先通过 L1/L2 indexer 判断该资产是否已经 ascend。已经 ascend 的资产不能重复 anchor；未 ascend 且可证明属于通道地址的新资产，才进入 anchor 流程。

Agent 验证：expand 后 commit height 增加，资产被当前 commitment 覆盖，L2 总量没有因重复 anchor 增加。

## Unlock

目标：把通道内属于用户的资产释放到用户 L2 地址。

| 步骤 | 消息 / 动作 | 验证点 |
| --- | --- | --- |
| 1 | 读取 safety snapshot | 通道 ready，资产在 commitment balance 中，punish coverage 完整 |
| 2 | `UnlockReq` | 请求释放资产到用户 L2 地址 |
| 3 | `UnlockResp` | Core Node 接受更新，返回本轮 revocation / next revocation 材料 |
| 4 | `UnlockCommitSigReq` / `UnlockCommitSigResp` | 交换新承诺签名和旧状态撤销确认 |
| 5 | `UnlockRevokeAndAckReq` / `UnlockRevokeAndAckResp` | 完成旧状态撤销，确认 unlock 交易签名 |
| 6 | L2 indexer 确认 | 用户 L2 地址出现资产，commit height 单调增加 |

Unlock 不需要用户提供 BTC L1 fee rate 或 fee UTXO。SatoshiNet L2 可以存在 0 聪资产 UTXO。

Agent 验证：用户 L2 spendable balance 增加；通道 commitment balance 减少；最新 local commitment 与 remote commitment 都已更新。

## Lock

目标：把用户 L2 地址上的资产重新纳入通道保护。

| 步骤 | 消息 / 动作 | 验证点 |
| --- | --- | --- |
| 1 | 查询 L2 spendable UTXO | 资产必须可花费，不能只是 pending |
| 2 | `LockReq` | 请求把资产锁回通道 |
| 3 | `LockResp` | 返回新承诺签名材料和下一撤销材料 |
| 4 | `LockCommitSigAndRevokeReq` / `LockCommitSigAndRevokeResp` | 交换签名并撤销旧状态 |
| 5 | `LockAckReq` / `LockAckResp` | 完成本轮状态推进 |
| 6 | 读取 safety snapshot | commit height 增加，资产重新进入通道控制 |

Agent 验证：资产从用户 L2 spendable balance 转入通道 commitment balance，且旧 remote commitment 有 punish coverage。

## Lock-with-expand

目标：在通道容量不足或资产集合不足时，把用户资产重新纳入通道控制。

Lock-with-expand 是资产安全能力，不是简单的转账接口。它用于保证用户随时可以把已经在 L2 或通道地址附近的资产重新纳入通道承诺保护。

Agent 验证：操作后资产被当前 commitment 覆盖；如果需要 expand，不能重复 ascend；如果通道状态不完整，应优先进入恢复流程。

## Splicing-out

目标：把通道资产退出到 BTC L1 地址。

| 步骤 | 消息 / 动作 | 验证点 |
| --- | --- | --- |
| 1 | 读取 safety snapshot | 通道 ready，无 pending，资产在 commitment balance 中 |
| 2 | Adapter 构造退出交易包 | BRC20 可能需要 transfer inscription；Runes/ORDX 遵守 L1 协议规则 |
| 3 | `SplicingOutReq` | 请求资产退出到 L1 地址 |
| 4 | `SplicingOutResp` | 校验服务费、新容量、新余额和下一撤销材料 |
| 5 | `SplicingOutCommitSigReq` / `SplicingOutCommitSigResp` | 交换 L1 退出、L2 descend 和承诺签名 |
| 6 | 广播 L2 descend / de-anchor 和 L1 相关交易 | 结果未知时进入恢复，不重复消费输入 |
| 7 | `SplicingOutRevokeAndAckReq` / `SplicingOutRevokeAndAckResp` | 撤销旧状态，完成本轮更新 |
| 8 | L1/L2 indexer 确认 | L2 资产减少，L1 目标地址收到资产 |

Agent 验证：L2 descend 与 L1 输出可关联；退出资产、金额、目标地址与用户授权一致。

## Cooperative Close

目标：双方协商关闭通道，把资产按最新状态退出。

| 步骤 | 消息 / 动作 | 验证点 |
| --- | --- | --- |
| 1 | 读取 safety snapshot | 通道 ready，无 pending，最新 commitment 可验证 |
| 2 | `ChannelCloseReq` | 请求协商关闭 |
| 3 | `ChannelCloseResp` | Core Node 返回 closing、de-anchor 和关联交易签名 |
| 4 | `ClosingSignedReq` / `ClosingSignedResp` | 客户端签署并确认关闭交易 |
| 5 | 广播关闭相关交易 | 结果未知时查询 L1/L2 tx 可见性 |
| 6 | `ClosingBroadcastedReq` / `ClosingBroadcastedResp` | 双方进入关闭完成或等待确认 |
| 7 | L1/L2 indexer 确认 | 通道资产退出或进入用户可控地址 |

Agent 验证：关闭前后的资产归属一致，没有遗漏通道地址上的用户资产。

## Force Close 与 Sweep

目标：当 Core Node 离线、拒绝服务或无法协商关闭时，用户单方面关闭通道。

| 步骤 | 动作 | 验证点 |
| --- | --- | --- |
| 1 | `stp.force_close_plan` | 返回最新 local commitment、CSV 延迟、后续 sweep 条件 |
| 2 | 广播 local commitment | 必须是最新承诺状态 |
| 3 | 等待 CSV 或其他 spend 条件 | 监控 peer 是否广播旧 remote commitment |
| 4 | `stp.sweep_build` | 构造清扫交易，默认 dry-run |
| 5 | 用户授权后广播 sweep | 用户取回可清扫资产 |

如果 Core Node 广播它持有的 commitment，用户可选择重新打开通道或清扫属于自己的通道资产。只有 Core Node 广播旧 commitment 时，用户才进入 punish 路径。

## Punish

目标：当 Core Node 广播旧 remote commitment 时，用户使用撤销材料惩罚旧状态。

| 步骤 | 动作 | 验证点 |
| --- | --- | --- |
| 1 | Watchtower 或 Agent 发现旧 commitment | txid 命中已撤销 remote commitment |
| 2 | `stp.punish_status` | 确认惩罚材料存在且 CSV 窗口仍有效 |
| 3 | `stp.punish_build` | 构造并 dry-run 验证 punish tx |
| 4 | 用户授权或测试网演练授权 | 主网必须保护用户授权边界 |
| 5 | `stp.punish_broadcast` | 广播惩罚交易 |
| 6 | L1 indexer 确认 | 通道进入 punished / closed 状态 |

测试网可以通过保留旧 commitment 和广播旧 commitment 的接口演练这个过程。主网不得开放故障注入接口。

## Reopen / Rebuild / Restore

目标：在通道关闭、状态丢失或链上结果未知后，恢复用户资产控制。

| 能力 | 流程重点 | 验证点 |
| --- | --- | --- |
| Restore | 从本地备份、peer 状态或持久化数据恢复 | 最新 commitment 与 punish coverage 可证明 |
| Reopen | 旧通道关闭但通道地址仍有用户资产 | 必要时由用户补充新 funding；不重复支付不必要费用 |
| Rebuild | channel point 或状态丢失，需要从 L1/L2 ledger 重建 | 依据 ascend / descend 记录分配资产，不重复 anchor |
| Expand | 已在通道地址的资产未被当前 commitment 覆盖 | 纳入承诺状态并推进 commit height |

Agent 验证：恢复后必须重新生成 safety snapshot。只要 `PUNISH_COVERAGE_UNKNOWN`、pending 不明、资产 ledger 不一致或通道状态不明，就不能继续普通价值移动。

## Agent 演练顺序

一个完整测试网演练可以按以下顺序执行：

1. 安装 SAT20 Wallet 或等价安全钱包边界。
2. 创建测试钱包，连接默认 Core Node。
3. Open 普通 client-core 通道。
4. Unlock sats，观察 commit height 增加。
5. Lock sats，确认资产回到通道保护。
6. Splicing-in Runes，等待 L1/L2 indexer 确认。
7. Unlock / Lock Runes。
8. Splicing-in BRC20，验证 transfer inscription 交易包。
9. Unlock / Lock BRC20。
10. Splicing-out 一种协议资产到 L1。
11. 导出 safety snapshot、commitment export 和 punish status。
12. 在测试网触发旧 commitment 广播，构造并广播 punish tx。
13. 使用 L1 浏览器、L2 浏览器、L1 indexer 和 L2 indexer 解释每一笔交易的作用。

演练目标不是展示余额变化，而是证明：用户持有最新退出路径，能识别旧状态，能在 peer 作恶时惩罚，能通过 indexer 独立复核资产事实。
