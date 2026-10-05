# DKVS：SatoshiNet 分布式键值存储

> 更新：2026-10-05。本文说明 DKVS 的数据模型、写入授权、同步协议和 SDK 集成边界。

DKVS 是由数据所有者控制的小数据存储与同步层，用于账户管理、加密备份和应用配置。它提供一个服务节点内的原子写入，以及网络可见数据的最终收敛，不提供跨节点线性一致或任意多主合并。

## 核心原则

1. key 表达稳定业务身份；数据结构升级不另造版本化 key。
2. `Seq` 只排序一个 key 当前生命周期的更新，`ETag = RecordHash(record)` 用于精确 CAS。
3. 删除物理移除当前记录；不保存持久 tombstone、delete floor 或 mutation log。
4. generation 只属于当前 endpoint 和 collection，用于 Wallet 同步及写入授权；P2P 不传播 generation。
5. Wallet 新写入同时验证 CAS、当前 binding、请求签名和本 endpoint 的 prefix generation。
6. `FREE_LOCAL` 是 endpoint-local 费用与保留策略，不是跨节点备份。
7. SDK 的 `dkvsManager` 统一管理 client、订阅、副本、outbox 和后台同步；PWA 使用领域级 WASM API。
8. 未发布功能不保留旧协议兼容、双写或迁移路径。

## 稳定 key 与权限

| Namespace | 用途与权限 | 放置 / 复制边界 |
| --- | --- | --- |
| `/account/<network>/<root-address>` | root 签名的账户服务 binding | 网络复制控制记录 |
| `/personal/<account>/<module>/...` | account owner 的私有业务数据 | FREE_LOCAL 或网络存储 |
| `/blob/<account>/<blob-key>` | owner 的加密大对象 | FREE_LOCAL 或网络存储 |
| `/name/<did>` | 当前 DID owner 的资料 | 网络存储 |
| `/svc/<did>/...` | 当前 DID owner 的服务配置 | 网络存储 |
| `/mail/<account>/...` | MessageManager / owner 管理的邮箱 | 当前绑定 CoreNode，AccountBound |
| `/topic/...` | Topic 服务状态 | 服务策略 / 协议定义 |
| `/sys/...` | SystemVerifier 授权的系统记录 | 网络存储 |
| `/tmp/...` | signer 与本地策略约束的临时数据 | LocalOnly |

当前 root 签名的 AccountServiceDescriptor binding record 是绑定事实，包含 AccountID、CoreNodeID 和能力信息。Wallet 普通写入必须由当前绑定的 CoreNode 接受；binding 的独立创建是受校验的引导例外。

Collection 是同步、endpoint-local generation 和当前集合 root 的范围。不同 key 的 Seq、不同 endpoint 的 generation 不可互相比大小来判断全网新旧。

## Record、删除与重建

签名 record 包含 `Version / Key / Value / Seq / IssueHeight / TTL / FeeProof / Flags / PubKey 或 account identity / Signature`。

- 初次创建使用 `Seq = 1`；更新使用当前 Seq + 1，并匹配当前 ETag。
- 删除命令使用 `FlagTombstone`、当前 Seq + 1，Value 签名绑定被删除记录的 RecordHash，并满足精确 CAS。
- 删除成功后移除 record、hash index 和该 key 的最新 change-generation 索引；snapshot 不包含删除命令。
- 删除后的 key 按不存在处理，重建从 `Seq = 1` 开始；历史高 Seq 不是新生命周期的下限。
- `TTL > 0` 时 expiry height 为 IssueHeight + TTL；`TTL = 0` 的保留由 paid policy 等决定。
- 新 Wallet RPC 写入要求 `currentHeight - 2 <= IssueHeight <= currentHeight`；此短窗口不用于拒绝 P2P 中旧但仍有效的当前记录。

普通 value、blob、batch、分页和完整副本分别有容量上限。DKVS 用于受限对象和引用，不承诺通用大文件存储。

