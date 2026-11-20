# Task: Phase 14 — Audit command lines print UTF-8 on Windows (BUG-021)

Status: awaiting approval of the DoD and Test Plan.

Related: BUG-021. The coverage audit's crash on a PASS comes from the success line added in Phase 12 (PR #41, "adjacent translations (Tiếng Việt)"); it was hidden because every real check of it ran with `PYTHONIOENCODING=utf-8`.

## Why

On Windows, Python's stdout uses the legacy code page (cp1252 here, also when piped or redirected). Book text has letters it cannot encode, so `print` raises `UnicodeEncodeError`. Measured 2026-11-20 on *The Personal MBA*, without `PYTHONIOENCODING`:

| Command line | Result |
|---|---|
| `grade_checks` (checks) | prints A1 to E2, then crashes on "｜" in E3; exit 1; E3 to E5, N1 and G1 never print |
| `grade_checks --sample N` | crashes on the first Vietnamese letter, 0 lines printed; the judged checks J1, J4, JC cannot run |
| `bilingual_coverage_audit` | crashes on the PASS line ("Tiếng Việt"); exit 1 for a book that passes |
| `translation_quality_audit`, `audit_suite` | fine on this book (their output was ASCII); the same crash is possible when a failure line shows book text |

`PYTHONUTF8=1` or `PYTHONIOENCODING=utf-8` avoids it.

## Scope

In: one small helper that switches stdout and stderr to UTF-8 when they are not, called first in `main()` of `grade_checks.py`, `bilingual_coverage_audit.py`, `translation_quality_audit.py` and `audit_suite.py` (the four that print book text or a language name); new tests; `SKILL.md` untouched.
Out: `structural_audit.py` and `href_resolve_audit.py` (no book text printed; not read in full, to confirm); changing what is printed; `errors="replace"` (it would corrupt the `--sample` JSON that Grade judges).

## Design

`scripts/console.py` (or a function in an existing shared module, to decide while reading imports): `use_utf8_output()` calls `stream.reconfigure(encoding="utf-8")` on `sys.stdout` and `sys.stderr` when the stream has `reconfigure` and its encoding is not UTF-8. It does nothing otherwise (pytest capture objects, already-UTF-8 streams). Called only from `main()`, never at import, so importing a module does not change the process.

## Definition of Done

- [ ] Tests first, seen red: run `bilingual_coverage_audit.main` on a small vi book and `grade_checks --sample` in a subprocess with `PYTHONIOENCODING=cp1252` (forces the legacy code page on any OS, including CI): exit 0, no traceback, UTF-8 bytes on stdout. A unit test for the helper on a cp1252 stream, and one that it does nothing on a stream without `reconfigure`.
- [ ] Existing tests are unedited and pass; `pytest -q` passes; CI green on ubuntu 3.10/3.12 and windows 3.12.
- [ ] Real check on *The Personal MBA* with no `PYTHONIOENCODING`: `grade_checks` prints all 14 lines, `--sample 2` prints JSON, the coverage audit prints PASS and exits 0.
- [ ] BUG-021 FIXED in the table and the entry, with the PR link; ledger row links the PR.

## Test Plan

- `pytest -q test/test_console_utf8.py` (new)
- `pytest -q`
- Real book, three commands, run with `unset PYTHONIOENCODING PYTHONUTF8`.

## Progress notes

- 2026-11-20: drafted after measuring the four command lines. Advise does not apply (no profile field, no detector or threshold change).
