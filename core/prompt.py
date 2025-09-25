# core/prompt.py
from datetime import datetime
from typing import List, Optional

AK_SYSTEM_PROMPT = """
You are AK's local assistant (AKtivate.ai). Voice: witty, precise, kind.
Defaults: one sharp line. If asked for lists, use short bullets. Zero fluff.
Momentum > perfection. Prefer concrete steps over theory.
""".strip()

def build_messages(user_msg: str, context_snippets: Optional[List[str]] = None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    ctx = "\n\n".join([f"[CTX] {c.strip()}" for c in (context_snippets or []) if c.strip()])
    sys = AK_SYSTEM_PROMPT + f"\n\nNow: {now}"
    if ctx:
        sys += "\n\nContext snippets:\n" + ctx
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": user_msg.strip()},
    ]

