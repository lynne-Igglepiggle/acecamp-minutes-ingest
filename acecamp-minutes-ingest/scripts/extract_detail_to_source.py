#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from lib.source_rules import normalize_question_headings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--detail-json', required=True, help='json file with extracted detail fields')
    ap.add_argument('--output', required=True)
    ap.add_argument('--record-time', required=True)
    ap.add_argument('--source-url', required=True)
    ap.add_argument('--article-id', required=True)
    args = ap.parse_args()

    d = json.loads(Path(args.detail_json).read_text(encoding='utf-8'))
    title = d.get('title', '')
    pub = d.get('pub', '')
    read = str(d.get('read', ''))
    like = str(d.get('like', ''))
    words = d.get('words', '')
    industry = d.get('industry', '')
    key = d.get('key', '').strip()
    body = d.get('body', '').strip()
    iq = d.get('iq', '').strip()
    expert = d.get('expert', '').strip()
    author = d.get('author', '').strip()
    co = d.get('co', '').strip()

    # normalize iq: keep first two question lines if long tail mixed with footer
    iq_lines = [x.strip() for x in iq.splitlines() if x.strip()]
    iq_q = [x for x in iq_lines if x.endswith('？') or x.endswith('?')]
    iq_out = iq_q[:2] if iq_q else iq_lines[:2]

    # normalize body with question headings
    body_out = normalize_question_headings(body)

    tags = []
    t = d.get('tags', '')
    if isinstance(t, list):
        tags = [x for x in t if x]
    elif isinstance(t, str) and t.strip():
        tags = [x.strip() for x in re.split(r'[,，\n]+', t) if x.strip()]

    out = []
    out.append('# AceCamp 文章全量记录（列表+详情页可见）\n')
    out.append(f'- 记录时间：{args.record_time}')
    out.append(f'- 来源页面：{args.source_url}')
    out.append(f'- article_id：{args.article_id}\n')

    out.append('## 一、基础信息')
    out.append(f'- 标题：{title}')
    out.append('- 内容类型：纪要')
    out.append('- 权限：VIP')
    out.append('- 标识：原创')
    out.append(f'- 行业：{industry}')
    out.append(f'- 发布时间：{pub}')
    out.append(f'- 阅读：{read}')
    out.append(f'- 点赞：{like}')
    out.append(f'- 字数/阅读时长：{words}')
    out.append('- VIP状态：已享VIP免费\n')

    out.append('## 二、要点（页面原文）')
    out.append(key + '\n')

    out.append('## 三、正文（“以下为专家观点汇总，具体细节仅供参考”原文）')
    out.append(body_out if body_out else '（正文未提取成功）')
    out.append('')

    out.append('## 四、智能追问（页面可见）')
    for i, q in enumerate(iq_out, 1):
        out.append(f'{i}. {q}')
    out.append('')

    out.append('## 五、标签（页面可见）')
    for tg in tags:
        out.append(f'- {tg}')
    out.append('')

    out.append('## 六、专家与作者信息（页面可见）')
    if expert:
        out.append(f'- 专家简介字段：{expert.splitlines()[0]}')
    out.append(f'- 发布人：{author}')
    if co:
        out.append(f'- 联合发布人：{co}')
    out.append('')

    out.append('## 七、补充说明')
    out.append('- 本文为从网页可见内容直接提取的“页面全量记录”。')

    Path(args.output).write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(args.output)


if __name__ == '__main__':
    main()
