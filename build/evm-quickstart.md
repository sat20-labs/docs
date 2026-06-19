# EVM Quickstart：部署第一个聪网合约

本文是面向 Solidity / EVM 开发者的入口页。当前先定义可执行 Quickstart 应包含的内容；待 EVM Runtime、RPC、Chain ID、Faucet 和工具链稳定后补充命令行步骤。

## 目标

开发者应能在测试网上完成：

1. 配置聪网 EVM RPC。
2. 获取测试 GAS。
3. 编译一个 Solidity 合约。
4. 部署合约。
5. 调用合约。
6. 在 Explorer 中验证部署和调用结果。

## Quickstart 应包含

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
