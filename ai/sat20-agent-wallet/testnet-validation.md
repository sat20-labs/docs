# SAT20 Agent Wallet 测试网验证记录

> 本文记录 AI Agent 通过 `sat20-agent-wallet` skill 在 BTC testnet4 / 聪网测试环境中可以观察和验证的结果。本文只保留用户、Agent 和第三方客户端能通过钱包、adapter、L1/L2 浏览器或 indexer 复核的证据；不记录调试日志、内部函数、运行时修复过程或临时环境细节。

> 2026-06-15 更新：当前聪网测试网需要重新建立演练证据链。下文中早期 BTC testnet4 交易仍然是可查询的 L1 历史事实，但早期聪网交易、L2 UTXO、commit height 和 punish 状态不再作为当前演练证据。新的演练从普通 `stp.open` 开始，再用 `stp.expand` 纳管通道地址上的白聪 UTXO，重新执行 Runes / BRC20 splicing-in，随后完成 unlock / lock、小额 splicing-out 和 punish drill。

“当前测试网演练结果”记录本轮最新证据。更早章节保留为历史验证记录，不能替代当前测试网状态。

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

早期测试网中验证过的普通 client open 证据：

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

## 当前测试网演练计划

当前演练从普通 `stp.open` 开始。通道进入 `READY_SAFE` 后，Agent 使用 `stp.expand` 将已经位于通道地址的白聪 UTXO 纳入通道管理。L1 地址资产余额检查显示当前可直接 expand 的资产只有白聪；Runes / BRC20 等协议资产需要重新通过 `stp.splicing_in` 进入通道。协议资产进入通道后，只做一轮最小 unlock / lock 和小额 splicing-out，然后进入 punish drill；punish 完成即视为本轮演练收口。

| 字段 | 当前值 |
| --- | --- |
| channel address | `tb1q9kf9jpmh92e8gxp4sk3mrmax28726qurl04j6x70457vzu46fzdqhe9hzu` |
| BTC L1 address summary | `32330` sats 类资产，其中普通 sats `32000` |
| SatoshiNet L2 address summary | 空 |
| L1 indexer | `https://apiprd.ordx.market/btc/testnet` |
| L2 indexer | `https://apiprd.ordx.market/satsnet/testnet` |

当前可用于 expand 的 L1 白聪 UTXO：

| UTXO | 当前 indexer 结果 | 演练用途 |
| --- | --- | --- |
| `e9c283cc9979bafa4f32f872dc2d0c910b89d810ef6801a1ad55bbeb5e585782:0` | `30000` sats，`Assets=null` | 作为主要 plain sats expand 素材 |
| `d21e85795638591adb0a20674c1436d5315a358387b56c2f16576e0f1f40901b:1` | `2000` sats，`Assets=null` | 作为小额 sats expand、unlock / lock 或 fee 观察素材 |

最短演练顺序：

1. 预检：`stp.status`、L1 channel address summary / UTXO detail、L2 channel address summary。
2. `stp.open`：记录 funding txid；通过 L1 indexer 每 10 分钟查一次确认。
3. `stp.safety_snapshot`：确认 `READY_SAFE`、channel point、commit height、commitment 和 punish coverage。
4. `stp.expand`：纳管 `e9c283...:0` 和 `d21e857...:1` 这类 plain sats UTXO，记录 L2 anchor txid。
5. Runes `stp.splicing_in`：重新采集 L1 splicing txid、L2 anchor txid、spendable UTXO。
6. BRC20 `stp.splicing_in`：重新采集 transfer commit / reveal / splicing txid、L2 anchor txid、spendable UTXO。
7. `stp.unlock` / `stp.lock`：选一个已 spendable 的资产做最小金额往返，记录两笔 L2 txid 和 commit height 变化。
8. 小额 `stp.splicing_out`：只退出一小部分资产到 BTC L1，记录 deAnchor txid、L1 splicing-out txid 和返回 UTXO。
9. Punish drill：保留旧 Core Node commitment，推进一次状态，广播旧 commitment，构造并广播 punish tx；punish 确认后本轮结束。

本轮演练的最小可交付证据包应包含：

| 证据 | 必填字段 |
| --- | --- |
| L1 UTXO 证据 | outpoint、value、asset list、confirmation、indexer URL |
| L2 anchor 证据 | txid、height、asset、amount、是否从 pending 进入 spendable |
| safety snapshot | channel point、commit height、local / remote commitment txid、余额、punish coverage |
| unlock / lock | 操作、资产、金额、L2 txid、commit height 前后变化 |
| 小额 splicing-out | asset、amount、deAnchor txid、L1 txid、返回 UTXO |
| punish drill | retained height、old commitment txid、punish build dry-run、punish broadcast txid、L1 可见性 |

L1 交易等待策略：

1. 广播 `stp.open` funding、`stp.expand` funding 或 `stp.splicing_in` L1 交易后，先记录 txid、operation、channel id、资产和金额。
2. 如果没有可并行执行的只读整理工作，Agent 进入低频等待模式，每 10 分钟通过 L1 indexer 检查一次该 tx 是否已确认。
3. 每次检查只输出一行状态：txid、确认数、下一次检查时间。
4. L1 未确认前不重复发起同类价值移动，不复用相关 UTXO。
5. L1 确认后再检查 L2 anchor、`stp.transaction` 和 `stp.safety_snapshot`，继续下一步。

## 当前测试网演练结果

`2026-06-18`，在最新一轮 fresh open 后完成了一个最小安全闭环：PWA 钱包持有助记词并为测试网 fault 请求签名；Agent 通过 skill 操作本地 STP client；Core Node 保留 height `0` 的服务端承诺交易；client 通过一次 sats unlock 将 commit height 推进到 `1`；随后 Core Node 在测试网广播旧承诺交易，client wallet 构造并广播 punish tx。完整 JSON 证据见 `evidence/testnet-minimal-punish-evidence-2026-06-18.json`。

