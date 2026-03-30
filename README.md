# acecamp-minutes-ingest

面向用户的 AceCamp 纪要收录工具。

这个 skill 的目标是：把一篇 AceCamp 纪要从页面变成**可复用的本地资产**，并自动做样式一致性校验。

---

## 这套 skill 产出什么

每篇文章默认产出：

- `source.md`
- `rendered.html`
- `share/*.pdf`
- `manifest.jsonl`
- `索引.xlsx`

也就是说，默认就是一套：

> **可搜索 + 可分享 + 可追溯** 的本地入库闭环。

---

## 入口怎么选

### 1. 单篇入库
优先用：

```bash
python3 skills/acecamp-minutes-ingest/scripts/ingest_from_open_page.py \
  --url <详情页URL> \
  --article-id <id> \
  --crawl-date <YYYY-MM-DD> \
  --record-time "YYYY-MM-DD HH:MM:SS +08:00"
```

适用：
- 浏览器里已经打开 AceCamp 详情页
- 想补一篇 / 指定一篇 / 手工录一篇

### 2. 搜索 / 关键词入库
优先用：

```bash
python3 skills/acecamp-minutes-ingest/scripts/search_and_ingest.py \
  --keyword <关键词> \
  --snapshot-path <minutes_snapshot.txt> \
  --window-days 3
```

适用：
- 想按关键词找文章
- 想批量补未入库文章

### 3. 已有 source 的下游处理
如果你已经有 `source.md`，直接用：

- `scripts/ingest_one.py`

它不是顶层主入口，而是：

> **source 级下游处理器**

负责：
- html 渲染
- pdf 导出
- manifest/index 同步
- 最终校验

---

## 最小流程

### 第一次跑
```bash
python3 skills/acecamp-minutes-ingest/scripts/preflight_check.py
```

通过后再开始入库。

### 日常单篇
1. 确认登录态正常
2. 打开详情页
3. 跑 `ingest_from_open_page.py`

### 日常搜索
1. 确认登录态正常
2. 准备搜索结果 snapshot
3. 跑 `search_and_ingest.py`

---

## 当前结构（简版）

### 顶层入口
- `scripts/ingest_from_open_page.py`
- `scripts/search_and_ingest.py`
- `scripts/preflight_check.py`

### 下游处理器
- `scripts/ingest_one.py`

### 内部实现层
都已沉到：
- `scripts/lib/`

例如：
- `lib/detail_extractor.py`
- `lib/source_builder.py`
- `lib/html_renderer.py`
- `lib/pdf_renderer.py`
- `lib/index_updater.py`
- `lib/output_validator.py`

---

## 关键规则（用户需要知道的版本）

- 登录 / 风控判断一律以**页面真实可见状态**优先。
- 正文必须保留页面可见原文，不能摘要改写。
- 问句和章节标题必须按 `### ` 标记，保证 rendered 蓝色样式。
- 图片要本地化到 `acecamp-raw/assets/<article_id>/`。
- 若 rendered 丢失图片或样式映射，必须视为失败。
- 若发布人为“共享调研纪要”，联合发布人规则必须正确处理。

---

## 命名规则

统一文件名按：

`文章日期_provider_文章id_文章名_crawl_date`

---

## 产物位置

- `acecamp-raw/source/`：纯文本原文
- `acecamp-raw/rendered/`：渲染 HTML（仅放 HTML）
- `acecamp-raw/share/`：共享 PDF（仅放 PDF）
- `acecamp-raw/index/manifest.jsonl`：机器索引
- `acecamp-raw/index/索引.xlsx`：人工索引

---

## 回归与自检

改脚本后建议跑：

```bash
python3 skills/acecamp-minutes-ingest/scripts/regression_samples_check.py
```

当前已经纳入正式覆盖的样本包括：
- `70560221`
- `70560289`

---

## 常用辅助脚本

- `scripts/login_policy.py`：登录策略输出入口（不是执行器）
- `scripts/log_issue.py`：补写错误日志
- `scripts/validate_staged_sources.py`：pre-commit 校验

---

## 参考文档

- Agent 执行规则：`skills/acecamp-minutes-ingest/SKILL.md`
- 脚本目录说明：`skills/acecamp-minutes-ingest/scripts/README.md`
- 渲染说明：`skills/acecamp-minutes-ingest/references/TEMPLATE_USAGE.md`
- 字段映射：`skills/acecamp-minutes-ingest/references/field-map.md`
