"""Tests for the Vietnamese (``vi``) profile and the Phase 2 profile fields.

Written before the implementation (red first). Ordinary test-first development:
there is no external oracle for Vietnamese. zh-tw expectations that must not
move come from the golden files (bb0eb35 / e0f41b6), never from the new code.
The expected label wording is the approved table in
docs/tasks/02-profile-vi/TASK.md.
"""
from __future__ import annotations

import json
import re
import unicodedata
import zipfile
from pathlib import Path

import pytest

from scripts import (
    assemble,
    audit_suite,
    bilingual_coverage_audit,
    bilingual_rewriter,
    dispatch,
    glossary,
    nav_builder,
    opf_builder,
    translation_quality_audit,
)
from scripts.lang_profile import ZH_TW, get_profile, resolve_profile

HERE = Path(__file__).parent
GOLDEN_P1 = json.loads((HERE / "golden" / "golden_zh_tw.json").read_text(encoding="utf-8"))
GOLDEN_P2 = json.loads((HERE / "golden" / "golden_zh_tw_phase2.json").read_text(encoding="utf-8"))
HAN = re.compile(r"[㐀-鿿豈-﫿]")
SLOT_NAMES = {"target_note", "name_advice", "title_rules", "avoid_example"}

VI = resolve_profile("vi")  # zh-tw until the vi profile is registered (Phase 2.5), so tests fail one by one


# --- registry and data ------------------------------------------------------


def test_vi_is_registered_and_lookup_is_case_insensitive():
    assert VI.code == "vi"
    assert get_profile("VI").code == "vi"
    assert resolve_profile("vi").code == "vi"
    assert resolve_profile("Vi").code == "vi"


def test_unregistered_code_still_raises_in_get_profile_and_falls_back_in_resolve():
    with pytest.raises(ValueError):
        get_profile("vn")
    assert resolve_profile("vn").code == "zh-tw"


def test_vi_scalar_fields():
    assert VI.long_name == "Tiếng Việt"
    assert VI.html_lang == "vi"
    assert VI.target_class == "tgt-vi"
    assert VI.footnote_label.format(n=7) == "Chú thích 7"
    assert VI.bilingual_edition_label == "Song ngữ Anh–Việt"
    assert VI.aup_refused_notice == "Chương này bị từ chối dịch do chính sách của LLM; giữ nguyên bản gốc, chưa dịch"
    assert VI.register_hints_file == "register_hints.vi.json"
    assert VI.simplified_gate is False


def test_vi_label_tables_use_the_same_english_keys_as_zh_tw():
    assert set(VI.structural_labels) == set(ZH_TW.structural_labels)
    assert set(VI.contents_labels) == set(ZH_TW.contents_labels)


def test_vi_label_wording_matches_the_approved_table():
    s, c = VI.structural_labels, VI.contents_labels
    assert s["Contents"] == "Mục lục" and c["Contents"] == "Mục lục"
    assert s["Introduction"] == "Lời nói đầu"
    assert s["PART I"] == "Phần I" and s["PART II"] == "Phần II"
    assert s["Acknowledgments"] == "Lời cảm ơn" and c["Acknowledgments"] == "Lời cảm ơn"
    assert s["Notes"] == "Chú thích" and c["Notes"] == "Chú thích"
    assert s["About the Author"] == "Về tác giả" and c["About the Author"] == "Về tác giả"
    assert c["Cover"] == "Bìa"
    assert c["Title Page"] == "Trang tiêu đề"
    assert c["Copyright"] == "Bản quyền"
    assert c["Dedication"] == "Lời đề tặng"
    assert s["Sign up now."] == "Đăng ký ngay."
    assert s["Discover your next great read!"] == "Khám phá cuốn sách hay tiếp theo của bạn!"
    assert s["What’s next on your reading list?"] == s["What's next on your reading list?"] == "Bạn sẽ đọc gì tiếp theo?"


def test_vi_prefix_labels():
    assert VI.prefix_labels == (
        ("praise for ", "Lời khen ngợi"),
        ("advance praise for ", "Lời khen ngợi"),
        ("also by ", "Cùng tác giả"),
    )


