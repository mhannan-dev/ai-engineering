"""Script-based language detection (English / Bangla) and legacy Bijoy-encoding detection."""

from typing import Literal

Language = Literal["en", "bn", "mixed", "unknown"]

_BENGALI_START, _BENGALI_END = 0x0980, 0x09FF

# Bijoy / SutonnyMJ fonts map Bangla glyphs onto Latin-1 code points, so text extracted from
# such PDFs looks like "Avgvi †mvbvi evsjv". These marks almost never appear in real English.
_BIJOY_MARKS = frozenset("†‡ˆ¨©¯­Ö×ÕØÿ")
_BIJOY_MARK_RATIO = 0.01


def _letter_counts(text: str) -> tuple[int, int]:
    bengali = latin = 0
    for ch in text:
        if _BENGALI_START <= ord(ch) <= _BENGALI_END:
            bengali += 1
        elif ch.isascii() and ch.isalpha():
            latin += 1
    return bengali, latin


def detect_language(text: str) -> Language:
    """Classify by script share: >=80% one script wins, otherwise mixed."""
    bengali, latin = _letter_counts(text)
    total = bengali + latin
    if total < 20:
        return "unknown"
    share = bengali / total
    if share >= 0.8:
        return "bn"
    if share <= 0.2:
        return "en"
    return "mixed"


def looks_like_bijoy(text: str) -> bool:
    """True when text is Bangla stored in a legacy ASCII font encoding instead of Unicode."""
    chars = [ch for ch in text if not ch.isspace()]
    if len(chars) < 200:
        return False
    bengali, _ = _letter_counts(text)
    marks = sum(ch in _BIJOY_MARKS for ch in chars)
    return bengali / len(chars) < 0.01 and marks / len(chars) >= _BIJOY_MARK_RATIO
