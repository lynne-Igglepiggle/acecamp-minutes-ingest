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
- Browser control available (OpenClaw browser tool for auto-login)

### Required config file
- **⚠️ 安全提示**: 敏感配置(密码等)请放在 `acecamp-raw/config.json`,不要放在 skill 目录下
- 首次使用会**自动提示输入**账号密码,或手动创建: `cp skills/acecamp-minutes-ingest/config.example.json acecamp-raw/config.json`
- Required fields:
  - path: `out_root`, `source_dir`, `rendered_dir`, `index_dir`
  - alert: `alert_channel`, `alert_target`
  - runtime: `timezone`, `minutes_url`
  - auto_login (optional but recommended): `enabled`, `max_retries`, `credentials.type/account/password`
- If user-browser mode is used, browser/plugin attach must be completed before ingest.
- If missing/invalid, preflight must fail.

### Preflight command
```bash
python3 skills/acecamp-minutes-ingest/scripts/preflight_check.py
```

If config missing or credentials are placeholder, preflight will **interactively prompt** for account/password.

## 1) Page workflow

### 1.1) Login State Detection & Handling

**Login Detection Method:**
- Open `https://www.acecamptech.com/search?type=minutes`
- Check for login indicators in page:
  - **Logged in**: User avatar/用户名 visible in top-right corner
  - **Logged in**: Can see VIP content (e.g., "VIP" labels on articles)
  - **Logged in**: "发布人" section shows actual author names, not placeholders
  - **Not logged in**: Redirect to login page or show "请登录" prompts
  - **Not logged in**: Article list shows limited/free content only

**Login State Verification Script:**
```javascript
// Check login via browser evaluate
() => {
  const userMenu = document.querySelector('.user-menu, .avatar, [class*="user"]');
  const vipLabels = document.querySelectorAll('.vip-label, [class*="vip"]');
  const loginPrompt = document.querySelector('.login-prompt, .please-login');
  return {
    isLoggedIn: !!(userMenu || vipLabels.length > 0),
    hasLoginPrompt: !!loginPrompt,
    userElement: userMenu ? userMenu.textContent?.trim() : null
  };
}
```

**If NOT Logged In:**
1. **Check if auto-login is enabled** in config.json (`auto_login.enabled`)
2. **If enabled:**
   - Load credentials from `auto_login.credentials` (account + password)
   - Use OpenClaw browser tool to perform login:
     - Navigate to login page
     - Click "密码登录"
     - Fill phone/email and password
     - Check "我已阅读并同意"
     - Click "登录"
   - **Retry up to `auto_login.max_retries` times** (default: 2)
   - After each failed attempt, wait 3 seconds and retry
3. **Verify login success** by checking for user avatar/name in page
4. **If auto-login fails after max retries:**
   - **Alert user** via configured channel (alert_channel/alert_target in config.json)
   - **Message template**:
     ```
     AceCamp 自动登录失败(已重试{X}次):
     - 账号: {account}

     请手动登录后回复"已登录"继续:
     1. 打开 https://www.acecamptech.com
     2. 使用微信扫码或账号密码登录
     3. 确认看到右上角头像后回复"已登录"
     ```
   - **Wait for user confirmation** before proceeding
5. **If auto-login is disabled:**
   - Alert user to enable it or manually login

**Session Persistence:**
- AceCamp uses cookie-based sessions
- If user reports "frequent logout", suggest checking browser cookie settings

### 1.2) Normal Page Workflow

1. Before opening any page, check existing browser tabs.
   - If target tab already exists (minutes list or target article detail), reuse its `targetId`.
   - Open new tab only when no reusable tab is found.
   - Helper: `python3 skills/acecamp-minutes-ingest/scripts/workflow_helpers.py resolve-tab --tabs-json '<tabs_json>' --match-url '<url_substring>'`
2. Open minutes page: `https://www.acecamptech.com/search?type=minutes`
3. **Verify login state** (see 1.1 above). If not logged in, trigger auto-login flow (see 1.1 "If NOT Logged In").
4. Filter scope if user requested (simple direct judgment based on visible page content).
5. Identify target article ID from list (`/article/detail/<id>`).
   - Default window: today / recent 3 days only.
   - Must be not yet ingested in local manifest.
   - Older articles only when user explicitly asks for backfill.
   - Helper picker: `python3 skills/acecamp-minutes-ingest/scripts/workflow_helpers.py pick-candidates --snapshot-path <minutes_snapshot.txt> --manifest-path acecamp-raw/index/manifest.jsonl`
6. Open detail page and extract visible full content + metadata.
   - Prefer using `extract_detail_to_source.py` to generate standardized source markdown from structured detail json.
   - Body extraction must support both CN and EN anchors (e.g., `以下是专家观点:` / `Expert Opinions:`).
   - If either anchor exists, corresponding body must be captured into source正文 (not empty).
