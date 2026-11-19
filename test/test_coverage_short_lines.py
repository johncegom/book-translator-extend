"""BUG-018 / Phase 13: a short source line counts as covered when the next paragraph is a marked
translation that differs from the source and has a non-ASCII letter the source lacks."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bilingual_coverage_audit  # type: ignore  # noqa: E402
from lang_profile import VI, ZH_TW  # type: ignore  # noqa: E402
from test_bilingual_coverage_audit import _write_epub  # noqa: E402


def _run(tmp_path: Path, body: str, profile):
    epub = tmp_path / "b.epub"
    _write_epub(epub, f"<html><body>{body}</body></html>")
    return bilingual_coverage_audit._audit_with_warnings(epub, epub, profile=profile)


def _pair(src: str, tgt: str, cls: str = "tgt tgt-vi") -> str:
    return f'<p class="src">{src}</p><p class="{cls}">{tgt}</p>'


def test_marked_vietnamese_label_with_shared_letters_is_covered(tmp_path):
    # BUG-018: "Sự chú ý" has no letter the detector counts, but it is a marked, different, accented line.
    ok, failures, warnings = _run(tmp_path, _pair("Attention", "Sự chú ý"), VI)
    assert ok and not failures and not warnings


@pytest.mark.parametrize("src, tgt", [
    ("Begin Reading", "Begin Reading"),                              # exact echo
    ("Data centers", "Data center"),                                 # near-echo, no accented letter
    ("Begin Reading", "—Begin Reading"),                             # only punctuation is non-ASCII
    ("He met Nguyễn in the market.", "He met Nguyễn at the market."),  # accented letter copied from the source
])
def test_near_echoes_still_warn(tmp_path, src, tgt):
    ok, failures, warnings = _run(tmp_path, _pair(src, tgt), VI)
    assert warnings, (src, tgt)


def test_sibling_without_the_tgt_class_still_warns(tmp_path):
    ok, failures, warnings = _run(tmp_path, '<p class="src">Attention</p><p>Sự chú ý</p>', VI)
    assert warnings


def test_long_line_stays_a_failure(tmp_path):
    src = "This is a long English paragraph that clearly needs a translated sibling after it."
    tgt = "This is a long English paragraph with one accent only: Sự"
    ok, failures, warnings = _run(tmp_path, _pair(src, tgt), VI)
    assert ok is False and failures


def test_zh_tw_short_near_echo_still_warns(tmp_path):
    ok, failures, warnings = _run(tmp_path, _pair("Begin Reading", "—Begin Reading", "tgt tgt-zh"), ZH_TW)
    assert warnings
