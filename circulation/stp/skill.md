# STP Skill：Core Node Client

> 本文说明如何安装和使用通用 STP skill，让 AI Agent 通过 STP 协议客户端适配器与 core node 交互，控制 BTC / 聪网钱包中的资产跨层流动。Codex 可以直接使用本文中的 skill 包；其他 Agent 也可以读取同一 `SKILL.md`、references 和 scripts 接入。

## 设计目标

STP skill 的目标不是把私钥放进 AI Agent，也不是把某一种语言的钱包实现写死在 skill 中。它采用三层结构：

1. Skill：定义 Agent 工作流、安全护栏、操作剧本和适配器契约。
2. 适配器调用脚本：把 Agent 的 JSON 请求转发给 SAT20 PWA Wallet Adapter 或第三方 STP 客户端。
3. 钱包适配器：真正管理私钥、构造交易、签名、持久化通道状态，并与 STP Server / core node 通信。

这样，任何团队都可以用 Go、JS、Python、Rust 或其他语言实现自己的 STP 客户端，只要满足统一 JSON 适配器契约，AI Agent 就能通过同一个 skill 操作它。

面向普通用户的推荐形态是：用户安装 SAT20 PWA Wallet，PWA 内部加载 `sat20wallet.wasm` 和 `stpd.wasm`，Agent skill 通过 PWA 暴露的受权限控制 adapter 发起 STP 操作。这样私钥、助记词、钱包数据库、交易确认和授权弹窗都留在 PWA 内，Agent 只拿到用户授权后的协议操作结果。

## Skill 目录

可安装 skill 位于：

```text
docs/circulation/stp/skills/stp-core-node-client/
```

该 skill 库只在 `sat20-labs/docs` 仓库中维护一份。英文文档或其他站点如需引用 STP skill，应链接到本目录或安装脚本，不应复制一份独立的 skill 库。

目录结构：

```text
stp-core-node-client/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── install.sh
│   ├── stp_adapter.py
│   ├── stp_transcend_rpc_adapter.py
│   └── stp_workspace_wallet_adapter.py
└── references/
    ├── adapter-contract.md
    ├── operation-playbooks.md
    └── pwa-wasm-adapter.md
```

## 安装

