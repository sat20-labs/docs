# STP 测试网 1 分钟演示脚本

> 本脚本用于把当前测试网真实操作剪成两个版本：1 分钟传播版和完整技术演示版。画面必须使用测试网真实钱包、真实浏览器和真实 txid；旁白可以后期录制。当前版本只列出能通过当前 L1/L2 indexer 复核的 txid。

## 版本 1.0：当前可复核安全闭环

这一版使用 `2026-06-18` 的当前可复核素材，重点证明 Agent 能建立通道、推动状态、识别旧 commitment，并广播 punish tx。

| 时间 | 画面 | 字幕 / 旁白 |
| --- | --- | --- |
| 0:00-0:06 | SAT20 PWA 钱包通道页 | “这是普通用户钱包连接 Core Node 的 STP 私人通道，不需要资产质押。” |
| 0:06-0:12 | BTC testnet4 浏览器打开 funding tx `cda894...00f7` | “L1 资产进入 2-of-2 通道地址，这是用户控制权的安全边界。” |
| 0:12-0:22 | Agent / indexer 展示 retained commitment `0d033a...8f83` | “Core Node 侧旧 commitment 被保留，用于测试网安全演练。” |
| 0:22-0:32 | SatoshiNet unlock tx `d7a593...3a11` | “一次 sats unlock 推动 commit height 从 0 到 1，旧 commitment 成为已撤销状态。” |
| 0:32-0:45 | BTC testnet4 浏览器展示 old commitment `0d033a...8f83` | “测试网 Core Node 故意广播旧状态。” |
| 0:45-0:55 | BTC testnet4 浏览器展示 punish tx `6221d7...76e8` | “用户钱包持有惩罚路径，Agent 构造并广播 punish tx。” |
| 0:55-1:00 | PWA 钱包 + 安全结论字幕 | “STP 的安全基础是承诺交易和惩罚旧状态的能力，资产控制权在用户手里。” |

## 必须展示的真实证据

| 证据 | 值 |
| --- | --- |
| channel id | `tb1q9kf9jpmh92e8gxp4sk3mrmax28726qurl04j6x70457vzu46fzdqhe9hzu` |
| client address | `tb1pxvm0c5gt6jcjg9el8fnnjuxwsn3yme9e0zkjnp0g4658suvkw0cq4mprqc` |
| Core Node pubkey | `0367f26af23dc40fdad06752c38264fe621b7bbafb1d41ab436b87ded192f1336e` |
| open funding | `cda894102cfe72667c54e14b259b95d38037f8cbb6e39d1adeef7f8efb5d00f7:0` |
| retained old commitment | `0d033af198e477de429c7ab656afec6e2cac5e672e62692fecf5b2a385c08f83` |
| state advance | `d7a593b9301ecf795fc58d9c339b741663723e226cb984fb981a2ceebb953a11` |
| punish tx | `6221d7793f2bbc2687d959aa2c144e25cc01be2decf9dbf2e4069cd9d21376e8` |

## 完整技术演示版

完整技术演示版不强行限制在 1 分钟内，建议 3-5 分钟，以讲清楚 RSMC 安全机制和真实链上证据为准。该版本必须包含：

1. 通道建立和 funding tx：说明 2-of-2 通道地址是 L1 安全边界。
2. Runes、BRC20、ORDX 的 splicing 证据：说明 STP 支持 BTC 原生协议资产跨 L1/L2 流动。
3. 至少一次 L2 unlock 和 lock：说明资产可以离开通道参与聪网流动，也可以重新回到通道保护。
4. `stp.safety_snapshot`：展示最新 commit height、local/remote commitment、punish coverage。
5. 测试网 Core Node 广播已撤销旧 commitment：在 `mempool.space/testnet4` 展示真实 old commitment tx。
6. Agent 构造 punish tx：展示 `stp.punish_build` dry-run 结果，确认输入、输出和可广播性。
7. Agent 广播 punish tx：展示 `stp.punish_broadcast` 返回 txid，并在 L1 浏览器展示 punish tx。
8. 结论：STP 的安全基础不是信任 Core Node，而是用户钱包持有最新承诺交易和惩罚旧状态的能力。

## 待补拍素材

当前可复核素材已经证明最小安全闭环。完整多资产宣传片还需要重新采集当前测试网上的 Runes、BRC20、ORDX splicing-in/out、unlock/lock 和新的 punish package。未重新采集前，不用旧 L2 txid 冒充当前演练结果。
