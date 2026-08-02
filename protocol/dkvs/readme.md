# DKVS：SatoshiNet 分布式键值存储

DKVS（Distributed Key-Value Store）是 SatoshiNet 内置的、由数据所有者控制的小数据存储与同步层。它为钱包、账户恢复、RGB11 状态备份、邮箱、服务发现和应用配置提供统一的签名 record 模型。

DKVS 不是通用多主数据库，也不是 Bitcoin 或 SatoshiNet 的共识状态。它解决的是：**负责保存某条数据的节点，如何验证写入者、原子接受更新，并最终收敛到同一个有效状态。**

## 核心原则

1. 普通 path 只有一个 owner 或 authority。
2. `Seq` 管理单个 key 的版本，`PathGeneration` 管理整个 logical path 的变更顺序。
3. 写入通过 CAS 或 batch-CAS 提交；任一前置条件失败时不部分落库。
4. record 的 key、value、费用证明、时间、sequence 和 path generation 都由签名覆盖。
5. 网络数据通过 SatoshiNet 原生 P2P 传播；`FREE_LOCAL` 数据只属于接收节点。
6. Wallet SDK 只通过 `dkvsManager` 管理 transport、replica、同步、generation 和 outbox。
7. DKVS 不自动合并账户管理、RGB11 或其他领域状态；领域层必须定义自己的冲突策略。

## Key 与 logical path

DKVS key 使用路径格式：

```text
/<namespace>/<segments...>
```

当前主要 namespace：

| Namespace | 用途 | Logical path / 权限 |
| --- | --- | --- |
| `/personal/<account_id>/<module>/...` | 用户个人数据、账户管理、RGB11 head | 按 module 划分 owner-exclusive path；仅 account owner 可写 |
| `/blob/<account_id>/<blob_key>` | 加密快照或较大对象 | 完整 blob key 为独立 owner-exclusive path |
| `/mail/<receiver>/msg/<sender>/<msg_id>` | 离线消息 | sender 子 path 为 shared-append；receiver 可删除 |
| `/mail/<receiver>/share/...` | Guardian/share 数据 | receiver owner-exclusive |
| `/name/<name>` | 名称资料 | 当前 DID/NS authority 可写 |
| `/svc/<service>/...` | 服务配置与发现 | 当前 service authority 可写 |
| `/tmp/...` | relay、ACK 等短期数据 | local-only，必须设置受限 TTL |
| `/sys/...` | 系统参数 | 配置的 system signer 可写 |

`/personal/<account_id>` 下按 module 划分 path，例如账户管理和 RGB11 使用不同 path，避免无关业务共享同一个 generation 和写锁。

### PathMode

| Mode | 语义 |
| --- | --- |
| `owner_exclusive` | 由 account ID 等确定 owner；正常情况下只有一个 active writer |
| `authority_exclusive` | owner 由 DID、service 或 system authority 决定 |
| `shared_append` | 多个写入者只能创建各自唯一 key，不共享 mutable value |
| `local_only` | 仅当前 endpoint 保存，不参与网络同步和 PathMeta |

## DKVSRecord v1

每条 record 包含：

```text
Version
Key
Value
PubKey
Signature
Seq
PathGeneration
IssueTime
TTL
ExpiryHeight
FeeProof
Flags
```

### 大小限制

- 普通 value 最大 16 KiB。
- `/blob` value 最大 1 MiB。
- blob 是一条完整 record，不再使用 manifest/chunk 拆分协议。
- 一个 batch 最多 64 个 mutation，record 总编码大小最多 8 MiB。
- key 最大 256 字节，segment 最大 64 字节。

应用不应把 DKVS 当作通用文件存储。大文件应使用专门的数据分发系统，DKVS 只保存必要的小对象、加密快照或引用。

### Seq 与 PathGeneration

正常更新必须满足：

```text
new.Seq = current.Seq + 1
```

同一 path 的每次有效 mutation 使用连续的：

```text
new.PathGeneration = current_path_generation + 1
```

同一个 batch 内，record 按 canonical key 顺序分配连续 `PathGeneration`。远端节点从 owner 已签名的 record 中读取 generation，不能按本地接收次数重新计数。

