"""BUG-005: the coverage failure text names the book's language, not always zh."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bilingual_coverage_audit  # type: ignore  # noqa: E402
from lang_profile import VI, ZH_TW  # type: ignore  # noqa: E402
from test_bilingual_coverage_audit import _write_epub  # noqa: E402

_BODY = (
    "<html><body><p>This is a long English paragraph that clearly needs a translated "
    "sibling after it for bilingual coverage.</p></body></html>"
)


def _failures(tmp_path: Path, profile) -> list[str]:
    epub = tmp_path / "missing.epub"
    _write_epub(epub, _BODY)
    passed, failures = bilingual_coverage_audit.audit(epub, epub, profile=profile)
    assert passed is False
    return failures


def test_vi_failure_text_names_vi(tmp_path: Path) -> None:
    failures = _failures(tmp_path, VI)
    assert "missing adjacent vi after:" in failures[0]
    assert "adjacent zh" not in failures[0]


def test_zh_tw_failure_text_is_unchanged(tmp_path: Path) -> None:
    assert "missing adjacent zh after:" in _failures(tmp_path, ZH_TW)[0]
