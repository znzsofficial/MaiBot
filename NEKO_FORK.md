# Neko MaiBot maintenance fork

这是 [Mai-with-u/MaiBot](https://github.com/Mai-with-u/MaiBot) 的薄维护 fork，
保留完整上游历史、作者归属和原 GPL-3.0/第三方许可，不是独立原创或官方发行。
当前源码基线为 **1.3.16 / fe88ec6b6053e40eaf430cb5ba7ed7e805add2cb**；
首个维护基线 1.3.15/062d45cf 的历史与初始补丁提交保留。
软件包仍使用上游版本号，具体修订以 **upstream SHA + fork SHA** 识别；未向官方 PyPI 包名发布。

## 维护差异

1. **精确发送回执**：只读 `maisaka.reply.after_send`，携带真实 session/reply/call ID、
   逐段发送结果及实际文字；Hook 失败不改投递结果，不补发，不把 unknown 当成功。
2. **表达选择整体 20 秒协作期限**：超时当轮跳过表达注入继续正文；保留外部取消语义，
   不承诺上游已接请求能硬取消或退费，不改学习和人设。
3. **Life 新摘要输入隔离**：过滤有归属的临时素材和内部任务，真实聊天、引用、已发言、
   工具调用配对及已有摘要保留；不清空历史，不追溯抹掉旧摘要。
4. **正式依赖锁**：1.3.15阶段修正Dashboard开发版锁；集成1.3.16后按用户追加选择，
   仅定向将SDK **2.16.0→2.17.0**，Dashboard仍 **1.9.10**，其他包版本保持上游正式锁。
5. **显式opt-in可信工具上下文**：仅为工具metadata声明`trusted_context="neko.tools.context.v1"`
   的插件工具构造并覆盖`_host_context`；非opt-in工具保持原行为。
   身份来自实际执行上下文，Focus不能借别群锚点账号，无有效上下文时不给模型信封背书。
    当前用于独立的Neko Files，消费者仍须核实会话/账号和自身授权；不是新增通用放行权限。

[neko-patches.json](neko-patches.json) 是重新构造的公开差异清单，只有上游标识、包版本及源码哈希，
不包含任何实例登记、运行路径、账号、Key 或配置。1.3.15的初始字节审计留在历史；
1.3.16保留原维护行为并合入上游对相同文件的变更，更新五源文件＋锁六项摘要。
本次只更新fork源码与验证，**未把线上1.3.15切换到1.3.16**。不按旧hash重套补丁，
也不把旧文档“未部署身份桥”当现行状态；原产品源码未整体格式化，锁保留LF字节。

### 文件能力的选择

- 继续使用独立 **Neko Files 0.2.3**；不把插件解析器、私有仓或运行数据复制进GPL宿主仓。
- 官方 `capabilities.files` 默认false保持，不自动开第二套索引/下载/文件工具；Neko Files独立名单、
  群目录/OCR开关与现有`neko.tools.context.v1`身份桥保持，不改用`ctx.files`；SDK2.17更新
  是宿主依赖升级，不代表插件切换取源、开放新能力或修改其最低兼容声明。
- 上游的`_file_scope`与本fork的`_host_context`并存；官方文件关闭时仍须允许Files旧链路执行，
  官方文件开启时其临时凭证不应覆盖本fork身份信封，也不能借模型参数选择其他聊天。
- 官方PDF/Office目前只存储收发，不解析；Files仍负责文档/单个压缩包成员读取。
  后续是否复用官方附件底座需另行适配、核验SDK/QQ适配器，并保留插件来源许可审查，非本次任务。
- 现有Files0.2.3的清单仍声明Host≤1.3.15/SDK≤2.16，因此在1.3.16/2.17以宿主兼容模式加载，
  不修改私有插件清单来隐藏提示。已在真实隔离Runner中验证加载、四工具、身份防伪造/跨会话拒绝、
  配置重载与卸载；不是全部格式/OCR或真实QQ的逐项验收，不取消原授权或许可边界。

## 本地验证与 CI

克隆时使用 `git -c core.autocrlf=false clone ...` 保留Git对象字节；已有带改动目录不要批量覆盖重检出。
CI也显式禁用检出换行转换，源码/许可证哈希仍按字节严格核验，不靠放宽CRLF断言通过。

```console
uv sync --locked --group dev
uv run --no-sync python scripts/neko_check.py
uv run --no-sync python scripts/neko_source.py --output <checkout之外的新路径>/maibot-neko-source.zip
```

运行公共契约前须在仓库外准备 `neko-tts` 源码克隆，将环境变量`NEKO_PLUGIN_FIXTURES`
指向其父目录。固定TTS提交 `7be09dec956fbae6a8600eef5df14cf116e18d57`；逐个核对消费文件与
固定提交字节，缺失或变化直接失败、不静默skip。CI只checkout公共TTS，不把插件源码打入宿主包。

Life已退役且仓库改为私有，2026-10-28用户批准解除公共CI的私仓依赖；不增加跨仓secret、不公开源码。
原Life真实集成测试完整保留在`pytests/neko_retired/test_life_bridge.py`；本地显式运行
`uv run --no-sync python scripts/neko_check.py --include-retired-life`时额外要求Life固定提交
`f6116cfc76943c9bd6b78b47d309478645908a75`，缺少源码仍失败，不自动skip。
公共CI不冒称执行私有Life消费者验证；宿主摘要隔离/精确回执/共享Focus保护与实际TTS消费者仍为必跑项。

- Linux 生产锚点 Python **3.14.4**，Windows 最低 Python **3.12**；SDK **2.17.0**、
  Dashboard **1.9.10** 从同一校验锁安装，不把 latest 当生产环境。
- 运行真实宿主类、真实 SDK，以及回执/取消/摘要/共享 Focus/回复扩展的受影响合成契约，
  不重复七插件全库，不声称覆盖整个上游。测试使用临时实例，禁止真实模型或 QQ 请求；
  唯一网络例外是 Windows 标准库内部创建 asyncio socket pair 的自连接，不放行模型代理或适配器端口。
- 关键组必须非空、每个发现用例实际通过，任何意外 skip/未执行都失败；不靠固定总数守门。
- 上游1.3.16删除了维护门禁依赖的`test_context_compaction.py`/`test_planner_text_reply.py`，
  fork保留其回归。旧`set_reply_options`被上游移除，相关断言按新补充编排改为验证同一请求快照、
  自然语言指导、缺快照失败及Focus原reply路径；不恢复废弃产品API或静默删门禁组。
  新增图片在正文前的精确回执、原生文件凭证与旧身份桥共存/取消撤销合成覆盖。
- 源码包只来自干净确切 Git SHA，验证运行文件成员、清单全部哈希及临时解压目录真实 SDK 导入，
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

本轮仅集成正式1.3.16源码及验证，**没有升级线上宿主**。不收录真实配置、Key、群名单、聊天/摘要/DB、
私有 Prompt、人设、插件运行目录、`.venv` 或私有补丁登记；第三方插件继续独立维护。

后续线上升级须另获维护/重启授权：在线核对现有来源与配置，准备已验固定fork SHA，
说明预计停机窗口后一次停写备份→切换→最小就绪验收。保留旧源码/overlay/登记及匹配运行数据，
不在停服后下载/解依赖，不直接生产 pull/merge，不重跑旧四-overlay升级器，
不让旧源码读已迁移数据。完成源码交付不代表自动允许升级、换模型、QQ试发或重启。

1.3.16新增数据库schema46，HTTP监听从`webui.host/port`改归`http.host/port`；
正式切换前必须用最新配置副本验证迁移并保留原监听/端口，不能套默认值覆盖入口。
原fast_model任务超时与宿主整体20秒保护范围不同，不随本次合并改用户模型或移除保护。
