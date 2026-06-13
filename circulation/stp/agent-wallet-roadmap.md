# Agent 可控钱包与 STP Skills 规划

> 本文从用户和 AI Agent 的共同视角定义 SAT20 PWA Wallet 与 STP Skills 的目标能力。最终目标是让 Agent 能在用户授权下安全控制 BTC testnet/mainnet 与聪网资产流动，并能向用户解释为什么 STP 与聪网是比特币原生、安全可退出的扩展网络。

## 核心原则

用户资产安全是所有功能的落脚点。

用户可以不了解 UTXO、承诺交易、CSV、splicing、BRC20 commit/reveal 或 Runes 细节，但 Agent 必须理解这些技术约束，并把它们转化为安全操作：

1. 先判断资产在哪一层：BTC L1、STP 通道、聪网个人地址或未确认交易中。
2. 先解释风险，再请求授权。
3. 先模拟和校验，再签名广播。
4. 任何时候都保留用户可退出、可恢复、可证明的路径。
5. lock 容量不足时，优先使用 lock-with-expand 恢复通道控制权。

## PWA Wallet 的双重角色

SAT20 PWA Wallet 不只是给人点击使用的钱包，也应该是 AI Agent 的安全执行层。

| 使用者 | PWA 应提供的能力 |
| --- | --- |
| 普通用户 | 创建/导入钱包、查看资产、确认交易、备份助记词、修改密码 |
| AI Agent | 标准 JSON adapter、权限会话、操作预览、风险检查、交易状态查询 |
| 开发者 | testnet adapter、可重复测试脚本、错误码、操作 playbook |

PWA 的边界必须清晰：私钥、助记词、密码输入、交易签名和撤销材料留在 PWA 内；Agent 只能发起意图、读取状态、解释结果。

## Skill 体系

### Wallet Skill

负责普通钱包能力：

- `wallet.status`：查询钱包、地址、WASM、L1/L2 资产清单。
- `wallet.create`：创建钱包。
- `wallet.import`：导入助记词或私钥。
- `wallet.export_mnemonic`：经 PWA 授权后导出助记词。
- `wallet.change_password`：经 PWA 授权后修改密码。
- `wallet.send_assets`：直接发送 BTC L1 或聪网资产。
- `wallet.transaction`：查询普通钱包交易状态。

### STP Channel Skill

负责通道生命周期：

- `stp.status`：查询 core node、通道、承诺高度、未完成事务。
- `stp.open`：打开通道。
- `stp.close`：协商关闭或强制关闭。
- `stp.splicing_in`：BTC L1 资产进入通道。
- `stp.splicing_out`：通道资产退出 BTC L1。
- `stp.unlock`：通道资产释放到聪网个人地址。
- `stp.lock`：聪网个人地址资产回锁到通道。
- `stp.lock_with_expand`：容量不足时扩容回锁，恢复用户通道控制权。
- `stp.transaction`：查询 STP 事务状态。

### Safety Skill

负责资产安全解释和自动保护：

- 检查网络是否匹配。
- 检查目标地址是否可用。
- 检查 UTXO 是否未确认或已被锁定。
- 检查通道是否 ready。
- 检查操作是否可被 BTC L1 承诺交易兜底。
- 给用户输出“为什么安全”和“剩余风险”。

### Testnet Lab Skill

负责测试网验证：

- 创建测试钱包。
- 获取 faucet 或测试资产。
- 转入 ORDX、BRC20、Runes 样本资产。
- 打开通道。
- splicing-in 到通道。
- unlock 到聪网个人地址。
- lock / lock-with-expand 回通道。
- splicing-out 回 BTC testnet4。

## PWA Adapter 要求

PWA 应提供一个 Agent-friendly adapter：

1. 支持 HTTP、postMessage 或本地 CLI wrapper。
2. 所有请求使用统一 JSON envelope。
3. 每个 value-moving 操作返回预览：资产、金额、来源、目标、手续费、风险。
4. 支持 `AUTH_REQUIRED`，让 Agent 引导用户在 PWA 内确认。
5. 支持会话授权范围，例如只允许 testnet、只允许单笔上限、只允许指定资产。
6. 支持撤销 Agent 授权。
7. 支持交易和通道操作审计日志。
8. 支持定期轮询未确认交易。
9. 支持 emergency exit / force close 指引。
10. 支持 lock-with-expand 的自动建议。

## 当前实施优先级

