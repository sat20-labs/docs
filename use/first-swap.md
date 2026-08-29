# 完成第一次 Swap

PWA的`市场`入口会按钱包当前网络打开对应L2市场：主网使用 [satsnet.ordx.market](https://satsnet.ordx.market/swap/?network=mainnet)，测试网使用 [test-satsnet.ordx.market](https://test-satsnet.ordx.market/swap/?network=testnet)。当前验收范围是AMM和限价单；不要把市场通道合约与`工具 -> 智能合约`中的模板AMM/LimitOrder混为一谈。

## 操作前准备

1. 已安装并解锁 SAT20 PWA Wallet。
2. 钱包连接到正确网络。
3. 钱包中有可用于测试的资产和测试 GAS。
4. 已确认目标 DEX 或社区 DEX 的域名和合约信息。

## 具体步骤

1. 在PWA中确认网络，再打开`市场`。页面URL必须带与钱包一致的`network`参数。
2. 市场通过SAT20 DApp Connect向父钱包请求账户或交易；钱包只接受允许的origin、未过期且未重复的requestId。
3. 选择输入资产和输出资产。
4. 查看价格、滑点、费用和预估结果。
5. 在钱包审批页核对来源、网络、资产、金额、价格/最小输出和费用；拒绝签名后请求必须终止，不能反复弹窗。
6. 批准后等待交易和对应市场item进入终态。页面toast或txid本身不是成交证明。
7. 回到资产页，核对输入资产、输出资产、找零、矿工费和合约状态。

## AMM与限价单的最小覆盖

| 类型 | 至少验证 |
| --- | --- |
| AMM | 读取现有池、一次可成交swap、余额/储备/Result变化；如本轮覆盖流动性，再验证add/remove |
| 限价单 | 按一个UTXO实际携带数量挂单、另一钱包成交、卖方/买方资产变化；再验证未成交订单取消/refund |

如果100或1000单位受池深度或价格限制，应先按池子储备计算合理数量（例如10），不能不断盲目重试。

## 如何验证

1. 记录交易 txid。
2. 在 SatoshiNet Explorer 查询交易状态。
3. 在 Indexer 查询输入和输出资产变化。
4. 如果交易涉及合约，查看合约 Result TX 或合约状态。

## 风险提醒

1. Swap 存在价格波动和滑点。
2. 测试网结果不代表主网流动性。
3. 主网交易前确认目标合约和域名来源。

**页面状态：已实现 / 测试网持续验收（Implemented / Testnet Iterating）**