SDK Blob 编解码使用统一的 `DKB1 + uint32(metadata length) + metadata + data` 格式；长度字段为大端，metadata 可以为空，data 必须非空。固定封装占 8 字节，包含在 Blob value 容量上限内；data 始终保持原始字节，不做隐式压缩。解码不猜测未封装内容，也不自动迁移或改写已有原始 value；直接 record API 仍返回原始存储字节。

## Wallet API 与写入授权

当前应用接口：

```text
GET  /v3/dkvs/config
GET  /v3/dkvs/record?key=...
GET  /v3/dkvs/key-state?key=...
POST /v3/dkvs/records/batch-cas
POST /v3/dkvs/active/sync
POST /v3/dkvs/active/watch
POST /v3/dkvs/prefixes/read
```

`/checkpoint`、`/snapshot` 和节点 `/subscriptions` 是 node-local 管理入口，不是 PWA managed replica 的兼容协议。不存在独立 `/write-context` 接口；SDK 从已完成同步的 metadata 获取写入上下文。

写入请求包含 RequestID、EndpointID、有序 mutations、每 key 的 `ExpectAbsent` 或 `ExpectedETag`，以及对 endpoint、prefix generations、RequestID、record hashes 和 CAS 条件的 wallet request signature。record signature 证明作者；request signature 证明这一次写入授权，不能由复制历史 record 替代。

服务端验证当前 binding、generation、精确 CAS、Seq、签名、权限、费用和 quota，并在提交前确认付款和容量校验仍适用于当前本地高度与策略。条件变化时重新验证原始授权请求；任一 mutation 失败时不部分提交，全部变更通过同一个提交锁和 DB batch 原子提交。

`STALE_GENERATION / WRITE_CONFLICT / INVALID_SEQUENCE` 后，领域层需要同步当前状态并重新构建新的业务请求。网络结果未知时，outbox 只能重放原始完整签名请求，不能给历史请求换 generation、重新授权或替换 CAS 条件。明确 record TTL 过期返回 `DKVS_EXPIRED_RECORD`，SDK 清理已拒绝的过期 outbox，不改变原 TTL、签名高度或授权。

## Active sync / watch 与 confirmed replica

SDK 显式注册 managed prefixes，持久化后在重启时恢复。普通 Get 不隐式永久订阅；已订阅数据从 confirmed replica 读取，未订阅数据每次按需在线读取，不保留短期读取缓存。按需读取与显式权威读取共用一次 5 秒截止时间，覆盖本次需要的配置、key-state、record、目录分页与校验高度查询；各步骤不重新计时。Active sync 的配置与分页同样沿用调用方 context，取消后不安装结果。managed 持久副本支持读取最后已确认的离线状态。

一个 ActiveScope 表示 collection，也可收窄为指定 keys。metadata 包含 `EndpointID / scope / generation / root / ViewHeight`。

- full sync 返回当前集合；分页固定 generation、root 和校验高度。服务端当前集合变化导致 cursor 失效，客户端重新读取。
- incremental sync 只返回上次 generation 之后变化、且仍当前存在的记录；它不是事件历史。
- 删除不返回历史 tombstone。SDK 合并候选记录后验证当前 root；增量无法解释删除时转 full sync。
- 只有完整结果通过校验，才原子安装 records 与同步 metadata；写入 ACK 不直接推进已完成同步位置。
- Wallet 本地安装有并发基线检查；outbox 与 confirmed records 分开保存。
- 一个终端使用一个聚合 long-poll；当前默认最多 16 个 prefixes、单页最多 256 条、Watch 超时 20 秒。每次至多返回一个变化 scope 的当前 page。
- 服务端不保存终端持久 session、离线事件队列或 mutation log；慢消费者重新读取当前状态。

SDK 保存已确认 records、managed prefixes、endpoint-local 同步 metadata、每 prefix 的 ACK 高水位和原始请求 outbox。不保存 P2P source ownership、删除历史或可跨节点比较的版本表。