官方 GitBook 文档入口是 [docs.sat20.org](https://docs.sat20.org)。

[**一键安装 STP Skill**](https://raw.githubusercontent.com/sat20-labs/docs/main/circulation/stp/skills/stp-core-node-client/scripts/install.sh)

在终端中执行：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/circulation/stp/skills/stp-core-node-client/scripts/install.sh | bash
```

该命令默认安装到 `~/.codex/skills/stp-core-node-client`。如果目标 Agent 使用不同的 skills 目录，可以指定：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/circulation/stp/skills/stp-core-node-client/scripts/install.sh | STP_SKILLS_DIR=/path/to/agent/skills bash
```

也可以固定安装某个分支：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/circulation/stp/skills/stp-core-node-client/scripts/install.sh | STP_DOCS_BRANCH=main bash
```

脚本会从 `https://github.com/sat20-labs/docs` 下载 skill 包，只安装 `circulation/stp/skills/stp-core-node-client` 目录；如果本地已存在同名 skill，会先移动为带时间戳的备份目录。

手动安装时，将整个 `stp-core-node-client` 目录复制到目标 Agent 的 skills 目录。对 Codex，可以使用：

```bash
mkdir -p ~/.codex/skills
cp -R docs/circulation/stp/skills/stp-core-node-client ~/.codex/skills/
```

安装后，Codex 可以通过 `$stp-core-node-client` 显式调用该 skill。其他 Agent 如果支持 `SKILL.md` 约定，也可以直接读取 `docs/circulation/stp/skills/stp-core-node-client/SKILL.md` 作为入口。

后续示例使用 `STP_SKILL_DIR` 表示 skill 安装目录：

```bash
export STP_SKILL_DIR="docs/circulation/stp/skills/stp-core-node-client"
```

## 配置适配器

skill 支持两种适配器方式。推荐优先使用 SAT20 PWA Wallet Adapter 暴露的 HTTP 或浏览器桥接接口。

### PWA Wallet Adapter

用户安装并解锁 SAT20 PWA Wallet 后，由 PWA 提供一个受权限控制的 STP adapter。Agent 设置：

```bash
export STP_ADAPTER_URL="http://127.0.0.1:19530/stp-adapter"
```

或设置一个本地 CLI wrapper，把 JSON 请求转发给 PWA 的 DApp Connect / postMessage 桥接。

PWA adapter 内部调用 `sat20wallet.wasm` 和 `stpd.wasm` 完成钱包与 STP 操作。Agent 不直接加载 WASM，也不保存私钥。

当前 PWA DApp Connect 桥已经暴露 `wallet.*` 和 `stp.*` 标准方法。`wallet.status` / `stp.status` 是只读查询；创建/导入/导出助记词、改密、发送资产和通道状态变更操作会进入 PWA 的 Agent Operation 授权弹窗，用户确认后再执行。

当前限制：PWA 侧 `wallet.transaction` / `stp.transaction` 轮询还需要继续标准化；后续应在 PWA 内补齐交易、reservation、L1/L2 可见性和下一步建议。

### 本地测试钱包 Adapter

在 SAT20 本地 workspace 中测试 skill 时，可以使用开发 adapter 创建 testnet 钱包：

```bash
STP_CLIENT_CMD="python3 docs/circulation/stp/skills/stp-core-node-client/scripts/stp_workspace_wallet_adapter.py" \
python3 docs/circulation/stp/skills/stp-core-node-client/scripts/stp_adapter.py --pretty '{"op":"wallet.create","chain":"testnet"}'
```

该 adapter 只用于 testnet bootstrap，生成的助记词应导入 SAT20 PWA Wallet；后续 STP 操作仍应由 PWA Adapter 授权执行。

### CLI 适配器

设置 `STP_CLIENT_CMD`：

```bash
export STP_CLIENT_CMD="stp-client --json"
```

Agent 会通过 skill 内置脚本调用：

```bash
python3 "$STP_SKILL_DIR/scripts/stp_adapter.py" '{"op":"stp.status","chain":"testnet"}'
```

脚本会把 JSON 请求追加到 `STP_CLIENT_CMD` 后面，并解析适配器返回的 JSON。

### 本地 STP 适配器

如果本机已经运行兼容 STP 服务，可以使用 skill 内置的本地 adapter，将统一 JSON 操作映射到本地 STP 客户端能力：

```bash
export STP_CLIENT_CMD="python3 $STP_SKILL_DIR/scripts/stp_transcend_rpc_adapter.py"
```

该 adapter 适合 testnet 自动化，支持 wallet import/unlock 以及 open/close/splicing-in/splicing-out/lock/unlock/lock-with-expand。异常恢复场景下还支持 `stp.clean_channel`，用于链上已确认关闭或惩罚、但 adapter 仍能看到旧 active channel 时的清理；清理后应走 ordinary `stp.open` + `stp.expand`，不能把它当作普通关闭通道的替代操作。

当前 testnet adapter 已能通过 `stp.safety_snapshot` 返回 `NO_REVOKED_REMOTE_STATE` 或 `COVERED`，Agent 可以直接据此判断是否允许继续价值移动。完整 L1/L2 余额、UTXO、PWA WASM 状态和用户授权状态应由 PWA adapter 补齐。

`stp.safety_snapshot` 还应区分承诺资产余额与 L2 可花费 UTXO。`local_balance` / `remote_balance` 表示当前承诺交易中的资产分配；`l2_spendable_balance` / `l2_pending_balance` 表示这些资产在 SatoshiNet UTXO 集中的可花费状态。Agent 发起 unlock/lock 前必须确认目标资产已经位于 `l2_spendable_balance`，不能只因为它出现在承诺资产集合中就继续操作。刚 splicing-in 的资产可能已经进入 commitment，但 anchor 输出仍在 `pendingUtxosL2`。

`stp.transaction` 应返回 Agent 可使用的 reservation 状态、相关 txid、channel id、错误码和下一步建议。如果链上交易已广播但未确认，Agent 应继续轮询，不得重复发起同一价值移动操作。

### HTTP 适配器

设置 `STP_ADAPTER_URL`：

```bash
export STP_ADAPTER_URL="http://127.0.0.1:19530/stp-adapter"
```

skill 内置脚本会向该 URL 发送 JSON POST 请求。

## 适配器职责

适配器必须完成真正的钱包和协议操作：

1. 管理用户私钥或连接安全钱包；推荐由 SAT20 PWA Wallet 完成。
2. 与 STP Server / core node 通信。
3. 构造、签名和广播 BTC L1 / SatoshiNet / STP 交易。
4. 保存通道状态、承诺交易、撤销材料和未完成事务。
5. 返回统一 JSON 响应给 Agent。

skill 只负责 Agent 工作流，不负责保管私钥。

## 支持操作

适配器至少应支持三组操作。

### 钱包管理

| 操作 | 目的 |
| --- | --- |
| `wallet.create` | 创建 testnet 钱包或请求 PWA 创建钱包 |
| `wallet.import` | 把助记词导入 PWA 钱包 |
| `wallet.export_mnemonic` | 经 PWA 授权后导出助记词 |
| `wallet.change_password` | 经 PWA 授权后修改钱包密码 |
| `wallet.status` | 查询 PWA 钱包和 WASM 初始化状态 |
| `wallet.send_assets` | 直接从钱包地址发送 BTC L1 或聪网资产 |
| `wallet.transaction` | 查询普通钱包交易状态 |

### 通道管理

| 操作 | 目的 |
| --- | --- |
| `stp.status` | 查询钱包、core node、通道和链状态 |
| `stp.open` | 打开通道 |
| `stp.reopen` | 通道关闭后恢复同一个 client-core channel，必要时创建新的 L1 funding |
| `stp.rebuild` | 根据 L1/L2 ledger 证据重建通道状态，避免重复 anchor |
| `stp.restore` | 从 peer、备份或本地持久化状态恢复通道 |
| `stp.expand` / `stp.expand_all` | 将已经位于通道地址但未纳入承诺状态的资产纳入通道管理 |
| `stp.unlock` | 通道资产释放到聪网个人地址 |
| `stp.lock` | 聪网个人资产回锁到通道 |
| `stp.lock_with_expand` | 容量不足时通过穿越合约和 expand 恢复通道控制权 |
| `stp.splicing_in` | L1 资产进入通道 |
| `stp.splicing_out` | 通道资产退出到 L1 |
| `stp.close` | 协商关闭或强制关闭通道 |
| `stp.transaction` | 查询未完成 STP 事务 |

### 资产安全管理

| 操作 | 目的 |
| --- | --- |
| `stp.safety_snapshot` | 查询通道点、commit height、承诺交易、余额、CSV 和惩罚覆盖 |
| `stp.commitment_export` | 导出当前承诺交易和只读校验材料，不导出私钥或 revocation secret |
| `stp.punish_status` | 查询已撤销 remote commitment 的 punish coverage |
| `stp.punish_build` | 对指定旧 commitment 构造并 dry-run 验证惩罚交易 |
| `stp.punish_broadcast` | 广播已验证的惩罚交易 |
| `stp.force_close_plan` | 生成本地强制关闭计划，证明用户可单方面退出 |
| `stp.sweep_build` | CSV 到期后构造、签名并验证 sweep tx；默认 dry-run，可在钱包授权后广播 |
| `stp.test_retain_server_commitment` | 测试网让 core node 保留旧 server commitment，主网不可用 |
| `stp.test_broadcast_retained_server_commitment` | 测试网让 core node 广播旧 server commitment，触发惩罚演练 |

完整契约见：

- `skills/stp-core-node-client/references/adapter-contract.md`
- `skills/stp-core-node-client/references/pwa-wasm-adapter.md`

## Agent 工作流

Agent 安装 skill 后，应按以下流程操作：

1. 调用 `wallet.status` 或 `stp.status`，确认网络、钱包、core node、通道状态。
2. 根据用户目标选择操作：
   - 钱包管理：create、import、export mnemonic、change password。
   - 普通转账：wallet.send_assets。
   - BTC L1 到聪网：open + splicing-in / expand。
   - 通道到聪网个人地址：unlock。
   - 聪网个人地址回通道：lock；容量不足时 lock-with-expand。
   - 通道到 BTC L1：splicing-out。
   - 永久退出：优先 cooperative close，异常时 force close。
3. 主网价值转移前要求用户确认资产、金额、地址、费率、通道和操作。
4. 每次价值移动前后都运行 `stp.safety_snapshot`；如果缺少承诺交易或 punish coverage，停止普通操作。
5. 如果 `stp.punish_status` 返回 `NO_REVOKED_REMOTE_STATE`，表示当前没有已撤销对方旧状态需要覆盖；如果返回 `COVERED`，表示已撤销状态均有 verified/broadcastable punish tx。只有这两种状态允许继续普通价值移动。
6. 如果 `stp.punish_status` 无法证明 coverage，归一化为 `PUNISH_COVERAGE_UNKNOWN`，停止普通价值移动，先要求钱包或 STP adapter 重新导出可验证证据。
7. 如果 `stp.safety_snapshot` 返回 `READY_DEGRADED`，只允许只读跟踪。典型场景是 reopen/open funding 已广播但 L1 未确认，或 adapter 正在恢复；此时不能继续 unlock、lock、splicing、close 或 punish drill。
8. 发起操作后轮询 `stp.transaction`。
9. 返回 txid、事务状态、通道状态和下一步建议。

测试网安全演练时，Agent 应按 `references/operation-playbooks.md` 中的 Testnet Punish Drill 执行：先演示 Runes/BRC20 splicing、L2 unlock/lock，再使用测试网故障注入接口触发旧 server commitment 广播，最后用 `stp.punish_build` / `stp.punish_broadcast` 证明惩罚能力。

真实测试网演练的总结见 `testnet-drill-summary-2026-06-13.md`。后续维护 skill 时，应优先从这份总结提炼 Agent 安全能力：价值移动前必须验证 `READY_SAFE`，刚 ascend 的资产必须等待 `l2_spendable_balance`，未知网络结果必须按“可能成功”处理，旧 server commitment 被广播时必须优先 punish，旧通道不能继续普通运行时应重新建立可证明安全的控制边界。

Agent 具体如何验证这些条件，以及 PWA adapter / indexer 还需要补充哪些数据，见 `agent-verification-and-data-gaps.md`。安装 skill 的 Agent 应把该文档作为安全验证清单，而不是只依赖操作成功或余额变化。

## 安全边界

1. Agent skill 不保存私钥。
2. Agent skill 不绕过钱包授权。
3. 导出助记词、修改密码必须在 PWA 钱包内确认，不应把钱包密码输入到 Agent 对话里。
4. mainnet 操作必须明确确认。
5. 服务端状态不能被盲目信任，交易、签名、资产和承诺高度必须由适配器校验。
6. lock 容量不足时，Agent 应优先使用 lock-with-expand，保障用户随时恢复 BTC 主网承诺交易兜底的控制权。
7. Agent 不能把 punish coverage 查询失败当成安全；无法证明惩罚覆盖时，默认停止新的通道价值移动。
