# Neko MaiBot maintenance fork

这是 [Mai-with-u/MaiBot](https://github.com/Mai-with-u/MaiBot) 的薄维护 fork，
保留完整上游历史、作者归属和原 GPL-3.0/第三方许可，不是独立原创或官方发行。
首个维护基线为 **1.3.15 / 062d45cf8bd4272ac57d7ec03fcf405e5a458211**。
软件包仍使用上游版本号，具体修订以 **upstream SHA + fork SHA** 识别；未向官方 PyPI 包名发布。

## 只保留这四项差异

1. **精确发送回执**：只读 `maisaka.reply.after_send`，携带真实 session/reply/call ID、
   逐段发送结果及实际文字；Hook 失败不改投递结果，不补发，不把 unknown 当成功。
2. **表达选择整体 20 秒协作期限**：超时当轮跳过表达注入继续正文；保留外部取消语义，
   不承诺上游已接请求能硬取消或退费，不改学习和人设。
3. **Life 新摘要输入隔离**：过滤有归属的临时素材和内部任务，真实聊天、引用、已发言、
   工具调用配对及已有摘要保留；不清空历史，不追溯抹掉旧摘要。
4. **Dashboard 锁修正**：只将开发版锁修正为正式 **1.9.9**，其余锁定版本不升级。

[neko-patches.json](neko-patches.json) 是重新构造的公开差异清单，只有上游标识、包版本及源码哈希，
不包含任何实例登记、运行路径、账号、Key 或配置。四源文件与锁已复现既有安装的登记字节；
这不是每次提交都重新验证线上状态。原产品源码未整体格式化，uv.lock 按已验证锁保留 LF 字节。

## 本地验证与 CI

```console
uv sync --locked --group dev
uv run --no-sync python scripts/neko_check.py
uv run --no-sync python scripts/neko_source.py --output <checkout之外的新路径>/maibot-neko-source.zip
```

运行契约前须在仓库外准备 `neko-life`、`neko-tts` 的源码克隆，将环境变量
`NEKO_PLUGIN_FIXTURES` 指向两目录的父目录。固定Life提交 `f6116cfc76943c9bd6b78b47d309478645908a75`、
TTS提交 `7be09dec956fbae6a8600eef5df14cf116e18d57`；测试逐个核对实际消费文件与固定提交字节，
缺失或变化直接失败，不静默skip。CI在兄弟目录checkout它们，不把插件代码打入宿主源码包。
只验证宿主Focus快照与插件消费者、精确回执到Life结算/TTS一次认领，不重跑邻居全库。

- Linux 生产锚点 Python **3.14.4**，Windows 最低 Python **3.12**；SDK **2.16.0**、
  Dashboard **1.9.9** 从同一校验锁安装，不把 latest 当生产环境。
- 运行真实宿主类、真实 SDK，以及回执/取消/摘要/共享 Focus/回复扩展的受影响合成契约，
  不重复七插件全库，不声称覆盖整个上游。测试使用临时实例，禁止真实模型或 QQ 请求；
  唯一网络例外是 Windows 标准库内部创建 asyncio socket pair 的自连接，不放行模型代理或适配器端口。
- 关键组必须非空、每个发现用例实际通过，任何意外 skip/未执行都失败；不靠固定总数守门。
- 1.3.15 原 `test_planner_text_reply.py` 的两个参数化用例在首次运行复现缺少
  `_consecutive_wait_count` 的 fake runtime 错误；仅给该测试 fixture 补真实运行时已有的初值 0。
  不删断言、不改产品行为，也不用全局 autouse 补丁遮盖其他回归。
- 源码包只来自干净确切 Git SHA，验证运行文件成员、五个哈希及临时解压目录真实 SDK 导入，
  检查模块来源，禁止回退可编辑安装源码。ZIP 和附带 JSON 含确切 commit/SHA256，CI artifact 保留 7 天。
  artifact 不是公开 Release，也不是生产发布证明；本仓门禁不冒充七插件上传器门禁。

## 分支与上游同步

- `origin` 为此 fork，`upstream` 为官方仓库；`main` 仅作上游快进镜像，**`neko/main` 为维护默认分支**。
- 每次只选择正式 tag，先 fetch/审查变动，在临时集成分支合并到维护线；逐项判断现有差异是否
  已被上游实现、仍需保留或需要移植，再验证相关行为。不要自动追 main/dev，不强推共享历史。
- GitHub Sync fork 只用于镜像线；不能对维护线使用丢弃提交式同步。
- 上游 16 个 workflow 原样职责留在 `.github/upstream-workflows/`，不在活动 workflow 路径。
  创建后先关闭 Actions；注册过的继承 workflow 逐个禁用，未注册的也不启用，再开放唯一只读 `neko-ci.yml`。
  因镜像线仍含官方 workflow，**每次推镜像前都要先关闭仓库 Actions，检查新增 workflow 并禁用**；
  不能只看维护分支安全就开放镜像流程。仓库默认 token 只读且不能批准 PR，无生产 secrets/OIDC。
- 不向 PyPI、Docker、CNB、Crowdin 自动发布，不自动改依赖、开上游 PR 或部署。
  未来官方新增/更名 workflow 必须先审查，不能假定旧禁用列表永久覆盖。

## 发布与迁移边界

本轮仅建立源码仓及验证，**没有迁移线上宿主**。不收录真实配置、Key、群名单、聊天/摘要/DB、
私有 Prompt、人设、插件运行目录、`.venv` 或私有补丁登记；第三方插件继续独立维护。

首次线上迁移须另获维护/重启授权：在线核对现有五文件与配置，准备已验同版 fork SHA，
说明预计停机窗口后一次停写备份→切换→最小就绪验收。保留旧源码/overlay/登记及匹配运行数据，
不在停服后下载/解依赖，不直接生产 pull/merge，不重跑旧四-overlay升级器，
不让旧源码读已迁移数据。完成源码交付不代表自动允许升级、换模型、QQ试发或重启。
