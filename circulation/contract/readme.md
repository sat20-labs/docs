智能合约
====

本文定义聪网智能合约的通用协议。具体合约类型的差异见：

1. [模版合约](template.md)
2. [EVM合约](evm.md)
3. [自然语言合约](agent.md)


协议边界
----

聪网智能合约是运行在聪网上的可编程共识状态机。合约状态由聪网节点维护，资产来源和资产结算由聪网UTXO模型表达。

智能合约不同于通道合约。通道合约基于RSMC、通道状态、承诺交易、多方签名和STP流程；智能合约基于链上交易、合约VM状态、canonical `CONTRACT_RESULT`和区块级state root。智能合约发起的资产转移不需要私钥签名，必须由VM执行结果授权。


合约类型
----

聪网智能合约第一阶段包含三类：

1. 模版合约：由聪网节点源码内置的Go runtime执行，对应`ContractTypeTemplate`。
2. EVM合约：由EVM执行器执行，对应`ContractTypeEVM`。
3. 自然语言合约：由AI Agent支持的自然语言协议合约，对应`ContractTypeAgent`，第一阶段优先支持预测型Agent合约，以单CoreNode Agent模式进入聪网合约结果流程。


核心模型
----

1. UTXO是链上资产的唯一来源。
2. VM是合约状态机。
3. `CONTRACT_DEPLOY`创建合约。
4. `CONTRACT_INVOKE`调用合约。
5. `CONTRACT_RESULT`结算VM产生的资产转移。
6. `COINBASE_CONTRACT_STATE_ROOT`在coinbase中承诺区块执行后的合约state root。
7. 所有节点必须确定性重放合约执行。
8. 合约UTXO不通过传统私钥签名解锁，而由VM执行结果授权花费。


地址规则
----

主网合约地址格式：

```text
ca + version + type + hash
```

测试网合约地址格式：

```text
tc + version + type + hash
```

字段定义：

1. `ca`为主网合约地址前缀。
2. `tc`为测试网合约地址前缀。
3. `version`当前为`1`。
4. `type`表示合约类型。
5. `hash`由合约类型定义长度和计算方式。


交易类型
----

合约相关交易分为四类：

1. `CONTRACT_DEPLOY`
2. `CONTRACT_INVOKE`
3. `CONTRACT_RESULT`
4. `COINBASE_CONTRACT_STATE_ROOT`

合约调用数据通过OP_RETURN携带：

```text
OP_RETURN | SAT20_MAGIC_NUMBER | CONTENT_TYPE | CONTENT
```

当前内容类型：

```text
CONTENT_TYPE_CONTRACT_DEPLOY     = OP_DATA_31
CONTENT_TYPE_CONTRACT_INVOKE     = OP_DATA_32
CONTENT_TYPE_CONTRACT_RESULT     = OP_DATA_33
CONTENT_TYPE_CONTRACT_STATE_ROOT = OP_DATA_34
```


CONTRACT_DEPLOY
----

`CONTRACT_DEPLOY`用于部署合约。

部署交易必须包含合约类型、合约内容、版本、deployer、随机值和gas limit。不同合约类型可以定义自己的部署payload，但必须能确定性生成合约地址和初始状态。

每个有效部署都必须在同一区块内由canonical `CONTRACT_RESULT`记录部署结果和state root。


CONTRACT_INVOKE
----

`CONTRACT_INVOKE`用于调用合约。

调用交易必须至少有一个输出转入被调用合约地址，作为gas/funding输出。该输出用于：

1. 绑定Call TX和Result TX。
2. 承载本次调用转入合约的资产。
3. 预付合约调用费用。
4. 在需要结算时作为`CONTRACT_RESULT`输入。

被调用合约地址不写入OP_RETURN。节点必须通过Call TX中输出到合约地址的输出确定被调用合约。

每个`CONTRACT_INVOKE`只能调用一个合约。如果交易中存在多个输出到合约地址的输出，这些输出必须属于同一个合约地址。

调用发起者身份由调用交易最后一个输入对应的前序输出地址解析得到。共识路径不使用witness中的公钥、签名公钥或其他可替换字段作为caller/invoker身份来源；如果最后一个输入的前序输出不可获得或无法解析地址，调用无效。


CONTRACT_RESULT
----

`CONTRACT_RESULT`用于记录VM执行结果并结算资产转移。

