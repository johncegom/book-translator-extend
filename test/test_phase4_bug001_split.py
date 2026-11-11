"""Phase 4.6 (BUG-001): spine files that pack several chapters are split at the TOC fragment targets.

Ordinary test-first on a synthetic EPUB (the real test book is copyrighted and never committed).
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts import assemble, extract_epub

CH = ["Alpha", "Bravo", "Charlie"]


@pytest.fixture(autouse=True)
def _small_threshold(monkeypatch):
    # The real threshold (60k characters) is far above these tiny synthetic chapters.
    monkeypatch.setattr(extract_epub, "_SPLIT_MIN_CHARS", 100)


def _para(tag: str, n: int) -> str:
    return f"{tag} paragraph {n} has enough words to count as real body prose for the extractor."


def _body_three_chapters(nested: bool = False) -> str:
    parts = []
    for i, name in enumerate(CH, start=1):
        parts.append(f'<h2 id="p{i}">{name} chapter</h2>')
        parts += [f"<p>{_para(name, k)}</p>" for k in (1, 2)]
    inner = "".join(parts)
    return f'<div id="wrap">{inner}</div>' if nested else inner


def _ncx(points: list[tuple[str, str]]) -> str:
    nav = "".join(
        f'<navPoint id="n{i}" playOrder="{i}"><navLabel><text>{label}</text></navLabel>'
        f'<content src="{src}"/></navPoint>' for i, (label, src) in enumerate(points, start=1))
    return ('<?xml version="1.0"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">'
            f"<navMap>{nav}</navMap></ncx>")


def make_epub(path: Path, *, points, nested=False, body=None) -> None:
    body = _body_three_chapters(nested) if body is None else body
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
                   '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
                   "</rootfiles></container>")
        z.writestr("OEBPS/content.opf",
                   '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id">'
                   '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Split Test</dc:title>'
                   '<dc:language>en</dc:language><dc:identifier id="id">x</dc:identifier></metadata><manifest>'
                   '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
                   '<item id="a" href="a.xhtml" media-type="application/xhtml+xml"/>'
                   '<item id="b" href="b.xhtml" media-type="application/xhtml+xml"/></manifest>'
                   '<spine toc="ncx"><itemref idref="a"/><itemref idref="b"/></spine></package>')
        z.writestr("OEBPS/toc.ncx", _ncx(points))
        z.writestr("OEBPS/a.xhtml",
                   '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>T</title></head>'
                   "<body><h1>Title page</h1><p>"
                   + _para("Title", 1) + "</p></body></html>")
        z.writestr("OEBPS/b.xhtml",
                   f'<html xmlns="http://www.w3.org/1999/xhtml"><head><title>B</title></head><body>{body}</body></html>')


THREE = [("Alpha", "b.xhtml#p1"), ("Bravo", "b.xhtml#p2"), ("Charlie", "b.xhtml#p3")]


def _extract(tmp_path: Path, name="book", **kw) -> tuple[Path, dict]:
    epub = tmp_path / f"{name}.epub"
    make_epub(epub, **kw)
    book = extract_epub.extract(epub, tmp_path / "out")
    return book, json.loads((book / "manifest.json").read_text(encoding="utf-8"))


def test_file_with_three_targets_becomes_three_items(tmp_path):
    book, m = _extract(tmp_path, points=THREE)
    spine = m["spine"]
    assert [e["id"] for e in spine] == ["item_001", "item_002", "item_003", "item_004"]
    parts = spine[1:]
    assert {e["original_path"] for e in parts} == {"OEBPS/b.xhtml"}
    assert [e["fragment_id"] for e in parts] == ["p1", "p2", "p3"]
    assert [e["first_heading"] for e in parts] == ["Alpha chapter", "Bravo chapter", "Charlie chapter"]
    for e, name in zip(parts, CH):
        text = (book / e["href"]).read_text(encoding="utf-8")
        assert f"{name} paragraph 1" in text and f"{name} paragraph 2" in text
        assert all(other not in text for other in CH if other != name)
    assert "fragment_id" not in spine[0]


def test_segments_cover_the_whole_original_text(tmp_path):
    book, m = _extract(tmp_path, points=THREE)
    joined = "".join((book / e["href"]).read_text(encoding="utf-8") for e in m["spine"][1:])
    for name in CH:
        assert joined.count(f"{name} paragraph 1") == 1 and joined.count(f"{name} paragraph 2") == 1


@pytest.mark.parametrize("points", [
    [("Alpha", "b.xhtml")],                                  # no fragments
    [("Alpha", "b.xhtml#p1")],                               # a single target
    [("Alpha", "b.xhtml#p1"), ("Again", "b.xhtml#p1")],      # the same target twice
    [("Alpha", "b.xhtml#nothere"), ("B", "b.xhtml#missing")],  # targets that do not exist
])
def test_no_split_without_two_usable_targets(tmp_path, points):
    _book, m = _extract(tmp_path, points=points)
    assert [e["id"] for e in m["spine"]] == ["item_001", "item_002"]
    assert all("fragment_id" not in e for e in m["spine"])


def test_no_split_when_all_targets_sit_inside_one_wrapper(tmp_path):
    _book, m = _extract(tmp_path, points=THREE, nested=True)
    assert [e["id"] for e in m["spine"]] == ["item_001", "item_002"]
    assert all("fragment_id" not in e for e in m["spine"])


# --- assemble -------------------------------------------------------------------------

def _translate_all(book: Path, m: dict) -> None:
    state = {"book": "x", "target_lang": "vi", "chapters": {}}
    nav = {}
    for e in m["spine"]:
        if e["output_strategy"] == "translate":
            html = (book / e["href"]).read_text(encoding="utf-8")
            import re
            paras = re.findall(r"<(?:p|h2)[^>]*>(.*?)</(?:p|h2)>", html)
            (book / "chapters" / f"{e['id']}_translation.txt").write_text(
                "\n\n".join(f"Bản dịch: {p}" for p in paras), encoding="utf-8")
            state["chapters"][e["id"]] = {"output_strategy": "translate", "status": "done"}
        nav[e["original_idref"]] = f"Chương {e['id']}"
    (book / "state.json").write_text(json.dumps(state), encoding="utf-8")
    (book / "translations_extra.json").write_text(json.dumps({"nav_overrides": nav}), encoding="utf-8")


def test_assemble_keeps_one_original_file_with_all_segments_in_order(tmp_path):
    book, m = _extract(tmp_path, points=THREE)
    _translate_all(book, m)
    out = tmp_path / "out.epub"
    assemble.assemble(book, out)
    with zipfile.ZipFile(out) as z:
        b = z.read("OEBPS/b.xhtml").decode("utf-8")
        assert [n for n in z.namelist() if n.endswith("b.xhtml")] == ["OEBPS/b.xhtml"]
    positions = [b.index(f"{n} paragraph 1") for n in CH]
    assert positions == sorted(positions)
    assert b.count("<head>") == 1 and b.count("<body") == 1
    assert b.count("Bản dịch: ") >= 6


def test_nav_links_to_the_fragments(tmp_path):
    book, m = _extract(tmp_path, points=THREE)
    _translate_all(book, m)
    out = tmp_path / "out.epub"
    assemble.assemble(book, out)
    with zipfile.ZipFile(out) as z:
        blob = "".join(z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith((".ncx", "nav.xhtml")))
    for frag in ("p1", "p2", "p3"):
        assert f"b.xhtml#{frag}" in blob


def test_a_file_below_the_size_threshold_is_not_split(tmp_path, monkeypatch):
    monkeypatch.setattr(extract_epub, "_SPLIT_MIN_CHARS", 100_000)
    _book, m = _extract(tmp_path, points=THREE)
    assert [e["id"] for e in m["spine"]] == ["item_001", "item_002"]
    assert all("fragment_id" not in e for e in m["spine"])


def test_default_threshold_keeps_ordinary_chapter_files_whole():
    import re
    source = (Path(extract_epub.__file__)).read_text(encoding="utf-8")
    default = int(re.search(r"^_SPLIT_MIN_CHARS = (\d+)$", source, re.M).group(1))
    assert default >= 50_000      # Alice's largest file is about 30k characters
