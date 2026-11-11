"""Phase 4: BUG-003 (standalone quality-audit CLI ignores the book's profile).

Ordinary test-first (no external oracle). BUG-002 tests are added after its Advise call.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts import translation_quality_audit

SRC = "The restaurant owner welcomed every guest at the door and showed them to a quiet table by the window."
TGT_VI = "Chủ nhà hàng chào đón mọi vị khách ở cửa và dẫn họ đến một chiếc bàn yên tĩnh bên cửa sổ."


def _epub(path: Path, body: str) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container version="1.0" '
            'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
            '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            "</rootfiles></container>",
        )
        z.writestr(
            "OEBPS/content.opf",
            '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0"><manifest>'
            '<item id="c1" href="xhtml/c1.xhtml" media-type="application/xhtml+xml"/></manifest>'
            '<spine><itemref idref="c1"/></spine></package>',
        )
        z.writestr("OEBPS/xhtml/c1.xhtml", f"<html><body>{body}</body></html>")


# About 40% of the source length: passes the zh-tw default (0.22), fails the vi register ratio (0.60).
TGT_SHORT = "Chủ nhà hàng chào đón mọi vị khách ở cửa và dẫn họ đến bàn."


def _vi_output(tmp_path: Path) -> Path:
    out = tmp_path / "out.epub"
    _epub(out, f'<p class="src">{SRC}</p><p class="tgt">{TGT_SHORT}</p>')
    return out


def _book(tmp_path: Path, state: dict | None) -> Path:
    book = tmp_path / "book"
    book.mkdir()
    (book / "glossary.json").write_text(
        json.dumps({"style_anchor": {"register": "storyteller cadence", "avoid": [], "prefer": []}}),
        encoding="utf-8")
    if state is not None:
        (book / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return book


def test_ratio_fixture_really_discriminates():
    assert 0.22 < len(TGT_SHORT) / len(SRC) < 0.60


def test_cli_uses_the_vi_profile_when_state_json_says_vi(tmp_path, capsys):
    book = _book(tmp_path, {"target_lang": "vi"})
    rc = translation_quality_audit.main(["--output", str(_vi_output(tmp_path)), "--book-dir", str(book)])
    out = capsys.readouterr().out
    assert "target too short" in out, out            # vi register ratio 0.60 applies (amber)


def test_cli_without_state_json_keeps_zh_tw(tmp_path, capsys):
    book = _book(tmp_path, None)
    rc = translation_quality_audit.main(["--output", str(_vi_output(tmp_path)), "--book-dir", str(book)])
    out = capsys.readouterr().out
    assert rc == 0 and "target too short" not in out, out   # zh-tw default 0.22 applies


def test_cli_without_book_dir_keeps_zh_tw(tmp_path, capsys):
    assert translation_quality_audit.main(["--output", str(_vi_output(tmp_path))]) == 0
    assert "target too short" not in capsys.readouterr().out


def test_cli_rejects_an_unknown_target_lang(tmp_path):
    import pytest
    book = _book(tmp_path, {"target_lang": "xx"})
    with pytest.raises(ValueError):
        translation_quality_audit.main(["--output", str(_vi_output(tmp_path)), "--book-dir", str(book)])


# --- BUG-002: the vi default ratio (Advise call 2026-11-12) ------------------------------

import pytest

from scripts.lang_profile import get_profile

VI = get_profile("vi")
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _glossary(tmp_path: Path, register: str | None):
    anchor = {"avoid": [], "prefer": []}
    if register is not None:
        anchor["register"] = register
    (tmp_path / "glossary.json").write_text(json.dumps({"style_anchor": anchor}), encoding="utf-8")


@pytest.mark.parametrize("register", ["zzz unknown", "", None])
def test_vi_unmatched_or_empty_register_gets_the_vi_default(tmp_path, register):
    _glossary(tmp_path, register)
    assert translation_quality_audit._min_length_ratio_from_book_dir(tmp_path, profile=VI) == 0.60


def test_vi_without_glossary_or_book_dir_gets_the_vi_default(tmp_path):
    assert translation_quality_audit._min_length_ratio_from_book_dir(tmp_path, profile=VI) == 0.60
    assert translation_quality_audit._min_length_ratio_from_book_dir(None, profile=VI) == 0.60


def test_zh_tw_and_no_profile_keep_0_22_in_every_unmatched_case(tmp_path):
    f = translation_quality_audit._min_length_ratio_from_book_dir
    assert f(None) == 0.22 and f(tmp_path) == 0.22
    _glossary(tmp_path, "zzz unknown")
    assert f(tmp_path) == 0.22 and f(tmp_path, profile=get_profile("zh-tw")) == 0.22


def test_vi_default_matches_every_vi_register_ratio():
    # Guard against drift while DECISION-012 is provisional: tune a register on purpose, not by accident.
    hints = json.loads((ASSETS / "register_hints.vi.json").read_text(encoding="utf-8"))
    default = hints["default_min_length_ratio"]
    assert 0 < default < 1
    assert all(r["min_length_ratio"] == default for r in hints["registers"])


def test_zh_tw_hints_file_has_no_default_key():
    hints = json.loads((ASSETS / "register_hints.json").read_text(encoding="utf-8"))
    assert "default_min_length_ratio" not in hints


@pytest.mark.parametrize("bad", ["0.6", 0, 1.5, -1, None, True])
def test_invalid_default_value_falls_back_to_0_22(tmp_path, monkeypatch, bad):
    from scripts import glossary
    hints = tmp_path / "hints.json"
    hints.write_text(json.dumps({"registers": [], "default_min_length_ratio": bad}), encoding="utf-8")
    monkeypatch.setattr(glossary, "_hints_path", lambda profile=None: hints)
    assert translation_quality_audit._min_length_ratio_from_book_dir(None, profile=VI) == 0.22
