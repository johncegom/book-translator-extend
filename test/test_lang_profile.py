"""Profile-API tests for scripts/lang_profile.py (Phase 1, zh-tw only).

Written before the module exists (red first). Expected values come from the
bb0eb35 golden file (test/golden/golden_zh_tw.json), not from the new code.
The guard tests run every consumer with a sentinel profile and assert that no
zh-tw data leaks through a dropped pass-through.
"""
from __future__ import annotations

import dataclasses
import json
import re
import zipfile
from pathlib import Path

import pytest

from scripts import (
    bilingual_coverage_audit,
    bilingual_rewriter,
    nav_builder,
    opf_builder,
    paragraph_classification,
    translation_quality_audit,
)
from scripts.lang_profile import ZH_TW, LanguageProfile, get_profile, resolve_profile

GOLDEN = json.loads((Path(__file__).parent / "golden" / "golden_zh_tw.json").read_text(encoding="utf-8"))
HAN = re.compile(r"[㐀-鿿]")

EXPECTED_FIELDS = {
    "code", "long_name", "html_lang", "target_class", "structural_labels", "contents_labels", "prefix_labels",
    "footnote_label", "bilingual_edition_label", "aup_refused_notice", "prompt_rules",
    "default_custom_instructions", "is_target_text",
}


def _sentinel() -> LanguageProfile:
    return dataclasses.replace(
        ZH_TW,
        code="sentinel",
        long_name="SENTINEL-LANG",
        html_lang="xx-Sentinel",
        target_class="tgt-sentinel",
        structural_labels={},
        contents_labels={"Contents": "CONTENTS_S"},
        prefix_labels=(),
        footnote_label="FN_S {n}",
        bilingual_edition_label="EDITION_S",
        aup_refused_notice="AUP_S",
        prompt_rules="RULES_S",
        default_custom_instructions="CUSTOM_S",
        is_target_text=lambda text: "Ω" in text,
    )


# --- registry and shape ------------------------------------------------------


def test_profile_has_exactly_the_approved_fields():
    assert {f.name for f in dataclasses.fields(LanguageProfile)} == EXPECTED_FIELDS


def test_zh_tw_profile_matches_oracle_data():
    assert ZH_TW.code == "zh-tw"
    assert ZH_TW.long_name == GOLDEN["target_long"]["zh-tw"]
    assert ZH_TW.html_lang == "zh-Hant"
    assert ZH_TW.target_class == "tgt-zh"
    assert ZH_TW.structural_labels == GOLDEN["tables"]["structural"]
    assert ZH_TW.contents_labels == GOLDEN["tables"]["contents"]
    assert [list(p) for p in ZH_TW.prefix_labels] == GOLDEN["tables"]["prefix"]
    assert ZH_TW.footnote_label.format(n=3) == "註腳 3"
    assert ZH_TW.bilingual_edition_label == "中英對照"
    assert ZH_TW.aup_refused_notice in GOLDEN["tables"]["aup_template"]
    assert HAN.search(ZH_TW.aup_refused_notice)
    assert ZH_TW.prompt_rules and ZH_TW.default_custom_instructions


def test_is_target_text_matches_oracle_han_check():
    for sample, results in GOLDEN["han"].items():
        assert ZH_TW.is_target_text(sample) is results["pc_HAN_RE"], repr(sample)


def test_profile_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        ZH_TW.code = "other"  # type: ignore[misc]


def test_get_profile_is_strict_and_case_insensitive_for_registered_codes():
    assert get_profile("zh-tw").code == "zh-tw"
    assert get_profile("ZH-TW").code == "zh-tw"
    with pytest.raises(ValueError):
        get_profile("vi")


@pytest.mark.parametrize("code", ["zh-tw", "ZH-TW", "zh-TW", "zh-cn", "en", "ja", "ko", "fr", "", "vi"])
def test_resolve_profile_falls_back_to_zh_tw(code):
    assert resolve_profile(code).code == "zh-tw"


def test_resolve_profile_handles_none():
    assert resolve_profile(None).code == "zh-tw"


# --- guard: no consumer falls back to zh-tw when given another profile --------


