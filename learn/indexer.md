# Indexer：比特币资产事实层

比特币主网原生只理解 UTXO 和 BTC。Ordinals、Runes、BRC20、ORDX 等资产协议都建立在 BTC 交易、脚本、铭文、sat range 或协议事件之上。用户、钱包、交易平台、STP 客户端和 AI Agent 要安全操作这些资产，首先需要一个统一的资产事实层。

Indexer 的作用就是把 BTC L1 上的交易事实解析为资产事实：

1. 某个地址有哪些 UTXO。
2. 每个 UTXO 中包含哪些 BTC、Ordinals、Runes、BRC20、ORDX 或其他资产。
3. 这些资产是否确认，是否可能受 mempool、reorg 或协议规则影响。
4. 某个资产转移、铸造、铭刻、部署或销毁事件是否有效。
5. 某个 L1 交易与聪网中的 ascend / descend / 通道状态是否对应。

## 为什么聪网需要 Indexer

STP 负责把 BTC L1 资产纳入通道，并让用户保持退出能力。Indexer 负责告诉钱包和 Agent：这些 BTC L1 资产到底是什么、在哪里、是否已经确认、是否可以进入通道。

没有 indexer，STP 无法可靠回答以下问题：

1. 用户选择的 UTXO 是否真的携带目标资产。
2. BRC20 transfer UTXO 是否有效。
3. Runes、ORDX、Ordinals 的资产归属是否与用户看到的一致。
4. splicing-in 的 L1 交易是否已经确认并可以映射到聪网。
5. splicing-out 或 close 之后，L1 资产是否已经回到用户可控制地址。

因此，聪网的资产基础不是单独的 STP，而是 STP + indexer。STP 提供跨层控制权，indexer 提供资产事实和可验证状态。

## Indexer 不控制资产

Indexer 不是托管方，也不是资产安全的单点信任来源。它的职责是从公开链上数据中计算资产状态，并把结果提供给钱包、交易平台、浏览器、STP 客户端和 Agent。

一个合格的 indexer 应满足三个要求：

1. 可复算：结果来自 BTC L1 和聪网交易，第三方可以独立运行同样规则复核。
2. 可追溯：余额和资产归属应能追溯到具体 txid、vout、sat range、inscription、rune event 或协议事件。
3. 可处理异常：mempool、确认数、reorg、旧状态、无效 transfer 和协议边界都应明确表达。

## L1 Indexer 与 L2 Indexer

聪网生态需要两类索引能力：

| Indexer | 作用 |
| --- | --- |
| BTC L1 Indexer | 解析 BTC 主网上的 UTXO、sat range、Ordinals、Runes、BRC20、ORDX 和普通 BTC 资产 |
| SatoshiNet L2 Indexer | 解析聪网上的 UTXO、ascend、descend、通道、合约、交易执行和资产状态 |

钱包、交易平台和 Agent 需要把 L1 与 L2 的证据串起来，而不是只看一个余额字段：资产从哪个 BTC UTXO 进入通道，哪个 ascend 事件把它映射到聪网，当前在聪网哪个地址或通道中，退出时又对应哪个 descend / L1 输出。

## 面向未来的分布式 Indexer

SAT20 indexer 不是一个中心化 API 服务，而是一套可独立运行、可交叉验证的资产事实计算规则。

在聪网中，L2 indexer 已经集成在聪网节点中。每个运行聪网节点的参与者都可以随节点维护自己的 L2 交易、UTXO、ascend、descend、通道和合约状态视图。因此，L2 indexer 本质上已经随聪网节点网络分布。

L1 indexer 的数据来源是 BTC 主网。聪网 Core Node 在运行时要求配置并依赖自己的 L1 indexer，用来验证 BTC L1 UTXO、资产协议事件、确认状态和跨层交易。因此，即使用户通过公共 API 访问，聪网 Core Node 网络本身也形成了事实上的 L1 indexer 分布式验证结构。

长期看，比特币主网上的多协议资产越重要，越需要更多钱包、交易平台、浏览器、Core Node 和独立基础设施团队运行自己的 L1 indexer，并对同一套资产事实进行交叉验证。

分布式 indexer 的目标不是创造新的共识层，而是让更多节点能独立计算和校验同一套资产事实，降低单点错误、延迟、分叉和数据污染风险。对用户来说，这意味着钱包和 Agent 可以从多个来源交叉验证资产状态；对交易平台来说，这意味着充值、提现和风控可以建立在更稳健的数据基础上。

## 与 AI Agent 的关系

AI Agent 操作资产时，不能只相信钱包界面的余额变化。它需要读取 indexer 证据，并回答：

1. 这个资产来自哪个 L1 UTXO。
2. 这个 UTXO 是否确认，是否被花费。
3. 该资产协议事件是否有效。
4. 该资产是否已经 ascend 到聪网，还是仍在 BTC L1。
5. 通道承诺交易、L1/L2 indexer 和钱包本地状态是否一致。

这就是为什么 indexer 必须进入 SAT20 文档主线：它是 STP 安全操作、交易平台接入、浏览器展示和 AI Agent 验证的共同基础。
