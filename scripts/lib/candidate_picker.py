import json
import re
from datetime import datetime, timedelta
from pathlib import Path


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
    lines = snapshot_text.splitlines()
    for i, ln in enumerate(lines):
        m = re.search(r'/article/detail/(\d+)', ln)
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
    if re.search(r'\d+小时前|\d+分钟前|刚刚', text):
        return True
    m = re.search(r'(\d{4}/\d{2}/\d{2})', text)
    if not m:
        return True
    try:
        d = datetime.strptime(m.group(1), '%Y/%m/%d')
    except Exception:
        return True
    return d.date() >= (today.date() - timedelta(days=window_days - 1))


def pick_candidates(snapshot_path: str, manifest_path: str = 'acecamp-raw/index/manifest.jsonl', allow_backfill: bool = False, window_days: int = 3, today: str = '', max_recent: int = 30) -> dict:
    txt = Path(snapshot_path).read_text(encoding='utf-8')
    entries = _parse_article_entries(txt)

    now = datetime.strptime(today, '%Y-%m-%d') if today else datetime.now()
    if not allow_backfill:
        entries = [e for e in entries if _is_within_window(e['text'], now, window_days)]
        entries = entries[:max_recent]

    candidate_ids = [e['id'] for e in entries]
    manifest_ids = _load_manifest_ids(Path(manifest_path))
    picked = [x for x in candidate_ids if x not in manifest_ids]

    return {
        'ok': True,
        'allowBackfill': allow_backfill,
        'windowDays': window_days,
        'maxRecent': max_recent,
        'totalSeen': len(candidate_ids),
        'picked': picked,
    }
