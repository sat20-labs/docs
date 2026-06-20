# STP 消息与数据模型

本文定义第三方 STP 客户端需要理解的协议消息、公共数据对象和错误语义。它面向钱包、SDK、PWA adapter、CLI、后端服务和 AI Agent 工具，目标是让任何开发语言都能实现客户端并接入兼容的 Core Node。

本文不是某个代码库的类型说明。开源 wallet SDK 中的 wire message 名称可以作为互操作参考，但协议实现应以本文描述的语义、签名、状态推进和可验证证据为准。

## SDK 源码参考

STP client / peer 消息定义已经迁移到开源 wallet SDK。本文给出协议层结构，源码是开发者核对字段名和最新 wire 定义的直接入口：

| 内容 | GitHub |
| --- | --- |
| STP channel 消息 | [sat20wallet/sdk/wire/types_stp_channel.go](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wire/types_stp_channel.go) |
| Ping、ActionSync、PerformAction | [sat20wallet/sdk/wire/types.go](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wire/types.go) |
| `MsgHeader`、`BaseResp` | [sat20wallet/sdk/wire/types_contract.go](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wire/types_contract.go) |

跨语言实现应以 JSON 字段名作为互操作边界。二进制字段在现有 Go SDK 中按 `[]byte` JSON 规则编码；非 Go 实现应在 adapter 层固定 hex 或 base64 编码，并在签名序列化中保持确定性。

## 参与方

| 参与方 | 协议职责 |
| --- | --- |
| Client Wallet | 用户钱包或受钱包授权的 adapter。持有用户私钥、通道状态、承诺交易、撤销材料和 pending 事务 |
| Core Node | 为普通用户提供 STP 服务的节点。它与 Client Wallet 建立私人通道，协签承诺交易，维护服务侧通道状态，并运行或配置 L1 indexer |
| Bootstrap Node | Core Node 的发现、准入和网络组织角色。普通用户打开私人通道时不直接把 Bootstrap Node 当作 STP peer |
| L1 Indexer | BTC L1 资产事实层。解析 UTXO、Ordinals、ORDX、BRC20、Runes、确认数、交易可见性和 reorg |
| L2 Indexer | SatoshiNet 资产事实层。解析聪网 UTXO、ascend、descend、通道、合约和交易确认 |

普通 STP 消息主要发生在 Client Wallet 和 Core Node 之间。L1/L2 indexer 不签署通道状态，但它们提供客户端验证资产事实和恢复 pending 事务所需的证据。

## 协议分层

STP 客户端通常分三层实现：

| 层 | 内容 |
| --- | --- |
| 用户操作层 | `stp.open`、`stp.splicing_in`、`stp.unlock`、`stp.lock`、`stp.close` 等 JSON 操作。它面向 UI、CLI 和 AI Agent |
| STP peer 消息层 | Client Wallet 与 Core Node 之间的认证消息。它负责协商、签名、撤销、ack 和状态推进 |
| 链与索引证据层 | BTC L1、SatoshiNet、L1 indexer、L2 indexer 返回的 UTXO、资产、交易、ascend、descend 和通道状态 |

上层 adapter 可以隐藏资产 UTXO、fee UTXO、BRC20 transfer inscription、stub UTXO 和交易包细节，但不能隐藏安全证据。Agent 至少要能读取 safety snapshot、commitment export、punish status、force close plan 和 transaction status。

## 消息信封

所有会改变通道状态、消耗资产、泄露撤销材料或确认广播结果的消息，都必须可认证。推荐信封如下：

| 字段 | 含义 |
| --- | --- |
| `version` | 协议消息版本 |
| `msg_id` | 消息类型或路径 |
| `chain` | 网络标识，例如 mainnet、testnet、testnet4 |
| `channel_id` | 通道地址或通道标识 |
| `commit_height` | 当前承诺高度；会改变承诺状态的消息必须携带 |
| `request_id` | 本次事务的稳定 ID，用于重试和恢复 |
| `sender_pubkey` | 发送方公钥 |
| `node_id` | Core Node 身份，可选但建议携带 |
| `payload` | 具体消息内容 |
| `signature` | 对除签名字段外的确定性序列化内容签名 |

接收方必须校验签名、链 ID、通道身份、发送方身份、承诺高度和资产数量。承诺高度回退、链 ID 不匹配、签名无效、资产不守恒或消息与 pending 事务不一致，都必须拒绝。

## 公共数据对象

### Channel Identity

