import json
from typing import Dict, Optional

_translations: Dict[str, Dict[str, str]] = {}


def set_translations(locale: str, mapping: Dict[str, str]) -> None:
    """Set translations for a locale."""
    _translations[locale] = mapping


def load_translations(locale: str, file_path: str) -> None:
    """Load translations for *locale* from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as handle:
        _translations[locale] = json.load(handle)


def translate(key: str, locale: str, *, default: Optional[str] = None) -> str:
    """Return the translated string for *key* in *locale*."""
    return _translations.get(locale, {}).get(
        key, default if default is not None else key
    )