规则：

1. `CONTRACT_RESULT`由出块节点构造，外部提交的`CONTRACT_RESULT`不进入mempool。
2. `CONTRACT_RESULT`必须位于它结算的`CONTRACT_DEPLOY`和`CONTRACT_INVOKE`之后。
3. 普通部署和调用的`CONTRACT_RESULT`必须与它结算的交易出现在同一区块。
4. 如果结算`CONTRACT_INVOKE`，对应Call TX转入合约地址的gas/funding输出必须作为Result TX输入。
5. Result TX输出必须与节点本地重放得到的资产转移结果一致。
6. Result TX允许批量结算多个执行项，批量顺序必须与协议执行顺序一致。
7. 注册触发器到期后可以在没有同区块普通合约交易的情况下产生`CONTRACT_RESULT`。验证节点必须通过Result TX花费的合约UTXO识别合约类型和合约地址，并基于上一状态、当前区块高度和确认时间重放到期触发器；无法证明触发器真实存在、已经到期且仍有效的孤立Result TX无效。

`CONTRACT_RESULT`的OP_RETURN只写入执行状态摘要和结果数量。call id、合约地址、输入输出、完整trace和资产转移明细由区块交易、本地重放和节点索引器推导。


State Root
----

合约state root写入coinbase交易，不修改区块头结构。

区块内可以同时包含模版合约、EVM合约和Agent合约的deploy/invoke/result。当前执行顺序为：

1. 模版合约交易执行和Result TX生成。
2. EVM合约交易执行和Result TX生成。
3. Agent合约交易执行和Result TX生成。
4. 将模版合约state root、EVM合约state root和Agent合约state root合成统一的contract state root。
5. 在coinbase中写入最终contract state root。


Gas和费用
----

智能合约使用统一的gas资产支付费用。

费用类型：

1. 合约调用费用。
2. VM执行费用。
3. Result TX打包费用。
4. 触发器执行费用。

费用规则：

1. gas费用由调用方或合约自身承担。
2. gas price第一阶段采用协议固定值。
3. gas费用归出块节点。
4. gas/funding输出中的费用部分不进入合约资产余额。
5. 执行成功且没有资产转移的调用可以不生成Result TX。
6. 需要资产转移、退款、revert或out of gas的调用必须生成Result TX。


Canonical Result TX
----

所有节点必须按相同规则构造和验证canonical Result TX。

输入选择规则：

1. 优先包含被结算`CONTRACT_INVOKE`转入合约地址的gas/funding输出。
2. 只选择当前合约地址下的可用UTXO。
3. UTXO按资产名称分组。
4. 同一资产内按确认高度、txid、vout排序。
5. 从排序后的UTXO列表头部开始选择，直到满足资产转移和费用需求。
6. 累计金额足够后停止选择。

输出规则：

1. 先输出VM结果指定的资产转移。
2. 同一执行项产生多个输出时，按VM定义的顺序输出。
3. 找零输出回同一个合约地址。
4. 找零输出位于资产输出之后。
5. OP_RETURN输出位于最后。


区块构造和验证
----

出块节点构造区块时：

1. 选择普通交易。
2. 选择合约相关交易。
3. 按区块内顺序执行合约部署和调用。
4. 检查已注册且在当前区块到期的触发器，即使本区块没有其他合约交易，也必须主动执行到期触发器。
5. 为需要结算的执行项生成canonical Result TX。
6. 计算最终contract state root。
7. 在coinbase中写入contract state root并领取gas费用。

验证节点验证区块时：

1. 独立解析区块内合约交易。
2. 按协议顺序重放合约执行。
3. 对没有同区块deploy/invoke的Result TX，根据其输入花费的合约UTXO确定合约类型，并重放对应到期触发器。
4. 构造本地canonical Result TX。
5. 比较区块中的Result TX和本地推导结果。
6. 计算本地contract state root。
7. 检查coinbase中的state root承诺。
8. 检查coinbase领取的gas费用。

任一检查不一致，区块无效。


测试网集成检查项
----

测试网启用合约前，节点配置必须至少确认：

