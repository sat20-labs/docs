EVM智能合约
====

本文定义聪网上EVM兼容智能合约的第一阶段协议方案。

聪网EVM合约的目标是在聪网UTXO模型上提供尽可能兼容EVM的执行环境。EVM负责执行合约状态机，UTXO负责表达真实资产来源和资产结算，交易是驱动合约状态变化的唯一事件。


合约类型边界
----

聪网上的EVM合约和通道合约是两种不同的合约类型。

通道合约基于RSMC/通道协作模型，核心目标是协调多方签名、通道状态、资产穿越、流动性池、AMM等协议动作。通道合约的资产控制和安全边界来自通道、多签、承诺交易和STP流程。

EVM合约是聪网上独立的虚拟机合约类型。它兼容EVM执行语义、ABI、Solidity开发模型和合约生态，但不照搬以太坊账户资产模型。EVM合约只负责执行状态机逻辑，真实资产由聪网UTXO模型表达和结算。

本文讨论的是聪网EVM合约，不是通道合约的EVM版本，也不是在通道合约内部嵌入EVM。


核心模型
----

1. UTXO是链上资产的唯一来源。
2. EVM合约是状态机。
3. 合约调用由交易驱动，合约触发器由区块环境驱动。
4. 所有节点必须确定性重放EVM执行。
5. EVM不能直接花费UTXO，只能产生资产转移intent。
6. 资产转移intent必须通过canonical Result TX在UTXO层结算。
7. 合约UTXO不通过传统私钥签名解锁，而由EVM执行结果授权花费。
8. 第一阶段采用同区块Result TX结算模型。
9. EVM state root第一阶段放入coinbase交易中作为区块级状态承诺，不修改区块头结构。


地址规则
----

EVM内部地址必须保持20字节，以兼容Solidity、ABI、event log、CREATE和CREATE2。

1. `msg.sender`是20字节EVM地址。
2. `address(this)`是20字节EVM合约地址。
3. event topic中的indexed address按EVM ABI编码。
4. CREATE和CREATE2生成20字节EVM合约地址。

聪网外部合约地址使用新的合约地址格式：

```text
ca + version + type + hash
```

测试网合约地址使用：

```text
tc + version + type + hash
```

地址字段定义：
1. 主网前缀为`ca`。
2. 测试网前缀为`tc`。
3. `version`当前为`1`。
4. `type`表示合约类型，EVM合约使用独立type。
5. `hash`直接使用20字节EVM地址。

EVM内部20字节地址和聪网外部`ca/tc`地址之间必须支持无损转换。

chain id、vm version和code hash不放入地址hash：
1. chain id由网络和地址前缀区分。
2. vm version由地址version、type和协议升级规则表达。
3. code hash由EVM_DEPLOY交易、合约状态和Result TX中的状态承诺表达。


资产规则
----

资产名称在ABI中按字符串编码，使用聪网资产层`AssetName.String()`的结果。

satoshi的资产名称固定为：

```text
::
```

第一阶段支持全部聪网已识别并能以UTXO表达的资产，包括：
1. satoshi，资产名称为`::`。
2. ORDX资产。
3. Runes资产。
4. BRC20资产。
5. 其他已经被聪网资产层识别并能以UTXO表达的资产。

EVM合约内部允许维护应用层资产账本，但真实资产余额必须以合约地址下的UTXO集合为准。


交易类型
----

EVM合约相关交易分为四类：

1. `EVM_DEPLOY`
2. `EVM_INVOKE`
3. `EVM_RESULT`
4. `COINBASE_EVM_STATE_ROOT`


合约触发器
----

EVM合约可以定义内置触发器。触发器不依赖外部Call TX，而是由区块高度、区块时间或其他协议允许的确定性链上条件触发。

触发器用于表达合约自身的自动执行逻辑。例如，vault合约可以定义在某个高度自动释放资产到指定地址。

触发器规则：
1. 触发条件必须完全由链上确定性数据决定。
2. 触发器不得依赖节点本地时间、外部服务、随机数或其他非确定性输入。
3. 触发器执行必须由所有节点确定性重放。
4. 触发器执行可以产生Asset Intent。
5. 触发器产生Asset Intent时，必须通过同一区块内的`EVM_RESULT`结算。
6. 触发器不需要`EVM_INVOKE`，因此没有Call TX gas/funding输入。
7. 触发器的执行费用和Result TX打包费用从合约自身的gas资产UTXO中扣除。
8. 如果合约没有足够gas资产支付触发器执行费用和Result TX打包费用，触发器不得执行。
9. 同一合约在同一区块中既有触发器又有`EVM_INVOKE`时，先按区块交易顺序执行`EVM_INVOKE`，再执行该区块高度下到期的触发器。


