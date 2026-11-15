"""Phase 7 / BUG-016: in-chapter toc.ncx entries get the target text when the profile opts in.

zh-tw: the expected output is the ORACLE record (main at bb0eb35), test/golden/golden_ncx_sections.json.
vi: no oracle exists, so ordinary test-first on the synthetic fixture.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from scripts import nav_builder
from scripts.lang_profile import get_profile
from test.golden.ncx_fixture import CHAPTER_HTML, ENTRIES, NCX

GOLDEN = json.loads((Path(__file__).parent / "golden" / "golden_ncx_sections.json").read_text(encoding="utf8"))


def _labels(xml: str) -> dict[str, str]:
    soup = BeautifulSoup(xml, "xml")
    return {p["id"]: p.find("navLabel", recursive=False).get_text() for p in soup.find_all("navPoint")}


def test_profile_flag_is_explicit_on_both_profiles():
    assert get_profile("zh-tw").ncx_section_labels is False
    assert get_profile("vi").ncx_section_labels is True


def test_zh_tw_matches_oracle_without_chapter_html():
    assert nav_builder.patch_toc_ncx(NCX, ENTRIES, get_profile("zh-tw")) == GOLDEN["zh-tw"]


def test_zh_tw_matches_oracle_even_when_chapter_html_is_passed():
    out = nav_builder.patch_toc_ncx(NCX, ENTRIES, get_profile("zh-tw"), chapter_html=CHAPTER_HTML)
    assert out == GOLDEN["zh-tw"]


def test_vi_in_chapter_entries_become_bilingual():
    out = nav_builder.patch_toc_ncx(NCX, ENTRIES, get_profile("vi"), chapter_html=CHAPTER_HTML)
    labels = _labels(out)
    assert labels["n2"] == "SLACK ｜ KHOẢNG ĐỆM"
    assert labels["n3"] == "Tunneling & Focus ｜ Hiệu ứng đường hầm & tập trung"


def test_vi_chapter_level_entries_are_unchanged_from_before():
    out = nav_builder.patch_toc_ncx(NCX, ENTRIES, get_profile("vi"), chapter_html=CHAPTER_HTML)
    labels = _labels(out)
    old = _labels(GOLDEN["zh-tw"])
    assert labels["n1"] == old["n1"] == "Chapter 1 ｜ Chương 1"
    assert labels["n6"] == old["n6"]


def test_vi_entry_without_tgt_sibling_or_with_identical_text_is_left_alone():
    labels = _labels(nav_builder.patch_toc_ncx(NCX, ENTRIES, get_profile("vi"), chapter_html=CHAPTER_HTML))
    assert labels["n4"] == "NO SIBLING"
    assert labels["n5"] == "Same Text"


def test_vi_missing_anchor_or_missing_file_is_left_alone():
    out = nav_builder.patch_toc_ncx(NCX, ENTRIES, get_profile("vi"), chapter_html={"ch2.xhtml": CHAPTER_HTML["ch2.xhtml"]})
    assert _labels(out)["n2"] == "SLACK"


def test_vi_target_text_is_xml_escaped_in_output():
    html = {"ch1.xhtml": '<h5 id="h_slack">SLACK</h5><p class="tgt">A &lt;b&gt; &amp; C</p>'}
    out = nav_builder.patch_toc_ncx(NCX, ENTRIES, get_profile("vi"), chapter_html=html)
    assert "SLACK ｜ A &lt;b&gt; &amp; C" in out
    assert _labels(out)["n2"] == "SLACK ｜ A <b> & C"


def test_vi_flag_on_but_no_chapter_html_warns_and_keeps_old_output():
    with pytest.warns(UserWarning, match="chapter_html"):
        out = nav_builder.patch_toc_ncx(NCX, ENTRIES, get_profile("vi"))
    assert _labels(out)["n2"] == "SLACK"


def test_zh_tw_without_chapter_html_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        nav_builder.patch_toc_ncx(NCX, ENTRIES, get_profile("zh-tw"))
