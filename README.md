# acecamp-minutes-ingest

面向用户的 AceCamp 纪要收录工具。

这个 skill 的目标是：把一篇 AceCamp 纪要从页面变成**可复用的本地资产**，并自动做样式一致性校验。

---

## skill说明

1. 抓取 AceCamp 的详情内容（保留原文）
2. 生成标准化 `source.md`
3. 生成展示样式 `rendered.html`
4. 自动生成 `rendered.pdf`（用于分享）到 `acecamp-raw/share/`
5. 同步 `manifest` 和 `索引`
6. 做一次保真验收（红字/蓝字/加粗/列表/图片）

> 结论：默认就是“**可搜索 + 可分享 + 可追溯**”的一套入库闭环。

---

## 这套 Skill 适合什么人用

- 你有一批 AceCamp 纪要要长期沉淀（AI/TMT/半导体）
- 你想保留原文并且不想每次手工改格式
- 你希望每篇都有可复核产物（html + pdf + manifest + 索引）
- 你想避免重复抓取已入库文章

---

## 推荐prompt模版

- 按 acecamp-minutes-ingest SKILL 流程和脚本入库 [防止agent自我发挥，少录入字段、字段错乱、触发反爬等问题]
- 可选：时间窗口、行业、搜索关键词、batchsize，etc.
- 可以规定mode：如特定单篇single、关键词keyword等

---

## 流程

### 0) 预检（第一次用请先跑）

```bash
python3 skills/acecamp-minutes-ingest/scripts/preflight_check.py
```

通过条件：
- `PREFLIGHT_OK`
- 会自动检查并创建目录：
  - `acecamp-raw/source`
  - `acecamp-raw/rendered`
  - `acecamp-raw/index`
  - `acecamp-raw/share`（PDF 共享目录）
- 会检查 `config.json`、`openpyxl`、`playwright`、pre-commit hook

如果缺 hook：

```bash
bash skills/acecamp-minutes-ingest/git-hooks/install.sh
```

---

### 1) 通用流程（适用于所有场景）

```text
1. 预检通过：preflight_check.py
2. 抓取/抽取原文：extract_detail_to_source.py（或已有 source 时跳过）
3. 生成 rendered：render_template.py（在 ingest_one 内部已调用 render_file）
4. 质量验真：validate_ingest_output.py（在 ingest_one 内部已自动执行）
5. 生成分享 PDF：render_pdf.py（到 acecamp-raw/share/）
6. 同步索引：manifest + 索引.xlsx（在 ingest_one 内部执行）
7. 一致性修复：industry/tags 与 source 冲突时自动修正并记录日志
8. 入库完成：输出 INGEST_ONE_OK 与产物路径
```

如果你已经有 `source.md`，可以直接从第 3 步开始；如果是从页面抓取，先从第 2 步开始。

### 1.1) 流程图（你只要按箭头走）

```text
[输入源]
   |
   |-- 有 source.md? ----是----> [2. 用 ingest_one 渲染/验真/落库]
   |                          |
   |                          +--> [3. 检查 share/output 与索引]
   |
   +-- 否 --> [1. 用 extract_detail_to_source 抽取 source]
                              |
                              +--> [2. 用 ingest_one 渲染/验真/落库]
```

### 1.2) 场景选择树（选对入口）

```text
你想要什么？
│
├─ 想补一篇/手工指定一篇 → 走「2) 单篇入库」
├─ 想按关键词抓一批       → 走「3) 关键词批量入库」
└─ 只想确认一次流程全貌   → 直接看「1) 通用流程」
```

---

### 2) 单篇入库（最直接）

**两步必备：**

1. 先拿到标准化 `source.md`（`extract_detail_to_source.py`）
2. 再用 `ingest_one.py` 完成入库 + 校验 + 共享文件生成

```bash
python3 skills/acecamp-minutes-ingest/scripts/extract_detail_to_source.py \
  --detail-json <detail.json> \
  --output <acecamp-raw/source/...md> \
  --record-time "YYYY-MM-DD HH:MM（Asia/Shanghai）" \
  --source-url <详情页URL> \
  --article-id <id>

python3 skills/acecamp-minutes-ingest/scripts/ingest_one.py \
  --source-path <acecamp-raw/source/...md> \
  --rendered-path <acecamp-raw/rendered/...html> \
  --source-url <详情页URL> \
  --record-time "YYYY-MM-DD HH:MM（Asia/Shanghai）" \
  --article-id <id> \
  --article-date <YYYY-MM-DD> \
  --provider acecamptech \
  --article-title "<标题>" \
  --crawl-date <YYYY-MM-DD> \
  --content-type "纪要" \
  --industry "<行业>" \
  --tags "<tag1,tag2>" \
  --author "<作者>" \
  --co-publisher "<共享发布人，可选>" \
  --min-body-chars 300
```

