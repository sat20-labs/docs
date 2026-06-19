# EVM 开发者预览

本文是面向 Solidity / EVM 开发者的预览入口。EVM Runtime、RPC、Chain ID、Faucet、示例仓库和 Explorer 验证流程稳定后，本页会升级为可执行 Quickstart。

## 目标

开发者预览阶段需要明确：

1. EVM Runtime 当前支持范围。
2. SatoshiNet UTXO 原生资产模型如何与 EVM 语义组合。
3. RPC、ABI、Event、Result TX 和合约状态的边界。
4. 工具链、示例仓库和测试网入口何时进入公开可执行状态。

## 升级为 Quickstart 前需要补齐

| 项目 | 内容 |
| --- | --- |
| 环境要求 | Node.js、Foundry / Hardhat、钱包、测试 GAS |
| 当前支持版本 | EVM Runtime、RPC、Solidity 版本 |
| 网络参数 | RPC、Chain ID、Explorer、Faucet |
| 示例仓库 | 最小 Solidity 合约和部署脚本 |
| 命令行步骤 | install、compile、deploy、invoke |
| 预期输出 | 合约地址、txid、Result TX、状态变化 |
| 验证方式 | Explorer、L2 Indexer、合约状态 |
| 常见错误 | GAS 不足、RPC 不匹配、合约地址错误、Result TX 未生成 |
| 生产注意事项 | 主网 GAS、合约审计、权限、升级策略 |

## 当前参考

- [智能合约协议](../protocol/contracts/readme.md)
- [EVM 合约](../protocol/contracts/evm.md)
- [智能合约与 GAS](../learn/smart-contracts-and-gas.md)

**页面状态：开发中（In Development）**
