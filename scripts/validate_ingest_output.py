#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

from lib.source_rules import validate_source_file


FORBIDDEN_INTROS = [
    "【以下为专家观点汇总，具体细节仅供参考。】",
    "以下为专家观点汇总，具体细节仅供参考。",
]


def _extract_section(text: str, start_marker: str, end_marker: str) -> str:
    i = text.find(start_marker)
    if i < 0:
        return ""
    j = text.find(end_marker, i + len(start_marker))
    return text[i:j if j >= 0 else len(text)]


def _extract_body_lines(md_text: str) -> list[str]:
    body = _extract_section(md_text, "## 三、正文", "## 四、智能追问")
    if not body:
        return []
    lines = []
    for ln in body.splitlines():
        if ln.startswith("### ") or ln.startswith("**") or ln.startswith("- ") or ln.startswith("* ") or "![" in ln or ln.strip():
            lines.append(ln)
    return lines


def _strip_q_markup(text: str) -> str:
    return text.strip()


def _extract_question_texts_from_source(md_text: str) -> list[str]:
    q_lines = []
    in_body = False
    for ln in md_text.splitlines():
        if ln.startswith("## 四、智能追问"):
            break
        if ln.startswith("## 三、正文"):
            in_body = True
            continue
        if not in_body:
            continue
        if ln.startswith("### "):
            q_lines.append(_strip_q_markup(ln[4:]))
    return q_lines


def _extract_q_html_texts(rendered: str) -> list[str]:
    vals = re.findall(r'<p class="q">\s*<strong>(.*?)</strong>\s*</p>', rendered, flags=re.S)
    return [html.unescape(re.sub(r"<[^>]+>", "", v)).strip() for v in vals]


def _count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.MULTILINE))


def _count_all_patterns(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.S))


def _count_image_lines(md_lines: list[str]) -> int:
    return _count_all_patterns("\n".join(md_lines), r"^!\[[^\]]*\]\([^\)]+\)$",)


def _count_list_items(md_lines: list[str]) -> int:
    return sum(1 for ln in md_lines if re.match(r"^\s*[-*]\s+", ln))


def _count_markups(md_text: str, tag: str) -> int:
    return len(re.findall(fr"<{tag}>.*?</{tag}>", md_text, flags=re.S))


def _check_render_contains(src_md: str, rendered: str) -> list[str]:
    errs: list[str] = []

    if any(x in src_md for x in FORBIDDEN_INTROS):
        errs.append("source contains forbidden injected intro text")

    # 基础 source 结构校验（由库函数统一校验）
    # 注意：这里复用已有规则，避免重复实现。由 ingest_one 的入口也会调用。
    # 本脚本单独执行时依旧保障同等标准。
    if "## 三、正文" not in src_md:
        errs.append("missing section: ## 三、正文")

    md_lines = _extract_body_lines(src_md)

    # 1) 问题/标题蓝色映射
    src_q = _extract_question_texts_from_source(src_md)
    rendered_q = _extract_q_html_texts(rendered)
    if len(rendered_q) < len(src_q):
        errs.append(f"q count too low in rendered: src={len(src_q)} rendered={len(rendered_q)}")
    else:
        for i, sq in enumerate(src_q):
            if i >= len(rendered_q):
                break
            if sq != rendered_q[i]:
                # 不做强严格一致性（空白与标点略差异可容忍）
                norm_sq = re.sub(r"\s+", "", sq)
                norm_rq = re.sub(r"\s+", "", rendered_q[i])
                if norm_sq != norm_rq:
                    errs.append(f"q text mismatch at index {i + 1}: src='{sq}' rendered='{rendered_q[i]}'")
                    break

    # 2) 红/蓝标记保真
    red_src = _count_markups(src_md, "red")
    blue_src = _count_markups(src_md, "blue")
    rendered_red = _count_pattern(rendered, r'class="red"')
    rendered_blue = _count_pattern(rendered, r'class="blue"')
    if red_src > rendered_red:
        errs.append(f"red markup dropped: src={red_src} rendered={rendered_red}")
    if blue_src > rendered_blue:
        errs.append(f"blue markup dropped: src={blue_src} rendered={rendered_blue}")

    # 3) 粗体保真（存在就至少要有一次 strong）
    bold_src = _count_all_patterns("\n".join(md_lines), r"\*\*[^\*]+\*\*")
    bold_rendered = _count_pattern(rendered, r"<strong>")
    if bold_src > 0 and bold_rendered == 0:
        errs.append("bold markdown present in source but no <strong> in rendered")

    # 4) 列表保真
    li_src = _count_list_items(md_lines)
    li_rendered = _count_pattern(rendered, r"<li")
    if li_src > 0 and li_rendered < li_src:
        errs.append(f"list items dropped: src={li_src} rendered={li_rendered}")

    # 5) 图片保真
    img_src = _count_image_lines(md_lines)
    img_rendered = _count_pattern(rendered, r"<img ")
    if img_src > 0 and img_rendered < img_src:
        errs.append(f"image tags dropped: src={img_src} rendered={img_rendered}")

    # 6) 反模板注入（rendered）
    for intro in FORBIDDEN_INTROS:
        if intro in rendered:
            errs.append(f"forbidden intro rendered: {intro}")

    return errs


def run_check(source_path: Path, rendered_path: Path, allow_empty_body: bool = False, min_body_chars: int = 300) -> list[str]:
    errs: list[str] = []

    if not source_path.exists():
        return [f"source not found: {source_path}"]
    if not rendered_path.exists():
        return [f"rendered not found: {rendered_path}"]

    md = source_path.read_text(encoding="utf-8")
    rendered = rendered_path.read_text(encoding="utf-8")

    try:
        # validate_source_file 用最小化规则（与入库主链路保持一致）
        validate_source_file(source_path, allow_empty_body=allow_empty_body, min_body_chars=min_body_chars)
    except Exception as e:
        errs.append(f"validate_source_file failed: {e}")

    errs.extend(_check_render_contains(md, rendered))

    return errs


def main():
    ap = argparse.ArgumentParser(description="Validate AceCamp extraction/ rendering fidelity between source markdown and rendered html")
    ap.add_argument("--source", required=True)
    ap.add_argument("--rendered", required=True)
    ap.add_argument("--allow-empty-body", action="store_true")
    ap.add_argument("--min-body-chars", type=int, default=300)
    args = ap.parse_args()

    errs = run_check(
        source_path=Path(args.source),
        rendered_path=Path(args.rendered),
        allow_empty_body=args.allow_empty_body,
        min_body_chars=args.min_body_chars,
    )

    if errs:
        print("ACECAMP_VALIDATION_FAIL")
        for e in errs:
            print(" -", e)
        sys.exit(1)

    print("ACECAMP_VALIDATION_OK")


if __name__ == "__main__":
    main()
