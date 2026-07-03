# 自然语言合约

自然语言合约是由AI Agent支持的聪网智能合约类型。合约内容以自然语言协议表达，由AI Agent进行结构化解释、验证和执行建议生成。

自然语言合约遵循[智能合约](./)的通用协议。本文只定义自然语言合约的边界和第一阶段要求。

## 命名

建议命名：

1. 中文名：自然语言合约。
2. 英文名：Natural Language Contract。
3. 技术简称：Agent合约。
4. 代码类型：`ContractTypeAgent`。

协议文档中使用“自然语言合约”。代码类型和内部实现可以使用`Agent`。

## 合约类型

自然语言合约类型为：

```
ContractTypeAgent
```

自然语言合约不是EVM合约，不要求用户编写Solidity、ABI或bytecode。

自然语言合约不是模版合约，不要求合约逻辑预先固化在聪网节点源码中。

自然语言合约不是通道合约，不依赖RSMC通道、多方签名或承诺交易。

## CoreNode Agent

聪网自然语言合约由协议内置的AI Agent支持。第一阶段可以将整个聪网网络理解为只有一个协议Agent，该Agent由内置CoreNode执行。

CoreNode身份由协议配置中的CoreNode地址确定。节点验证`ready`、`reject`和`confirm`等CoreNode专用接口时，按通用caller规则解析调用交易最后一个输入的前序输出地址，并要求该地址等于协议配置的CoreNode地址。

CoreNode确认结果本身不再在payload中重复携带CoreNode公钥和签名。确认交易必须由有效CoreNode地址发起；Result TX和state root仍由所有节点独立验证。这样可以避免在payload中存储冗余身份字段，并让CoreNode身份检查与其他合约调用保持一致。

CoreNode在自然语言合约中同时承担以下角色：

1. Agent执行者。
2. 合约内容可理解性、可验证性和可执行性的审核者。
3. 协议oracle。
4. 生成自然语言合约执行结论的授权实体。

自然语言合约的普通用户不能替代CoreNode生成协议认可的Agent结论。普通用户可以部署合约、提交材料、请求执行或发起争议，但不能调用只允许CoreNode调用的内置Agent接口。

后续协议可以扩展为多Agent验证模式，例如3个Agent中至少2个给出一致结论才接受执行结果。测试阶段可以先采用单CoreNode Agent模式。

## 合约内容

自然语言合约内容是一份可执行协议文本。协议文本必须能被AI Agent解析为可验证、可验收、可执行的结构。

协议文本应包含：

1. 合同目的。
2. 参与方和角色。
3. 标的资产。
4. 资产进入合约的方式。
5. 触发条件。
6. 验证数据来源。
7. 验收标准。
8. 执行方式。
9. 超时、失败和争议处理。
10. 可生成的资产转移结果。

合约可以包含结构化辅助字段：

1. 资产列表。
2. 参与方地址列表。
3. 时间或区块高度限制。
4. 允许使用的数据源。
5. 验证器或仲裁器规则。
6. 合约版本。

自然语言正文是合约语义的核心来源。结构化字段只能辅助解析，不得改变正文的核心含义。

## 部署规则

`CONTRACT_DEPLOY`用于部署自然语言合约。

部署payload包含：

1. 合约类型。
2. 合约正文。
3. 合约版本。
4. deployer。
5. 部署随机值。
6. 可选结构化辅助字段。

自然语言合约部署后不会自动进入可执行状态。部署成功只创建一个待确认合约，初始状态为`PendingReady`。

所有自然语言合约都必须提供一个固定的CoreNode激活接口：

```
ready
```

`ready`接口只能由CoreNode调用，其他地址无权调用。调用者身份仍按通用规则由调用交易最后一个输入解析得到。

CoreNode调用`ready`接口时，需要检查：

1. 内容是否完整。
2. 条件是否可验证。
3. 验收标准是否明确。
4. 执行结果是否可以映射为Asset Intent。
5. 是否依赖不可验证或不可共识的私有事实。
6. 是否存在矛盾条款、循环条件或无法执行的条款。

如果检查通过，CoreNode交互生成canonical `CONTRACT_RESULT`，该Result声明合约进入`Ready`状态。只有进入`Ready`状态的自然语言合约才能接受普通业务调用。

如果检查不通过，CoreNode交互生成拒绝结果，合约进入`Rejected`或`Invalid`状态。未进入`Ready`状态的合约不得产生资产转移执行结果。

## 调用规则

`CONTRACT_INVOKE`用于向自然语言合约提交事件、证明、验收请求、执行请求或争议材料。

调用内容可以包含：

1. 触发动作。
2. 调用者身份。
3. 链上证明。
4. 外部证明。
5. 验收材料。
6. 执行请求。
7. 争议或申诉材料。

调用交易必须输出到被调用合约地址，作为gas/funding输出。调用者身份由调用交易最后一个输入解析得到。

