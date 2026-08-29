# 监控、备份与升级

节点和基础设施运行者需要可重复的监控、备份、升级和恢复流程。

## 最小监控面

1. 节点高度、peer、mempool 和出块状态。
2. L1/L2 indexer 高度和 reorg 状态。
3. STP 通道和合约状态。
4. 数据目录、钱包目录和关键数据库备份。
5. 版本升级、回滚和兼容性检查。
6. 告警、日志和公开状态页。

每项至少同时记录“进程是否存活”和“业务是否前进”。例如节点存活但区块不增长、Indexer进程存活但tip落后、STP在线但通道commit不收敛，都应告警。

## 备份边界

| 数据 | 要求 |
| --- | --- |
| 链与Indexer | 记录网络、tip高度/hash、DB backend和代码版本；恢复后先做一致性校验 |
| STP钱包/通道 | 加密备份钱包、当前通道、commitment、watchtower和reservation；不得与链快照混为可随意删除的数据 |
| 合约 | 保存部署tx、invoke history和运行状态证据；通道双方分别备份 |
| DKVS | 备份endpoint identity、record、change log和cursor head必须来自同一时点；只复制record会破坏watch连续性 |
| 配置/密钥 | 配置可版本化，私钥、助记词、API凭据和撤销秘密进入受控秘密存储 |

## 升级流程

1. 冻结候选commit和所有未提交diff，编译后记录产物hash。
2. 先跑对应单元/虚拟网络/E2E，再在测试网验证；`transcend TestRunAll`不得并发运行。
3. 升级前记录pending交易和reservation。已广播动作必须继续监控，不能因服务重启或120秒超时被判失败。
4. 分批升级并比较共同高度hash、Indexer tip、peer、合约状态和STP服务。
5. PWA升级发布后不强制接管正在运行的旧页面；提示用户关闭后重开，保留旧release cache直到新页面READY。
6. 回滚只恢复已批准的数据范围。SatoshiNet测试网回滚不是生产功能，主网必须拒绝。

## 恢复与告警原则

- 网络结果未知按“可能成功”处理，不自动重发或删除resv/合约。
- 通道双方状态分叉先找共同commit/invoke起点；不能用自动删除掩盖根因。
- 磁盘、证书、DNS、反向代理和上游Indexer异常需要独立告警。
- 每次恢复都留下时间、操作者、版本、备份、命令、输出和复核结果。

**页面状态：可执行基线 / 持续完善（Operational Baseline / Iterating）**
