# scripts/README.md

`skills/acecamp-minutes-ingest/scripts` 目录说明（按用途分组）

## 核心入口（优先使用）

1. `preflight_check.py`
- 作用：执行环境与配置预检（Python/openpyxl/config/hook）
- 通过标志：`PREFLIGHT_OK`

2. `extract_detail_to_source.py`
- 作用：将详情抽取结果（detail json）规范化生成标准 `source.md`
- 包含问句标题规范化（支持 `?` / `？`）

3. `ingest_one.py`
- 作用：单篇入库主入口（校验 → 渲染 → manifest/index 同步 → 一致性修正）
- 默认读取 `config.json` 中 `strict_consistency` / `min_body_chars`，CLI 可覆盖

## 规则与辅助

4. `workflow_helpers.py`
- 作用：流程辅助（tab 复用解析、候选文章选择、open 动作保护）
- 关键命令：
  - `resolve-tab`
  - `pick-candidates`
  - `guard-open`

5. `validate_staged_sources.py`
- 作用：用于 pre-commit 的 staged source 校验
- 仅在 staged 命中 `acecamp-raw/source/*.md` 时触发

## 质量保障与记录

6. `regression_samples_check.py`
- 作用：一键回归检查 3 个样本（70560067/70560083/70560077）
- 建议：每次改脚本后先跑一遍

7. `log_issue.py`
- 作用：标准化追加 `acecamp-raw/logs/error-log.jsonl`
- 用于人工指出问题后的快速落 log

## 底层模块

8. `lib/`
- `config.py`：统一配置读取与默认值
- `error_log.py`：统一 error-log 追加
- `source_rules.py`：统一问句规范化/正文校验

---

## 建议执行顺序

1) `preflight_check.py`
2) （需要时）`workflow_helpers.py pick-candidates`
3) `extract_detail_to_source.py`
4) `ingest_one.py`
5) （脚本变更后）`regression_samples_check.py`
6) （有人工反馈时）`log_issue.py`

## 补漏模式

1) 在 AceCamp 页面内查看目标列表并按可见内容直接判断范围。
2) 复制页面快照文本。
3) 用 `pick-candidates` 做未入库对比：

```bash
python3 skills/acecamp-minutes-ingest/scripts/workflow_helpers.py pick-candidates \
  --snapshot-path <minutes_snapshot.txt> \
  --manifest-path acecamp-raw/index/manifest.jsonl \
  --window-days 3
```
