# 搭建白标 DEX

当前已有可复用组件：SatoshiNet节点、L1/L2 Indexer、SAT20 PWA的DApp Connect、主/测试市场前端，以及AMM和限价单通道合约。但仓库尚未发布一个带版本、安装器、配置schema和升级策略的“一键白标DEX工具包”。

自建项目应把环境完全分开：独立域名、CSP允许列表、market URL、API proxy、Indexer数据、合约登记和测试钱包。测试站不能复用生产域名或把测试合约写入生产配置。发布前至少验证钱包origin授权、网络参数、AMM/限价单、资产核账、错误恢复、Explorer链接和升级回退。

**页面状态：组件可复用；标准化发行包规划中（Components Available / Packaged Toolkit Planned）**