| 字段 | 含义 |
| --- | --- |
| `channel_id` | 通道标识，通常可由通道地址表示 |
| `channel_address` | Client Wallet 与 Core Node 的 2-of-2 地址 |
| `client_pubkey` | 用户通道公钥 |
| `core_node_pubkey` | Core Node 通道公钥 |
| `channel_point` | 当前承诺交易花费的 BTC L1 outpoint |
| `commit_height` | 当前承诺高度 |
| `csv_delay` | 强制关闭后的惩罚窗口 |

### Asset Descriptor

| 字段 | 含义 |
| --- | --- |
| `asset_type` | `sats`、`ordx`、`runes`、`brc20` 等 |
| `asset_name` | 协议资产名 |
| `amount` | 资产数量，使用字符串避免精度问题 |
| `binding_sat` | ORDX 等绑定聪资产的绑定参数 |
| `selected_asset_only` | 当一个 UTXO 有多种资产时，本次只处理用户明确指定的资产 |

### UTXO Reference

| 字段 | 含义 |
| --- | --- |
| `outpoint` | `txid:vout` |
| `address` | 所属地址 |
| `value_sats` | 白聪数量；SatoshiNet L2 可以为 0 |
| `assets` | 该输出携带的资产列表 |
| `spendable` | 是否已经可作为下一笔交易输入 |
| `source` | `l1` 或 `l2` |

### Commitment Descriptor

| 字段 | 含义 |
| --- | --- |
| `commitment_txid` | 承诺交易 ID |
| `commitment_tx` | 交易 hex 或结构化只读对象 |
| `commit_height` | 该承诺对应的高度 |
| `owner` | `local` 或 `remote` |
| `channel_point` | 该承诺花费的通道 outpoint |
| `balances` | 该承诺下双方资产归属 |
| `deanchor_tx` | 对应的 L2 descend / de-anchor 交易，可为空 |
| `prev_txs` / `next_txs` | 为 BRC20、stub 或交易包准备的关联交易 |
| `others` | 用于清扫通道地址中用户资产的附加承诺或清扫交易 |

客户端不能只保存余额。每次承诺高度推进后，必须持久化最新 local commitment、remote commitment、撤销材料、关联交易和 pending 事务。

### Revocation Descriptor

| 字段 | 含义 |
| --- | --- |
| `revocation_hash` | 旧状态撤销承诺 |
| `revocation_secret` | 撤销秘密或其受控引用，不应暴露给未授权上层 |
| `next_commitment_point` | 下一承诺点 |
| `revoked_commitment_txid` | 已撤销 remote commitment |
| `punish_material_status` | `missing`、`verified`、`broadcastable`、`broadcasted` |

### Safety Snapshot

| 字段 | 含义 |
| --- | --- |
| `status` | `READY_SAFE`、`READY_DEGRADED`、`PUNISH_COVERAGE_UNKNOWN` 等 |
| `channel_id` | 通道标识 |
| `commit_height` | 当前承诺高度 |
| `channel_point` | 当前通道 outpoint |
| `local_commitment` | 本方可广播的最新退出交易摘要 |
| `remote_commitments` | 对方承诺状态摘要和撤销覆盖 |
| `punish_coverage` | 旧 remote commitment 的惩罚覆盖 |
| `pending` | 未完成事务 |
| `l1_view` / `l2_view` | indexer 证据摘要 |

## 消息结构索引

本节列出第三方客户端需要实现或理解的主要消息结构。字段类型使用协议层表达：`bytes` 表示二进制数据，`bytes[]` 表示二进制数组，`bytes[][]` 表示二维签名数组，`string[]` 表示字符串数组。

为保持表格可读性，本文会把一组 embedded 字段写成 `CommitSigInfo`、`SplicingSigInfo` 或 `RevokeAndAck`。实际 JSON wire 中这些字段按 SDK 定义展开，第三方实现应以字段名和签名序列化规则保持兼容。

### 公共结构

`MsgHeader`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` | int | 消息版本 |
| `msgId` | string | 消息类型或路径 |

`BaseResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | int | `0` 表示成功，非 0 表示失败 |
| `msg` | string | 错误或状态文本 |

`OpenChannelFee`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `manageFee` | int64 | 通道管理费用 |
| `mortgageFee` | int64 | Core Node 准入或特定服务相关费用；普通 client open 不应理解为用户质押 |
| `minReserveSats` | int64 | 通道最低保留白聪 |
| `commitmentFee` | int64 | 承诺交易费用预算 |
| `commitmentFeeRate` | int64 | 承诺交易费率参数 |
| `splicingInFee` | int64 | splicing-in 服务费用 |
| `splicingOutFee` | int64 | splicing-out 服务费用 |

