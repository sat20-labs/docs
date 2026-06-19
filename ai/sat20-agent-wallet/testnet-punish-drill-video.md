# STP 测试网惩罚演练短视频制作规范

> 本文定义两个视频版本：1 分钟传播版和完整技术演示版。完整技术演示版不强行限制在 2 分钟内，必须讲清楚旧 commitment 广播、punish tx 构造和 punish tx 广播。目标用户是懂比特币、理解 UTXO 和通道安全模型的用户。视频必须基于真实测试网交易和真实钱包状态，不使用模拟 tx 冒充演练结果。

## 核心叙事

视频要传递一个事实：STP 不是托管桥。用户可以把 BTC、Runes、BRC20 等 BTC L1 原生资产通过 splicing 纳入通道，在聪网上 unlock/lock 流动，同时钱包仍持有最新承诺交易和对旧承诺交易的惩罚能力。即使 Core Node 广播旧状态，用户仍能通过惩罚交易保护资产。

一句话主线：

“我们把 Runes 和 BRC20 资产从 BTC testnet4 splicing 到 STP 通道，在聪网上 unlock/lock 流动；随后让测试网 Core Node 故意广播一个已撤销的旧承诺交易，再用用户钱包构造并广播惩罚交易，证明资产安全仍由用户掌握。”

## 素材来源

必须采集以下真实素材：

| 素材 | 用途 |
| --- | --- |
| SAT20 PWA 钱包 | 展示用户钱包、通道、授权、资产状态 |
| SAT20 Agent Wallet skill 输出 | 展示 Agent 使用标准 JSON 操作和可复核响应，而不是人工后台操作 |
| BTC L1 浏览器 `https://mempool.space/testnet4` | 展示 funding tx、旧 commitment tx、punish tx |
| L2 区块浏览器 | 展示 SatoshiNet 侧资产状态和通道相关交易 |
| L1 indexer API | 展示 BTC testnet4 UTXO 和资产信息 |
| L2 indexer API | 展示聪网 UTXO、资产和通道地址状态 |
| `stp.safety_snapshot` 输出 | 展示承诺高度、通道点、承诺交易和惩罚覆盖 |
| `stp.splicing_in` / `stp.splicing_out` 输出 | 展示 Runes、BRC20 等协议资产如何进入和退出通道 |
| `stp.unlock` / `stp.lock` 输出 | 展示资产如何在 L2 个人地址与通道保护之间切换 |
| `stp.punish_build` / `stp.punish_broadcast` 输出 | 展示惩罚交易构造和广播结果 |

## 当前测试网素材清单

当前视频素材只使用能够通过当前 L1/L2 indexer 复核的 txid。回滚前的旧 L2 txid、旧 L2 UTXO、旧 commit height 和旧 safety snapshot 不再作为画面证据出现。

当前可复核的起点：

| 片段 | 真实证据 | 当前用途 |
| --- | --- | --- |
| channel address | `tb1q9kf9jpmh92e8gxp4sk3mrmax28726qurl04j6x70457vzu46fzdqhe9hzu` | 旧通道地址，BTC L1 仍有可查询 UTXO |
| L1 plain sats UTXO | `e9c283cc9979bafa4f32f872dc2d0c910b89d810ef6801a1ad55bbeb5e585782:0`，`30000` sats | 优先作为 expand 素材 |
| L1 plain sats UTXO | `d21e85795638591adb0a20674c1436d5315a358387b56c2f16576e0f1f40901b:1`，`2000` sats | 小额 expand 或状态推进素材 |
| 协议资产 | 当前 L1 地址余额只确认白聪 | Runes / BRC20 需要重新 `splicing_in` |
| L2 address summary | 当前为空 | 需要重新采集 SatoshiNet 侧证据 |

当前演练优先采用最短路径：`stp.open`，expand 当前通道地址的 plain sats，重新执行 Runes 和 BRC20 的 splicing-in，完成一组 unlock / lock，再对小部分资产执行 splicing-out，最后执行测试网旧 commitment / punish drill。punish 完成后，本轮素材采集即收口。每次 L1 广播后，如果没有并行整理工作，只通过 L1 indexer 每 10 分钟检查一次确认。

