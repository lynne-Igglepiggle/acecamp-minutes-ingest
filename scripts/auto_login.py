#!/usr/bin/env python3
"""
AceCamp Auto Login - Simple Browser Tool Version
Generates action sequence for OpenClaw browser tool.
"""

import json
import sys
from pathlib import Path

# 读取 acecamp-raw 目录的真实配置（敏感信息不应放在 skill 目录）
ACE_CONFIG = Path(__file__).parent.parent.parent.parent / "acecamp-raw" / "config.json"

def load_config():
    if not ACE_CONFIG.exists():
        print(f"Error: Config not found at {ACE_CONFIG}")
        print("Please create config from template: cp skills/acecamp-minutes-ingest/config.example.json acecamp-raw/config.json")
        sys.exit(1)
    with open(ACE_CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    config = load_config()
    auto = config.get('auto_login', {})
    
    if not auto.get('enabled'):
        print("Auto login disabled")
        sys.exit(1)
    
    cred = auto.get('credentials', {})
    account = cred.get('account')
    password = cred.get('password')
    login_type = cred.get('type', 'phone')
    
    if not account or not password:
        print("Credentials not configured")
        sys.exit(1)
    
    # Action sequence for OpenClaw browser tool
    actions = [
        {"kind": "navigate", "url": "https://www.acecamptech.com/login"},
        {"kind": "wait", "timeMs": 2000},
        {"kind": "click", "ref": "e83"},  # 密码登录
        {"kind": "wait", "timeMs": 500},
    ]
    
    if login_type == "phone":
        actions.append({"kind": "type", "ref": "e107", "text": account})
    else:
        actions.append({"kind": "click", "ref": "e146"})  # 邮箱登录
        actions.append({"kind": "wait", "timeMs": 500})
        actions.append({"kind": "type", "ref": "e107", "text": account})
    
    actions.extend([
        {"kind": "wait", "timeMs": 300},
        {"kind": "type", "ref": "e182", "text": password},
        {"kind": "wait", "timeMs": 300},
        {"kind": "click", "ref": "e129"},  # 同意
        {"kind": "wait", "timeMs": 300},
        {"kind": "click", "ref": "e133"},  # 登录
        {"kind": "wait", "timeMs": 3000},
    ])
    
    result = {
        "account": account,
        "max_retries": auto.get('max_retries', 2),
        "actions": actions,
        "check_script": """
        () => {
            const user = document.querySelector('.user-nav, .nav-user, [class*="user"]');
            const name = document.querySelector('.user-name');
            return { isLoggedIn: !!(user || name), userName: name?.textContent?.trim() };
        }
        """
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
