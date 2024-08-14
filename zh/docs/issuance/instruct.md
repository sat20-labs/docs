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