`CommitSigInfo`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `commitSig` | bytes[] | commitment 签名 |
| `commitDeAnchorSig` | bytes[] | commitment 对应 de-anchor / anchor 签名 |
| `commitPrevTxSig` | bytes[][] | commitment 前置交易签名，例如 BRC20 transfer inscription 相关交易 |
| `commitNextTxSig` | bytes[][] | commitment 后续交易签名 |
| `commitOtherPrevTxSig` | bytes[][][] | 附加清扫交易的前置交易签名 |
| `commitOtherTxSig` | bytes[][] | 附加清扫交易签名 |

`SplicingSigInfo`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `splicingPrevTxSig` | bytes[][] | splicing 前置交易签名 |
| `splicingSig` | bytes[] | splicing 交易签名 |
| `deAnchorSig` | bytes[] | de-anchor 或 anchor 交易签名 |

`RevokeAndAck`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `revocation` | bytes32 | 上一个 commitment revocation hash 的 preimage |
| `nextRevKey` | bytes | 下一承诺点或下一 revocation key |

### 连接与同步结构

`AbbrChannelInfo`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` | int | 通道数据版本 |
| `channelId` | string | 通道标识 |
| `commitHeight` | int | 当前承诺高度 |
| `staticMerkleRoot` | bytes | 静态通道数据 root |
| `localAssetMerkleRoot` | bytes | 本方资产 root |
| `remoteAssetMerkleRoot` | bytes | 对方资产 root |

`PingRequest`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `pubKey` | bytes | 发送方公钥 |
| `mode` | string | ping 模式 |
| `info` | AbbrChannelInfo | 通道摘要，可为空 |
| `nodeId` | bytes | Core Node 身份，可选 |

`PingReq = PingRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `msgSig` | bytes | 对消息内容的签名 |

`PingResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` / `msg` | BaseResp | 结果 |
| `commitHeight` | int | peer 看到的承诺高度 |
| `action` | string | 下一动作 |
| `param` | string | 下一动作参数 |
| `paramSig` | bytes | 参数签名 |

`ActionSyncReq = ActionSyncRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `pubKey` | bytes | 请求方公钥 |
| `reason` | string | 同步原因 |
| `nodeId` | bytes | Core Node 身份，可选 |
| `msgSig` | bytes | 请求签名 |

`ActionSyncResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` / `msg` | BaseResp | 结果 |
| `channelData` | bytes | 可恢复的通道数据 |

### Open 结构

`ChannelOpenReq = OpenChannelRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `nodeId` | bytes | Core Node 身份 |
| `channelType` | int | 通道类型 |
| `channelWalletId` | int | 子钱包或子账户 ID |
| `fundingKey` | bytes | 本方 funding 公钥 |
| `feeRate` | int64 | BTC L1 费率参数 |
| `localFundingAmount` | int64 | 本方 funding 白聪数量 |
| `outpoints` | string[] | 可选 funding 输入 |
| `needSendFundingTx` | bool | 是否需要客户端构造并广播 funding tx |
| `skipOpeningAnchorTx` | bool | 恢复场景是否跳过 opening anchor |
| `l2DrainTxId` | string | 恢复场景关联的 L2 drain txid |
| `memo` | bytes | 备注 |
| `msgSig` | bytes | 请求签名 |

`ChannelOpenResp = BaseResp + AcceptChannel`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | 本次 open reservation ID |
| `commitHeight` | int | 初始承诺高度 |
| `csv` | uint16 | CSV 延迟 |
| `openFee` | OpenChannelFee | open 费用参数 |
| `fundingKey` | bytes | Core Node funding 公钥 |
| `revbasePoint` | bytes | Core Node revocation base point |
| `commitPoint` | bytes | Core Node commitment point |
| `invoiceSig` | bytes | 服务端 invoice 签名 |

`FundingCreatedReq = FundingCreated + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | open reservation ID |
| `fundingPoint` | string | funding outpoint |
| `revbasePoint` | bytes | 客户端 revocation base point |
| `commitPoint` | bytes | 客户端 commitment point |
| `commitSig` | bytes[] | 客户端初始 commitment 签名 |
| `deAnchorSig` | bytes[] | 客户端 de-anchor 签名 |
| `msgSig` | bytes | 请求签名 |

`FundingCreatedResp = BaseResp + FundingSigned`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | open reservation ID |
| `commitSig` | bytes[] | Core Node commitment 签名 |
| `deAnchorSig` | bytes[] | Core Node de-anchor 签名 |

`FundingBroadcastedReq = FundingBroadcasted + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | open reservation ID |
| `fundingTxId` | string | 已广播的 BTC L1 funding txid |
| `msgSig` | bytes | 请求签名 |

