# DKVS 技术白皮书

DKVS（Distributed Key-Value Store）是 SatoshiNet 内置的分布式小数据存储层。它面向钱包、DApp、本地 Agent、D-Indexer 和节点协作场景，提供可签名、可同步、可按 key 权限验证的 record 存储能力。

DKVS 不替代 Bitcoin L1，也不把任意链外数据变成共识状态。它的目标是让 SatoshiNet 节点在不引入 libp2p 或外部 DHT 依赖的前提下，用原生 P2P 消息同步小型、可验证的数据记录。

## 设计目标

1. 为用户、名称、服务、邮箱、blob manifest、临时数据和系统数据提供统一 key-value 数据模型。
2. 每条 record 自带 pubkey、签名、TTL、expiry height、seq 和 fee proof；删除使用短期传播的签名删除命令，不作为永久 record 保存。
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
| `/blob/<account_id>/<object_id>/manifest` 和 `/blob/<account_id>/<object_id>/chunk/<n>` | 用户命名的小 blob 分片 | 仅 `sha256(pubkey)==account_id` 的 owner 可写 |
| `/tmp/...` | 临时数据 | TTL 受限 |
| `/sys/...` | 系统参数、miner/pool 元数据等系统数据 | 只允许配置的 system signer |

segment 字符集限制为 `[a-z0-9._-]`，并有长度限制。DKVS-safe name 原样作为 `name_id`；不安全 canonical name 使用 `hex(sha256(canonical_name))`。

`object_id` 是 owner 自己选择的稳定名称，可以是用户熟悉的文件名或对象名，不是内容 hash。同一 `account_id + object_id` 可通过更高版本 record 更新。写入时必须先提交 manifest，再提交 chunks；manifest 和全部 chunks 必须使用相同 pubkey、seq 和 expiry，节点逐块校验 chunk hash，并在读取组装时校验最终 content hash。内容 hash 只保证完整性，不参与对象寻址或写入权限。

## Record 与选择规则

同一个 key 当前只保存一个 active candidate，不保存多版本历史。

DKVS record 尽量保持紧凑。当前 record 只保留一个数据字段 `Value`，不再区分 `Value` 和 `Data`；整条 record 的最大编码尺寸为 16KB。`FeeProof`、pubkey、签名和元数据也计入这 16KB，因此应用应把主要空间留给 `Value`。

如果同 key 已有 record 且 pubkey 不变，DKVS 默认认为 signer 沿用现有 owner，不重复 resolve DID。若 indexer 本地通知 name 已转移，或新 record pubkey 变化，则下次写入必须重新 resolve 当前 owner。

选择规则为：

1. 当前权限失效的旧 record 不能阻止新 owner 写入。
2. 旧 record 当前仍有效时，按 `seq -> expiry_height -> hash/bytes` 比较。
3. `seq` 是 key 自身的 revision，不与区块高度绑定；写入在外部 resolver 或 AUTOPAY 校验完成后，必须重新核对已有 record 的 pubkey、seq 和 hash，再原子提交。
4. 删除命令使用同 key owner 签名并推进 seq。节点验证后物理删除 record、hash 索引和关联 blob，只在有界传播窗口内保留删除命令，不写入 active 视图、snapshot 或永久 sequence floor。
5. Get/List/Sync/Checkpoint 只返回未过期且当前权限仍有效的 active record。

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

fee proof 当前是紧凑二进制结构，并放在 record 的 `FeeProof` bytes 字段中。record 签名覆盖 `FeeProof`，因此 fee proof 本身不再携带独立签名、record hash、key hash、record size、expiry height 或 namespace 这类可从 record 推导或由验证上下文提供的字段。

当前 proof 模式和编码内容如下：

| Mode | 编码内容 | 当前用途 |
| --- | --- |
| `AUTOPAY` | `pool_contract` | 当前推荐模式。节点读取 `autopay.tc` template 合约 state 判断 record signer 有多少 record 容量。 |
| `FREE_LOCAL` | 无额外字段 | 本地测试、开发或显式白名单策略。 |
| `ONESHOT` | `pool_contract`、`payer`、`payment_txid`、`paid_amount` | 一次性支付 proof 的预留格式。 |
| `LEASE` | `pool_contract`、`lease_contract`、`plan_id` | 租约/套餐式支付 proof 的预留格式。 |

主网默认不接受 `FREE_LOCAL`。`ONESHOT` 和 `LEASE` 目前只保留紧凑编码和基础字段校验，真实一次性支付和租约支付校验待后续阶段实现。

### AUTOPAY 验证

AUTOPAY 是当前可落地的 fee proof 方案。用户提交 record 时提供 `autopay.tc` template 合约地址；节点读取该合约 state，并验证：

1. 合约是 `autopay.tc` template。
2. 合约状态为 active 且未 closed。
3. 节点从 `record.PubKey` 派生 p2tr 地址，把该地址作为当前 record 的委托支付地址。
4. 合约的服务名称、recipient、fee asset 和最低支付额度与 DKVS 策略匹配。
5. 该委托地址在合约 state 中存在 active 委托配置。
6. 该委托地址的每区块支付额度可覆盖它当前写入的 full-size active record 数量。
7. 该委托地址的 funding 余额足以支付下一个区块。

容量按满负荷 record 计算：

