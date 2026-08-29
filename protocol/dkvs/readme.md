# DKVS：SatoshiNet 分布式键值存储

DKVS（Distributed Key-Value Store）是 SatoshiNet 内置的、由数据所有者控制的小数据存储与同步层。它为钱包、账户恢复、RGB11 加密备份、邮箱、服务发现和应用配置提供统一的签名 record 模型。

DKVS 不是通用多主数据库，也不是 Bitcoin 或 SatoshiNet 的共识状态。它解决的是：**服务节点如何验证写入者、原子接受更新，并让可传播数据通过节点间协议最终收敛；Wallet 如何维护当前服务节点的已确认本地副本。**

## 核心原则

1. key 表达稳定业务身份，不能表达实现或 schema 版本。
2. `Seq` 管理单个 key 的更新顺序，`ETag = RecordHash(record)` 管理单 key 并发。
3. Wallet 写入只使用 `ExpectAbsent` 或 `ExpectedETag`，不使用 path root、path generation 或 endpoint epoch。
4. batch-CAS 在一个服务节点内原子提交；任一 mutation 失败时不部分落库。
5. `FREE_LOCAL` 是费用模式和 endpoint-local 保留策略，不是第二套应用协议。
6. Wallet 对一个服务节点只维持一个聚合 prefix long-poll，并从本地 confirmed replica 读取已订阅数据。
7. `PathMeta`、`StateRoot`、network delete floor 和 path snapshot 只属于节点间 canonical 同步。
8. Wallet SDK 的 `dkvsManager` 是 transport、prefix registry、replica、cursor、outbox 和后台同步的唯一 owner。
9. DKVS 不理解或自动合并账户管理、RGB11 等领域对象；领域层必须定义自己的冲突策略。
10. 当前第一版直接使用最终协议和本地 schema，不保留双读、双写、legacy decoder 或版本化 key fallback。

## 稳定 key 与 namespace

DKVS key 使用路径格式：

```text
/<namespace>/<segments...>
```

主要 namespace：

| Namespace | 用途 | 写入权限 |
| --- | --- | --- |
| `/account/...` | 公开账户映射和账户资料 | 对应 account identity |
| `/personal/<account_id>/<application>/...` | 钱包、账户管理、RGB11 等私有业务数据 | account owner |
| `/blob/<account_id>/<blob_name>` | 加密快照或受限较大对象 | account owner |
| `/mail/<receiver>/msg/<sender>/<msg_id>` | 离线消息 | sender 创建，receiver 可删除 |
| `/mail/<receiver>/share/...` | Guardian/share 数据 | receiver 或协议指定 writer |
| `/name/<name>` | 名称资料 | 当前 DID/NS authority |
| `/svc/<service>/...` | 服务配置与发现 | 当前 service authority |
| `/tmp/...` | 临时应用数据 | 受限 TTL，按策略 local-only |
| `/sys/...` | 系统参数 | 配置的 system signer |

正确的 key 直接表达业务对象：

```text
/personal/<account_id>/wallet/catalog
/personal/<account_id>/wallet/settings
/mail/<account_id>/msg/<sender_id>/<msg_id>
/blob/<account_id>/<blob_name>
```

同一业务对象的数据结构升级继续使用同一个 key 和更高 `Seq`。只有外部协议版本本身就是业务身份、多个协议代际必须长期并存且由调用方明确选择时，版本才可以进入 key；此类例外必须显式审批、进入最小 allowlist 并有专门测试。

## 签名 record 与 ETag

DKVS 保持一套签名 record：

```text
Version
Key
Value
Seq
IssueHeight
TTL
FeeProof
Flags
PubKey / account identity
Signature
```

`ExpiryHeight` 由 record 的高度和 TTL 语义推导。`ETag` 定义为：

```text
ETag = RecordHash(record)
```

对已删除 key，ETag 是最新签名 tombstone 或服务端 effective delete floor 的 hash。

主要大小边界：

- 普通 value 最大 16 KiB；
- `/blob` value 最大 1 MiB；
- 一个 batch 最多 64 个 mutation，总 record 编码大小最多 8 MiB；
- key 最大 256 字节，单个 segment 最大 64 字节；
- subscription snapshot 另有 record 数量和总字节上限。

DKVS 不是通用文件存储。大文件应使用专门的数据分发系统；DKVS 优先保存小对象、加密快照、manifest、metadata 或稳定引用。

## 四个一致性边界

| 问题 | 机制 | 所属层 |
| --- | --- | --- |
| 单 key 并发 | `Seq` + `ETag` | Wallet 与服务节点 |
| Wallet 增量位置 | endpoint-scoped opaque cursor | Wallet subscription |
| FREE_LOCAL 归属 | 稳定 `EndpointID` | 当前服务节点 |
| 节点间 canonical 收敛 | `PathMeta` + `StateRoot` | SatoshiNet P2P 内部 |

