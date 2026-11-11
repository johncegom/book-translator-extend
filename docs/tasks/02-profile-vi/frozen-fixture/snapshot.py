"""Snapshot assemble + audit_suite output for the frozen fixture.

Usage: python snapshot.py <frozen_book_dir> <source_epub> <snapshot.json> [scripts_dir]

Writes: ordered zip member names, SHA-256 of each member's content, and the
audit_suite stdout/exit code. Zip member timestamps are not compared (they
differ run to run). Run twice on unchanged code to prove stability, then
before/after a change and diff the two JSON files.
"""
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import zipfile
from pathlib import Path


def main(book: Path, source_epub: Path, out_json: Path, scripts: Path) -> int:
    sys.path.insert(0, str(scripts))
    import assemble
    import audit_suite

    with tempfile.TemporaryDirectory() as tmp:
        epub = Path(tmp) / "out.epub"
        assemble.assemble(book, epub)
        with zipfile.ZipFile(epub) as z:
            members = [(n, hashlib.sha256(z.read(n)).hexdigest()) for n in z.namelist()]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = audit_suite.main(["--source", str(source_epub), "--output", str(epub), "--book-dir", str(book)])
    snap = {"members": members, "audit_exit": code, "audit_output": buf.getvalue().replace(tmp, "<TMP>")}
    out_json.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(members)} members, audit exit {code}")
    return 0


if __name__ == "__main__":
    scripts = Path(sys.argv[4]) if len(sys.argv) > 4 else Path(__file__).resolve().parents[4] / "scripts"
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), scripts))
