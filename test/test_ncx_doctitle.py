"""BUG-008: the NCX docTitle carries the profile's bilingual edition label, like nav.xhtml's <title>.

Ordinary test-first. The zh-tw golden cases have no docTitle in their NCX input, so they stay as derived
from the oracle; this only changes what a real NCX that has a docTitle looks like.
"""
from __future__ import annotations

from bs4 import BeautifulSoup

from scripts import nav_builder
from scripts.lang_profile import get_profile

NCX = """<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <docTitle><text>{title}</text></docTitle>
  <navMap>
    <navPoint id="n1" playOrder="1">
      <navLabel><text>Chapter 1</text></navLabel>
      <content src="xhtml/chapter1.xhtml"/>
    </navPoint>
  </navMap>
</ncx>
"""

ENTRIES = [{
    "id": "item_001",
    "original_path": "OPS/xhtml/chapter1.xhtml",
    "first_heading": "Chapter 1",
    "output_strategy": "translate",
    "original_idref": "chap1",
    "_translations_extra": {"nav_overrides": {"chap1": "Chương 1"}},
}]


def _doc_title(xml: str) -> str:
    return BeautifulSoup(xml, "xml").find("docTitle").find("text").get_text()


def test_doctitle_gets_the_profile_edition_label_for_vi():
    out = nav_builder.patch_toc_ncx(NCX.format(title="System Design Interview"), ENTRIES, get_profile("vi"))
    assert _doc_title(out) == "System Design Interview ｜ Song ngữ Anh–Việt"


def test_doctitle_uses_the_zh_tw_label_for_zh_tw():
    out = nav_builder.patch_toc_ncx(NCX.format(title="Some Book"), ENTRIES, get_profile("zh-tw"))
    assert _doc_title(out) == "Some Book ｜ 中英對照"


def test_doctitle_label_is_not_added_twice():
    once = nav_builder.patch_toc_ncx(NCX.format(title="Some Book"), ENTRIES, get_profile("vi"))
    twice = nav_builder.patch_toc_ncx(once, ENTRIES, get_profile("vi"))
    assert _doc_title(twice) == "Some Book ｜ Song ngữ Anh–Việt"


def test_ncx_without_doctitle_is_unchanged_in_structure():
    xml = NCX.replace("  <docTitle><text>{title}</text></docTitle>\n", "")
    out = nav_builder.patch_toc_ncx(xml, ENTRIES, get_profile("vi"))
    assert BeautifulSoup(out, "xml").find("docTitle") is None
