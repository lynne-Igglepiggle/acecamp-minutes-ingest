# AceCamp Hook 说明

这个目录里的 hook 用于防止“正文漏录/占位正文”被提交。

## 作用

在 `git commit` 前自动检查本次暂存（staged）的：
- `acecamp-raw/source/*.md`

若发现以下问题会拦截提交：
- 正文段为空
- 正文是占位文本（如“未展示/待补充”）
- 长文正文明显过短

## 安装

在仓库根目录执行：

```bash
bash skills/acecamp-minutes-ingest/git-hooks/install.sh
```

安装后会写入：
- `.git/hooks/pre-commit`

## 触发范围

仅当本次提交包含 `acecamp-raw/source/*.md` 变更时触发检查。

如果提交不包含这些文件，会直接跳过：
- `PRE-COMMIT: no staged acecamp source changes, skip`

## 失败后怎么处理

1. 根据终端报错定位对应 source 文件
2. 补齐正文原文（不要摘要化）
3. 重新 `git add` 后再 `git commit`

## 备注

这是仓库级防呆机制，目的是降低误入库风险，减少人工复查压力。
