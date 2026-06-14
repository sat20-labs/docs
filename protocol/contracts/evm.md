EVM合约
====

EVM合约是聪网智能合约的一种执行类型。EVM执行Solidity/EVM状态机，聪网UTXO模型负责真实资产来源和资产结算。

EVM合约遵循[智能合约](readme.md)的通用协议。本文只定义EVM合约特有规则。


合约类型
----

EVM合约类型为：

```text
ContractTypeEVM
```

EVM合约兼容EVM执行语义、ABI、Solidity开发模型和EVM事件模型，但不采用以太坊账户资产模型。EVM合约内部状态可以维护应用账本，真实资产余额以合约地址UTXO集合为准。


地址规则
----

EVM内部地址保持20字节，以兼容Solidity和ABI。

1. `msg.sender`是20字节EVM地址。
2. `address(this)`是20字节EVM合约地址。
3. event topic中的indexed address按EVM ABI编码。
4. CREATE和CREATE2生成20字节EVM合约地址。

聪网外部合约地址使用：

```text
ca/tc + version + ContractTypeEVM + hash
```

EVM合约地址hash为20字节EVM地址。EVM内部20字节地址和聪网外部`ca/tc`地址必须支持无损转换。

chain id、vm version和code hash不放入地址hash：

1. chain id由网络和地址前缀区分。
2. vm version由地址version、type和协议升级规则表达。
3. code hash由部署交易、合约状态和state root承诺表达。


部署规则
----

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


调用规则
----

`CONTRACT_INVOKE`用于调用EVM合约。

EVM调用payload包含：

1. calldata。
2. gas limit。
3. call nonce。

调用交易必须输出到被调用合约地址，作为gas/funding输出。被调用合约地址由Call TX输出解析，不写入OP_RETURN。

EVM `msg.sender`由调用交易最后一个输入的前序输出地址确定，再映射为20字节EVM地址。节点不得从witness公钥推导`msg.sender`。

EVM合约的默认调用表示向合约地址发起一次空calldata调用。输出中的satoshi作为`msg.value`，其他资产仍由聪网资产层和预编译资产接口表达。


StateDB和执行器
----

EVM执行器第一阶段基于go-ethereum `core/vm`。

实现要求：

1. 不修改EVM opcode语义。
2. 实现聪网自定义StateDB。
3. StateDB维护storage、code、log和state root。
4. 合约资产由UTXO集合表达，不由EVM account balance表达。


资产规则
----

资产名称在ABI中按字符串编码，使用聪网资产层`AssetName.String()`结果。

satoshi资产名称固定为：

```text
::
```

第一阶段支持聪网已识别并能以UTXO表达的资产：

1. satoshi。
2. ORDX资产。
3. Runes资产。
4. BRC20资产。
5. 其他已被聪网资产层识别的资产。

EVM合约内部可以维护ERC20或其他应用层余额。该余额不等同于聪网原生资产余额。需要兑现为聪网资产转移时，合约必须通过资产接口生成Asset Intent，并由`CONTRACT_RESULT`结算。


预编译资产接口
----

EVM不能直接花费UTXO，只能生成Asset Intent。底层资产接口通过预编译合约提供。

预编译合约负责：

1. 查询合约UTXO资产状态。
2. 生成资产转移intent。
3. 参与Result TX确定性验证。

第一阶段接口：

1. `assetBalance(contract, assetName)`
2. `transferAsset(to, assetName, amount)`
3. `receivedAsset(assetName)`


`msg.value`和balance
----

`msg.value`表示本次Call TX转入合约地址的satoshi数量。

`address.balance`返回satoshi余额。`address(this).balance`表示当前合约地址可支配的satoshi总量，该数值由合约地址UTXO集合统计得到。

多资产余额必须通过预编译合约查询。合约storage中的资产记录如果与UTXO统计不一致，Result TX验证以UTXO资产状态和预编译接口为准。


Gas
----

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


触发器
----

EVM合约可以通过协议预编译合约注册高度触发器。触发器记录在EVM状态中，并参与EVM state root。

高度触发器至少包含：

1. trigger id。
2. 目标合约地址。
3. 触发高度。
4. 触发执行gas limit。
5. 触发时调用的calldata。

出块节点在构造每个区块时必须检查EVM状态中已经到期的触发器。即使候选区块没有普通EVM deploy/invoke交易，只要存在到期触发器，也必须执行触发器并在需要结算时生成canonical `CONTRACT_RESULT`。

验证节点遇到没有同区块EVM deploy/invoke的EVM Result TX时，必须通过Result TX花费的EVM合约UTXO确定合约地址，并基于上一EVM状态、当前区块高度和区块确认时间重放触发器。触发器不存在、未到期、已被移除、gas limit无效或重放结果不一致时，区块无效。


Result TX和state root
----

EVM合约不接受外部提交的`CONTRACT_RESULT`进入mempool。

出块节点执行EVM后，根据Asset Intent构造canonical `CONTRACT_RESULT`。验证节点独立重放EVM，并比较Result TX和state root。

EVM state root、模版合约state root和Agent合约state root合成统一contract state root，写入coinbase。