EVM_DEPLOY
----

`EVM_DEPLOY`用于部署EVM合约。

`EVM_DEPLOY`的OP_RETURN必须携带：
1. init code。
2. constructor参数。
3. deployer EVM address。
4. gas limit。
5. 部署nonce。

`EVM_DEPLOY`执行成功后必须生成：
1. 20字节EVM合约地址。
2. 聪网`ca/tc`合约地址。
3. code hash。
4. 初始storage root。

每个`EVM_DEPLOY`必须通过`EVM_RESULT`记录部署结果、合约地址和state root。


EVM_INVOKE
----

`EVM_INVOKE`用于调用EVM合约。

`EVM_INVOKE`的OP_RETURN必须携带：
1. calldata。
2. gas limit。
3. call nonce。

`EVM_INVOKE`必须至少有一个输出转入被调用的合约地址，作为gas/funding输出。该输出承担三个作用：
1. 作为Call TX和Result TX之间的UTXO级绑定。
2. 承载本次调用转入合约的资产。
3. 预付合约调用费用和Result TX打包费用。

被调用合约地址不写入`EVM_INVOKE`的OP_RETURN。节点必须通过Call TX中输出到合约地址的输出确定被调用合约。

每个`EVM_INVOKE`只能调用一个EVM合约。一个`EVM_INVOKE`如果包含多个输出到EVM合约地址的输出，则这些输出必须属于同一个合约地址；否则该交易无效。

gas/funding输出在协议层拆分为费用部分和funding部分。费用部分归出块节点，并通过coinbase领取；扣除费用后的剩余部分才进入合约UTXO集合。

如果`EVM_INVOKE`产生资产转移或执行失败并需要退款，必须由同一区块内的`EVM_RESULT`结算。

如果`EVM_INVOKE`执行成功且没有产生资产转移，则不生成`EVM_RESULT`。该调用只需要支付合约调用费用，不需要支付Result TX打包费用。扣除合约调用费用后，gas/funding输出中的剩余资产直接成为合约UTXO，合约后续允许使用。


EVM_RESULT
----

`EVM_RESULT`用于记录EVM执行结果并结算资产转移intent。

`EVM_RESULT`允许批量结算多个`EVM_DEPLOY`、`EVM_INVOKE`和合约触发器。被同一个`EVM_RESULT`批量结算的执行项，必须按协议执行顺序记录。

`EVM_RESULT`必须位于它结算的所有`EVM_DEPLOY`和`EVM_INVOKE`之后，并且必须与它结算的交易出现在同一个区块。

如果`EVM_INVOKE`被某个`EVM_RESULT`结算，该`EVM_INVOKE`转入合约地址的gas/funding输出必须作为该`EVM_RESULT`的输入。

如果一个`EVM_RESULT`批量结算多个`EVM_INVOKE`，这些`EVM_INVOKE`的gas/funding输出都必须作为该`EVM_RESULT`的输入。

如果`EVM_RESULT`结算的是合约触发器，则不要求存在Call TX gas/funding输入。节点必须通过合约状态、触发条件、区块环境和本地EVM重放验证该触发器确实在当前区块可执行。

`EVM_RESULT`的OP_RETURN只承诺最小结果数据。交易本身、Result TX输入输出、本地EVM重放可以推导出的信息，不写入OP_RETURN。

`EVM_RESULT`的OP_RETURN必须包含：
1. 执行状态摘要。
2. 批量结果数量。
3. 可选的错误码或revert reason摘要。

call id规则：
1. `EVM_INVOKE`的call id由invoke txid、合约输出vout/index和该输出对应的contract address生成。
2. `EVM_DEPLOY`的call id由deploy txid和contract address生成。
3. 合约触发器的call id由contract address、trigger id和触发区块高度生成。
4. `EVM_RESULT`不在OP_RETURN中写入call id列表。
5. 节点必须通过`EVM_RESULT`输入中的gas/funding输出反向确定它结算的`EVM_INVOKE`。
6. `EVM_DEPLOY`对应的`EVM_RESULT`必须通过同一区块内的交易顺序和结果数量确定。
7. 合约触发器对应的`EVM_RESULT`必须通过合约状态、触发条件和触发区块高度确定。
8. 批量结果顺序必须和协议执行顺序一致。