以下清单用于把 STP skill 从测试网联调能力推进到普通用户可安装、Agent 可长期操作的钱包能力。

| 优先级 | 任务 | 验收标准 |
| --- | --- | --- |
| P0 | PWA adapter 完整 `wallet.status` | 返回真实钱包地址、网络、解锁状态、L1/L2 资产、UTXO 摘要、WASM 初始化状态 |
| P0 | PWA adapter 完整 `stp.status` | 返回 core node、通道列表、channel status、commit height、pending reservation |
| P0 | PWA adapter 完整 `wallet.transaction` / `stp.transaction` | Agent 能按 txid / reservation 异步轮询，不需要读取后台日志 |
| P0 | PWA 授权弹窗标准化 | 每个价值移动操作展示资产、金额、来源、目标、手续费、通道和风险，用户确认后才签名 |
| P0 | `stp.safety_snapshot` 产品化 | Agent 能在 PWA 内读取 channel point、commit height、承诺交易、余额、CSV、punish coverage |
| P0 | 网络结果未知处理 | timeout、连接中断或服务暂不可用后返回 `NETWORK_RESULT_UNKNOWN`、reservation、txid 和下一步建议，不让 Agent 盲目重试 |
| P1 | `stp.commitment_export` | 导出只读承诺交易和校验材料，不导出私钥或 revocation secret |
| P1 | `stp.force_close_plan` | peer 离线时给出可广播 local commitment、CSV 等待和 sweep 条件 |
| P1 | `stp.punish_status` / `stp.punish_build` / `stp.punish_broadcast` | Agent 能证明、构造并广播对旧 remote commitment 的惩罚交易 |
| P1 | `stp.sweep_build` 拆分 | 已支持 build / sign / verify / optional broadcast；后续用真实测试网样例固化 schema |
| P1 | 测试网 fault API | 仅测试网构建提供保留和广播旧 server commitment 的接口，主网构建不可用 |
| P1 | ORDX 通道演练 | 按 `bindingSat` 规则完成 ORDX splicing / unlock / lock 测试 |
| P2 | 视频素材采集工具 | 自动采集 PWA、L1 浏览器、L2 浏览器、indexer JSON、skill 输出截图 |
| P2 | Agent skill 分发 | 将 `stp-core-node-client` 作为可安装 skill 发布，并保持文档目录与用户安装目录一致 |

P0 的目标是让 Agent 不依赖后台日志或人工判断，就能通过 PWA 直接操作并跟踪 STP。P1 的目标是让 Agent 不只是会转移资产，还能证明用户拥有强制退出和惩罚能力。P2 的目标是把测试网真实演练转化为可传播、可复现的产品材料。

## 当前测试网验证基线

截至当前测试网演练，Agent 使用 `stp-core-node-client` skill 和本地 transcend adapter 已验证：

| 能力 | 状态 |
| --- | --- |
| 普通 client 连接 core node open | 已完成，普通用户不需要质押资产 |
| 通道恢复 / rebuild / expand | 已完成，包含 interrupted splicing-in recovery |
| sats unlock / lock | 已完成 |
| Runes splicing-in/out、unlock/lock | 已完成 |
| BRC20 splicing-in/out、unlock/lock | 已完成 |
| 结果未知后收敛 | 已完成，已观察到广播后结果未知但 tx 可见并最终收敛 |
| `stp.safety_snapshot` | 已可返回 `READY_SAFE` |
| punish coverage | 已可返回 `COVERED` |
| 真实 punish drill | 已完成，包含旧 server commitment 广播、client punish build、四笔 punish tx 广播和确认 |
| ORDX 通道演练 | 已完成小额 splicing-in、unlock、lock；当前协议会忽略同 UTXO 中的 Ordinals NFT |
| PWA adapter 完整交易轮询 | 未完成 |
| 短视频 | 未完成，已进入制作阶段；已有 1 分钟传播版和完整技术演示版脚本、txid 素材清单 |

## 对用户的表达

Agent 最终应能把复杂技术翻译成用户能理解的安全结论：

- 你的资产不是托管给聪网。
- STP 通道保留 BTC L1 承诺交易兜底。
- 你可以通过 close 或 force close 退出。
- 资产在聪网自由流动时，可以通过 lock 或 lock-with-expand 重新纳入通道保护。
- 所有跨层动作都有交易 ID、状态和可验证链上证据。

这就是 STP 和聪网要证明的核心：让比特币原生资产获得更高效的流动性，同时尽量保持比特币主网安全模型下的用户控制权。
