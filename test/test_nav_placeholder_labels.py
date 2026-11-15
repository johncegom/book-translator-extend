"""Phase 8 / BUG-017: a page with no heading shows only its target label, not "(untitled) | label".

Expected values for the unchanged cases come from the ORACLE record (main at bb0eb35),
test/golden/golden_nav_label.json. The two placeholder cases changed on purpose (DECISION-018, all languages).
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts import nav_builder
from scripts.lang_profile import get_profile

GOLDEN = json.loads((Path(__file__).parent / "golden" / "golden_nav_label.json").read_text(encoding="utf8"))


def _entry(first, override=None, idref="x"):
    e = {"id": "i1", "first_heading": first, "output_strategy": "translate", "original_idref": idref}
    if override:
        e["_translations_extra"] = {"nav_overrides": {idref: override}}
    return e


def test_unchanged_cases_equal_the_oracle_record():
    cases = {
        "normal_heading": _entry("Chapter One", idref="a"),
        "structural_page": _entry("Contents", idref="b"),
        "placeholder_without_label": _entry("(untitled)", idref="e"),
        "empty_heading_uses_id": {"id": "i6", "first_heading": "", "output_strategy": "translate", "original_idref": "f"},
    }
    for name, entry in cases.items():
        assert nav_builder._nav_display_label(entry) == GOLDEN[name], name


def test_placeholder_with_label_shows_only_the_label_zh_tw():
    assert nav_builder._nav_display_label(_entry("(untitled)", "標籤")) == "標籤"
    assert nav_builder._nav_display_label(_entry("Untitled", "標籤")) == "標籤"


def test_placeholder_with_label_shows_only_the_label_vi():
    vi = get_profile("vi")
    assert nav_builder._nav_display_label(_entry("(untitled)", "Phần I"), None, vi) == "Phần I"
    assert nav_builder._nav_display_label(_entry("Chapter One", "Chương Một"), None, vi) == "Chapter One ｜ Chương Một"


def test_nav_xhtml_has_no_untitled_text():
    manifest = {"title": "T", "book_stem": "t"}
    entries = [dict(_entry("(untitled)", "Phần I"), original_path="OEBPS/c1.xhtml")]
    nav = nav_builder.build_nav_xhtml(manifest, entries, "OEBPS/nav.xhtml", "OEBPS", profile=get_profile("vi"))
    assert "Phần I" in nav and "untitled" not in nav.lower()
