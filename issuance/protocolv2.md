ORDX 协议 v2.0
====

SAT20 资产发行协议ORDX会在兼容老版本的基础上，根据BTC生态建设的需要，不断对协议进行升级。

本次升级主要是为了支持聪资产更好的在二层网络流通，同时让协议更简洁，更好用。

本次升级内容：

数据写入方式
---
ORDX协议的数据写入方式，从最初的铭文方式，升级为OP_RETURN数据方式。


新的指令
---
v2.0版本主要支持ordinals nft的销毁和交换指令。
这两个指令的效果是永久的，由owner发起执行，将对应的ordinals nft永久销毁，或者转移到另外一个聪上。

数据格式：
OP_RETURN ｜ MAGIC_NUMBER ｜ CT_TYPE ｜ CONTENT  
MAGIC_NUMBER = OP_16  
CT_DESTROY = OP_4  
CT_SWAP = OP_5  


销毁的content： 
Satoshi ｜ Inscription Number  

交换的content： 
assetName |（start, end）｜ (start, end)  
注意输入的聪范围，必须是自己能控制的聪；但输出的聪，不一定是自己能控制的聪，也就是可以远程交换，直接将聪的绑定资产送给其他人。
如果该utxo中该资产有多个range，每个range都需要有一个op_return来执行。
assetName的格式：协议：类型：tickername（如果是nft，填inscription_number）


探索新功能
---
stake/unstake跟deploy有类似的地方，但其资产发行方式需要通过质押指定的资产才能发行对应的新资产。这可以简化质押资产的管理方式。
该操作指令必须配合聪网的通道才能生效。质押发行的资产不绑定聪。
assetName ｜ amt


备注：请注意以上新功能仅处于探索阶段，并没有正式实施。