def test_rewriter_uses_profile_class_and_notice():
    entry = {"id": "item_003", "output_strategy": "translate", "first_heading": "H", "original_idref": "x"}
    src = "<html><body><p>First paragraph long enough to translate here.</p></body></html>"
    out = bilingual_rewriter.insert_bilingual(src, entry, ["Ω one"], profile=_sentinel())
    html = out[0] if isinstance(out, tuple) else out
    assert "tgt-sentinel" in html
    assert "tgt-zh" not in html and not HAN.search(html)
    aup = bilingual_rewriter.insert_bilingual(src, entry, [], chapter_status="aup_refused",
                                              aup_reason="why", profile=_sentinel())
    aup_html = aup[0] if isinstance(aup, tuple) else aup
    assert "AUP_S" in aup_html and "why" in aup_html and not HAN.search(aup_html)


def test_nav_uses_profile_labels_and_language():
    manifest = {"title": "T", "book_stem": "t"}
    entries = [
        {"id": "item_001", "output_strategy": "translate", "first_heading": "Contents", "original_idref": "c1",
         "original_path": "OEBPS/c1.xhtml"},
        {"id": "item_002", "output_strategy": "translate", "first_heading": "Footnote 7", "original_idref": "c2",
         "original_path": "OEBPS/c2.xhtml"},
    ]
    nav = nav_builder.build_nav_xhtml(manifest, entries, "OEBPS/nav.xhtml", "OEBPS", profile=_sentinel())
    assert 'lang="xx-Sentinel"' in nav and "EDITION_S" in nav and "CONTENTS_S" in nav and "FN_S 7" in nav
    assert "zh-Hant" not in nav and not HAN.search(nav)


def test_opf_uses_profile_language():
    opf = opf_builder.build_minimal_opf({"title": "T", "book_stem": "t"}, [], "OEBPS/content.opf", None,
                                        profile=_sentinel())
    assert "<dc:language>xx-Sentinel</dc:language>" in opf and "zh-Hant" not in opf


def test_is_english_content_uses_profile_target_check():
    mixed_han = "The quick brown fox 狐狸 jumps over the lazy dog and keeps running far away."
    mixed_omega = "The quick brown fox Ω jumps over the lazy dog and keeps running far away."
    sentinel = _sentinel()
    assert paragraph_classification.is_english_content(mixed_han) is False
    assert paragraph_classification.is_english_content(mixed_han, profile=sentinel) is True
    assert paragraph_classification.is_english_content(mixed_omega, profile=sentinel) is False


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


SRC_TEXT = "This is a long English paragraph that clearly needs a translated sibling after it for coverage."


def test_coverage_audit_uses_profile_target_check(tmp_path):
    omega = tmp_path / "omega.epub"
    han = tmp_path / "han.epub"
    _write_epub(omega, f'<p class="src">{SRC_TEXT}</p><p class="tgt tgt-sentinel">Ω {SRC_TEXT}</p>')
    _write_epub(han, f'<p class="src">{SRC_TEXT}</p><p class="tgt tgt-zh">這是一段很長的中文翻譯內容。</p>')
    sentinel = _sentinel()
    assert bilingual_coverage_audit.audit(omega, omega, profile=sentinel)[0] is True
    assert bilingual_coverage_audit.audit(han, han, profile=sentinel)[0] is False
    # default profile unchanged
    assert bilingual_coverage_audit.audit(han, han)[0] is True
    assert bilingual_coverage_audit.audit(omega, omega)[0] is False


def test_quality_audit_uses_profile_target_check(tmp_path):
    inline_omega = tmp_path / "inline_omega.epub"
    inline_han = tmp_path / "inline_han.epub"
    _write_epub(inline_omega, '<p class="src">Title Ω inline bilingual</p>')
    _write_epub(inline_han, '<p class="src">Title 標題 inline bilingual</p>')
    sentinel = _sentinel()
    ok, failures = translation_quality_audit.audit(inline_omega, profile=sentinel)
    assert ok is True, failures
    ok, failures = translation_quality_audit.audit(inline_han, profile=sentinel)
    assert ok is False and "source-only paragraph not in exceptions" in failures[0]
    # default profile unchanged
    assert translation_quality_audit.audit(inline_han)[0] is True
    assert translation_quality_audit.audit(inline_omega)[0] is False


def test_dispatch_prompt_uses_profile_rules():
    from scripts import dispatch

    prompt = dispatch.build_subagent_prompt(
        chapter_label="item_003", book_title="Alice", target_lang="zh-tw", glossary={},
        style_sample="s", carryover="c", chapter_html="<p>Hello world, this is Alice.</p>",
        profile=_sentinel(),
    )
    assert "RULES_S" in prompt and "SENTINEL-LANG" in prompt
    assert "台灣繁體中文" not in prompt