1. 合约解析、区块验证和出块侧Result Builder全部开启，并使用相同网络参数和合约地址前缀。
2. coinbase必须写入统一contract state root，验证节点必须检查state root承诺。
3. EVM触发器扫描必须在每个候选区块运行，不能只在区块包含普通合约交易时运行。
4. Agent合约必须配置CoreNode地址、公钥、Agent收款地址、bootstrap收款地址和链参数。
5. Agent `confirm`必须携带CoreNode公钥和签名，节点必须验证公钥、地址和签名。
6. caller/invoker身份解析必须依赖最后一个输入的前序输出地址，节点的UTXO视图必须能提供该前序输出脚本。
7. mempool必须拒绝外部提交的`CONTRACT_RESULT`，Result TX只允许由出块流程插入候选区块。
8. 本地测试必须覆盖deploy、invoke、result-only trigger、Agent ready/confirm、EVM state root、Template state root和混合区块state root。
9. 上线前需要固定gas参数、区块gas上限、合约Result打包费和触发器打包费。
10. 节点、钱包、区块浏览器、资产浏览器和市场必须使用同一套合约交易解析和状态查询字段。


钱包、浏览器和市场接口契约
----

钱包、区块浏览器、资产浏览器和市场集成合约功能时，至少需要共享以下接口语义：

1. 合约部署接口：返回deploy txid、合约类型、合约地址、deployer、payload hash、初始状态和同区块Result状态。
2. 合约调用接口：构造`CONTRACT_INVOKE`，必须包含转入合约地址的gas/funding输出，并展示由最后输入前序输出解析得到的caller/invoker。
3. 合约结果查询接口：按txid、contract address、call id或trigger id查询canonical Result TX、状态、资产转移、gas费用和错误信息。
4. 合约状态查询接口：按合约地址查询合约类型、当前状态、state root、最近更新时间、余额和类型特有状态。
5. EVM接口：提供EVM地址和聪网合约地址互转、ABI calldata构造、event/log查询、EVM storage/code hash查询和触发器查询。
6. Agent接口：提供预测合约deploy/ready/bet/confirm状态、投注聚合、候选结果、确认材料、CoreNode签名和结算/退款结果查询。
7. 资产接口：按合约地址查询全部UTXO资产余额，并区分合约资金池、gas/funding输入、Result输出和找零输出。
8. 市场接口：市场只展示已经进入`Ready`或类型定义可公开展示状态的合约；涉及投注、购买或资产转移时，必须从节点查询最新状态和余额后构造交易。

这些接口返回的交易、状态和资产结果必须能追溯到链上交易、canonical Result TX和区块state root，不能只依赖前端本地推断。


索引器落库和查询要求
----

索引器必须为合约功能建立可查询的链上视图，至少包括：

1. 合约部署表：contract address、contract type、deploy txid、deployer、payload、payload hash、创建高度、创建时间和初始Result状态。
2. 合约调用表：invoke txid、contract address、caller/invoker地址、action、payload、gas/funding输出、确认高度和执行状态。
3. 合约Result表：result txid、contract address、result type、call id、trigger id、输入UTXO、输出资产转移、gas费用、执行状态、错误信息、高度和时间。
4. 合约状态表：contract address、contract type、state root、当前状态、类型特有状态、更新时间和最后Result txid。
5. EVM扩展表：EVM地址映射、code hash、storage root、logs/events、registered triggers和trigger执行历史。
6. Agent扩展表：Agent合约内容hash、ready结果、bet记录、outcome聚合、confirm记录、CoreNode公钥、CoreNode签名、result hash和结算/退款明细。
7. 资产视图：合约地址UTXO资产余额、已锁定资金池、Result转出、找零和费用归集。
8. 重组处理：索引器必须能按区块高度回滚合约部署、调用、Result、状态、触发器和资产视图。

查询API至少应支持按合约地址、txid、调用者地址、合约类型、状态、高度范围、trigger id、Agent outcome和EVM event topic检索。


Mempool规则
----

mempool必须拒绝以下交易：

1. payload格式非法的`CONTRACT_DEPLOY`或`CONTRACT_INVOKE`。
2. 没有输出到合约地址的`CONTRACT_INVOKE`。
3. 输出到不存在合约地址的`CONTRACT_INVOKE`。
4. 同一个`CONTRACT_INVOKE`输出到多个不同合约地址。
5. gas limit缺失或超过协议上限。
6. gas/funding不足。
7. gas资产类型不符合协议规定。
8. 本地模拟无法通过。
9. 外部提交的`CONTRACT_RESULT`。
