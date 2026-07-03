# EVM 合约

EVM合约是聪网智能合约的一种执行类型。EVM执行Solidity/EVM状态机，聪网UTXO模型负责真实资产来源和资产结算。

EVM合约遵循[智能合约](./)的通用协议。本文只定义EVM合约特有规则。

## 合约类型

EVM合约类型为：

```
ContractTypeEVM
```

EVM合约兼容EVM执行语义、ABI、Solidity开发模型和EVM事件模型，但不采用以太坊账户资产模型。EVM合约内部状态可以维护应用账本，真实资产余额以合约地址UTXO集合为准。

## 地址规则

EVM内部地址保持20字节，以兼容Solidity和ABI。

1. `msg.sender`是20字节EVM地址。
2. `address(this)`是20字节EVM合约地址。
3. event topic中的indexed address按EVM ABI编码。
4. CREATE和CREATE2生成20字节EVM合约地址。

聪网外部合约地址使用：

```
ca/tc + version + ContractTypeEVM + hash
```

EVM合约地址hash为20字节EVM地址。EVM内部20字节地址和聪网外部`ca/tc`地址必须支持无损转换。

chain id、vm version和code hash不放入地址hash：

1. chain id由网络和地址前缀区分。
2. vm version由地址version、type和协议升级规则表达。
3. code hash由部署交易、合约状态和state root承诺表达。

## 部署规则

`CONTRACT_DEPLOY`用于部署EVM合约。

EVM部署payload包含：

1. init code。
2. constructor参数。
3. deployer EVM address。
4. gas limit。
5. 部署nonce。

部署成功后生成：

1. 20字节EVM合约地址。
2. 聪网`ca/tc`合约地址。
3. code hash。
4. 初始storage root。

部署结果必须通过同一区块内的canonical `CONTRACT_RESULT`记录。

## 调用规则

`CONTRACT_INVOKE`用于调用EVM合约。

EVM调用payload包含：

1. calldata。
2. gas limit。
3. call nonce。

调用交易必须输出到被调用合约地址，作为gas/funding输出。被调用合约地址由Call TX输出解析，不写入OP\_RETURN。

EVM `msg.sender`由调用交易最后一个输入的前序输出地址确定，再映射为20字节EVM地址。节点不得从witness公钥推导`msg.sender`。

EVM合约的默认调用表示向合约地址发起一次空calldata调用。输出中的satoshi作为`msg.value`，其他资产仍由聪网资产层和预编译资产接口表达。

EVM calldata直接作为EVM调用输入，不在协议层预定义业务action和参数。合约如果需要读取本次Call TX转入合约地址的资产数量，应通过预编译资产接口查询funding output，而不是要求用户在calldata中重复填写同一经济参数。

## StateDB和执行器

EVM执行器第一阶段基于go-ethereum `core/vm`。

实现要求：

1. 不修改EVM opcode语义。
2. 实现聪网自定义StateDB。
3. StateDB维护storage、code、log和state root。
4. 合约资产由UTXO集合表达，不由EVM account balance表达。

## 资产规则

资产名称在ABI中按字符串编码，使用聪网资产层`AssetName.String()`结果。

satoshi资产名称固定为：

```
::
```

第一阶段支持聪网已识别并能以UTXO表达的资产：

1. satoshi。
2. ORDX资产。
3. Runes资产。
4. BRC20资产。
5. 其他已被聪网资产层识别的资产。

EVM合约内部可以维护ERC20或其他应用层余额。该余额不等同于聪网原生资产余额。需要兑现为聪网资产转移时，合约必须通过资产接口生成Asset Intent，并由`CONTRACT_RESULT`结算。

## 预编译资产接口

EVM不能直接花费UTXO，只能生成Asset Intent。底层资产接口通过预编译合约提供。

预编译合约负责：

1. 查询合约UTXO资产状态。
2. 生成资产转移intent。
3. 参与Result TX确定性验证。

当前资产预编译地址为：

```
0x0000000000000000000000000000000000534E01
```

第一阶段接口：

1. `balanceOf(address owner, string assetName) returns (string)`：查询指定EVM地址对应合约地址当前可用的指定资产余额。
2. `fundingAssetAmount(string assetName) returns (string)`：查询本次Call TX funding output中指定资产的剩余可认领数量。若`assetName`为统一gas资产，返回值会扣除本次调用预留的Result费用后再提供给合约。
3. `fundingSats() returns (uint256)`：查询本次Call TX funding output中的白聪数量。
4. `claimFundingAsset(string assetName, string amount) returns (bool)`：合约明确认领本次funding中的指定资产数量。只有被认领的funding资产进入本次合约业务处理；未认领的多余资产按framework规则退款或保留为非业务资产。
5. `callerAddress() returns (string)`：返回按通用规则解析出的聪网caller地址。
6. `transferAsset(string assetName, string to, string amount, bytes extraData) returns (bool)`：声明一笔资产转移intent。
7. `transferAssets(string[] assetNames, string[] recipients, string[] amounts, bytes[] extraData) returns (bool)`：声明多笔资产转移intent。该接口用于close或批量结算时一次性表达多个接收者和多种资产。
8. `compareAmount(string left, string right) returns (int256)`：按Decimal语义比较两个资产数量字符串。
9. `addAmount`、`subAmount`、`mulAmount`、`divAmount`：按Decimal语义计算资产数量字符串。
10. `uintToAmount(uint256)`、`amountToUintFloor(string)`、`amountToUintCeil(string)`：在整数和资产数量字符串之间转换。

