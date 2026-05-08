ORDX 协议 v2.0
====

SAT20 资产发行协议ORDX会在兼容老版本的基础上，根据BTC生态建设的需要，不断对协议进行升级。

本次升级主要是为了支持聪资产更好的在二层网络流通，同时让协议更简洁，更好用。

数据写入方式
---
ORDX协议的数据写入方式，从最初的铭文方式，升级为OP_RETURN数据方式。


新的指令
---
v2.0版本主要支持两类新指令：

1. 资产解绑指令
2. 地址级冻结/解冻指令

### 1. 资产解绑指令

这个指令的效果是永久的。
解绑指令只能由资产owner发起执行，将目标utxo（可多个）作为输入，输出到某个vout，同时增加解绑指令op_return，指定解绑的ticker+vout，该vout中指定的ticker资产全部解绑（其他类型资产不受影响）。


数据格式：
OP_RETURN ｜ SAT20_MAGIC_NUMBER ｜ CT_TYPE ｜ CONTENT  
SAT20_MAGIC_NUMBER    = OP_16  
CONTENT_TYPE_UNBIND   = OP_DATA_40  
CONTENT               = 目标ticker名称+vout

### 2. 地址级冻结/解冻指令

该指令主要用于稳定币等受控资产场景。

冻结和解冻的目标，是某个地址在某个ticker下的资产权限状态。

冻结的核心规则如下：

1. 冻结是地址级的，目标对象为 `ticker + address + height`
2. 冻结生效区块高度在内容中明确指定，但该指令所在交易的确认高度与冻结高度差必须小于等于2，才算有效的冻结指令
3. 被冻结地址上，该ticker当前持有的资产，以及后续再流入该地址的该ticker资产，都视为冻结资产
4. 冻结资产不可再作为该ticker的有效可转移资产使用
5. 如果底层BTC UTXO被花费，这部分冻结资产不会跟随输出转移，而是在协议层直接销毁
6. 解冻后，该地址上的绑定了该ticker资产的utxo可以正常转移资产；已经因为花费而被协议层销毁的资产不会恢复

发起权限：

1. 只有selfmint=100的ticker才有可能被冻结/解冻
2. 仅允许该ticker的deployer发起冻结和解冻
2. 这里的deployer，指的是该ticker deploy铭文当前的owner，而不是最初部署时的铭刻地址

数据格式：
OP_RETURN ｜ SAT20_MAGIC_NUMBER ｜ CT_TYPE ｜ CONTENT  
SAT20_MAGIC_NUMBER      = OP_16  
CONTENT_TYPE_FREEZE     = OP_DATA_43  
CONTENT_TYPE_UNFREEZE   = OP_DATA_44  
CONTENT                 = 目标ticker名称+目标address+冻结高度 （解冻不需要提供高度）

其中：

- `目标ticker` 只能是 ordx 协议的 ft 类型资产
- `目标address` 为标准地址字符串
- 同一个地址是否处于冻结状态，由该ticker下最近一次冻结/解冻指令决定


该功能在索引器1.5.0激活。
