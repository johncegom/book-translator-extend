# Task: Phase 10 — Font override for Vietnamese glyph coverage

Status: in review. Code is on PR #34. This doc was written after the code, so the DoD below needs your approval before the phase can be marked done.

## Why

Source fonts (Adobe Caslon Pro, DIN Next) often lack the letters Vietnamese needs (ạ ế ợ ữ). A reader device then falls back per letter and words look uneven.

## Scope

In: new `scripts/font_override.py` (runs after `assemble.py`, shared assembly code untouched); `test/test_font_override.py`; bundled Be Vietnam Pro fonts and its OFL license in `assets/fonts/BeVietnamPro/`.
Out: wiring it into `SKILL.md` or `assemble.py`; zh-tw; fonts other than Be Vietnam Pro.

## Design (as built)

Rule is per font, not per letter. An embedded font is kept only if it has a glyph for every Vietnamese letter. A font named but not embedded counts as unsupported unless it is on `KNOWN_VIETNAMESE_FONTS`. A font-family list is kept only if every font in it is supported; otherwise Be Vietnam Pro goes first. If every font is supported, the EPUB is not changed. Running it twice changes nothing.

## Definition of Done

- [ ] Unsupported fonts are replaced as a whole; supported fonts are kept.
- [ ] A book whose fonts are all supported is left byte-for-byte unchanged in content (no font added).
- [ ] Second run on its own output changes nothing.
- [x] Real check on one vi book: user opened *The Personal MBA* output on 2026-11-17 and confirmed it renders correctly.
- [ ] `pytest -q` passes; CI green on ubuntu 3.10/3.12 and windows 3.12.
- [x] DECISIONS entry: DECISION-019.
- [ ] Ledger Evidence cell links the PR.

## Test Plan

- `pytest -q test/test_font_override.py`
- `pytest -q`
- Real book: `python -m scripts.font_override --epub in.epub --out out.epub`

## Progress notes

- 2026-11-16: code and tests done (20 passed together with grade tests). Full suite, CI and the real-book check not yet done.
- 2026-11-17: user checked the *The Personal MBA* output, fine. DECISION-019 added. Open: full suite, CI, approval, PR link in ledger.
