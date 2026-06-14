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

截至 `2026-06-07`，已有以下真实演练素材可用于第一版剪辑和后续惩罚演练前置画面：

| 片段 | 真实证据 | 状态 |
| --- | --- | --- |
| 通道 | `tb1q9kf9jpmh92e8gxp4sk3mrmax28726qurl04j6x70457vzu46fzdqhe9hzu` | client/Core Node 均 `READY` |
| funding | `820cf0b942b301b548fd1fd65c7cd7a8d57ddcbd31d9c1811b9da17fb8c38e58` | 已确认 |
| plain sats splicing-in | `57bdad236c7e13ad32d7979cf790ef41c974fa107c98549271ff8a6ec2cfa7c6` | 已确认，commit height `6` |
| sats unlock | `275a4c82424aa93609818f1ece97eb6a3b059ded03c4235a3652b46cb8dbfc43` | 已确认，commit height `7` |
| sats lock | `5eaa2cbd31f284991bcacd5bdfebe78ae5a522be4ef4195ea6b31ccae7333631` | 已确认，commit height `8` |
| Runes splicing-out | `e1c677fb5b2a2f1f84a47db948f1bb35f4efa495bc169103e57f9bf3e4f7cd9a` | 已确认，commit height `9` |
| plain sats splicing-out fee preparation | `ba3539d6c4d5e36529247cad69e453a0df1e346af21a7b46dd3f2d226a1d9107` | 已确认，commit height `10` |
| BRC20 splicing-out L2 deAnchor | `6b7f3af34a3829860f7dcf4c837318e0de89c0cbb305da0d57da85c1b6439d50` | 聪网已确认 |
| BRC20 transfer commit | `5fd5a7409f8c54e90b5333e085a48a4daed73e92bc5e58b3905916e950bc93b1` | BRC20 splicing-out 前置交易 |
| BRC20 transfer reveal | `e1e72d8ba63c8ac9830a2bd263aa341c256253afdde55b324020ed5e394f2763` | BRC20 splicing-out 前置交易 |
| BRC20 splicing-out L1 | `354819de004c0265f52e5784c98e031a822fd12c30b65ab91c63672d8e79293b` | 已确认并触发后续 channel 清理 |
| sats unlock after recovery | `c3808db88a6bd9ee2a32d0c97a0f4dad33688ac4499ad164d9313247c23b19a8` | 聪网已确认，commit height `16` |
| sats lock after recovery | `1e3d013de886560017556f9889d820a7f5d53dac55e8e07298b8353596fffecd` | 聪网已确认，commit height `17` |
| sats unlock for L2 fee UTXO | `7c74c09f2089609ce4067d2aa761351020ed15bd5262b906302373588dd35c15` | 聪网已确认 |
| Runes unlock | `85e44685ccdd4576e8c7355398c9e001f16b9e2bc8771f366b0ef6044e643dd3` | 聪网已确认 |
| Runes lock | `1bf09936ebff4983447c84e816d533480fc6507fc06c69724b4039b133af1737` | 聪网已确认，commit height `20` |
| BRC20 splicing-in L1 | `2bd1b4fd7dd2be1286fae12e7a7746f1963c029a5425e8fd7ac1cb9c19d09d17` | 已确认，恢复后 commit height `22` |
| sats lock latest | `9a26d678310bbb09ecff91d4c49196b55c3d60598e401a2dc9afe8014f330a1a` | 聪网已确认，commit height `23` |
| Runes unlock latest | `21a4c2abdc15fccd7bb4b9655c7ac7cfa17afd6b9e990d74aec17989847f3fef` | 聪网已确认，commit height `24` |
| Runes lock latest | `1eb447d589c09f7a90ad1ad1a32ac512688739766e4591ee3a15d9105fe0b72d` | 聪网已确认，commit height `25` |
| BRC20 unlock latest | `4c2a6d370d9b163ded2ee445d1c1a183b3a0c5276610416ac86abc58d9525e29` | 聪网已确认，commit height `26` |
| BRC20 lock latest | `2f9382c069115cfe72f9e4475843014c6a6ef6a4094a2c9e3a480092e938c033` | 聪网已确认，commit height `27` |
| ORDX 小额 splicing-in L1 | `7a095955bac2ab3379bed7362b483f0d7bd743a46aa6590b795592c3457bbc5d` | 已推动 commit height `28` |
| ORDX unlock | `66a999a21b5709ee8cbfb353f2ded0cd925f3134c2ae249d30b42f60896dfe15` | 聪网已确认，commit height `29` |
| ORDX lock | `9299ab8ba755dcb3e669450664e1475978d7a1abc215ab6470f6705b97fe93b9` | 已完成，commit height `30` |
| sats unlock latest | `653e7406434a84aefbee408e6874b41b1c162970490b3832d2abed01ede00b0a` | 聪网已确认，commit height `38` |
| sats lock latest | `e0bfc23e254eb3c6b9633d72f60d8bff1179f91a44c67495d4c742ea0b2d1bd4` | 聪网已确认，commit height `39` |
| Runes unlock latest | `9fc617970e216adbb0ba147cfc24692778d871318271c867f93465cd7a60034c` | 聪网已确认，commit height `40` |
| Runes lock latest | `2bd0b006da9cc1050580e3f16a48625f635a64ecda118d1aeb383fe0292acd20` | 聪网已确认，commit height `41` |
| BRC20 unlock latest | `b757801d700c74dbed9889bee0342a1376b4003193db933a76c54b029c82041d` | 聪网已确认，commit height `43` |
| BRC20 lock latest | `5373e064ff0b408d10410d7160915f5c79b2cb7cfd0e91159f232daa67168e54` | 聪网已确认，commit height `44` |
| retained old Core Node-side commitment | `d4774addc9758f26807a5d476e7305051051549a362e9659fc4f6152db25e634` | retained height `44`，BTC testnet4 mempool 可见 |
| retained deAnchor | `13767d3d7139880cc571c7d0c7739656492965e4323af79d933009b3b3a5c173` | 聪网 height `3460` 已确认 |
| state advance after retain | `7439b9ad4cf7dd9df0d3c7528dd11c272c914372742a17b9bf9e4fef8f10f1a4` | 小额 sats lock，commit height `45` |
| punish tx | `94fc21bf3702f147152d3a9aa6312e32615be95228a3a11f10d6aa636290e7dc` | `stp.punish_build` verified，已广播，BTC testnet4 mempool 可见 |

