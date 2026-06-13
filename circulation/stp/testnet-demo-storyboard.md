# STP 测试网 1 分钟演示脚本

> 本脚本用于把当前测试网真实操作剪成两个版本：1 分钟传播版和完整技术演示版。画面必须使用测试网真实钱包、真实浏览器和真实 txid；旁白可以后期录制。

> 2026-06-13 收口状态：完整多资产 punish 素材已经确认，优先用于视频主线。惩罚确认后，旧 channel 数据不可安全复用，Agent 已清理 stale channel 并用 ordinary `stp.open` 建立 fresh client-core channel。fresh funding `e9c283cc9979bafa4f32f872dc2d0c910b89d810ef6801a1ad55bbeb5e585782` 已确认，通道为 `READY_SAFE`，小额 sats unlock `b88653f646e192765acaecbf338138c057c4ae420cbfddf7476f3cf5ea7994a8` 将 commit height 推进到 `1`，并生成新的 verified punish coverage。由于测试网即将回滚，本轮不再继续新的链上操作。

## 版本 1.0：60 秒资产流动与惩罚证明

| 时间 | 画面 | 字幕 / 旁白 |
| --- | --- | --- |
| 0:00-0:06 | SAT20 PWA 钱包通道页 | “这是普通用户钱包连接 core node 的 STP 私人通道，不需要资产质押。” |
| 0:06-0:12 | 通道详情 / safety snapshot | “Agent 先确认 `READY_SAFE`：commit height、承诺交易和 punish coverage 都可验证。” |
| 0:12-0:20 | BTC testnet4 浏览器打开 funding tx `820cf0...38e58` | “L1 资产进入 2-of-2 通道地址，core node 不能单独挪走用户资产。” |
| 0:20-0:30 | Runes / BRC20 / ORDX splicing 证据：`e1c677...cd9a`、`2bd1b4...9d17`、`7a0959...bc5d` | “Runes、BRC20、ORDX 等 BTC 原生协议资产可以通过 STP splicing 流动，不是托管桥。” |
| 0:30-0:39 | Runes unlock/lock `9fc617...034c` / `2bd0b0...d20`，BRC20 unlock/lock `b75780...041d` / `5373e0...8e54` | “unlock 进入聪网个人地址，lock 再回到通道保护，资产流动和安全边界可以切换。” |
| 0:39-0:49 | retained old commitment `d4774a...e634` + commit height 从 `44` 到 `45` | “测试网 core node 故意广播一个已撤销的旧承诺状态。” |
| 0:49-0:56 | punish build/broadcast `94fc21...e7dc` + BTC testnet4 mempool | “用户钱包已持有惩罚路径，Agent 构造并广播 punish tx。” |
| 0:56-1:00 | PWA 钱包资产总览 + 结论字幕 | “STP 的安全性来自最新承诺交易和惩罚旧状态的能力，资产控制权在用户手里。” |

## 必须展示的真实证据

| 证据 | 值 |
| --- | --- |
| channel id | `tb1q9kf9jpmh92e8gxp4sk3mrmax28726qurl04j6x70457vzu46fzdqhe9hzu` |
| client address | `tb1pxvm0c5gt6jcjg9el8fnnjuxwsn3yme9e0zkjnp0g4658suvkw0cq4mprqc` |
| core node pubkey | `0367f26af23dc40fdad06752c38264fe621b7bbafb1d41ab436b87ded192f1336e` |
| latest commit height | `45` |
| latest safety | `READY_SAFE` |
| latest local balance | `30640` sats, `88` Runes, `100` BRC20, `100` ORDX |
| punish coverage | `COVERED` |
| retained old commitment | `d4774addc9758f26807a5d476e7305051051549a362e9659fc4f6152db25e634` |
| retained deAnchor | `13767d3d7139880cc571c7d0c7739656492965e4323af79d933009b3b3a5c173` |
| punish tx | `94fc21bf3702f147152d3a9aa6312e32615be95228a3a11f10d6aa636290e7dc` |

## 完整技术演示版

完整技术演示版不强行限制在 1 分钟内，建议 3-5 分钟，以讲清楚 RSMC 安全机制和真实链上证据为准。该版本必须包含：

1. 通道建立和 funding tx：说明 2-of-2 通道地址是 L1 安全边界。
2. Runes、BRC20、ORDX 的 splicing 证据：说明 STP 支持 BTC 原生协议资产跨 L1/L2 流动。
3. 至少一次 L2 unlock 和 lock：说明资产可以离开通道参与聪网流动，也可以重新回到通道保护。
4. `stp.safety_snapshot`：展示最新 commit height、local/remote commitment、punish coverage。
5. 测试网 core node 广播已撤销旧 commitment：在 `mempool.space/testnet4` 展示真实 old commitment tx。
6. Agent 构造 punish tx：展示 `stp.punish_build` dry-run 结果，确认输入、输出和可广播性。
7. Agent 广播 punish tx：展示 `stp.punish_broadcast` 返回 txid，并在 L1 浏览器展示 punish tx。
8. 结论：STP 的安全基础不是信任 core node，而是用户钱包持有最新承诺交易和惩罚旧状态的能力。

1 分钟版用于快速传播，完整技术演示版用于说服懂比特币、关注 RSMC 和通道安全的人。

## 版本 1.1：fresh open 收口素材状态

这版不替代完整 punish 技术线，而是作为视频最后的“恢复后仍可安全继续”的收口画面。核心点是：旧 channel 被惩罚并删除后，Agent 不误用 `reopen`，而是 fresh open；fresh channel 已进入 `READY_SAFE`，并通过一次小额 unlock 证明状态可以继续推进、旧状态有新的 punish coverage。

| 时间 | 画面 | 字幕 / 旁白 |
| --- | --- | --- |
| 0:00-0:07 | PWA 钱包 / Agent skill 输出 | “旧通道关闭后，Agent 选择 fresh open，重新建立用户可验证的通道安全边界。” |
| 0:07-0:16 | BTC testnet4 funding `e9c283...5782` | “新的 2-of-2 channel funding 已确认，用户重新获得标准 STP 通道安全边界。” |
| 0:16-0:26 | `stp.safety_snapshot` | “fresh channel 为 `READY_SAFE`，commit height `0`，local/remote commitment 都存在。” |
| 0:26-0:38 | sats unlock `b88653...94a8` | “一笔小额 unlock 推进到 commit height `1`，证明新通道状态机正常工作。” |
| 0:38-0:52 | punish coverage 输出 | “旧 remote commitment `f30e4e...fd3e` 已有 punish tx `84524f...31a4`，`verified=true`。” |
| 0:52-1:00 | 主线 punish tx 确认画面回放 | “完整安全证明仍来自前面的真实 old commitment 和四笔 punish tx；fresh channel 是演练后的安全收口。” |
