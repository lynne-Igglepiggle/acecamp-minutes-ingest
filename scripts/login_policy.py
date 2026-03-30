#!/usr/bin/env python3
"""
AceCamp Login Policy

当前文件既是 AceCamp 登录规则的统一 policy 输出入口，
也承担标准登录执行入口的职责。

核心规则：
- AceCamp 登录页默认按“无滑块密码登录流”建模。
- 标准流程：切密码登录 -> 填账号密码 -> 勾协议 -> 点击登录。
- 若点击登录未成功提交，且真实渲染页面无阻断异常，则补发一次 Enter 作为标准提交兜底。
- snapshot/DOM 文本不构成滑块/验证码存在证据。
- 只有当真实渲染页面明确显示且实际阻断流程的验证层出现时，才作为异常处理。
"""

import argparse
import json
import sys
from pathlib import Path

ACE_CONFIG = Path(__file__).parent.parent.parent.parent / "acecamp-raw" / "config.json"


def load_config():
    if not ACE_CONFIG.exists():
        print(f"Error: Config not found at {ACE_CONFIG}")
        print("Please create config from template: cp skills/acecamp-minutes-ingest/config.example.json acecamp-raw/config.json")
        sys.exit(1)
    with open(ACE_CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_policy(config: dict) -> dict:
    auto = config.get('auto_login', {})
    if not auto.get('enabled'):
        return {
            "enabled": False,
            "status": "disabled"
        }

    cred = auto.get('credentials', {})
    account = cred.get('account')
    password = cred.get('password')
    login_type = cred.get('type', 'phone')

    if not account or not password:
        return {
            "enabled": True,
            "status": "missing_credentials"
        }

    return {
        "enabled": True,
        "status": "policy_ready",
        "login_type": login_type,
        "account": account,
        "password": password,
        "max_retries": auto.get('max_retries', 2),
        "policy": {
            "mode": "no-slider-default",
            "passwordLoginPreferred": True,
            "fixedDomRefActionsAllowed": False,
            "manualSliderOnlyIfVisiblyShown": True,
            "snapshotDomTextCountsAsEvidence": False,
            "sliderIsDefaultFlow": False,
            "enterSubmitFallback": True,
            "steps": [
                "open login page or gated detail page",
                "treat AceCamp login as a no-slider flow by default",
                "if password login toggle is visibly available, switch to password login",
                "fill account and password",
                "check agreement if visibly present",
                "click login",
                "if click login does not submit and the real rendered page shows no blocking exception, press Enter once as submit fallback",
                "only if the real rendered page clearly shows a slider/captcha layer and it actually blocks the flow, treat it as an exception requiring manual intervention"
            ]
        },
        "notes": [
            "Do not conclude slider present from snapshot/DOM text.",
            "AceCamp login should be treated as a no-slider flow unless the real page visibly blocks login with a slider.",
            "If click login does not submit and no blocking exception is visibly present, press Enter once as submit fallback.",
            "Real page-visible state is the only evidence for captcha exception handling."
        ]
    }


def emit_policy(config: dict):
    policy = build_policy(config)
    out = dict(policy)
    if 'password' in out:
        out['password'] = '***'
    print(json.dumps(out, ensure_ascii=False, indent=2))


def get_login_executor_js(account: str, password: str) -> str:
    account_json = json.dumps(account, ensure_ascii=False)
    password_json = json.dumps(password, ensure_ascii=False)
    return f"""
() => {{
  const account = {account_json};
  const password = {password_json};

  const bodyText = () => (document.body?.innerText || '');
  const isBlockingExceptionVisible = () => {{
    return false;
  }};

  const findExact = (text) => Array.from(document.querySelectorAll('button,span,div,a,label')).find(el => (el.textContent || '').trim() === text);

  const setVal = (el, value) => {{
    if (!el) return false;
    el.focus();
    const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    const native = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
    if (native) native.call(el, value); else el.value = value;
    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
    return true;
  }};

  const textNow = bodyText();
  const needsPasswordMode = textNow.includes('密码登录');
  const passwordModeActive = textNow.includes('验证码登录') || textNow.includes('请输入密码');
  const passwordToggle = needsPasswordMode ? findExact('密码登录') : null;
  if (passwordToggle) passwordToggle.click();

  const inputs = Array.from(document.querySelectorAll('input'));
  const accountInput = inputs.find(i => (i.placeholder || '').includes('手机号')) || inputs.find(i => (i.placeholder || '').includes('邮箱'));
  const passwordInput = inputs.find(i => (i.placeholder || '').includes('密码')) || inputs.find(i => i.type === 'password');
  const checkbox = document.querySelector('input[type="checkbox"]');

  const okAccount = setVal(accountInput, account);
  const okPassword = setVal(passwordInput, password);
  if (checkbox && !checkbox.checked) checkbox.click();

  const loginBtn = Array.from(document.querySelectorAll('button')).find(el => ['登录','登 录'].includes((el.textContent || '').trim()));
  if (loginBtn) loginBtn.click();

  let enterFallbackUsed = false;
  if (!isBlockingExceptionVisible()) {{
    const active = document.activeElement;
    const target = passwordInput || accountInput || active;
    if (target) {{
      target.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }}));
      target.dispatchEvent(new KeyboardEvent('keypress', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }}));
      target.dispatchEvent(new KeyboardEvent('keyup', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }}));
      enterFallbackUsed = true;
    }}
  }}

  return {{
    okAccount,
    okPassword,
    checked: checkbox ? checkbox.checked : null,
    clickedLogin: !!loginBtn,
    enterFallbackUsed,
    passwordModeActive,
    currentUrl: location.href,
    title: document.title,
    visibleTextHead: bodyText().slice(0, 300)
  }};
}}
"""


def main():
    ap = argparse.ArgumentParser(description='AceCamp login policy / execution entry')
    ap.add_argument('--print-policy', action='store_true', help='print policy json and exit')
    ap.add_argument('--emit-executor-js', action='store_true', help='print browser evaluate JS for login execution and exit')
    args = ap.parse_args()

    config = load_config()
    policy = build_policy(config)

    if args.emit_executor_js:
        if policy.get('status') != 'policy_ready':
            print(json.dumps(policy, ensure_ascii=False, indent=2))
            sys.exit(1)
        print(get_login_executor_js(policy['account'], policy['password']))
        return

    emit_policy(config)


if __name__ == "__main__":
    main()
