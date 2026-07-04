# EVM 样本合约

聪网 EVM Runtime 已进入公开测试网测试阶段。当前测试网已经部署并验证 EVM 标准样本合约，用于展示 Solidity 应用如何在聪网 EVM Runtime 上运行，并通过聪网原生资产接口完成资产读取、认领和 Result TX 结算。

当前测试网上线的两个 EVM 标准样本合约是：

1. `ConstantProductAMM`
2. `LimitOrderBook`

本文先记录当前样本合约的开发者视角。测试网合约地址、txid、Explorer 链接和 PWA 操作截图需要在后续测试记录中补齐。

样本源码当前位于 [`sat20wallet/sdk/e2e/testdata/contracts/StandardApps.sol`](https://github.com/sat20-labs/sat20wallet/blob/main/sdk/e2e/testdata/contracts/StandardApps.sol)。该源码是测试网标准样本的参考实现，不代表未来主网合约模板只能采用这两个业务形态。

## 当前样本

| 样本 | 类型 | 验证重点 |
| --- | --- | --- |
| `ConstantProductAMM` | Solidity AMM 样本 | 添加流动性、swap、移除流动性、资产预编译接口、ABI calldata、Result TX |
| `LimitOrderBook` | Solidity 限价单样本 | 创建订单、填单、取消订单、订单状态视图、资产预编译接口、ABI calldata、Result TX |

如果测试网后续切换样本合约，应同步更新本页和 [EVM 开发者预览](evm-quickstart.md)。

## ConstantProductAMM

`ConstantProductAMM` 是 EVM Runtime 上的常数乘积 AMM 样本合约。它用 Solidity 实现 AMM 状态机，同时通过聪网资产预编译接口处理真实资产输入和输出。

核心接口包括：

| 接口 | 用途 |
| --- | --- |
| `addLiquidity(uint256 minLiquidity)` | 添加资产和聪流动性，铸造内部 LP 份额 |
| `swapSatForAsset(string minAssetOut)` | 输入聪，输出目标资产 |
| `swapAssetForSat(uint256 minSatOut)` | 输入目标资产，输出聪 |
| `removeLiquidity(uint256 liquidity, string minAssetOut, uint256 minSatOut)` | 移除 LP 份额，取回资产和聪 |
| `liquidityOfCaller()` | 查询当前调用者 LP 份额 |
| `reserves()` | 查询池子资产、资产储备、聪储备和总 LP |
| `quoteSatForAsset(uint256 satIn)` | 估算输入聪可获得的资产 |
| `quoteAssetForSat(string assetIn)` | 估算输入资产可获得的聪 |
| `quoteAddLiquidity(string assetIn, uint256 satIn)` | 估算添加流动性可获得的 LP 份额 |
| `quoteRemoveLiquidity(uint256 liquidity)` | 估算移除流动性可获得的资产和聪 |

测试目标：

1. 部署 Solidity AMM 合约，构造参数指定池子管理的资产名称。
2. 调用时由 PWA 根据函数签名和参数生成 ABI calldata。
3. 通过 funding output 向合约输入资产和聪；这些经济输入不由 Solidity 参数重复决定。
4. 合约调用 `fundingAssetAmount`、`fundingSats` 和 `claimFundingAsset` 识别并认领输入资产。
5. 合约更新储备和 LP 状态。
6. Swap 时合约通过 `transferAsset` 生成资产转移 intent。
7. 聪网通过 canonical Result TX 完成输出资产结算。
8. `reserves()` 和 Explorer / Indexer 展示的合约资产状态保持可解释一致。

`ConstantProductAMM` 与模板 AMM 合约用途相似，但它验证的是 Solidity / EVM 路径：开发者可以用 EVM 合约表达 AMM 逻辑，资产结算仍由聪网 UTXO 资产层和 Result TX 负责。

## LimitOrderBook

`LimitOrderBook` 是 EVM Runtime 上的限价单样本合约。它用 Solidity 维护订单状态，并通过聪网资产预编译接口处理挂单、填单、取消和资产结算。

核心接口包括：

| 接口 | 用途 |
| --- | --- |
| `createOrder(string sellAsset, string buyAsset, string buyAmount)` | 创建订单，卖出资产来自本次 funding output |
| `fillOrder(uint256 orderId)` | 填充订单，支付资产来自本次 funding output |
| `cancelOrder(uint256 orderId)` | Maker 取消未完成订单并取回剩余卖出资产 |
| `activeOrderCount()` | 查询活跃订单数量 |
| `activeOrderId(uint256 activeIndex)` | 按活跃索引查询订单 ID |
| `orderInfo(uint256 orderId)` | 查询订单状态 |
| `stateView()` | 返回订单簿 JSON 视图 |
| `quoteFillOrder(uint256 orderId, string paidIn)` | 估算填单可获得的卖出资产数量 |

核心流程：

1. Maker 创建订单，把卖出资产转入合约地址。
2. 调用时由 PWA 根据 `createOrder(string,string,string)` 生成 ABI calldata；calldata 中的 `buyAmount` 是订单期望收到的买入资产数量，卖出资产数量来自 funding output。
3. 合约读取 funding output，确认卖出资产数量。
4. 合约记录订单状态，包括 maker、接收地址、卖出资产、买入资产、剩余卖出数量和剩余买入数量。
5. Taker 调用 `fillOrder(uint256)` 并通过 funding output 转入订单要求的买入资产。
6. 合约计算成交比例，更新剩余订单状态。
7. 合约通过 `transferAsset` 把支付资产转给 maker，把卖出资产转给 taker。
8. Maker 可以取消未完成订单，合约通过 Result TX 退回剩余卖出资产。

测试目标：

1. 验证 EVM 合约可以维护订单簿状态。
2. 验证挂单资产由 funding output 提供，而不是由 calldata 中的金额决定。
3. 验证填单资产由 funding output 提供。
4. 验证部分成交、完全成交和取消订单都能通过 Result TX 结算。
5. 验证订单状态视图、钱包余额和 Explorer / Indexer 证据一致。

`LimitOrderBook` 与模板限价单合约用途相似，但它验证的是 Solidity / EVM 路径：订单簿状态由 EVM storage 表达，资产转移仍由聪网原生资产接口和 canonical Result TX 结算。

## 预编译资产接口

EVM 合约不能直接花费 UTXO。它通过聪网资产预编译接口表达资产读取和转移意图。

常用接口包括：

| 接口 | 用途 |
| --- | --- |
| `balanceOf(address,string)` | 查询 EVM 地址对应合约地址的指定资产余额 |
| `fundingAssetAmount(string)` | 查询本次 Call TX funding output 中的指定资产数量 |
| `claimFundingAsset(string,string)` | 认领本次 funding 中的指定资产，使其进入合约业务处理 |
| `fundingSats()` | 查询本次 Call TX 转入合约地址的聪数量 |
| `callerAddress()` | 查询调用者在聪网中的接收地址，用于退款和资产归属 |
| `transferAsset(string,string,string,bytes)` | 声明一笔资产转移 intent |
| `transferAssets(string[],string[],string[],bytes[])` | 一次声明多笔资产转移 intent |
| `compareAmount(string,string)` | 按资产 Decimal 语义比较数量 |

完整规则见 [EVM 合约](../protocol/contracts/evm.md)。

## 测试网操作路径

当前推荐路径：

1. 打开 [SAT20 PWA Wallet](https://sat20.org/pwa/?install=1)。
2. 确认连接聪网测试网。
3. 在 `工具` 首页领取测试 GAS。
4. 进入 PWA `工具 -> 智能合约` 中的 EVM 合约测试或部署工具。
5. 使用 Solidity 源码编译入口，或使用 PWA 提供的标准样本入口，准备 `ConstantProductAMM` 或 `LimitOrderBook` 的 init code。
6. 部署合约，并等待 Deploy TX 和同区块 Result TX。
7. 调用样本接口前，先填写函数签名、参数、sats、funding assets 和 gas limit，点击生成 calldata 并完成 estimate。
8. 确认 calldata 与当前参数一致后签名广播。
9. 在钱包、工具页或 Explorer 中查看 Invoke TX、Result TX、状态视图和资产变化。

如果 PWA 暂未对普通用户开放完整源码部署体验，可以先使用 PWA 提供的标准样本入口。CLI、RPC、示例仓库和更完整的 Solidity 开发者流程仍处于公开测试网迭代阶段。

## 验证清单

每个 EVM 样本都应能给出：

1. Deploy TX。
2. 合约地址。
3. Invoke TX。
4. Result TX，如果该调用产生资产转移、退款、revert 或 out of gas。
5. 合约状态变化。
6. contract state root 所在区块。
7. 合约 metadata，包括源码、ABI、compiler config 和 code hash。
8. calldata 生成记录，以及本次调用的 sats、funding assets 和 gas limit。

## 限制

1. 当前为测试网样本，不代表主网开放。
2. 测试网参数、工具入口和样本合约可能调整。
3. EVM 内部余额不等同于聪网原生资产余额。
4. 函数参数不应重复表达已经由 funding output 表达的经济输入。
5. 真正的资产转移必须通过 Result TX 验证。
6. Solidity 合约必须遵守聪网 UTXO 资产模型和预编译资产接口规则。

**页面状态：开发中（In Development）**
