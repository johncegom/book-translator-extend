"""Phase 2 ground-truth pins for zh-tw behaviour that the Vietnamese work will touch.

Same method as derive.py: ``compute()`` calls the pre-Phase-2 code and
``golden_zh_tw_phase2.json`` is its output run inside a worktree of e0f41b6
(whose scripts/, assets/ and the pinned test files equal bb0eb35 / dac59fe).
The characterization test recomputes it on the current code.

Re-derive (never hand-edit the JSON, never regenerate it from refactored code):

    git worktree add ../bt-oracle2 e0f41b6
    cd ../bt-oracle2
    python <repo>/test/golden/derive_phase2.py > <repo>/test/golden/golden_zh_tw_phase2.json

Groups: glossary_prompt, register_block, resolve_register, resolve_register_override,
resolve_register_rules, subagent_prompts, generic_rules, min_length_ratio, quality_audit.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

REGISTER_STRINGS = [
    "literary plain prose",
    "literary plain prose with fable cadence",
    "LITERARY PLAIN PROSE",
    "商管科普 narrative",
    "商管/社科 narrative，第一人稱保留",
    "學術論述，精確優先",
    "學術論述",
    "narrative",
    "plain",
    "zzz unknown register",
    "x",
    "",
    "   ",
]
OVERRIDE_IDS = ["literary_fiction", "LITERARY_FICTION", " academic_technical ", "non_fiction_narrative", "nope", "", None]
CUSTOM_HINTS = {"registers": [{"id": "x", "register": "foo bar", "subagent_rules": ["R1", "R2"]}, "not-a-dict"]}


def _anchor(register):
    return {"style_anchor": {"register": register}}


def _simplified_epub(path: Path) -> None:
    src = "This is a long English paragraph that clearly needs a translated sibling after it for the audit."
    tgt = "这是一个很长的简体中文翻译，学国应该时这们个经历实来体现进觉党报见远边长万与业东严两临卫。"
    body = f'<p class="src">{src}</p><p class="tgt tgt-zh">{tgt}</p>'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr(
            "META-INF/container.xml",
            '<?xml version="1.0"?><container version="1.0" '
            'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles>'
            '<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>'
            "</rootfiles></container>",
        )
        z.writestr(
            "OEBPS/content.opf",
            '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0"><manifest>'
            '<item id="c1" href="xhtml/c1.xhtml" media-type="application/xhtml+xml"/></manifest>'
            '<spine><itemref idref="c1"/></spine></package>',
        )
        z.writestr("OEBPS/xhtml/c1.xhtml", f"<html><body>{body}</body></html>")


def _id(register):
    return register.get("id") if isinstance(register, dict) else None


def compute() -> dict:
    from scripts import dispatch, glossary
    from scripts import translation_quality_audit as tqa

    g: dict = {}

    prompt = glossary.GLOSSARY_PROMPT
    g["glossary_prompt"] = {
        "text": prompt,
        "sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "rendered": prompt.format(source_lang="English", target_lang="zh-tw", full_text="SAMPLE TEXT"),
        "path_name": glossary.REGISTER_HINTS_PATH.name,
    }

    hints = glossary._load_register_hints()
    g["register_block"] = {
        "block": glossary._REGISTER_HINTS_BLOCK,
        "hints_sha256": hashlib.sha256(json.dumps(hints, ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
        "ids": [h.get("id") for h in hints],
    }

    g["resolve_register"] = {
        repr(r): _id(glossary.resolve_register(_anchor(r))) for r in REGISTER_STRINGS
    }
    g["resolve_register"]["no_style_anchor"] = _id(glossary.resolve_register({}))
    g["resolve_register"]["style_anchor_not_dict"] = _id(glossary.resolve_register({"style_anchor": "x"}))
    g["resolve_register"]["custom_hints_match"] = _id(glossary.resolve_register(_anchor("foo"), CUSTOM_HINTS))
    g["resolve_register"]["custom_hints_no_match"] = _id(glossary.resolve_register(_anchor("zzz"), CUSTOM_HINTS))
    g["resolve_register"]["custom_hints_registers_not_list"] = _id(
        glossary.resolve_register(_anchor("foo"), {"registers": "x"}))

    g["resolve_register_override"] = {repr(i): _id(glossary.resolve_register_override(i)) for i in OVERRIDE_IDS}

    rules = {}
    for r in REGISTER_STRINGS:
        rules[f"glossary|{r!r}"] = glossary.resolve_register_rules(_anchor(r), fallback_rules=["FALLBACK"])
    for i in OVERRIDE_IDS:
        rules[f"override|{i!r}"] = glossary.resolve_register_rules(
            _anchor("literary plain prose"), register_override=i, fallback_rules=["FALLBACK"])
    rules["no_fallback_no_match"] = glossary.resolve_register_rules(_anchor("zzz unknown register"))
    g["resolve_register_rules"] = rules

    g["generic_rules"] = list(dispatch.GENERIC_SUBAGENT_RULES)

    prompts = {}
    base = dict(chapter_label="item_003", book_title="Alice", target_lang="zh-tw",
                style_sample="風格範例。", carryover="前情提要。", chapter_html="<p>Hello world, this is Alice.</p>")
    cases = {
        "no_anchor": {"terms": {"Alice": "愛麗絲"}},
        "literary": {"terms": {"Alice": "愛麗絲"}, **_anchor("literary plain prose")},
        "nonfiction": {"terms": {"Alice": "愛麗絲"}, **_anchor("商管/社科 narrative，第一人稱保留")},
        "academic": {"terms": {"Alice": "愛麗絲"}, **_anchor("學術論述，精確優先")},
        "unmatched": {"terms": {"Alice": "愛麗絲"}, **_anchor("zzz unknown register")},
    }
    for name, gloss in cases.items():
        text = dispatch.build_subagent_prompt(glossary=gloss, **base)
        prompts[name] = {"sha256": hashlib.sha256(text.encode()).hexdigest(), "text": text}
    for rid in ["literary_fiction", "non_fiction_narrative", "academic_technical", "nope"]:
        text = dispatch.build_subagent_prompt(glossary=cases["no_anchor"], register_override=rid, **base)
        prompts[f"override_{rid}"] = {"sha256": hashlib.sha256(text.encode()).hexdigest(), "text": text}
    text = dispatch.build_subagent_prompt(glossary=cases["literary"], custom_instructions="CUSTOM RULE TEXT", **base)
    prompts["custom_instructions"] = {"sha256": hashlib.sha256(text.encode()).hexdigest(), "text": text}
    g["subagent_prompts"] = prompts

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ratios = {}
        for label, gloss in {
            "literary": _anchor("literary plain prose"),
            "nonfiction": _anchor("商管/社科 narrative，第一人稱保留"),
            "academic": _anchor("學術論述，精確優先"),
            "unmatched": _anchor("zzz unknown register"),
            "no_anchor": {},
        }.items():
            d = root / label
            d.mkdir()
            (d / "glossary.json").write_text(json.dumps(gloss, ensure_ascii=False), encoding="utf-8")
            ratios[label] = tqa._min_length_ratio_from_book_dir(d)
        g["min_length_ratio"] = ratios

        epub = root / "simplified.epub"
        _simplified_epub(epub)
        ok, failures = tqa.audit(epub)
        ok2, failures2, warnings2 = tqa.audit_with_warnings(epub)
        g["quality_audit"] = {"ok": ok, "failures": failures, "ok_with_warnings": ok2,
                              "failures_with_warnings": failures2, "warnings": warnings2}
    return g


if __name__ == "__main__":
    sys.path.insert(0, os.getcwd())
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(compute(), ensure_ascii=False, indent=1, sort_keys=True))
