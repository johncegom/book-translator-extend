"""Phase 3 (3.4): the Vietnamese ``is_target_text`` rule from the Advise outcome in
docs/tasks/03-detector-audits/TASK.md ("3.3 Advise outcome").

Ordinary test-first (no external oracle for Vietnamese). Labelled samples live in
test/data/vi_detector_samples.json; the cases below pin the boundaries of the rule.
Phase 2 tests in test_lang_profile_vi.py are unchanged and must stay green.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts import bilingual_coverage_audit
from scripts.lang_profile import get_profile

VI = get_profile("vi")
HERE = Path(__file__).parent
SAMPLES = json.loads((HERE / "data" / "vi_detector_samples.json").read_text(encoding="utf-8"))["samples"]


def test_sample_file_is_big_enough_and_covers_every_language():
    assert len(SAMPLES) >= 40
    kinds = {s["kind"] for s in SAMPLES}
    assert {"vi_long", "vi_short", "en_long", "en_short", "fr", "pt", "en_with_accents",
            "mixed_en_with_vi_name", "mixed_vi_with_en_term", "edge", "edge_nfd"} <= kinds


@pytest.mark.parametrize("sample", SAMPLES, ids=lambda s: f"{s['kind']}:{s['text'][:24]!r}")
def test_labelled_samples(sample):
    assert VI.is_target_text(sample["text"]) is sample["expected"]


# --- proper nouns do not count ------------------------------------------------

@pytest.mark.parametrize("text", [
    "He met Nguyễn.",                     # short: the only match is a capitalised name
    "Dinner at Đà Nẵng tonight",          # short, capitalised names only
    "Then Phạm Văn Đức left.",
])
def test_short_english_with_vietnamese_names_is_not_vietnamese(text):
    assert VI.is_target_text(text) is False


@pytest.mark.parametrize("text", [
    "Chương Một",                         # Title Case heading: no lowercase token, count every token
    "Nguyễn",
    "Đà Nẵng",
    "CHƯƠNG 1",
    "Ỹ",
])
def test_title_case_or_single_name_text_falls_back_to_all_tokens(text):
    assert VI.is_target_text(text) is True


def test_all_digit_tokens_are_ignored():
    assert VI.is_target_text("1234 5678") is False
    assert VI.is_target_text("Chapter 12") is False


def test_lowercase_initial_means_first_character_islower_after_nfc():
    # underscore and digit starts are not lowercase-initial; the fallback then counts them
    assert VI.is_target_text("_x 9y") is False
    # a decomposed lowercase word still counts after NFC
    import unicodedata
    assert VI.is_target_text(unicodedata.normalize("NFD", "người")) is True


# --- function words (short text) ---------------------------------------------

@pytest.mark.parametrize("word", ["và", "không", "tôi", "xin", "chào", "các", "này"])
def test_each_function_word_alone_in_lowercase_counts(word):
    assert VI.is_target_text(f"ok {word}") is True


@pytest.mark.parametrize("word", ["em", "là", "anh"])
def test_ambiguous_words_do_not_count(word):
    assert VI.is_target_text(f"ok {word}") is False
    assert VI.is_target_text(word) is False


def test_xin_chao_and_other_short_phrases():
    assert VI.is_target_text("Xin chào") is True
    assert VI.is_target_text("Tôi và em.") is True
    assert VI.is_target_text("Portuguese: eu vou em casa") is False


# --- share rule for long paragraphs -------------------------------------------

def _para(matching: int, other: int) -> str:
    # lowercase words only; "ăn" matches (distinctive letter), "background" does not
    return " ".join(["ăn"] * matching + ["background"] * other)


def test_share_rule_cutoff_is_a_quarter_of_the_lowercase_tokens():
    two_in_eight = _para(2, 6)          # share 0.25, >= 50 chars
    one_in_eight = _para(1, 7)          # share 0.125
    assert len(two_in_eight) >= 50 and len(one_in_eight) >= 50
    assert VI.is_target_text(two_in_eight) is True
    assert VI.is_target_text(one_in_eight) is False


def _exact_length(n: int) -> str:
    """'ăn' plus 'word' padding, lowercase only, exactly n characters, 1 match in the text."""
    text = "ăn" + " word" * ((n - 2) // 5)
    text += "d" * (n - len(text))
    assert len(text) == n
    return text


def test_fifty_character_boundary():
    # 49 chars: any single match is enough; 50 chars: the share rule applies (1 match in 10 tokens)
    assert VI.is_target_text(_exact_length(49)) is True
    assert VI.is_target_text(_exact_length(50)) is False


def test_english_paragraph_with_a_vietnamese_name_is_not_vietnamese():
    text = "Nguyễn walked into the room and sat down quietly by the window, thinking about the long day."
    assert VI.is_target_text(text) is False


def test_vietnamese_paragraph_with_english_names_still_counts():
    text = "Sue Bierman và ủy ban của bà tiếp tục làm việc với Embarcadero Freeway suốt nhiều năm."
    assert VI.is_target_text(text) is True


# --- audits use the rule on the source side too ------------------------------

def _write_epub(path: Path, body: str) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container version="1.0" '
            'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
            '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            "</rootfiles></container>",
        )
        z.writestr(
            "OEBPS/content.opf",
            '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0"><manifest>'
            '<item id="c1" href="xhtml/c1.xhtml" media-type="application/xhtml+xml"/></manifest>'
            '<spine><itemref idref="c1"/></spine></package>',
        )
        z.writestr("OEBPS/xhtml/c1.xhtml", f"<html><body>{body}</body></html>")


def test_long_english_source_with_a_vietnamese_name_is_not_exempt_from_coverage(tmp_path):
    src = "The restaurant owner, Phạm Văn Đức, welcomed every guest at the door and showed them to a table."
    path = tmp_path / "name.epub"
    _write_epub(path, f'<p class="src">{src}</p>')
    ok, failures, _warnings = bilingual_coverage_audit._audit_with_warnings(path, path, profile=VI)
    assert ok is False and failures


def test_short_english_source_with_a_vietnamese_name_is_flagged_not_skipped(tmp_path):
    # Short untranslated English goes amber by design (see bilingual_coverage_audit); the point is
    # that it is no longer silently exempted just because it contains a Vietnamese name.
    path = tmp_path / "short.epub"
    _write_epub(path, '<p class="src">He met Nguyễn in the market.</p>')
    ok, failures, warnings = bilingual_coverage_audit._audit_with_warnings(path, path, profile=VI)
    assert failures or warnings