```text
max_records = floor(delegate_amount_per_block / full_record_fee_per_block)
```

`delegate_amount_per_block` 来自 `autopay.tc` runtime state 中该委托地址的独立配置；如果委托人没有显式配置，runtime 使用合约部署时设置的最低支付额度。

测试网可以内置一套默认 DKVS AUTOPAY 策略，用固定服务名称、recipient、fee asset、最低支付额度和 full-record fee 定位默认合约并计算容量；这些默认值本身不授权写入，仍必须读到 live 且 active 的合约 state，并且 record signer 对应的委托地址必须有有效支付配置和余额。主网在真实合约参数、recipient 和收益规则最终确定前，不启用免费写入，也不凭默认值放行。

### AUTOPAY 支付池与挖矿收益

DKVS 保存费用最终应合并到挖矿收益或配置的服务接收地址中。第一阶段由 `autopay.tc` 充当 DKVS 支付池：多个委托地址把支付资产 funding 到同一个合约，每个区块由合约聚合本区块所有 active 委托人的应付金额，并生成一笔统一的 result tx。

如果 `autopay.tc` 的 recipient 为空，本区块聚合支付作为矿工费用进入区块收益；如果 recipient 不为空，聚合支付输出到配置的服务接收地址。DKVS core 只负责验证 record 是否被有效 fee proof 覆盖，不在 P2P 同步层单独计算或分配收益。

## 保存与过期清理

DKVS 区分 active 视图和物理保存：

- active record 才会被 `GET`、prefix list、sync、checkpoint 和 snapshot 返回；
- TTL 或 `expiry_height` 到期后，record 不再属于 active 视图；
- 之前已经缴费过的 record，第一版暂时物理永久保存，便于后续续费、审计或恢复；
- 免费 record，包括本地 `FREE_LOCAL` 或无 fee proof 但被本地策略接受的 record，过期后可以被物理删除。

节点实现需要在 DKVS 模块中提供定时清理机制，低频扫描并删除过期免费 record。当前实现还会在区块处理路径中周期性触发同一套清理逻辑；这不改变 wire 协议，也不影响付费 record 的物理保留。

用户主动删除与过期清理不同：删除命令一旦通过权限和 revision 校验，就会物理删除对应 record；删除 blob manifest 时，同一 `account_id + object_id` 下的 manifest、chunks 和 hash 索引在一个批次中删除。路径级 `PathMeta` 与 record 在同一 DB batch 中更新，并记录 active 数量、最大 seq 和 active root，用于校验 Mirror 覆盖范围，而不是充当永久 tombstone 集合。

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

同步分为两种语义：

- miner-to-miner 使用 Merge Sync。接收方只合并响应中出现的更新，绝不因对方遗漏某个 key 而删除本地 record。
- 普通节点以及尚未完成可信基线同步的 miner 使用 Mirror Sync。Mirror 只能从已认证的 core node 或 bootstrap node 获取；响应使用节点身份签名，签名覆盖 network、session、filter、请求与响应 cursor、done、root 和有序 record hash。

Mirror 在内存中暂存完整会话并设置 `DKVSReady=false`，验证页边界、签名、record 数量、总字节数、权限、fee proof、blob 完整性和覆盖范围 root 后，再以一个 DB batch 原子替换目标 key/prefix。Mirror 中缺失的 key 会被物理删除，但不产生删除命令或 sequence floor。会话失败或 root 变化时丢弃暂存数据并重试；节点只有成功建立可信基线后才对外服务 DKVS 数据。

收到 notify 后，节点用 get/data 拉取缺失 record，完整重新验证并向其他 peer 转发更新。签名删除命令也通过 notify/get/data 和反熵同步传播，并仅在有限 relay window 内保留，使短期离线节点能够追赶；长期落后的普通节点通过可信 Mirror 恢复状态。分页响应同时受 record 数量和 wire payload 大小限制，Mirror 暂存区还受总 record 数和总字节数限制。blob generation 必须包含 manifest 声明的全部 chunks，并作为一组原子替换，避免部分 generation 对外可见。

## Checkpoint

DKVS checkpoint 是本地 active record 集的 Merkle root，用于快速比较节点视图和导出 snapshot。它不是链上共识根。

它解决的是“两个节点当前 DKVS active 视图是否一致”的问题：sync response 可以携带覆盖本次 filter 的 active root，接收方在原子应用前核对暂存数据的 root。checkpoint/root 本身只是计算结果，不单独签名；P2P Mirror 响应由 server/miner 节点身份签名，从而把 root 与完整同步上下文绑定。SatoshiNet indexer 不持有私钥，也不产生签名。checkpoint 不证明全网所有历史数据都永久存在，也不自动产生链上交易。

当前已删除 checkpoint 签名与链上 anchor 方案。原因是完整 DKVS 数据长期不会由所有节点永久保存：未来可能只由 core node 保存全量，普通节点按订阅保存，规模扩大后还可能按 DHT 分组保存。强制全局 anchor 会带来高计算成本和错误安全感。更合理的长期目标是：某条 record 更新后，所有负责保存该 record 的节点最终收敛。

## 当前边界

当前阶段不包含普通节点开放订阅市场、mailbox quota、blob 大对象 SDK、一次性支付或租约支付的完整结算、checkpoint 链上锚定和 DHT 分组存储。这些属于后续协议阶段。
