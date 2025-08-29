# telegram_notify.py
import os, requests
from typing import Optional

"""
Minimal Telegram notifier. Reads token/chat_id from env or parameters.
To use it:

from dotenv import load_dotenv
load_dotenv()  # before importing or calling send_telegram

from telegram_notify import send_telegram

send_telegram("Hello, world!")
"""

API_BASE = "https://api.telegram.org"

def send_telegram(
    message: str,
    chat_id: Optional[str] = None,
    token: Optional[str] = None,
    parse_mode: Optional[str] = None,
    disable_web_page_preview: bool = True,
    timeout: int = 10,
    debug: bool = False,
) -> bool:
    """Send a Telegram message. Returns True on success, False otherwise."""
    # Read from env at call time (avoids import-time empty vars)
    chat_id = (chat_id or os.getenv("TELEGRAM_CHAT_ID", "")).strip()
    token   = (token   or os.getenv("TELEGRAM_BOT_TOKEN", "")).strip()

    if not chat_id or not token:
        if debug:
            print("Telegram config missing: TELEGRAM_CHAT_ID or TELEGRAM_BOT_TOKEN.")
        return False

    url = f"{API_BASE}/bot{token}/sendMessage"
    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)] or [""]

    ok_all = True
    for chunk in chunks:
        data = {
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if parse_mode:
            data["parse_mode"] = parse_mode

        try:
            r = requests.post(url, data=data, timeout=timeout)
            if debug:
                print("Telegram status:", r.status_code)
                try:
                    print("Telegram resp:", r.json())
                except Exception:
                    print("Telegram resp (text):", r.text)
            if not r.ok or not r.json().get("ok", False):
                ok_all = False
        except Exception as e:
            if debug:
                print("Telegram exception:", repr(e))
            ok_all = False
    return ok_all