执行后会输出：

- `acecamp-raw/source/<命名规则>.md`
- `acecamp-raw/rendered/<命名规则>.html`
- `acecamp-raw/share/<命名规则>.pdf`
- 更新/新增：`acecamp-raw/index/manifest.jsonl`
- 更新：`acecamp-raw/index/索引.xlsx`

---

### 3) 关键词批量入库（你要求“关键词=xxx”的常用场景）

用流程：先搜索+筛选未入库，再逐条入库。

```bash
python3 skills/acecamp-minutes-ingest/scripts/workflow_helpers.py pick-candidates \
  --snapshot-path <minutes_snapshot.txt> \
  --manifest-path acecamp-raw/index/manifest.jsonl \
  --window-days 3
```

> 注意：默认只处理最近窗口 + 本地未入库，避免重复；历史回补请手动指定“补漏”意图。

---

## 命名规则（最重要）

统一文件名（source/rendered/share）都按：

`文章日期_provider_文章id_文章名_crawl_date`

示例：

`2026-03-11_acecamptech_70559685_存储测试机专家访谈-存储CPFT测试机扩产需求..._2026-03-27.html`

---

## 产物位置（用户最关心）

- `acecamp-raw/source/`：纯文本原文（人审友好）
- `acecamp-raw/rendered/`：渲染 HTML（样式保真）
- `acecamp-raw/share/`：共享 PDF（外部查看/转发）
- `acecamp-raw/index/manifest.jsonl`：机器索引（入库状态）
- `acecamp-raw/index/索引.xlsx`：人工索引（行业/标签汇总）

---

## 你最担心的两个问题（先说结论）

### Q1 为什么我看不到图片？

请先确认 PDF 是否从本机打开；`rendered.html` 使用相对资源（assets），PDF 已单独落 `share`，用于对外展示更稳。

### Q2 为什么有时没入库？

常见原因：
- source 正文为空或长度阈值不达标（`--min-body-chars`）
- `manifest/index` 结构未对齐（会自动修复，并记录）
- 页面反爬或字段缺失（会停止，建议人工确认后重试）

---

## 质量约束（避免踩坑）

- `source` 正文必须保留页面可见原文，不得改写
- 问句/章节标题需按 `### ` 标题化（保证蓝色样式）
- 图片下载失败会记录日志（可定位）
- `ingest_one.py` 内置校验：
  - `source` 有效
  - 长文长度阈值（默认 300）
  - `rendered` 与 `source` 样式映射保真
- 图片异常/样式丢失会判定为失败

---

## 验收与回归（建议每次改脚本后执行）

```bash
python3 skills/acecamp-minutes-ingest/scripts/validate_ingest_output.py \
  --source <source.md> \
  --rendered <rendered.html>

python3 skills/acecamp-minutes-ingest/scripts/regression_samples_check.py
```

---

## 常见问题（排障）

- 预检失败：通常是 `config.json` 缺失/占位、`openpyxl` 或 `playwright` 未装、hook 未装
- 抓取报错：详情页字段缺失、验证码、风控 —— 建议先人工确认后再重试（本 skill 设计为“失败即停”）
- 想回看日志：`acecamp-raw/logs/error-log.jsonl`

详细日志追加可用：

```bash
python3 skills/acecamp-minutes-ingest/scripts/log_issue.py \
  --article-id <id> \
  --stage human_review \
  --error-type HumanRaisedIssue \
  --message "..."
```

---

## 你会经常用到的“最小流程”

1. `preflight_check.py`
2. `extract_detail_to_source.py`
3. `ingest_one.py`
4. `validate_ingest_output.py`（可选，入库脚本会自动执行）
5. 如有样式修改后，请 `regression_samples_check.py`

这样就能快速确认“这篇是否合格、是否可分享、是否已入库”。

---

## 参考文档

- Agent 执行规则：`skills/acecamp-minutes-ingest/SKILL.md`
- 渲染模板用法：`skills/acecamp-minutes-ingest/references/TEMPLATE_USAGE.md`
- 字段映射：`skills/acecamp-minutes-ingest/references/field-map.md`