所有资产数量在预编译资产接口中优先使用字符串表达。EVM合约内部可以为了业务计算临时转换为`uint256`，但最终资产转移intent必须回到资产字符串，并由Result TX按资产精度截断或校验。

## `msg.value`和balance

`msg.value`表示本次Call TX转入合约地址的satoshi数量。

`address.balance`返回satoshi余额。`address(this).balance`表示当前合约地址可支配的satoshi总量，该数值由合约地址UTXO集合统计得到。

多资产余额必须通过预编译合约查询。合约storage中的资产记录如果与UTXO统计不一致，Result TX验证以UTXO资产状态和预编译接口为准。

## 合约信息和状态视图接口

为了让钱包、市场和浏览器在不知道具体Solidity源码的情况下展示基础信息，建议EVM合约实现一组轻量只读接口：

```solidity
function contractName() external view returns (string memory);
function contractSubtype() external view returns (string memory);
function managedAssetCount() external view returns (uint256);
function managedAsset(uint256 index) external view returns (string memory);
function managedAssetBalance(uint256 index) external view returns (string memory);
function managedAssetBalance(string calldata assetName) external view returns (string memory);
```

节点查询EVM合约状态时会尝试调用这些接口。没有实现`contractName()`的合约，基础显示名称返回`unknown`。`managedAsset*`接口用于返回合约自己认为正在管理的资产名称和数量；浏览器仍可以同时展示合约地址UTXO中的实际资产余额，两者不要求完全相等，但差异应被视为需要关注的合约状态信息。

合约可以额外实现：

```solidity
function stateView() external view returns (string memory);
```

`stateView()`返回合约自定义JSON字符串，用于展示订单簿、池子、用户份额或其他业务视图。该视图不替代共识状态，只是对合约storage和资产状态的可读投影。

## 部署工具和源码metadata

钱包可以提供Solidity源码编译入口。编译参数不由用户自由选择，而由聪网当前支持的EVM编译配置决定，并展示给用户。当前测试阶段默认配置为：

1. `solcVersion`: `0.8.30`。
2. `evmVersion`: `paris`。
3. optimizer开启，`runs=200`。
4. metadata `bytecodeHash=none`。
5. 只支持单文件源码，不允许import。

部署交易确认后，钱包或部署工具可以把合约地址、Solidity源码、ABI、compiler config、constructor参数和init/runtime code hash提交给L2 indexer的metadata接口。indexer保存metadata用于浏览器、市场和钱包展示；metadata不是共识状态，不能替代链上deploy交易、EVM code hash和state root。

## Gas

EVM保留gas机制。

规则：

1. opcode gas成本沿用geth。
2. 每个部署和调用必须声明gas limit。
3. 执行超过gas limit时结果为out of gas。
4. gas费用由调用方承担。
5. 区块存在EVM gas总上限。
6. gas price第一阶段采用协议固定值。
7. gas费用使用统一gas资产支付。
8. gas费用归出块节点。

默认gas上限参数：

1. 单次deploy/invoke gas上限为`50,000,000`。
2. 单次触发器执行gas上限为`5,000,000`。
3. 单区块EVM执行总gas上限为`1,000,000,000`。

## 触发器

EVM合约可以通过协议预编译合约注册高度触发器。触发器记录在EVM状态中，并参与EVM state root。

高度触发器至少包含：

1. trigger id。
2. 目标合约地址。
3. 触发高度。
4. 触发执行gas limit。
5. 触发时调用的calldata。

出块节点在构造每个区块时必须检查EVM状态中已经到期的触发器。即使候选区块没有普通EVM deploy/invoke交易，只要存在到期触发器，也必须执行触发器并在需要结算时生成canonical `CONTRACT_RESULT`。

验证节点遇到没有同区块EVM deploy/invoke的EVM Result TX时，必须通过Result TX花费的EVM合约UTXO确定合约地址，并基于上一EVM状态、当前区块高度和区块确认时间重放触发器。触发器不存在、未到期、已被移除、gas limit无效或重放结果不一致时，区块无效。

触发器注册和执行必须同时满足：

1. gas limit必须为正数。
2. gas limit不能超过单次触发器执行gas上限。
3. 合约必须有足够gas资金覆盖触发器执行和Result TX打包费用。
4. 区块内所有EVM执行的累计gas不能超过单区块EVM执行总gas上限。

## Result TX和state root

EVM合约不接受外部提交的`CONTRACT_RESULT`进入mempool。

出块节点执行EVM后，根据Asset Intent构造canonical `CONTRACT_RESULT`。验证节点独立重放EVM，并比较Result TX和state root。

EVM state root、模版合约state root和Agent合约state root合成统一contract state root，写入coinbase。

## 关闭规则

EVM合约使用通用`close`语义。deployer发起合约关闭时，EVM执行器会先尝试调用合约的：

```solidity
function close() external returns (bool);
```

合约应在`close()`中通过预编译资产接口为自己管理的资产生成必要的转移intent，例如返还LP、订单、押金或其他有明确归属的资产。`close()`执行完成后，framework再按通用规则处理合约管理资产中的剩余利润，以及合约地址上超出runtime管理记录的非管理资产。

如果EVM合约没有实现`close()`或`close()`失败，节点仍会按协议规则处理Result验证；但作为可公开使用的合约，应实现明确的`close()`，并使用`transferAssets`一次性表达多资产、多接收者的关闭分配。