def test_vi_text_fields_have_no_han_and_no_braces_in_prompt_text():
    for field in ("long_name", "html_lang", "target_class", "footnote_label", "bilingual_edition_label",
                  "aup_refused_notice", "prompt_rules", "default_custom_instructions"):
        assert not HAN.search(getattr(VI, field)), field
    assert "{" not in VI.prompt_rules and "}" not in VI.prompt_rules
    assert VI.prompt_rules and VI.default_custom_instructions
    for mapping in (VI.structural_labels, VI.contents_labels):
        assert not any(HAN.search(v) for v in mapping.values())


def test_zh_tw_new_fields_keep_todays_behaviour():
    assert ZH_TW.register_hints_file == "register_hints.json"
    assert ZH_TW.simplified_gate is True
    assert list(ZH_TW.generic_rules) == GOLDEN_P2["generic_rules"]
    assert dispatch.GENERIC_SUBAGENT_RULES == GOLDEN_P2["generic_rules"]
    assert set(ZH_TW.glossary_prompt_slots) == SLOT_NAMES


def test_generic_rules_and_slots_for_vi():
    assert VI.generic_rules and all(isinstance(r, str) and r for r in VI.generic_rules)
    assert not any(HAN.search(r) for r in VI.generic_rules)
    assert set(VI.glossary_prompt_slots) == SLOT_NAMES
    for name, value in VI.glossary_prompt_slots.items():
        assert value.strip(), name
        assert "{" not in value and "}" not in value, name
        assert not HAN.search(value), name
    for value in ZH_TW.glossary_prompt_slots.values():
        assert "{" not in value and "}" not in value


# --- is_target_text ---------------------------------------------------------

# Letters shared with French/Portuguese (à á â ã è é ê ì í ò ó ô õ ù ú) do not count: a phrase such as
# "Xin chào" has none of the distinctive letters and is a known false negative that Phase 3's
# threshold/short-paragraph rules handle; it is deliberately not pinned here.
VI_POSITIVE = [
    "Tiếng Việt", "đường", "Đà Nẵng", "Nguyễn", "ăn cơm", "ơn", "ư", "ĩ", "ũ", "ạ", "ả", "ệ",
    "ổ", "ữ", "Ỹ", "Việt Nam", "mặt trời mọc",
    unicodedata.normalize("NFD", "Việt"),  # decomposed letters must still count
]
VI_NEGATIVE = [
    "", "plain english", "café", "naïve", "façade", "crêpe", "château", "rôle", "über", "señor", "Zoë",
    "1234", "hello world, this is a normal English sentence", "中文", "ひらがな", "Привет",
]


@pytest.mark.parametrize("text", VI_POSITIVE)
def test_vi_is_target_text_positive(text):
    assert VI.is_target_text(text) is True


@pytest.mark.parametrize("text", VI_NEGATIVE)
def test_vi_is_target_text_negative(text):
    assert VI.is_target_text(text) is False


def test_vi_detector_sample_count():
    assert len(VI_POSITIVE) + len(VI_NEGATIVE) >= 20


# --- register hints, glossary prompt, generic rules --------------------------


def test_vi_register_file_is_vietnamese_only_with_distinct_names():
    hints = glossary._load_register_hints(profile=VI)
    assert len(hints) >= 2
    assert {"literary_fiction", "non_fiction_narrative"} <= {h.get("id") for h in hints}
    blob = json.dumps(hints, ensure_ascii=False)
    assert not HAN.search(blob)
    assert re.search(r"[ăđơưĩũ]", blob), "register file should contain Vietnamese text"
    tokens = [{t for t in re.split(r"[\s/，,;；、]+", str(h["register"]).casefold()) if len(t) >= 2} for h in hints]
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens)):
            assert not (tokens[i] & tokens[j]), "register names must not share tokens (resolve_register matches on them)"
    assert all(h.get("subagent_rules") for h in hints)


def test_zh_tw_hints_unchanged_by_the_profile_argument():
    default = glossary._load_register_hints()
    assert default == glossary._load_register_hints(profile=ZH_TW)
    assert [h["id"] for h in default] == GOLDEN_P2["register_block"]["ids"]