这些机制分别解决不同问题。Wallet 请求不携带 `ExpectedPathRoot`、`ExpectedPathGeneration`、`ViewHeight` CAS 或 endpoint generation。

## 费用与存储模式

服务节点从 `FeeProof` 推导 `FREE_LOCAL`、`AUTOPAY` 或其他 paid mode。推导出的 `storage_mode` 可以出现在 API 响应中，但不是另一份持久化真相。

### AUTOPAY 与其他 paid mode

`AUTOPAY` 是主要的可传播存储模式。节点验证合约、服务名、fee asset、recipient、signer 对应委托、active delegate、每区块额度、余额和容量。通过验证的 canonical record 可以进入节点间复制。

### FREE_LOCAL

`FREE_LOCAL` 的严格语义是：

- 只属于当前 `EndpointID` 对应的存储实例；
- 单 endpoint、单写者；
- 必须带有效的 FREE_LOCAL fee proof；
- 受当前节点的 TTL、每 signer quota、节点总 quota 和 blob 限制；
- 不进入 P2P relay、canonical snapshot、checkpoint 或 anti-entropy；
- 不支持无损切换服务节点；
- UI 不得把它描述为全网备份或跨节点持久化。

允许的状态转换：

```text
不存在          -> FREE_LOCAL
不存在          -> AUTOPAY/PAID
FREE_LOCAL      -> FREE_LOCAL
FREE_LOCAL      -> AUTOPAY/PAID
AUTOPAY/PAID    -> AUTOPAY/PAID
```

禁止：

```text
AUTOPAY/PAID -> FREE_LOCAL
```

`FREE_LOCAL -> AUTOPAY/PAID` 不使用 promote API。Wallet 读取当前 `Seq/ETag`，构造 `Seq+1`、新 FeeProof 和新签名，然后执行普通 `Put(ExpectedETag)`；服务端在同一个 DB batch 中把该 key 切换为 canonical，并在提交成功后 relay。

## CRUD 与 key 级 CAS

最终 Wallet 应用 API 相对于现有 DKVS 基础路径为：

```text
GET  /config
GET  /record?key=...
GET  /key-state?key=...
POST /records/batch-cas
POST /subscriptions/snapshot
POST /subscriptions/watch
```

### Read

已订阅 prefix：

```text
Get(key)
-> 读取本地 confirmed replica
-> 按最后可信 ViewHeight 检查 expiry
-> 返回 value 与 freshness
```

未订阅 key 在线时直接从服务节点读取；离线时返回 unavailable。普通 `Get` 不会自动建立永久订阅。

### Put / Update

写入只携带：

```text
request_id
exact signed record
ExpectAbsent 或 ExpectedETag
EndpointID（batch 包含 FREE_LOCAL 时必须）
```

服务端验证当前 effective key state、precondition、连续 `Seq`、签名、namespace 权限、fee mode、TTL 和 quota，并原子提交 record 与 change commit。

写成功后 Wallet 可以立即幂等应用响应，但不能直接把 subscription cursor 跳到写响应返回的 cursor。后台同步仍从原 cursor 读取完整 commit 顺序，遇到相同 ETag 或 RequestID 时去重。

### Delete 与 recreate

Delete 是普通签名 tombstone Put：

```text
Flags = Tombstone
Value = empty
Seq = current floor + 1
ExpectedETag = current ETag
```

FREE_LOCAL delete 只保存 endpoint-local floor；canonical delete 进入节点间 delete floor。重新创建一个已删除 key 前，如果 Wallet 本地没有历史状态，应调用 `/key-state` 获取 `active / deleted / never_seen`、最新 `Seq` 和 ETag。

### Multi-key batch

一个 batch 可以包含同一逻辑 owner 的多个 key，每个 mutation 有独立 ETag precondition。所有 precondition、record、delete state、节点内部 PathMeta 和一个 change commit 在同一个服务端 DB batch 中提交；任一项失败时全部不生效。完全相同的 signed request 可以原样重放；只部分生效表示服务端原子性异常。

## Durable change log 与 opaque cursor

当前 endpoint 的每次有效视图变化都必须在同一事务中追加一个 change commit，包括：

- FREE_LOCAL 或 paid Put；
- 显式 Delete；
- TTL/retention expiry；
- FREE_LOCAL 通过普通 Put 切换为 AUTOPAY；
- 接收 P2P canonical 更新；
- P2P mirror/path snapshot 改变当前 endpoint effective view。

