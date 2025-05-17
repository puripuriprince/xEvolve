from __future__ import annotations

import os
from typing import Protocol

try:
    from google import genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None  # type: ignore

__all__ = ["generate"]

_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")


class _Callable(Protocol):
    def __call__(self, prompt: str) -> str: ...


def _real(prompt: str) -> str:
    if genai is None:
        raise RuntimeError("google-genai not installed")
    client = genai.Client(api_key=_API_KEY)
    return client.models.generate_content(model=_MODEL, contents=prompt).text


def _stub(prompt: str) -> str:
    return ""  # empty diff for offline/debug


generate: _Callable = _real if _API_KEY and _API_KEY != "YOUR_GEMINI_API_KEY" else _stub 