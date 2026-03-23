# acecamp-minutes-ingest

面向用户的 AceCamp 纪要收录工具说明。

## 这个 skill 做什么

把 AceCamp 纪要文章标准化收录到本地目录：

- `acecamp-raw/source/`：源记录（markdown）
- `acecamp-raw/rendered/`：渲染页面（html）
- `acecamp-raw/index/manifest.jsonl`：机器索引
- `acecamp-raw/index/索引.xlsx`：人工索引

并强制执行：
- 命名规则：`文章日期_provider_文章id_文章名_crawl_date`
- 每篇收录后关闭新开的工作标签页
- 详情抓取报错时立即停止，禁止自动重试（反爬严格）
- source 正文必须是页面可见原文，不得摘要改写
- 问句行必须用 `### ` 标记，保证 rendered 中问题标题显示为蓝色
- 正文提取以“有实质正文文本”为准；中英文锚点（`以下是专家观点：` / `Expert Opinions:`）仅作辅助，不是必需条件

需要注意：AceCamp 对单个用户反爬较严格，不要过度抓取。根据观察，每日新纪要大致在 **10–30 篇**（以当日实际更新为准），建议分批分时入库。

---

## 依赖与前置

### 必需
- Python 3
- `openpyxl`
- 浏览器控制可用（能打开并操作 AceCamp 页面）
- 告警配置（`alert_channel` + `alert_target`）已配置

### 若使用用户浏览器通道
- 用户浏览器/插件 attach 成功，可在同一 tab 连续执行

### 反爬约束（硬规则）
- 详情页抓取报错即停，禁止自动重试。
- 若出现验证码/风控页/详情页字段缺失，立即停止并告警。

如果缺少配置，预检会失败。

---

## 浏览器标签页策略（默认）

- 打开主页或文章页前，先检查已有 tabs。
- 有可复用目标页就复用 `targetId`，没有再新开。
- 每篇收录后仅关闭“本次新开”的详情页，避免标签堆积。
- 可用脚本：

```bash
python3 skills/acecamp-minutes-ingest/scripts/workflow_helpers.py resolve-tab \
  --tabs-json '<tabs_json>' \
  --match-url 'acecamptech.com/search?type=minutes'
```

- 强制拦截“有 tab 还 open 新 tab”（硬约束）：

```bash
python3 skills/acecamp-minutes-ingest/scripts/workflow_helpers.py guard-open \
  --resolve-json '<resolve_tab_output_json>' \
  --planned-action open
```

若存在可复用 tab，上述命令会返回 `OPEN_BLOCKED_REUSE_REQUIRED` 并以非 0 退出。

- 选文可用脚本（默认最近窗口 + 未入库过滤）：

```bash
python3 skills/acecamp-minutes-ingest/scripts/workflow_helpers.py pick-candidates \
  --snapshot-path <minutes_snapshot.txt> \
  --manifest-path acecamp-raw/index/manifest.jsonl \
  --window-days 3
```

## 快速开始

### 0) 执行前指引（细化要求）

- 默认只处理今天/最近 3 天且本地未入库文章。
- 日常入库和补漏都按页面可见内容直接判断（不引入额外行业分组规则）。
- 若你要补历史旧文，必须在指令里明确写“补漏/回补 + 指定日期或ID”。
- source 必须保留页面可见原文；问句行必须以 `### ` 开头（保证 rendered 蓝色问题样式）。

### 1) 预检（首次必须）

```bash
python3 skills/acecamp-minutes-ingest/scripts/preflight_check.py
```

通过条件：输出 `PREFLIGHT_OK`。若失败，按报错修复后重跑。

如果提示 hook 未安装，执行：

```bash
bash skills/acecamp-minutes-ingest/git-hooks/install.sh
```

hook 说明见：
- `skills/acecamp-minutes-ingest/git-hooks/HOOK.md`

### 2) 从详情抽取为标准 source（推荐）

```bash
python3 skills/acecamp-minutes-ingest/scripts/extract_detail_to_source.py \
  --detail-json <detail.json> \
  --output <input_md> \
  --record-time "YYYY-MM-DD HH:MM（Asia/Shanghai）" \
  --source-url <详情页URL> \
  --article-id <id>
```