`2026-06-18`，当前测试网又完成了一轮更紧凑的安全闭环，可作为最新 punish 证明素材：

| 片段 | 真实证据 | 状态 |
| --- | --- | --- |
| fresh open funding | `dbaff278b630215bfe12543ab0f84287c7a3df424fc8381121a2057966003df1` | BTC testnet4 height `140388` |
| BRC20 expand | `97e9fae9442559ac597649c03ad4eee095f6f58d4c2b5217fa6d7290b6747265` | `brc20:f:sgas` `1000`，commit height `1` |
| sats unlock / lock | `4b3a2ab3a957f99884cb2e862b9879f61d8d9d2dcc1d1b79fd34eb77f4f45b04`、`41170da95b97d33723c47af6b1633e1d409b364aa01b9c0785595a44dbe5c19d` | commit height 推进到 `3` |
| BRC20 splicing-out | `ddf3e3e712d9b5bb343fccdf6c4485accb4587dcb6afb1731fe8a87c36b64238` | BTC testnet4 height `140395`，通道 `sgas` `1000 -> 900` |
| retained old Core Node-side commitment | `d6084d8f789a8977c5e6ed6f7245587aab71129df4776bf5b60a851cafda2939` | retained height `4`，随后推进到 height `5` |
| punish package | `2364b55db774a2a032ec16f991b49ddc70ee7e4aa3b8c96aaf99960669c8ab7a`、`79a1fc6d17befb774aeee54e7f1675aa1f323653714441d1034ef1ead7912a22`、`f2d01ac1e9b1df247b45e2e4536efef8cfbfe70d563972197e7fa6f37f004e0c`、`4a426d996035e29e78ffb9f5fa570f0cce4ce26c17e1e39f06ed66303c7f7539` | old commitment 与全部 punish tx 均在 BTC testnet4 height `140402` 确认 |

这组素材适合作为“当前测试网最新安全验证”片段：它简短、完整，并且 old commitment 与 punish package 已确认。它不包含新的 Runes splicing-in；如果视频需要同时展示 Runes，需要重新采集一轮当前 L1/L2 都可复核的新素材。

视频不展示网络错误、重试过程或后台排障。遇到等待确认、pending anchor 或未 ready 的状态，只展示 Agent 的最终可解释结论：暂停价值移动，等待 L1/L2 证据完整后再继续。

## 1 分钟结构（优先）

| 时间 | 画面 | 讲述重点 |
| --- | --- | --- |
| 0:00-0:06 | PWA 钱包资产页 + 通道页 | 用户钱包连接 Core Node 的私人通道，不是托管账户 |
| 0:06-0:12 | L1 浏览器 funding tx | BTC 进入 2-of-2 通道地址，这是安全边界 |
| 0:12-0:24 | L1/L2 indexer + splicing tx | 当前素材展示 BRC20 与 sats 的通道流转；Runes / ORDX 需要重新采集当前可复核 txid |
| 0:24-0:36 | L2 浏览器 + unlock/lock tx | 资产可以在聪网个人地址流动，也可以重新回到通道保护 |
| 0:36-0:48 | `stp.safety_snapshot` | Agent 读取承诺高度、local/remote commitment 和 punish coverage |
| 0:48-0:56 | 旧 commitment `d6084d...2939` 与 punish package | Core Node 广播旧状态，Agent 用用户钱包广播 punish |
| 0:56-1:00 | PWA 钱包 + 安全结论字幕 | 用户拥有链上退出和惩罚旧状态的能力 |

## 当前演练结构

新版视频不复用早期 L2 状态作当前结论。1 分钟版可以压缩为：

| 时间 | 画面 | 讲述重点 |
| --- | --- | --- |
| 0:00-0:08 | PWA / Agent 执行 `stp.open` | “Agent 从普通 client open 开始，建立可验证的 STP 私人通道安全边界。” |
| 0:08-0:18 | L1 indexer 查询通道地址白聪 UTXO | “通道地址上已有白聪 UTXO，Agent 用 expand 将其纳入通道管理。” |
| 0:18-0:30 | `stp.expand` + L2 anchor | “通道地址上的 L1 UTXO 被重新纳入通道承诺状态。” |
| 0:30-0:40 | Runes / BRC20 `stp.splicing_in` | “协议资产重新通过 splicing-in 进入通道，形成新的 L1/L2 证据。” |
| 0:40-0:48 | unlock / lock / 小额 splicing-out | “资产可以进入聪网个人地址、回到通道保护，也可以小额退出回 BTC L1。” |
| 0:48-0:54 | safety snapshot + retained old commitment | “每次状态推进后，旧 remote commitment 都有惩罚覆盖。” |
| 0:54-1:00 | old commitment + punish tx 的 L1 浏览器 | “Core Node 广播旧状态时，用户钱包可以广播 punish tx 保护资产。” |

