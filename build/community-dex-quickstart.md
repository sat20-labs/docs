# 搭建社区 DEX / DAO

本文用于规划社区测试网DEX原型。当前参考市场、钱包连接、AMM与限价单组件可用，但DAO公开入口和标准化白标发行包尚未开放；因此本页是集成清单，不是可直接复制的一键部署脚本。

## 目标

一个 BTC 社区应能在测试网上完成：

1. 选择社区资产。
2. 部署或配置 DEX 前端。
3. 配置 AMM 或限价单模块。
4. 如确需DAO或社区基金，单独完成合约模型和安全评审；当前公开PWA不提供通用入口。
5. 接入钱包、Indexer 和 Explorer。
6. 完成一次测试交易。
7. 生成用户教程和风险提示。

## 操作前准备

1. 社区名称、域名和品牌素材。
2. 资产协议、ticker、数量和当前流动性。
3. 钱包和签名人安排。
4. 测试网资产和测试 GAS。
5. 所需模块：DEX、AMM、限价单、Launchpad、DAO、Explorer。

## 推荐步骤

1. 阅读 [Community Stack](../community-stack/)。
2. 选择最小模块组合。
3. 生成部署配置。
4. 在测试网部署合约或启用模板。
5. 配置 DEX 前端和后台。
6. 使用 SAT20 PWA Wallet 完成连接和授权。
7. 完成一次 Swap 或限价单测试。
8. 在 Explorer 和 Indexer 中验证结果。
9. 提交到 [Built on SatoshiNet](../ecosystem/built-on-satoshinet.md)。

## 验收标准

1. 用户能打开社区 DEX。
2. 用户能连接钱包。
3. 用户能看到资产和交易对。
4. 用户能完成一次测试网交易。
5. Explorer 能展示交易。
6. 社区能说明如何退出、如何验证资产、如何获得支持。

**页面状态：参考组件可用 / 标准化社区发行包规划中（Components Available / Packaged Flow Planned）**
