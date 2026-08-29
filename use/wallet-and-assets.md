# 钱包与资产：第一次进入聪网

本文面向普通用户，说明当前SAT20 PWA Wallet的实际入口、资产位置和跨层操作。PWA同时支持主网和测试网；测试功能、Faucet、合约演练必须留在测试网。

## 操作前准备

1. 打开或安装 [SAT20 PWA Wallet](https://sat20.org/pwa/)。
2. 创建或导入钱包。
3. 完成助记词备份和解锁。
4. 确认当前网络是 mainnet 还是 testnet。
5. 准备需要使用的BTC L1资产或测试资产，并预留网络费。测试网可从PWA `工具 -> Faucet` 领取测试SGAS。

## 当前钱包入口

| 入口 | 当前能力 |
| --- | --- |
| 资产 | L1、SatoshiNet L2、Channel三种位置的余额与发送/接收 |
| Channel模式 | open、close、splicing-in/out、unlock、lock，以及容量不足时经用户确认的lock-with-expand |
| 市场 | 在受控内嵌页打开主网或测试网AMM/限价单市场，并由钱包审批请求 |
| 工具 | 测试Faucet、智能合约部署/调用、Mint和Mining入口 |
| 设置 | 子账户、账户管理、操作日志、密码、助记词、公钥、UTXO、节点和推荐人 |
| RGB11 | L1发行、导入、invoice、发送及账户恢复；跨入聪网的STP路径尚未开放 |

## 具体步骤

1. 打开资产页，确认顶部网络、当前钱包和子账户。
2. 在Bitcoin页查看L1资产和UTXO；本地有缓存时，远端查询失败应继续显示缓存并标明刷新异常。
3. 在SatoshiNet页查看L2资产；普通L1/L2发送都必须真实广播后才算提交成功。
4. 进入Channel模式。没有通道时，钱包先读取服务端费用配置并展示容量、服务费和预留网络费，再由用户确认open。
5. funding广播后钱包持续监控直至确认；关闭、扩容和其他已广播流程同样不能因短UI超时被当作失败重试。
6. 使用splicing-in把L1资产纳入通道，使用unlock释放到L2个人地址；回程使用lock、splicing-out或close。
7. 如果lock提示通道容量不足，钱包应解释额外BTC网络费用并询问是否执行lock-with-expand，不能静默扩容。
8. 在钱包、BTC Explorer、SatoshiNet Explorer和Indexer中核对终态。

## 如何验证

1. 查看钱包显示的 txid。
2. 在 BTC L1 Explorer 中确认 L1 交易。
3. 在 SatoshiNet Explorer 中确认 L2 交易。
4. 用 Indexer 查询资产是否在正确地址、UTXO 或通道中。
5. 如果涉及 STP 通道，确认钱包能给出安全快照。
6. 对pending操作先看操作日志和reservation/交易状态；网络结果未知时不得重复提交。

## 风险提醒

1. 不要把助记词发给 Agent 或任何网页表单。
2. 主网操作前确认资产、金额、地址和费用。
3. 如果钱包或 Agent 无法证明通道安全，停止操作。
4. 网络结果未知时，不要重复发起同一笔价值移动。

## 下一步

- [将资产进入聪网](../learn/stp.md)
- [使用 Explorer 验证交易](explorer-verification.md)
- [使用 AI Agent 查询和操作](ai-agent.md)

**页面状态：已实现 / 持续迭代（Implemented / Iterating），2026-08-29按PWA与Wallet SDK源码核对**
