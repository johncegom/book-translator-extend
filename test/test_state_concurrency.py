"""BUG-010: several processes updating state.json at once must not lose an update.

Ordinary test-first. Real processes (multiprocessing, spawn on Windows and Linux CI), because threads
would share one interpreter lock and hide the race.
"""
from __future__ import annotations

import json
import multiprocessing as mp
from pathlib import Path

import pytest

from scripts import state

PROCS = 6
PER_PROC = 8


def _worker(args) -> None:
    path_str, proc = args
    path = Path(path_str)
    for n in range(PER_PROC):
        item = f"item_{proc:02d}{n:02d}"
        state.update(path, lambda st, item=item: state.mark_done(st, item, f"text for {item}"))


def _ids() -> list[str]:
    return [f"item_{p:02d}{n:02d}" for p in range(PROCS) for n in range(PER_PROC)]


def test_parallel_updates_lose_nothing(tmp_path: Path):
    path = tmp_path / "state.json"
    state.save(path, state.init_state(Path("book.epub"), _ids(), "vi"))
    ctx = mp.get_context("spawn")
    with ctx.Pool(PROCS) as pool:
        pool.map(_worker, [(str(path), p) for p in range(PROCS)])
    final = state.load(path)
    statuses = {cid: entry["status"] for cid, entry in final["chapters"].items()}
    assert set(statuses.values()) == {"done"}, [c for c, s in statuses.items() if s != "done"]


def test_update_returns_the_new_state_and_persists_it(tmp_path: Path):
    path = tmp_path / "state.json"
    state.save(path, state.init_state(Path("book.epub"), ["item_001"], "vi"))
    new = state.update(path, lambda st: state.mark_done(st, "item_001", "x"))
    assert new["chapters"]["item_001"]["status"] == "done"
    assert state.load(path)["chapters"]["item_001"]["status"] == "done"


def test_update_on_a_missing_file_raises_instead_of_creating_one(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        state.update(tmp_path / "missing.json", lambda st: None)


def test_save_leaves_no_temp_or_lock_file_behind(tmp_path: Path):
    path = tmp_path / "state.json"
    state.save(path, state.init_state(Path("book.epub"), ["item_001"], "vi"))
    state.update(path, lambda st: state.mark_done(st, "item_001", "x"))
    assert sorted(p.name for p in tmp_path.iterdir()) == ["state.json"]


def test_save_is_atomic_a_failed_replace_keeps_the_old_file_and_cleans_up(tmp_path: Path, monkeypatch):
    import os

    path = tmp_path / "state.json"
    st = state.init_state(Path("book.epub"), ["item_001"], "vi")
    state.save(path, st)
    before = path.read_text(encoding="utf-8")
    st["glossary_built"] = True

    def boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        state.save(path, st)
    assert path.read_text(encoding="utf-8") == before
    assert [p.name for p in tmp_path.iterdir()] == ["state.json"]


def test_a_stale_lock_file_does_not_block_forever(tmp_path: Path):
    path = tmp_path / "state.json"
    state.save(path, state.init_state(Path("book.epub"), ["item_001"], "vi"))
    lock = path.with_name(path.name + ".lock")
    lock.write_text("stale")
    import os, time
    old = time.time() - 3600
    os.utime(lock, (old, old))
    state.update(path, lambda st: state.mark_done(st, "item_001", "x"))
    assert state.load(path)["chapters"]["item_001"]["status"] == "done"
