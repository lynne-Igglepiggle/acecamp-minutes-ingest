#!/usr/bin/env python3
import argparse
import json
import re
import urllib.request
from pathlib import Path
from lib.source_rules import normalize_question_headings


def _find_acecamp_raw_root(output_path: Path) -> Path:
    for p in [output_path] + list(output_path.parents):
        if p.name == 'acecamp-raw':
            return p
    return output_path.parent.parent


def _localize_images(raw_html: str, article_id: str, output_path: Path) -> str:
    if not raw_html:
        return raw_html

    # Check if there are any images in the HTML
    if not re.search(r'<\s*img\b', raw_html, flags=re.I):
        return raw_html  # No images, don't create asset directory

    acecamp_root = _find_acecamp_raw_root(output_path)
    asset_dir = acecamp_root / 'assets' / str(article_id)
    asset_dir.mkdir(parents=True, exist_ok=True)

    idx = 0

    def repl(m):
        nonlocal idx
        tag = m.group(0)
        src_m = re.search(r'src\s*=\s*["\']([^"\']+)["\']', tag, flags=re.I)
        if not src_m:
            return ''
        src = src_m.group(1).strip()
        idx += 1
        ext = '.jpg'
        lower = src.lower()
        if '.png' in lower:
            ext = '.png'
        elif '.webp' in lower:
            ext = '.webp'
        elif '.gif' in lower:
            ext = '.gif'
        fn = f'img{idx}{ext}'
        local_file = asset_dir / fn
        try:
            req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as r:
                local_file.write_bytes(r.read())
            rel = Path('..') / 'assets' / str(article_id) / fn
            return f'\n![{article_id}-{idx}]({rel.as_posix()})\n'
        except Exception:
            return f'\n![{article_id}-{idx}]({src})\n'

    return re.sub(r'<\s*img\b[^>]*>', repl, raw_html, flags=re.I)


def _wrap_blue_text(html: str) -> str:
    """
    识别原文中的蓝色文本（AceCamp 通常为 rgb(102, 163, 224)），
    用 <blue> 标记包裹，供后续渲染使用。
    """
    # 匹配 style 中包含蓝色样式的元素（包括 rgb/rgba 格式）
    blue_patterns = [
        r'color\s*:\s*rgb\(102\s*,\s*163\s*,\s*224\)',
        r'color\s*:\s*rgba\(102\s*,\s*163\s*,\s*224',
        r'color\s*:\s*#66a3e0',
        r'color\s*:\s*rgb\(100\s*,\s*160\s*,\s*220\)',
        r'color\s*:\s*#4a90e2',
    ]
    pattern = '|'.join(blue_patterns)
    
    def repl(m):
        full_tag = m.group(0)
        # 提取文本内容（递归移除内部标签）
        inner = m.group(1) if len(m.groups()) > 0 else full_tag
        # 移除所有内部标签
        text = re.sub(r'<[^>]+>', '', inner)
        text = (text.replace('&nbsp;', ' ').replace('&amp;', '&')
                   .replace('&lt;', '<').replace('&gt;', '>')
                   .replace('&quot;', '"').replace('&#39;', "'"))
        return f'<blue>{text}</blue>'
    
    # 匹配带蓝色样式的标签（span/strong/b）及其内容（支持嵌套标签）
    regex = rf'<\s*(span|strong|b)[^>]*(?:{pattern})[^>]*>([\s\S]*?)<\s*/\s*\1\s*>'
    return re.sub(regex, repl, html, flags=re.I)


def html_to_preserved_markdown(raw_html: str, article_id: str = '', output_path: Path = None) -> str:
    """
    Convert limited rich HTML to markdown-like text while preserving key styles:
    - bold: <strong>/<b> -> **text**
    - red text: inline color red -> <red>text</red>
    - blue text: preserve <blue> markers from original HTML
    - list nesting: <ul>/<ol>/<li> -> indented '- '
    """
    if not raw_html:
        return ''

    s = raw_html
    if article_id and output_path is not None:
        s = _localize_images(s, article_id, output_path)
    
    s = re.sub(r'<\s*br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'</\s*p\s*>', '\n', s, flags=re.I)
    s = re.sub(r'<\s*p[^>]*>', '', s, flags=re.I)

    # bold
    s = re.sub(r'<\s*(strong|b)[^>]*>([\s\S]*?)<\s*/\s*\1\s*>', r'**\2**', s, flags=re.I)

    # red text via inline style
    s = re.sub(
        r'<\s*span[^>]*style="[^"]*color\s*:\s*(#f00|#ff0000|red|rgb\(255\s*,\s*0\s*,\s*0\))[^"]*"[^>]*>([\s\S]*?)<\s*/\s*span\s*>',
        r'<red>\2</red>', s, flags=re.I)

    # list items -> bullet (simple flatten with indentation markers)
    s = re.sub(r'<\s*/\s*(ul|ol)\s*>', '\n', s, flags=re.I)
    s = re.sub(r'<\s*(ul|ol)[^>]*>', '\n', s, flags=re.I)
    s = re.sub(r'<\s*li[^>]*>', '\n- ', s, flags=re.I)
    s = re.sub(r'<\s*/\s*li\s*>', '', s, flags=re.I)

    # 保留 <blue> 和 <red> 标记，strip 其他 tags
    s = re.sub(r'<(?!/?blue|/?red)[^>]+>', '', s)

    # unescape basic entities
    s = (s.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
           .replace('&quot;', '"').replace('&#39;', "'"))

    # cleanup
    s = re.sub(r'\n{3,}', '\n\n', s)
    s = re.sub(r'[ \t]+\n', '\n', s)
    return s.strip()


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
    body_html = d.get('body_html', '').strip()
    iq = d.get('iq', '').strip()
    expert = d.get('expert', '').strip()
    author = d.get('author', '').strip()
    co = d.get('co', '').strip()

    # normalize iq: keep first two question lines if long tail mixed with footer
    iq_lines = [x.strip() for x in iq.splitlines() if x.strip()]
    iq_q = [x for x in iq_lines if x.endswith('？') or x.endswith('?')]
    iq_out = iq_q[:2] if iq_q else iq_lines[:2]

    # normalize body with style-preserving conversion + heading rules
    body_src = html_to_preserved_markdown(body_html, args.article_id, Path(args.output)) if body_html else body
    body_out = normalize_question_headings(body_src)

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
