# 资产发行协议

比特币主网本身只原生理解 BTC 与 UTXO。Ordinals、Runes、BRC20、ORDX 等资产协议，都把资产语义写入 BTC 交易、脚本、铭文、sat range 或协议事件中。Indexer 的职责不是发明这些资产，而是把它们从链上事实中解析出来，形成统一、可查询、可复核的资产状态。

因此，资产发行协议应放在 Indexer 下面理解：它们是 Indexer 需要支持和统一表达的协议族。ORDX 是 SAT20 独自设计的聪绑定资产协议，但它不是唯一资产协议；聪网需要同时服务 BTC 主网上已经存在和未来出现的多种资产。

## Indexer 支持的主要资产类型

| 协议 / 资产类型 | 核心语义 | Indexer 需要表达什么 |
| --- | --- | --- |
| BTC | 比特币原生 UTXO 资产 | 地址 UTXO、金额、确认数、花费状态、mempool / reorg 状态 |
| Ordinals | 基于 sat 序号和 inscription 的数字对象 | sat range、inscription、owner、所在 UTXO、转移历史 |
| Runes | BTC L1 上的同质化资产协议 | etching、mint、transfer、余额、UTXO 归属和有效性 |
| BRC20 | 基于 inscription 的 deploy / mint / transfer 资产协议 | ticker、deploy、mint、transfer inscription、有效/无效 transfer、地址余额 |
| ORDX | SAT20 设计的聪绑定资产发行协议 | ticker、deploy、mint、绑定聪、解绑、冻结、UTXO 归属和 sat range |

STP 和 SatoshiNet 通过 Indexer 确认资产事实，而不是直接猜测资产。资产进入通道前，客户端必须先通过 L1 indexer 确认目标 UTXO 中的资产协议、数量、有效性和确认状态。资产进入聪网后，L2 indexer 继续追踪 ascend、descend、enUTXO、通道和合约状态。

## 统一表达原则

Indexer 对不同资产协议应尽量提供统一的查询语义：

1. 资产标识：协议、ticker / rune id / inscription id / asset name。
2. 资产数量：按协议精度表达，不能丢失 divisibility。
3. 承载位置：txid、vout、sat range、address、layer。
4. 有效性：协议事件是否有效，是否已被后续事件消费或失效。
5. 确认状态：mempool、confirmations、height、reorg 风险。
6. 跨层状态：是否已经 ascend 到聪网，是否已经 descend 回 BTC L1。

钱包、交易平台、STP 客户端和 AI Agent 都应基于这些字段做判断，而不是只依赖单个余额字段。

## ORDX 协议

ORDX 是 SAT20 体系中的聪绑定资产发行协议。它的核心思想是：资产不是独立存在的账户余额，而是绑定在可识别、可追踪的聪上。聪在哪里，资产就在哪里；聪属于谁，资产就属于谁。

### 核心属性

ORDX 资产继承聪的几个关键属性：

1. 聪不可凭空销毁，因此绑定在聪上的资产也不能在协议外随意消失。
2. 聪的序号使每一聪具备可识别性，资产可以绑定到特定聪或特定聪集合上。
3. 聪在 UTXO 中流动，资产也随 UTXO 流动。
4. 聪的非均质化让资产天然具备 SFT 属性。
5. 资产发行、铸造、解绑、冻结等状态都应由 indexer 从 BTC L1 交易中复算。

ORDX 与账户模型资产不同。钱包和交易平台不能只看地址余额，还必须理解承载资产的 UTXO、sat range、绑定数量和协议状态。

### 基础能力

ORDX 依赖两类基础能力：

1. 识别和跟踪聪：确定某个 UTXO 中包含哪些 sat range，某个聪当前位于哪里。
2. 在聪上写入和读取协议数据：通过铭文或 OP_RETURN 表达 deploy、mint、unbind、freeze 等协议事件。

Indexer 是 ORDX 的事实计算层。它负责解析 BTC L1 交易，判断协议事件是否有效，并向钱包、浏览器、STP 客户端和交易平台提供可查询结果。

### Deploy

`deploy` 用于部署一个 ORDX ticker。

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `p` | 是 | 协议名，固定为 `ordx` |
| `op` | 是 | 指令，固定为 `deploy` |
| `tick` | 是 | 资产名称；通常为 3 个或 5-16 个字符，4 字符名称为 BRC20 保留 |
| `lim` | 否 | 单次 mint 上限，默认 `10000`；特殊 sat 资产默认 `1` |
| `n` | 否 | 每聪绑定的 token 数量，默认 `1`，最大 `65535` |
| `selfmint` | 否 | 项目方或持有者自铸比例 |
| `max` | 否 | 最大供应量 |
| `block` | 否 | 允许 mint 的高度区间 |
| `attr` | 否 | 对可绑定聪的属性要求 |
| `des` | 否 | 描述信息 |