发送与接收分别返回结果。发送冲突、原签名高度失效、资金暂停及临时网络失败不阻断通过同 endpoint 校验的接收 sync / Watch。冲突请求保留原授权与提示、停止自动提交；临时网络失败通过既有 5 秒间隔重试原授权，其间 Watch 继续接收。接收自身的来源和基线校验仍须通过。明确的存储降级、配额和结构化请求拒绝以业务错误返回，保留原请求和拒绝信息、停止自动提交；HTTP 429 等临时失败保持原请求重试。传输协调器在操作返回或 panic 时均释放占用并唤醒等待者，本地不可恢复错误保留 fail-fast。

账户后台任务和 mailbox 维护的错误独立保留并向调用方返回，不阻断通过自身校验的 managed 接收。失败任务保留待处理，其余任务继续执行，已确认变更的通知不会被一次业务拒绝阻塞。已完成的 Watch 页面若落后于并发前台写入的 ACK，SDK 丢弃旧页面，通过已有有界同步流程重新读取当前状态；新响应仍须通过 endpoint、ACK 下界、root 和安装基线校验。

离线副本只代表最后已确认状态，不能证明网络当前最新；没有可信高度时不能根据墙钟推造链高度。连接不同 EndpointID 不会自动取得覆盖旧副本的授权。当前 SDK 阻止直接切换；有有效 FREE_LOCAL 或其 pending outbox 时返回 local-only endpoint mismatch，否则仍需显式来源 / 基线决策。

同 endpoint、同一组已完整同步目录的刷新不会撤销确认副本的读取资格；网络刷新失败后可读取 OFFLINE_READY 副本，成功刷新恢复 READY。首次同步、未完成同步或新增目录不能借此取得离线读取资格，写入仍须通过原有在线授权与 CAS 校验。完整同步或 Watch 的目录 ViewHeight 只推进已知 endpoint 校验高度，不以迟到页面降低其他目录的过期校验高度；主动 best-height 查询仍可以确认真实链回退。

从显式选择的恢复节点或其他按需来源读取记录时，使用该来源的当前高度校验本次结果，不修改 managed replica 的校验高度。刷新共享校验高度前，已知 EndpointID 必须与持久副本来源一致；存储估算等读取不能把另一来源的策略与本地副本高度混用。同来源在线刷新暂时失败时可以沿用已有可信高度，网络失败不能解除来源一致性要求。来源不一致时返回 endpoint mismatch，保留原副本及其高度。

Get、目录列表、就绪检查和使用本地状态的写入 builder 采用同一确认边界：所有已注册或待同步目录均已完成同步，且 client 已知的 EndpointID 与副本来源一致。已知另一来源时返回 endpoint mismatch，保留原副本；同一 EndpointID 的 URL 别名可以共用副本。client 尚未确认来源时，可以读取最后确认的离线视图，其来源仍为副本持久化的 EndpointID，不归属给未知端点。

重建 DKVS Manager 后，合格确认副本以已持久化的 ViewHeight 恢复尚未知的校验高度，零高度也属于已知高度。已取得的在线高度优先；Get 与目录列表执行一致的签名和 TTL 校验。这个离线边界只描述最后确认视图，不表示最新链高。

账户 managed-data 确认等待只观察本地已确认 state/blob，验证签名、TTL、profile 内容及数据版本/摘要关系，未就绪时唤醒已有 DKVS 同步 worker。等待本身不发起或等待同步 HTTP。调用方 context 控制整个等待，包括根钱包暂不可用的阶段；未指定 deadline 时，整个调用使用一次 30 秒默认截止时间。取消等待不取消共享接收 worker；worker 需由现有生命周期启动。

## 费用与放置边界

`FREE_LOCAL` 要求有效 fee proof、有限 TTL，并受 signer / node quota 限制；仅当前 endpoint 可用，不进入 P2P 或 network snapshot。通过普通 Seq + 1、CAS、新 AUTOPAY proof 与签名可以升级为 paid；paid 不能降级为 FREE_LOCAL。

`AUTOPAY / PAID` 由 FeeVerifier 和合约状态判断当前可用性与保留。网络可见记录参与 P2P；停付后的 grace 是本地 retention 行为，不形成删除历史。需要资金时不应将付费数据自动改成 FREE_LOCAL；SDK 保留原始待充值 outbox 与提示，同时继续接收订阅更新。

