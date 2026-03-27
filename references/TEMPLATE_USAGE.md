# AceCamp Render 模板用法

固定模板脚本：
- `skills/acecamp-minutes-ingest/scripts/render_template.py`

命令：
```bash
python3 skills/acecamp-minutes-ingest/scripts/render_template.py \
  <input_md> \
  <output_html> \
  --source-url <详情页URL> \
  --record-time "YYYY-MM-DD HH:MM（Asia/Shanghai）" \
  --article-id <id>
```

示例：
```bash
python3 skills/acecamp-minutes-ingest/scripts/render_template.py \
  acecamp-raw/source/2026-03-23_acecamptech_70560056_AIInfra龙头Skill开发和前端云拓展对流量和收入带动Agentic流程显著刺激HTTP请求数量开发者生态扩张等VercelNetlifyRender_2026-03-23.md \
  acecamp-raw/rendered/2026-03-23_acecamptech_70560056_AIInfra龙头Skill开发和前端云拓展对流量和收入带动Agentic流程显著刺激HTTP请求数量开发者生态扩张等VercelNetlifyRender_2026-03-23.rendered.html \
  --source-url https://www.acecamptech.com/article/detail/70560056 \
  --record-time "2026-03-23 13:01（Asia/Shanghai）" \
  --article-id 70560056
```