`FundingBroadcastedResp = BaseResp`

### Unlock 结构

`UnlockReq = UnlockRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `channel` | string | 通道标识 |
| `commitHeight` | int | 当前承诺高度 |
| `assetName` | string | 资产名 |
| `amt` | string[] | 释放数量列表 |
| `feeRate` | int64 | 兼容字段；SatoshiNet unlock 不应要求用户设置 BTC fee rate |
| `feeUtxos` | string[] | 兼容字段；adapter 不应暴露给普通 Agent 选择 |
| `address` | string[] | 目标 L2 地址列表 |
| `memo` | bytes | 备注 |
| `reason` | string | 操作原因 |
| `more` | bytes | 扩展数据 |
| `nodeId` | bytes | Core Node 身份，可选 |
| `msgSig` | bytes | 请求签名 |

`UnlockResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` / `msg` | BaseResp | 结果 |
| `id` | int64 | reservation ID |
| `revealKey` | bytes | 本轮 reveal key |
| `rev` | bytes | 本轮 revocation key |
| `nextRevKey` | bytes | 下一 revocation key |
| `feeRate` | int64 | 返回的费用参数 |

`UnlockCommitSigReq = CommitSigInfo + rev keys + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `channel` | string | 通道标识 |
| `id` | int64 | reservation ID |
| `commitSigInfo` | CommitSigInfo | 新 commitment 相关签名集合 |
| `rev` | bytes | 本方 revocation key |
| `nextRevKey` | bytes | 本方下一 revocation key |
| `msgSig` | bytes | 请求签名 |

`UnlockCommitSigResp = BaseResp + CommitSigInfo + RevokeAndAck`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | reservation ID |
| `commitSigInfo` | CommitSigInfo | 对方 commitment 相关签名集合 |
| `rev` | RevokeAndAck | 对方对旧状态的撤销确认 |

`UnlockRevokeAndAckReq`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `channel` | string | 通道标识 |
| `id` | int64 | reservation ID |
| `rev` | RevokeAndAck | 客户端对旧状态的撤销确认 |
| `unlockSig` | bytes[] | unlock 交易签名 |
| `msgSig` | bytes | 请求签名 |

`UnlockRevokeAndAckResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` / `msg` | BaseResp | 结果 |
| `id` | int64 | reservation ID |
| `unlockSig` | bytes[] | Core Node unlock 交易签名 |

### Lock 结构

`LockReq = LockRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `channel` | string | 通道标识 |
| `commitHeight` | int | 当前承诺高度 |
| `assetName` | string | 资产名 |
| `amt` | string | 锁入数量 |
| `feeRate` | int64 | 兼容字段 |
| `lockUtxos` | string[] | 兼容字段；adapter 通常内部选择 |
| `feeUtxos` | string[] | 兼容字段；adapter 通常内部选择 |
| `revealKey` | bytes | reveal key |
| `rev` | bytes | revocation key |
| `nextRevKey` | bytes | 下一 revocation key |
| `needSendLockTx` | bool | 是否需要发送 lock tx |
| `memo` | bytes | 备注 |
| `reason` | string | 操作原因 |
| `more` | bytes | 扩展数据 |
| `nodeId` | bytes | Core Node 身份，可选 |
| `msgSig` | bytes | 请求签名 |

`LockResp = BaseResp + CommitSigInfo + rev keys`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | reservation ID |
| `feeRate` | int64 | 返回的费用参数 |
| `commitSigInfo` | CommitSigInfo | Core Node commitment 相关签名 |
| `rev` | bytes | Core Node revocation key |
| `nextRevKey` | bytes | Core Node 下一 revocation key |

`LockCommitSigAndRevokeReq`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `channel` | string | 通道标识 |
| `id` | int64 | reservation ID |
| `commitSigInfo` | CommitSigInfo | 客户端 commitment 相关签名 |
| `rev` | RevokeAndAck | 客户端对旧状态的撤销确认 |
| `msgSig` | bytes | 请求签名 |

`LockCommitSigAndRevokeResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` / `msg` | BaseResp | 结果 |
| `id` | int64 | reservation ID |
| `rev` | RevokeAndAck | Core Node 对旧状态的撤销确认 |
| `lockSig` | bytes[] | Core Node lock 交易签名 |

`LockAckReq`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `channel` | string | 通道标识 |
| `id` | int64 | reservation ID |
| `lockSig` | bytes[] | 客户端 lock 交易签名 |
| `msgSig` | bytes | 请求签名 |

`LockAckResp = BaseResp + id`

### Splicing-in 结构

`SplicingInReq = SplicingInRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `channel` | string | 通道标识 |
| `commitHeight` | int | 当前承诺高度 |
| `assetName` | string | 资产名 |
| `amt` | string | 加入通道的资产数量 |
| `stub` | string | stub UTXO，可选 |
| `utxos` | string[] | 兼容字段；adapter 通常内部选择资产 UTXO |
| `fees` | string[] | 兼容字段；adapter 通常内部选择 fee UTXO |
| `preTxInputs` | string[] | 前置交易输入 |
| `revealKey` | bytes | reveal key |
| `needSendSplicingTx` | bool | 是否需要构造并广播 L1 splicing tx |
| `feeRate` | int64 | BTC L1 费率参数 |
| `reason` | string | 操作原因 |
| `memo` | bytes | 备注 |
| `nodeId` | bytes | Core Node 身份，可选 |
| `msgSig` | bytes | 请求签名 |

`SplicingInResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` / `msg` | BaseResp | 结果 |
| `id` | int64 | reservation ID |
| `serviceFee` | int64 | 服务费 |
| `rev` | bytes | Core Node revocation key |
| `nextRevKey` | bytes | Core Node 下一 revocation key |
| `newCapacity` | int64 | 新通道容量 |
| `newLocalBalance` | string | 新本方余额 |
| `newRemoteBalance` | string | 新对方余额 |
| `invoiceSig` | bytes | invoice 签名 |

`SplicingInCommitSigReq = SplicingSigInfo + CommitSigInfo + rev keys + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `channel` | string | 通道标识 |
| `id` | int64 | reservation ID |
| `splicingSigInfo` | SplicingSigInfo | splicing 与 anchor/de-anchor 签名 |
| `commitSigInfo` | CommitSigInfo | commitment 签名 |
| `rev` | bytes | 客户端 revocation key |
| `nextRevKey` | bytes | 客户端下一 revocation key |
| `msgSig` | bytes | 请求签名 |

`SplicingInCommitSigResp = BaseResp + SplicingSigInfo + CommitSigInfo + RevokeAndAck`

`SplicingInRevokeAndAckReq`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `channel` | string | 通道标识 |
| `id` | int64 | reservation ID |
| `txId` | string | splicing txid |
| `rev` | RevokeAndAck | 客户端对旧状态的撤销确认 |
| `msgSig` | bytes | 请求签名 |

`SplicingInRevokeAndAckResp = BaseResp + id`

### Splicing-out 结构

`SplicingOutReq = SplicingOutRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `channel` | string | 通道标识 |
| `commitHeight` | int | 当前承诺高度 |
| `assetName` | string | 资产名 |
| `amt` | string | 退出数量 |
| `stub` | string | stub UTXO |
| `utxos` | string[] | 兼容字段；adapter 通常内部选择资产 UTXO |
| `fees` | string[] | 兼容字段；adapter 通常内部选择 fee UTXO |
| `preTxInputs` | string[] | 前置交易输入 |
| `revealKey` | bytes | reveal key |
| `address` | string | BTC L1 目标地址 |
| `feeRate` | int64 | BTC L1 费率参数 |
| `reason` | string | 操作原因 |
| `memo` | bytes | 备注 |
| `nodeId` | bytes | Core Node 身份，可选 |
| `msgSig` | bytes | 请求签名 |

`SplicingOutResp` 与 `SplicingInResp` 字段一致。

`SplicingOutCommitSigReq = SplicingSigInfo + CommitSigInfo + rev keys + msgSig`

`SplicingOutCommitSigResp = BaseResp + SplicingSigInfo + CommitSigInfo + RevokeAndAck`

`SplicingOutRevokeAndAckReq`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `channel` | string | 通道标识 |
| `id` | int64 | reservation ID |
| `deAnchorTxId` | string | L2 descend / de-anchor txid |
| `rev` | RevokeAndAck | 客户端对旧状态的撤销确认 |
| `msgSig` | bytes | 请求签名 |

`SplicingOutRevokeAndAckResp = BaseResp + id`

