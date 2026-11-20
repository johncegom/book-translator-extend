"""BUG-021: audit command lines must not crash when stdout uses a legacy code page (Windows cp1252)."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bilingual_coverage_audit  # type: ignore  # noqa: E402
from scripts import grade_checks  # noqa: E402
from test_bilingual_coverage_audit import _write_epub  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
_SRC = "This is a long English paragraph that clearly needs a translated sibling after it for coverage."
_VI = "Đây là một đoạn văn dài bằng tiếng Việt đã được dịch đầy đủ cho cuốn sách này."


def _cp1252_stdout(monkeypatch):
    raw = io.BytesIO()
    wrapper = io.TextIOWrapper(raw, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", wrapper)
    return wrapper, raw


def _vi_book(tmp_path: Path):
    epub = tmp_path / "book.epub"
    _write_epub(epub, f'<html><body><p class="src">{_SRC}</p><p class="tgt tgt-vi">{_VI}</p></body></html>')
    book_dir = tmp_path / "book"
    book_dir.mkdir()
    (book_dir / "state.json").write_text(json.dumps({"target_lang": "vi"}), encoding="utf-8")
    return epub, book_dir


def test_helper_switches_a_legacy_stream_to_utf8(monkeypatch):
    from console_utf8 import use_utf8_output  # type: ignore

    wrapper, raw = _cp1252_stdout(monkeypatch)
    use_utf8_output()
    print("｜ Tiếng Việt")
    wrapper.flush()
    assert raw.getvalue().decode("utf-8").strip() == "｜ Tiếng Việt"


def test_helper_leaves_a_stream_without_reconfigure_alone(monkeypatch):
    from console_utf8 import use_utf8_output  # type: ignore

    monkeypatch.setattr(sys, "stdout", io.StringIO())
    use_utf8_output()  # must not raise


def test_coverage_audit_pass_line_prints_on_a_cp1252_stdout(tmp_path, monkeypatch):
    epub, book_dir = _vi_book(tmp_path)
    wrapper, raw = _cp1252_stdout(monkeypatch)
    rc = bilingual_coverage_audit.main(["--source", str(epub), "--output", str(epub), "--book-dir", str(book_dir)])
    wrapper.flush()
    assert rc == 0
    assert "Tiếng Việt" in raw.getvalue().decode("utf-8")


def test_grade_sample_prints_vietnamese_on_a_cp1252_stdout(tmp_path, monkeypatch):
    import zipfile

    epub = tmp_path / "o.epub"
    with zipfile.ZipFile(epub, "w") as z:
        z.writestr("ch.xhtml", f'<html><body><p class="src">{_SRC}</p><p class="tgt tgt-vi">{_VI}</p></body></html>')
    (tmp_path / "glossary.json").write_text(json.dumps({"terms": {}, "style_anchor": {"avoid": []}}), encoding="utf-8")
    wrapper, raw = _cp1252_stdout(monkeypatch)
    rc = grade_checks.main(["--source", str(epub), "--output", str(epub), "--book-dir", str(tmp_path), "--sample", "1"])
    wrapper.flush()
    assert rc == 0
    assert "Đây là một đoạn văn" in json.loads(raw.getvalue().decode("utf-8"))[0]["tgt"]


def test_coverage_audit_command_line_exits_zero_under_cp1252(tmp_path):
    epub, book_dir = _vi_book(tmp_path)
    env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
    env.pop("PYTHONUTF8", None)
    done = subprocess.run(
        [sys.executable, "-m", "scripts.bilingual_coverage_audit", "--source", str(epub), "--output", str(epub), "--book-dir", str(book_dir)],
        cwd=ROOT, env=env, capture_output=True,
    )
    assert done.returncode == 0, done.stderr.decode("utf-8", "replace")[-300:]
    assert "Tiếng Việt" in done.stdout.decode("utf-8")
