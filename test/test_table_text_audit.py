"""Phase 14 / BUG-012: the audit gate warns about table cells that extraction skipped.

Ordinary test-first (new behaviour, no oracle). The audit is WARN only: it never fails the run.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import audit_suite  # type: ignore  # noqa: E402
import table_text_audit  # type: ignore  # noqa: E402
from audit_result import AuditResult  # type: ignore  # noqa: E402

VERSE = (
    '<table class="simplelist"><tr><td>He that takes away the sugar,</td></tr>'
    "<tr><td>Shall be called a dirty</td></tr></table>"
)
PROSE = "<p>A plain paragraph.</p>"


def _page(body: str) -> str:
    return f"<html><body>{body}</body></html>"


def _book(tmp_path: Path, chapters: dict[str, str], strategies: dict[str, str] | None = None) -> Path:
    """A book folder with manifest.json and chapters/<id>.html."""
    book = tmp_path / "book"
    (book / "chapters").mkdir(parents=True)
    spine = []
    for item_id, html in chapters.items():
        (book / "chapters" / f"{item_id}.html").write_text(html, encoding="utf-8")
        spine.append({"id": item_id, "href": f"chapters/{item_id}.html", "src_href": f"OEBPS/{item_id}.xhtml",
                      "output_strategy": (strategies or {}).get(item_id, "translate")})
    (book / "manifest.json").write_text(json.dumps({"spine": spine}), encoding="utf-8")
    return book


def _output(tmp_path: Path, body: str = PROSE, source_only: list[dict] | None = None) -> Path:
    path = tmp_path / "out.epub"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" '
                   'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile '
                   'full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr("OEBPS/content.opf", '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0">'
                   '<manifest><item id="c1" href="xhtml/c1.xhtml" media-type="application/xhtml+xml"/></manifest>'
                   '<spine><itemref idref="c1"/></spine></package>')
        z.writestr("OEBPS/xhtml/c1.xhtml", _page(body))
        if source_only is not None:
            z.writestr("OEBPS/translations/source_only.json", json.dumps(source_only))
    return path


def test_unhandled_cells_warn_and_name_the_item_and_cell(tmp_path):
    book = _book(tmp_path, {"item_001": _page(PROSE), "item_002": _page(PROSE + VERSE)})
    result = table_text_audit.run(_output(tmp_path), book)
    assert result.name == "table_text"
    assert result.status == "warn" and not result.failures
    text = "\n".join(result.warnings)
    assert "item_002" in text and "He that takes away the sugar," in text
    assert "item_001" not in text
    assert result.details["unhandled"] == 2


def test_cells_listed_in_source_only_pass(tmp_path):
    book = _book(tmp_path, {"item_001": _page(PROSE + VERSE)})
    listed = [{"src_text": "He that takes away the sugar,", "reason": "left in English on purpose"},
              {"src_text": "Shall be called a dirty", "reason": "left in English on purpose"}]
    result = table_text_audit.run(_output(tmp_path, source_only=listed), book)
    assert result.status == "pass" and not result.warnings


def test_cells_followed_by_a_translated_row_pass(tmp_path):
    book = _book(tmp_path, {"item_001": _page(PROSE + VERSE)})
    body = (
        '<table><tr><td>He that takes away the sugar,</td></tr>'
        '<tr class="tgt tgt-vi"><td class="tgt tgt-vi">Kẻ nào bỏ gói đường,</td></tr>'
        '<tr><td>Shall be called a dirty</td></tr>'
        '<tr class="tgt tgt-vi"><td class="tgt tgt-vi">Sẽ bị gọi là bẩn thỉu</td></tr></table>'
    )
    result = table_text_audit.run(_output(tmp_path, body), book)
    assert result.status == "pass" and not result.warnings


def test_only_the_unhandled_cell_is_named(tmp_path):
    book = _book(tmp_path, {"item_001": _page(VERSE)})
    body = ('<table><tr><td>He that takes away the sugar,</td></tr>'
            '<tr class="tgt"><td class="tgt">Kẻ nào bỏ gói đường,</td></tr>'
            '<tr><td>Shall be called a dirty</td></tr></table>')
    result = table_text_audit.run(_output(tmp_path, body), book)
    assert result.status == "warn" and result.details["unhandled"] == 1
    text = "\n".join(result.warnings)
    assert "Shall be called a dirty" in text and "He that takes away" not in text


def test_a_book_with_no_tables_passes(tmp_path):
    result = table_text_audit.run(_output(tmp_path), _book(tmp_path, {"item_001": _page(PROSE)}))
    assert result.status == "pass" and not result.warnings


def test_cells_that_hold_paragraphs_are_already_extracted_so_they_pass(tmp_path):
    html = _page("<table><tr><td><p>Already a paragraph of its own.</p></td></tr></table>")
    result = table_text_audit.run(_output(tmp_path), _book(tmp_path, {"item_001": html}))
    assert result.status == "pass"


def test_a_table_on_a_source_only_item_is_not_checked(tmp_path):
    book = _book(tmp_path, {"item_001": _page(VERSE)}, {"item_001": "source_only"})
    assert table_text_audit.run(_output(tmp_path), book).status == "pass"


def test_missing_manifest_warns_not_checked(tmp_path):
    book = tmp_path / "empty"
    book.mkdir()
    result = table_text_audit.run(_output(tmp_path), book)
    assert result.status == "warn" and "not checked" in result.warnings[0]


def test_missing_chapter_file_warns_not_checked(tmp_path):
    book = _book(tmp_path, {"item_001": _page(PROSE)})
    (book / "chapters" / "item_001.html").unlink()
    result = table_text_audit.run(_output(tmp_path), book)
    assert result.status == "warn" and "not checked" in "\n".join(result.warnings)


def test_run_all_appends_the_audit_last_and_the_summary_counts_it(tmp_path, monkeypatch):
    for module in (audit_suite.structural_audit, audit_suite.bilingual_coverage_audit,
                   audit_suite.translation_quality_audit, audit_suite.href_resolve_audit):
        name = module.__name__.split(".")[-1]
        monkeypatch.setattr(module, "run", lambda *a, _n=name, **k: AuditResult(name=_n, status="pass", failures=[]))
    book = _book(tmp_path, {"item_001": _page(PROSE + VERSE)})
    results = audit_suite.run_all(tmp_path / "src.epub", _output(tmp_path), book)
    assert [r.name for r in results][-1] == "table_text" and len(results) == 5
    assert audit_suite.format_summary(results).splitlines()[0] == "4 PASS / 1 WARN / 0 FAIL"
    assert audit_suite.all_passed(results) is True
