"""Tests for Banglish detection, normalization and phonetic transliteration."""

from knowledge_worker.text.banglish import (
    is_banglish,
    normalize_query,
    transliterate_banglish,
)


class TestBanglishDetection:
    def test_detects_common_banglish_queries(self):
        assert is_banglish("krittim buddhimotta")
        assert is_banglish("amr chuti koto din baki?")
        assert is_banglish("dhakar baire gele doinik vata koto?")
        assert is_banglish("japan koto taka biniyog korbe")
        assert is_banglish("chuti kobe pabo?")

    def test_does_not_flag_pure_english(self):
        assert not is_banglish("What is the annual leave policy?")
        assert not is_banglish("how many days of leave do employees get?")
        assert not is_banglish("travel allowance outside Dhaka")
        assert not is_banglish("remote work guidelines")

    def test_does_not_flag_native_bangla(self):
        assert not is_banglish("ছুটির নীতিমালা কী?")
        assert not is_banglish("কৃত্রিম বুদ্ধিমত্তা নিয়ে কী বলা হয়েছে?")
        assert not is_banglish("ঢাকার বাইরে যাতায়াত ভাতা কত?")

    def test_empty_or_punctuation_only(self):
        assert not is_banglish("")
        assert not is_banglish("???")
        assert not is_banglish("123 456")


class TestBanglishTransliteration:
    def test_transliterate_krittim_buddhimotta(self):
        result = transliterate_banglish("krittim buddhimotta")
        assert result == "কৃত্রিম বুদ্ধিমত্তা"

    def test_transliterate_amr_chuti(self):
        result = transliterate_banglish("amr chuti koto din baki?")
        assert result == "আমার ছুটি কত দিন বাকি?"

    def test_transliterate_japan_biniyog(self):
        result = transliterate_banglish("japan koto taka biniyog korbe")
        assert result == "জাপান কত টাকা বিনিয়োগ করবে"

    def test_transliterate_dhaka_vata(self):
        result = transliterate_banglish("dhakar baire gele doinik vata koto?")
        assert result == "ঢাকার বাইরে গেলে দৈনিক ভাতা কত?"

    def test_preserves_digits_and_symbols(self):
        result = transliterate_banglish("amr 20 din chuti ache!")
        assert "আমার" in result
        assert "২০" in result or "20" in result
        assert "ছুটি" in result
        assert "আছে!" in result


class TestNormalizeQuery:
    def test_banglish_is_normalized_to_bangla(self):
        normalized, was_banglish = normalize_query("krittim buddhimotta")
        assert was_banglish is True
        assert normalized == "কৃত্রিম বুদ্ধিমত্তা"

    def test_english_query_stays_english(self):
        query = "annual leave policy"
        normalized, was_banglish = normalize_query(query)
        assert was_banglish is False
        assert normalized == query

    def test_bangla_query_stays_bangla(self):
        query = "ছুটির নীতিমালা"
        normalized, was_banglish = normalize_query(query)
        assert was_banglish is False
        assert normalized == query
