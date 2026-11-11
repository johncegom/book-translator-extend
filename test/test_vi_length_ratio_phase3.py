"""Phase 3 (3.6): per-register min_length_ratio for vi, from the measurements in
docs/tasks/03-detector-audits/TASK.md ("3.2 results", "3.6 Advise outcome"). Ordinary test-first."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts import translation_quality_audit
from scripts.lang_profile import get_profile

VI = get_profile("vi")
ASSETS = Path(__file__).resolve().parent.parent / "assets"
VI_REGISTERS = json.loads((ASSETS / "register_hints.vi.json").read_text(encoding="utf-8"))["registers"]

SRC = ("The Embarcadero Freeway had stretched more than a mile along the waterfront. It blocked views of the bay. "
       "Nobody expected it to come down.")
FULL = ("Embarcadero Freeway từng kéo dài hơn một dặm dọc bờ sông. Nó che mất tầm nhìn ra vịnh. "
        "Không ai nghĩ rằng nó sẽ bị dỡ bỏ.")
HALF = "Embarcadero Freeway từng kéo dài hơn một dặm dọc bờ sông."  # about 0.45 of the source


def _write_epub(path: Path, body: str) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml",
                   '<?xml version="1.0"?><container version="1.0" '
                   'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
                   '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
                   "</rootfiles></container>")
        z.writestr("OEBPS/content.opf",
                   '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0"><manifest>'
                   '<item id="c1" href="xhtml/c1.xhtml" media-type="application/xhtml+xml"/></manifest>'
                   '<spine><itemref idref="c1"/></spine></package>')
        z.writestr("OEBPS/xhtml/c1.xhtml", f"<html><body>{body}</body></html>")


@pytest.mark.parametrize("register", VI_REGISTERS, ids=lambda r: r["id"])
def test_every_vi_register_has_the_provisional_ratio(register):
    assert register["min_length_ratio"] == 0.60


@pytest.mark.parametrize("phrase", ["storyteller cadence", "practical business memoir", "scholarly precision"])
def test_book_dir_lookup_returns_the_vi_ratio_for_each_registered_phrase(tmp_path, phrase):
    (tmp_path / "glossary.json").write_text(json.dumps({"style_anchor": {"register": phrase}}), encoding="utf-8")
    assert translation_quality_audit._min_length_ratio_from_book_dir(tmp_path, profile=VI) == 0.60


def test_the_fallback_for_an_unmatched_register_is_the_vi_default(tmp_path):
    # BUG-002 fixed in Phase 4 (was pinned at 0.22 here).
    (tmp_path / "glossary.json").write_text(json.dumps({"style_anchor": {"register": "zzz unknown"}}), encoding="utf-8")
    assert translation_quality_audit._min_length_ratio_from_book_dir(tmp_path, profile=VI) == 0.60


def test_truncated_vi_paragraph_fails_and_a_full_one_passes(tmp_path):
    ratio = 0.60
    assert len(HALF) < ratio * len(SRC) <= len(FULL)
    bad, good = tmp_path / "bad.epub", tmp_path / "good.epub"
    _write_epub(bad, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{HALF}</p>')
    _write_epub(good, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{FULL}</p>')
    ok, failures = translation_quality_audit.audit(bad, min_length_ratio=ratio, profile=VI)
    assert ok is False and any("target too short" in f for f in failures)
    ok, failures = translation_quality_audit.audit(good, min_length_ratio=ratio, profile=VI)
    assert ok is True, failures
