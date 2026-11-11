"""Bilingual XHTML rewriting for assembled EPUB spine items."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

try:  # pragma: no cover - import style depends on caller
    from .content_blocks import walk_text_nodes
    from .lang_profile import ZH_TW
except ImportError:  # pragma: no cover
    from content_blocks import walk_text_nodes  # type: ignore
    from lang_profile import ZH_TW  # type: ignore

# The zh-tw label tables live in lang_profile; these names stay as aliases (the
# same dict objects) for existing importers.
STRUCTURAL_LABELS_ZH_TW = ZH_TW.structural_labels
CONTENTS_LINK_LABELS_ZH_TW = ZH_TW.contents_labels


def _aup_note_template(notice: str) -> str:
    """HTML for the AUP-refused note; ``{reason}`` is filled in later."""
    return (
        '<div class="aup-refused-note" '
        'style="border-left: 4px solid #c44; padding: 0.5em 1em; margin: 1em 0; '
        'background: #fff4f0; font-size: 0.9em;">'
        '<strong>' + notice + '</strong><br/>'
        "This chapter was refused by the translation LLM's usage policy; "
        "the original English is preserved verbatim. "
        '<em>Reason: {reason}</em>'
        '</div>'
    )


_AUP_NOTE_HTML_TEMPLATE = _aup_note_template(ZH_TW.aup_refused_notice)


def insert_bilingual(
    src_html: str,
    entry: dict,
    translations: list[str],
    *,
    chapter_status: str | None = None,
    aup_reason: str | None = None,
    profile=None,
) -> tuple[str, list[str]] | str:
    """Per-paragraph interleave src + translation. If chapter_status='aup_refused',
    return source HTML with a visible annotation block prepended; do not insert
    translation siblings."""
    profile = ZH_TW if profile is None else profile
    if chapter_status == "aup_refused":
        return _emit_aup_refused_chapter(src_html, aup_reason or "", profile)
    soup = BeautifulSoup(src_html, "html.parser")
    promoted_ids = {id(h) for h in _promote_header_headings(soup)}
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    # 內建 contents 連結標籤只在該頁沒有自己的譯文時才補；否則會和逐段譯文
    # 疊成「Dedication ｜ 獻辭」+「獻詞」兩份中文。
    if entry.get("role") == "contents" and entry.get("output_strategy") != "translate":
        _bilingualize_contents_links(soup, profile)
    nodes = _text_nodes_for_bilingual(soup)
    # Promoted header headings (chapter numbers / part names) were stripped by
    # dispatch's extract_blocks, so no translation segment exists for them. Pair
    # body translations against non-promoted nodes only; promoted headings get a
    # nav/structural label (if any) without consuming a body slot.
    body_nodes = [n for n in nodes if id(n) not in promoted_ids]
    warnings: list[str] = []
    aligned_body = _align_translations(body_nodes, translations, entry, profile)
    if entry.get("output_strategy") == "translate" and len(body_nodes) != len(aligned_body):
        warnings.append(
            f"{entry.get('translation_id') or entry['id']}: paragraph count mismatch "
            f"(src_text={len(body_nodes)} tgt={len(translations)}); pairing available paragraphs"
        )

    body_index = 0
    for node in nodes:
        source_text = _clean_text(node.get_text(" ", strip=True))
        if not source_text:
            continue
        if id(node) in promoted_ids:
            # A promoted header heading that is the chapter title (e.g.
            # "CHAPTER 1 The Past") takes the nav-override label, since dispatch
            # stripped it and it is translated nowhere else. A bare chapter number
            # ("1") instead gets only an exact structural label — using the nav
            # override there would duplicate the title that already renders on the
            # separate in-body title heading.
            if _is_bare_chapter_number(source_text):
                candidate = _exact_translation_for_text(source_text, entry, profile) or None
            else:
                candidate = _heading_zh_label(source_text, entry, profile) or None
        else:
            candidate = aligned_body[body_index] if body_index < len(aligned_body) else None
            body_index += 1
        if _looks_like_identifier(source_text) and not candidate:
            continue
        _add_class(node, "src")
        if candidate:
            translated = str(candidate)
            unpaired = False
        else:
            translated = _fallback_translation(source_text, entry, profile)
            unpaired = entry.get("output_strategy") == "translate"
        translated = _ensure_han_translation(translated, source_text)
        if not translated:
            continue
        target = soup.new_tag("p")
        target["class"] = _target_classes(node, unpaired=unpaired, profile=profile)
        target.string = translated
        node.insert_after(target)
    return str(soup), warnings


def _emit_aup_refused_chapter(src_html: str, reason: str, profile=None) -> str:
    """Inject an AUP-refused notice at the top of <body> and return the result."""
    from bs4 import BeautifulSoup
    safe_reason = (reason or "(no reason recorded)").replace("<", "&lt;").replace(">", "&gt;")
    profile = ZH_TW if profile is None else profile
    note = _aup_note_template(profile.aup_refused_notice).format(reason=safe_reason)
    soup = BeautifulSoup(src_html, "html.parser")
    body = soup.find("body")
    if body is None:
        return note + src_html
    body.insert(0, BeautifulSoup(note, "html.parser"))
    return str(soup)


def _promote_header_headings(soup: BeautifulSoup) -> list:
    """Move h1-h6 out of header into the body root before stripping decor.

    Returns the promoted heading nodes. dispatch's ``extract_blocks`` strips
    ``<header>`` entirely, so these headings were never translated; the caller
    must not let them consume a body translation slot.
    """
    body = soup.find("body")
    if body is None:
        return []
    promoted: list = []
    insert_at = 0
    heading_tags = ["h1", "h2", "h3", "h4", "h5", "h6"]
    for header in list(soup.find_all("header")):
        for heading in list(header.find_all(heading_tags)):
            heading.extract()
            body.insert(insert_at, heading)
            insert_at += 1
            promoted.append(heading)
        header.decompose()
    return promoted


def _is_bare_chapter_number(text: str) -> bool:
    """True for a standalone chapter-number heading like "1" or roman "IV"."""
    stripped = text.strip()
    return bool(
        re.fullmatch(r"[0-9]{1,4}", stripped)
        or re.fullmatch(r"[IVXLCDM]{1,8}", stripped)
    )


def _bilingualize_contents_links(soup: BeautifulSoup, profile=None) -> None:
    profile = ZH_TW if profile is None else profile
    for link in soup.find_all("a"):
        text = _clean_text(link.get_text(" ", strip=True))
        if "｜" in text:
            continue
        zh = profile.contents_labels.get(text)
        if zh:
            link.string = f"{text} ｜ {zh}"


def _align_translations(nodes: list, translations: list[str], entry: dict, profile=None) -> list[str | None]:
    if entry.get("output_strategy") != "translate":
        return []
    if len(nodes) == len(translations):
        return list(translations)
    if len(nodes) == len(translations) + 1 and nodes:
        first = _clean_text(nodes[0].get_text(" ", strip=True))
        if first.lower() in {"introduction", "chapter"}:
            return [_fallback_translation(first, entry, profile), *translations]
        if nodes[0].name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            zh = _heading_zh_label(first, entry, profile)
            if zh and zh != first:
                return [zh, *translations]
    return list(translations)


def _text_nodes_for_bilingual(soup: BeautifulSoup) -> list:
    return list(walk_text_nodes(soup))


def _target_classes(node, *, unpaired: bool = False, profile=None) -> list[str]:
    profile = ZH_TW if profile is None else profile
    classes = ["tgt", profile.target_class]
    for cls in node.get("class", []):
        if cls not in classes and cls != "src":
            classes.append(cls)
    if unpaired:
        classes.append("unpaired")
    return classes


def _add_class(node, cls: str) -> None:
    classes = list(node.get("class", []))
    if cls not in classes:
        classes.append(cls)
    node["class"] = classes


def _fallback_translation(text: str, entry: dict, profile=None) -> str:
    exact = _exact_translation_for_text(text, entry, profile)
    if exact:
        return exact
    return ""


def _exact_translation_for_text(text: str, entry: dict, profile=None) -> str:
    profile = ZH_TW if profile is None else profile
    extra = _translations_extra_by_exact_text(entry)
    exact = extra.get(text)
    if exact:
        return str(exact)
    exact = profile.structural_labels.get(text)
    if exact:
        return exact
    return ""


def _translations_extra_by_exact_text(entry: dict) -> dict:
    extra = entry.get("_translations_extra")
    if not isinstance(extra, dict):
        return {}
    by_exact_text = extra.get("by_exact_text")
    if not isinstance(by_exact_text, dict):
        return {}
    return by_exact_text


def _ensure_han_translation(translated: str, source_text: str) -> str:
    """Preserve the model result; never manufacture Han to satisfy an audit.

    Whether an already non-Han result is legitimate is decided later from its
    paragraph location and recorded with a reason in source_only.json.
    ``source_text`` remains in the signature for compatibility with callers.
    """
    del source_text
    return translated


def _looks_like_identifier(text: str) -> bool:
    stripped = text.strip()
    return bool(
        re.fullmatch(r"[._A-Za-z0-9-]{6,}", stripped)
        and ("_" in stripped or re.search(r"\d", stripped))
    )


def _heading_zh_label(first: str, entry: dict, profile=None) -> str:
    profile = ZH_TW if profile is None else profile
    override = _translations_extra_nav_overrides(entry).get(str(entry.get("original_idref") or ""))
    if override:
        return str(override)
    exact = profile.structural_labels.get(first)
    if exact:
        return exact
    contents = profile.contents_labels.get(first)
    if contents:
        return contents
    contents_style = _clean_text(first.replace("\n", " "))
    if contents_style != first:
        exact = profile.structural_labels.get(contents_style) or profile.contents_labels.get(contents_style)
        if exact:
            return exact
    return _exact_translation_for_text(contents_style, entry, profile) or _fallback_translation(first, entry, profile)


def _translations_extra_nav_overrides(entry: dict) -> dict:
    extra = entry.get("_translations_extra")
    if not isinstance(extra, dict):
        return {}
    nav_overrides = extra.get("nav_overrides")
    if not isinstance(nav_overrides, dict):
        return {}
    return nav_overrides


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