以下信息不写入`EVM_RESULT`的OP_RETURN：
1. call id列表。
2. contract address列表。
3. gas used。
4. 执行前state root。
5. 执行后state root。
6. code hash或contract root。
7. intent commitment。
8. asset settlement commitment。
9. logs commitment。

这些信息必须由节点通过以下来源得到：
1. `EVM_RESULT`输入。
2. `EVM_RESULT`输出。
3. 同一区块内被结算的`EVM_DEPLOY`和`EVM_INVOKE`。
4. 本地EVM确定性重放。
5. 节点内部索引器数据库。

完整trace不写入链上，节点必须通过本地重放得到完整执行细节。


COINBASE_EVM_STATE_ROOT
----

第一阶段不修改聪网区块头结构。EVM state root必须放入coinbase交易中，作为区块级状态承诺。

coinbase中的EVM state root表示该区块内所有EVM合约交易执行和结算完成后的最终EVM状态。

节点验证区块时，必须独立重放区块内EVM合约交易，并检查本地计算出的EVM state root是否和coinbase中的承诺一致。

该方案不改变当前80字节区块头结构，不改变区块哈希计算方式，不破坏旧区块头解析逻辑。区块浏览器等外围系统只需要识别coinbase中的EVM state root承诺。


调用数据
----

EVM合约调用数据通过OP_RETURN携带。

数据格式：

```text
OP_RETURN | SAT20_MAGIC_NUMBER | CT_TYPE | CONTENT
```

字段定义：

```text
SAT20_MAGIC_NUMBER      = OP_16
CONTENT_TYPE_EVM_DEPLOY = OP_DATA_31
CONTENT_TYPE_EVM_INVOKE = OP_DATA_32
CONTENT_TYPE_EVM_RESULT = OP_DATA_33
CONTENT                 = 合约内容 / 调用参数 / 调用结果
```

调用参数使用标准ABI编码：

```text
4 bytes methodID + ABI encoded params
```


合约UTXO解锁规则
----

合约地址上的UTXO不通过传统私钥签名解锁。花费合约UTXO时，节点必须验证该花费是否由EVM执行结果授权。

花费合约UTXO必须满足：
1. 当前区块中存在对应的`EVM_DEPLOY`、`EVM_INVOKE`，或存在当前区块高度下可执行的合约触发器。
2. 对应交易调用或部署了该合约，或者对应触发器属于该合约。
3. 如果授权来源是`EVM_INVOKE`，`EVM_RESULT`必须花费对应Call TX转入合约地址的gas/funding输出。
4. 如果授权来源是合约触发器，`EVM_RESULT`不需要花费Call TX gas/funding输出，但必须花费合约自身的gas资产UTXO支付触发器执行费用和Result TX打包费用。
5. 所有节点重放EVM后得到相同的资产转移intent。
6. `EVM_RESULT`只花费EVM授权的合约UTXO。
7. `EVM_RESULT`输出完全匹配EVM执行结果。
8. `EVM_RESULT`携带正确的EVM_RESULT数据。

合约地址本质上是由EVM状态机控制的UTXO集合。


Asset Intent
----

EVM不能直接花费UTXO，只能生成Asset Intent。

Asset Intent包含：
1. call id。
2. intent index。
3. from contract。
4. to address。
5. asset name。
6. amount。
7. extra data。

节点重放EVM后，必须根据Asset Intent生成canonical Result TX。

底层资产接口全部通过预编译合约实现。预编译合约负责：
1. 查询合约UTXO资产状态。
2. 生成资产转移intent。
3. 参与Result TX确定性验证。

预编译接口包括：
1. `assetBalance(contract, assetName)`。
2. `transferAsset(to, assetName, amount)`。
3. `receivedAsset(assetName)`。


Canonical Result TX规则
----

所有节点必须按相同规则构造canonical Result TX。

输入选择规则：
1. 必须首先包含被结算`EVM_INVOKE`转入合约地址的gas/funding输出。
2. 只能选择当前合约地址下的可用UTXO。
3. UTXO按asset name分组。
4. 同一资产内按确认高度、txid、vout排序。
5. 从排序后的UTXO列表头部开始依次选择，直到累计金额足够满足intent和费用。
6. 一旦累计金额足够，必须停止选择更多UTXO。