自然语言合约默认调用不携带自然语言材料或结构化动作。第一阶段可作为向合约地址转入资产的普通链上行为，除非合约协议明确规定默认行为，否则不改变自然语言合约业务状态。

自然语言合约调用分为两类：

1. CoreNode内置调用：包括`ready`以及后续协议定义的Agent专用接口，只允许CoreNode调用。
2. 普通业务调用：由参与方或其他授权地址提交事件、证明、验收、执行请求或争议材料。

除`ready`外，普通业务调用只能在合约状态为`Ready`后生效。

## AI Agent执行规则

AI Agent根据合约正文、合约状态、触发条件、证明材料和链上环境生成结构化执行结论。

第一阶段Agent由CoreNode执行。CoreNode生成的Agent结论进入聪网合约执行流程，并通过canonical `CONTRACT_RESULT`表达。Agent不能只输出自由文本，必须输出可验证、可比较、可重放的结构化结论。

执行结论必须包含：

1. 触发条件是否满足。
2. 使用的验证材料。
3. 验收是否通过。
4. 需要生成的Asset Intent。
5. 是否需要等待更多材料。
6. 是否进入失败、超时或争议状态。
7. 结论摘要。

AI Agent不能直接花费UTXO。资产转移必须通过canonical `CONTRACT_RESULT`结算。

Agent具体执行方式仍需后续明确，至少包括：

1. 模型版本或Agent实现版本。
2. 固定提示词和解释规则。
3. 结构化输出schema。
4. 输出签名或CoreNode身份验证方式。
5. 单Agent模式和多Agent阈值模式的切换规则。
6. 失败、超时、争议和重试规则。

## 可验证性

自然语言合约必须避免依赖无法形成共识的事实。

允许的数据来源包括：

1. 聪网链上交易。
2. 合约自身状态。
3. 指定链上合约或预言机结果。
4. 部署时指定的外部证明。
5. 多方签署的验收材料。
6. 协议允许的AI Agent验证结果。
7. CoreNode作为协议oracle给出的验证结果。

如果多个节点的AI Agent可能对同一材料得出不同结论，协议必须提供约束机制：

1. 固定模型版本。
2. 固定提示词和解释规则。
3. 固定结构化输出格式。
4. 多Agent共识。
5. 仲裁器或挑战期。
6. 只接受可独立校验的证明材料。

## Result TX和状态

自然语言合约不接受外部提交的`CONTRACT_RESULT`进入mempool。

出块节点根据AI Agent执行结论构造canonical `CONTRACT_RESULT`。验证节点必须根据协议规定的Agent验证方式复核执行结论，并比较Result TX。

自然语言合约结果进入聪网合约结果流程。无论是`ready`激活结果、拒绝结果、普通执行结果、失败结果还是争议结果，都必须通过canonical `CONTRACT_RESULT`表达，不能由外部用户直接提交非canonical Result TX。

自然语言合约状态至少包含：

1. 合约正文hash。
2. 合约版本。
3. 当前执行状态。
4. 已提交证明。
5. 已验收事项。
6. 待执行事项。
7. 已生成结果。
8. 争议或失败状态。

自然语言合约状态应尽量使用统一状态定义。不同合约可以只使用其中一部分状态，但相同状态名称在不同自然语言合约中必须表达相同含义。

基础状态包括：

1. `PendingReady`：合约已部署，等待CoreNode调用`ready`审核。
2. `Ready`：CoreNode已确认合约内容可理解、可验证、可执行，可以接受普通业务调用。
3. `Rejected`：CoreNode拒绝激活，合约不能执行普通业务调用。
4. `Invalid`：合约内容、结构或调用材料无效，不能进入后续执行流程。
5. `PendingEvidence`：合约等待参与方提交证明或验收材料。
6. `PendingExecution`：触发条件已满足，等待Agent生成执行结论或等待Result结算。
7. `Completed`：合约主要义务已完成，相关资产转移已经结算。
8. `Failed`：合约因失败条件、超时或不可执行原因结束。
9. `Disputed`：合约进入争议状态，等待CoreNode、仲裁器或协议定义的争议流程处理。
10. `Expired`：合约超过有效期且未满足继续执行条件。

Agent合约state root必须进入统一contract state root。

## 预测型自然语言合约

\[仅用于测试网络演示]

第一阶段优先支持预测型自然语言合约。预测型自然语言合约是`ContractTypeAgent`下的固定子类型：

```
prediction
```

预测型自然语言合约当前仅在testnet启用。mainnet下Agent合约暂不开放可用子类型，节点、oracle、索引器和市场都不应把prediction作为mainnet可用合约展示或执行。

预测型自然语言合约用于表达一个可验证事件的多个候选结果。用户向合约地址投注，Agent在事件结束后根据部署时指定的数据来源确认最终结果，合约根据确认结果自动分配奖金或退款。

