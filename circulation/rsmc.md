RSMC
====

在闪电网络中，RSMC（Revocable Sequence Maturity Contract）是一种合约类型，用于确保闪电网络通道的安全性和可靠性。
RSMC是基于时间锁定的合约，它允许参与方在特定条件下撤销或关闭闪电网络通道。它的设计目的是防止欺诈行为和恶意操作，并确保交易的安全性。
用户的资产都是锁定在通道中，用户通过持有承诺交易，并且有能力构造惩罚交易来确保自己资产的安全。在任何时候，用户都可以不需要任何第三方的许可，取回自己的资金。


## 一、RSMC基本原理

闪电网络通道内的资金并不直接存在“账户”，而是通过**一对承诺交易（Commitment Transaction）**来代表当前通道状态。

* 每个通道参与者（Alice、Bob）都有一份**自己的承诺交易**，该交易可以单方面在主链上结算。
* 承诺交易花费的是最初的**Funding Transaction**输出。

**Funding Transaction（资金交易）**：

* 输入：双方的出资
* 输出：一个 2-of-2 多签（`<Alice, Bob>`）
* 只有双方签名才能花费这个输出。

**RSMC机制：**

* 每个承诺交易都包含一种特殊的“延迟支付”输出，带有撤销条件。
* 这样，当某一方广播旧的承诺交易（作弊）时，对方能立即花掉这笔资金作为惩罚。

RSMC核心输出结构如下（以Alice的commitment为例）：

| 输出类型             | 说明     |
| ---------------- | -------------------------- |
| **to_local**     | 支付给Alice，但加了延迟（例如 `OP_CHECKSEQUENCEVERIFY 144`），防止Alice立即花费。包含一个“撤销密钥”（revocation key），一旦Alice作弊广播旧交易，Bob可以立刻花走这笔资金。 |
| **to_remote**    | 立即支付给Bob（普通P2WPKH输出）     |

---

## 二、通道初始状态：Alice & Bob 建立通道

假设：

* Alice 和 Bob 想建立一个 1 BTC 通道。
* Alice 出资 1 BTC，Bob 出资 0 BTC。

### 1️⃣ Funding Transaction

* 输出：`2-of-2 multisig(Alice_pub, Bob_pub)`
* 这笔输出金额：1 BTC
* TxID 假设为 `funding_txid`

### 2️⃣ 双方各自生成承诺交易（C1a、C1b）

**C1a**：Alice 的视角（她签署并保留Bob签名）
**C1b**：Bob 的视角（他签署并保留Alice签名）

假设通道初始分配为：

* Alice：1.00000000 BTC
* Bob：0.00000000 BTC

则 Alice 的承诺交易（C1a）如下：

| 输出       | 金额 (BTC)   | 条件                                    |
| -------- | ---------- | ------------------------------------- |
| to_local | 1.00000000 | RSMC脚本（Alice延迟144块后可花，否则Bob可用撤销密钥立即花） |

而 Bob 的承诺交易（C1b）如下：

| 输出        | 金额 (BTC)   | 条件            |
| --------- | ---------- | ------------- |
| to_remote | 1.00000000 | 支付给Alice的普通输出 |

此时，双方都签好彼此的承诺交易，但 **都不广播**。
只有 `Funding TX` 被广播并确认。

---

## 三、通道状态更新

假设 Alice 要支付 0.3 BTC 给 Bob。

目标状态：

* Alice: 0.7 BTC
* Bob: 0.3 BTC

这时会生成新的承诺交易对：

* Alice的视角：C2a
* Bob的视角：C2b

### 1️⃣ 构造新的承诺交易

Alice的承诺交易（C2a）：

| 输出        | 金额 (BTC) | 条件               |
| --------- | -------- | ---------------- |
| to_local  | 0.7      | RSMC（Alice的延迟输出） |
| to_remote | 0.3      | 普通输出，立即给Bob      |

Bob的承诺交易（C2b）：

| 输出        | 金额 (BTC) | 条件             |
| --------- | -------- | -------------- |
| to_local  | 0.3      | RSMC（Bob的延迟输出） |
| to_remote | 0.7      | 普通输出，立即给Alice  |

### 2️⃣ 生成新的撤销密钥

* 在闪电通道每次更新时，双方各生成一个新的 **revocation secret**。
* 每个旧的状态会暴露出前一个状态的秘密，用来防止作弊。

例如：

* 每个状态有唯一的哈希密钥对 `(revocation_secret_n, revocation_hash_n)`。
* 若Alice与Bob从C1更新到C2：

  * Alice发给Bob自己旧状态(C1)的`revocation_secret_1`。
  * 这样Bob若检测到Alice再广播C1，就能用该secret花走Alice的延迟输出。

### 3️⃣ 安全替换旧状态

更新到C2时：

1. 双方签好新承诺交易（C2a、C2b）
2. 互相交换签名并验证成功
3. 双方各自泄露上一个状态（C1）的撤销密钥
4. 旧状态（C1）失效

此时，若Alice再广播C1，她将被Bob惩罚。

---

## 四、惩罚机制：Alice 作弊广播旧承诺交易（C1a）

假设 Alice 恶意地广播了旧的承诺交易 **C1a**（她的余额是 1 BTC）。

Bob 节点监控链上交易，发现有人广播了这笔过期状态的承诺交易（通过TXID匹配和脚本识别）。

### 1️⃣ Bob识别到作弊

* Bob在之前更新时获得了 `revocation_secret_1`。
* 他可以立即花掉Alice的 `to_local` 输出（即 1 BTC）。

RSMC脚本一般结构如下（简化版）：

```  
OP_IF  
    # 如果对方提供revocation secret，可立即花费  
    <revocation_pubkey>  
OP_ELSE  
    # 否则，等待时间锁后自己花费  
    <delay> OP_CSV OP_DROP <local_delayed_pubkey>  
OP_ENDIF  
OP_CHECKSIG  
```  

### 2️⃣ 惩罚交易（Penalty Transaction）

Bob构造一笔“惩罚交易”：

* 输入：Alice的`to_local`输出（被锁定的RSMC输出）
* 使用 `revocation_secret_1` 对应的公钥签名
* 输出：全额1 BTC给自己

该交易不需要等待时间锁，可以立即花费。

最终结果：

* Bob获得1 BTC
* Alice失去全部通道资金

---

## 五、完整例子流程汇总

| 阶段 | 事件      | Alice         | Bob           | 备注                  |
| -- | ---------- | ------------ | -------------- | ------------ |
| ①  | 开通通道      | 出资 1 BTC        | 出资 0 BTC        | FundingTX上链      |
| ②  | 初始状态      | C1a: to_local=1   | C1b: to_remote=1 | 双方都有commitment  |
| ③  | 更新状态（Alice→Bob 0.3 BTC） | C2a: to_local=0.7, to_remote=0.3 | C2b: to_local=0.3, to_remote=0.7 | 更新后泄露C1的revocation secret       |
| ④  | Alice作弊广播C1a  | 链上检测  | 检测到旧状态      | Bob获得Alice旧状态的revocation secret |
| ⑤  | Bob发起惩罚交易   | 全部资金 1 BTC   | 归Bob所有  | Alice被惩罚     |

---


## 六、瞭望塔
在实际的使用场景中，Alice或者Bob作为用户节点，不可能长期在线，所以需要一个监控节点，监控有没有过时的承诺交易被广播，如果有，就广播对应的惩罚交易，帮助用户惩罚对方，取回通道中所有资产，这种监控节点就是瞭望塔。