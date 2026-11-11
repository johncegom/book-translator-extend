"""Build the frozen zh-tw Alice fixture used to compare assemble/audit output
before and after the Phase 1 refactor (docs/tasks/01-profile-zh-tw/TASK.md).

Usage: python build.py <extracted_book_dir> <out_dir>
  <extracted_book_dir>: output of scripts/extract_epub.py (runs/alice/out/alice)
  <out_dir>: new directory; must not exist.

The fixture is an excerpt: item_002 (title page, full), item_003 and item_004
(chapter headings plus the first paragraphs). All other translate items are
marked drop_explicit. Translations are hand-written and fixed, so reruns on
unchanged code are identical.
"""
import json
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup

HERE = Path(__file__).resolve().parent
KEEP_PARAGRAPHS = {"item_003": 5, "item_004": 4}  # <p> elements kept after the heading


def main(src: Path, out: Path) -> None:
    if out.exists():
        raise SystemExit(f"{out} already exists")
    shutil.copytree(src, out)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["spine"]:
        if entry["output_strategy"] == "translate" and entry["id"] not in {"item_002", *KEEP_PARAGRAPHS}:
            entry["output_strategy"] = "drop_explicit"
            entry["reason"] = "frozen fixture excerpt"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    by_id = {e["id"]: e for e in manifest["spine"]}
    for item, keep in KEEP_PARAGRAPHS.items():
        # assemble reads the original-path copy first, then chapters/<id>.html; trim both.
        paths = {out / "chapters" / f"{item}.html", out / Path(by_id[item]["original_path"]).name}
        for path in paths:
            if not path.is_file():
                continue
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "xml")
            for p in soup.find_all("p")[keep:]:
                p.decompose()
            path.write_text(str(soup), encoding="utf-8")
    for name in ("state.json", "glossary.json", "translations_extra.json"):
        shutil.copy(HERE / name, out / name)
    (out / "chapters").mkdir(exist_ok=True)
    for f in (HERE / "translations").glob("*_translation.txt"):
        shutil.copy(f, out / "chapters" / f.name)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