预测型自然语言合约的Agent只负责：

1. `ready`：审核合约内容是否可以被理解、验证和执行。
2. `confirm`：根据指定数据来源提交最终结果。

下注记录、手续费、奖金分配、退款和合约关闭都由预测合约runtime确定性处理。

### 部署payload

预测型自然语言合约的部署payload包含：

```json
{
  "subtype": "prediction",
  "title": "...",
  "description": "...",
  "time_base": "unix",
  "event_time": 1780310400,
  "bet_deadline": 1780306800,
  "confirm_after": 1780396800,
  "source_url": "https://xxx.com",
  "bet_asset": "::",
  "min_bet_unit": "10000",
  "outcomes": [
    {"id": "a", "text": "..."},
    {"id": "b", "text": "..."},
    {"id": "c", "text": "..."}
  ]
}
```

字段规则：

1. `subtype`必须为`prediction`。
2. `title`和`description`描述预测目标。
3. `time_base`指定时间基准，可以为`unix`或`height`。
4. `event_time`、`bet_deadline`和`confirm_after`按`time_base`解释。
5. `source_url`为部署时指定的数据来源站点或入口URL，可以是比赛预告页面、赛事页面或结果查询网站。
6. `bet_asset`为投注资产名称，使用聪网资产层的`AssetName.String()`格式。
7. `min_bet_unit`为最小投注份额，使用字符串表达，最终按`bet_asset`对应资产属性解析为Decimal。
8. `outcomes`为候选结果列表，数量不固定，但至少包含2个候选结果。
9. `outcomes.id`使用小写字母编号，例如`a`、`b`、`c`，同一个合约内必须唯一。
10. 部署payload不包含手续费比例、Agent策略、bootstrap地址或Agent地址，这些属于协议内置配置。

### 内置配置

预测型自然语言合约第一阶段使用协议内置配置：

1. 部署者手续费：奖池的6%。
2. Agent手续费：奖池的3%。
3. bootstrap node手续费：奖池的1%。
4. 赢家奖池：奖池的90%。

如果后续采用3个Agent的多Agent模式，Agent手续费总额仍为3%，每个参与并形成有效确认结果的Agent获得1%。当前单Agent模式下，CoreNode Agent获得完整3%。

bootstrap node收款地址由协议内置bootstrap公钥推导，当前参考实现可使用`indexer/common/btc.go`中的`GetBootstrapAddress()`。Agent收款地址由协议内置Agent/CoreNode公钥推导，后续实现可以增加与`GetBootstrapAddress()`对应的Agent地址推导函数。

### 下注规则

预测型自然语言合约进入`Ready`状态后，内部状态进入`Betting`，用户可以通过`bet`调用参与投注。

`bet`调用参数包含：

```json
{
  "outcome_id": "a"
}
```

下注规则：

1. 任何地址都可以调用`bet`。
2. 合约必须处于通用`Ready`状态，且预测合约内部状态必须为`Betting`。
3. 当前时间或区块高度必须小于或等于`bet_deadline`。
4. `outcome_id`必须存在于部署payload的`outcomes`列表中。
5. 下注资产必须为部署payload中的`bet_asset`。
6. 下注金额以Call TX转入合约地址的funding output为准，不能以调用参数中的金额为准。
7. 下注金额必须大于或等于`min_bet_unit`。
8. 下注金额必须是`min_bet_unit`的整数倍。
9. 同一地址可以对多个候选结果下注。
10. 同一地址对同一候选结果多次下注时，状态按地址和候选结果聚合金额，历史记录保留每次调用。

每个候选结果的投注都必须独立满足最小投注份额和整数倍规则。

### 结果确认

`confirm`是预测型自然语言合约的Agent结果确认接口，只允许CoreNode Agent调用。第一阶段默认触发器为`confirm`调用。

`confirm`调用参数包含：

```json
{
  "result_type": "outcome",
  "outcome_id": "a",
  "result_url": "https://xxx.com/match/result/123",
  "result": "Team A 2-1 Team B",
  "observed_at": 1780314000,
  "agent_version": 1,
  "model_version": "model-v1"
}
```

确认规则：

1. 调用者必须是CoreNode Agent。
2. 合约必须已经进入`Ready`状态。
3. 当前时间或区块高度必须已经超过`bet_deadline`。
4. 当前时间或区块高度必须已经到达`confirm_after`。
5. `result_type`必须为`outcome`、`cancelled`、`invalid`或`unverifiable`之一。
6. 当`result_type`为`outcome`时，`outcome_id`必须存在于部署payload的`outcomes`列表中。
7. 当`result_type`为`cancelled`、`invalid`或`unverifiable`时，`outcome_id`可以为空，合约进入全额退款流程。
8. `result_url`为Agent实际用于确认结果的具体页面URL，可以不同于部署payload中的`source_url`。
9. `result_url`必须属于部署payload中`source_url`指定的网站范围：scheme必须相同，hostname必须相同或为其子域名；如果发生HTTP跳转，跳转后的最终URL也必须满足同样规则。
10. `result`记录Agent观察到的实际结果，例如比分、取消说明或不可验证说明；长度上限为128字节。
11. `observed_at`记录Agent观察到结果的时间或高度。
12. `agent_version`为整数版本号，记录生成确认结果的Agent实现版本。
13. `model_version`记录生成确认结果的模型版本。

