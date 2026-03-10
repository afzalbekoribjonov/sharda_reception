from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent

SUPPORTED_LANGS = ("uz", "ru", "en")
DEFAULT_LANG = "uz"


def load_translations() -> dict[str, dict[str, str]]:
    translations: dict[str, dict[str, str]] = {}
    for lang in SUPPORTED_LANGS:
        p = BASE_DIR / f"{lang}.json"
        data: dict[str, Any] = json.loads(p.read_text(encoding="utf-8-sig"))
        translations[lang] = {str(k): str(v) for k, v in data.items()}
    return translations