当前通道素材已经覆盖通道恢复、sats unlock/lock、Runes unlock/lock、Runes splicing-out、BRC20 splicing-out、BRC20 splicing-in、ORDX 小额 splicing-in 和 ORDX unlock/lock。最新一轮还完成了真实Core Node 侧旧 commitment 广播和真实 punish 广播：通道在 retained height `44` 后推进到 `45`，client safety snapshot 显示旧 commitment `d4774add...e634` 的 punish tx `94fc21...e7dc` 为 `verified=true`、`broadcastable=true`，随后旧 commitment 与 punish tx 均进入 BTC testnet4 mempool。该素材可以直接用于完整技术演示版的惩罚证明段落。

视频不展示网络错误、重试过程或后台排障。遇到等待确认、pending anchor 或未 ready 的状态，只展示 Agent 的最终可解释结论：暂停价值移动，等待 L1/L2 证据完整后再继续。

`2026-06-13`，通道已恢复到新的 channel point `88e1b9dba50105996acf881183654742e3503bb7f553b4afe9c8165662e744c6:0`，并完成了一轮更适合视频演示的多资产流程：

| 片段 | 真实证据 | 状态 |
| --- | --- | --- |
| BRC20 expand | `d4774addc9758f26807a5d476e7305051051549a362e9659fc4f6152db25e634:1` -> anchor `14c707412407c63dbb12e26b174494f2e061c706884ae0e1d6e067c34e2d26dc` | commit height `1` |
| ORDX expand | `d4774addc9758f26807a5d476e7305051051549a362e9659fc4f6152db25e634:2` -> anchor `c908624076d08ef5da215d9e7ac33d6d3236a7ea6eb54065a666e9fc2ef57c7f` | commit height `3` |
| Runes expand | `d4774addc9758f26807a5d476e7305051051549a362e9659fc4f6152db25e634:3` -> anchor `5b78b6382b8a8f84f4a59e7353294f76a74d2250a17d387d755d00ac8e4ccb2f` | commit height `4` |
| sats unlock / lock | `1f1023962f5f82d6a7f3fe7811d9858294d533730dd9b944d188c1aed6e4dae0` / `ab8830a55d02fe576baf28aa8e8801d492eea14908ce1f85457c520c4ab0e435` | commit height `5` / `6` |
| BRC20 unlock / lock | `245fe5a2a8ee09c895e9c83ce37c9efaa8866ecf569ec307514376150b6211ca` / `c00b0e01b3b1d7f9d436569988b29ac0fd62243123cdd120ab028a9b87f2634e` | commit height `7` / `8` |
| retained old Core Node-side commitment | `3cc0479d77d1f9b9523bdd5f515821bd539df0c54fc39c11ae8f5db3b5791b0f` | retained height `8`，L1 mempool 可见 |
| state advance after retain | `b822218ad2e8524392b3fa29549b133eea95c186f1cb7695f6fe6622c241d215` | commit height `9` |
| punish package | `1abfb62dda8dc11816fd2483c079f8e58fd12bd7a47a78005a01667baef90f40`, `b32445e3423db7b550e7b6d949c41a8f5b81d5e09a8549cb7eae08a140e4c60f`, `25d895df2ccccdbee48dba65876f8a46981aaa62815d7d1555313150235ced6d`, `363d2c9482bdfd76861add15d9c520b0f5e8bc42318e1e598ad6a1b1d450f73e` | 全部在 BTC testnet4 height `139325` 确认，观察时确认数 `5` |

