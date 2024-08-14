SAT20名字服务
====

聪是我们整个协议生态的基础，其序数可以看作是聪的索引。但是，序数是一个64位的整数，太长，不容易记住。为了更快索引到每一个聪，我们有必要发展一套基于聪的名字服务，供用户记住每个对他来说意义重大的聪。序数跟名字的关系，和IP地址和域名的关系类似。SAT20的名字服务，是一种完全去中心化的，基于BTC的名字服务，每个人都可以公平使用，不受任何第三方控制。

名字服务的核心，是每个名字都是唯一的。没有子名字空间。这避免了欺诈的可能性。
每个名字都是一个铭刻在聪上的数据，是一个nft。一个聪只有一个名字，名字和聪也是一一对应的。  
名字绑定在聪上，谁拥有聪，名字也就属于谁。聪转给谁，名字也就转给谁。  
名字也是一种聪资产。  


命名规则
---
1. 名称的第一个实例有效。
2. 名称使用UTF-8字符。
3. 大小写无关。所有名称/命名空间都将以小写形式索引。
4. 名称不允许有空格。
5. 名称不允许标点符号。(带句号的名字，都是来自其他名字协议)
6. 名字长度，从3字节开始申请，但4字节暂时禁止注册。

注：4字节预留给BRC20的ticker。1-2字节协议内部使用，从协议层面禁止注册，永不开放注册，杜绝无谓的炒作。


组合规则
---
名字可以组合起来，形成某种特别含义。协议制定基本的规则如下：
1. 名字用@符号组合起来，比如Alice@sat20
2. 组合名字时需要双方都签名许可，也就是说组合是一种契约关系
3. 后一个名字，比如sat20，属于组织形式上更高一级的名字，比如是公司，俱乐部等一些组织


兼容性
----
SAT20名字服务兼容目前BTC网络上的主要名字服务。比如.btc为例，某个名字，1.btc，将做为一个整体，而不是分成名字1和名字空间.btc。根据我们的开发进展，我们计划兼容这些名字服务：（只读取名字，不支持铸造）
1. .btc
2. .x
3. 其他

注意，带.的名字，和不带.的名字，是不同的名字，比如123.btc和123，是两个独立的名字，相互之间没有关系。

垄断性资源
----
名字是一种核心资源，也是一种资产。比如Ticker名字Pearl，就是一个名字，由Deploy这个ticker的地址自动持有。如果一个名字已经被注册，其他人就无法部署这个名字的ticker。通过注册某个名字，将自动获得该名字相关的所有权限，SAT20协议维护这种权限。


版税
----
拥有某种资源的人，在资源被使用时，会自动根据某种可配置的税率收取版税，资源所有人自动获得版税收入。

