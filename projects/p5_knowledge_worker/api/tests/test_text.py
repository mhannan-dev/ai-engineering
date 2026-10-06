from knowledge_worker.text.language import detect_language, looks_like_bijoy
from knowledge_worker.text.normalize import normalize_for_search, normalize_text
from knowledge_worker.text.tokenizer import tokenize

BIJOY = (
    "Avgvi †mvbvi evsjv, Avwg †Zvgvq fvjevwm| wPiw`b †Zvgvi AvKvk, †Zvgvi evZvm, Avgvi cÖv‡Y "
    "evRvq evuwk| I gv, dvN¸‡b †Zvi Av‡gi ‡ev‡j ªv‡Y cvMj K‡i| "
) * 3


class TestTokenizer:
    def test_keeps_bangla_words_whole(self):
        # The default BM25 regex returns ['অন', 'কর', 'বছর', '২০'] for this sentence.
        tokens = tokenize("ছুটির নীতিমালা অনুযায়ী কর্মীরা বছরে ২০ দিন ছুটি পাবেন।")
        assert tokens == ["ছুটি", "নীতিমালা", "অনুযায়ী", "কর্মী", "বছরে", "20", "দিন", "ছুটি", "পাবেন"]

    def test_bangla_inflections_share_a_stem(self):
        assert tokenize("ঢাকায় অফিসের কর্মীদের ছুটিগুলো বইটি") == ["ঢাকা", "অফিস", "কর্মী", "ছুটি", "বই"]

    def test_does_not_overstem_short_bangla_words(self):
        # "শহর" ends in র after a consonant, "মাটি"/"ছুটি" end in টি but it is part of the word.
        assert tokenize("শহর মাটি ছুটি") == ["শহর", "মাটি", "ছুটি"]

    def test_bangla_stopwords_removed(self):
        assert tokenize("এবং এই জন্য ছুটি") == ["ছুটি"]

    def test_english_stemming_and_stopwords(self):
        assert tokenize("The Leave Policies") == ["leav", "polici"]

    def test_bangla_and_ascii_digits_match(self):
        assert tokenize("২০২৬") == tokenize("2026") == ["2026"]

    def test_zero_width_joiner_ignored(self):
        assert tokenize("র‍্যাংক") == tokenize("র্যাংক")


class TestNormalize:
    def test_collapses_whitespace_and_blank_lines(self):
        assert normalize_text("a  \t b\r\n\n\n\nc ") == "a b\n\nc"

    def test_search_form_lowercases_and_maps_digits(self):
        assert normalize_for_search("Room ১০১") == "room 101"


class TestLanguage:
    def test_english(self):
        assert detect_language("Employees receive twenty days of annual leave each year.") == "en"

    def test_bangla(self):
        assert detect_language("কর্মীরা প্রতি বছর বিশ দিনের বার্ষিক ছুটি পাবেন এবং তা জমা রাখা যাবে।") == "bn"

    def test_mixed(self):
        text = "Annual leave policy: কর্মীরা প্রতি বছর বিশ দিন ছুটি পাবেন, subject to approval."
        assert detect_language(text) == "mixed"

    def test_too_short_is_unknown(self):
        assert detect_language("ok") == "unknown"

    def test_detects_bijoy_encoding(self):
        assert looks_like_bijoy(BIJOY)

    def test_unicode_bangla_and_english_are_not_bijoy(self):
        assert not looks_like_bijoy("আমার সোনার বাংলা, আমি তোমায় ভালোবাসি। " * 10)
        assert not looks_like_bijoy("Employees receive twenty days of annual leave. " * 10)
