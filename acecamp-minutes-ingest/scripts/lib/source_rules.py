#!/usr/bin/env python3
import re
from pathlib import Path
from typing import List, Tuple, Optional


def normalize_question_headings(text: str) -> str:
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            out.append('')
            continue
        if (s.endswith('?') or s.endswith('？')) and not s.startswith('### '):
            out.append('### ' + s)
        else:
            out.append(s)
    return '\n'.join(out).strip()


def parse_expected_words(text: str) -> Optional[int]:
    m_words = re.search(r'本文共(\d+)字', text)
    return int(m_words.group(1)) if m_words else None


def extract_body_section(text: str) -> str:
    if '## 三、正文' not in text:
        return ''
    body_start = text.find('## 三、正文')
    body_end = text.find('## 四、智能追问', body_start + 1)
    return text[body_start:body_end if body_end > 0 else len(text)].strip()


def validate_question_heading_lines(text: str) -> List[Tuple[int, str]]:
    bad = []
    for i, ln in enumerate(text.splitlines(), start=1):
        s = ln.strip()
        if re.match(r'^(Chris|匿名投资者|提问|Q\d*|问|What\s)[:：]?', s):
            if (s.endswith('?') or s.endswith('？')) and not s.startswith('### '):
                bad.append((i, s[:120]))
    return bad


def validate_source_file(source_path: Path, allow_empty_body: bool = False, min_body_chars: int = 300):
    if not source_path.exists():
        raise RuntimeError(f'source not found: {source_path}')

    text = source_path.read_text(encoding='utf-8')
    if '## 三、正文' not in text:
        raise RuntimeError('missing section: ## 三、正文')

    body = extract_body_section(text)
    expected_words = parse_expected_words(text)

    if not allow_empty_body:
        if not body:
            raise RuntimeError('empty body section')
        no_ws = re.sub(r'\s+', '', body)
        if any(x in body for x in ['未展示', '暂无正文', '待补充']) and len(no_ws) < 60:
            raise RuntimeError('body appears placeholder-only')

        dynamic_min = min_body_chars
        # Anti-truncation guard for long articles: require at least 50% of declared word count.
        if expected_words and expected_words >= 3000:
            dynamic_min = max(dynamic_min, int(expected_words * 0.5))

        if len(no_ws) < dynamic_min and (expected_words is None or expected_words >= 800):
            raise RuntimeError(
                f'body too short ({len(no_ws)} chars), expected >= {dynamic_min} for full-text extraction'
            )

    bad = validate_question_heading_lines(text)
    if bad:
        sample = '; '.join([f'line {i}' for i, _ in bad[:5]])
        raise RuntimeError(f'question lines must start with ### ({sample})')