失败事务和真正 no-op 不写 change，也不唤醒 waiter。一个 multi-key batch 对应一个原子 commit。

外部 cursor 是 opaque token，绑定 `EndpointID`、revision、前一 token 和本次 commit history。客户端不能自行解释、构造或只保存裸 revision。以下情况返回 `RESET_REQUIRED` 或 `ENDPOINT_MISMATCH`：

- cursor 属于其他 endpoint；
- cursor 不存在、已 compact、超前或被篡改；
- 相同 revision 的 token 不匹配；
- 数据库恢复旧备份后形成了另一条 change history。

正常重启必须一起恢复 EndpointID、record state、change log 和 head token，因此原 cursor 可以继续使用。cursor reset 是正常恢复路径，Wallet 重新拉 snapshot 即可；不需要 endpoint epoch。

## 显式 prefix subscription

Wallet SDK 提供显式的 prefix 注册、取消、列举和状态查询。订阅列表持久化；Wallet 重启后自动恢复。访问某个 key 不会隐式永久订阅整个 path。

初次订阅或 reset 时，服务节点在同一 DB snapshot、read transaction 或一致性锁下读取：

```text
endpoint effective records
+ current change-log head cursor
```

因此 snapshot 前的变化已经进入 records，snapshot 后的变化一定出现在 cursor 之后，不存在 snapshot-to-watch 丢失窗口。Wallet 验证每条 record 的签名、key、identity、Seq 和 expiry，但不保存或验证 PathMeta、StateRoot、PathGeneration、EndpointPathState 或 local overlay。

一个终端对一个服务节点只保持一个聚合 long-poll，请求携带完整 prefix set 和一个 cursor。默认/建议边界：

```text
MaxPrefixesPerTerminal = 16
MaxPrefixLength        = 256
MaxChangesPerResponse  = 256
LongPollTimeout        = 60 seconds
ReconnectJitter        = 0-1 second
```

服务端使用 `topic -> waiter references` 索引，只唤醒受 mutation 影响的 topic；不能扫描全部终端，不能为每个 prefix 建立独立 long-poll，也不能为每个请求创建周期 ticker。waiter 注册后必须再次检查 backlog，以关闭“先查后等”的竞态窗口。

响应按原子 commit 分组。Wallet 对每个 commit 使用一个本地 DB batch 应用全部 key，最后写入 commit cursor，成功后才通知领域 observer。

## Wallet 本地副本与 outbox

`dkvsManager` 是唯一 DKVS 协调层。领域模块只通过逻辑 key 或领域 API 访问数据，不持有 DKVS client，也不自行实现 restore、冲突、远端同步或自动备份 worker。PWA JavaScript 不感知 DKVS transport。

本地副本只保存：

```text
dkvs:subscription-state
dkvs:subscription-prefix:<prefix>
dkvs:subscription-record:<key>
dkvs:subscription-key-state:<key>
dkvs:outbox:<request_id>
```

订阅状态为：

```text
SYNCING
READY
OFFLINE_READY
RESET_REQUIRED
ERROR
```

本地副本不保存 PathMeta、PathRoot、PathGeneration、network/local 两套 delete floor、EndpointGeneration、HasLocalOnly 或 path session 状态。当前第一版也不保留旧 schema fallback 或自动迁移分支；开发期旧 cache、replica、subscription state 和 outbox 可以直接清理重建。

durable outbox 以唯一 `RequestID` 为 key，保存 exact signed mutations、每 key precondition、状态、重试次数和错误。包含 FREE_LOCAL 的请求固定当前 EndpointID。网络超时后必须原样重放，不能修改旧 entry、重新签名或替换 precondition。conflict 后由领域层基于新 key state 重新计算，并创建新的 RequestID 和 signed mutation。

服务端 change log、Wallet replica 和 outbox 都是 durable data，应使用紧凑、确定性的二进制编码和严格 decode 校验。JSON 只用于 HTTP API、日志和人工诊断；除非有显式、已记录的兼容要求，不能把 API JSON 直接作为持久化格式。

## 离线读取与服务节点切换

本地 subscription state 保存最后可信 `ViewHeight`：

- 最后可信高度已经达到 expiry 时隐藏 record；
- 无法确认离线期间链高度时返回 `offline_last_known` freshness；
- 不根据墙钟时间伪造区块高度；
- 离线可读只表示最后确认状态可用，不表示网络当前最新。

切换服务节点前，Wallet 必须扫描 active FREE_LOCAL records 和 FREE_LOCAL pending outbox。需要保留的数据先通过普通 AUTOPAY Put 转为 canonical，并等待写成功、outbox 清空和当前 subscription 观察到相同 ETag。

