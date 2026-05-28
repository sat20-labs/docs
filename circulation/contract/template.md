模版合约
====

模版合约是聪网原生智能合约类型。其执行逻辑由聪网节点源码中内置的Go runtime实现。

模版合约遵循[智能合约](readme.md)的通用协议。本文只定义模版合约特有规则。


合约类型
----

模版合约类型为：

```text
ContractTypeTemplate
```

模版合约不执行EVM bytecode，不使用Solidity ABI，不维护EVM account state。模版合约也不是通道合约，不依赖RSMC通道、多方签名或承诺交易。

模版合约的资产控制边界来自合约VM状态和canonical `CONTRACT_RESULT`。


地址规则
----

模版合约使用通用合约地址格式：

```text
ca/tc + version + ContractTypeTemplate + hash
```

模版合约地址hash长度为32字节。hash输入为：

1. `Contract.Encode()`得到的合约内容。
2. deployer。
3. 部署随机值。

部署随机值用于让相同deployer和相同合约内容生成不同合约地址。

模版合约runtime中的`URL()`等于合约地址。


部署规则
----

`CONTRACT_DEPLOY`用于部署模版合约。

部署payload包含：

1. 模版名称。
2. 模版版本。
3. deployer。
4. 部署随机值。
5. gas limit。
6. `Contract.Encode()`得到的合约内容。

节点根据部署payload生成合约地址、初始化runtime状态，并在同一区块内通过`CONTRACT_RESULT`记录部署结果和state root。

如果合约地址已存在，部署无效。


调用规则
----

`CONTRACT_INVOKE`用于调用模版合约。

调用交易必须输出到被调用合约地址。该输出同时作为：

1. Call TX和Result TX的绑定UTXO。
2. 本次调用转入合约的资产。
3. 本次调用和后续结算的费用来源。

调用者身份由调用交易最后一个输入解析得到。runtime中的用户状态、LP归属、refund权限和历史记录都使用该身份。


费用规则
----

模版合约使用统一gas资产支付费用。

不同模版可以定义自己的调用费和撮合费。限价单和AMM模版沿用原通道合约的费用计算方式，但费用资产使用统一gas资产。

gas/funding输出中用于费用的部分不进入合约资产池。扣除费用后的剩余资产才作为合约可支配资产。


Result TX规则
----

模版合约不接受外部提交的`CONTRACT_RESULT`进入mempool。

出块节点根据模版runtime结果构造canonical `CONTRACT_RESULT`。验证节点必须独立重放runtime，并比较区块中的Result TX。

如果Result TX缺失、输入输出不符合canonical规则，或与本地重放结果不一致，区块无效。


状态规则
----

模版合约状态属于全局合约VM状态。

模版合约state root、EVM合约state root和Agent合约state root合成统一的contract state root，并写入coinbase。

模版runtime必须满足：

1. 相同链上输入得到相同状态。
2. 不依赖本地时间、外部服务、随机数或其他非确定性数据。
3. 合约资产余额由合约地址UTXO集合和runtime状态共同验证。


第一阶段模版
----

第一阶段实现两个交易类模版：

1. 限价单交易合约。
2. AMM交易合约。

两个模版都从原通道合约业务逻辑迁移，但不保留以下能力：

1. 通道两端签名。
2. RSMC通道状态。
3. L1 deposit/withdraw。
4. L1 commit/reveal和BRC20 transfer inscription流程。
5. 老通道合约状态迁移。


限价单交易合约
----

限价单交易合约对应原`SwapContractRuntime`的限价单交易逻辑。

接口名称和订单类型值与通道合约保持一致：

1. `swap`：挂买单或卖单。
2. `refund`：取消挂单或取回可退资产。
3. 买单订单类型为`2`。
4. 卖单订单类型为`1`。
5. refund订单类型为`3`。

撮合规则：

1. 买单按价格从高到低排序。
2. 卖单按价格从低到高排序。
3. 同价格按区块顺序、交易顺序和item id排序。
4. 只有买价大于或等于卖价时成交。
5. 成交价使用卖单价格。
6. 买单可以吃到更低价格卖单。
7. 每次撮合生成买家资产转移和卖家聪转移，两笔transfer位于同一个Result TX中。
8. 买单完成后，未使用的聪退回买家。
9. 卖单剩余资产不足以按价格成交时，剩余资产退回卖家。

refund规则：

1. `refund`参数包含item id列表。
2. item id列表为空时，取消调用者所有未完成挂单。
3. item id列表非空时，只取消指定item。
4. 调用者只能取消自己的挂单。
5. 已成交并已经通过Result TX发出的资产不再进入refund。


AMM交易合约
----

AMM交易合约对应原AMM通道合约的swap和流动性逻辑。

接口名称和订单类型值与通道合约保持一致：

1. `swap`：AMM买入或卖出。
2. `refund`：取回可退资产。
3. `addliq`：添加流动性。
4. `removeliq`：移除流动性。
5. 买单订单类型为`2`。
6. 卖单订单类型为`1`。
7. 添加流动性订单类型为`9`。
8. 移除流动性订单类型为`10`。

部署和ready规则：

1. AMM合约部署内容包含资产名称、初始资产数量、初始聪数量和常数K。
2. 合约部署后，如果合约地址中的资产池、聪池或`asset*sats`没有达到部署参数要求，合约不进入可交易状态。
3. 合约可以通过`addliq`补充底池。
4. 当资产池、聪池和`asset*sats >= K`都满足后，合约进入可交易状态。
5. 合约ready后，正常交易过程中不再要求实时`asset*sats >= K`。
6. 如果池子被移空，合约退出可交易状态，必须再次通过`addliq`达到初始K后才能重新ready。

AMM swap规则：

1. AMM采用常数乘积公式。
2. AMM买入时，用户输入聪，输出资产。
3. AMM卖出时，用户输入资产，输出聪。
4. AMM卖出参数中的`Amt`表示最小可接受输出聪数量，输入资产数量以Call TX funding output为准。
5. AMM买入参数中的`Amt`表示最小可接受输出资产数量，输入聪数量由`UnitPrice`和funding output确定。
6. 滑点保护失败时，本区块直接生成refund result。
7. 同一区块内AMM先处理swap，再处理add/remove liquidity，以对齐原通道合约。
8. 因addliq达到ready的区块不会同时撮合之前等待中的swap，等待中的swap会在后续区块结算。

流动性规则：

1. `addliq`参数包含资产数量和入池聪数量。
2. 入池聪数量使用`addliq`参数中的`Value`，不是Call TX funding output中的全部sats。
3. 多余资产或多余聪按池子比例计算后通过Result TX退回。
4. `removeliq`参数包含要移除的LPT数量。
5. 如果请求移除的LPT超过调用者余额，按调用者实际LPT余额处理。
6. 移除流动性时，LP获得对应池子份额。
7. 产生利润时，LP获得60%利润；原服务端和基金会两部分合并后统一给基金会。
8. 当前实现使用部署者地址作为基金会接收地址。