### 3) 单命令执行（校验 + 渲染 + 索引同步）

```bash
python3 skills/acecamp-minutes-ingest/scripts/ingest_one.py \
  --source-path <input_md> \
  --rendered-path <output_html> \
  --source-url <详情页URL> \
  --record-time "YYYY-MM-DD HH:MM（Asia/Shanghai）" \
  --article-id <id> \
  --article-date <YYYY-MM-DD> \
  --provider acecamptech \
  --article-title "<title>" \
  --crawl-date <YYYY-MM-DD> \
  --content-type "<类型>" \
  --industry "<行业>" \
  --tags "<tag1, tag2,...>" \
  --author "<作者>" \
  --co-publisher "<联合发布人，可选>" \
  --min-body-chars 300
```

说明：长文若正文过短会被 `ingest_one.py` 直接拦截失败，防止“漏录正文”入库。

另外，`ingest_one.py` 会在入库后自动做行业/标签一致性检查（以 source 为准）：
- 默认：发现不一致时自动修正并记入 error-log（不中断）
- 严格模式：加 `--strict-consistency`，发现不一致后自动修正并返回失败
- 配置联动：`config.json` 的 `strict_consistency` / `min_body_chars` 会作为默认值，CLI 传参可覆盖

---

## 默认选文规则（重要）

- 默认只处理今天/最近 3 天的纪要。
- 且必须是本地未入库（`manifest.jsonl` 不存在该 `article_id`）。
- 历史旧文仅在你明确说“补漏/回补”时处理。

## SAMPLE USAGE

- 看最近 3 天 AI/TMT/半导体纪要里，哪些还没入库。
- 每小时补录 2 篇未入库的科技纪要（优先 AI/TMT）。
- 只收录“今天发布且属于 AI/TMT/半导体”的纪要，并同步 source/rendered/manifest/索引。
- 指定文章 ID（如 70559969）执行单篇补录，完成后自动更新 manifest 与索引。
- 先做缺口检查（today minutes vs manifest），只对缺失项执行入库。
- 对已入库文章重渲染（rendered 样式更新后批量刷新 html，不改 source 正文）。
- 抓取时如遇风控/验证码/字段缺失，立即停止并通过告警通道通知。
- 按行业做批次任务：先 AI，再 TMT，再半导体，每批 1~3 篇，分时执行。
- 每日收盘前跑一次“科技纪要补齐”，确保当天科技相关 minutes 无漏录。

---

## 错误日志

- 运行中断会记录到：`acecamp-raw/logs/error-log.jsonl`
- 人工评审指出的问题（HumanRaisedIssue）也要追加到同一日志，避免漏复盘。
- 建议每周回顾一次高频错误，持续优化规则与脚本。
- 日志字段与示例见：`skills/acecamp-minutes-ingest/logging.md`
- 推荐使用命令追加，避免手写 JSON 出错：

```bash
python3 skills/acecamp-minutes-ingest/scripts/log_issue.py \
  --article-id 70560077 \
  --stage human_review \
  --error-type HumanRaisedIssue \
  --message "要点/正文提取不完整，问题未蓝化" \
  --source-url https://www.acecamptech.com/article/detail/70560077
```

## 回归样本一键自检

每次改动脚本后，建议先跑：

```bash
python3 skills/acecamp-minutes-ingest/scripts/regression_samples_check.py
```

默认覆盖 3 个已知风险样本：
- `70560067`（中文锚点）
- `70560083`（英文锚点）
- `70560077`（中文问号蓝色样式）

## 常见问题

### Q1: 为什么预检失败？
通常是：
- `config.json` 不存在（会自动从 example 生成）
- `alert_target` 仍是占位符
- `openpyxl` 未安装

### Q2: 报错后会自动重试吗？
不会。详情抓取报错会立即停止并报错，避免触发 AceCamp 反爬。

### Q3: 这套文件路径能改吗？
可以，改 `config.json` 的 `out_root/source_dir/rendered_dir/index_dir`。

---

## 参考文档

- Agent 执行规则：`skills/acecamp-minutes-ingest/SKILL.md`
- 渲染模板用法：`skills/acecamp-minutes-ingest/references/TEMPLATE_USAGE.md`
- 字段映射：`skills/acecamp-minutes-ingest/references/field-map.md`
