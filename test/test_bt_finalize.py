"""scripts/bt_finalize.py: validate a raw reply, write the chapter file, mark the item done.

Ordinary test-first (no zh-tw oracle involved). The parallel test runs the real script in
separate processes, the way the fan-out does (BUG-010).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts import state

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "bt_finalize.py"

HTML = "<html><body><p>The cache holds hot data close to the client.</p><p>Eviction removes the oldest entries first.</p></body></html>"
RAW = (
    "[[PARA_1]]\nBộ nhớ đệm giữ dữ liệu được dùng nhiều ở gần client.\n\n"
    "[[PARA_2]]\nEviction loại bỏ các mục cũ nhất trước tiên.\n"
)


def _book(tmp_path: Path, items: list[str], raw: str = RAW) -> Path:
    for sub in ("translation_raw", "chapters", "prompts"):
        (tmp_path / sub).mkdir()
    for item in items:
        (tmp_path / "translation_raw" / f"{item}.txt").write_text(raw, encoding="utf-8")
        (tmp_path / "chapters" / f"{item}.html").write_text(HTML, encoding="utf-8")
        (tmp_path / "prompts" / f"{item}.prompt.txt").write_text("prompt", encoding="utf-8")
    state.save(tmp_path / "state.json", state.init_state(Path("book.epub"), items, "vi"))
    return tmp_path


def _run(book: Path, item: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(book), item, "test-model"],
        capture_output=True, text=True, encoding="utf-8",
    )


def test_valid_reply_writes_the_chapter_and_marks_it_done(tmp_path: Path):
    book = _book(tmp_path, ["item_001"])
    result = _run(book, "item_001")
    assert result.returncode == 0, result.stderr
    assert "OK item_001 2 paras" in result.stdout
    text = (book / "chapters" / "item_001_translation.txt").read_text(encoding="utf-8")
    assert text.split("\n\n") == [
        "Bộ nhớ đệm giữ dữ liệu được dùng nhiều ở gần client.",
        "Eviction loại bỏ các mục cũ nhất trước tiên.",
    ]
    assert state.load(book / "state.json")["chapters"]["item_001"]["status"] == "done"
    assert list((book / "translation_log").iterdir())


def test_invalid_reply_exits_1_and_changes_nothing(tmp_path: Path):
    book = _book(tmp_path, ["item_001"], raw="[[PARA_1]]\nChỉ có một đoạn.\n")
    result = _run(book, "item_001")
    assert result.returncode == 1
    assert "WARNINGS" in result.stdout
    assert state.load(book / "state.json")["chapters"]["item_001"]["status"] == "pending"
    assert not (book / "chapters" / "item_001_translation.txt").exists()


def test_reply_without_markers_exits_1_with_warnings_and_changes_nothing(tmp_path: Path):
    # validate_translation accepts this (it falls back to a paragraph-count check) but
    # extract_aligned_translation raises. Nothing may be written or marked done first (BUG-011).
    book = _book(tmp_path, ["item_001"], raw="Bộ nhớ đệm giữ dữ liệu ở gần client.\n\nEviction loại bỏ mục cũ nhất.\n")
    result = _run(book, "item_001")
    assert result.returncode == 1
    assert "WARNINGS" in result.stdout
    assert "Traceback" not in result.stderr
    assert state.load(book / "state.json")["chapters"]["item_001"]["status"] == "pending"
    assert not (book / "chapters" / "item_001_translation.txt").exists()


def test_parallel_runs_lose_no_update(tmp_path: Path):
    items = [f"item_{n:03d}" for n in range(1, 7)]
    book = _book(tmp_path, items)
    procs = [
        subprocess.Popen(
            [sys.executable, str(SCRIPT), str(book), item],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
        )
        for item in items
    ]
    outputs = [p.communicate() for p in procs]
    assert [p.returncode for p in procs] == [0] * len(items), outputs
    final = state.load(book / "state.json")
    assert {c: e["status"] for c, e in final["chapters"].items()} == {i: "done" for i in items}
