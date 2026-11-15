"""Ground-truth derivation for Phase 8 (BUG-017). Run against the ORACLE (main at bb0eb35):

    cd <scratch>/bt-oracle
    PYTHONPATH=. python <repo>/test/golden/derive_nav_label.py > <repo>/test/golden/golden_nav_label.json

Records the oracle's zh-tw output of _nav_display_label for synthetic entries. The "placeholder_*" cases are
the ones BUG-017 changes on purpose (DECISION-018); the others must stay equal. Never regenerate from new code.
"""
import json
from scripts import nav_builder

CASES = {
    "normal_heading": {"id": "i1", "first_heading": "Chapter One", "output_strategy": "translate", "original_idref": "a"},
    "structural_page": {"id": "i2", "first_heading": "Contents", "output_strategy": "translate", "original_idref": "b"},
    "placeholder_with_override": {"id": "i3", "first_heading": "(untitled)", "output_strategy": "translate", "original_idref": "c",
                                  "_translations_extra": {"nav_overrides": {"c": "標籤"}}},
    "untitled_word_with_override": {"id": "i4", "first_heading": "Untitled", "output_strategy": "translate", "original_idref": "d",
                                    "_translations_extra": {"nav_overrides": {"d": "標籤"}}},
    "placeholder_without_label": {"id": "i5", "first_heading": "(untitled)", "output_strategy": "translate", "original_idref": "e"},
    "empty_heading_uses_id": {"id": "i6", "first_heading": "", "output_strategy": "translate", "original_idref": "f"},
}
print(json.dumps({k: nav_builder._nav_display_label(v) for k, v in CASES.items()}, ensure_ascii=False, indent=1))
