"""Ground-truth derivation for Phase 7 (BUG-016). Run against the ORACLE (main at bb0eb35):

    git worktree add <scratch>/bt-oracle bb0eb35
    cd <scratch>/bt-oracle
    PYTHONPATH=. python <repo>/test/golden/derive_ncx.py > <repo>/test/golden/golden_ncx_sections.json

The oracle predates the profile: patch_toc_ncx(ncx_xml, entries) takes no profile and no chapter HTML.
This records its zh-tw output for the fixture. There is no oracle for vi (ordinary test-first). Never regenerate it from the new code.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ncx_fixture import ENTRIES, NCX
from scripts import nav_builder

out = {"zh-tw": nav_builder.patch_toc_ncx(NCX, ENTRIES)}
print(json.dumps(out, ensure_ascii=False, indent=1))
