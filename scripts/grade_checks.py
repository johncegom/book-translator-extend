"""Run the yes/no checks of docs/grade-rubric.md and print `ID: YES|NO - evidence` lines.

    python -m scripts.grade_checks --source SRC.epub --output OUT.epub --book-dir BOOK_DIR

Generic: book facts come from the book folder (state.json, translations_extra.json,
translations/source_only.json, spec_terms.json) and the language profile. Exit 0 only if every check is YES.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
try:
    from . import audit_suite, dispatch
    from .paragraph_classification import reasoned_source_only_entries
except ImportError:  # pragma: no cover - script invocation
    import audit_suite, dispatch  # type: ignore
    from paragraph_classification import reasoned_source_only_entries  # type: ignore

MIN_BLOCK_CHARS = 50
SEP = "｜"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _squash(text: str) -> str:
    """Text with all whitespace removed, so spacing around inline tags cannot hide an echo or a match."""
    return re.sub(r"\s+", "", text or "")


def _classes(tag) -> list[str]:
    return tag.get("class") or []


def _content_docs(z: zipfile.ZipFile):
    for name in sorted(z.namelist()):
        if name.lower().endswith((".html", ".xhtml")) and not name.endswith("nav.xhtml"):
            yield name, BeautifulSoup(z.read(name), "html.parser")


def _pairs(z: zipfile.ZipFile):
    """Every src block (any length) as (file, src_text, tgt_text or None)."""
    for name, soup in _content_docs(z):
        for tag in soup.find_all(True):
            if "src" not in _classes(tag):
                continue
            nxt = tag.find_next_sibling()
            tgt = _norm(nxt.get_text()) if nxt is not None and "tgt" in _classes(nxt) else None
            yield name, _norm(tag.get_text()), tgt


def _nav_entries(z: zipfile.ZipFile) -> tuple[str, list[str]]:
    name = next(n for n in z.namelist() if n.endswith("nav.xhtml"))
    soup = BeautifulSoup(z.read(name), "html.parser")
    title = _norm(soup.title.get_text()) if soup.title else ""
    toc = soup.find("nav", attrs={"epub:type": "toc"}) or soup.find("nav")
    return title, [_norm(a.get_text()) for a in toc.find_all("a")]


def _ncx(z: zipfile.ZipFile):
    name = next(n for n in z.namelist() if n.endswith(".ncx"))
    soup = BeautifulSoup(z.read(name), "xml")
    doc = soup.find("docTitle")
    points = []
    for p in soup.find_all("navPoint"):
        label = _norm(p.find("navLabel", recursive=False).get_text())
        points.append((label, p.find("content", recursive=False)["src"]))
    return (_norm(doc.get_text()) if doc else ""), points


def _numbers(labels: list[str]) -> list[tuple[str, str]]:
    """(English number, target number) for numbered chapter labels: `N | <name> N` or `Chapter N | <name> N`."""
    out = []
    for label in labels:
        if SEP not in label:
            continue
        left, right = (s.strip() for s in label.split(SEP, 1))
        if not re.match(r"(?i)(chapter\s+)?\d+$", left):
            continue
        ml, mr = re.search(r"(\d+)", left), re.search(r"(\d+)", right)
        out.append((ml.group(1), mr.group(1) if mr else ""))
    return out


def _anchor_target(z: zipfile.ZipFile, fname: str, frag: str) -> str | None:
    """Text of the tgt element right after the anchor; searches every part of a split file."""
    stem = Path(fname.split("/")[-1]).stem
    for n in sorted(z.namelist()):
        if n.endswith((".html", ".xhtml")) and Path(n).stem.startswith(stem):
            anchor = BeautifulSoup(z.read(n), "html.parser").find(id=frag)
            if anchor is not None:
                nxt = anchor.find_next_sibling()
                if nxt is not None and "tgt" in _classes(nxt):
                    return _norm(nxt.get_text())
                return None
    return None


_NUMBER = re.compile(r"\d[\d.,]*\d|\d")


def _plain_number(token: str) -> str:
    """Digits of one number token, whichever of "." and "," the writer used (no fixed rule exists).

    A last group that is not exactly 3 digits is a decimal part ("0.50", "0,5", "1.234,56"): its
    trailing zeros are dropped so "0.50" equals "0,5". A last group of 3 digits is a thousands group.
    """
    parts = re.split(r"[.,]", token)
    if len(parts) > 1 and len(parts[-1]) != 3:
        parts[-1] = parts[-1].rstrip("0")
    return "".join(parts)


def _number_tokens(text: str) -> set[str]:
    """Numbers of 3+ digits, separators removed (2,750 equals 2.750).

    One- and two-digit numbers are skipped on purpose: Vietnamese often spells them out
    ("3 a.m." becomes "ba giờ sáng"), which a script cannot match. Found on the first real run.
    """
    return {n for n in (_plain_number(t) for t in _NUMBER.findall(text)) if len(n) >= 3}


def _number_pairs(z: zipfile.ZipFile):
    """(source text, target text) per paired block, with endnote markers removed from the source.

    An endnote marker is a `<sup class="endnote">` the source puts right after a figure ("$28,650." then
    note 10); get_text would flatten it into "28,650.10" (BUG-019). The marker is a note number, not part of
    the figure, so N1 must not demand it in the target.
    """
    for name, soup in _content_docs(z):
        for tag in soup.find_all(True):
            if "src" not in _classes(tag):
                continue
            nxt = tag.find_next_sibling()
            if nxt is None or "tgt" not in _classes(nxt):
                continue
            clone = BeautifulSoup(str(tag), "html.parser")
            for sup in clone.find_all("sup", class_="endnote"):
                sup.decompose()
            yield _norm(clone.get_text()), _norm(nxt.get_text())


_QUOTED = re.compile(r"“[^”]*”|\"[^\"]*\"")


def _is_title_like(quoted: str) -> bool:
    """3+ words, and every word of 4+ letters starts with a capital: a title of a work, not a term in quotes."""
    words = [w for w in re.split(r"[\s/]+", quoted.strip("“”\" ")) if w]
    if len(words) < 3:
        return False
    long_words = [re.sub(r"^\W+", "", w) for w in words if len(re.sub(r"\W", "", w)) >= 4]
    return all(w[:1].isupper() for w in long_words)


def _strip_quoted_titles(text: str) -> str:
    """Remove quoted title-like phrases, so a glossary term inside the title of a work is not listed for JC.

    Titles of works stay in the source language by design, so the term cannot appear in the translation.
    """
    return _QUOTED.sub(lambda m: "" if _is_title_like(m.group(0)) else m.group(0), text)


def sample_pairs(output: Path, book_dir: Path, n: int = 20, seed: int = 20261114) -> list[dict]:
    """Fixed-seed sample of paired blocks for the judged items (J1 to J4, JC).

    Same output + same seed = same pairs, so a rerun grades the same text.
    """
    so_path = book_dir / "translations" / "source_only.json"
    skip: set[str] = set()
    if so_path.is_file():
        skip = {_norm(k) for k in reasoned_source_only_entries(json.loads(so_path.read_text(encoding="utf-8")))}
    with zipfile.ZipFile(output) as z:
        raw = [(f, s, t) for f, s, t in _pairs(z) if t and len(s) >= MIN_BLOCK_CHARS and s not in skip]
    # Endnote and reference pages are not running text: when most 50+ char blocks of a file
    # start with a note number, the whole file is left out of the sample.
    numbered: dict[str, list[bool]] = {}
    for f, s, _t in raw:
        numbered.setdefault(f, []).append(bool(re.match(r"\d{1,4}\s", s)))
    note_files = {f for f, flags in numbered.items() if len(flags) >= 3 and sum(flags) / len(flags) >= 0.6}
    pool = [(f, s, t) for f, s, t in raw if f not in note_files]
    glossary_path = book_dir / "glossary.json"
    glossary = json.loads(glossary_path.read_text(encoding="utf-8")) if glossary_path.is_file() else {}
    terms = {**(glossary.get("terms") or {})}
    avoid = (glossary.get("style_anchor") or {}).get("avoid") or []
    chosen = sorted(random.Random(seed).sample(range(len(pool)), min(n, len(pool))))
    out = []
    for i in chosen:
        f, s, t = pool[i]
        judged_src = _strip_quoted_titles(s)
        found = {k: v for k, v in terms.items() if re.search(r"\b" + re.escape(k) + r"\b", judged_src, re.I)}
        out.append({"id": f"P{i:04d}", "file": f, "src": s, "tgt": t, "glossary_terms": found, "style_avoid": avoid})
    return out


def label_has_target(label: str, labels: set[str], overrides: set[str]) -> bool:
    """E1: a profile label, a nav_overrides value (target label alone, BUG-017), or `English ｜ target`."""
    return label in labels or label in overrides or (SEP in label and bool(label.split(SEP, 1)[1].strip()))


def run_checks(source: Path, output: Path, book_dir: Path) -> list[tuple[str, bool, str]]:
    profile = audit_suite._profile_for_book(book_dir)
    results: list[tuple[str, bool, str]] = []

    def add(cid: str, ok: bool, evidence: str) -> None:
        results.append((cid, ok, evidence))

    audits = {r.name: r for r in audit_suite.run_all(source, output, book_dir)}
    so_path = book_dir / "translations" / "source_only.json"
    source_only: dict[str, str] = {}
    if so_path.is_file():
        entries = reasoned_source_only_entries(json.loads(so_path.read_text(encoding="utf-8")))
        source_only = {_squash(k): v for k, v in entries.items()}

    cov = audits["bilingual_coverage"]
    add("A1", not cov.failures, f"bilingual_coverage {cov.status}, {len(cov.failures)} FAIL lines")

    with zipfile.ZipFile(output) as z:
        pairs = list(_pairs(z))
        nav_title, nav_labels = _nav_entries(z)
        ncx_title, ncx_points = _ncx(z)
        long_blocks = [(t, g) for _f, t, g in pairs if len(t) >= MIN_BLOCK_CHARS]
        missing = [t for t, g in long_blocks if g is None and _squash(t) not in source_only]
        add("A2", not missing,
            f"{len(long_blocks)} blocks of {MIN_BLOCK_CHARS}+ chars, {len(missing)} without a tgt"
            + (f": {missing[0][:80]!r}" if missing else ""))
        same = [s for _f, s, g in pairs if g is not None and _squash(s) == _squash(g) and len(s.split()) >= 5 and _squash(s) not in source_only]
        add("B1", not same, f"{len(same)} identical pairs of 5+ words not in source_only.json"
            + (f": {same[0][:80]!r}" if same else ""))
        tq = audits["translation_quality"]
        add("B2", not tq.failures, f"translation_quality {tq.status}, {len(tq.failures)} FAIL lines")

        terms = dispatch.load_fixed_terms(book_dir)
        if not terms:
            add("C1", True, "no spec_terms.json")
        else:
            bad = [(k, s[:60]) for _f, s, g in pairs if g is not None
                   for k, v in terms.items()
                   if re.search(re.escape(k), s, re.I) and v.lower() not in g.lower()]
            add("C1", not bad, f"{len(terms)} fixed terms, {len(bad)} paragraphs without the mandated rendering"
                + (f": {bad[0]}" if bad else ""))

        nn, cn = _numbers(nav_labels), _numbers([l for l, _ in ncx_points])
        each_equal = all(a == b for a, b in nn + cn)
        same_numbers = [a for a, _ in nn] == [a for a, _ in cn]
        add("C2", bool(nn) and each_equal and same_numbers,
            f"nav numbers {[a for a, _ in nn]}, ncx numbers {[a for a, _ in cn]}, English=target in each label: {each_equal}")

        ratios = [len(g) / len(t) for t, g in long_blocks if g]
        threshold = audit_suite.translation_quality_audit._min_length_ratio_from_book_dir(book_dir, profile=profile)
        low = min(ratios) if ratios else 0.0
        add("D1", bool(ratios) and low >= threshold,
            f"lowest ratio {low:.3f} over {len(ratios)} blocks, threshold {threshold}")

        labels = set(profile.structural_labels.values()) | set(profile.contents_labels.values())
        labels.add(profile.bilingual_edition_label)
        extra_path = book_dir / "translations_extra.json"
        extra = json.loads(extra_path.read_text(encoding="utf-8")) if extra_path.is_file() else {}
        overrides = set((extra.get("nav_overrides") or {}).values())

        bad_nav = [l for l in nav_labels if not label_has_target(l, labels, overrides)]
        add("E1", not bad_nav, f"{len(nav_labels)} nav entries, {len(bad_nav)} without a target label"
            + (f": {bad_nav[:3]}" if bad_nav else ""))
        wrong = []
        for l in nav_labels:
            if SEP not in l:
                continue
            left, right = (s.strip() for s in l.split(SEP, 1))
            for key, val in {**profile.structural_labels, **profile.contents_labels}.items():
                if left.lower() == key.lower() and right != val and right not in overrides:
                    wrong.append(l)
        add("E2", not wrong, f"{len(wrong)} structural nav labels differ from the profile and nav_overrides"
            + (f": {wrong[:2]}" if wrong else ""))
        suffix = f" {SEP} {profile.bilingual_edition_label}"
        add("E3", nav_title.endswith(suffix) and ncx_title.endswith(suffix),
            f"nav title {nav_title!r}, ncx docTitle {ncx_title!r}")

        excluded, e4_bad = [], []
        for label, src in ncx_points:
            fname, _, frag = src.partition("#")
            target = _anchor_target(z, fname, frag) if frag else None
            if not target or target == label:
                excluded.append(label)
            elif SEP not in label:
                e4_bad.append(label)
        add("E4", not e4_bad,
            f"{len(ncx_points)} ncx entries, {len(excluded)} excluded (no differing tgt after the anchor), "
            f"{len(e4_bad)} missing {SEP}" + (f": {e4_bad[:3]}" if e4_bad else ""))
    with zipfile.ZipFile(output) as z:
        pairs2 = [(s_, g_) for s_, g_ in _number_pairs(z) if g_ and len(s_) >= MIN_BLOCK_CHARS]
    lost = [(sorted(_number_tokens(s_) - _number_tokens(g_))[:3], s_[:50]) for s_, g_ in pairs2 if _number_tokens(s_) - _number_tokens(g_)]
    add("N1", not lost, f"{len(pairs2)} blocks, {len(lost)} with a source number missing from the target"
        + (f": {lost[0]}" if lost else ""))
    glosses = Counter(p for s_, g_ in pairs2 for p in set(re.findall(r"\(([^()]{3,60})\)", g_)) if p not in s_)
    repeated = [(p, c) for p, c in glosses.items() if c > 3]
    add("G1", not repeated, f"{len(repeated)} parenthetical glosses added by the translation appear in more than 3 blocks"
        + (f": {sorted(repeated, key=lambda x: -x[1])[:2]}" if repeated else ""))
    placeholder = [l for l in nav_labels + [l for l, _ in ncx_points] if l.split(SEP, 1)[0].strip() in {"", "(untitled)"}]
    add("E5", not placeholder, f"{len(placeholder)} nav/ncx labels whose source side is empty or '(untitled)'"
        + (f": {placeholder[:3]}" if placeholder else ""))
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--book-dir", type=Path, required=True)
    ap.add_argument("--sample", type=int, metavar="N", help="print N fixed-seed pairs as JSON for the judged items, then exit")
    ap.add_argument("--seed", type=int, default=20261114)
    args = ap.parse_args(argv)
    if args.sample:
        print(json.dumps(sample_pairs(args.output, args.book_dir, args.sample, args.seed), ensure_ascii=False, indent=1))
        return 0
    results = run_checks(args.source, args.output, args.book_dir)
    for cid, ok, ev in results:
        print(f"{cid}: {'YES' if ok else 'NO'} - {ev}")
    return 0 if all(ok for _c, ok, _e in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
