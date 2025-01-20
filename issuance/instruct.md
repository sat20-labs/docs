指令
====


SAT20资产发行协议只有deploy和mint指令，不需要transfer指令。


deploy
----

| KEY | Required | Description |
| :---: | :---: | :------- |
| p	| Yes | 协议名称: ordx |
| op | Yes | 指令: deploy |
| tick | Yes | 名称: 只允许3或5-16个字符，（为brc-20保留4个字符） |
| lim | No | 每次mint的token的限额，默认是10000。如果deploy特殊sat上的token，默认是1。 |
| selfmint | No | 自己铸造的比例（两位小数），只有持有该ticker的地址才能铸造（父子铭文）。 |
| max | No | mint的总量，64位整数。 |
| block | No | mint的开始高度和结束高度（开始-结束）。|
| attr | No | sat的属性要求，比如"rar=uncommon;trz=8"，可扩展。 |
| des | No | 描述内容 |


例如，公平发射的ticker：  
{   
  "p": "ordx",  
  "op": "deploy",  
  "tick": "satoshi",  
  “block”: "830000-833144",  
  "lim": "10000"  
}  

或者，项目方控盘的ticker：  
{   
  "p": "ordx",  
  "op": "deploy",  
  "tick": "Gamever",  
  "selfmint": "100%",  
  "max": "1000000000",  
  "lim": "10000"  
}  

部署ticker的规则：
1. ticker的名字必须没有被用过，或者部署着拥有该名字（DID）
2. 如果有block参数，要求该deploy被确认的高度，必须比start高度大1000以上
违背规则的ticker无效。


attr是一个可以扩展的属性，目的是让越来越多特殊的sat可以通过这个属性被筛选出来。目前支持的属性有：
1. rar：稀有度，在Ordinals中定义：common, uncommon, rare, epic, legendary, mythic 
2. trz：trailing zeros，尾部为零的数量，比如trz=8，说明该sat的编号的尾部有8个零  
3. 未来支持自定义的属性


mint
----

| KEY | Required | Description |
| :---: | :---: | :------- |
| p	| Yes | 协议名称: ordx |
| op | Yes | 指令: mint |
| tick | Yes | 名称: 只允许3或5-16个字符，（为brc-20保留4个字符） |
| amt | No | mint得到的token的数量，默认等于lim，不能超过lim |
| sat | No | sat的序号，设置了attr属性的ticker，mint时需要提供满足条件的sat |


例如：  
{  
  "p": "ordx",  
  "op": "mint",  
  "tick": "satoshi"  
}   

每次mint时，需要做的规则检查：
1. 协议必须是ordx
2. op必须是mint
3. ticker必须已经部署过
4. amt小于等于deploy的“lim”
5. 如果deploy有“selfmint”：
  * 只有持有ticker的地址才能mint（父子铭文）
  * 该次铸造的数量，加上已经铸造的总量，不超过max*selfmint
6. 如果deploy有”max“：该次铸造的数量，加上已经铸造的总量，不超过max
6. 如果deploy有”block“：该次mint的block高度要在规定之内
7. 如果deploy有“attr”：mint时检查指定的sat是否具备以下属性：
    * 如果有rar属性：检查该sat是否是这种类型
    * 如果有trz属性：检查该sat的序号是否有足够的尾数零
    * 如果有自定义属性，根据自定义规则做检查

如果不满足以上规则，当次mint无效。



ordx v2.0
----
ordx v2.0 将对资产的操作，从最初的铭文方式，升级为OP_RETURN操作码方式，用于支持新的指令。
v2.0版本主要支持ordinals nft的销毁和交换指令。
这两个指令的效果是永久的，由owner发起执行，将对应的ordinals nft永久销毁，或者转移到另外一个聪上。

数据格式：
OP_RETURN ｜ MAGIC_NUMBER ｜ CT_TYPE ｜ CONTENT
MAGIC_NUMBER = OP_16
CT_DESTROY = OP_4
CT_SWAP = OP_5
CT_STAKE = OP_6
CT_UNSTAKE = OP_7


销毁的content：
Satoshi ｜ Inscription Number

交换的content：
assetName |（start, end）｜ (start, end)
注意输入的聪范围，必须是自己能控制的聪；但输出的聪，不一定是自己能控制的聪，也就是可以远程交换，直接将聪的绑定资产送给其他人。
如果该utxo中该资产有多个range，每个range都需要有一个op_return来执行。
assetName的格式：协议：类型：tickername（如果是nft，填inscription_number）

探索新功能：  
stake/unstake跟deploy有类似的地方，但其资产发行方式需要通过质押指定的资产才能发行对应的新资产。这可以简化质押资产的管理方式。
该操作指令必须配合聪网的通道才能生效。质押发行的资产不绑定聪。
assetName ｜ amt