network snapshot 的缺项不提前删除本地 AUTOPAY grace 缓存；该缓存继续不参与 network root 和 relay。同 key 的合法当前记录仍可替换缓存，grace 到期由现有 retention 清理删除。

付款恢复后，旧的过期判断不能删除该记录。成功写入或同名重建的当前记录与付款校验一起发布；并发维护只更新仍对应当前记录的结果，不能清除新记录的有效网络同步资格。

AccountBound mailbox 放置在账户当前绑定的 CoreNode。消息 append / delete 通过 MessageManager 管理，普通 DKVS PUT 不能绕过消息协议。

## 节点 P2P 同步

P2P 传递签名 operation 和当前集合 snapshot，不传递 Wallet generation。source 资格来自有效 CoreNode / Bootstrap 身份与配置；source 只固定在一次同步 session 内，不持久化成 collection ownership。

当前同步流程：

```text
连接有效 source → 签名分页提取目录线索（不暂存完整 records）→ 与本地目录合并、节点级去重队列
→ 同时只有一个 source/session 下载目录 snapshot
→ 同步期间有效来源的 Notify 进入节点内存队列
→ 所有目录安装成功 → 按到达顺序处理缓存 Notify
→ 在同一入队锁内检查队列为空并设置节点 READY
```

READY 属于整个节点，单个 peer 或目录完成不能提前开放通知处理。失败或断连保留未完成目录；Notify 缓存有数量 / 字节上限，溢出要求重新同步。

非矿工连接的持续 Notify 订阅由完成的目录发现/订阅声明确定。单个目录 snapshot 只控制本次服务范围，不修改持续订阅；首次单独请求目录也不建立持久订阅。服务期间临时范围可接收 Notify，完成、取消或超时释放后仅保留已声明的持续订阅。矿工连接和 `/account` binding 通知按路由规则放行。发现响应校验失败时拒绝页面、保留未完成任务，并进入已有同步调度和换源流程。

source 在目录 session 的首个请求捕获一次独立 snapshot，之后所有页读取它。链高度前进或新的写入不改变该 snapshot；接收端安装后处理缓存 Notify。ViewHeight 只保留为创建时的记录有效性校验高度，不是逐页与当前链高度比较的分页条件。接收端另按本地当前高度验证付款资格，并在安装前确认该校验仍适用，不改变 source 的快照边界。每连接最多保留一个目录 snapshot，records 上限 64 MiB；完成、取消、断连或闲置 2 分钟释放。

同一活动 session、相同 filters 的第一页重发复用已捕获 snapshot，不能借重发改变订阅范围。接收端忽略同 session 中与前一已验签页内容和签名完全一致的重复响应，不重复安装或取消下一页超时；不同内容、错误签名及其他 session 仍按现有校验处理。连接按顺序处理和发送消息，接收端只保留前一已接收响应的摘要，不保存页历史。

完整安装验证 root、source signature、scope、记录权限 / fee 和接收端并发基线。每个待响应页在同一源共尝试两次（每次超时 10 秒），仍超时后交回现有连接选择，优先其他有效源；没有替代源时继续原源。未完成目录保留，连接不因 DKVS 超时关闭。目录发现只提供路径线索，不要求各页的全局 root 相同，不据此直接安装或删除 KV。单个目录的完整校验不变；新目录可能由 Notify 或下一轮 anti-entropy 补齐。发现消息携带 records，但接收端仅从中提取目录路径，不直接安装发现页中的记录。

## 领域集成边界

账户管理定义恢复包、root 保护、多设备冲突策略和钱包 inventory；RGB11 定义 encrypted snapshot / head、业务 revision 和资产证据验证。这些领域通过 SDK 协调层读写，不能把 DKVS 最终一致误当作领域对象的自动合并或资产有效性证明。

Wallet-independent primitives、codecs、replica 与 outbox 位于 `sdk/wallet/dkvs`；Manager 生命周期、endpoint 选择和领域适配位于父包 `wallet`。PWA 调用领域级 WASM API，不自行维护 DKVS transport。

RGB11 资产验证与备份边界见 [RGB11 资产与 Wallet SDK](../rgb11/readme.md)。
