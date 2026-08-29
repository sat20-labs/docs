# 部署 Launchpad

当前代码中存在LaunchPool/Launchpad相关通道合约运行时和测试，但当前PWA发布范围没有独立的公开Launchpad部署入口。部署资产或mint完成可以触发既有市场侧流程，并不自动证明一个面向外部开发者的Launchpad产品已经开放。

开放前必须固定：资产部署/mint前置、合约peer、募集资产、价格和上限、成功/失败/退款规则、AMM衔接、管理员权限、测试网登记表和真实资产核账。任何合约缺少对应资产时，应先检查peer同步和部署状态，不能临时伪造资产或跳过前置。

**页面状态：底层运行时与测试存在；公开部署流程未开放（Runtime Exists / Public Flow Unavailable）**
