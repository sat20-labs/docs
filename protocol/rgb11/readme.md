# RGB11 资产与 Wallet SDK

RGB11 是基于 Bitcoin L1、采用客户端验证模型的资产协议。SAT20 Wallet SDK 将 RGB11 合约、资产状态、UTXO 证明、收发流程和本地恢复能力内聚在专用的 `rgb11Manager` 中，并通过统一的钱包接口提供给 PWA、桌面钱包和其他应用。

RGB11 资产的有效性最终由合约、consignment、一次性封印、Bitcoin 交易证据和客户端验证结果决定。Indexer 可以提供交易和 UTXO 证据，但不能替代 RGB11 客户端验证，也不能凭索引结果创造资产余额。

> 当前实现首先完成 Bitcoin L1 钱包闭环。RGB11 资产进入 SatoshiNet 的 STP 流程仍在开发中；在完整 STP 支持上线前，SDK 会把需要 STP 的路径视为不可用。

## 1. 协议版本与源码基线

### 1.1 采用的 RGB 版本

SAT20 的 `rgb11` 协议空间明确锁定在 **RGB 0.11.1 系列**。当前 Go 实现所采用的共识、operations、invoicing、schema 和 PSBT/API 冻结基线为 **`0.11.1-rc.11`**。

版本关系必须按以下方式理解：

- SAT20 协议名：`rgb11`；
- 协议目标：RGB `0.11.1`；
- 冻结的 Rust 共识与数据格式基线：`0.11.1-rc.11`；
- 当前代码不会自动跟随 RGB 上游最新分支；
- RGB `0.12` 具有共识级和数据结构变化，不属于 `rgb11` 的兼容升级；未来接入时必须使用独立协议空间 `rgb12`。

因此，文档中“RGB11”不是泛指所有 RGB 版本，而是特指上述冻结版本集合。

### 1.2 官方 Rust 源码与精确 commit

SAT20 Go 实现以以下冻结的上游 Rust 代码为协议和互操作参考。所有链接均固定到精确 commit，不能用浮动的 `master`、`main` 或 semver 范围替代。

