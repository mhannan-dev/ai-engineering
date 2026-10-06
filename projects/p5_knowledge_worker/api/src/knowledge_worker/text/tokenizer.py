"""Bilingual (English + Bangla) tokenizer for BM25.

The usual BM25 pattern `\\b\\w\\w+\\b` splits Bangla words at every vowel sign, because Python does
not treat combining marks (া ি ু ্ ...) as word characters: "ছুটির নীতিমালা" becomes ["অন", "কর"].
Here a token is any run of Latin letters/digits or Bengali-block characters, so marks stay inside
the word. English tokens get Snowball stemming; Bangla tokens get a light suffix stripper.
"""

import re
import unicodedata
from functools import lru_cache

from bm25s.stopwords import STOPWORDS_EN
from py_rust_stemmers import SnowballStemmer

from knowledge_worker.text.normalize import normalize_for_search

_TOKEN = re.compile(r"[a-z0-9]+|[ঀ-৿]+")
_BENGALI_VOWEL_SIGNS = frozenset(chr(c) for c in range(0x09BE, 0x09CD))  # া ি ী ু ূ ৃ ে ৈ ো ৌ

_STOPWORDS_BN = frozenset(
    unicodedata.normalize("NFC", w)
    for w in """
    এবং ও যে এই সেই এটা এটি ওই করে হয় থেকে জন্য না কি কী তার তাদের একটি এক আর বা কিন্তু হবে ছিল
    হয়েছে করা এর যা তা সে আমি আমরা তুমি আপনি তিনি তারা কোন কোনো সব সকল মধ্যে উপর নিয়ে দিয়ে পর
    আগে এখন তবে যদি তাহলে শুধু আরও অনেক খুব হলো হল হচ্ছে ছিলেন করেন করতে থাকে নয় নেই হতে যেমন
    """.split()
)
_STOPWORDS = frozenset(STOPWORDS_EN) | _STOPWORDS_BN

# Noun inflections, longest first. Stripped only when the stem keeps two base letters (vowel
# signs don't count), so "বইটি" -> "বই" but "ছুটি" (leave) is not cut down to "ছু".
_BN_SUFFIXES = tuple(
    unicodedata.normalize("NFC", s)
    for s in ("গুলোতে", "গুলোর", "গুলো", "গুলি", "দেরকে", "দের", "টিতে", "টির", "টার", "টি", "টা",
              "খানা", "য়ের", "ের", "কে", "তে")
)
# Short endings, stripped only right after a vowel sign ("ছুটির" -> "ছুটি", "ঢাকায়" -> "ঢাকা",
# "কর্মীরা" -> "কর্মী") so that words which simply end in that letter ("শহর") stay intact.
_BN_AFTER_VOWEL = tuple(unicodedata.normalize("NFC", s) for s in ("রা", "য়", "র"))

_english = SnowballStemmer("english")


def _base_letters(text: str) -> int:
    return sum(not unicodedata.category(ch).startswith("M") for ch in text)


@lru_cache(maxsize=50_000)
def _stem_bn(token: str) -> str:
    for suffix in _BN_SUFFIXES:
        stem = token[: -len(suffix)]
        if token.endswith(suffix) and _base_letters(stem) >= 2:
            return stem
    for suffix in _BN_AFTER_VOWEL:
        stem = token[: -len(suffix)]
        if token.endswith(suffix) and _base_letters(stem) >= 2 and stem[-1] in _BENGALI_VOWEL_SIGNS:
            return stem
    return token


def tokenize(text: str) -> list[str]:
    """Normalize, split, drop stopwords and single characters, then stem each token."""
    tokens = []
    for token in _TOKEN.findall(normalize_for_search(text)):
        if token in _STOPWORDS or len(token) < 2:
            continue
        tokens.append(_english.stem_word(token) if token.isascii() else _stem_bn(token))
    return tokens
