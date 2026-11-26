"""Warn about table cells that extraction skipped and nobody dealt with (BUG-012).

``extract_epub`` does not read text that sits directly in a ``<td>`` or ``<th>``, so such cells are never
translated and no other audit sees them. This audit lists them at the audit gate. It is WARN only: leaving a
cell in the source language on purpose is allowed. A cell counts as dealt with when its text is in
``translations/source_only.json`` or when the output has a translated row (class ``tgt``) right after its row,
which is what the by-hand method in SKILL.md Step 7 produces.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
import extract_epub  # type: ignore  # noqa: E402

try:  # pragma: no cover - import mode depends on caller
    from .audit_result import AuditResult
    from .bilingual_coverage_audit import _source_only_exceptions
    from .epub_reader import EPUBReader
except ImportError:  # pragma: no cover
    from audit_result import AuditResult  # type: ignore
    from bilingual_coverage_audit import _source_only_exceptions  # type: ignore
    from epub_reader import EPUBReader  # type: ignore

SHOWN_CELLS = 3
HINT = "Decide: translate them by hand after assembly, list them in source_only.json, or ignore (BUG-012)."


def run(output: Path, book_dir: Path) -> AuditResult:
    not_checked = _not_checked_reason(book_dir)
    skipped: list[tuple[str, str, list[str]]] = []
    if not_checked is None:
        skipped, not_checked = _skipped_cells(Path(book_dir))
    if not_checked is not None:
        return _warn([f"not checked: {not_checked}"], {"checked": False})

    handled = _handled_cells(Path(output)) if skipped else None
    if skipped and handled is None:
        return _warn([f"not checked: cannot read the output EPUB {output}"], {"checked": False})

    warnings: list[str] = []
    unhandled = 0
    for item_id, href, cells in skipped:
        left = [c for c in cells if c not in (handled or set())]
        if not left:
            continue
        unhandled += len(left)
        shown = "; ".join(repr(c[:40]) for c in left[:SHOWN_CELLS])
        more = f" (and {len(left) - SHOWN_CELLS} more)" if len(left) > SHOWN_CELLS else ""
        warnings.append(f"{item_id} ({href}): {len(left)} table cell(s) not translated: {shown}{more}")
    details = {"checked": True, "unhandled": unhandled, "items_with_skipped_cells": len(skipped)}
    if not warnings:
        return AuditResult(name="table_text", status="pass", failures=[], details=details)
    warnings.append(HINT)
    return AuditResult(name="table_text", status="warn", failures=[], warnings=warnings, details=details)


def _warn(warnings: list[str], details: dict) -> AuditResult:
    return AuditResult(name="table_text", status="warn", failures=[], warnings=warnings, details=details)


def _not_checked_reason(book_dir: Path) -> str | None:
    if not (Path(book_dir) / "manifest.json").is_file():
        return f"no manifest.json in {book_dir}"
    return None


def _skipped_cells(book_dir: Path) -> tuple[list[tuple[str, str, list[str]]], str | None]:
    """(item id, href, skipped cell texts) for every translate item that has any, or a reason it cannot be known."""
    try:
        manifest = json.loads((book_dir / "manifest.json").read_text(encoding="utf-8"))
        spine = manifest["spine"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [], f"manifest.json is unreadable ({exc.__class__.__name__})"
    found: list[tuple[str, str, list[str]]] = []
    for entry in spine:
        if entry.get("output_strategy") != "translate":
            continue
        href = str(entry.get("href") or "")
        path = book_dir / href
        try:
            html = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return [], f"chapter file {href or '(no href)'} of {entry.get('id')} is missing"
        cells = list(dict.fromkeys(extract_epub.skipped_table_text(html)))
        if cells:
            found.append((str(entry.get("id")), href, cells))
    return found, None


def _handled_cells(output: Path) -> set[str] | None:
    """Cell texts that are in source_only.json or whose row is followed by a ``tgt`` row; None if unreadable."""
    try:
        with EPUBReader(output) as reader:
            handled = set(_source_only_exceptions(reader))
            for path in reader.spine_xhtml_paths():
                soup = BeautifulSoup(reader.read(path), "html.parser", from_encoding="utf-8")
                for cell in soup.find_all(["td", "th"]):
                    row = cell.find_parent("tr")
                    nxt = row.find_next_sibling("tr") if row is not None else None
                    if nxt is not None and "tgt" in (nxt.get("class") or []):
                        handled.add(re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip())
            return handled
    except (OSError, ValueError, KeyError):
        return None