示例：

```json
{
  "p": "ordx",
  "op": "deploy",
  "tick": "satoshi",
  "block": "830000-833144",
  "lim": "10000"
}
```

部署规则应至少包括：

1. ticker 名称未被使用。
2. 如果设置 `block`，deploy 确认高度必须早于 mint 起始高度足够区块。
3. 字段格式、数量上限、名称长度和属性条件必须通过 indexer 校验。

### Mint

`mint` 用于铸造已经部署的 ticker。

| 字段 | 必填 | 含义 |
| --- | --- | --- |
| `p` | 是 | 协议名，固定为 `ordx` |
| `op` | 是 | 指令，固定为 `mint` |
| `tick` | 是 | 已部署资产名称 |
| `amt` | 否 | 本次 mint 数量，默认等于 `lim`，不能超过 `lim` |
| `sat` | 否 | 当 deploy 设置 sat 属性要求时，指定满足条件的聪 |

示例：

```json
{
  "p": "ordx",
  "op": "mint",
  "tick": "satoshi"
}
```

Mint 校验应至少包括：

1. ticker 已经部署。
2. `amt` 不超过单次上限。
3. 总供应量不超过 `max`。
4. 如果有 `block`，mint 高度位于允许区间内。
5. 如果有 `selfmint`，按 selfmint 规则校验铸造权限和额度。
6. 如果有 `attr` 或 `sat`，目标聪满足稀有度、尾零或其他扩展条件。

## ORDX v2 指令

ORDX v2 在兼容旧版本的基础上，增加了更适合 L2 流通和受控资产场景的能力。

### 数据写入方式

v2 支持通过 OP_RETURN 写入协议数据：

```text
OP_RETURN | SAT20_MAGIC_NUMBER | CONTENT_TYPE | CONTENT
```

OP_RETURN 让部分协议事件表达更简洁，也更便于 indexer 直接解析。

### Unbind

`unbind` 将指定 UTXO 输出中的某个 ORDX ticker 与聪解绑。该操作是永久的，只能由资产 owner 发起。

规则：

1. 输入包含需要解绑的目标 UTXO。
2. 输出指定目标 vout。
3. OP_RETURN 内容指定 ticker 与 vout。
4. 该 vout 中指定 ticker 的资产全部解绑，其他资产类型不受影响。

### Freeze / Unfreeze

`freeze` 和 `unfreeze` 面向稳定币等受控资产场景，用于地址级权限控制。

规则：

1. 冻结目标是 `ticker + address + height`。
2. 冻结高度由指令声明，且指令确认高度必须与冻结高度接近。
3. 被冻结地址上该 ticker 的现有资产和后续流入资产都视为冻结资产。
4. 冻结资产不可作为该 ticker 的有效可转移资产使用。
5. 如果底层 BTC UTXO 被花费，冻结资产不会随输出转移，而是在协议层失效。
6. 解冻后，该地址上仍有效的绑定资产可以正常转移；已经因冻结花费而失效的资产不会恢复。

发起权限：

1. 只有满足协议规则的受控 ticker 才能被冻结或解冻。
2. 通常仅允许该 ticker 的当前 deploy owner 发起。

## 与 STP 和聪网的关系

资产进入聪网时，必须先由 L1 indexer 确认其协议类型、数量、有效性和所在 UTXO。STP splicing-in 只会让用户明确指定的一种资产进入聪网；如果一个 UTXO 同时携带多种资产，未指定资产不会被 ascend。

ORDX 必然绑定聪。进入聪网时，客户端必须根据资产数量和 `bindingSat` 计算需要多少聪。ORDX mint 结果中可能同时包含 ordinals NFT 与 ORDX ticker 资产；当前 STP 不把 `ordx:o` 类型资产 ascend 到聪网，客户端和 indexer 应把它作为不进入聪网的附带对象处理。

BRC20 和 Runes 在聪网上不需要绑定聪，但在 BTC L1 上仍受各自协议和比特币输出规则约束。STP 客户端和 Agent 不能把 L2 的 0 聪资产 UTXO 规则套用到 L1。

## 相关服务

ORDX 可以扩展出名字服务、KV 数据服务、SFT/NFT/FT/DID 等应用形态。但这些应用都应建立在同一个基础上：资产事实由 BTC L1 交易和 indexer 复算，资产控制权由 UTXO 所有权决定。