### Close 结构

`ChannelCloseReq = CloseChannelRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `channel` | string | 通道标识 |
| `commitHeight` | int | 当前承诺高度 |
| `feeRate` | int64 | BTC L1 费率参数，可选 |
| `revealKey` | bytes | reveal key，可选 |
| `nodeId` | bytes | Core Node 身份，可选 |
| `msgSig` | bytes | 请求签名 |

`ChannelCloseResp = BaseResp + ClosingSigned`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | reservation ID |
| `deAnchorSig` | bytes[] | de-anchor 签名 |
| `closingsig` | bytes[] | closing 交易签名 |
| `prevTxSig` | bytes[][] | 前置交易签名 |

`ClosingSignedReq`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | reservation ID |
| `deAnchorSig` | bytes[] | 客户端 de-anchor 签名 |
| `closingsig` | bytes[] | 客户端 closing 签名 |
| `prevTxSig` | bytes[][] | 客户端前置交易签名 |
| `channel` | string | 通道标识 |
| `msgSig` | bytes | 请求签名 |

`ClosingSignedResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` / `msg` | BaseResp | 结果 |
| `splicingTxId` | string | 关闭过程中生成的退出或 splicing txid |

`ClosingBroadcastedReq`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | reservation ID |
| `deAnchorTxId` | string | 已广播的 de-anchor txid |
| `channel` | string | 通道标识 |
| `msgSig` | bytes | 请求签名 |

`ClosingBroadcastedResp = BaseResp`

### Recover Payment 结构

`RecoverPaymentRequireReq = RecoverPaymentRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `channel` | string | 通道标识 |
| `commitHeight` | int | 当前承诺高度 |
| `paymentTxId` | string | 需要恢复的 payment txid |
| `reason` | string | 恢复原因 |
| `nodeId` | bytes | Core Node 身份，可选 |
| `msgSig` | bytes | 请求签名 |

Recover payment 后续结构与 unlock 的 commit-sig、revoke-and-ack 模式一致，只是最终签名字段为 `paymentSig`。

### PerformAction 结构

`PerformActionReq = PerformActionRequest + msgSig`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `version` / `msgId` | MsgHeader | 消息头 |
| `action` | string | action / reservation 类型 |
| `param` | bytes | action 参数 |
| `feeRate` | int64 | BTC L1 费率参数 |
| `reqTime` | int64 | 请求时间 |
| `sendInL1` | bool | fee 或相关交易是否在 L1 发送 |
| `more` | bytes | 扩展数据 |
| `pubKey` | bytes | 请求方公钥 |
| `nodeId` | bytes | Core Node 身份，可选 |
| `msgSig` | bytes | 请求签名 |

`PerformActionResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` / `msg` | BaseResp | 结果 |
| `id` | int64 | action ID |
| `serviceAddress` | string | 服务费收款地址 |
| `serviceFee` | int64 | 服务费 |
| `invoice` | bytes | invoice |
| `invoiceSig` | bytes | invoice 签名 |

`PerformActionAckReq`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int64 | action ID |
| `tx` | string | fee 交易 hex |
| `txId` | string | fee txid |

