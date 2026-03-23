#!/usr/bin/env python3
import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path




def cmd_resolve_tab(args):
    data = json.loads(args.tabs_json)
    tabs = data.get('tabs', []) if isinstance(data, dict) else []
    for t in tabs:
        url = str(t.get('url', ''))
        if args.match_url in url:
            print(json.dumps({
                'ok': True,
                'found': True,
                'targetId': t.get('targetId'),
                'url': url,
                'title': t.get('title', ''),
                'mustReuse': True,
                'allowOpen': False,
                'policy': 'reuse-existing-tab-first',
            }, ensure_ascii=False))
            return
    print(json.dumps({
        'ok': True,
        'found': False,
        'mustReuse': False,
        'allowOpen': True,
        'policy': 'reuse-existing-tab-first',
    }, ensure_ascii=False))


def cmd_guard_open(args):
    decision = json.loads(args.resolve_json)
    planned = args.planned_action

    if planned == 'open' and decision.get('found'):
        print(json.dumps({
            'ok': False,
            'error': 'OPEN_BLOCKED_REUSE_REQUIRED',
            'message': 'Matching tab exists; must reuse targetId instead of opening new tab.',
            'targetId': decision.get('targetId'),
        }, ensure_ascii=False))
        raise SystemExit(2)

    print(json.dumps({
        'ok': True,
        'plannedAction': planned,
        'found': bool(decision.get('found')),
        'allowed': True,
    }, ensure_ascii=False))


def _load_manifest_ids(path: Path):
    ids = set()
    if not path.exists():
        return ids
    for ln in path.read_text(encoding='utf-8').splitlines():
        if not ln.strip():
            continue
        try:
            ids.add(str(json.loads(ln).get('article_id', '')))
        except Exception:
            pass
    return ids


def _parse_article_entries(snapshot_text: str):
    entries = []
    seen = set()
    # best-effort line-oriented parse from snapshot text
    lines = snapshot_text.splitlines()
    for i, ln in enumerate(lines):
        m = re.search(r"/article/detail/(\d+)", ln)
        if not m:
            continue
        aid = m.group(1)
        if aid in seen:
            continue
        seen.add(aid)
        ctx = lines[i - 1] if i > 0 else ''
        text = (ctx + ' ' + ln).strip()
        entries.append({'id': aid, 'text': text})
    return entries


def _is_within_window(text: str, today: datetime, window_days: int):
    if re.search(r"\d+小时前|\d+分钟前|刚刚", text):
        return True
    m = re.search(r"(\d{4}/\d{2}/\d{2})", text)
    if not m:
        return True  # if no date marker, keep candidate for safety
    try:
        d = datetime.strptime(m.group(1), "%Y/%m/%d")
    except Exception:
        return True
    return d.date() >= (today.date() - timedelta(days=window_days - 1))


def cmd_pick_candidates(args):
    txt = Path(args.snapshot_path).read_text(encoding='utf-8')
    entries = _parse_article_entries(txt)

    if args.today:
        today = datetime.strptime(args.today, '%Y-%m-%d')
    else:
        today = datetime.now()

    if not args.allow_backfill:
        entries = [e for e in entries if _is_within_window(e['text'], today, args.window_days)]
        entries = entries[:args.max_recent]

    candidate_ids = [e['id'] for e in entries]
    manifest_ids = _load_manifest_ids(Path(args.manifest_path))
    picked = [x for x in candidate_ids if x not in manifest_ids]

    print(json.dumps({
        'ok': True,
        'allowBackfill': args.allow_backfill,
        'windowDays': args.window_days,
        'maxRecent': args.max_recent,
        'totalSeen': len(candidate_ids),
        'picked': picked,
    }, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='command', required=True)

    p1 = sub.add_parser('resolve-tab')
    p1.add_argument('--tabs-json', required=True)
    p1.add_argument('--match-url', required=True)
    p1.set_defaults(func=cmd_resolve_tab)

    p2 = sub.add_parser('pick-candidates')
    p2.add_argument('--snapshot-path', required=True)
    p2.add_argument('--manifest-path', default='acecamp-raw/index/manifest.jsonl')
    p2.add_argument('--allow-backfill', action='store_true')
    p2.add_argument('--window-days', type=int, default=3)
    p2.add_argument('--today', default='', help='YYYY-MM-DD, optional override for testing')
    p2.add_argument('--max-recent', type=int, default=30)
    p2.set_defaults(func=cmd_pick_candidates)

    p3 = sub.add_parser('guard-open')
    p3.add_argument('--resolve-json', required=True, help='JSON output from resolve-tab')
    p3.add_argument('--planned-action', choices=['open', 'reuse'], required=True)
    p3.set_defaults(func=cmd_guard_open)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
