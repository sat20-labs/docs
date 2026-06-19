# SAT20 Agent Wallet

> 本文说明如何安装和使用通用 SAT20 Agent Wallet skill，让 AI Agent 通过 SAT20 钱包适配器操作 SAT20 Wallet、STP 通道、BTC L1 资产和聪网资产。Codex 可以直接使用本文中的 skill 包；其他 Agent 也可以读取同一 `SKILL.md`、references 和 scripts 接入。

## 演示视频

- [1 分钟中文有声版演示视频](demo-video.md)

## 设计目标

SAT20 Agent Wallet 建立在 [比特币生态 AI Agent 资产安全评估规范](../bitcoin-agent-safety-standard.md) 之上。Agent 在操作 SAT20/STP 之前，应先用这套通用规范判断资产控制权、退出能力、链上证据、Core Node 风险和缺失数据，再决定是否允许价值移动。

SAT20 Agent Wallet skill 的目标不是把私钥放进 AI Agent，也不是把某一种语言的钱包实现写死在 skill 中。它采用三层结构：

1. Skill：定义 Agent 工作流、安全护栏、操作剧本和适配器契约。
2. 适配器调用脚本：把 Agent 的 JSON 请求转发给 SAT20 PWA Wallet Adapter 或第三方 SAT20 钱包客户端。
3. 钱包适配器：真正管理私钥、构造交易、签名、持久化钱包和通道状态，并与 indexer、SatoshiNet 和 Core Node 通信。

这样，任何团队都可以用 Go、JS、Python、Rust 或其他语言实现自己的 SAT20 钱包适配器，只要满足统一 JSON 适配器契约，AI Agent 就能通过同一个 skill 操作它。

面向普通用户的推荐形态是：用户安装 SAT20 PWA Wallet，PWA 内部加载 `sat20wallet.wasm` 和 `stpd.wasm`，SAT20 Agent Wallet 通过 PWA 暴露的受权限控制 adapter 发起 STP 操作。这样私钥、助记词、钱包数据库、交易确认和授权弹窗都留在 PWA 内，Agent 只拿到用户授权后的协议操作结果。

## 推荐安装顺序

面向普通用户和主网场景，先安装 SAT20 PWA Wallet，再安装 SAT20 Agent Wallet skill。

原因很简单：PWA 钱包是安全边界，负责私钥、助记词、钱包密码、签名、授权弹窗、钱包数据库和通道状态；skill 是 Agent 的操作知识、工作流和安全检查清单。Agent 应通过 PWA adapter 调用钱包，而不是替代钱包。

推荐顺序：

