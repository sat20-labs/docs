# 使用 AI Agent 查询和操作

AI Agent 可以帮助用户理解资产状态、检查 STP 通道安全、解释交易作用，并在用户授权后调用钱包 adapter。

Agent 不是钱包。Agent 不保存私钥、助记词或钱包密码。

## 推荐使用方式

1. 先安装并初始化 SAT20 PWA Wallet。
2. 在钱包内完成创建、导入、备份和解锁。
3. 安装 SAT20 Agent skill。
4. 让 Agent 通过 PWA adapter 调用 `wallet.status`。
5. 如果涉及 STP，调用 `stp.status` 和 `stp.safety_snapshot`。
6. Agent 给出安全判断和下一步建议。
7. 任何价值移动都在 PWA 钱包内确认。

## Agent 会告诉你什么

1. 资产现在在 BTC L1、STP 通道、聪网个人地址还是 pending 状态。
2. 当前通道是否 `READY_SAFE`。
3. 是否持有最新承诺交易。
4. 是否有 punish coverage。
5. 如果 Core Node 离线，你如何退出。
6. 如果发现旧 commitment，你是否能惩罚。
7. 本次操作有哪些 txid 和验证入口。

## 必须停止的情况

1. Agent 无法读取钱包状态。
2. 钱包没有展示授权弹窗。
3. 通道安全快照缺失。
4. 惩罚覆盖未知或缺失。
5. 网络结果未知但还没有完成 txid / reservation 检查。
6. 用户不理解主网操作的资产、金额、地址和费用。

**页面状态：开发中（In Development）**
