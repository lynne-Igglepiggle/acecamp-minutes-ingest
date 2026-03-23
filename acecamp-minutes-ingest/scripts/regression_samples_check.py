#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


CASES = {
    '70560067': {
        'min_body_chars': 800,
        'min_q': 5,
        'desc': '中文锚点正文提取（回归）',
    },
    '70560083': {
        'min_body_chars': 800,
        'min_q': 5,
        'desc': '英文锚点正文提取（回归）',
    },
    '70560077': {
        'min_body_chars': 1000,
        'min_q': 10,
        'desc': '中文问号问题蓝色样式',
    },
}


def find_single(glob_pat: str):
    matches = sorted(Path().glob(glob_pat))
    return matches[0] if matches else None


def body_len_from_source(source_text: str) -> int:
    m = re.search(r'## 三、正文[\s\S]*?(?=\n## 四、智能追问|\Z)', source_text)
    if not m:
        return 0
    body = m.group(0)
    return len(re.sub(r'\s+', '', body))


def check_case(case_id: str):
    cfg = CASES[case_id]
    src = find_single(f'acecamp-raw/source/*_{case_id}_*.md')
    rnd = find_single(f'acecamp-raw/rendered/*_{case_id}_*.rendered.html')
    if not src or not rnd:
        return False, f'{case_id} missing file(s): source={bool(src)} rendered={bool(rnd)}'

    s = src.read_text(encoding='utf-8')
    h = rnd.read_text(encoding='utf-8')

    blen = body_len_from_source(s)
    if blen < cfg['min_body_chars']:
        return False, f'{case_id} body too short: {blen} < {cfg["min_body_chars"]}'

    q_count = h.count('class="q"')
    if q_count < cfg['min_q']:
        return False, f'{case_id} q_count too low: {q_count} < {cfg["min_q"]}'

    return True, f'{case_id} PASS body={blen} q={q_count} ({cfg["desc"]})'


def main():
    ap = argparse.ArgumentParser(description='Run AceCamp regression checks for known edge samples')
    ap.add_argument('--cases', default='70560067,70560083,70560077', help='comma-separated case ids')
    args = ap.parse_args()

    all_ok = True
    for case_id in [x.strip() for x in args.cases.split(',') if x.strip()]:
        if case_id not in CASES:
            print(f'{case_id} SKIP unknown case')
            continue
        ok, msg = check_case(case_id)
        print(msg)
        all_ok = all_ok and ok

    if not all_ok:
        raise SystemExit(1)
    print('REGRESSION_OK')


if __name__ == '__main__':
    main()