| 领域 | 上游版本 | 上游源码 |
| --- | --- | --- |
| RGB 共识、operation ID、seal、commitment | `rgb-consensus 0.11.1-rc.11` | [`rgb-protocol/rgb-consensus@44e79963`](https://github.com/rgb-protocol/rgb-consensus/commit/44e79963aa4603270eee9aa112ef07a512345e98) |
| Operations、consignment、invoicing | `rgb-ops` / `rgb-invoicing 0.11.1-rc.11` | [`rgb-protocol/rgb-ops@5308b9d4`](https://github.com/rgb-protocol/rgb-ops/commit/5308b9d46c91857513ff5be2459992264687632b) |
| PSBT utilities 与 API | `rgb-psbt-utils 0.11.1-rc.11` | [`rgb-protocol/rgb-api@8d448f46`](https://github.com/rgb-protocol/rgb-api/commit/8d448f46c866d44ca0495ad0e924e57d9fd294dd) |
| 官方 schema：NIA、IFA、CFA、UDA | `rgb-schemas 0.11.1-rc.11` | [`rgb-protocol/rgb-schemas@c5e43e98`](https://github.com/rgb-protocol/rgb-schemas/commit/c5e43e987d18a2398d5f5f6c78629480fd792abd) |
| Strict Encoding | `rgb-strict-encoding 1.0.2` | [`rgb-protocol/rgb-strict-encoding@7698a5e9`](https://github.com/rgb-protocol/rgb-strict-encoding/commit/7698a5e96a2a27d5bfa4cd3560da0e8af8e4a18a) |
| Strict Types | `rgb-strict-types 1.0.2` | [`rgb-protocol/rgb-strict-types@09b58e6c`](https://github.com/rgb-protocol/rgb-strict-types/commit/09b58e6c2db25cef8bdb15e33b8654530607b972) |

### 1.3 钱包互操作参考

钱包流程的主要外部 oracle 是：

- [`RGB-Tools/rgb-lib`](https://github.com/RGB-Tools/rgb-lib)，版本 `0.3.0-beta.7`，固定 commit [`538f2abaa67d7ce96be32d94092e8f1b9e3ea38e`](https://github.com/RGB-Tools/rgb-lib/commit/538f2abaa67d7ce96be32d94092e8f1b9e3ea38e)。它用于核对钱包状态、Esplora 同步、invoice、consignment、签名、接收和余额流程。
- [`RGB-WG/rgb`](https://github.com/RGB-WG/rgb) 官方命令行钱包，固定 tag `v0.11.1-alpha.3`、commit [`a9bba35ceed7e0c4bc4e477f663ab022d7b0a23e`](https://github.com/RGB-WG/rgb/commit/a9bba35ceed7e0c4bc4e477f663ab022d7b0a23e)。它只用于人工核对 CLI 命令面和钱包派生路径。

必须注意：`RGB-WG/rgb v0.11.1-alpha.3` 使用的是 alpha.3 crate 格式，不能作为 `0.11.1-rc.11` consignment/parser 的发布门禁。rc.11 文件互操作以冻结的 rc.11 Rust crates 和 `rgb-lib 0.3.0-beta.7` 为准。

### 1.4 SAT20 Go 实现

SAT20 使用独立的 Go 实现：

- 源代码：[`sat20-labs/rgb11`](https://github.com/sat20-labs/rgb11)；
- Wallet SDK adapter：[`sat20-labs/sat20wallet`](https://github.com/sat20-labs/sat20wallet/tree/main/sdk/wallet/rgb11)；
- 精确上游版本、commit、crate checksum 和翻译映射：[`UPSTREAM_MANIFEST.json`](https://github.com/sat20-labs/rgb11/blob/main/UPSTREAM_MANIFEST.json)；
- 官方互操作说明：[`OFFICIAL_INTEROP.md`](https://github.com/sat20-labs/rgb11/blob/main/OFFICIAL_INTEROP.md)。

`github.com/sat20-labs/rgb11` 是对冻结 Rust 基线的**独立 Go 重实现**，不是 RGB 上游官方 Go SDK，也不是把 Rust 库包装成 Go FFI。共识结构、Strict Encoding、ID、seal、anchor、consignment 和 PSBT 字段必须与冻结上游一致；Wallet SDK、DKVS、Indexer 和 PWA 的接入属于 SAT20 adapter 层。

当前 manifest 记录了部分逐文件翻译关系，例如：

```text
rgb-strict-encoding/rust/src/traits.rs
  -> strict_encoding/encoder.go, strict_encoding/decoder.go

rgb-consensus/src/commit_verify/digest.rs
  -> consensus/tagged_hash.go

rgb-consensus/src/operation/commit.rs
  -> consensus/id.go

rgb-consensus/src/seals/txout/blind.rs
  -> seals/blind.go

rgb-ops/src/containers/consignment.rs
  -> consignment/armor.go
```

Go 实现只有在冻结的 Rust differential vectors、官方 parser round-trip 和钱包互操作门禁通过后，才能声明对应能力已兼容。

## 2. 资产身份

RGB11 资产有两个不同层次的标识：

- **Contract ID / official asset ID**：协议级唯一身份，是验证资产的最终依据；
- **SAT20 AssetName**：钱包、UI 和资产列表使用的可读索引名称。

当前 Wallet SDK 为新发行或导入的合约生成确定性 AssetName：

```text
rgb11:<type>:<normalized_ticker>_<contract_fingerprint>
```

例如：

```text
rgb11:f:usdt_k7m3q9x2d4
```

其中：

- `rgb11` 是协议名；
- `f` 表示同质化资产；
- ticker 会转为小写、限制字符和长度；
- fingerprint 默认取 Contract ID 的 10 字符确定性摘要；
- Contract ID 始终保存在 ticker 扩展信息中，不能仅凭短 ticker 判断资产身份。

短 ticker 只适合显示。未经主资产注册或发行方认证时，UI 应显示带 fingerprint 的名称；只有明确完成认证后，才可以把 `usdt` 等短名作为主要显示名称。

## 3. Wallet SDK 边界

外层 `wallet.Manager` 只暴露 RGB11 领域接口，协议实现由内部 `rgb11Manager` 负责。其职责包括：

- 合约发行、导入和注册；
- consignment 解码与客户端验证；
- RGB11 UTXO、allocation proof 和余额投影；
- invoice、地址接收能力和发送准备；
- PSBT 构造、Tapret carrier 签名和交易广播；
- relay、ACK/NACK 和 pending transfer 生命周期；
- DKVS 加密备份、恢复和多设备冲突检测；
- RGB11 UTXO 锁定与重建。

外层钱包不应重新实现 RGB11 内部函数，也不应直接操作 RGB11 engine store、projection store 或 DKVS transport。

## 4. 发行与导入

### 4.1 发行

`IssueRGB11Asset` 根据发行请求构造 RGB11 合约，并完成：

1. 选择 Bitcoin L1 carrier UTXO；
2. 构造资产分配和合约状态；
3. 生成并验证 RGB11 合约；
4. 保存合约、证明和 ticker 扩展信息；
5. 锁定承载 RGB11 状态的 UTXO；
6. 更新本地资产投影和备份状态。

首版发行入口开放 NIA、IFA 和 UDA；CFA 可以按冻结的官方 schema 导入和验证，但当前 SDK/PWA 不提供 CFA 发行入口。

发行前后的余额都来自客户端可验证状态，不从 L1 Indexer 的普通资产 ticker 接口合成。

### 4.2 导入

导入合约时，SDK 必须先解析和验证合约文件，再注册：

- Contract ID；
- schema；
- canonical AssetName；
- 原始 ticker、normalized ticker 和 fingerprint；
- issuer/control metadata；
- 可选 reject-list 或 policy adapter 信息；
- 当前验证状态。

无效、损坏或与已有状态冲突的合约不能进入可用资产列表。

## 5. 接收方式

### 5.1 Witness invoice

Witness 接收使用当前钱包子账户的固定 P2TR 地址脚本。连续创建多个 invoice 时：

- 每个 invoice 有独立 `RequestID`、金额和过期时间；
- witness script 可以保持为当前子账户的固定地址脚本；
- 收到 consignment 后，仍必须通过其 Contract ID、seal、allocation 和 Bitcoin witness 证据完成验证。

固定地址只解决被动接收和地址稳定性，不降低客户端验证要求。

### 5.2 Blind seal

Blind 模式使用一次性封印。SDK 会为待接收状态保留 carrier UTXO，并使用 `pending-rgb` 原因锁定，直到接收完成、失败、取消或过期。

### 5.3 配置化地址接收

应用可以为一个 Bitcoin 地址发布 RGB11 receive capability/profile，使发送方能够解析该地址对应的接收能力，并通过 DKVS mailbox 投递加密 consignment。该流程适合被动接收，不要求接收方在线生成一次性 invoice。

地址/profile 只描述接收能力和投递位置，不代表接收方已经接受资产。最终接受仍由本地 consignment 验证和 ACK 决定。

## 6. 发送、Relay 与 ACK

标准发送流程为：

1. 解析 invoice 或接收地址能力；
2. 检查资产、余额、UTXO 锁和最小确认数；
3. 构造 transition、consignment、PSBT 和 change seals；
4. 保存 pending transfer；
5. 向接收方投递 consignment；
6. 接收方验证后返回 ACK 或 NACK；
7. ACK 满足策略后广播 Bitcoin 交易；
8. 跟踪确认数并更新 allocation、余额和 UTXO 锁。

SDK 支持三类传输接口：

- SAT20/DKVS relay 与 mailbox；
- 配置化地址投递；
- 标准 RGB JSON-RPC proxy。

公共 relay record 只包含传输定位和校验所需的信息。私有 seal disclosure、完整本地 consignment、签名交易和 change seal 不写入公共 relay record 或 wallet head。

ACK 不是资产有效性的替代证明。接收方只有在本地客户端验证通过后才能签发 ACK；发送方也必须校验 ACK 与 transfer、recipient 和 relay record 的绑定关系。

## 7. UTXO 与余额模型

RGB11 状态绑定 Bitcoin UTXO。Wallet SDK 对相关 UTXO 使用两个锁定原因：

```text
rgb          已确认承载 RGB11 状态
pending-rgb  正在参与待完成的接收或发送流程
```

钱包启动、切换钱包、切换子账户或恢复快照后，会根据 projection store 和 allocation proof 重建锁定集合。

RGB11 余额由本地有效 allocation 汇总。以下情况不会形成可用余额：

- 缺少 allocation proof；
- consignment 验证失败；
- witness 交易或 outpoint 无法确认；
- Contract ID、schema 或 assignment 不匹配；
- 状态被 reject-list/policy 判定为不可接受；
- 本地 RGB11 状态标记为 inconsistent/broken。

## 8. DKVS 钱包备份

RGB11 钱包状态使用独立 DKVS path，不与账户管理或其他模块共享 generation。核心对象为：

```text
/personal/<account_id>/rgb11/<wallet_id>/head
/blob/<account_id>/<rgb11_snapshot_key>
```

实际 key 由 SDK 的 `RGB11WalletHeadPath` 和 `RGB11WalletSnapshotBlobKey` 统一生成。

### 8.1 Head 与 snapshot

- snapshot 包含 RGB11 engine records、projection records 和 ticker metadata；
- snapshot 在写入 DKVS 前使用当前钱包公钥加密；
- head 包含 wallet ID、sequence、state hash 和 operation ID；
- head 与 snapshot 通过同一 `dkvsManager` batch-CAS 原子写入目标节点；
- 恢复时先验证 head，再解密 snapshot，并检查 state hash、wallet ID、account index 和 engine build ID。

DKVS 只负责可靠保存和同步加密状态，不能替代 RGB11 资产验证。

### 8.2 保存模式

优先级为：

1. 当前钱包存在有效 DKVS AUTOPAY 委托时，使用可传播的付费保存；
2. AUTOPAY 不可用或查询失败，但当前 endpoint 明确启用 FREE_LOCAL 时，回退到临时保存；
3. 两种模式都不可用时，返回保存策略错误。

`FREE_LOCAL` 的含义必须明确：

- 只保存在当前 endpoint；
- 不通过 P2P relay；
- 不进入网络 PathMeta、checkpoint 或 snapshot；
- 只能从同一 endpoint 恢复；
- UI 不得把它显示为“全网备份”。

### 8.3 多设备和冲突

同一 RGB11 wallet 同一时间只支持一个 active writer。另一个设备可以读取和恢复，但在写入前必须同步到最新 head。

当两个设备基于同一旧 head 分别修改并提交时，后提交者会收到 head conflict、DKVS write conflict 或 stale generation。SDK 不自动合并两个 RGB11 状态；用户或应用必须选择最新有效状态并重新执行未提交操作。

## 9. 安全边界

RGB11 钱包集成依赖以下独立检查：

- RGB11 合约和 schema 验证；
- consignment 完整性和状态转换验证；
- seal 与 allocation proof 验证；
- Bitcoin 交易、outpoint、script 和确认数证据；
- 钱包私钥对 PSBT/Tapret carrier 的正确签名；
- DKVS record 身份、签名、sequence、PathGeneration 和费用证明；
- relay/ACK 与 transfer ID、recipient、txid/vout 的绑定。

任何一层验证失败，都不能通过其他层的索引结果或网络响应绕过。

当前实现不把一般化的发行方冻结能力定义为 RGB11 协议共识规则。可选 reject-list 或 policy adapter 只影响当前钱包是否接受某个状态；其具体治理和冻结语义需要由资产发行方案单独定义。

## 10. 当前测试覆盖

Wallet SDK 已包含真实本地三节点 E2E，覆盖：

- 固定地址 witness invoice；
- 独立 RequestID；
- RGB11 head + encrypted snapshot 原子保存；
- 同 endpoint 新设备恢复；
- FREE_LOCAL 跨 endpoint 隔离；
- AUTOPAY 查询失败回退 FREE_LOCAL；
- stale writer/head conflict；
- 非法 amount 和接收 mode；
- 既有 issue、transfer、proxy、address delivery、ACK 和 allocation 单元/集成测试。

这些测试使用本地 SatoshiNet bootstrap、core、miner 节点，不依赖公共测试网或外部 RGB regtest 服务。

Go 引擎仓库还保留冻结 Rust/Go differential vectors、官方 rc.11 parser round-trip，以及 `rgb-lib` 双向文件交换与 regtest 互操作证据。具体门禁和证据位置见 `UPSTREAM_MANIFEST.json` 与 `OFFICIAL_INTEROP.md`。

## 11. 主要 Wallet SDK API

常用入口包括：

```text
IssueRGB11Asset
ImportRGB11Contract / ImportRGB11ContractFile
CreateRGB11Invoice
PrepareRGB11Transfer
PrepareConfiguredRGB11AddressTransfer
DeliverAndBroadcastConfiguredRGB11AddressTransfer
AcceptRGB11Consignment
ValidateRGB11Consignment
RefreshRGB11State
GetRGB11State
GetRGB11AssetBalance
ListRGB11Outputs
SyncRGB11WalletState
RestoreLatestRGB11WalletState
ActivateRGB11WalletState
RebuildRGB11Locks
```

应用层应使用这些领域 API，不直接拼装 DKVS key、record、sequence、PathGeneration 或 RGB11 内部存储对象。
