# AceCamp Minutes Ingest Skill v2.1

相比 **v2.0**，**v2.1** 重点是把 AceCamp 入库链路正式收口成一套更稳定、可复用、可验证的流程。

## Highlights

- 引入**双主入口架构**
  - `scripts/ingest_from_open_page.py`：单篇详情页入库主入口
  - `scripts/search_and_ingest.py`：搜索 / 关键词入库主入口
- `ingest_one.py` 明确降级为 **source-level downstream processor**
- 核心实现下沉到 `scripts/lib/`
- 登录规则收口为 **no-slider-default**，补充 `Enter` 提交兜底
- 增强正文 / 列表 / 图片 / 问题标题样式保真
- 强化 metadata 一致性与回归样本校验
- 文档与目录语义同步更新

## Key Changes

### 1. 新的主入口结构
v2.1 正式区分两类主入口：

- **单篇入库**：`scripts/ingest_from_open_page.py`
- **搜索 / 关键词入库**：`scripts/search_and_ingest.py`

`ingest_one.py` 不再作为平级顶层入口，而是下游 source 处理器。

### 2. 核心能力下沉到 `scripts/lib/`
新增并启用：

- `lib/detail_extractor.py`
- `lib/source_builder.py`
- `lib/html_renderer.py`
- `lib/pdf_renderer.py`
- `lib/index_updater.py`
- `lib/output_validator.py`
- `lib/candidate_picker.py`
- `lib/tab_guard.py`

旧版分散脚本职责已重组收口。

### 3. 登录链路升级
AceCamp 登录规则在 v2.1 中被明确写死为：

- 默认按**无滑块密码登录流**处理
- 标准流程：切密码登录 -> 填账号密码 -> 勾协议 -> 点登录
- 若点击登录未成功提交，且真实页面无阻断异常：
  - **补一次 `Enter` 作为提交兜底**
- snapshot / DOM 文本不能作为滑块存在证据
- 只有真实渲染页面中明确可见且实际阻断流程的验证层，才视为异常

`login_policy.py` 现已升级为：
- 登录策略入口
- 登录执行入口
- 支持输出脱敏 policy JSON
- 支持输出可供浏览器执行的登录 JS

### 4. 内容保真增强
v2.1 强化了以下保真要求：

- 整行粗体问句 `**……？**` 自动规范为 `### ……？`
- 要点保留原始换行，不再依赖模型猜拆句
- 有序 / 无序列表映射更稳定
- 图片必须本地化并在 rendered 中按顺序渲染
- 红字 / 加粗 / 蓝色标题样式丢失时可直接判失败

### 5. metadata 与输出物修复
- `ingest_one.py` 新增 source 反读 metadata，优先以 source 为准：
  - industry
  - tags
  - author
  - co_publisher
- 输出目录语义固定为：
  - `acecamp-raw/rendered/`：**HTML only**
  - `acecamp-raw/share/`：**PDF only**

### 6. 回归与验收增强
- 扩充回归样本，覆盖：
  - 长正文
  - 多标签
  - 共享调研纪要
  - 联合发布人
  - 图片
  - 有序列表
  - 无序列表
  - 要点原始换行
  - 问题标题样式
- 完成门禁更明确：
  - source written
  - rendered written
  - manifest synced
  - index synced
  - working tab closed

## Migration Notes

从 v2.0 升级到 v2.1，建议切换到以下调用方式：

### 单篇详情页入库
```bash
python3 skills/acecamp-minutes-ingest/scripts/ingest_from_open_page.py \
  --url <detail_url> \
  --article-id <id>
```

### 搜索 / 关键词入库
```bash
python3 skills/acecamp-minutes-ingest/scripts/search_and_ingest.py \
  --keyword <keyword> \
  --snapshot-path <snapshot.txt>
```

### 已有 `source.md`
继续使用：
- `scripts/ingest_one.py`

但应将其理解为：
> downstream processor, not the primary entrypoint

## Summary

v2.1 把 AceCamp Minutes Ingest Skill 从一组“能跑的脚本”升级成了一套：

- 主入口清晰
- 内部实现收口
- 登录规则硬化
- 保真要求更严格
- 输出物语义更清楚
- 更适合持续维护和扩展
