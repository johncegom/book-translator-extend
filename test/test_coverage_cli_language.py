"""BUG-022: the coverage audit command line takes its language from the book folder."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bilingual_coverage_audit  # type: ignore  # noqa: E402
from test_bilingual_coverage_audit import _write_epub  # noqa: E402

_SRC = "This is a long English paragraph that clearly needs a translated sibling after it for coverage."
_VI = "Đây là một đoạn văn dài bằng tiếng Việt đã được dịch đầy đủ cho cuốn sách này."
_ZH = "這是一段很長的中文翻譯段落，已經完整翻譯了上面的英文內容，供雙語覆蓋檢查使用。"


def _book(tmp_path: Path, target: str, state: dict | None):
    epub = tmp_path / "book.epub"
    cls = "tgt tgt-vi" if target == _VI else "tgt tgt-zh"
    _write_epub(epub, f'<html><body><p class="src">{_SRC}</p><p class="{cls}">{target}</p></body></html>')
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    if state is not None:
        (book_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return epub, book_dir


def _run(epub: Path, *extra: str) -> int:
    return bilingual_coverage_audit.main(["--source", str(epub), "--output", str(epub), *extra])


def test_vi_book_passes_with_book_dir(tmp_path, capsys):
    epub, book_dir = _book(tmp_path, _VI, {"target_lang": "vi"})
    assert _run(epub, "--book-dir", str(book_dir)) == 0
    out = capsys.readouterr()
    assert "bilingual_coverage_audit: PASS" in out.out
    assert "adjacent Han" not in out.out
    assert out.err == ""


def test_no_book_dir_warns_and_uses_zh_tw(tmp_path, capsys):
    epub, _ = _book(tmp_path, _VI, None)
    assert _run(epub) == 1  # a vi book audited as zh-tw: the old, wrong verdict, now with a warning
    assert "zh-tw" in capsys.readouterr().err


def test_book_dir_without_state_json_warns(tmp_path, capsys):
    epub, book_dir = _book(tmp_path, _ZH, None)
    assert _run(epub, "--book-dir", str(book_dir)) == 0
    err = capsys.readouterr().err
    assert "state.json" in err and "zh-tw" in err


def test_unregistered_target_lang_raises(tmp_path):
    epub, book_dir = _book(tmp_path, _VI, {"target_lang": "vn"})
    with pytest.raises(ValueError):
        _run(epub, "--book-dir", str(book_dir))


def test_zh_tw_success_line_is_unchanged(tmp_path, capsys):
    epub, book_dir = _book(tmp_path, _ZH, {"target_lang": "zh-tw"})
    assert _run(epub, "--book-dir", str(book_dir)) == 0
    out = capsys.readouterr()
    assert "all English content paragraphs have adjacent Han translations" in out.out
    assert out.err == ""
