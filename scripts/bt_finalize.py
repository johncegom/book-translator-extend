"""Finalize one translated item: validate the raw reply, write the chapter file, mark it done.

Usage: python scripts/bt_finalize.py <book_dir> <item_id> [model]

Reads <book_dir>/translation_raw/<item_id>.txt, checks it against chapters/<item_id>.html,
writes chapters/<item_id>_translation.txt, marks the item done in state.json and writes the
translation log entry. Safe to run from several processes at once: the state.json change goes
through state.update (BUG-010). Exits 1 and prints WARNINGS when validation fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:  # pragma: no cover - import mode depends on caller
    from . import dispatch, state, translation_log
except ImportError:  # pragma: no cover
    import dispatch, state, translation_log  # type: ignore


def finalize(book_dir: Path, item: str, model: str = "opus") -> int:
    raw = (book_dir / "translation_raw" / f"{item}.txt").read_text(encoding="utf-8")
    html = (book_dir / "chapters" / f"{item}.html").read_text(encoding="utf-8")
    n = len(dispatch.html_to_paragraphs(html))
    warnings = dispatch.validate_translation(raw, html)
    if warnings:
        print("WARNINGS", warnings)
        return 1
    text = dispatch.extract_aligned_translation(raw, n)
    (book_dir / "chapters" / f"{item}_translation.txt").write_text(text, encoding="utf-8")
    state.update(book_dir / "state.json", lambda st: state.mark_done(st, item, text))
    translation_log.write_log_entry(
        book_dir=book_dir,
        chapter_id=item,
        prompt=(book_dir / "prompts" / f"{item}.prompt.txt").read_text(encoding="utf-8"),
        raw_response=raw,
        parsed_translation=text,
        validation_warnings=[],
        model=model,
        source_paragraph_count=n,
    )
    print("OK", item, n, "paras")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    return finalize(Path(argv[1]), argv[2], argv[3] if len(argv) > 3 else "opus")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