7. If opening detail page or extracting content throws any error, stop immediately and report the exact error. Do NOT auto-retry (AceCamp anti-bot is strict).
8. Source正文必须保留页面可见原文,不得摘要改写。
9. 正文中的问句行(例如"Chris:...?"或英文问句)必须用 `### ` 标记为问题标题,以触发 rendered 蓝色问题样式。
10. 正文中的章节标题行(例如"二、 磷化铟原材料""三、 磷化铟的制造封测"等)也必须用 `### ` 标记,确保 rendered 中统一蓝色标题样式。
11. 正文样式保真为硬要求:红字、加粗、列表缩进在 rendered 中必须可见。
12. 若正文包含图片,必须执行本地化下载到 `acecamp-raw/assets/<article_id>/`,并在 rendered 中按原文位置顺序渲染。
13. 图片下载失败可回退外链,但必须记录失败日志(article_id、原URL、错误原因)。
14. `ingest_one.py` 内置硬门禁校验:正文文本非空、非占位,且长文(元数据>=800字)正文长度不得低于阈值(默认300字符),否则直接失败。
15. 入库后自动执行 industry/tags 一致性校验(以 source 为准):默认自动修正+记日志;`--strict-consistency` 时修正后返回失败。
16. 质检门禁:若原文有图片但 rendered 图片数为 0,或原文样式标记在 rendered 丢失,必须判失败,不得宣称完成。

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
- 正文(完整)
- 智能追问
- 标签
- 专家简介字段
- 发布人
- 发布人说明
- 联合发布人(若发布人为"共享调研纪要"时必填)

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
  --record-time "YYYY-MM-DD HH:MM(Asia/Shanghai)" \
  --article-id <id>
```

### share output (pdf)

- `render_pdf.py` will render `<rendered_html>.pdf` and copy it to `acecamp-raw/share/` as sharing artifact.
- This is done in `ingest_one.py` by default after rendered/html validation and index sync.

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
  --record-time "YYYY-MM-DD HH:MM(Asia/Shanghai)" \
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

1. Read today's minutes list.
2. Determine target IDs by direct judgment from visible page content.
3. Compare article_id set against manifest article_id set.
4. Report "missing IDs + title".

## 6) Keyword-based article ingestion (关键词入库流程)

When user wants to ingest articles matching specific keywords (e.g., "帮我入库所有关于 HBM 的文章"):

### 6.1 Search workflow

1. **Open search page**: Navigate to `https://www.acecamptech.com/search?type=minutes`
2. **Verify login state** (see 1.1). Must be logged in to access VIP content.
3. **Enter keyword**: Type keyword in search box (顶部搜索框 `searchbox "请输入关键词"`)
4. **Submit search**: Press Enter or click "搜索" button
5. **Filter by content type**: Click "纪要" tab to filter for minutes only
   - URL changes to: `https://www.acecamptech.com/global_search?keyword=<keyword>`
   - Note: The "纪要" tab shows `[active] [selected]` when selected

### 6.2 Extract search results

From the search results page, extract for each article:
- **article_id**: From URL `/article/detail/<id>`
- **标题**: Article title text
- **摘要/预览**: Content preview snippet
- **发布时间**: Date/time (e.g., "2026/03/04 17:04" or "1天前")
- **作者**: Author name (e.g., "Patrick", "Leo Gao")
- **内容类型**: Always "纪要" when filtered
- **标签/认证**: "认证专业数据源", "行业专家", "VIP", etc.

### 6.3 Deduplication check

For each found article:
1. Check if article_id exists in `acecamp-raw/index/manifest.jsonl`
2. Skip if already ingested
3. Collect new article_ids for ingestion

### 6.4 Batch ingestion

For each new article:
1. Open detail page: `https://www.acecamptech.com/article/detail/<article_id>`
2. Extract full content + metadata (see section 2)
3. Generate source markdown + rendered HTML
4. Update manifest and Excel index
5. **Close tab after each article** (avoid tab accumulation)

### 6.5 Completion report

Report to user:
- Keyword searched
- Total results found
- Already ingested (skipped)
- Newly ingested count + article titles
- Any errors encountered

### 6.6 URL patterns summary

| Action | URL Pattern |
|--------|-------------|
| Minutes list | `https://www.acecamptech.com/search?type=minutes` |
| Search results (综合) | `https://www.acecamptech.com/global_search?keyword=<keyword>` |
| Article detail | `https://www.acecamptech.com/article/detail/<article_id>` |

## 7) Completion checklist

- [ ] source written
- [ ] rendered written
- [ ] manifest synced
- [ ] index synced
- [ ] tab closed
- [ ] git commit done

If any checkbox fails, do not claim completion.
