"""BUG-012: table text is not extracted, so tell the user at extract time.

Ordinary test-first (new behaviour, no zh-tw oracle). The warning is output only; manifest.json and the
extracted chapters are unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

from ebooklib import epub

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import extract_epub  # type: ignore  # noqa: E402

PROSE = "<p>" + "A plain paragraph of body text that is long enough to count. " * 6 + "</p>"
TABLE = (
    '<table class="simplelist"><tr><td>He that takes away the sugar,</td></tr>'
    "<tr><td>Shall be called a dirty</td></tr></table>"
)


def test_skipped_table_text_lists_cells_that_are_not_paragraphs():
    html = f"<html><body>{PROSE}{TABLE}</body></html>"
    assert extract_epub.skipped_table_text(html) == [
        "He that takes away the sugar,",
        "Shall be called a dirty",
    ]


def test_skipped_table_text_is_empty_for_plain_prose():
    assert extract_epub.skipped_table_text(f"<html><body>{PROSE}</body></html>") == []


def _make_epub(path: Path, chapters: dict[str, str]) -> None:
    book = epub.EpubBook()
    book.set_identifier("t")
    book.set_title("T")
    book.set_language("en")
    items = []
    for name, body in chapters.items():
        c = epub.EpubHtml(title=name, file_name=f"{name}.xhtml", lang="en")
        c.content = f"<html><body><h1>{name}</h1>{body}</body></html>"
        book.add_item(c)
        items.append(c)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", *items]
    epub.write_epub(str(path), book)


def test_extract_warns_on_stderr_and_names_the_item(tmp_path: Path, capsys):
    src = tmp_path / "book.epub"
    _make_epub(src, {"one": PROSE, "two": PROSE + TABLE})
    extract_epub.extract(src, tmp_path / "out")
    err = capsys.readouterr().err
    assert "table" in err.lower()
    assert "He that takes away the sugar," in err
    assert "one.xhtml" not in err


def test_extract_prints_no_warning_without_tables(tmp_path: Path, capsys):
    src = tmp_path / "book.epub"
    _make_epub(src, {"one": PROSE})
    extract_epub.extract(src, tmp_path / "out")
    assert capsys.readouterr().err == ""