| 阶段 | 证据 | 结果 |
| --- | --- | --- |
| 普通 open | `cda894102cfe72667c54e14b259b95d38037f8cbb6e39d1adeef7f8efb5d00f7:0` | BTC testnet4 height `140402`，通道进入 ready，commit height `0` |
| 保留 Core Node commitment | `0d033af198e477de429c7ab656afec6e2cac5e672e62692fecf5b2a385c08f83` | retained height `0`，`l2_acceptance_ok=true` |
| 推进状态 | `d7a593b9301ecf795fc58d9c339b741663723e226cb984fb981a2ceebb953a11` | sats unlock `1000`，commit height `0 -> 1` |
| 广播旧 commitment | `0d033af198e477de429c7ab656afec6e2cac5e672e62692fecf5b2a385c08f83` | BTC testnet4 height `140407`，旧 deAnchor 在状态推进后 `missing-inputs` 属于可预期结果 |
| punish tx | `6221d7793f2bbc2687d959aa2c144e25cc01be2decf9dbf2e4069cd9d21376e8` | BTC testnet4 height `140407` 确认；本地 channel `status=-2`，Core Node `status=-1` |

这轮最小演练验证了一个面向 Agent 的关键产品原则：PWA 钱包是私钥和授权边界，Agent 只提交可解释的协议操作和待签名消息；当旧承诺交易出现在 BTC L1 上时，Agent 能识别本地 punish coverage，广播 punish tx，并通过 L1 indexer 确认交易已经生效。

`2026-06-18`，在当前测试网状态下完成了一轮更紧凑的安全闭环：普通 open、expand、sats unlock / lock、BRC20 小额 splicing-out、保留旧 Core Node commitment、推进 commit height、广播旧 commitment、构造并广播 punish package。完整 JSON 证据见 `evidence/testnet-compact-punish-evidence-2026-06-18.json`。

| 阶段 | 证据 | 结果 |
| --- | --- | --- |
| 普通 open | `dbaff278b630215bfe12543ab0f84287c7a3df424fc8381121a2057966003df1:0` | BTC testnet4 height `140388`，通道进入 ready |
| expand | `97e9fae9442559ac597649c03ad4eee095f6f58d4c2b5217fa6d7290b6747265` | `brc20:f:sgas` `1000` 纳入通道，commit height `1` |
| sats unlock | `4b3a2ab3a957f99884cb2e862b9879f61d8d9d2dcc1d1b79fd34eb77f4f45b04` | commit height `2` |
| sats lock | `41170da95b97d33723c47af6b1633e1d409b364aa01b9c0785595a44dbe5c19d` | commit height `3` |
| BRC20 splicing-out | `ddf3e3e712d9b5bb343fccdf6c4485accb4587dcb6afb1731fe8a87c36b64238` | BTC testnet4 height `140395`，通道 `sgas` `1000 -> 900`，commit height `4` |
| 保留旧 Core Node commitment | `d6084d8f789a8977c5e6ed6f7245587aab71129df4776bf5b60a851cafda2939` | retained height `4`，`l2_acceptance_ok=true` |
| 推进状态 | `030b357ad599d900564831cef63f79a2e07531022c3af4ceed8dd0d0df37bfdc` | commit height `5`，height `4` 成为旧状态 |
| 广播旧 commitment | `d6084d8f789a8977c5e6ed6f7245587aab71129df4776bf5b60a851cafda2939` | BTC testnet4 height `140402` |
| punish package | `2364b55db774a2a032ec16f991b49ddc70ee7e4aa3b8c96aaf99960669c8ab7a`、`79a1fc6d17befb774aeee54e7f1675aa1f323653714441d1034ef1ead7912a22`、`f2d01ac1e9b1df247b45e2e4536efef8cfbfe70d563972197e7fa6f37f004e0c`、`4a426d996035e29e78ffb9f5fa570f0cce4ce26c17e1e39f06ed66303c7f7539` | 全部在 BTC testnet4 height `140402` 确认 |

这轮演练没有强行纳入一个存在旧 anchor / drain 歧义的 Runes 候选 UTXO。Agent 的正确行为是停止并报告证据不足，而不是为了凑齐流程去构造无法证明安全的 expand。

## 历史多资产能力覆盖

回滚前的测试网演练已经覆盖过 Runes、BRC20、ORDX、sats 的 splicing、expand、unlock、lock、splicing-out 和 punish package。由于这些早期 L2 txid 已不能在当前 SatoshiNet indexer 上复核，本文不再列出旧 txid，也不再把旧 evidence 文件作为当前证据。

这些历史演练保留为 Agent 行为规则：

1. 普通资产发送应通过 `wallet.send_assets` 暴露给 Agent。Agent 提交转账意图，PWA 负责预览、自动选币、授权、签名、广播和交易跟踪。
2. `stp.punish_broadcast` 返回 EOF 或连接中断时，Agent 不能盲目重试；必须先查询每个已生成 txid 是否在 L1/L2 可见。
3. Runes / BRC20 / ORDX 进入通道后，不能只看 commitment balance；还要确认 L2 spendable 状态。
4. BRC20 / Runes 在聪网上可以由 `0` sats 的 UTXO 携带，不能套用 BTC L1 dust 规则。
5. ORDX 必然绑定聪，应按 `bindingSat` 判断所需 sats；同一 UTXO 中未被请求 ascend 的资产不应计入本次 L2 余额预期。
6. Expand 不是重新发行资产，而是把已在通道地址、且可由 L1/L2 证据证明属于用户的资产纳入当前承诺状态。

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