完整技术演示版需要保留更多页面停留时间，展示 open funding、plain sats expand、Runes / BRC20 splicing-in、pending L2 anchor 到 spendable、unlock / lock、小额 splicing-out，以及 punish build dry-run 的输入输出摘要。

## 完整技术演示版（建议 3-5 分钟）

| 时间 | 画面 | 讲述重点 |
| --- | --- | --- |
| 0:00-0:20 | PWA 钱包资产页 + 通道页 | 用户资产由钱包控制，不是托管在 Core Node |
| 0:20-0:45 | L1 浏览器 funding tx | BTC 进入 2-of-2 通道地址，这是 L1 安全边界 |
| 0:45-1:20 | L1/L2 indexer + `stp.splicing_in` / `stp.splicing_out` | Runes、BRC20 和 ORDX 的 UTXO 被纳入或退出通道；ORDX 展示绑定聪和 stub |
| 1:20-1:50 | L2 浏览器 + `stp.unlock` / `stp.lock` | 通道资产释放到聪网个人地址，再重新回到通道保护 |
| 1:50-2:20 | `stp.safety_snapshot` | Agent 读取通道点、承诺高度、local/remote commitment 和 punish coverage |
| 2:20-2:45 | `stp.test_retain_server_commitment` + 状态更新 | 保留 Core Node 侧旧 commitment，再推动 commit height 前进，使该 commitment 成为已撤销旧状态 |
| 2:45-3:15 | `stp.test_broadcast_retained_server_commitment` + L1 浏览器 | Core Node 广播旧 commitment；在 `mempool.space/testnet4` 展示真实 old commitment tx |
| 3:15-3:45 | `stp.punish_build` dry-run | Agent 构造 punish tx，展示将花费旧 commitment 输出，不展示私钥或 revocation secret |
| 3:45-4:20 | `stp.punish_broadcast` + L1 浏览器 | Agent 广播 punish tx，并在 L1 浏览器展示真实 punish txid |
| 4:20-5:00 | PWA 钱包 + L1/L2 indexer 最终状态 | 用户拥有资产流动、强制关闭和惩罚旧状态的能力 |

## 交易解释模板

每个 tx 必须用一句话解释作用：

- Funding tx：把 BTC L1 资产锁进用户与 Core Node 的 2-of-2 通道地址。
- Splicing-in tx：把 Runes、BRC20、ORDX 或其他 L1 协议资产追加进已有通道，不需要重新打开通道。
- ORDX anchor tx：按 `bindingSat` 把 ORDX 资产映射到聪网上；小额 ORDX 会使用 stub 满足 BTC L1 dust 约束。
- Pending L2 anchor output：资产已经进入承诺交易的资产集合，但 L2 输出仍未转为可花费，Agent 必须等待它从 `pendingUtxosL2` 进入 `UtxosL2`。
- Unlock tx：把通道内资产释放到聪网个人地址，用于 L2 快速流动和合约交互。
- Lock tx：把聪网个人地址资产重新纳入通道保护；容量不足时使用 lock-with-expand。
- Splicing-out tx：把通道资产退出回 BTC L1 地址。
- Commitment tx：通道某一高度的退出交易，定义该高度下资产归属。
- State update tx / L2 tx：推动通道状态变化，让 commit height 前进。
- Old commitment tx：测试网中故意广播的已撤销Core Node 侧旧 commitment。
- Punish tx：用户钱包用已保存的惩罚材料花费旧 commitment 输出，把资产追回到用户控制路径。
- Sweep tx：强制关闭 CSV 到期后，把用户输出清扫回用户地址。

## 画面要求