### IssueTime 与确定性选择

Wallet SDK 使用节点返回的 `server_time_ms` 构造单调时间：

```text
IssueTime = max(server_time_ms, previous_issue_time + 1)
```

异常情况下同 key 出现多个候选时，选择顺序是：

1. 更大的 `Seq`；
2. 相同业务内容的 retention renewal；
3. 更大的 `IssueTime`；
4. `RecordHash` 字节序。

该规则保证最终确定性，但不承诺多设备并发修改的业务语义都被保留。

## PathMeta 与状态同步

网络可比较的 PathMeta 包含：

```text
Path
Generation
StateRoot
ActiveRecords
ActiveTotalSize
MinExpiryHeight
ViewHeight
```

`StateRoot` 是 path 当前有效 record 和 delete floor 的确定性摘要。它用于判断两个节点是否需要同步，不是链上承诺，也不是 Merkle membership proof。

比较规则：

1. generation 较小的一方需要同步；
2. generation 和 root 相同，path 已收敛；
3. generation 相同但 root 不同，执行完整 path reconciliation；
4. endpoint 的 generation 低于客户端已确认状态时，该 endpoint 被视为 stale，不能继续写入。

完整 path snapshot 会携带 PathMeta、有效 records、delete floors 和 `server_time_ms`。接收方必须完整验证并在一个本地 DB batch 中替换 confirmed state。

## CAS 与 batch-CAS

单 key CAS 至少绑定：

```text
signed_record
expected_path_generation
expected_record_hash 或 expect_absent
```

batch-CAS 用于同一个 owner 的多 key 原子提交，例如：

- 账户恢复包的 envelope、share、questions 和 manifest；
- RGB11 的 encrypted snapshot 与 wallet head；
- 应用需要同时更新的多个相关 key。

batch-CAS 的保证范围是接收 RPC 节点的本地数据库：

- 全部校验成功后一次提交；
- 任一 mutation 失败时 `applied=0`；
- 多 path 按 canonical 顺序加锁；
- 完全相同的 record/batch 重试是幂等成功；
- 只存在部分 record 时返回 conflict，不自动补齐剩余 mutation。

它不是跨节点线性一致事务，也不支持跨 owner 事务。

## 费用与保留策略

### AUTOPAY

`AUTOPAY` 是可跨节点传播的主要费用模式。节点读取 `autopay.tc` 合约状态，验证：

- 合约模板、服务名称、fee asset 和 recipient；
- signer 对应的委托地址；
- active delegate 状态；
- 每区块额度和余额；
- 当前 active record 数量是否超过容量。

容量按满尺寸 record 计算：

```text
max_records = floor(amount_per_block / full_record_fee_per_block)
```

### FREE_LOCAL

`FREE_LOCAL` 用于开发、临时缓存和明确的本节点备份：

- 必须带有效 FREE_LOCAL fee proof；
- 只写入当前 endpoint；
- 不通过 P2P relay；
- 不进入网络 PathMeta、checkpoint 或 path snapshot；
- TTL、记录数、字节数和 blob key 数受节点策略限制；
- 新设备只有连接到同一个 endpoint 才能恢复；
- 切换 endpoint 后不能把它显示为“网络备份”。

当前默认本地策略通常允许有限 TTL、每 signer 有界记录数和有界总字节数。主网是否允许 FREE_LOCAL 由节点策略决定。

### 其他 proof

`ONESHOT` 和 `LEASE` 已保留紧凑编码，但完整结算验证仍属于后续阶段。

## P2P 与 endpoint-local overlay

Relayable record 通过 SatoshiNet 原生 DKVS 消息传播。远端节点重新验证：

- key 和 namespace；
- owner/authority；
- 签名与 fee proof；
- sequence、PathGeneration 和 delete floor；
- 大小、TTL、expiry 和 quota。

当收到 generation gap 时，节点不能猜测中间状态，必须标记 path stale 并执行完整 path sync。

`FREE_LOCAL` 不进入网络 snapshot。Wallet SDK 在完成网络 path snapshot 后，会从同一 endpoint 读取 local-only records，并合并为 endpoint-scoped overlay。该 overlay 不参与网络 `StateRoot`。

