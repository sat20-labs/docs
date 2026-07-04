# 合约模板目录

本文整理聪网智能合约相关模板、运行时和测试网入口。更详细的协议规则见 [智能合约协议](../protocol/contracts/readme.md)。

## 当前状态矩阵

| 类型 | 状态 | 测试网入口 | 说明 |
| --- | --- | --- | --- |
| Agent / Prediction 合约 | 已实现 / 测试中 | [Prediction 合约测试](../use/prediction-contract.md) | 当前公开测试网优先验证场景 |
| 模板合约：AMM | 已实现 / 测试网迭代 | PWA `工具 -> 智能合约`，[部署 AMM 池](amm-pool-quickstart.md) | 智能合约模板测试能力，不是市场 AMM |
| 模板合约：限价单 | 已实现 / 测试网迭代 | PWA `工具 -> 智能合约`，[部署限价单模块](limit-order-quickstart.md) | 智能合约模板测试能力，不是市场限价单 |
| 模板合约：资产兑换 | 已实现 / 测试网迭代 | 待补充 | 面向固定规则资产兑换场景 |
| EVM Runtime | 已实现 / 测试网迭代 | [EVM 开发者预览](evm-quickstart.md) | 复用 Solidity / EVM 开发生态；调用使用 ABI calldata，资产结算仍走聪网 UTXO 模型 |
| EVM 样本：ConstantProductAMM | 已实现 / 测试中 | PWA `工具 -> 智能合约`，[EVM 样本合约](evm-sample-contracts.md) | Solidity AMM 标准样本，不是市场 AMM |
| EVM 样本：LimitOrderBook | 已实现 / 测试中 | PWA `工具 -> 智能合约`，[EVM 样本合约](evm-sample-contracts.md) | Solidity 限价单标准样本，不是市场限价单 |

## 模板文档应包含

每个模板合约后续应补齐：

1. 合约类型和模板名称。
2. 部署参数。
3. 调用接口。
4. 输入资产规则。
5. Result TX 输出规则。
6. 权限边界。
7. 费用和 GAS。
8. Explorer / Indexer 验证方法。
9. 测试网合约地址或示例 txid。
10. 已知限制。

## 当前优先级

1. Prediction 合约：补齐用户测试、部署者 Quickstart 和测试网证据。
2. AMM 模板合约：补齐部署、swap、add liquidity、remove liquidity 和验证流程。
3. 限价单模板合约：补齐挂单、成交、取消和 Result TX 验证流程。
4. EVM 样本合约：补齐 `ConstantProductAMM` 和 `LimitOrderBook` 的测试网地址、txid、calldata 生成记录和 Explorer 验证记录。
5. EVM Runtime：补齐 RPC、Chain ID、示例仓库、Solidity 部署流程、estimate 流程和 ABI calldata 调用流程。

**页面状态：规划中（Planning）**
