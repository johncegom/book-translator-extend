"""Ground-truth derivation for the Phase 1 zh-tw language-profile refactor.

``compute()`` calls the zh-tw behaviour of the scripts under test and returns a
JSON-serialisable dict. ``golden_zh_tw.json`` holds the output of running it
against the ORACLE: main at commit bb0eb35 (pre-refactor). The characterization
test recomputes it on the current code and requires an exact match.

Re-derive (never hand-edit golden_zh_tw.json, never regenerate it from
refactored code):

    git worktree add ../bt-oracle bb0eb35
    cd ../bt-oracle
    python <repo>/test/golden/derive.py > <repo>/test/golden/golden_zh_tw.json

Not covered here, by design:
  * ``assemble.py:280`` local Han regex is inside a function; it is pinned by
    the frozen-book snapshot (docs/tasks/01-profile-zh-tw/frozen-fixture).
  * ollama/omlx prompts (out of scope, see TASK.md).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

HAN_SAMPLES = [
    "", "plain english", "譯文", "中", "㐀", "䶿", "一", "鿿", "〇", "。", "，",
    "ひらがなカタカナ", "한글", "豈", "\U00020000", "English ｜ 中文", "價格 价格", "后 後 余 餘",
    "鿿0", "ꀀ",
]
PARAGRAPH_SAMPLES = [
    "", "OK.", "Hi there", "x" * 49, "x" * 50,
    "The quick brown fox jumps over the lazy dog and keeps running far away.",
    "The quick brown fox 狐狸 jumps over the lazy dog and keeps running far away.",
    "1234567890" * 6, "https://example.com/some/long/path/that/goes/on/and/on/and/on", "12", "XIV",
    "node_module_name_01", "Chapter One",
    "這是一段已經翻譯成中文的段落，長度超過五十個字元，所以應該不需要再翻譯，對吧？" * 2,
]
TARGET_LANGS = ["zh-tw", "ZH-TW", "zh-TW", "zh-cn", "en", "ja", "ko", "fr", "", "vi"]
NAV_FIRSTS = [
    "Contents", "Cover", "Title Page", "Copyright", "Dedication", "PART I", "Notes", "About the Author",
    "Acknowledgments", "Introduction", "Footnote 3", "Footnote  12", "Praise for Some Book - a blurb",
    "Advance praise for X", "Also by Someone", "also by lower", "Chapter 1", "Unknown Heading",
    "CHAPTER I.\nDown the Rabbit-Hole", "Sign up now.", "Contents\n", "  Notes  ",
]
ASSEMBLE_REEXPORTS = [
    "STRUCTURAL_LABELS_ZH_TW", "CONTENTS_LINK_LABELS_ZH_TW", "_insert_bilingual", "_build_nav_xhtml",
    "_missing_nav_zh_warnings", "_source_ncx_path", "_patch_toc_ncx", "_promote_header_headings",
    "_bilingualize_contents_links", "_align_translations", "_text_nodes_for_bilingual", "_target_classes",
    "_add_class", "_fallback_translation", "_exact_translation_for_text", "_translations_extra_by_exact_text",
    "_ensure_han_translation", "_looks_like_identifier", "_clean_text", "_render_nav_item",
    "_nav_display_label", "_nav_zh_label", "_translations_extra_nav_overrides", "_nav_entry_by_filename",
    "_nav_label", "_contents_style", "_nav_path",
]


def _entries():
    extras = {
        "nav_overrides": {"idref_a": "覆寫標題"},
        "by_exact_text": {"Chapter 1": "第一章", "Unknown Heading": "未知標題"},
    }
    out = []
    for i, first in enumerate(NAV_FIRSTS):
        base = {"id": f"item_{i:03d}", "first_heading": first, "output_strategy": "translate",
                "original_idref": f"idref_{i}"}
        out.append(base)
        out.append({**base, "_translations_extra": extras})
    out.append({"id": "ov", "first_heading": "Anything", "output_strategy": "source_only",
                "original_idref": "idref_a", "_translations_extra": extras})
    out.append({"id": "nav_entry", "first_heading": "", "output_strategy": "nav", "original_idref": "x"})
    out.append({"id": "drop", "first_heading": "Dropped", "output_strategy": "drop_explicit"})
    return out


def _node(markup: str):
    from bs4 import BeautifulSoup

    return BeautifulSoup(markup, "html.parser").find()


def compute() -> dict:
    from scripts import assemble, bilingual_coverage_audit as bca, bilingual_rewriter as br
    from scripts import dispatch, nav_builder, paragraph_classification as pc
    from scripts import translation_quality_audit as tqa

    g: dict = {}

    g["tables"] = {
        "structural": br.STRUCTURAL_LABELS_ZH_TW,
        "contents": br.CONTENTS_LINK_LABELS_ZH_TW,
        "prefix": [list(p) for p in nav_builder._PREFIX_LABELS_ZH_TW],
        "aup_template": br._AUP_NOTE_HTML_TEMPLATE,
        "assemble_reexports": {n: hasattr(assemble, n) for n in ASSEMBLE_REEXPORTS},
    }

    g["target_long"] = {code: dispatch._target_long(code) for code in TARGET_LANGS}

    g["han"] = {
        s: {
            "pc_HAN_RE": bool(pc.HAN_RE.search(s)),
            "tqa_HAN_RE_count": len(tqa._HAN_RE.findall(s)),
            "tqa_contains_han": tqa._contains_han(s),
            "contains_simplified": tqa.contains_simplified_chinese(s),
            "offending_simplified": tqa._offending_simplified_chinese_chars(s),
        }
        for s in HAN_SAMPLES
    }

    g["paragraph"] = {s: pc.is_english_content(s) for s in PARAGRAPH_SAMPLES}
    reasons = {}
    paths = ["OEBPS/Bibliography.xhtml", "OEBPS/87_Index.xhtml", "OEBPS/index.xhtml", "OEBPS/index_split_006.html",
             "OEBPS/notes.xhtml", "OEBPS/notes_on_contributors.xhtml", "OEBPS/Copyright.xhtml",
             "OEBPS/chap01.xhtml", "OEBPS/endnotes_split_006.xhtml", "OEBPS/preferences.xhtml"]
    classes = ["", "bib", "bib-x", "index2", "ind01a", "body"]
    texts = ["Aagaard et al.", "12", "XIV", "https://example.com", "node_module_name_01", "——", "漢字",
             "Some English prose that is long enough to count for coverage."]
    for path in paths:
        for cls in classes:
            for text in texts:
                markup = f'<p class="{cls}">x</p>' if cls else "<p>x</p>"
                reasons[f"{path}|{cls}|{text}"] = pc.untranslated_reason(path, _node(markup), text)
    g["untranslated_reason"] = reasons

    entries = _entries()
    g["nav"] = {
        "zh_label": [nav_builder._nav_zh_label(e["first_heading"] or e["id"], e) for e in entries],
        "display_label": [nav_builder._nav_display_label(e) for e in entries],
        "heading_zh_label": [br._heading_zh_label(e["first_heading"] or e["id"], e) for e in entries],
        "missing_warnings": nav_builder.missing_nav_zh_warnings(entries),
        "contents_style": [nav_builder._contents_style(f) for f in NAV_FIRSTS],
    }

    src = (
        '<html><body><h2>CHAPTER I.<br/>Down</h2><p class="a">First paragraph long enough to translate here.</p>'
        "<p>Second paragraph.</p><ul><li>Item</li></ul><h3>Contents</h3></body></html>"
    )
    entry = {"id": "item_003", "output_strategy": "translate", "first_heading": "CHAPTER I. Down",
             "original_idref": "x", "role": "body"}
    rewriter: dict = {}
    for key, tr in {"full": ["第一章", "第一段。", "第二段。", "項目", "目錄"], "short": ["只有一段"], "none": []}.items():
        res = br.insert_bilingual(src, entry, tr)
        rewriter[key] = list(res) if isinstance(res, tuple) else res
    rewriter["aup"] = br.insert_bilingual(src, entry, [], chapter_status="aup_refused", aup_reason="政策 & <x>")
    rewriter["target_classes"] = br._target_classes(_node('<p class="src extra">x</p>'))
    rewriter["target_classes_unpaired"] = br._target_classes(_node('<p class="x">x</p>'), unpaired=True)
    g["rewriter"] = rewriter

    audit: dict = {
        "terminal_kind": {s: tqa._terminal_kind(s) for s in
                          ["Hi.", "Why?", "Wow!", "Note:", "a;", "你好。", "什麼？", "", "」", "x"]},
        "sentence_count": {s: tqa._sentence_punctuation_count(s) for s in ["A. B! C?", "。！？", "none", "…"]},
        "is_newly_in_scope": {str(n): bca._is_newly_in_scope("x" * n) for n in (0, 49, 50, 51)},
        "legacy_min_length": pc.LEGACY_ENGLISH_MIN_LENGTH,
        "banned_patterns": [str(p) for p in tqa.BANNED_PATTERNS],
        "title_margin": tqa._TITLE_RATIO_MARGIN,
        "short_margin": tqa._SHORT_SENTENCE_RATIO_MARGIN,
        "short_source_max": tqa._SHORT_SOURCE_MAX,
        "simplified_chars_sha256": hashlib.sha256(
            "".join(sorted(tqa.SIMPLIFIED_CHINESE_CHARS)).encode()).hexdigest(),
        "tgt_class": {
            c: [tqa._has_tgt_class(_node(f'<p class="{c}">x</p>')), bca._is_target(_node(f'<p class="{c}">x</p>'))]
            for c in ["tgt", "tgt-zh", "tgt-vi", "src", "tgt tgt-zh", ""]
        },
    }
    reviewable = {}
    for name in ["p", "li", "dd", "dt", "h2"]:
        for s_text in ["Title Without Stop", "A short sentence here.", "Why? Because.", "x" * 160, "Index term, 12"]:
            for ratio in (0.0, 0.1, 0.17, 0.19, 0.2, 0.21, 0.22, 0.3, 1.0):
                t_len = max(1, int(len(s_text) * ratio))
                for ending in ("", "。", "？"):
                    tgt = ("字" * t_len) + ending
                    for min_ratio in (0.22, 0.3):
                        reviewable[f"{name}|{s_text}|{ratio}|{ending}|{min_ratio}"] = (
                            tqa._looks_reviewable_short_target(
                                _node(f"<{name}>{s_text}</{name}>"), s_text, tgt, min_ratio))
    audit["reviewable_short_target"] = reviewable
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        ratios = {"no_dir": tqa._min_length_ratio_from_book_dir(None),
                  "no_glossary": tqa._min_length_ratio_from_book_dir(base)}
        for label, gl in {
            "empty": {},
            "register_literary": {"style_anchor": {"register": "literary plain prose"}},
            "register_unmatched": {"style_anchor": {"register": "no such register anywhere"}},
            "register_nonfiction": {"style_anchor": {"register": "non_fiction_narrative"}},
        }.items():
            d = base / label
            d.mkdir()
            (d / "glossary.json").write_text(json.dumps(gl), encoding="utf-8")
            try:
                ratios[label] = tqa._min_length_ratio_from_book_dir(d)
            except Exception as exc:  # pinned too: exception type only
                ratios[label] = f"raises {type(exc).__name__}"
        audit["min_length_ratio"] = ratios
    g["audit"] = audit

    g["prompt"] = {}
    glossary = {"terms": {"Alice": "愛麗絲"}, "chapter_titles_zh": {"CHAPTER I": "第一章"}}
    for lang in ["zh-tw", "zh-cn", "en"]:
        prompt = dispatch.build_subagent_prompt(
            chapter_label="item_003", book_title="Alice", target_lang=lang, glossary=glossary,
            style_sample="風格範例。", carryover="前情提要。", chapter_html="<p>Hello world, this is Alice.</p>",
        )
        g["prompt"][lang] = {"sha256": hashlib.sha256(prompt.encode()).hexdigest(), "text": prompt}
    return g


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(compute(), ensure_ascii=False, indent=1, sort_keys=True))
