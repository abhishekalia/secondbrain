# core/llm.py
import json, time, logging
from typing import List, Dict
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_TAG = "mistral:latest"
TIMEOUT_S = 30
RETRIES = 2

logger = logging.getLogger(__name__)

class LLMError(RuntimeError):
    pass

def chat(messages: List[Dict], stream: bool = False) -> str:
    payload = {
        "model": MODEL_TAG,
        "messages": messages,
        "stream": False if stream else False,
    }
    data = json.dumps(payload).encode("utf-8")

    last_err = None
    for attempt in range(RETRIES + 1):
        try:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                body = resp.read().decode("utf-8")
                j = json.loads(body)
                content = (j.get("message") or {}).get("content", "").strip()
                if not content:
                    raise LLMError("Empty LLM response")
                return content
        except Exception as e:
            last_err = e
            logger.exception("LLM call failed (attempt %d): %s", attempt + 1, e)
            time.sleep(0.5 * (attempt + 1))
    raise LLMError(f"LLM call failed after retries: {last_err}")