连接新 endpoint 时：

```text
获取新的 EndpointID
-> 旧 cursor 自然失效
-> 对全部显式 prefix 拉取新 snapshot
-> 原子安装新 replica 与 cursor
-> 完成切换
```

新 snapshot 完成前，旧 replica 最多以 `offline_last_known` 使用，不能标记为新 endpoint 的 READY 数据。

## 节点间 P2P 边界

节点内部继续保留：

```text
canonical PathMeta / StateRoot
network tombstone / delete floor
trusted PathSnapshot
Notify / Inv / Get / Data
anti-entropy
普通节点的订阅范围
Miner 的完整 canonical 数据
```

Wallet change log 是当前 endpoint 的业务视图增量，不替代 P2P canonical root。P2P 小范围变化可以生成普通 change commit；大范围替换可以生成 `RESET_PREFIX`。canonical snapshot 或 mirror 不能删除 endpoint-local FREE_LOCAL keyspace，也不能把完整 PathMeta/snapshot 结构下发给 Wallet。

## 领域层边界

### 账户管理

账户管理使用稳定的 `/personal/<account_id>/account/...` key。恢复包和相关对象可以通过 multi-key batch 原子提交。多设备字段级合并、钱包 inventory、root wallet 保护和恢复策略属于账户管理领域逻辑，不是 DKVS 的通用多主保证。

### RGB11

RGB11 使用独立的 `/personal/<account_id>/rgb11/...` 和 `/blob/<account_id>/...` key：

- encrypted snapshot 与 wallet head 使用一个 key-ETag batch-CAS；
- head 绑定单调业务 revision、snapshot state hash 和 operation ID；
- FREE_LOCAL 只支持同 endpoint 恢复；
- 需要跨节点持久化时通过普通 AUTOPAY Put 更新；
- stale writer 收到 head 或 DKVS write conflict，不能覆盖较新状态；
- RGB 资产有效性仍由客户端验证和 Bitcoin evidence 决定。

更多内容见 [RGB11 资产与 Wallet SDK](../rgb11/readme.md)。

## 容量目标与验收

第一版目标是单服务节点至少支持 10,000 个实时在线终端，前提是主要订阅私有 prefix。平均每终端 4–8 个 prefix 时，仍然只有 10,000 个 active long-poll，而不是按 prefix 放大连接数。公共热门 prefix 和无界大 Blob 不属于本阶段容量 SLA，需要后续独立热点分发策略。

10,000 终端能力是验收目标，不是仅凭 goroutine 数量即可声明的性质。发布前至少需要：

- 100、1,000、5,000、10,000 终端逐级测试；
- 10,000 终端、平均 5 个 prefix、60 秒 long-poll 持续 30–60 分钟；
- 空闲请求频率接近 `10,000 / 60 ≈ 167 RPS`，不随 prefix 数线性增长；
- 1,000 个私有 prefix 短时更新时 P99 通知延迟目标小于 2 秒；
- timeout/cancel、重启和 compaction 后 waiter、FD、goroutine、heap、topic reference 无泄漏；
- race detector、故障注入和真实目标硬件的 CPU、RSS、DB IOPS、网络余量验证。

## 稳定错误码

Wallet 应按 typed error 或稳定错误码处理，不解析英文文本。主要应用错误包括：

```text
DKVS_WRITE_CONFLICT
DKVS_ENDPOINT_MISMATCH
DKVS_RESET_REQUIRED
DKVS_PERMISSION_DENIED
DKVS_INVALID_SEQUENCE
DKVS_LOCAL_ONLY_ENDPOINT_MISMATCH
DKVS_STORAGE_MODE_DOWNGRADE
DKVS_QUOTA_EXCEEDED
DKVS_RECORD_NOT_FOUND
```

节点内部同步仍可能使用 stale generation、path divergence 等错误，但这些不是 Wallet CRUD 的写前置条件。

## 明确边界

DKVS 第一版不提供：

- 任意多主 CRDT；
- 跨账户事务；
- 跨节点线性一致提交；
- quorum、BFT 或链上 commit certificate；
- FREE_LOCAL 跨 endpoint 恢复；
- PAID/AUTOPAY 到 FREE_LOCAL 的降级；
- promote API 或 endpoint epoch；
- 通用大文件存储；
- 公共热门 prefix 的 10,000 终端 fan-out SLA；
- 自动理解和合并任意业务对象；
- 旧 Wallet PathMeta 协议、旧本地 schema 或版本化 key 兼容层。

应用应把 DKVS 当作可验证、owner-controlled、最终一致的小数据层，而不是关系数据库或全局共识数据库。
