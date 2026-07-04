# EVM 开发者预览

本文是面向 Solidity / EVM 开发者的测试网预览入口。聪网智能合约框架已经完成开发并进入公开测试网，EVM Runtime、模板合约和 Agent 合约正在围绕钱包、Explorer、Indexer、RPC 和开发者工具持续迭代。

当前测试网已经开放 Agent / Prediction 合约体验，并上线了两个 EVM 标准样本合约：`ConstantProductAMM` 和 `LimitOrderBook`。EVM 开发者可以先通过样本合约理解 Solidity 合约如何与聪网 UTXO 资产模型、ABI calldata、Result TX 和 contract state root 组合。

## 当前可做

1. 通过 [SAT20 PWA Wallet](https://sat20.org/pwa/?install=1) 进入测试网。
2. 在 PWA `工具` 首页领取测试 GAS。
3. 在 `市场 -> Prediction` 体验 Agent 合约调用。
4. 在 PWA `工具 -> 智能合约` 体验或部署 `ConstantProductAMM`、`LimitOrderBook` EVM 样本合约。
5. 阅读智能合约协议、EVM 合约规则和资产预编译接口。
6. 准备 Solidity 合约迁移时需要处理的 UTXO 资产模型差异。

## EVM 开发者需要理解

1. EVM 执行 Solidity / EVM 状态机，但聪网真实资产来源和结算由 UTXO 模型表达。
2. 合约内部 ERC20 或应用账本不等于聪网原生资产余额。
3. EVM invoke 的 payload 是 Solidity ABI calldata；PWA 可以根据函数签名和参数生成 calldata，也可以接受原始 calldata。
4. 资产和聪的业务输入来自转入合约地址的 funding output，不应在 Solidity 参数中重复填写同一经济数量；测试 GAS / Result fee 用于支付执行和结果交易费用。
5. 合约要转移聪网原生资产，需要通过资产预编译接口生成 Asset Intent，再由 canonical Result TX 结算。
6. EVM gas unit 和测试 GAS 资产不是同一个单位，当前由协议参数换算。
7. 合约状态参与 contract state root。
8. 部署和调用都需要测试 GAS。
9. 测试网期间，工具链和 RPC 可能调整。

## PWA 交互模型

部署 EVM 合约时，PWA 从节点读取当前 compiler config，使用固定编译配置生成 init code。当前测试阶段默认配置为 `solc 0.8.30`、`evmVersion=paris`、optimizer `runs=200`、metadata `bytecodeHash=none`，并以单文件 Solidity 源码为主。有效 Deploy TX 必须在同一区块内生成 canonical Result TX，源码、ABI、compiler config 和 code hash 可以作为 metadata 提交给 L2 indexer，用于钱包、Explorer 和工具展示。

调用 EVM 合约时，PWA 的基本流程是：

1. 选择合约地址。
2. 填写函数签名、参数、sats、funding assets 和 gas limit，或直接填写 `calldataHex`。
3. 点击生成 calldata，并用节点的 estimate 接口检查 calldata、funding 和 gas limit 是否可接受。
4. 在签名前确认 calldata 与当前 JSON 参数一致。
5. 签名并广播 Invoke TX。
6. 如果本次执行产生资产转移、退款、revert 或 out of gas，检查同区块 canonical Result TX。

示例调用 JSON：

```json
{
  "function": "swapAssetForSat(uint256)",
  "args": ["1000"],
  "sats": "0",
  "funding": [
    {
      "assetName": "brc20:f:ooxx",
      "amount": "100000"
    }
  ],
  "gasLimit": 5000000
}
```

这里的 `args` 只用于 ABI 编码，`funding` 才是本次调用真正转入合约地址的资产输入。合约应通过 `fundingAssetAmount`、`fundingSats` 和 `claimFundingAsset` 读取并认领这些输入。

## 待公开参数

| 项目 | 内容 |
| --- | --- |
| RPC | 测试网 EVM RPC / 合约 RPC 入口 |
| Chain ID | 测试网 Chain ID |
| 示例仓库 | 最小 Solidity 合约、部署脚本和调用脚本 |
| CLI 流程 | install、compile、deploy、generate calldata、estimate、invoke |
| Explorer 验证 | Deploy TX、Invoke TX、Result TX、event、state root |
| 钱包接口 | PWA / Wallet SDK 合约部署、调用、calldata 生成和 estimate 接口 |
| 常见错误 | GAS 不足、RPC 不匹配、合约地址错误、Result TX 未生成 |

## 当前参考

- [智能合约协议](../protocol/contracts/readme.md)
- [EVM 合约](../protocol/contracts/evm.md)
- [EVM 样本合约](evm-sample-contracts.md)
- [智能合约与 GAS](../learn/smart-contracts-and-gas.md)
- [Prediction 合约 Quickstart](prediction-contract-quickstart.md)

**页面状态：开发中（In Development）**
