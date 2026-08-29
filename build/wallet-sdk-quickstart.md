# 集成 Wallet SDK

Wallet SDK位于 [`sat20wallet/sdk`](https://github.com/sat20-labs/sat20wallet/tree/main/sdk)，Go module为`github.com/sat20-labs/sat20wallet/sdk`。它已经被PWA和Transcend使用，但接口仍在快速迭代，接入时必须固定commit并记录本地replace依赖，不能只写一个浮动版本号。

## 选择接入层

| 场景 | 推荐入口 |
| --- | --- |
| 普通用户、DApp、AI Agent | SAT20 PWA Wallet及其授权/DApp Connect边界 |
| Go钱包或服务 | `sdk/wallet.Manager`公开接口 |
| 浏览器钱包 | `sdk/wasm`包装；不要从JavaScript绕过授权直接调用内部状态 |
| STP服务 | Transcend或同等协议客户端，复用SDK通道能力 |

## 初始化顺序

1. 构造明确的`common.Config`：`Env`、`Chain`、`Mode`、peer、L1 Indexer和L2 Indexer。
2. 为每个网络使用独立数据库。SDK默认保持自己的Pebble路径；L1 Indexer测试部署使用Badger不要求SDK切换。
3. 调用`wallet.NewManager(cfg, db)`，检查返回值，再调用`Start()`启动Indexer client、状态bootstrap、action monitor、channel heartbeat、watchtower和DKVS同步。
4. 创建或导入钱包后解锁。UI锁屏不应销毁Manager；真正退出运行时才调用`Stop()`/`Close()`。
5. 链/环境切换不在原Manager上就地修改：停止旧Manager，用目标网络配置和独立DB重新创建。

## 业务边界

- 资产查询：使用L1/L2 Indexer接口并区分Bitcoin、SatoshiNet与Channel位置；RGB11余额由客户端验证状态合并。
- 发送和广播：调用方显式提供网络；重复广播同一原始交易可视为幂等成功，但Bitcoin与SatoshiNet广播不能由底层盲猜。
- 通道：通过`GetCurrentChannel`操作当前钱包/子账户的唯一通道；生命周期pending时不要并行恢复、重开或同步旧snapshot。
- DKVS：领域模块只使用SDK的DKVS manager/账户管理接口，不自行维护cursor、outbox或第二套typed recovery helper。
- 账户恢复：root账户数据由Account Management恢复；导入非root钱包助记词只恢复该钱包链上数据。
- 授权：私钥、助记词和签名留在钱包边界。DApp或Agent只提交意图并接收授权后的结果与证据。

## 最小验收

1. create/import、错误密码、修改密码、重启解锁和重复钱包限制。
2. L1/L2资产查询、真实发送与unknown-result幂等处理。
3. open/close、splicing、unlock/lock、容量不足的lock-with-expand和ping恢复。
4. DKVS写入、更新、删除、重建；FREE_LOCAL不传播，AUTOPAY最终更新能从另一节点读到。
5. 账户恢复分别覆盖无RGB11和有RGB11数据。
6. PWA审批拒绝不会广播，批准只广播一次，并留下操作日志。

更完整的接口域见 [API源码地图](api-source-map.md)，STP集成见 [第三方STP客户端接入指南](../protocol/stp/client-integration.md)。

**页面状态：已实现 / API持续迭代（Implemented / API Iterating）**
