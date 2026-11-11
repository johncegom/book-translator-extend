"""Scripted dry run of SKILL.md's Phase 4 path with target_lang=vi on the Alice excerpt.

Inputs are gitignored (runs/alice/). Usage: python docs/tasks/04-skill-file/dry_run.py
Steps follow SKILL.md: init_state(.., 'vi') + save -> build_subagent_prompt(target_lang=state[...])
-> assemble -> audit_suite CLI. No manual fixes between steps.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts import dispatch, state as state_mod  # noqa: E402

HAN = re.compile("[㐀-鿿]")
src_book = ROOT / "runs" / "alice" / "frozen_vi"
work = Path(tempfile.mkdtemp(prefix="dry_run_vi_")) / "alice"
shutil.copytree(src_book, work)
(work / "state.json").unlink()                                   # start from a book with no state

manifest = json.loads((work / "manifest.json").read_text(encoding="utf-8"))
st = state_mod.init_state(ROOT / "runs" / "alice" / "alice.epub", manifest["spine"], "vi")
for cid, entry in st["chapters"].items():
    if entry.get("output_strategy") == "translate" and (work / "chapters" / f"{cid}_translation.txt").exists():
        entry.update(status="done")
state_mod.save(work / "state.json", st)
assert json.loads((work / "state.json").read_text(encoding="utf-8"))["target_lang"] == "vi"
print("state.json target_lang = vi")

glossary = json.loads((work / "glossary.json").read_text(encoding="utf-8"))
html = (work / "chapters" / "item_002.html").read_text(encoding="utf-8")
prompt = dispatch.build_subagent_prompt(
    chapter_label="item_002", book_title="Alice", target_lang=st["target_lang"], glossary=glossary,
    style_sample="", carryover="", chapter_html=html)
assert "Vietnamese" in prompt or "Tiếng Việt" in prompt or "tiếng Việt" in prompt, "no Vietnamese rules in prompt"
print("prompt built: %d chars, Han chars in prompt: %d" % (len(prompt), len(HAN.findall(prompt))))

out = work / "out.epub"
r = subprocess.run([sys.executable, str(ROOT / "scripts" / "assemble.py"), "--book", str(work), "--out", str(out)],
                   capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
print("assemble rc", r.returncode, r.stdout[-300:], r.stderr[-300:])
assert r.returncode == 0 and out.is_file()

r = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_suite.py"), "--source", str(ROOT / "runs" / "alice" / "alice.epub"),
                    "--output", str(out), "--book-dir", str(work)],
                   capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
print("audit_suite rc", r.returncode)
print(r.stdout[-1200:], r.stderr[-300:])

# The excerpt has only 3 translated chapters, so the coverage audit is expected to fail on the rest.
# Check that every failure is in a chapter with no translation file (nothing else is wrong).
translated = {e["src_href"] for e in manifest["spine"]
              if (work / "chapters" / f"{e['id']}_translation.txt").exists()}
failing = set(re.findall(r"- (OEBPS/\S+?\.html): ", r.stdout))
bad = [f for f in failing if any(f.endswith(Path(t).name) for t in translated)]
print("translated chapters:", len(translated), "| failing files:", len(failing), "| failures inside translated chapters:", bad)
assert not bad, bad
print("quality + href + structural audits ran under the vi profile; failures only in untranslated chapters")
print("work dir:", work)