如果`EVM_RESULT`结算的是合约触发器，则没有`EVM_INVOKE` gas/funding输出。此时输入选择从该合约地址下的可用UTXO开始，并且必须包含足够支付触发器执行费用和Result TX打包费用的gas资产UTXO。

输出顺序规则：
1. 先输出intent指定的目标资产。
2. 同一call产生多个intent时，按intent index排序。
3. 找零输出必须输出回同一个合约地址。
4. 找零输出位于资产输出之后。
5. OP_RETURN输出固定为最后一个输出。

找零规则：
1. 合约UTXO输入总额大于intent总额时，剩余资产必须回到同一个合约地址。
2. 找零不能由区块构造者自由指定。
3. dust规则按聪网现有交易规则处理。

费用规则：
1. 合约调用费用由调用方预付。
2. Result TX打包费用由调用方预付。
3. 调用方必须在调用合约时提供足够gas/funding。
4. gas/funding必须覆盖合约调用费用。
5. 如果该调用需要Result TX，gas/funding还必须覆盖Result TX打包费用。
6. 如果gas/funding不足，该`EVM_INVOKE`无效，不得进入区块。


EVM执行器和StateDB
----

第一阶段基于go-ethereum的`core/vm`实现EVM执行器。

实现要求：
1. 不修改`core/vm`的EVM语义。
2. 必须实现聪网自定义StateDB。
3. StateDB必须维护合约状态、合约日志和状态承诺。
4. 合约资产由UTXO集合表达，不由EVM account balance表达。

EVM balance作为兼容视图存在，但不能绕过聪网UTXO资产账本。

`msg.value`规则：
1. 支持`msg.value`。
2. `msg.value`表示本次Call TX转入合约地址的satoshi数量。
3. satoshi资产名称为`::`。

`address.balance`规则：
1. `address.balance`返回satoshi余额。
2. `address(this).balance`表示当前合约地址可支配的satoshi总量。
3. 该数值由合约地址下的UTXO统计得到。

多资产余额规则：
1. 多资产余额必须通过预编译合约查询。
2. 合约内部允许用storage维护多资产信息。
3. 真实资产余额以预编译合约按合约UTXO集合统计的结果为准。
4. 合约storage中的多资产记录必须和预编译接口统计所有UTXO得到的结果一致。
5. 如果二者不一致，Result TX验证以预编译接口和UTXO资产状态为准。

ERC20余额规则：
1. Solidity合约内部ERC20余额只是合约storage。
2. ERC20余额允许作为应用层账本。
3. ERC20余额不等于聪网原生资产余额。
4. ERC20转账如果需要兑现为聪网资产转移，必须通过预编译合约生成Asset Intent，并由Result TX结算。


Gas和费用
----

EVM必须保留gas机制，防止复杂计算攻击。

Gas规则：
1. EVM opcode gas成本沿用geth。
2. 每个`EVM_DEPLOY`和`EVM_INVOKE`必须声明gas limit。
3. 节点执行超过gas limit时，执行结果为out of gas。
4. gas费用由调用方承担。
5. 区块必须有EVM gas总上限。
6. gas price第一阶段采用协议固定值，不做动态费用市场。
7. gas费用使用一种新的专用资产支付。
8. gas资产名称待定，后续按`AssetName.String()`结果写入协议。
9. gas费用归出块节点。

gas/funding费用拆分为两类：
1. 合约调用费用。
2. Result TX打包费用。

合约调用费用用于支付EVM执行成本。每个`EVM_DEPLOY`和`EVM_INVOKE`都必须支付合约调用费用。该费用使用gas专用资产支付，归出块节点。

Result TX打包费用用于支付`EVM_RESULT`的区块打包成本。只有需要`EVM_RESULT`结算的调用才需要支付Result TX打包费用。该费用使用gas专用资产支付，归出块节点。

gas/funding输出中的费用部分不进入合约资产余额。节点验证合约UTXO集合时，必须先扣除应支付给出块节点的gas费用，扣除后的剩余部分才作为合约UTXO资产。

合约相关交易是特殊交易，不额外使用satoshi支付普通网络费。

出块排序规则：
1. 普通交易先打包。
2. 合约相关交易统一放到普通交易之后。
3. 合约相关交易不和普通satoshi手续费交易混合排序。
4. 合约相关交易只在合约交易集合内部按gas规则排序。

调用合约时，调用方必须提供足够gas资产作为gas/funding。只要调用交易提供了足够gas/funding，矿工即可接受该调用及对应Result TX。

