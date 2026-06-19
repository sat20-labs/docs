# 我是钱包或交易平台

钱包和交易平台是聪网生态的重要入口。用户最终需要在钱包和交易平台中完成资产识别、充值提现、跨层流动、交易和安全验证。

## 你需要接入什么

| 能力 | 作用 |
| --- | --- |
| L1 Indexer | 查询 BTC L1 UTXO、资产、确认数和花费状态 |
| L2 Indexer | 查询聪网 UTXO、交易、合约、通道和跨层状态 |
| STP 状态 | 判断通道、splicing、unlock、lock、close 和 pending 事务 |
| 钱包授权 | 用户签名、交易确认、助记词和密码留在钱包安全边界内 |
| Explorer 链接 | 给用户和客服提供可复核证据 |

## 推荐路径

1. 阅读 [交易平台与钱包接入](../build/exchange-and-wallet.md)。
2. 阅读 [API 源码地图](../build/api-source-map.md)，定位当前权威接口实现。
3. 阅读 [Indexer 接入与资产事实层](../build/indexer.md)。
4. 如果需要跨层资产流动，阅读 [第三方 STP 客户端接入指南](../protocol/stp/client-integration.md)。
5. 在测试网上完成充值、提现、splicing-in、splicing-out、unlock、lock 的证据链验证。

## 上线前检查

1. 是否能区分 L1 余额、L2 可花费余额和 pending 状态。
2. 是否能处理 timeout / EOF / 未索引 / reorg 等未知结果。
3. 是否能展示 txid、vout、height、confirmations 和 explorer 链接。
4. 是否能阻止用户在通道安全证据缺失时继续价值移动。
5. 是否能在主网操作前展示清晰授权信息。