Agent根据部署payload中的`source_url`确定允许的数据来源范围，并在该网站范围内找到具体结果页面`result_url`。Agent解析`result_url`内容，找到预测事件的最终结果，然后通过`confirm`提交结构化结果。合约runtime只处理结构化结果，不直接依赖非结构化网页内容进行资金分配。

清洗后文本应去除脚本、样式、广告、导航和明显动态噪声，只保留Agent用于判断结果的主体文本。第一阶段共识节点验证CoreNode调用者身份和结构化确认结果，不在区块验证路径重新抓取网页。索引器、浏览器和审计工具可以通过`result_url`、`result`、`observed_at`和Agent日志复核CoreNode确认过程。

如果采用多Agent模式，多个Agent分别提交`confirm`结果。合约runtime在相同`result_type`和相同`outcome_id`达到协议阈值后确认最终结果，并按该结果自动结算或退款。

### 自动结算和退款

预测型自然语言合约不提供对外开放的`settle`或`refund`接口。正常情况下，`confirm`触发合约自动结算或退款。

有赢家时，合约按以下顺序分配runtime记录的有效投注`bet_asset`资金：

1. 6%发送给deployer。
2. 3%发送给Agent。
3. 1%发送给bootstrap node。
4. 剩余90%按赢家下注金额占全部赢家下注金额的比例分配给赢家。

手续费和赢家分配使用Decimal计算。比例计算产生的余数进入赢家奖池。赢家分配产生的余数按赢家下注金额从大到小分配；下注金额相同时，按地址字典序分配。

没有赢家时，合约不收取手续费，runtime记录的有效投注`bet_asset`资金按原下注金额比例退款。

以下情况进入全额退款流程，不收取手续费：

1. 比赛或事件取消。
2. 数据来源可访问但结果不在候选结果列表中。
3. Agent确认结果为不可验证或无效。
4. 合约内容在ready后发现无法执行且尚未完成结算。

`confirm_after`是Agent开始检查结果的预期时间或高度。到达`confirm_after`后，Agent开始检查数据来源并尝试确认结果；如果Agent尚未确认，合约不自动退款，继续等待Agent处理。

只有通过有效`bet`调用并被runtime记录的`bet_asset`资金参与当前预测合约结算。无效调用、非投注资产和合约地址上超出runtime记录的资产按通用framework规则处理，不参与预测奖金分配。

### 不提供部署者取消接口

预测型自然语言合约不提供deployer专用的`cancel`接口。

原因如下：

1. 合约进入`Ready`前不能接受投注，通常没有需要deployer退款的资金。
2. 合约处于`Betting`时，允许deployer取消会产生提前终止合约、规避未来结果或影响投注人的风险。
3. 合约处于`ClosedForBet`或`PendingResult`时，结果确认权属于Agent，deployer不能替代Agent判断事件结果。
4. 比赛取消、结果无效、数据不可验证或合约无法执行时，应由CoreNode Agent通过`confirm`提交`cancelled`、`invalid`或`unverifiable`结果，并触发全额退款。
5. 到达`confirm_after`后Agent尚未确认时，协议选择继续等待Agent处理，不授权deployer绕过Agent触发退款。

### 内部状态

预测型自然语言合约使用通用`Ready`状态表示合约已经通过CoreNode审核，可以接受业务调用。预测业务自身维护独立内部状态：

1. `Betting`：允许用户下注。
2. `ClosedForBet`：下注截止，不再接受新下注。
3. `PendingResult`：等待Agent提交最终结果。
4. `Confirmed`：结果已经被Agent确认或达到多Agent阈值。
5. `Settled`：奖金已经分配，合约关闭。
6. `Refundable`：合约进入退款流程。

`Betting`不是通用合约状态，只是预测型自然语言合约的内部状态。

## 第一阶段定位

自然语言合约第一阶段允许先以单CoreNode Agent模式进入聪网合约结果流程。合约部署后必须先由CoreNode通过`ready`接口确认，确认结果通过canonical `CONTRACT_RESULT`写入链上状态。

第一阶段仍需继续明确Agent执行细节。进入完整主网共识执行前，必须明确模型确定性、验证方式、挑战机制、仲裁机制、多Agent阈值规则和state root承诺规则。
