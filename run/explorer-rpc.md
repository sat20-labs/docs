# Explorer / RPC

Explorer 和 RPC 是用户、开发者、钱包、交易平台和 Agent 验证聪网状态的公共入口。

## 需要提供的能力

1. 按 txid、address、asset、contract 查询。
2. 展示 BTC L1 与聪网 L2 的跨层证据。
3. 展示 STP 通道、commit height、ascend / descend 和 punish 证据。
4. 展示合约部署、调用和 Result TX。
5. 表达 pending、not found、reorg、unindexed 和 failed 等状态。

## 当前公开入口与边界

- SatoshiNet主网交易浏览器：[mempool.sat20.org](https://mempool.sat20.org/)。
- 主网应用浏览器：[mainnet.sat20.org/browser/app](https://mainnet.sat20.org/browser/app/)。
- 测试网应用浏览器：[testnet.sat20.org/browser/app](https://testnet.sat20.org/browser/app/)。
- Bitcoin L1分别使用 [mempool.space](https://mempool.space/) 与 [testnet4](https://mempool.space/testnet4/)。

浏览器是可读展示层，协议事实仍来自对应链和Indexer。某项页面不存在、路由404或字段尚未展示时，不能解释成交易不存在；应调用PWA当前配置的L1/L2 Indexer端点，并明确网络与API proxy。

## RPC发布检查

1. 健康检查之外，抽查best height/hash、交易、地址、UTXO、资产、通道和合约接口。
2. 主网与测试网proxy必须返回各自网络数据；跨网txid查询不得静默回退。
3. `not found`、`pending`、`unindexed`、`reorged`和服务不可用应有不同错误或状态。
4. 写接口、管理接口和测试网故障注入接口不得混入公共只读RPC；主网必须拒绝测试能力。
5. Explorer链接生成器必须显式接收Bitcoin/SatoshiNet标识，底层函数不能盲猜技术栈。

用户侧验证步骤见 [使用Explorer验证交易和资产](../use/explorer-verification.md)。

**页面状态：已实现 / 展示持续完善（Implemented / Iterating）**
