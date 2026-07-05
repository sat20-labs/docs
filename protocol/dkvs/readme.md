# DKVS 技术白皮书

DKVS（Distributed Key-Value Store）是 SatoshiNet 内置的分布式小数据存储层。它面向钱包、DApp、本地 Agent、D-Indexer 和节点协作场景，提供可签名、可同步、可按 key 权限验证的 record 存储能力。

DKVS 不替代 Bitcoin L1，也不把任意链外数据变成共识状态。它的目标是让 SatoshiNet 节点在不引入 libp2p 或外部 DHT 依赖的前提下，用原生 P2P 消息同步小型、可验证的数据记录。

## 设计目标

1. 为用户、名称、服务、邮箱、blob manifest、临时数据和系统数据提供统一 key-value 数据模型。
2. 每条 record 自带 pubkey、签名、TTL、expiry height、seq、fee proof 和 tombstone 标记。
3. 节点接收本地 REST 写入或 P2P 数据时，都必须重新验证 key、签名、TTL、权限、fee proof、hash 和选择规则。
4. miner 之间使用 SatoshiNet 原生 wire 消息同步，不使用 libp2p、Kademlia 或旧 L1 DKVS 网络层。
5. 当前阶段优先保证保存某条 record 的节点在更新后收敛；长期可演进为 core node 全量保存、普通节点订阅、再到按 DHT 分组保存。

## Key Namespace

DKVS key 使用路径形式：

```text
/<namespace>/<segments...>
```

当前 namespace 包括：

| Namespace | 用途 | 写入权限 |
| --- | --- | --- |
| `/personal/<account_id>/...` | 用户个人数据 | `sha256(pubkey)==account_id` |
| `/name/<name_id>` | 名称级资料 | L1 Ordinals DID/NS owner 的当前 signing key 或 owner address |
| `/svc/<service>/...` | 服务配置和服务发现 | service resolver 返回的当前 signing key 或 owner address |
| `/mail/<mailbox>/msg/<msg_id>` | 离线消息 | 任意有效 signer 可投递，quota 后续阶段实现 |
| `/mail/<mailbox>/share/<package>/<share>` | Guardian/share 数据 | mailbox owner 写入 |
| `/blob/<object>/manifest` 和 `/blob/<object>/chunk/<n>` | 小 blob 分片 | record signer 负责完整性，SDK 校验 manifest/chunk |
| `/tmp/...` | 临时数据 | TTL 受限 |
| `/sys/...` | 系统参数、miner/pool 元数据等系统数据 | 只允许配置的 system signer |

segment 字符集限制为 `[a-z0-9._-]`，并有长度限制。DKVS-safe name 原样作为 `name_id`；不安全 canonical name 使用 `hex(sha256(canonical_name))`。

## Record 与选择规则

同一个 key 当前只保存一个 active candidate，不保存多版本历史。

如果同 key 已有 record 且 pubkey 不变，DKVS 默认认为 signer 沿用现有 owner，不重复 resolve DID。若 indexer 本地通知 name 已转移，或新 record pubkey 变化，则下次写入必须重新 resolve 当前 owner。

选择规则为：

1. 当前权限失效的旧 record 不能阻止新 owner 写入。
2. 旧 record 当前仍有效时，按 `seq -> expiry_height -> hash/bytes` 比较。
3. tombstone 是同 key 的删除 record；权限仍按 key owner 校验。
4. Get/List/Sync/Checkpoint 只返回未过期且当前权限仍有效的 active record。

## DID / Name Resolver

DKVS core 通过 `DIDResolver` 接口接入真实 DID/NS 数据。当前推荐的生产路径是 L1 indexer NS API：

```text
GET /ns/name/:name
GET /ns/address/:address
```

`/ns/name/:name` 返回当前 owner address。DKVS 从 record pubkey 派生 p2tr 地址，并要求它等于当前 owner address。name 随 UTXO 转移时，L1 indexer 可以在本地调用 SatoshiNet indexer 的 `NotifyDKVSNameTransfers(names)`，提示 DKVS 标记这些 name 下次写入必须重新 resolve。

没有配置 resolver 时，`/name` 和 `/svc` 默认不可写，避免主网误开放权限。

## Fee Proof 与保存费用

每条 DKVS record 可以携带 `fee_proof`，证明该 record 的保存费用已经被某种支付或授权机制覆盖。fee proof 不参与共识交易语义；它是 DKVS 写入验证的一部分，节点在本地 REST 写入、P2P `dkvsdata` 接收和启动同步落库时都要重新验证。

fee proof 当前是 JSON 结构，核心字段包括：

| 字段 | 含义 |
| --- | --- |
| `mode` | 支付模式，当前支持 `AUTOPAY`、`FREE_LOCAL`、`ONESHOT`、`LEASE` |
| `pool_contract` | DKVS Pool 或 AUTOPAY 合约地址 |
| `payer` | 付款人地址；AUTOPAY 中要求等于 record pubkey 派生的 p2tr 地址 |
| `payer_pubkey` | 可选 payer 公钥；提供时必须能派生出 `payer` |
| `key_hash` | `sha256(key)` / DKVS key hash，绑定 proof 与 key |
| `record_hash` | `FeeAnchorHash(record)`，绑定 proof 与 record 内容；计算时排除 record signature、proof 内的 `record_hash` 和 `proof_signature`，避免自引用 |
| `record_size` | proof 覆盖的 record size；AUTOPAY 按 full-size record 计费 |
| `expiry_height` | proof 覆盖到的 expiry height |
| `namespace` | key namespace，必须与 key 实际 namespace 一致 |
| `proof_signature` | 可选 payer 对 fee proof 规范字段的签名；主网默认要求开启 |

