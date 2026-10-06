"""Unicode normalization shared by ingestion and querying, so both sides see identical text."""

import re
import unicodedata

# ZWJ / ZWNJ steer Bangla conjunct rendering (e.g. "র‍্যাংক") but carry no meaning for search.
_INVISIBLE = dict.fromkeys(map(ord, "​‌‍⁠﻿"), None)
_BANGLA_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_SPACES = re.compile(r"[ \t  -   　]+")
_BLANK_LINES = re.compile(r"\n{3,}")


def normalize_text(text: str) -> str:
    """Clean extracted text for storage: NFC, no invisible joiners, collapsed whitespace."""
    text = unicodedata.normalize("NFC", text).translate(_INVISIBLE)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(_SPACES.sub(" ", line).strip() for line in text.split("\n"))
    return _BLANK_LINES.sub("\n\n", text).strip()


def normalize_for_search(text: str) -> str:
    """Stricter form used only for matching: also lowercases and maps Bangla digits to ASCII."""
    return normalize_text(text).lower().translate(_BANGLA_DIGITS)
