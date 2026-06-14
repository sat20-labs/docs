# SAT20 Agent Wallet 测试网验证记录

> 本文记录 AI Agent 通过 `sat20-agent-wallet` skill 在 BTC testnet4 / 聪网测试环境中可以观察和验证的结果。本文只保留用户、Agent 和第三方客户端能通过钱包、adapter、L1/L2 浏览器或 indexer 复核的证据；不记录调试日志、内部函数、运行时修复过程或临时环境细节。

## 验证原则

Agent 的验证对象不是“某个服务是否声称成功”，而是以下可复核事实：

| 证据 | Agent 需要验证什么 |
| --- | --- |
| BTC L1 tx / outpoint | funding、splicing、commitment、punish 是否真实可见或已确认 |
| SatoshiNet tx / UTXO | anchor、unlock、lock、deAnchor 是否进入 L2 状态 |
| channel id / channel point | 当前承诺交易引用的通道点是否和通道状态一致 |
| commit height | 每次通道状态推进是否单调递增 |
| commitment export | 用户是否持有可广播的最新本地承诺交易 |
| punish coverage | 已撤销的对方旧承诺是否有 verified / broadcastable punish tx |
| reservation / transaction status | 未完成操作是否已经被钱包或 adapter 接管，避免重复发起 |

只有这些证据完整时，Agent 才能把通道判断为 `READY_SAFE` 并继续价值移动。

## 普通 Client Open

普通 client 钱包连接 Core Node 打开私人 STP 通道时，不需要质押资产。质押资产只属于节点连接 bootstrap node 并准备升级为 Core Node 的路径。

测试网中验证过的普通 client open 证据：

| 字段 | 值 |
| --- | --- |
| channel id | `tb1q9kf9jpmh92e8gxp4sk3mrmax28726qurl04j6x70457vzu46fzdqhe9hzu` |
| client address | `tb1pxvm0c5gt6jcjg9el8fnnjuxwsn3yme9e0zkjnp0g4658suvkw0cq4mprqc` |
| fresh open funding | `e9c283cc9979bafa4f32f872dc2d0c910b89d810ef6801a1ad55bbeb5e585782` |
| funding 状态 | BTC testnet4 已确认 |
| open 后状态 | `READY_SAFE` |

Agent 规则：

1. 如果普通 open 返回 stake-asset 相关错误，先检查 peer 类型是否误连 bootstrap node。
2. 如果旧 channel 数据已经删除或不可恢复，按普通 `stp.open` 新建通道，然后再 `stp.expand` / `stp.expand_all` 纳管通道地址上仍属于用户的资产。

## Fresh Channel 基础往返

fresh open 后，Agent 先读取 `stp.safety_snapshot`，确认承诺交易、通道点、commit height 和 punish coverage 都可验证，然后执行小额 sats 往返：

| 操作 | 资产 | 金额 | txid | 结果 |
| --- | --- | --- | --- | --- |
| `stp.unlock` | sats | `100` | `b88653f646e192765acaecbf338138c057c4ae420cbfddf7476f3cf5ea7994a8` | commit height 推进到 `1`，新旧状态有惩罚覆盖 |

该验证说明：通道打开后，用户可以把通道内白聪释放到聪网个人地址；状态每推进一次，旧 remote commitment 都必须进入可惩罚集合。

## Runes Splicing-In

Agent 验证了 Runes 资产从 BTC L1 进入 STP 通道，并在 SatoshiNet 侧形成可验证 anchor：

| 字段 | 值 |
| --- | --- |
| asset | `runes:f:BITCOIN•TESTNET` |
| amount | `10` |
| L1 splicing tx | `4ab20f45818dc73e11ad5834249f358a017c5c6b384074530c9e96e5364f06ed` |
| L2 anchor tx | `4919367e362fdf61d0943afe0b3629f79dc93fed5cf7bde811949fa44971ca1a` |
| L2 anchor height | `3491` |
| result commit height | `4` |

Agent 规则：