def test_resolve_register_functions_use_the_profile_file():
    hints = glossary._load_register_hints(profile=VI)
    first = hints[0]
    found = glossary.resolve_register({"style_anchor": {"register": first["register"]}}, profile=VI)
    assert found is not None and found["id"] == first["id"]
    assert glossary.resolve_register({"style_anchor": {"register": first["register"]}}) is None  # zh file has no such name
    override = glossary.resolve_register_override("literary_fiction", profile=VI)
    assert override is not None and not HAN.search(json.dumps(override, ensure_ascii=False))
    rules = glossary.resolve_register_rules(
        {"style_anchor": {"register": first["register"]}}, fallback_rules=["F"], profile=VI)
    assert rules and rules != ["F"] and not any(HAN.search(r) for r in rules)


def test_build_glossary_prompt_for_zh_tw_is_byte_identical_to_the_constant_and_the_golden():
    assert glossary.build_glossary_prompt() == glossary.GLOSSARY_PROMPT
    assert glossary.build_glossary_prompt(ZH_TW) == glossary.GLOSSARY_PROMPT
    assert glossary.GLOSSARY_PROMPT == GOLDEN_P2["glossary_prompt"]["text"]


def test_build_glossary_prompt_for_vi():
    prompt = glossary.build_glossary_prompt(VI)
    for slot in ("__TARGET_NOTE__", "__NAME_ADVICE__", "__TITLE_RULES__", "__AVOID_EXAMPLE__", "__REGISTER_HINTS_BLOCK__"):
        assert slot not in prompt
    assert not HAN.search(prompt)
    assert "Chương 1" in prompt
    assert glossary._format_register_hints(glossary._load_register_hints(profile=VI)) in prompt
    rendered = prompt.format(source_lang="English", target_lang="vi", full_text="SAMPLE")
    assert "SAMPLE" in rendered
    assert "chapter_titles_zh" in prompt  # DECISION-002: the key name stays


# --- prompts ----------------------------------------------------------------


def _prompt(**kw):
    base = dict(chapter_label="item_003", book_title="Alice", target_lang="vi", glossary={"terms": {"Alice": "Alice"}},
                style_sample="Mẫu văn phong.", carryover="Phần trước.", chapter_html="<p>Hello world, this is Alice.</p>")
    base.update(kw)
    return dispatch.build_subagent_prompt(**base)


def test_vi_subagent_prompt_has_vietnamese_rules_and_no_chinese():
    prompt = _prompt()
    assert VI.prompt_rules in prompt
    assert "Tiếng Việt" in prompt
    assert "Traditional Chinese" not in prompt
    assert not HAN.search(prompt)
    assert VI.default_custom_instructions in prompt
    for rule in VI.generic_rules:
        assert rule in prompt


def test_vi_subagent_prompt_with_matched_register_uses_the_vi_register_rules():
    first = glossary._load_register_hints(profile=VI)[0]
    prompt = _prompt(glossary={"terms": {}, "style_anchor": {"register": first["register"]}})
    assert first["subagent_rules"][0] in prompt
    assert not HAN.search(prompt)


def test_zh_cn_and_en_prompts_keep_the_pinned_fallback():
    # The Phase 1 golden pins the zh-tw rule text for these codes; Phase 2 must not move it.
    for lang in ("zh-cn", "en"):
        text = _prompt(target_lang=lang, glossary={"terms": {"Alice": "愛麗絲"}}, style_sample="風格範例。",
                       carryover="前情提要。")
        assert ZH_TW.prompt_rules in text


# --- guards: new consumers honour a non-zh profile ---------------------------


def _vi_entry(first="Contents", idref="c1", strategy="translate"):
    return {"id": "item_001", "output_strategy": strategy, "first_heading": first, "original_idref": idref,
            "original_path": "OEBPS/c1.xhtml"}


def test_nav_with_vi_profile():
    entries = [_vi_entry("Contents"), {**_vi_entry("Footnote 7", "c2"), "id": "item_002"},
               {**_vi_entry("Praise for Some Book - a blurb", "c3"), "id": "item_003"}]
    nav = nav_builder.build_nav_xhtml({"title": "T"}, entries, "OEBPS/nav.xhtml", "OEBPS", profile=VI)
    assert 'lang="vi"' in nav and "Song ngữ Anh–Việt" in nav
    assert "Contents ｜ Mục lục" in nav and "Footnote 7 ｜ Chú thích 7" in nav and "Lời khen ngợi" in nav
    assert not HAN.search(nav) and "zh-Hant" not in nav


def test_opf_with_vi_profile():
    opf = opf_builder.build_minimal_opf({"title": "T", "book_stem": "t"}, [], "OEBPS/content.opf", None, profile=VI)
    assert "<dc:language>vi</dc:language>" in opf