1. 画面必须展示真实 txid，但可缩短显示中间部分。
2. 涉及助记词、私钥、密码、revocation secret 的内容必须遮挡或不展示。
3. 每个关键画面保留 4-8 秒，避免观众看不清 txid 和状态。
4. 字幕使用技术表达，不使用夸张承诺。
5. 视频必须出现“testnet4 / SatoshiNet testnet”标识，避免被误解为主网演示。

## Agent 采集流程

1. 等通道进入 `READY`。
2. 运行 `stp.safety_snapshot`，保存 JSON 输出。
3. 对至少一种 Runes 资产运行 `stp.splicing_in`，保存 L1 txid、通道资产变化和 indexer UTXO 证据。
4. 对至少一种 BRC20 资产运行 `stp.splicing_in`，保存 L1 txid、通道资产变化和 indexer UTXO 证据。
5. 对 ORDX 资产可选运行小额 `stp.splicing_in`，展示绑定聪和 stub；如果 L2 输出仍在 `pendingUtxosL2`，只作为 splicing-in 素材，不作为 unlock 素材。
6. 对其中一种已经位于 `UtxosL2` 的资产运行 `stp.unlock`，展示资产从通道进入聪网个人地址。
7. 对该资产运行 `stp.lock`；如果容量不足，运行 `stp.lock_with_expand`，展示资产重新回到通道保护。
8. 可选运行一次小额 `stp.splicing_out`，展示资产退出回 BTC L1。
9. 再次运行 `stp.safety_snapshot`，保存新 commit height 和 commitment tx。
10. 运行 `stp.test_retain_server_commitment`，保存 retained height 和 retained commitment txid。
11. 发起一个小额测试网通道状态更新，使 commit height 前进。
12. 再次运行 `stp.safety_snapshot` 和 `stp.punish_status`。
13. 运行 `stp.test_broadcast_retained_server_commitment`。
14. 在 `mempool.space/testnet4` 打开旧 commitment tx。
15. 运行 `stp.punish_build`，确认 dry-run 成功。
16. 运行 `stp.punish_broadcast`。
17. 在 `mempool.space/testnet4` 打开 punish tx。
18. 在 PWA 钱包、L1 indexer、L2 indexer 中截取最终资产状态。
19. 生成两个版本：1 分钟传播版附关键 txid；完整技术演示版必须包含 old commitment txid、punish build 结果和 punish broadcast txid。

## 推荐制作方式

优先使用浏览器自动化采集真实页面截图或短录屏，再用 `ffmpeg` 合成：

- `1920x1080`，30 fps。
- 主要画面：PWA、L1 浏览器、L2 浏览器、indexer JSON。
- 旁白：1 分钟版只讲主线；完整技术演示版讲清楚 RSMC、旧 commitment、punish build 和 punish broadcast。
- 字幕：保留关键 txid、channel id、commit height、operation name。

如果当前环境无法直接录屏，可以先生成以下交付物：

1. `drill-evidence.json`：所有 operation 输出和 txid。
2. `storyboard.md`：逐秒脚本。
3. `frames/`：关键页面截图。
4. `stp-punish-drill.mp4`：最终短视频。

## 待确认项

正式演练和视频制作前，需要确认以下信息：

1. L2 区块浏览器的测试网正式 URL。
2. 测试网 Core Node 是否已经开放 fault 接口，并确认这些接口在非测试网运行时会直接拒绝。
3. 视频旁白语言：中文、英文，或先中文后英文字幕。
4. 视频品牌露出：是否使用 SAT20 / SatoshiNet / STP 标志，以及使用哪一版素材。
5. 最终发布比例：`16:9` 横屏、`9:16` 竖屏，或两版都生成。

## 审核清单

发布前必须确认：

1. 所有 txid 都能在对应浏览器或 indexer 查到。
2. 视频没有泄露助记词、私钥、密码或 revocation secret。
3. 视频明确标注测试网。
4. 演练至少包含一种 Runes 和一种 BRC20 的 splicing-in 证据。
5. 演练至少包含一次 L2 unlock 和一次 lock 或 lock-with-expand。
6. 惩罚交易不是模拟输出，而是真实构造并广播。
7. 结论表达为“用户拥有链上退出和惩罚能力”，不表达为“没有任何风险”。