1. L1 splicing tx 未确认前，不重复发起同一资产 splicing-in。
2. 资产只出现在 commitment balance 中还不够；必须等 L2 anchor 进入可花费状态后，才能执行 unlock / lock。

## BRC20 Splicing-In 与 L2 往返

BRC20 进入通道通常包含 transfer inscription 前置交易和 splicing 交易。Agent 不需要理解内部构造细节，但必须能跟踪这些可见交易并确认最终 L2 anchor 可花费。

| 字段 | 值 |
| --- | --- |
| asset | `brc20:f:sgas` |
| amount | `100` |
| transfer commit tx | `03fb93e84154bd55c4fb47c5f08eb839189229ea13f6ade710c9b2bd6ff24d03` |
| transfer reveal tx | `015b6d3cbfce0ef37899d812a68713cfbb89fd84e25616fda6edf648aa52b66f` |
| L1 splicing tx | `c6481a19471dc2fc15ec411f9c2b04f5c48a13ea33a74e4e4be494cc3f703793` |
| L2 anchor UTXO | `440828e1b6ef36a3136021b40d9f8940cf0f866f93ee3b1c95a3c9758432d531:0` |
| L2 anchor height | `3492` |

BRC20 anchor 可花费后，Agent 完成了通道与聪网个人地址之间的往返：

| 操作 | 资产 | 金额 | txid | 结果 |
| --- | --- | --- | --- | --- |
| `stp.unlock` | `brc20:f:sgas` | `10` | `2e5e0fe1f44a8a6e1754558c5a9829a2b78bd6b661c7ba10f215e755888cd862` | 通道资产释放到聪网个人地址 |
| `stp.lock` | `brc20:f:sgas` | `10` | `63fd7bf150e2678956fa765b4780c2ff5cf07cd203d0d04e7eb3ae31f7e3c289` | 个人地址资产重新回到通道保护 |

Agent 规则：

1. BRC20 / Runes 在聪网上可以由 `0` sats 的 UTXO 携带，不能套用 BTC L1 dust 规则。
2. BTC L1 上携带 BRC20 / Runes 的 transfer UTXO 仍受 L1 输出规则约束。
3. 如果 adapter 无法证明 BRC20 anchor 已经从 pending 变为 spendable，Agent 只能等待，不能提前 unlock。

## 多协议资产 Expand

当资产已经位于通道地址，但尚未纳入当前通道承诺状态时，Agent 使用 `stp.expand` / `stp.expand_all` 将资产纳入通道管理。验证过的多协议资产包括：

| 操作 | L1 UTXO | 资产 | 金额 | L2 anchor txid | result commit height |
| --- | --- | --- | --- | --- | --- |
| `stp.expand` | `d4774addc9758f26807a5d476e7305051051549a362e9659fc4f6152db25e634:1` | `brc20:f:sgas` | `100` | `14c707412407c63dbb12e26b174494f2e061c706884ae0e1d6e067c34e2d26dc` | `1` |
| `stp.expand` | `d4774addc9758f26807a5d476e7305051051549a362e9659fc4f6152db25e634:6` | sats | `24377` | `f869badc78b2c75a5368259a8644f49eb67449e8a00af1b86d36ac88913b29fd` | `2` |
| `stp.expand` | `d4774addc9758f26807a5d476e7305051051549a362e9659fc4f6152db25e634:2` | `ordx:f:dogcoin` | `100` | `c908624076d08ef5da215d9e7ac33d6d3236a7ea6eb54065a666e9fc2ef57c7f` | `3` |
| `stp.expand` | `d4774addc9758f26807a5d476e7305051051549a362e9659fc4f6152db25e634:3` | `runes:f:BITCOIN•TESTNET` | `88` | `5b78b6382b8a8f84f4a59e7353294f76a74d2250a17d387d755d00ac8e4ccb2f` | `4` |

Agent 规则：

