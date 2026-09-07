"""
DeepSeek client (OpenAI-compatible). Fails softly: callers pass a fallback string.

Env vars:
  DEEPSEEK_API_KEY   — required to enable LLM
  DEEPSEEK_MODEL     — default 'deepseek-chat'
  DEEPSEEK_BASE_URL  — default 'https://api.deepseek.com'
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_dotenv():
    """Minimal .env loader — no dependency on python-dotenv."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        # Do not overwrite an existing real env var
        os.environ.setdefault(k, v)


_load_dotenv()
_client = None
_model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def is_available() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY"))


def _get_client():
    global _client
    if _client is not None:
        return _client
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
        _client = OpenAI(
            api_key=key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
        return _client
    except Exception as e:
        print(f"[llm] client init failed: {e}", file=sys.stderr)
        return None


def call(prompt: str, *, system: str | None = None, fallback: str = "",
         max_tokens: int = 700, temperature: float = 0.4) -> str:
    """Return LLM text on success, `fallback` on any error or missing key."""
    client = _get_client()
    if client is None:
        return fallback
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or fallback
    except Exception as e:
        print(f"[llm] call failed ({type(e).__name__}: {e}) — using fallback", file=sys.stderr)
        return fallback
