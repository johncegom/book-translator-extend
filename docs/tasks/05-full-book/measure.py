"""Phase 5 measurement: aggregate numbers only, never text.

Reads the gitignored run directory and prints ratio percentiles, detector results,
terminal-punctuation counts and item statuses. Usage (repo root):
    python docs/tasks/05-full-book/measure.py runs/subtract/out/subtract
"""
from __future__ import annotations

import collections
import json
import re
import statistics
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
import dispatch  # noqa: E402
import lang_profile  # noqa: E402
import state as state_mod  # noqa: E402


def pct(values, p):
    values = sorted(values)
    if not values:
        return None
    k = (len(values) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return round(values[lo] + (values[hi] - values[lo]) * (k - lo), 3)


def vi_share(text: str):
    """Same counting as lang_profile._vi_is_target_text, returning the share."""
    text = unicodedata.normalize("NFC", text).strip()
    tokens = [t for t in re.findall(r"\w+", text) if not t.isdigit()]
    counted = [t for t in tokens if t[0].islower()] or tokens
    if not counted:
        return None
    return sum(1 for t in counted if lang_profile._vi_token_matches(t)) / len(counted)


def main(book_dir: Path) -> None:
    manifest = json.loads((book_dir / "manifest.json").read_text(encoding="utf-8"))
    st = state_mod.load(book_dir / "state.json")
    profile = lang_profile.get_profile(st["target_lang"])
    print("items by (strategy,status):", dict(collections.Counter(
        (v["output_strategy"], v["status"]) for v in st["chapters"].values())))
    ratios, shares_long, n_long, n_all = [], [], 0, 0
    en_shares = []  # the same detector share over the English source: the false-positive side
    false_long, false_all, no_terminal, end_cut = [], 0, 0, 0
    for e in manifest["spine"]:
        if e["output_strategy"] != "translate":
            continue
        src = dispatch.html_to_paragraphs((book_dir / f"chapters/{e['id']}.html").read_text(encoding="utf-8"))
        tr = (book_dir / f"chapters/{e['id']}_translation.txt").read_text(encoding="utf-8").split("\n\n")
        assert len(src) == len(tr), e["id"]
        for s, t in zip(src, tr):
            n_all += 1
            ok = profile.is_target_text(t)
            if not ok:
                false_all += 1
            if len(s) >= 50:
                n_long += 1
                ratios.append(len(t) / len(s))
                es = vi_share(s)
                if es is not None:
                    en_shares.append(es)
                sh = vi_share(t)
                if sh is not None:
                    shares_long.append(sh)
                if not ok:
                    false_long.append(round(sh, 3) if sh is not None else None)
                if not re.search(r"[.!?…:;\"”’)\]]$", t.strip()):
                    no_terminal += 1
                if not re.search(r"[.!?…:;\"”’)\]]$", s.strip()):
                    end_cut += 1
    print("translated paragraphs:", n_all, " of 50+ source chars:", n_long)
    print("length ratio (50+): min", pct(ratios, 0), "p1", pct(ratios, 1), "p5", pct(ratios, 5),
          "median", pct(ratios, 50), " below 0.60:", sum(r < 0.60 for r in ratios))
    print("detector share (50+ translations): min", pct(shares_long, 0), "p1", pct(shares_long, 1),
          "p5", pct(shares_long, 5), "median", pct(shares_long, 50))
    print("detector share over the ENGLISH source (50+): max", pct(en_shares, 100), "p99", pct(en_shares, 99),
          "median", pct(en_shares, 50), " >=0.17:", sum(x >= 0.17 for x in en_shares),
          " >=0.20:", sum(x >= 0.20 for x in en_shares), " >=0.25:", sum(x >= 0.25 for x in en_shares), "of", len(en_shares))
    print("is_target_text false: 50+ chars", len(false_long), "(shares", sorted(set(false_long)), ") all paragraphs", false_all)
    print("50+ paragraphs with no terminal punctuation: translation", no_terminal, " source", end_cut)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