1. Expand 不是重新发行资产，而是把已在通道地址、且可由 L1/L2 证据证明属于用户的资产纳入当前承诺状态。
2. ORDX UTXO 可能同时包含 Ordinals NFT；当前 STP 只 ascend 用户明确指定的 ORDX ticker 资产，其他资产不应计入本次 L2 余额预期。
3. 一个 L1 UTXO 同时携带多种资产时，只 ascend 请求中明确指定的一种资产。

## 旧 Commitment 惩罚演练

测试网演练的核心是让 Core Node 广播一个已经被撤销的 Core Node 侧旧 commitment，然后让 client wallet 构造并广播 punish 包。Agent 只需要关注可验证证据：

| 阶段 | 证据 |
| --- | --- |
| 保留 Core Node 侧旧 commitment | retained commit height `7` |
| Core Node 侧旧 commitment | `151226853632d61d177b3279fcf99a7c144beaa3d018abd55f00f5b2adc24909` |
| 推进到新状态 | `86310825ffa2d7d229d95b175c164ed2e32cefa354459f2060d68fb65ea326d7`，commit height `8` |
| punish coverage | 旧 commitment 已被识别为 revoked，punish material 为 verified / broadcastable |

client wallet 构造并广播的 punish 包：

| txid | 作用 | 结果 |
| --- | --- | --- |
| `459877810aa391f4da5ce6a7b0a817daee0dd63f4a24b8d77062dee7ef47fbee` | 花费旧 commitment 的可惩罚输出 | BTC testnet4 已确认 |
| `23b3e6809eb5277ff9da7fb767ca8dc54e75f034104069f8c8a873b5e7c41451` | BRC20 清扫所需的前置交易 | BTC testnet4 已确认 |
| `c80dd18b79bbf1600a1a630be953de7e9f698d96c5b6a1d20eecf8f27dbb6859` | BRC20 transfer reveal | BTC testnet4 已确认 |
| `22643d7c0b8f4a6aee93bcafceecc318ca56b9d31196e17b87fda43a9ee845d5` | 将旧 commitment 上的通道资产清扫到 client 控制路径 | BTC testnet4 已确认 |

确认信息：

| 字段 | 值 |
| --- | --- |
| confirmation height | BTC testnet4 height `139387` |
| 演练结论 | Core Node 广播旧状态后，用户钱包可以惩罚旧状态并取回资产控制权 |

## Agent 必须学会的安全规则

1. `READY_SAFE` 必须来自安全快照，而不是单纯来自余额或通道 ready 状态。
2. 每次 value-moving 前都要确认 latest commitment、channel point、commit height、余额和 punish coverage。
3. 看到旧 remote commitment 被广播时，优先执行 `stp.punish_build` / `stp.punish_broadcast`，暂停普通 splicing、unlock、lock。
4. 广播返回未知网络结果时，不盲目重发；先按 txid 查询 L1/L2 可见性，再根据缺失交易做最小补救。
5. 未确认 funding、pending anchor、pending reservation 都是“等待状态”，不是“失败状态”。
6. 如果 adapter 无法证明某个资产是否 spendable，Agent 必须停止价值移动并报告缺失证据。
7. 当旧 channel 数据不可恢复时，不强行使用 reopen；按 fresh open + expand 恢复用户资产控制。

## 当前仍需补充的公开证据

这些不是调试细节，而是为了让第三方 Agent 更稳定地复现验证：

| 缺口 | 需要补充的公开数据 |
| --- | --- |
| safety snapshot 样例 | 一份完整、脱敏、稳定字段的 `READY_SAFE` JSON |
| commitment export 样例 | local / remote commitment 的 txid、hex、输出归属、CSV、资产摘要 |
| punish build 样例 | 指定旧 commitment 后，返回 punish txid、输入、输出和 verified/broadcastable |
| sweep build 样例 | force-close CSV 到期后，`broadcast:false` 的 signed/verified sweep tx 响应 |
| explorer 链接包 | L1/L2 浏览器、indexer API、PWA 截图与每个 txid 的对应关系 |
