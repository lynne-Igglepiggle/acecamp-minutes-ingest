# AceCamp Logging 规范

## 日志位置

运行日志写入：
- `acecamp-raw/logs/error-log.jsonl`

说明：
- 该文件为运行数据，不属于 skill 可发布内容。
- 仓库已通过 `.gitignore` 忽略 `acecamp-raw/logs/*.jsonl`。

## 记录时机

以下场景应写日志：
1. preflight 失败
2. ingest 流程异常中止
3. industry/tags 一致性不匹配（自动修正时写 DataMismatch）
4. 人工评审指出问题（HumanRaisedIssue）

## JSONL 格式（每行一条 JSON）

必备字段：
- `time`：ISO 时间（秒级）
- `article_id`：文章 ID，若无则空字符串
- `stage`：阶段（如 `preflight` / `ingest_one` / `post_ingest_check` / `human_review`）
- `error_type`：错误类型（如 `PreflightFail` / `RuntimeError` / `DataMismatch` / `HumanRaisedIssue`）
- `error_message`：错误描述
- `source_url`：文章链接，若无则空字符串
- `action_taken`：处理动作（如 `stopped` / `auto_fixed` / `fixed_and_backfilled`）

可选字段：
- `mismatches`：一致性差异详情（数组）
- 其他调试字段（按需补充）

## 示例

```json
{"time":"2026-03-23T21:20:01","article_id":"","stage":"preflight","error_type":"PreflightFail","error_message":"preflight checks failed","source_url":"","action_taken":"stopped"}
{"time":"2026-03-23T21:21:11","article_id":"70560067","stage":"ingest_one","error_type":"RuntimeError","error_message":"body too short (42 chars), expected full-text extraction","source_url":"https://www.acecamptech.com/article/detail/70560067","action_taken":"stopped"}
{"time":"2026-03-23T21:22:33","article_id":"70560083","stage":"post_ingest_check","error_type":"DataMismatch","error_message":"industry/tags mismatch auto-fixed","source_url":"https://www.acecamptech.com/article/detail/70560083","action_taken":"auto_fixed","mismatches":[["industry","AI,电力基础设施,制造业","制造业"]]}
{"time":"2026-03-23T21:23:44","article_id":"70560067","stage":"human_review","error_type":"HumanRaisedIssue","error_message":"正文漏录（页面存在“以下为专家观点”正文但source写成无正文）","source_url":"https://www.acecamptech.com/article/detail/70560067","action_taken":"fixed_and_backfilled"}
```

## 复盘建议

- 每周至少一次查看 `error-log.jsonl`。
- 汇总 Top 错误类型（次数、影响文章数、修复状态）。
- 将高频问题沉淀到：
  - `SKILL.md`（规则）
  - 脚本（自动化防呆）
  - `README`（用户指引）
