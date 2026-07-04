# Prediction 合约 Quickstart

Prediction 是当前聪网公开测试网优先开放的 Agent 合约场景。它用于验证自然语言 / Agent 合约在聪网智能合约框架中的基本闭环：部署、ready、投注、结果确认、Result TX、派奖或退款。

本文面向测试网部署者和开发者。普通用户操作步骤见 [Prediction 合约测试](../use/prediction-contract.md)。

## 当前状态

| 项目 | 状态 |
| --- | --- |
| 合约类型 | Agent 合约 / Natural Language Contract |
| 子类型 | `prediction` |
| 可用环境 | 聪网公开测试网 |
| 主网状态 | 暂未开放 |
| 推荐入口 | SAT20 PWA Wallet `工具` 和 `市场 -> Prediction` |
| 费用资产 | 测试 GAS |

## 基本流程

1. 部署者在 PWA `工具` 中创建 Prediction 合约。
2. 合约部署交易进入聪网测试网。
3. Core Node Agent 审核合约内容，调用 `ready`。
4. 合约进入可投注状态。
5. 用户在 `市场 -> Prediction` 选择候选结果并投注。
6. 投注截止后，Core Node Agent 根据指定数据来源确认结果。
7. 合约生成 canonical Result TX。
8. 用户获得派奖或退款。

## 部署参数

Prediction 合约部署参数应包含：

| 字段 | 含义 |
| --- | --- |
| `title` | 比赛或事件标题 |
| `description` | 事件说明，帮助用户理解预测对象 |
| `time_base` | 时间基准，通常为 unix 时间，也可以按协议支持使用高度 |
| `event_time` | 比赛或事件发生时间 |
| `bet_deadline` | 停止投注时间 |
| `confirm_after` | Agent 开始确认结果的时间 |
| `source_url` | 结果来源 URL |
| `bet_asset` | 投注资产名称 |
| `min_bet_unit` | 最小投注单位 |
| `outcomes` | 候选结果列表 |

候选结果应明确、互斥，并能被结果来源验证。不要使用“可能”“大概”“看情况”这类无法形成清晰结算结果的描述。

## 示例 payload

```json
{
  "subtype": "prediction",
  "title": "Team A vs Team B",
  "description": "Predict the final match winner.",
  "time_base": "unix",
  "event_time": 1780310400,
  "bet_deadline": 1780306800,
  "confirm_after": 1780396800,
  "source_url": "https://example.com/match/team-a-vs-team-b",
  "bet_asset": "::",
  "min_bet_unit": "10000",
  "outcomes": [
    { "id": "a", "text": "Team A wins" },
    { "id": "b", "text": "Team B wins" },
    { "id": "c", "text": "Draw" }
  ]
}
```

字段细节以 [自然语言合约](../protocol/contracts/agent.md) 中的 Prediction 协议定义为准。

## 部署检查

部署前应检查：

1. 钱包在测试网。
2. 钱包有足够测试 GAS。
3. `bet_deadline` 早于 `event_time`。
4. `confirm_after` 不早于事件结果可公开查询的时间。
5. `source_url` 是公开可访问页面。
6. 候选结果至少两个，并且不会互相重叠。
7. `min_bet_unit` 与目标测试资产的精度和用户体验匹配。

## 投注调用

用户投注时，调用参数只表达候选结果：

```json
{
  "outcome_id": "a"
}
```

投注金额以 Call TX 转入合约地址的 funding output 为准，不应在调用参数中重复表达金额。这样可以避免 UI 参数和链上资产输入不一致。

## 结果确认

结果确认由 Core Node Agent 发起。确认参数包括：

```json
{
  "result_type": "outcome",
  "outcome_id": "a",
  "result_url": "https://example.com/match/team-a-vs-team-b/result",
  "result": "Team A 2-1 Team B",
  "observed_at": 1780314000,
  "agent_version": 1,
  "model_version": "model-v1"
}
```

`result_url` 应属于部署时 `source_url` 指定的网站范围。合约 runtime 处理结构化确认结果，索引器、浏览器和审计工具可以根据 `result_url`、`result`、`observed_at` 和 Agent 日志复核确认过程。

## 验证 Result TX

开发者和测试者应关注：

1. Deploy TX 是否成功。
2. Ready Result TX 是否出现。
3. Bet TX 是否被合约接受。
4. Confirm 调用是否由 Core Node Agent 发起。
5. 结算 Result TX 是否按协议分配奖池或退款。
6. contract state root 是否随区块更新。
7. 钱包、市场和 Explorer 展示是否一致。

如果合约状态和资产分配不一致，应优先保留合约地址、txid、区块高度、页面截图和钱包日志。

## 与其他合约类型的关系

Prediction 不是 EVM 合约，不需要 Solidity、ABI 或 bytecode。它也不是通道合约，不依赖通道两端共同验证。Prediction 属于聪网智能合约体系，由全网验证合约调用、Result TX 和 state root。

EVM 合约适合复用 Solidity 生态；模板合约适合高频、规则固定、需要节点内置确定性 runtime 的场景；Prediction 适合测试 Agent 如何把外部可验证事件转化为结构化合约结果。

**页面状态：开发中（In Development）**