`PerformActionAckResp`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` / `msg` | BaseResp | 结果 |
| `id` | int64 | action ID |
| `status` | int | action 状态 |
| `actionResvId` | int64 | 关联 reservation ID |
| `actionStatus` | int | 关联 reservation 状态 |
| `actionResult` | bytes | action 结果 |

## 消息族

### 连接与同步

| 消息 | 方向 | 语义 |
| --- | --- | --- |
| `PingRequest` / `PingReq` | Client Wallet -> Core Node | 握手、身份证明、通道摘要同步 |
| `PingResponse` / `PingResp` | Core Node -> Client Wallet | 返回 peer 当前承诺高度、下一动作或需要同步的信息 |
| `ActionSyncRequest` / `ActionSyncReq` | 任一方 -> 对方 | 在重启、结果未知或状态不一致时请求同步事务状态 |
| `ActionSyncResp` | 对方 -> 请求方 | 返回可同步的通道数据或 pending 事务数据 |

### Open Channel

| 消息 | 方向 | 语义 |
| --- | --- | --- |
| `OpenChannelRequest` / `ChannelOpenReq` | Client Wallet -> Core Node | 请求打开私人通道，携带 funding 意图、通道公钥、金额和 memo |
| `ChannelOpenResp` | Core Node -> Client Wallet | 接受通道，返回 CSV、费用、服务端 funding key、revocation base point 和 commitment point |
| `FundingCreatedReq` | Client Wallet -> Core Node | 提交 funding outpoint、初始承诺签名和相关 de-anchor 签名 |
| `FundingCreatedResp` | Core Node -> Client Wallet | 返回服务端签名，形成双方可验证的初始承诺状态 |
| `FundingBroadcastedReq` | Client Wallet -> Core Node | 通知 BTC L1 funding 已广播 |
| `FundingBroadcastedResp` | Core Node -> Client Wallet | 确认进入等待确认和 anchor 阶段 |

Open 完成后，客户端必须能通过 L1 indexer 验证 funding，通过 L2 indexer 验证 ascend / anchor，并生成安全快照。

### Unlock

| 消息 | 方向 | 语义 |
| --- | --- | --- |
| `UnlockRequest` / `UnlockReq` | Client Wallet -> Core Node | 请求把通道资产释放到用户 L2 地址 |
| `UnlockResp` | Core Node -> Client Wallet | 接受更新，返回本轮 revocation / next revocation 材料 |
| `UnlockCommitSigReq` | Client Wallet -> Core Node | 发送新承诺签名，并提供本方下一状态材料 |
| `UnlockCommitSigResp` | Core Node -> Client Wallet | 返回服务端承诺签名和对旧状态的 revoke-and-ack |
| `UnlockRevokeAndAckReq` | Client Wallet -> Core Node | 客户端撤销旧状态并确认 unlock 交易签名 |
| `UnlockRevokeAndAckResp` | Core Node -> Client Wallet | 服务端确认，本轮状态推进完成 |

Unlock 会推进 commit height。SatoshiNet 没有 BTC L1 fee rate 语义，普通 adapter 不应要求用户提供 fee UTXO。

### Lock

| 消息 | 方向 | 语义 |
| --- | --- | --- |
| `LockRequest` / `LockReq` | Client Wallet -> Core Node | 请求把用户 L2 资产重新锁回通道 |
| `LockResp` | Core Node -> Client Wallet | 接受更新，返回承诺签名材料和下一 revocation 材料 |
| `LockCommitSigAndRevokeReq` | Client Wallet -> Core Node | 发送承诺签名并撤销旧状态 |
| `LockCommitSigAndRevokeResp` | Core Node -> Client Wallet | 返回服务端撤销确认和 lock 交易签名 |
| `LockAckReq` | Client Wallet -> Core Node | 最终确认 lock 交易签名 |
| `LockAckResp` | Core Node -> Client Wallet | 本轮状态推进完成 |

Lock-with-expand 可以理解为 Lock 与 Expand 的组合能力：当通道容量或资产集合不足时，客户端应能把资产重新纳入通道控制权。

### Splicing-in

| 消息 | 方向 | 语义 |
| --- | --- | --- |
| `SplicingInRequest` / `SplicingInReq` | Client Wallet -> Core Node | 请求把 BTC L1 资产加入已有通道 |
| `SplicingInResp` | Core Node -> Client Wallet | 返回服务费、新容量、新余额和下一 revocation 材料 |
| `SplicingInCommitSigReq` | Client Wallet -> Core Node | 发送 splicing、anchor/de-anchor、commitment 相关签名 |
| `SplicingInCommitSigResp` | Core Node -> Client Wallet | 返回服务端对应签名和 revoke-and-ack |
| `SplicingInRevokeAndAckReq` | Client Wallet -> Core Node | 通知 splicing 交易 ID 并撤销旧状态 |
| `SplicingInRevokeAndAckResp` | Core Node -> Client Wallet | 本轮状态推进完成 |

Expand 复用 splicing-in 的安全语义，但资产已经在通道地址上。客户端必须通过 L1/L2 indexer 判断是否已经 ascend，避免重复发行 L2 资产。

### Splicing-out

| 消息 | 方向 | 语义 |
| --- | --- | --- |
| `SplicingOutRequest` / `SplicingOutReq` | Client Wallet -> Core Node | 请求把通道资产退出到 BTC L1 地址 |
| `SplicingOutResp` | Core Node -> Client Wallet | 返回服务费、新容量、新余额和下一 revocation 材料 |
| `SplicingOutCommitSigReq` | Client Wallet -> Core Node | 发送 L1 退出、L2 descend / de-anchor 和 commitment 相关签名 |
| `SplicingOutCommitSigResp` | Core Node -> Client Wallet | 返回服务端对应签名和 revoke-and-ack |
| `SplicingOutRevokeAndAckReq` | Client Wallet -> Core Node | 通知 de-anchor 交易 ID 并撤销旧状态 |
| `SplicingOutRevokeAndAckResp` | Core Node -> Client Wallet | 本轮状态推进完成 |

Splicing-out 后，客户端必须能把 L2 descend 与 L1 输出通过 indexer 关联起来。BRC20 可能需要 transfer inscription 交易包，Runes 和 ORDX 必须遵守各自 L1 转移规则。

### Close

| 消息 | 方向 | 语义 |
| --- | --- | --- |
| `CloseChannelRequest` / `ChannelCloseReq` | Client Wallet -> Core Node | 请求协商关闭通道 |
| `ChannelCloseResp` | Core Node -> Client Wallet | 返回 closing、de-anchor 和相关交易签名 |
| `ClosingSignedReq` | Client Wallet -> Core Node | 客户端签署关闭交易并提交 |
| `ClosingSignedResp` | Core Node -> Client Wallet | 返回退出交易或 splicing 交易 ID |
| `ClosingBroadcastedReq` | Client Wallet -> Core Node | 通知关闭相关交易已广播 |
| `ClosingBroadcastedResp` | Core Node -> Client Wallet | 通道进入关闭完成或等待确认状态 |

Force close 不依赖对方在线。客户端广播最新 local commitment 后，必须按 CSV 条件构造 sweep，并继续监控 peer 是否广播旧状态。

### Recover Payment

| 消息 | 方向 | 语义 |
| --- | --- | --- |
| `RecoverPaymentRequest` / `RecoverPaymentRequireReq` | 任一方 -> 对方 | 结果未知或 payment 状态不一致时请求恢复 |
| `RecoverPaymentRequireResp` | 对方 -> 请求方 | 返回恢复所需的 revocation / next revocation 材料 |
| `RecoverPaymentCommitSigReq` | 请求方 -> 对方 | 重新提交承诺签名 |
| `RecoverPaymentCommitSigResp` | 对方 -> 请求方 | 返回对应承诺签名和 revoke-and-ack |
| `RecoverPaymentRevokeAndAckReq` | 请求方 -> 对方 | 完成旧状态撤销与 payment 签名确认 |
| `RecoverPaymentRevokeAndAckResp` | 对方 -> 请求方 | 恢复事务完成 |

### 远程动作

| 消息 | 方向 | 语义 |
| --- | --- | --- |
| `PerformActionRequest` / `PerformActionReq` | Client Wallet -> Core Node | 请求 Core Node 执行需要服务端参与的动作 |
| `PerformActionResp` | Core Node -> Client Wallet | 返回 action id、服务地址、服务费和 invoice |
| `PerformActionAckReq` | Client Wallet -> Core Node | 提交 fee 交易或确认材料 |
| `PerformActionAckResp` | Core Node -> Client Wallet | 返回 action 状态和结果 |

远程动作不替代 STP 通道安全规则。只要动作会改变通道资产或承诺状态，就必须回到承诺交易、撤销材料、commit height 和 indexer 证据。

## 错误与结果未知

| 情况 | 处理原则 |
| --- | --- |
| 签名无效、链 ID 错误、commit height 回退 | 明确失败，拒绝消息 |
| 资产不守恒、UTXO 已花费、通道状态不匹配 | 明确失败或进入恢复；不得继续普通价值移动 |
| EOF、timeout、连接中断、服务重启 | 结果未知，不能直接当成失败 |
| 交易广播后响应丢失 | 按“可能成功”处理，查询 L1/L2 tx 可见性并锁定相关输入 |
| indexer 暂未返回交易 | 查询 mempool、peer 状态和 pending 事务，等待收敛 |

只有在双方仍处于同一旧安全状态、无 pending 事务、相关 L1/L2 交易均不可见时，客户端才可以重新做 preflight 并重试同类操作。

## 测试网故障注入

测试网可以开放保留旧 commitment、广播旧 commitment、构造 punish、广播 punish 等能力，让 AI Agent 验证自己确实持有保护用户资产的材料。

这些能力必须满足：

1. 只能在测试网启用。
2. 主网接口直接拒绝。
3. Agent 必须先 dry-run 验证 commitment、de-anchor、punish 和 sweep。
4. 广播旧 commitment 后，通道应立即进入关闭或已惩罚路径，不再允许普通价值移动。

主网安全不依赖故障注入接口。主网客户端依赖的是本地持久化承诺交易、撤销材料、watchtower 监控和 L1/L2 indexer 证据。