当前支持四种 mode：

| Mode | 当前用途 | 主网边界 |
| --- | --- | --- |
| `AUTOPAY` | 当前推荐模式。用户提供 `autopay.tc` template 合约地址，节点读取合约 state 判断该 payer 有多少 record 容量。 | 主网参数未最终确定前不默认放行。 |
| `FREE_LOCAL` | 本地测试、开发或白名单策略。 | 主网默认不接受；过期后可物理删除。 |
| `ONESHOT` | 一次性支付 proof 的预留格式，包含 `payment_txid`、`paid_amount`。 | 当前只做 JSON 字段级校验，真实 DKVS Pool 支付校验待实现。 |
| `LEASE` | 租约/套餐式支付 proof 的预留格式，包含 `lease_contract`、`plan_id`。 | 当前只做 JSON 字段级校验，真实租约合约校验待实现。 |

### AUTOPAY 验证

AUTOPAY 是当前可落地的 fee proof 方案。用户提交 record 时提供 `autopay.tc` template 合约地址；节点读取该合约 state，并验证：

1. 合约是 `autopay.tc` template。
2. 合约状态为 active 且未 closed。
3. deployer 是写 record 的 payer。
4. `payer_pubkey` 若存在，必须能派生出 `payer` p2tr 地址。
5. record pubkey 必须等于 `payer_pubkey`，且派生出的 p2tr 地址必须等于 `payer`。
6. recipient、fee asset、end height 与 DKVS 策略匹配。
7. 每区块支付金额可覆盖该 AUTOPAY 合约当前持有的 full-size active record 数量。

容量按满负荷 record 计算：

```text
max_records = floor(amount_per_block / full_record_fee_per_block)
```

如果合约 state 使用 fixed schedule，`amount_per_block = base_amount`。如果使用 linear schedule，`amount_per_block = base_amount + step_amount * max(0, current_block - active_height - 1)`。

测试网可以内置一套默认 DKVS AUTOPAY 策略，用固定 deployer、recipient、fee asset、base amount 和 full-record fee 计算默认合约地址；这些默认值本身不授权写入，仍必须读到 live 且 active 的合约 state。主网在真实合约参数、recipient 和收益规则最终确定前，不启用免费写入，也不凭默认值放行。

### DKVS Pool 与挖矿收益

DKVS 保存费用最终应合并到挖矿收益中。目标设计是由 DKVS Pool 合约在每个区块自动发出一笔 result tx，该 result tx 的 fee 就是当前区块应支付给 miner 的全部 record 保存费用。这样 DKVS core 只负责验证 record 是否被有效 fee proof 覆盖，不在 P2P 同步层单独计算或分配收益。

当前 DKVS Pool 合约尚未实现，AUTOPAY verifier 只验证合约状态和 record 容量是否覆盖，不代表最终收益分配已经完成。主网费用策略需要等 DKVS Pool 合约、result tx 格式和收益结算规则确定后再启用。

## 保存与过期清理

DKVS 区分 active 视图和物理保存：

- active record 才会被 `GET`、prefix list、sync、checkpoint 和 snapshot 返回；
- TTL 或 `expiry_height` 到期后，record 不再属于 active 视图；
- 之前已经缴费过的 record，第一版暂时物理永久保存，便于后续续费、审计或恢复；
- 免费 record，包括本地 `FREE_LOCAL` 或无 fee proof 但被本地策略接受的 record，过期后可以被物理删除。

节点实现需要在 DKVS 模块中提供定时清理机制，低频扫描并删除过期免费 record。当前实现还会在区块处理路径中周期性触发同一套清理逻辑；这不改变 wire 协议，也不影响付费 record 的物理保留。

## P2P 同步

DKVS 使用 6 个 SatoshiNet 原生 wire command：

| Command | 用途 |
| --- | --- |
| `dkvsnotify` | 通知 record hash/key 更新 |
| `dkvsinv` | 广播 record inventory |
| `dkvsget` | 按 key/hash 拉取 record |
| `dkvsdata` | 返回 record 数据 |
| `dkvssyncreq` | 分页启动同步请求 |
| `dkvssyncres` | 分页同步响应 |

miner 新连接后执行分页同步；收到 notify 后用 get/data 拉取缺失 record。接收端必须完整重新验证，不能信任远端节点。

## Checkpoint

DKVS checkpoint 是本地 active record 集的 Merkle root，用于快速比较节点视图和导出 snapshot。它不是链上共识根。

它解决的是“两个节点当前 DKVS active 视图是否一致”的问题：sync response 可以携带 checkpoint root，接收方同步后重新计算本地 root，如果不一致就知道需要继续分页拉取、重新同步或告警。checkpoint 不保存私钥，不需要签名，不证明全网所有历史数据都永久存在，也不自动产生链上交易。当前设计不把 checkpoint 发布为 DKVS record；SatoshiNet indexer 本身不持有 checkpoint 签名私钥。

当前已删除 checkpoint 签名与链上 anchor 方案。原因是完整 DKVS 数据长期不会由所有节点永久保存：未来可能只由 core node 保存全量，普通节点按订阅保存，规模扩大后还可能按 DHT 分组保存。强制全局 anchor 会带来高计算成本和错误安全感。更合理的长期目标是：某条 record 更新后，所有负责保存该 record 的节点最终收敛。

## 当前边界

当前阶段不包含普通节点开放订阅市场、mailbox quota、blob 大对象 SDK、DKVS Pool 合约/result tx 收益结算、checkpoint 链上锚定和 DHT 分组存储。这些属于后续协议阶段。