def test_rewriter_with_vi_profile():
    entry = {"id": "item_003", "output_strategy": "translate", "first_heading": "H", "original_idref": "x"}
    src = "<html><body><p>First paragraph long enough to translate here.</p></body></html>"
    out = bilingual_rewriter.insert_bilingual(src, entry, ["Đoạn văn đầu tiên."], profile=VI)
    html = out[0] if isinstance(out, tuple) else out
    assert "tgt-vi" in html and "tgt-zh" not in html and not HAN.search(html)
    aup = bilingual_rewriter.insert_bilingual(src, entry, [], chapter_status="aup_refused", aup_reason="why", profile=VI)
    aup_html = aup[0] if isinstance(aup, tuple) else aup
    assert VI.aup_refused_notice in aup_html and not HAN.search(aup_html)


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


SRC = "This is a long English paragraph that clearly needs a translated sibling after it for the coverage audit."
VI_TGT = "Đây là một đoạn văn tiếng Việt khá dài, đã được dịch đầy đủ để kiểm tra độ bao phủ của bản dịch song ngữ."


def test_coverage_audit_vi_passes_with_translation_and_fails_without(tmp_path):
    good = tmp_path / "good.epub"
    echo = tmp_path / "echo.epub"
    missing = tmp_path / "missing.epub"
    _write_epub(good, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{VI_TGT}</p>')
    _write_epub(echo, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{SRC}</p>')
    _write_epub(missing, f"<p>{SRC}</p>")
    assert bilingual_coverage_audit.audit(good, good, profile=VI)[0] is True
    assert bilingual_coverage_audit.audit(echo, echo, profile=VI)[0] is False
    assert bilingual_coverage_audit.audit(missing, missing, profile=VI)[0] is False


SIMPLIFIED_QUOTE = "这是一个很长的简体中文引文，学国应该时这们个经历实来体现进觉党报见远边长万与业东严两临卫。"


def test_quality_audit_simplified_gate_is_off_for_vi_and_on_for_zh_tw(tmp_path):
    path = tmp_path / "quote.epub"
    tgt = f"{VI_TGT} Trích dẫn nguyên văn: {SIMPLIFIED_QUOTE}"
    _write_epub(path, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{tgt}</p>')
    ok_vi, failures_vi = translation_quality_audit.audit(path, profile=VI)
    assert ok_vi is True, failures_vi
    ok_zh, failures_zh = translation_quality_audit.audit(path)
    assert ok_zh is False and any("Simplified Chinese" in f for f in failures_zh)


def test_banned_patterns_still_apply_to_vi(tmp_path):
    path = tmp_path / "banned.epub"
    _write_epub(path, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">(untitled) {VI_TGT}</p>')
    ok, failures = translation_quality_audit.audit(path, profile=VI)
    assert ok is False and any("banned pattern" in f for f in failures)


def test_min_length_ratio_for_vi_falls_back_to_the_default(tmp_path):
    (tmp_path / "glossary.json").write_text(json.dumps({"style_anchor": {"register": "zzz unknown"}}), encoding="utf-8")
    assert translation_quality_audit._min_length_ratio_from_book_dir(tmp_path, profile=VI) == 0.22
    assert translation_quality_audit._min_length_ratio_from_book_dir(tmp_path) == 0.22


# --- strict target_lang handling and end-to-end assemble ----------------------


def _make_vi_book(tmp_path: Path, target_lang: str | None = "vi") -> Path:
    book = tmp_path / "tiny_book_vi"
    chapters = book / "chapters"
    chapters.mkdir(parents=True)
    (chapters / "item_001.html").write_text("<html><body><h1>Title Page</h1><p>Tiny Book</p></body></html>", encoding="utf-8")
    (chapters / "item_002.html").write_text(
        "<html><body><h1>Chapter 1</h1><p>Hello there, how are you today?</p><p>World.</p></body></html>", encoding="utf-8")
    (chapters / "ch_01_translation.txt").write_text(
        "Chương 1\n\nXin chào, hôm nay bạn thế nào?\n\nThế giới.", encoding="utf-8")
    spine = [
        {"id": "item_001", "src_idref": "title", "original_idref": "title", "src_href": "OEBPS/xhtml/title.xhtml",
         "original_path": "OEBPS/xhtml/title.xhtml", "href": "chapters/item_001.html", "linear": "yes",
         "media_type": "application/xhtml+xml", "role": "title_page", "char_count": 9, "first_heading": "Title Page",
         "output_strategy": "source_only"},
        {"id": "item_002", "src_idref": "x", "original_idref": "x", "src_href": "OEBPS/xhtml/x.xhtml",
         "original_path": "OEBPS/xhtml/x.xhtml", "href": "chapters/item_002.html", "linear": "yes",
         "media_type": "application/xhtml+xml", "role": "body", "char_count": 12, "first_heading": "Chapter 1",
         "output_strategy": "translate", "translation_id": "ch_01"},
    ]
    manifest = {"book_stem": "tiny_book_vi", "title": "Tiny Book", "authors": ["A"], "language": "en", "spine": spine,
                "chapters": [{"id": "ch_01", "spine_id": "item_002", "href": "chapters/item_002.html",
                              "src_href": "OEBPS/xhtml/x.xhtml", "original_path": "OEBPS/xhtml/x.xhtml",
                              "char_count": 12, "first_heading": "Chapter 1", "output_strategy": "translate"}]}
    (book / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    (book / "translations_extra.json").write_text(
        json.dumps({"nav_overrides": {"title": "Trang tiêu đề", "x": "Chương 1"}}, ensure_ascii=False), encoding="utf-8")
    if target_lang is not None:
        (book / "state.json").write_text(json.dumps({"target_lang": target_lang}), encoding="utf-8")
    return book


def _epub_text(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n).decode("utf-8", "replace") for n in z.namelist()
                if n.endswith((".xhtml", ".html", ".opf", ".ncx", ".json"))}


def test_assemble_vi_book_end_to_end(tmp_path):
    out = tmp_path / "out.epub"
    assemble.assemble(_make_vi_book(tmp_path, "vi"), out)
    files = _epub_text(out)
    joined = "\n".join(files.values())
    assert not HAN.search(joined), "no Han anywhere in a vi book"
    assert "tgt-zh" not in joined and "zh-Hant" not in joined
    assert any("tgt-vi" in text for text in files.values())
    opf = next(t for n, t in files.items() if n.endswith(".opf"))
    assert "<dc:language>vi</dc:language>" in opf
    nav = next(t for n, t in files.items() if n.endswith("nav.xhtml"))
    assert 'lang="vi"' in nav and "Song ngữ Anh–Việt" in nav and "Mục lục" in nav
    assert "Trang tiêu đề" in nav
    assert bilingual_coverage_audit.audit(out, out, profile=VI)[0] is True


def test_assemble_rejects_an_unregistered_target_lang(tmp_path):
    book = _make_vi_book(tmp_path, "vn")
    with pytest.raises(ValueError, match="vn"):
        assemble.assemble(book, tmp_path / "out.epub")
    assert not (tmp_path / "out.epub").exists()


def test_assemble_without_state_still_means_zh_tw(tmp_path):
    book = _make_vi_book(tmp_path, None)
    (book / "chapters" / "ch_01_translation.txt").write_text("第一章\n\n你好嗎？\n\n世界。", encoding="utf-8")
    (book / "translations_extra.json").write_text(
        json.dumps({"nav_overrides": {"title": "書名頁", "x": "第一章"}}, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out.epub"
    assemble.assemble(book, out)
    joined = "\n".join(_epub_text(out).values())
    assert "tgt-zh" in joined and "zh-Hant" in joined


def test_audit_suite_rejects_an_unregistered_target_lang_before_running_anything(tmp_path):
    book = tmp_path / "book"
    book.mkdir()
    (book / "state.json").write_text(json.dumps({"target_lang": "vn"}), encoding="utf-8")
    with pytest.raises(ValueError, match="vn"):
        audit_suite.run_all(tmp_path / "missing_source.epub", tmp_path / "missing_output.epub", book)


def test_audit_suite_without_state_means_zh_tw(tmp_path):
    book = tmp_path / "book"
    book.mkdir()
    assert audit_suite._profile_for_book(book).code == "zh-tw"
    (book / "state.json").write_text(json.dumps({"target_lang": "vi"}), encoding="utf-8")
    assert audit_suite._profile_for_book(book).code == "vi"
