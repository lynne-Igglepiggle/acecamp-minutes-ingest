# scripts/README.md

`skills/acecamp-minutes-ingest/scripts` 目录说明（按当前重构后结构）

## 顶层入口（外层应尽量少）

### 1. `preflight_check.py`
- 作用：执行环境与配置预检（Python / openpyxl / playwright / config / hook）
- 通过标志：`PREFLIGHT_OK`

### 2. `ingest_from_open_page.py`
- 作用：**单篇网页入库主入口**
- 适用：浏览器已定位到 `/article/detail/<id>` 页面时，日常单篇入库优先用它
- 内部链路：
  - `lib/detail_extractor.py`
  - `lib/source_builder.py`
  - `ingest_one.py`
  - `lib/output_validator.py`

### 3. `search_and_ingest.py`
- 作用：**关键词 / 搜索入库主入口**
- 适用：像“录入一篇 AXTI 相关纪要”“按关键词批量入库”这类搜索驱动场景
- 当前职责：挑候选 → 生成/执行对 `ingest_from_open_page.py` 的委派

### 4. `ingest_one.py`
- 作用：**source 级下游处理器**（不是顶层主入口）
- 负责：source 校验 → html 渲染 → pdf 导出 → manifest/index 同步 → 一致性修正 → output validate
- 心智模型：`source.md` 已经存在时，才轮到它出场

---

## 内部实现（已下沉到 `lib/`）

### `lib/source_builder.py`
- `detail.json -> source.md`

### `lib/html_renderer.py`
- `source.md -> rendered.html`

### `lib/pdf_renderer.py`
- `rendered.html -> share/*.pdf`

### `lib/index_updater.py`
- `manifest.jsonl / 索引.xlsx` 更新

### `lib/output_validator.py`
- source / rendered 一致性验收

### 其他底层模块
- `lib/config.py`：统一配置读取与默认值
- `lib/error_log.py`：统一 error-log 追加
- `lib/source_rules.py`：统一正文规则 / 问句规范 / source 校验

---

## 辅助脚本

### `login_policy.py`
- 作用：AceCamp 登录策略 / policy 输出入口，同时也是登录执行入口
- 规则补充：AceCamp 登录默认按无滑块密码登录流处理；若点击“登录”未成功提交，且真实页面无阻断异常，可补发一次 `Enter` 作为提交兜底
- 当前支持：
  - 默认输出脱敏 policy JSON
  - `--emit-executor-js` 输出可供浏览器 evaluate 执行的标准登录脚本

### `log_issue.py`
- 作用：标准化追加 `acecamp-raw/logs/error-log.jsonl`

---

## 质量保障与开发期工具

### `regression_samples_check.py`
- 作用：回归样本检查

### `validate_staged_sources.py`
- 作用：用于 pre-commit 的 staged source 校验

---

## 当前建议执行顺序

1. `preflight_check.py`
2. 单篇优先：`ingest_from_open_page.py`
3. 搜索/关键词：`search_and_ingest.py`
4. 如需拆步调试：`lib/detail_extractor.py` → `lib/source_builder.py` → `ingest_one.py`
5. 如有样式 / 规则修改后，跑 `regression_samples_check.py`
6. 如有人工反馈，跑 `log_issue.py`

---

## 一句话理解

- `search_and_ingest.py` = 找哪篇
- `ingest_from_open_page.py` = 录这篇
- `lib/detail_extractor.py` = 从页面抽 detail
- `lib/source_builder.py` = detail 变 source
- `ingest_one.py` = source 变最终产物
