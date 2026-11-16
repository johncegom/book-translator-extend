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


def _epub_with(src_html: str, tgt: str) -> zipfile.ZipFile:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("ch.xhtml", f'<html><body><p class="src">{src_html}</p><p class="tgt tgt-vi">{tgt}</p></body></html>')
    return zipfile.ZipFile(io.BytesIO(buf.getvalue()))


def _lost(z: zipfile.ZipFile) -> list[str]:
    return [t for s, t in g._number_pairs(z) if g._number_tokens(s) - g._number_tokens(t)]


def test_n1_ignores_an_endnote_marker_stuck_to_a_figure():
    # BUG-019: the source is "$28,650." then a superscript link to endnote 10, flattened by get_text to "28,650.10"
    src = 'The average cumulative debt in 2017 is $28,650.<a href="n.xhtml#e9"><sup class="endnote">10</sup></a> For students who pursue an MBA it is $66,300.<a href="n.xhtml#e10"><sup class="endnote">11</sup></a>'
    tgt = "Khoản nợ tích lũy trung bình năm 2017 là 28.650 đô la. 10 Với người học MBA là 66.300 đô la. 11"
    assert _lost(_epub_with(src, tgt)) == []


def test_n1_compares_decimals_in_either_notation():
    src = "If you save $0.50 on each T-shirt, you save $500 on every 1,000 T-shirts you make over a year."
    tgt = "Nếu bạn tiết kiệm 0,5 đô la trên mỗi áo thun, bạn tiết kiệm 500 đô la cho mỗi 1.000 chiếc áo làm ra trong một năm."
    assert _lost(_epub_with(src, tgt)) == []
    # a thousands figure written either way, and a decimal with a thousands part
    assert g._number_tokens("1,234.56 and 2,750") == g._number_tokens("1.234,56 và 2.750")


def test_n1_still_reports_a_number_that_is_really_missing():
    src = "Sales reached 2,750 units in 2019, up from the 1,980 units of the year before it, a clear gain."
    tgt = "Doanh số đạt 2.750 đơn vị năm 2019, tăng so với năm trước đó, một mức tăng rõ rệt."
    assert len(_lost(_epub_with(src, tgt))) == 1


def test_sample_pairs_ignores_glossary_terms_inside_quoted_titles(tmp_path):
    import json
    title = "For an example of how I do this, see “Diagramming a Value Stream/Flowcharting a System” on my website."
    plain = "A Value Stream is the path a product takes, and a quoted “value stream” here is a term, not a title."
    tgt = "Đây là bản dịch đủ dài để vượt ngưỡng năm mươi ký tự của mẫu chấm."
    body = "".join(f'<p class="src">{s}</p><p class="tgt tgt-vi">{tgt}</p>' for s in (title, plain))
    epub = tmp_path / "o.epub"
    with zipfile.ZipFile(epub, "w") as z:
        z.writestr("ch.xhtml", f"<html><body>{body}</body></html>")
    (tmp_path / "glossary.json").write_text(json.dumps({"terms": {"Value Stream": "Chuỗi giá trị"}}), encoding="utf-8")
    by_src = {p["src"]: p["glossary_terms"] for p in g.sample_pairs(epub, tmp_path, n=5)}
    assert by_src[title] == {}
    assert by_src[plain] == {"Value Stream": "Chuỗi giá trị"}


def test_strip_quoted_titles_only_removes_title_case_phrases():
    assert g._strip_quoted_titles("see “Diagramming a Value Stream/Flowcharting a System” now") == "see  now"
    assert g._strip_quoted_titles('see "The Pomodoro Technique," by Cirillo') == "see  by Cirillo"
    # two words, or a lowercase phrase, is a term in quotes, not a title
    assert g._strip_quoted_titles("a “slot machine” and “One Armed”") == "a “slot machine” and “One Armed”"


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