这一轮素材比 `2026-06-11` 的单笔 punish 更完整：它展示了 Core Node 侧旧 commitment 下多协议资产的惩罚包，而不是只有普通双输出惩罚。完整技术演示版应优先采用这组素材。视频旁白应以 L1 已确认的 old commitment / punish 交易和 Core Node closed 状态作为惩罚演示结论，不展示中间调试过程。

`2026-06-13` 后续又启动了一轮更干净的复拍流程：旧通道已关闭且不再复用，因此重新 `open` 一个 fresh client-core channel，再把通道地址上的遗留资产 `expand` 进新通道。

| 片段 | 真实证据 | 状态 |
| --- | --- | --- |
| fresh open funding | `fc2282849c15286fe2e7dba05847dad376d4d49a04fde06111d0a3ceac48093c` | BTC testnet4 height `139342` 已确认 |
| fresh opening anchor | `1162c17f071ea4c7cdfb77689ec9e9afcf1f82a9b813e806166db43e4e62a76e` | 新通道 `commitHeight=0` |
| expand channel sats | `c66b47bf25eeeea439ed83d06f49cee08402e1321135a0de9a1afe5d5b242463` | 聪网 height `3488` 已确认，commit height `1` |
| sats unlock / lock | `063f9df62ef0c70ad219ee70d7d617a13fa185afa2810689c2f81d5a6e01ea6b` / `08f0eb48c9d0bb09cc5843e4545ff04f44fc4f60bf3af44bca1979ee334ba726` | 聪网 height `3489` / `3490`，commit height `2` / `3` |
| Runes splicing-in | `4ab20f45818dc73e11ad5834249f358a017c5c6b384074530c9e96e5364f06ed` -> L2 anchor `4919367e362fdf61d0943afe0b3629f79dc93fed5cf7bde811949fa44971ca1a` | L1 height `139370`，L2 height `3491`，commit height `4` |
| BRC20 splicing-in | commit `03fb93e84154bd55c4fb47c5f08eb839189229ea13f6ade710c9b2bd6ff24d03`，reveal `015b6d3cbfce0ef37899d812a68713cfbb89fd84e25616fda6edf648aa52b66f`，splicing `c6481a19471dc2fc15ec411f9c2b04f5c48a13ea33a74e4e4be494cc3f703793` | 当前 L1 `0` 确认，local/core 均 `commitHeight=5`，BRC20 anchor `440828e1b6ef36a3136021b40d9f8940cf0f866f93ee3b1c95a3c9758432d531:0` 仍在 `pendingUtxosL2` |

这轮 fresh open 素材更适合展示 Agent 的安全纪律：即使 BRC20 已经进入双方 commitment 的资产分配，只要 L1 splicing tx 尚未确认、L2 anchor 仍在 `pendingUtxosL2`，Agent 就不应执行 BRC20 unlock/lock。视频中可以把这作为“AI Agent 懂得等待可花费证明”的一幕，避免观众误以为 commitment balance 就等于可立即花费的 L2 UTXO。

