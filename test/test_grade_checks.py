"""Helpers of scripts/grade_checks.py on a tiny synthetic EPUB (no book text)."""
from __future__ import annotations

import io
import zipfile

from scripts import grade_checks as g

NAV = '<html xmlns:epub="x"><head><title>T ｜ Song ngữ</title></head><body><nav epub:type="toc"><ol><li><a href="a">1 ｜ Chương 1: X</a></li><li><a href="b">(untitled) ｜ Trang</a></li></ol></nav></body></html>'
NCX = '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><docTitle><text>T ｜ Song ngữ</text></docTitle><navMap><navPoint id="n"><navLabel><text>SLACK ｜ KHOẢNG ĐỆM</text></navLabel><content src="ch.xhtml#h"/></navPoint></navMap></ncx>'
CH = '<html><body><h5 id="h" class="src">SLACK</h5><p class="tgt tgt-vi">KHOẢNG ĐỆM</p><p class="src">Alone</p><p>x</p></body></html>'


def _zip() -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("nav.xhtml", NAV)
        z.writestr("toc.ncx", NCX)
        z.writestr("ch.xhtml", CH)
    return zipfile.ZipFile(io.BytesIO(buf.getvalue()))


def test_numbers_reads_plain_and_chapter_labels():
    assert g._numbers(["1 ｜ Chương 1: X", "Chapter 2 ｜ Chương 2", "Notes ｜ Chú thích", "3 ｜ Chương 4"]) == [("1", "1"), ("2", "2"), ("3", "4")]


def test_nav_and_ncx_readers():
    z = _zip()
    title, labels = g._nav_entries(z)
    assert title.endswith("Song ngữ") and labels == ["1 ｜ Chương 1: X", "(untitled) ｜ Trang"]
    doc, points = g._ncx(z)
    assert doc.endswith("Song ngữ") and points == [("SLACK ｜ KHOẢNG ĐỆM", "ch.xhtml#h")]


def test_pairs_and_anchor_target():
    z = _zip()
    assert list(g._pairs(z)) == [("ch.xhtml", "SLACK", "KHOẢNG ĐỆM"), ("ch.xhtml", "Alone", None)]
    assert g._anchor_target(z, "xhtml/ch.xhtml", "h") == "KHOẢNG ĐỆM"
    assert g._anchor_target(z, "xhtml/ch.xhtml", "missing") is None


def test_sample_pairs_attaches_glossary_terms_and_is_stable(tmp_path):
    import json
    src = "The scarcity trap is a long enough source sentence to pass the fifty character floor."
    html = f'<html><body><p class="src">{src}</p><p class="tgt tgt-vi">Bẫy khan hiếm là một câu đủ dài để vượt ngưỡng năm mươi ký tự.</p></body></html>'
    epub = tmp_path / "o.epub"
    with zipfile.ZipFile(epub, "w") as z:
        z.writestr("ch.xhtml", html)
    (tmp_path / "glossary.json").write_text(json.dumps({"terms": {"scarcity trap": "bẫy khan hiếm", "tunnel": "đường hầm"}, "style_anchor": {"avoid": ["x"]}}), encoding="utf-8")
    first = g.sample_pairs(epub, tmp_path, n=5)
    assert first == g.sample_pairs(epub, tmp_path, n=5)
    assert len(first) == 1 and first[0]["glossary_terms"] == {"scarcity trap": "bẫy khan hiếm"}
    assert first[0]["style_avoid"] == ["x"]


def test_sample_pairs_skips_endnote_pages(tmp_path):
    import json

    def block(src, tgt):
        return f'<p class="src">{src}</p><p class="tgt tgt-vi">{tgt}</p>'

    body = block("This is an ordinary body paragraph that is long enough for the sample floor of fifty.", "Đây là một đoạn thân bài bình thường đủ dài để vào mẫu.")
    notes = "".join(
        block(f"{n} some cited work: A. Author, Title of the Work, Journal of Things 7, no. 1 (2002): 1-10.", f"{n} một công trình được trích : A. Author, Title of the Work, Journal of Things 7, no. 1 (2002): 1-10.")
        for n in (4, 17, 23, 31)
    )
    epub = tmp_path / "o.epub"
    with zipfile.ZipFile(epub, "w") as z:
        z.writestr("body.xhtml", f"<html><body>{body}</body></html>")
        z.writestr("notes.xhtml", f"<html><body>{notes}</body></html>")
    (tmp_path / "glossary.json").write_text(json.dumps({"terms": {}}), encoding="utf-8")
    files = {p["file"] for p in g.sample_pairs(epub, tmp_path, n=20)}
    assert files == {"body.xhtml"}


def test_e1_accepts_a_bare_nav_overrides_label_but_not_a_bare_english_one():
    labels = {"Mục lục"}
    overrides = {"Phần I"}
    assert g.label_has_target("Phần I", labels, overrides)
    assert g.label_has_target("Mục lục", labels, overrides)
    assert g.label_has_target("Chapter ｜ Chương", labels, overrides)
    assert not g.label_has_target("Dedication", labels, overrides)
    assert not g.label_has_target("Chapter ｜ ", labels, overrides)