1. 安装 [SAT20 PWA Wallet](https://sat20.org/pwa/?install=1)。
2. 在 PWA 内创建或导入钱包。
3. 完成助记词备份、密码设置、网络选择和解锁。
4. 在 PWA 中启用或连接受权限控制的 Agent adapter。
5. 安装 SAT20 Agent Wallet skill。
6. Agent 先执行 `wallet.status`、`stp.status` 和 `stp.safety_snapshot`，确认钱包、网络、Core Node、通道和惩罚覆盖状态。
7. 只有安全快照满足要求后，Agent 才发起 open、splicing、unlock、lock、close 或 punish 等操作。

## Skill 目录

可安装 skill 位于：

```text
docs/ai/sat20-agent-wallet/skills/sat20-agent-wallet/
```

该 skill 库只在 `sat20-labs/docs` 仓库中维护一份。英文文档或其他站点引用 SAT20 Agent Wallet skill 时，统一链接到本目录或安装脚本，避免复制独立 skill 库。

目录结构：

```text
sat20-agent-wallet/
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

## 安装 Skill

官方 GitBook 文档入口是 [docs.sat20.org](https://docs.sat20.org)。

如果你还没有安装 SAT20 PWA Wallet，请先打开：

```text
https://sat20.org/pwa/?install=1
```

[**一键安装 SAT20 Agent Wallet**](https://raw.githubusercontent.com/sat20-labs/docs/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/install.sh)

在终端中执行：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/install.sh | bash
```

该命令默认安装到 `~/.codex/skills/sat20-agent-wallet`。如果目标 Agent 使用不同的 skills 目录，可以指定：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/install.sh | SAT20_SKILLS_DIR=/path/to/agent/skills bash
```

也可以固定安装某个分支：

```bash
curl -fsSL https://raw.githubusercontent.com/sat20-labs/docs/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/install.sh | SAT20_DOCS_BRANCH=main bash
```

脚本会从 `https://github.com/sat20-labs/docs` 下载 skill 包，只安装 `ai/sat20-agent-wallet/skills/sat20-agent-wallet` 目录；如果本地已存在同名 skill，会先移动为带时间戳的备份目录。

手动安装时，将整个 `sat20-agent-wallet` 目录复制到目标 Agent 的 skills 目录。对 Codex，可以使用：

```bash
mkdir -p ~/.codex/skills
cp -R docs/ai/sat20-agent-wallet/skills/sat20-agent-wallet ~/.codex/skills/
```

安装后，Codex 可以通过 `$sat20-agent-wallet` 显式调用该 skill。其他 Agent 如果支持 `SKILL.md` 约定，也可以直接读取 `docs/ai/sat20-agent-wallet/skills/sat20-agent-wallet/SKILL.md` 作为入口。

安装 skill 后，第一步不是直接移动资产，而是让 Agent 连接 PWA adapter 并读取 `wallet.status` / `stp.status` / `stp.safety_snapshot`。这些检查能确认 Agent 没有绕过钱包授权，也能确认通道安全材料是否完整。

后续示例使用 `SAT20_AGENT_WALLET_DIR` 表示 skill 安装目录：

```bash
export SAT20_AGENT_WALLET_DIR="docs/ai/sat20-agent-wallet/skills/sat20-agent-wallet"
```

## 配置适配器

skill 支持两种适配器方式。推荐优先使用 SAT20 PWA Wallet Adapter 暴露的 HTTP 或浏览器桥接接口。

新文档统一使用 `SAT20_ADAPTER_URL`、`SAT20_CLIENT_CMD`、`SAT20_SKILLS_DIR` 等变量。为了兼容已有测试网工具，安装脚本和转发脚本仍接受旧的 `STP_ADAPTER_URL`、`STP_CLIENT_CMD`、`STP_SKILLS_DIR`。

### PWA Wallet Adapter

用户安装并解锁 SAT20 PWA Wallet 后，由 PWA 提供一个受权限控制的 SAT20 wallet adapter。Agent 设置：

```bash
export SAT20_ADAPTER_URL="http://127.0.0.1:19530/stp-adapter"
```

或设置一个本地 CLI wrapper，把 JSON 请求转发给 PWA 的 DApp Connect / postMessage 桥接。

PWA adapter 内部调用 `sat20wallet.wasm` 和 `stpd.wasm` 完成钱包与 STP 操作。Agent 不直接加载 WASM，也不保存私钥。

当前 PWA DApp Connect 桥已经暴露 `wallet.*` 和 `stp.*` 标准方法。`wallet.status` / `stp.status` 是只读查询；创建/导入/导出助记词、改密、发送资产和通道状态变更操作会进入 PWA 的 Agent Operation 授权弹窗，用户确认后再执行。

`wallet.send_assets` 是 Agent 可控钱包的基础能力。Agent 只提交转账意图：网络、资产、金额、目标地址和可选备注；PWA 负责自动选币、估费、构造交易、展示预览、请求用户授权、签名广播和返回 txid。Agent 不应直接持有私钥、助记词或绕过 PWA 授权，也不应默认要求用户手工选择 asset UTXO 或 fee UTXO。

当前限制：PWA 侧 `wallet.transaction` / `stp.transaction` 轮询还需要继续标准化；后续应在 PWA 内补齐交易、reservation、L1/L2 可见性和下一步建议。

### 本地测试钱包 Adapter

在 SAT20 本地 workspace 中测试 skill 时，可以使用开发 adapter 创建 testnet 钱包：

```bash
SAT20_CLIENT_CMD="python3 docs/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/stp_workspace_wallet_adapter.py" \
python3 docs/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/stp_adapter.py --pretty '{"op":"wallet.create","chain":"testnet"}'
```

该 adapter 只用于 testnet bootstrap，生成的助记词应导入 SAT20 PWA Wallet；后续 STP 操作仍应由 PWA Adapter 授权执行。

### CLI 适配器

设置 `SAT20_CLIENT_CMD`：

```bash
export SAT20_CLIENT_CMD="stp-client --json"
```

Agent 会通过 skill 内置脚本调用：

```bash
python3 "$SAT20_AGENT_WALLET_DIR/scripts/stp_adapter.py" '{"op":"stp.status","chain":"testnet"}'
```

脚本会把 JSON 请求追加到 `SAT20_CLIENT_CMD` 后面，并解析适配器返回的 JSON。

### 本地 STP 适配器

如果本机已经运行兼容 STP 服务，可以使用 skill 内置的本地 adapter，将统一 JSON 操作映射到本地 STP 客户端能力：

```bash
export SAT20_CLIENT_CMD="python3 $SAT20_AGENT_WALLET_DIR/scripts/stp_transcend_rpc_adapter.py"
```

该 adapter 适合 testnet 自动化，支持 wallet import/unlock 以及 open/close/splicing-in/splicing-out/lock/unlock/lock-with-expand。异常恢复场景下还支持 `stp.clean_channel`，用于链上已确认关闭或惩罚、但 adapter 仍能看到旧 active channel 时的清理；清理后应走 ordinary `stp.open` + `stp.expand`，不能把它当作普通关闭通道的替代操作。

当前 testnet adapter 已能通过 `stp.safety_snapshot` 返回 `NO_REVOKED_REMOTE_STATE` 或 `COVERED`，Agent 可以直接据此判断是否允许继续价值移动。完整 L1/L2 余额、UTXO、PWA WASM 状态和用户授权状态应由 PWA adapter 补齐。

`stp.safety_snapshot` 还应区分承诺资产余额与 L2 可花费 UTXO。`local_balance` / `remote_balance` 表示当前承诺交易中的资产分配；`l2_spendable_balance` / `l2_pending_balance` 表示这些资产在 SatoshiNet UTXO 集中的可花费状态。Agent 发起 unlock/lock 前必须确认目标资产已经位于 `l2_spendable_balance`，不能只因为它出现在承诺资产集合中就继续操作。刚 splicing-in 的资产可能已经进入 commitment，但 anchor 输出仍在 `pendingUtxosL2`。

`stp.transaction` 应返回 Agent 可使用的 reservation 状态、相关 txid、channel id、错误码和下一步建议。如果链上交易已广播但未确认，Agent 应继续轮询，不得重复发起同一价值移动操作。

### HTTP 适配器

设置 `SAT20_ADAPTER_URL`：

```bash
export SAT20_ADAPTER_URL="http://127.0.0.1:19530/stp-adapter"
```

skill 内置脚本会向该 URL 发送 JSON POST 请求。

## 适配器职责

适配器必须完成真正的钱包和协议操作：

1. 管理用户私钥或连接安全钱包；推荐由 SAT20 PWA Wallet 完成。
2. 与 Core Node 通信。
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
| `stp.status` | 查询钱包、Core Node、通道和链状态 |
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
| `stp.test_retain_server_commitment` | 测试网让 Core Node 保留 Core Node 侧旧 commitment，主网不可用 |
| `stp.test_broadcast_retained_server_commitment` | 测试网让 Core Node 广播 Core Node 侧旧 commitment，触发惩罚演练 |

完整契约见：

- `skills/sat20-agent-wallet/references/adapter-contract.md`
- `skills/sat20-agent-wallet/references/pwa-wasm-adapter.md`

## Agent 工作流

Agent 安装 skill 后，应按以下流程操作：

1. 连接 SAT20 PWA Wallet adapter 或其他受控钱包 adapter，确认私钥、密码、助记词和签名仍在钱包安全边界内。
2. 调用 `wallet.status` 或 `stp.status`，确认网络、钱包、Core Node、通道状态。
3. 根据用户目标选择操作：
   - 钱包管理：create、import、export mnemonic、change password。
   - 普通转账：wallet.send_assets。
   - BTC L1 到聪网：open + splicing-in / expand。
   - 通道到聪网个人地址：unlock。
   - 聪网个人地址回通道：lock；容量不足时 lock-with-expand。
   - 通道到 BTC L1：splicing-out。
   - 永久退出：优先 cooperative close，异常时 force close。
4. 主网价值转移前要求用户在 PWA 钱包内确认资产、金额、地址、费率、通道和操作。
5. 每次价值移动前后都运行 `stp.safety_snapshot`；如果缺少承诺交易或 punish coverage，停止普通操作。
6. 如果 `stp.punish_status` 返回 `NO_REVOKED_REMOTE_STATE`，表示当前没有已撤销对方旧状态需要覆盖；如果返回 `COVERED`，表示已撤销状态均有 verified/broadcastable punish tx。只有这两种状态允许继续普通价值移动。
7. 如果 `stp.punish_status` 无法证明 coverage，归一化为 `PUNISH_COVERAGE_UNKNOWN`，停止普通价值移动，先要求钱包或 STP adapter 重新导出可验证证据。
8. 如果 `stp.safety_snapshot` 返回 `READY_DEGRADED`，只允许只读跟踪。典型场景是 reopen/open funding 已广播但 L1 未确认，或 adapter 正在恢复；此时不能继续 unlock、lock、splicing、close 或 punish drill。
9. 发起操作后轮询 `stp.transaction`。
10. 返回 txid、事务状态、通道状态和下一步建议。

测试网安全演练时，Agent 应按 `references/operation-playbooks.md` 中的 Testnet Punish Drill 执行：先演示 Runes/BRC20 splicing、L2 unlock/lock，再使用测试网故障注入接口触发Core Node 侧旧 commitment 广播，最后用 `stp.punish_build` / `stp.punish_broadcast` 证明惩罚能力。

真实测试网演练的总结见 [测试网演练总结](testnet-drill-summary-2026-06-13.md)。后续维护 skill 时，应优先从这份总结提炼 Agent 安全能力：价值移动前必须验证 `READY_SAFE`，刚 ascend 的资产必须等待 `l2_spendable_balance`，未知网络结果必须按“可能成功”处理，Core Node 侧旧 commitment 被广播时必须优先 punish，旧通道不能继续普通运行时应重新建立可证明安全的控制边界。

Agent 具体如何验证这些条件，以及 PWA adapter / indexer 还需要补充哪些数据，见 [验证矩阵与数据缺口](verification-and-data-gaps.md)。安装 skill 的 Agent 应把该文档作为安全验证清单，而不是只依赖操作成功或余额变化。

## 安全边界

1. SAT20 Agent Wallet 不保存私钥。
2. SAT20 Agent Wallet 不绕过钱包授权。
3. 导出助记词、修改密码必须在 PWA 钱包内确认，钱包密码不进入 Agent 对话。
4. mainnet 操作必须明确确认。
5. 核心节点状态不能被盲目信任，交易、签名、资产和承诺高度必须由适配器校验。
6. lock 容量不足时，Agent 应优先使用 lock-with-expand，保障用户随时恢复 BTC 主网承诺交易兜底的控制权。
7. Agent 不能把 punish coverage 查询失败当成安全；无法证明惩罚覆盖时，默认停止新的通道价值移动。