`2026-06-13` 后续，BRC20 splicing-in 完成收敛，Agent 补拍了 BRC20 往返和第二轮四笔 punish 包：

| 片段 | 真实证据 | 状态 |
| --- | --- | --- |
| BRC20 anchor spendable | `440828e1b6ef36a3136021b40d9f8940cf0f866f93ee3b1c95a3c9758432d531:0` | 聪网 height `3492`，进入 `UtxosL2` |
| BRC20 unlock / lock | `2e5e0fe1f44a8a6e1754558c5a9829a2b78bd6b661c7ba10f215e755888cd862` / `63fd7bf150e2678956fa765b4780c2ff5cf07cd203d0d04e7eb3ae31f7e3c289` | commit height `6` / `7` |
| retained old Core Node-side commitment | `151226853632d61d177b3279fcf99a7c144beaa3d018abd55f00f5b2adc24909` | retained height `7`，随后用 `86310825ffa2d7d229d95b175c164ed2e32cefa354459f2060d68fb65ea326d7` 推进到 height `8` |
| punish package | `459877810aa391f4da5ce6a7b0a817daee0dd63f4a24b8d77062dee7ef47fbee`, `23b3e6809eb5277ff9da7fb767ca8dc54e75f034104069f8c8a873b5e7c41451`, `c80dd18b79bbf1600a1a630be953de7e9f698d96c5b6a1d20eecf8f27dbb6859`, `22643d7c0b8f4a6aee93bcafceecc318ca56b9d31196e17b87fda43a9ee845d5` | 四笔均在 BTC testnet4 height `139387` 确认 |
| fresh open after punish | `e9c283cc9979bafa4f32f872dc2d0c910b89d810ef6801a1ad55bbeb5e585782` | 惩罚确认后清理 stale channel，用 ordinary `stp.open` 重新打开；funding 已在 BTC testnet4 height `139406` 确认 |
| fresh channel safety close-out | unlock `b88653f646e192765acaecbf338138c057c4ae420cbfddf7476f3cf5ea7994a8`，punish `84524f5aaa367f6ff7bcb15e1d01f8f7fa97fa93779c04cb96bc5ec58afa31a4` | fresh channel `READY_SAFE`，commit height `1`，新 revoked remote commitment 已有 verified / broadcastable punish coverage |

这组素材可以作为完整技术演示版的第二条备选线：它展示了 BRC20 资产从 pending 到 spendable、再到 unlock/lock，最后进入旧 commitment 惩罚包。视频叙事不展示中间调试过程，只强调用户钱包持有承诺交易和惩罚旧状态的能力。最终画面使用 fresh open 后的新通道状态：funding 已确认、通道 `READY_SAFE`、commit height 已推进到 `1`，且新的 revoked remote commitment 已有 verified punish coverage。由于测试网即将回滚，本轮不再追加新的 expand/splicing/punish 链上操作。

## 1 分钟结构（优先）

| 时间 | 画面 | 讲述重点 |
| --- | --- | --- |
| 0:00-0:06 | PWA 钱包资产页 + 通道页 | 用户钱包连接 Core Node 的私人通道，不是托管账户 |
| 0:06-0:12 | L1 浏览器 funding tx | BTC 进入 2-of-2 通道地址，这是安全边界 |
| 0:12-0:24 | L1/L2 indexer + splicing tx | Runes、BRC20、ORDX 的真实 txid 证明多协议资产可进入或退出通道 |
| 0:24-0:36 | L2 浏览器 + unlock/lock tx | 资产可以在聪网个人地址流动，也可以重新回到通道保护 |
| 0:36-0:48 | `stp.safety_snapshot` | Agent 读取承诺高度、local/remote commitment 和 punish coverage |
| 0:48-0:56 | 旧 commitment `d4774add...e634` 与 punish `94fc21...e7dc` | Core Node 广播旧状态，Agent 用用户钱包广播 punish |
| 0:56-1:00 | PWA 钱包 + 安全结论字幕 | 用户拥有链上退出和惩罚旧状态的能力 |

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
