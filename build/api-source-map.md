# API 源码地图

SAT20 当前仍在快速演进，接口字段、错误码和测试网能力会随 STP、indexer、聪网节点和钱包适配器一起变化。现阶段 API 文档采用 source-first 方式维护：先明确接口域、权威代码入口、稳定性等级和接入边界；等接口进入稳定期后，再沉淀 OpenAPI、Swagger 或 SDK 文档。

旧的 ORDX indexer Swagger 只覆盖早期部分接口，不能代表当前 SAT20 / 聪网完整接口体系。本页直接链接到 GitHub 源码，作为当前最可靠的接口入口。

## 接口域

| 接口域 | 负责项目 | 面向对象 | 当前文档策略 |
| --- | --- | --- | --- |
| BTC L1 Indexer API | [`indexer`](https://github.com/sat20-labs/indexer) | 钱包、交易平台、浏览器、STP 客户端、Agent | 以 Gin router、handler 和 wire model 为准 |
| SatoshiNet Node RPC | [`satoshinet`](https://github.com/sat20-labs/satoshinet) | 节点运维、矿工、钱包、合约工具 | 以 JSON-RPC command、handler 和 help registry 为准 |
| SatoshiNet L2 Indexer API | [`satoshinet/indexer`](https://github.com/sat20-labs/satoshinet/tree/main/indexer) | 钱包、交易平台、浏览器、STP 客户端、Agent | 以 L2 indexer router、handler 和 model 为准 |
| SAT20 Wallet WASM / PWA Adapter API | [`sat20wallet`](https://github.com/sat20-labs/sat20wallet) | 钱包 UI、DApp、AI Agent、PWA adapter | 以 WASM wrapper、PWA bridge、Agent adapter contract 为准 |
| STP Agent Adapter API | [`docs`](https://github.com/sat20-labs/docs) + [`sat20wallet`](https://github.com/sat20-labs/sat20wallet) + [`transcend`](https://github.com/sat20-labs/transcend) | AI Agent 和第三方 STP 客户端 | 以 `sat20-agent-wallet` skill 契约和实现 adapter 为准 |

## 稳定性等级

| 等级 | 含义 | 接入建议 |
| --- | --- | --- |
| Public Stable | 对外稳定接口，字段变化需要兼容 | 可用于生产接入 |
| Public Experimental | 可用于测试网和早期集成，字段可能变化 | 接入方需要保留兼容层 |
| Internal | 内部模块接口，不承诺外部兼容 | 不建议第三方直接依赖 |
| Testnet Only | 只在测试网可用，主网必须拒绝 | 仅用于演练、验证和故障注入 |
| Deprecated | 历史接口或过时文档 | 不作为新接入依据 |

## BTC L1 Indexer API

BTC L1 indexer 负责解析 BTC 主网上的 UTXO、sat range、Ordinals、Runes、BRC20、ORDX、mempool、确认数和 reorg 状态。它是钱包、交易平台、STP 和 AI Agent 判断 L1 资产事实的入口。

权威源码入口：

| 内容 | GitHub 源码 |
| --- | --- |
| 服务启动与 RPC 初始化 | [`main.go`](https://github.com/sat20-labs/indexer/blob/main/main.go) |
| Gin 总路由与 Swagger 挂载 | [`rpcserver/router.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/router.go) |
| 基础接口 router / handler | [`rpcserver/base/router.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/base/router.go), [`rpcserver/base/handler.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/base/handler.go) |
| ORDX / 多资产接口 router / handler | [`rpcserver/ordx/router.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/ordx/router.go), [`rpcserver/ordx/handler.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/ordx/handler.go), [`rpcserver/ordx/handler_v3.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/ordx/handler_v3.go) |
| Ordinals 内容接口 | [`rpcserver/ord/router.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/ord/router.go), [`rpcserver/ord/handler.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/ord/handler.go) |
| BTC 节点代理接口 | [`rpcserver/bitcoind/router.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/bitcoind/router.go), [`rpcserver/bitcoind/handler.go`](https://github.com/sat20-labs/indexer/blob/main/rpcserver/bitcoind/handler.go) |
| 对外响应模型 | [`rpcserver/wire/`](https://github.com/sat20-labs/indexer/tree/main/rpcserver/wire) |
| indexer 管理与协议处理 | [`indexer/indexermgr.go`](https://github.com/sat20-labs/indexer/blob/main/indexer/indexermgr.go), [`indexer/handle.go`](https://github.com/sat20-labs/indexer/blob/main/indexer/handle.go) |
| ORDX 协议处理 | [`indexer/ft/`](https://github.com/sat20-labs/indexer/tree/main/indexer/ft), [`indexer/nft/`](https://github.com/sat20-labs/indexer/tree/main/indexer/nft), [`indexer/ns/`](https://github.com/sat20-labs/indexer/tree/main/indexer/ns) |
| Runes / BRC20 处理 | [`indexer/runes/`](https://github.com/sat20-labs/indexer/tree/main/indexer/runes), [`indexer/brc20/`](https://github.com/sat20-labs/indexer/tree/main/indexer/brc20) |

接入重点：

1. 查询地址 UTXO 和单个 outpoint 的资产详情。
2. 查询资产协议状态、有效性和确认数。
3. 区分 mempool、已确认、未索引、reorg 和已花费状态。
4. 对 BRC20 transfer、Runes、ORDX、Ordinals 分别按协议规则解释。
5. 不把单个余额字段当成资产安全证明。

## SatoshiNet Node RPC

SatoshiNet 节点 RPC 继承 btcd 风格 JSON-RPC，同时扩展聪网交易、资产、合约、挖矿和网络能力。它服务节点运维、钱包、矿工、合约工具和调试工具。

权威源码入口：

| 内容 | GitHub 源码 |
| --- | --- |
| 节点启动与 RPC server 启动 | [`btcd.go`](https://github.com/sat20-labs/satoshinet/blob/main/btcd.go), [`server.go`](https://github.com/sat20-labs/satoshinet/blob/main/server.go) |
| JSON-RPC server | [`rpcserver.go`](https://github.com/sat20-labs/satoshinet/blob/main/rpcserver.go) |
| RPC handler adapter | [`rpcadapters.go`](https://github.com/sat20-labs/satoshinet/blob/main/rpcadapters.go) |
| WebSocket RPC | [`rpcwebsocket.go`](https://github.com/sat20-labs/satoshinet/blob/main/rpcwebsocket.go) |
| RPC help / result registry | [`rpcserverhelp.go`](https://github.com/sat20-labs/satoshinet/blob/main/rpcserverhelp.go) |
| JSON-RPC command 注册与解析 | [`btcjson/register.go`](https://github.com/sat20-labs/satoshinet/blob/main/btcjson/register.go), [`btcjson/cmdparse.go`](https://github.com/sat20-labs/satoshinet/blob/main/btcjson/cmdparse.go) |
| 链节点命令与结果 | [`btcjson/chainsvrcmds.go`](https://github.com/sat20-labs/satoshinet/blob/main/btcjson/chainsvrcmds.go), [`btcjson/chainsvrresults.go`](https://github.com/sat20-labs/satoshinet/blob/main/btcjson/chainsvrresults.go) |
| btcd 扩展命令与结果 | [`btcjson/btcdextcmds.go`](https://github.com/sat20-labs/satoshinet/blob/main/btcjson/btcdextcmds.go), [`btcjson/btcdextresults.go`](https://github.com/sat20-labs/satoshinet/blob/main/btcjson/btcdextresults.go) |
| 钱包相关命令模型 | [`btcjson/walletsvrcmds.go`](https://github.com/sat20-labs/satoshinet/blob/main/btcjson/walletsvrcmds.go), [`btcjson/walletsvrresults.go`](https://github.com/sat20-labs/satoshinet/blob/main/btcjson/walletsvrresults.go) |
| 合约执行与结果 | [`contract/`](https://github.com/sat20-labs/satoshinet/tree/main/contract) |
| POS 挖矿 | [`mining/posminer/`](https://github.com/sat20-labs/satoshinet/tree/main/mining/posminer) |

接入重点：

1. 区分继承自 btcd 的节点 RPC 与 SAT20 / SatoshiNet 扩展 RPC。
2. 合约、资产、挖矿相关接口以当前 command / result struct 为准。
3. 节点 RPC 不替代 indexer；资产事实仍需要 L1/L2 indexer 交叉验证。

## SatoshiNet L2 Indexer API

SatoshiNet L2 indexer 集成在聪网节点体系中，负责解析 L2 UTXO、ascend、descend、通道、合约、Core Node 状态和资产状态。它是 STP 操作后验证 L2 资产事实的入口。

权威源码入口：

| 内容 | GitHub 源码 |
| --- | --- |
| L2 indexer 启动 | [`indexer/main.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/main.go) |
| L2 indexer 总路由 | [`indexer/rpcserver/router.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/rpcserver/router.go) |
| SatoshiNet 查询 router / handler | [`indexer/rpcserver/satoshinet/router.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/rpcserver/satoshinet/router.go), [`indexer/rpcserver/satoshinet/handler.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/rpcserver/satoshinet/handler.go) |
| indexer 查询 router / handler / model | [`indexer/rpcserver/indexer/router.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/rpcserver/indexer/router.go), [`indexer/rpcserver/indexer/handler.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/rpcserver/indexer/handler.go), [`indexer/rpcserver/indexer/model.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/rpcserver/indexer/model.go) |
| L2 indexer 管理器 | [`indexer/indexer/indexermgr.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/indexer/indexermgr.go) |
| L2 交易处理 | [`indexer/indexer/handle.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/indexer/handle.go) |
| ascend / descend / STP 相关解析 | [`indexer/indexer/base/transcend.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/indexer/base/transcend.go), [`indexer/indexer/stp/transcend.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/indexer/stp/transcend.go) |
| channel 状态索引 | [`indexer/indexer/base/channel_state.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/indexer/base/channel_state.go) |
| 合约索引 | [`indexer/indexer/contract_index.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/indexer/contract_index.go), [`indexer/indexer/contract/indexer.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/indexer/contract/indexer.go) |
| L2 RPC client | [`indexer/share/satsnet_rpc/rpc.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/share/satsnet_rpc/rpc.go), [`indexer/share/satsnet_rpc/rpcclient.go`](https://github.com/sat20-labs/satoshinet/blob/main/indexer/share/satsnet_rpc/rpcclient.go) |

接入重点：

1. 查询 L2 UTXO、资产余额和可花费状态。
2. 查询 ascend / descend 与 BTC L1 txid、outpoint 的对应关系。
3. 查询通道地址 ledger，用于 rebuild、expand 和异常恢复。
4. 查询合约执行结果和合约状态。
5. 区分 pending、confirmed、not indexed 和 reorg / rollback 后状态。

## SAT20 Wallet WASM / PWA Adapter API

SAT20 Wallet 负责私钥、助记词、签名、资产发送、用户授权、PWA 钱包状态和 STP adapter 调用。AI Agent 不直接接触私钥，而是通过 PWA adapter 或本地受控 adapter 发起操作。

权威源码入口：

| 内容 | GitHub 源码 |
| --- | --- |
| Go WASM 入口 | [`sdk/wasm/main.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wasm/main.go) |
| 钱包核心管理 | [`sdk/wallet/manager.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/manager.go), [`sdk/wallet/wallet.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/wallet.go) |
| 钱包基础接口 | [`sdk/wallet/interface.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/interface.go) |
| 普通资产发送 | [`sdk/wallet/interface_send.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/interface_send.go), [`sdk/wallet/interface_send2.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/interface_send2.go) |
| PSBT / 签名接口 | [`sdk/wallet/interface_psbt.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/interface_psbt.go), [`sdk/wallet/sign.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/sign.go) |
| 合约客户端接口 | [`sdk/wallet/interface_contract_client.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/interface_contract_client.go), [`sdk/wallet/interface_contract_unified.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/interface_contract_unified.go) |
| STP / 通道钱包能力 | [`sdk/wallet/channelwallet.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/channelwallet.go), [`sdk/wallet/chaininfo_satsnet.go`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/wallet/chaininfo_satsnet.go) |
| PWA WASM wrapper | [`pwa/utils/sat20.ts`](https://github.com/sat20-labs/sat20wallet/blob/main/pwa/utils/sat20.ts), [`pwa/utils/stp.ts`](https://github.com/sat20-labs/sat20wallet/blob/main/pwa/utils/stp.ts) |
| PWA Agent adapter | [`pwa/composables/usePwaAgentAdapter.ts`](https://github.com/sat20-labs/sat20wallet/blob/main/pwa/composables/usePwaAgentAdapter.ts) |
| PWA DApp Connect 类型 | [`pwa/types/sat20-dapp-connect.ts`](https://github.com/sat20-labs/sat20wallet/blob/main/pwa/types/sat20-dapp-connect.ts) |
| PWA DApp bridge | [`pwa/composables/usePwaDappBridge.ts`](https://github.com/sat20-labs/sat20wallet/blob/main/pwa/composables/usePwaDappBridge.ts) |
| 授权弹窗与授权状态 | [`pwa/components/approve/ApproveAgentOperation.vue`](https://github.com/sat20-labs/sat20wallet/blob/main/pwa/components/approve/ApproveAgentOperation.vue), [`pwa/store/approve.ts`](https://github.com/sat20-labs/sat20wallet/blob/main/pwa/store/approve.ts) |
| L1 / L2 资产 hooks | [`pwa/composables/hooks/useL1Assets.ts`](https://github.com/sat20-labs/sat20wallet/blob/main/pwa/composables/hooks/useL1Assets.ts), [`pwa/composables/hooks/useL2Assets.ts`](https://github.com/sat20-labs/sat20wallet/blob/main/pwa/composables/hooks/useL2Assets.ts) |

接入重点：

1. 钱包创建、导入、导出助记词、修改密码必须由钱包授权边界处理。
2. `wallet.*` 和 `stp.*` agent-facing 操作只返回授权后的结果和可验证证据。
3. STP 价值移动前后需要 `stp.safety_snapshot`、`stp.transaction`、commitment export 和 punish coverage。
4. PWA adapter 是面向普通用户和 AI Agent 的推荐接入层；底层 WASM 函数不是 Agent 直接操作边界。

## STP Agent Adapter API

STP Agent Adapter 是面向 AI Agent 的语言无关 JSON 契约。它不替代钱包，也不替代 Core Node；它定义 Agent 如何请求钱包执行操作、如何读取安全证据、如何在网络结果未知时恢复。

权威文档与源码入口：

| 内容 | GitHub 源码 |
| --- | --- |
| SAT20 Agent Wallet 安装与使用 | [`ai/sat20-agent-wallet/readme.md`](https://github.com/sat20-labs/docs/blob/main/ai/sat20-agent-wallet/readme.md) |
| 互操作技能规范 | [`ai/sat20-agent-wallet/interoperability.md`](https://github.com/sat20-labs/docs/blob/main/ai/sat20-agent-wallet/interoperability.md) |
| Adapter contract | [`ai/sat20-agent-wallet/skills/sat20-agent-wallet/references/adapter-contract.md`](https://github.com/sat20-labs/docs/blob/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/references/adapter-contract.md) |
| 操作 playbooks | [`ai/sat20-agent-wallet/skills/sat20-agent-wallet/references/operation-playbooks.md`](https://github.com/sat20-labs/docs/blob/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/references/operation-playbooks.md) |
| PWA WASM adapter 说明 | [`ai/sat20-agent-wallet/skills/sat20-agent-wallet/references/pwa-wasm-adapter.md`](https://github.com/sat20-labs/docs/blob/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/references/pwa-wasm-adapter.md) |
| 通用转发脚本 | [`ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/stp_adapter.py`](https://github.com/sat20-labs/docs/blob/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/stp_adapter.py) |
| transcend RPC adapter | [`ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/stp_transcend_rpc_adapter.py`](https://github.com/sat20-labs/docs/blob/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/stp_transcend_rpc_adapter.py) |
| workspace wallet adapter | [`ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/stp_workspace_wallet_adapter.py`](https://github.com/sat20-labs/docs/blob/main/ai/sat20-agent-wallet/skills/sat20-agent-wallet/scripts/stp_workspace_wallet_adapter.py) |

接入重点：

1. Agent 只表达目标、资产、金额、方向和安全检查要求。
2. 资产输入、fee 输入、BRC20 transfer inscription、交易包和签名由 adapter 内部处理。
3. 主网价值移动必须经过用户授权。
4. 测试网 fault / punish drill 接口只能在测试网使用。

## 文档演进

当前 API 文档以源码地图为准。后续接口稳定后，文档可以逐步补齐：

1. 关键 Public Stable 接口的请求/响应样例。
2. 标准错误码和状态机。
3. OpenAPI / Swagger，只覆盖稳定公开接口。
4. 多语言 SDK 或 client generator。
5. Agent 可复核的 explorer / indexer URL schema。
