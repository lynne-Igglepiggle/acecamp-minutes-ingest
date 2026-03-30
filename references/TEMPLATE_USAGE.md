# AceCamp Render 模板说明

当前渲染链路已经调整为：

- 用户侧 / 主流程：不要直接调用渲染内部件
- 下游处理器：`ingest_one.py`
- 实际渲染实现：`skills/acecamp-minutes-ingest/scripts/lib/html_renderer.py`

## 当前建议

### 日常使用
优先通过顶层入口完成渲染：

- 单篇网页入库：`scripts/ingest_from_open_page.py`
- 已有 source 再处理：`scripts/ingest_one.py`

### 内部实现关系

```text
source.md
  -> ingest_one.py
      -> lib/html_renderer.py
      -> rendered.html
```

## 为什么不再暴露单独的 render 脚本

渲染现在是内部实现能力，不再占用顶层脚本心智。

## 如果你在改模板样式

请直接查看：
- `skills/acecamp-minutes-ingest/scripts/lib/html_renderer.py`

改完后建议跑：

```bash
python3 skills/acecamp-minutes-ingest/scripts/regression_samples_check.py
```