## Wallet SDK 的 dkvsManager

领域模块不直接持有 DKVS transport。`dkvsManager` 统一负责：

- endpoint client 与 endpoint identity；
- per-path 锁和 readiness；
- confirmed replica 与 local-only overlay；
- sequence、PathGeneration 和单调 IssueTime；
- CAS/batch-CAS；
- exact signed batch outbox；
- path refresh、watch 和 change notification；
- typed error 映射。

写入流程：

```text
等待 path ready
→ 获取 per-path 锁
→ 读取 confirmed replica / PathMeta
→ 分配 seq 与 PathGeneration
→ 签名 exact record/batch
→ 保存 exact outbox
→ 提交 CAS/batch-CAS
→ 使用写响应更新 replica、PathMeta 和 outbox
→ 通知领域模块
```

重试必须复用完全相同的签名 bytes，不重新生成 sequence、generation、time 或签名。

稳定错误码包括：

```text
DKVS_WRITE_CONFLICT
DKVS_STALE_GENERATION
DKVS_STALE_ENDPOINT
DKVS_PERMISSION_DENIED
DKVS_INVALID_SEQUENCE
DKVS_PATH_DIVERGED
DKVS_LOCAL_ONLY_ENDPOINT_MISMATCH
DKVS_QUOTA_EXCEEDED
DKVS_RECORD_NOT_FOUND
```

调用方应使用 typed error 或稳定错误码，不应解析英文错误文本。

## 账户管理

账户管理使用 `/personal/<account_id>/account/...`：

- recovery package 使用四记录原子 batch；
- managed wallet state 使用加密 envelope 和单调 revision；
- 显式同步会先刷新远端 path；
- CAS 冲突、stale generation、path divergence 和 invalid sequence 使用有界重试；
- 钱包重命名、账户元数据和新增子账户由账户管理层按字段重放；
- 删除钱包属于 inventory mutation，会折叠同钱包更早的 metadata mutation；
- root wallet 不能删除；
- 错误 secret 或错误 root mnemonic 不能恢复状态。

这些字段级合并属于账户管理领域逻辑，不是 DKVS 的通用多主保证。

## RGB11

RGB11 使用独立的 `/personal/<account_id>/rgb11/...` 和 `/blob/<account_id>/...`：

- encrypted snapshot 与 wallet head 使用一个 batch-CAS；
- head 是单调 revision，并绑定 snapshot state hash 和 operation ID；
- 同 endpoint 的 FREE_LOCAL 备份可供新设备恢复；
- active AUTOPAY 可升级为 relayable backup；
- AUTOPAY 查询失败但节点支持 FREE_LOCAL 时，回退到临时备份；
- stale writer 必须返回 head conflict，不能覆盖较新的远端状态；
- RGB 资产有效性最终由客户端验证和 Bitcoin evidence 决定，DKVS 只保存加密状态和传输数据。

更多内容见 [RGB11 资产与 Wallet SDK](../rgb11/readme.md)。

## E2E 验收范围

Wallet SDK E2E 使用本地启动的 bootstrap、core 和 miner 节点，覆盖：

- AUTOPAY name owner rotation、mailbox append/tombstone 和三节点同步；
- FREE_LOCAL 同 endpoint 恢复与跨 endpoint 隔离；
- account recovery package 原子发布；
- account management 激活、恢复、边界条件和双设备字段级合并；
- RGB11 固定地址 invoice、encrypted backup、同 endpoint 恢复和 stale writer；
- CAS、PathGeneration、PathMeta、typed error 与 P2P 收敛。

连接已有公网测试网、消耗真实测试资产或修改公共网络状态的测试使用独立 build tag，不进入默认测试集合。

## 明确边界

DKVS v1 不提供：

- 任意多主 CRDT；
- 跨账户事务；
- 跨节点线性一致提交；
- quorum、BFT 或链上 commit certificate；
- FREE_LOCAL 跨 endpoint 恢复；
- 通用大文件存储；
- ONESHOT/LEASE 的完整结算实现；
- 自动理解并合并任意业务对象。

应用应把 DKVS 当作可验证、owner-controlled、最终一致的小数据层，而不是关系数据库或全局共识数据库。
