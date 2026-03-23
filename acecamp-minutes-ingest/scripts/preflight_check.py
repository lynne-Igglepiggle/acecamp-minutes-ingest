#!/usr/bin/env python3
import importlib.util
import shutil
import json
import sys
from pathlib import Path
from lib.error_log import append_error_log


def check_python():
    return shutil.which('python3') is not None


def check_openpyxl():
    return importlib.util.find_spec('openpyxl') is not None


def check_dirs(root: Path):
    needed = [root / 'acecamp-raw' / 'source', root / 'acecamp-raw' / 'rendered', root / 'acecamp-raw' / 'index']
    for d in needed:
        d.mkdir(parents=True, exist_ok=True)
    return True


def check_config(root: Path):
    cfg = root / 'skills' / 'acecamp-minutes-ingest' / 'config.json'
    example = root / 'skills' / 'acecamp-minutes-ingest' / 'config.example.json'
    if not cfg.exists():
        if example.exists():
            cfg.write_text(example.read_text(encoding='utf-8'), encoding='utf-8')
            print(f'INFO auto-created config from template: {cfg}')
        else:
            print(f'FAIL missing config: {cfg}')
            print(f'FAIL missing template: {example}')
            return False
    try:
        data = json.loads(cfg.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'FAIL invalid config.json: {e}')
        return False

    required = ['out_root', 'source_dir', 'rendered_dir', 'index_dir', 'alert_channel', 'alert_target', 'timezone', 'minutes_url']
    missing = [k for k in required if str(data.get(k, '')).strip() == '']
    if missing:
        print('FAIL missing required config keys:', ', '.join(missing))
        return False

    if str(data.get('alert_target', '')).strip() == 'REPLACE_WITH_YOUR_TARGET_ID':
        print('FAIL alert_target still placeholder in config.json')
        return False

    if not isinstance(data.get('tech_categories', []), list):
        print('FAIL tech_categories must be an array')
        return False

    # Optional booleans sanity
    for k in ['alert_on_login_required', 'alert_on_error', 'close_tab_after_each', 'stop_on_preflight_fail', 'sanitize_title', 'strict_consistency']:
        if k in data and not isinstance(data[k], bool):
            print(f'FAIL {k} must be boolean')
            return False

    print(f"PASS config ({data['alert_channel']} -> {data['alert_target']})")
    print(f"PASS output root ({data['out_root']})")
    return True


def check_hook_installed(root: Path):
    hook = root / '.git' / 'hooks' / 'pre-commit'
    marker = 'validate_staged_sources.py'
    if not hook.exists():
        print('WARNING hook not installed: .git/hooks/pre-commit')
        print('INFO install hook: bash skills/acecamp-minutes-ingest/git-hooks/install.sh')
        return False
    try:
        txt = hook.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        print('WARNING hook unreadable: .git/hooks/pre-commit')
        print('INFO install hook: bash skills/acecamp-minutes-ingest/git-hooks/install.sh')
        return False

    if marker not in txt:
        print('WARNING acecamp hook marker missing in .git/hooks/pre-commit')
        print('INFO install hook: bash skills/acecamp-minutes-ingest/git-hooks/install.sh')
        return False

    print('PASS pre-commit hook installed for acecamp source validation')
    return True


def main():
    root = Path.cwd()
    ok = True

    if check_python():
        print('PASS python3')
    else:
        ok = False
        print('FAIL python3 not found')

    if check_openpyxl():
        print('PASS openpyxl')
    else:
        ok = False
        print('FAIL openpyxl not installed')

    check_dirs(root)
    print('PASS acecamp-raw directories ready under', root)

    if not check_config(root):
        ok = False

    check_hook_installed(root)

    print('INFO login state must be checked in browser at runtime.')

    if ok:
        print('PREFLIGHT_OK')
        sys.exit(0)
    else:
        append_error_log(root, '', 'preflight', 'PreflightFail', 'preflight checks failed')
        print('PREFLIGHT_FAIL')
        sys.exit(1)


if __name__ == '__main__':
    main()
