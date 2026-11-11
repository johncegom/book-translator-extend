"""Phase 3 (3.5): the quality audit fails a target paragraph equal to its source.

Per the Advise outcome (docs/tasks/03-detector-audits/TASK.md, "3.5 Advise outcome") the check
applies to every profile, with no profile field. Ordinary test-first.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts import translation_quality_audit
from scripts.lang_profile import ZH_TW, get_profile

VI = get_profile("vi")
SRC = "This is a long English paragraph that clearly needs a translated sibling after it for the audit."
VI_TGT = "Đây là một đoạn văn tiếng Việt khá dài, đã được dịch đầy đủ để kiểm tra bản dịch song ngữ này."
ZH_TGT = "這是一段很長的英文段落，顯然需要在它後面有一段翻譯，讓審核可以檢查雙語書。"


def _write_epub(path: Path, body: str, source_only: list | None = None) -> None:
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
        if source_only is not None:
            z.writestr("OEBPS/translations/source_only.json", json.dumps(source_only, ensure_ascii=False))


def _audit(tmp_path, body, profile=None, source_only=None):
    path = tmp_path / "t.epub"
    _write_epub(path, body, source_only)
    return translation_quality_audit.audit(path, profile=profile)


def test_vi_echo_fails_with_an_explicit_message(tmp_path):
    ok, failures = _audit(tmp_path, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{SRC}</p>', VI)
    assert ok is False
    assert any("target equals source" in f for f in failures)


def test_zh_tw_echo_fails_too(tmp_path):
    ok, failures = _audit(tmp_path, f'<p class="src">{SRC}</p><p class="tgt tgt-zh">{SRC}</p>', ZH_TW)
    assert ok is False
    assert any("target equals source" in f for f in failures)


def test_echo_is_reported_exactly_once_as_a_failure(tmp_path):
    ok, failures = _audit(tmp_path, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{SRC}</p>', VI)
    assert ok is False and len([f for f in failures if "equals source" in f]) == 1


def test_whitespace_and_nfc_differences_still_count_as_an_echo(tmp_path):
    spaced = SRC.replace(" ", "  ")
    ok, failures = _audit(tmp_path, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{spaced}</p>', VI)
    assert any("equals source" in f for f in failures)


def test_real_translations_pass_for_both_profiles(tmp_path):
    ok_vi, f_vi = _audit(tmp_path, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{VI_TGT}</p>', VI)
    assert ok_vi is True, f_vi
    ok_zh, f_zh = _audit(tmp_path, f'<p class="src">{SRC}</p><p class="tgt tgt-zh">{ZH_TGT}</p>', ZH_TW)
    assert not any("equals source" in f for f in f_zh)


def test_a_near_echo_is_not_this_checks_job(tmp_path):
    near = SRC.rstrip(".")  # only the final period differs
    ok, failures = _audit(tmp_path, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{near}</p>', VI)
    assert not any("equals source" in f for f in failures)


def test_short_sources_headings_and_listed_exceptions_are_exempt(tmp_path):
    short = "Short line."
    ok, f = _audit(tmp_path, f'<p class="src">{short}</p><p class="tgt tgt-vi">{short}</p>', VI)
    assert not any("equals source" in x for x in f)
    ok, f = _audit(tmp_path, f'<h2 class="src">{SRC}</h2><p class="tgt tgt-vi">{SRC}</p>', VI)
    assert not any("equals source" in x for x in f)
    exc = [{"src_text": SRC, "reason": "verbatim epigraph"}]
    ok, f = _audit(tmp_path, f'<p class="src">{SRC}</p><p class="tgt tgt-vi">{SRC}</p>', VI, source_only=exc)
    assert not any("equals source" in x for x in f)


def test_a_decomposed_unicode_echo_is_still_an_echo(tmp_path):
    import unicodedata
    src = "Nguyễn đã đến thăm khu bờ sông Embarcadero cùng gia đình vào một buổi sáng mùa hè năm đó."
    nfd = unicodedata.normalize("NFD", src)
    ok, failures = _audit(tmp_path, f'<p class="src">{src}</p><p class="tgt tgt-vi">{nfd}</p>', VI)
    assert any("equals source" in f for f in failures)
