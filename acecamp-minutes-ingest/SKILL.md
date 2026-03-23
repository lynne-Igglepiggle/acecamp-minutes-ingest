---
name: acecamp-minutes-ingest
description: Ingest AceCamp articles (especially 科技向纪要) into local knowledge files with a strict, human-reviewed workflow. Use when user asks to collect/录入 AceCamp 内容, create source+rendered files, sync manifest/index, enforce filename convention, or check missing daily minutes.
---

# acecamp-minutes-ingest

Execute AceCamp ingestion in this fixed order.

## 0) Core rules

- Use filename convention:
  - `文章日期_provider_文章id_文章名_crawl_date`
- For each article, produce all of:
  - source markdown
  - rendered html (template style)
  - manifest upsert
  - Excel index upsert
- After finishing one article, close the newly opened working tab.


## -1) Prerequisites (must check before run)

### Required
- Python 3 available (`python3`)
- `openpyxl` installed (for `索引.xlsx` write)
- Browser control available (can open and operate AceCamp pages)

### Required config file
- If `skills/acecamp-minutes-ingest/config.json` is missing, preflight auto-creates it from `config.example.json`
- Required fields:
  - path: `out_root`, `source_dir`, `rendered_dir`, `index_dir`
  - alert: `alert_channel`, `alert_target`
  - runtime: `timezone`, `minutes_url`
- If user-browser mode is used, browser/plugin attach must be completed before ingest.
- If missing/invalid, preflight must fail.

### Preflight command
```bash
python3 skills/acecamp-minutes-ingest/scripts/preflight_check.py
```

If preflight reports missing alert config, stop and show:
- `FAIL alert_channel/alert_target not configured in config.json`

## 1) Page workflow

1. Before opening any page, check existing browser tabs.
   - If target tab already exists (minutes list or target article detail), reuse its `targetId`.
   - Open new tab only when no reusable tab is found.
   - Helper: `python3 skills/acecamp-minutes-ingest/scripts/workflow_helpers.py resolve-tab --tabs-json '<tabs_json>' --match-url '<url_substring>'`
2. Open minutes page: `https://www.acecamptech.com/search?type=minutes`
2. Check login state.
3. If not logged in, ask user to login manually (and send configured reminder channel if requested by user workflow).
4. Filter scope if user requested (simple direct judgment based on visible page content).
5. Identify target article ID from list (`/article/detail/<id>`).
   - Default window: today / recent 3 days only.
   - Must be not yet ingested in local manifest.
   - Older articles only when user explicitly asks for backfill.
   - Helper picker: `python3 skills/acecamp-minutes-ingest/scripts/workflow_helpers.py pick-candidates --snapshot-path <minutes_snapshot.txt> --manifest-path acecamp-raw/index/manifest.jsonl`
6. Open detail page and extract visible full content + metadata.
   - Prefer using `extract_detail_to_source.py` to generate standardized source markdown from structured detail json.
   - Body extraction must support both CN and EN anchors (e.g., `以下是专家观点：` / `Expert Opinions:`).
   - If either anchor exists, corresponding body must be captured into source正文 (not empty).
7. If opening detail page or extracting content throws any error, stop immediately and report the exact error. Do NOT auto-retry (AceCamp anti-bot is strict).
8. Source正文必须保留页面可见原文，不得摘要改写。
9. 正文中的问句行（例如“Chris：...？”或英文问句）必须用 `### ` 标记为问题标题，以触发 rendered 蓝色问题样式。
10. `ingest_one.py` 内置硬门禁校验：正文文本非空、非占位，且长文（元数据>=800字）正文长度不得低于阈值（默认300字符），否则直接失败。
11. 入库后自动执行 industry/tags 一致性校验（以 source 为准）：默认自动修正+记日志；`--strict-consistency` 时修正后返回失败。

## 2) Metadata to capture (minimum)

- article_id
- 标题
- 内容类型
- 权限
- 标识
- 行业
- 发布时间
- 阅读
- 点赞
- 字数/阅读时长
- VIP状态
- 要点
- 正文（完整）
- 智能追问
- 标签
- 专家简介字段
- 发布人
- 发布人说明
- 联合发布人（若发布人为“共享调研纪要”时必填）

## 3) File outputs

### source

Write source markdown under:
- `acecamp-raw/source/<convention>.md`

### rendered

Render via:
- `skills/acecamp-minutes-ingest/scripts/render_template.py`

Command pattern:

```bash
python3 skills/acecamp-minutes-ingest/scripts/render_template.py \
  <source_md> \
  <rendered_html> \
  --source-url <detail_url> \
  --record-time "YYYY-MM-DD HH:MM（Asia/Shanghai）" \
  --article-id <id>
```

## 4) Sync machine+human indexes

Upsert both with one command:

```bash
python3 skills/acecamp-minutes-ingest/scripts/upsert_index_manifest.py \
  --article-id <id> \
  --article-date <YYYY-MM-DD> \
  --provider acecamptech \
  --article-title "<title>" \
  --crawl-date <YYYY-MM-DD> \
  --source-url <detail_url> \
  --record-time "YYYY-MM-DD HH:MM（Asia/Shanghai）" \
  --source-path <relative_source_path> \
  --rendered-path <relative_rendered_path> \
  --content-type "<类型>" \
  --industry "<行业>" \
  --tags "<tag1, tag2,...>" \
  --author "<作者>"
```

This updates:
- `acecamp-raw/index/manifest.jsonl`
- `acecamp-raw/index/索引.xlsx`

## 5) Daily missing check (tech scope)

1. Read today’s minutes list.
2. Determine target IDs by direct judgment from visible page content.
3. Compare article_id set against manifest article_id set.
4. Report “missing IDs + title”.

## 6) Completion checklist

- [ ] source written
- [ ] rendered written
- [ ] manifest synced
- [ ] index synced
- [ ] tab closed
- [ ] git commit done

If any checkbox fails, do not claim completion.