执行成功且没有资产转移的`EVM_INVOKE`不生成Result TX，因此不需要支付Result TX打包费用。扣除合约调用费用后，gas/funding输出中的剩余资产直接成为合约UTXO，合约后续允许使用。


Revert和失败处理
----

1. 如果EVM执行revert，合约storage不更新。
2. revert也是一种EVM_RESULT，必须通过Result TX表达。
3. revert Result TX必须退回除gas以外的其他资产。
4. revert不退gas。
5. out of gas按revert处理。
6. out of gas必须扣除gas费用。
7. 非法调用在mempool阶段拒绝，不得进入区块。
8. 如果区块中包含非法调用，该区块无效。
9. 如果Result TX缺失或退款输出错误，整个区块无效。


Mempool规则
----

mempool必须拒绝以下交易：
1. calldata格式非法的`EVM_DEPLOY`或`EVM_INVOKE`。
2. 没有输出到EVM合约地址的`EVM_INVOKE`。
3. 输出到不存在合约地址的`EVM_INVOKE`。
4. 同一个`EVM_INVOKE`输出到多个不同EVM合约地址的交易。
5. gas limit缺失或超过协议上限的交易。
6. gas/funding不足的交易。
7. gas资产类型不符合协议规定的交易。
8. 无法在本地模拟通过的交易。

mempool保存合法的`EVM_DEPLOY`和`EVM_INVOKE`，但`EVM_RESULT`由出块节点在构造区块时生成或选择，并由全网节点确定性验证。


区块构造规则
----

出块节点构造区块时必须遵守：
1. 先选择普通交易。
2. 再选择合约相关交易。
3. 合约相关交易按gas规则排序。
4. 按区块内顺序执行`EVM_DEPLOY`和`EVM_INVOKE`。
5. 为所有`EVM_DEPLOY`生成`EVM_RESULT`。
6. 为产生资产转移、revert或out of gas的`EVM_INVOKE`生成`EVM_RESULT`。
7. 对执行成功且没有资产转移的`EVM_INVOKE`不生成`EVM_RESULT`。
8. 检查当前区块高度下可执行的合约触发器。
9. 为产生资产转移的合约触发器生成`EVM_RESULT`。
10. 根据确定性规则构造canonical Result TX。
11. 在coinbase中写入最终EVM state root。
12. 在coinbase中领取合约调用费用、触发器执行费用和Result TX打包费用。


区块验证规则
----

节点验证区块时必须执行以下流程：

1. 按区块内交易顺序扫描。
2. 发现`EVM_DEPLOY`时，执行部署逻辑，生成合约地址和初始状态。
3. 发现`EVM_INVOKE`时，从Call TX输出解析被调用合约地址，并执行EVM调用。
4. 执行后得到state diff、logs、gas used和Asset Intent。
5. 如果交易需要`EVM_RESULT`，加入待结算队列。
6. 根据当前区块高度和合约状态检查可执行的合约触发器。
7. 如果触发器需要`EVM_RESULT`，加入待结算队列。
8. 发现`EVM_RESULT`时，根据其输入中的gas/funding输出反向确定被结算的`EVM_INVOKE`。
9. 根据`EVM_RESULT`的批量结果数量、区块交易顺序和待结算队列确定被结算的`EVM_DEPLOY`和合约触发器。
10. 根据协议规则构造canonical Result TX。
11. 比较区块中的Result TX和本地推导结果。
12. 如果不一致，区块无效。
13. 区块扫描结束后，如果仍有未结算的`EVM_DEPLOY`、需要Result TX的`EVM_INVOKE`或需要Result TX的合约触发器，区块无效。
14. 计算最终EVM state root。
15. 检查最终EVM state root是否等于coinbase中的承诺。
16. 如果不一致，区块无效。
17. 计算本区块所有合约交易和触发器应支付的合约调用费用、触发器执行费用和Result TX打包费用。
18. 检查coinbase领取的gas专用资产数量是否等于应支付费用总额。
19. 如果不一致，区块无效。

区块内多个合约调用按交易顺序串行执行。后面的`EVM_INVOKE`允许读取前面EVM交易已经提交的合约状态，但不能读取区块后面尚未执行的状态。

同一个合约在同一区块内被多次调用时必须串行执行。


待确定问题
----

以下细节尚未最终确定：

1. gas专用资产的名称。
2. gas专用资产的发行规则。
3. 固定gas price的具体数值。
4. 上线测试时间