"""Banglish (Romanized Bengali) detection, normalization and phonetic transliteration.

Converts informal Romanized Bengali queries (e.g. 'krittim buddhimotta' or
'amr chuti koto din baki?') into standard Unicode Bengali ('কৃত্রিম বুদ্ধিমত্তা',
'আমার ছুটি কত দিন বাকি?'), allowing seamless hybrid search across Bengali documents.
"""

import re
import unicodedata
from functools import lru_cache

import avro

# Common Banglish informal words, slang, contractions, and tricky phonetic spellings
# mapped directly to standard Unicode Bengali.
BANGLISH_DICTIONARY: dict[str, str] = {
    # Pronouns & Common queries
    "amar": "আমার",
    "amr": "আমার",
    "amader": "আমাদের",
    "apnar": "আপনার",
    "apnr": "আপনার",
    "apnader": "আপনাদের",
    "tumi": "তুমি",
    "tomar": "তোমার",
    "tumar": "তোমার",
    "she": "সে",
    "tara": "তারা",
    "tader": "তাদের",
    # Question words
    "koto": "কত",
    "kotho": "কত",
    "kotoTuku": "কতটুকু",
    "kotodin": "কতদিন",
    "kemon": "কেমন",
    "kmn": "কেমন",
    "keno": "কেন",
    "kno": "কেন",
    "kobe": "কবে",
    "kothay": "কোথায়",
    "ki": "কী",
    "kee": "কী",
    # Verbs / Auxiliaries
    "ache": "আছে",
    "ase": "আছে",
    "asen": "আছেন",
    "achen": "আছেন",
    "nai": "নাই",
    "nei": "নেই",
    "hobe": "হবে",
    "hbe": "হবে",
    "hocche": "হচ্ছে",
    "hoyeche": "হয়েছে",
    "korbe": "করবে",
    "krbe": "করবে",
    "korte": "করতে",
    "krte": "করতে",
    "kora": "করা",
    "kori": "করি",
    "pabo": "পাবো",
    "paben": "পাবেন",
    "paowa": "পাওয়া",
    "jabe": "যাবে",
    "jaoa": "যাওয়া",
    "gele": "গেলে",
    "geleo": "গেলেও",
    "bolun": "বলুন",
    "janan": "জানান",
    "dekhan": "দেখান",
    "chai": "চাই",
    "chaichen": "চাইছেন",
    # Connectives & Modifiers
    "kintu": "কিন্তু",
    "ebong": "এবং",
    "ar": "আর",
    "aar": "আর",
    "shob": "সব",
    "sob": "সব",
    "shokol": "সকল",
    "shudhu": "শুধু",
    "sudhu": "শুধু",
    "baki": "বাকি",
    "baire": "বাইরে",
    "ekhane": "এখানে",
    "shekhane": "সেখানে",
    "othoba": "অথবা",
    "doya": "দয়া",
    "kore": "করে",
    "plz": "দয়া করে",
    "pls": "দয়া করে",
    # Enterprise, HR, & Domain-specific terms
    "chuti": "ছুটি",
    "suti": "ছুটি",
    "din": "দিন",
    "dine": "দিনে",
    "bochor": "বছর",
    "bochhor": "বছর",
    "bosor": "বছর",
    "doinik": "দৈনিক",
    "dainik": "দৈনিক",
    "taka": "টাকা",
    "vata": "ভাতা",
    "bhata": "ভাতা",
    "biniyog": "বিনিয়োগ",
    "biniog": "বিনিয়োগ",
    "prokolpo": "প্রকল্প",
    "shorkar": "সরকার",
    "sorkar": "সরকার",
    "nitimala": "নীতিমালা",
    "shikriti": "স্বীকৃতি",
    "sompadona": "সম্পাদনা",
    "rohingya": "রোহিঙ্গা",
    "dhaka": "ঢাকা",
    "dhakar": "ঢাকার",
    "bidesh": "বিদেশ",
    "kaj": "কাজ",
    "krittim": "কৃত্রিম",
    "kritrim": "কৃত্রিম",
    "buddhimotta": "বুদ্ধিমত্তা",
    "buddhimatta": "বুদ্ধিমত্তা",
    "rail": "রেল",
    "shongkranto": "সংক্রান্ত",
    "onumoti": "অনুমতি",
    "bebostha": "ব্যবস্থা",
}

# High-frequency English words used to distinguish real English from Banglish queries.
COMMON_ENGLISH_WORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "in", "on", "at", "to", "for",
    "with", "by", "from", "up", "about", "into", "over", "after", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "can", "could", "should",
    "would", "will", "shall", "may", "might", "must", "what", "which", "who", "whom", "this",
    "that", "these", "those", "how", "many", "much", "days", "annual", "leave", "policy",
    "handbook", "guidelines", "travel", "allowance", "remote", "work", "salary", "bonus",
    "office", "rules", "employee", "company", "get", "take", "apply", "request", "please",
    "tell", "me", "find", "show", "where", "when", "why", "who", "report", "benefit",
})

_WORD_PATTERN = re.compile(r"[a-zA-Z]+|\d+|[^\s\w]+|\s+")
_BANGLA_CHAR_RE = re.compile(r"[\u0980-\u09FF]")


def is_banglish(text: str) -> bool:
    """Returns True if the text appears to be Romanized Bengali (Banglish).

    - If the text contains native Bengali script (Unicode), returns False.
    - If words predominantly match English vocabulary, returns False.
    - If words match Banglish dictionary or common Banglish morphology, returns True.
    """
    if _BANGLA_CHAR_RE.search(text):
        return False

    raw_words = [w.lower() for w in re.findall(r"[a-zA-Z]+", text)]
    if not raw_words:
        return False

    banglish_score = 0
    english_score = 0

    for word in raw_words:
        if word in BANGLISH_DICTIONARY:
            banglish_score += 2
        elif word in COMMON_ENGLISH_WORDS:
            english_score += 2
        else:
            # Check for Banglish morphological endings
            if any(word.endswith(suffix) for suffix in ("chhe", "chhi", "hobe", "korbe", "korte", "pabo", "jabe")):
                banglish_score += 1.5

    if banglish_score > 0 and banglish_score >= english_score:
        return True

    return False


@lru_cache(maxsize=10_000)
def transliterate_banglish(text: str) -> str:
    """Convert Romanized Bengali (Banglish) to clean Unicode Bengali.

    Uses exact dictionary lookups for common terms, slang and shortcuts,
    and falls back to Avro phonetic parsing for arbitrary words while
    preserving punctuation and whitespace.
    """
    tokens = _WORD_PATTERN.findall(text)
    output: list[str] = []

    for token in tokens:
        lower = token.lower()
        if lower in BANGLISH_DICTIONARY:
            output.append(BANGLISH_DICTIONARY[lower])
        elif token.isalpha():
            # Fall back to phonetic Avro transliteration
            output.append(avro.parse(token))
        else:
            output.append(token)

    result = "".join(output)
    return unicodedata.normalize("NFC", result)


def normalize_query(query: str) -> tuple[str, bool]:
    """Preprocesses a user query for search.

    If the query is detected as Banglish, it is transliterated to standard
    Unicode Bengali.

    Returns:
        `(query_for_search, was_banglish_transliterated)`
    """
    if is_banglish(query):
        return transliterate_banglish(query), True
    return query, False
