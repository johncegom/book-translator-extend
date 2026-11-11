"""Language profiles: everything that depends on the target language.

Phase 1 registers only ``zh-tw``. The zh-tw data below was moved verbatim from
``bilingual_rewriter``, ``nav_builder``, ``dispatch`` and friends; the golden
tests in ``test/golden`` pin it against the pre-refactor code (bb0eb35).

``get_profile`` is strict. ``resolve_profile`` is the lenient lookup the
existing entry points use: it casefolds and falls back to zh-tw for any
unregistered code (DECISION-006). Compare profiles by ``.code``, never by
identity or ``==`` (the package can be imported under two module names).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Callable

_ZH_TW_STRUCTURAL_LABELS = {
    'Contents': '目錄',
    'Introduction': '導論',
    'PART I': '第一部',
    'PART II': '第二部',
    'Acknowledgments': '致謝',
    'Notes': '註釋',
    'About the Author': '關於作者',
    'What’s next on your reading list?': '你的下一本書想讀什麼？',
    "What's next on your reading list?": '你的下一本書想讀什麼？',
    'Discover your next great read!': '發現下一本精彩好書！',
    'Get personalized book picks and up-to-date news about this author.': '取得為你量身推薦的書單，以及這位作者的最新消息。',
    'Sign up now.': '立即註冊。',
    'GO TO NOTE REFERENCE IN TEXT': '返回正文註記位置',
}

_ZH_TW_CONTENTS_LABELS = {
    'Contents': '目錄',
    'Cover': '封面',
    'Title Page': '書名頁',
    'Copyright': '版權頁',
    'Dedication': '獻辭',
    'PART I': '第一部',
    'PART II': '第二部',
    'Acknowledgments': '致謝',
    'Notes': '註釋',
    'About the Author': '關於作者',
}

_ZH_TW_PREFIX_LABELS = (
    ('praise for ', '各界讚譽'),
    ('advance praise for ', '各界讚譽'),
    ('also by ', '作者其他著作'),
)

_ZH_TW_PROMPT_RULES = 'Traditional Chinese rule: If the target is 台灣繁體中文, output must use\n繁體中文 (Traditional Chinese / Taiwan locale). 禁止使用任何簡體字。\n常見錯誤對照：『学』→『學』、『为』→『為』、『这』→『這』、\n『们』→『們』、『实』→『實』、『时』→『時』、『国』→『國』。'

_ZH_TW_DEFAULT_CUSTOM_INSTRUCTIONS = 'If the target is 台灣繁體中文, use 台灣用語 (e.g. 「軟體」not「软件」, 「網路」not「网络」). Avoid 翻譯腔. Prefer short sentences over four-character literary clichés.'

_ZH_TW_GLOSSARY_SLOTS = {
    'target_note': '台灣繁體中文 if target is zh-tw — use 台灣用語',
    'name_advice': 'transliteration for English names unless a Chinese\n    convention exists',
    'title_rules': 'Use standard 台灣繁中 for structural pages (Cover, Title Page,\n    Copyright, Dedication, Introduction, Acknowledgments, Notes, About the\n    Author, Index, Glossary). For numbered chapters, use clean readable forms\n    such as "第一章　人工智慧的過去、現在與未來"; for part dividers, use forms\n    such as "第一部　RenAIssance 的基礎".',
    'avoid_example': '翻譯腔',
}

_ZH_TW_GENERIC_RULES = (
    "Plain target-language prose. Match the glossary's prefer/avoid lists in style_anchor.",
    "Glossary names are mandatory — use them verbatim throughout.",
    "Preserve paragraph boundaries and source paragraph count.",
    "Avoid 翻譯腔. Default to short, natural sentences over literary clichés.",
)

# The zh-tw "is this already target-language text" detector (U+4E00-U+9FFF).
HAN_RE = re.compile(r"[\u4e00-\u9fff]")


def _zh_tw_is_target_text(text: str) -> bool:
    """True when text contains any CJK Han character (U+4E00-U+9FFF)."""
    return bool(HAN_RE.search(text))


@dataclass(frozen=True)
class LanguageProfile:
    code: str
    long_name: str
    html_lang: str
    target_class: str
    structural_labels: dict[str, str]
    contents_labels: dict[str, str]
    prefix_labels: tuple[tuple[str, str], ...]
    footnote_label: str  # contains "{n}"
    bilingual_edition_label: str
    aup_refused_notice: str
    prompt_rules: str
    default_custom_instructions: str
    is_target_text: Callable[[str], bool]
    register_hints_file: str  # bare filename under assets/
    glossary_prompt_slots: dict[str, str]  # target_note, name_advice, title_rules, avoid_example; no braces
    generic_rules: tuple[str, ...]  # subagent rules used when no register matches
    simplified_gate: bool  # True: flag Simplified Chinese characters in the target text


ZH_TW = LanguageProfile(
    code="zh-tw",
    long_name='台灣繁體中文',
    html_lang="zh-Hant",
    target_class="tgt-zh",
    structural_labels=_ZH_TW_STRUCTURAL_LABELS,
    contents_labels=_ZH_TW_CONTENTS_LABELS,
    prefix_labels=_ZH_TW_PREFIX_LABELS,
    footnote_label="註腳 {n}",
    bilingual_edition_label="中英對照",
    aup_refused_notice='本章因 LLM 政策拒答，保留原文未譯',
    prompt_rules=_ZH_TW_PROMPT_RULES,
    default_custom_instructions=_ZH_TW_DEFAULT_CUSTOM_INSTRUCTIONS,
    is_target_text=_zh_tw_is_target_text,
    register_hints_file="register_hints.json",
    glossary_prompt_slots=_ZH_TW_GLOSSARY_SLOTS,
    generic_rules=_ZH_TW_GENERIC_RULES,
    simplified_gate=True,
)

# --- Vietnamese ---------------------------------------------------------------
# Wording follows docs/tasks/02-profile-vi/TASK.md (provenance table); several terms
# are accepted as temporary.

_VI_STRUCTURAL_LABELS = {
    "Contents": "Mục lục",
    "Introduction": "Lời nói đầu",
    "PART I": "Phần I",
    "PART II": "Phần II",
    "Acknowledgments": "Lời cảm ơn",
    "Notes": "Chú thích",
    "About the Author": "Về tác giả",
    "What’s next on your reading list?": "Bạn sẽ đọc gì tiếp theo?",
    "What's next on your reading list?": "Bạn sẽ đọc gì tiếp theo?",
    "Discover your next great read!": "Khám phá cuốn sách hay tiếp theo của bạn!",
    "Get personalized book picks and up-to-date news about this author.": (
        "Nhận gợi ý sách dành riêng cho bạn và tin tức mới nhất về tác giả này."
    ),
    "Sign up now.": "Đăng ký ngay.",
    "GO TO NOTE REFERENCE IN TEXT": "QUAY LẠI VỊ TRÍ GHI CHÚ TRONG VĂN BẢN",
}

_VI_CONTENTS_LABELS = {
    "Contents": "Mục lục",
    "Cover": "Bìa",
    "Title Page": "Trang tiêu đề",
    "Copyright": "Bản quyền",
    "Dedication": "Lời đề tặng",
    "PART I": "Phần I",
    "PART II": "Phần II",
    "Acknowledgments": "Lời cảm ơn",
    "Notes": "Chú thích",
    "About the Author": "Về tác giả",
}

_VI_PREFIX_LABELS = (
    ("praise for ", "Lời khen ngợi"),
    ("advance praise for ", "Lời khen ngợi"),
    ("also by ", "Cùng tác giả"),
)

_VI_PROMPT_RULES = (
    "Vietnamese rule: If the target is Tiếng Việt, write standard Vietnamese with full "
    "diacritics in Unicode NFC. Keep the original spelling of personal names and place "
    "names unless the glossary gives a Vietnamese form. Prefer natural, idiomatic "
    "Vietnamese over word-for-word rendering. Use Vietnamese punctuation and quotation "
    "marks consistently."
)

_VI_DEFAULT_CUSTOM_INSTRUCTIONS = (
    "Translate for a Vietnamese general reader. Keep sentences natural; avoid "
    "translationese (câu dịch từng chữ)."
)

_VI_GLOSSARY_SLOTS = {
    "target_note": "Tiếng Việt if target is vi — use natural, standard Vietnamese",
    "name_advice": "keep the original spelling of personal and place names; do not transliterate",
    "title_rules": (
        "Use standard Vietnamese for structural pages (Cover, Title Page,\n"
        "    Copyright, Dedication, Introduction, Acknowledgments, Notes, About the\n"
        "    Author, Index, Glossary). For numbered chapters, use clean readable forms\n"
        '    such as "Chương 1: Rơi xuống hang thỏ"; for part dividers, use forms\n'
        '    such as "Phần I: Nền tảng".'
    ),
    "avoid_example": "dịch từng chữ",
}

_VI_GENERIC_RULES = (
    "Plain target-language prose. Match the glossary's prefer/avoid lists in style_anchor.",
    "Glossary names are mandatory — use them verbatim throughout.",
    "Preserve paragraph boundaries and source paragraph count.",
    "Avoid translationese (dịch từng chữ). Default to short, natural sentences over literary clichés.",
)

# Letters distinctive to Vietnamese: ă đ ơ ư ĩ ũ (either case) and the tone-marked vowels
# U+1EA0-U+1EF9. Letters shared with French/Portuguese (à á â ã è é ê ì í ò ó ô õ ù ú) do not
# count, so "café" or "crêpe" is not Vietnamese. Thresholds for mixed text and short
# paragraphs are Phase 3's job.
_VI_DISTINCTIVE_RE = re.compile(
    "[ăđơưĩũĂĐƠƯĨŨẠ-ỹ]"
)


def _vi_is_target_text(text: str) -> bool:
    """True when the NFC-normalised text contains a letter distinctive to Vietnamese."""
    return bool(_VI_DISTINCTIVE_RE.search(unicodedata.normalize("NFC", text)))


VI = LanguageProfile(
    code="vi",
    long_name="Tiếng Việt",
    html_lang="vi",
    target_class="tgt-vi",
    structural_labels=_VI_STRUCTURAL_LABELS,
    contents_labels=_VI_CONTENTS_LABELS,
    prefix_labels=_VI_PREFIX_LABELS,
    footnote_label="Chú thích {n}",
    bilingual_edition_label="Song ngữ Anh–Việt",
    aup_refused_notice="Chương này bị từ chối dịch do chính sách của LLM; giữ nguyên bản gốc, chưa dịch",
    prompt_rules=_VI_PROMPT_RULES,
    default_custom_instructions=_VI_DEFAULT_CUSTOM_INSTRUCTIONS,
    is_target_text=_vi_is_target_text,
    register_hints_file="register_hints.vi.json",
    glossary_prompt_slots=_VI_GLOSSARY_SLOTS,
    generic_rules=_VI_GENERIC_RULES,
    simplified_gate=False,
)

_REGISTRY: dict[str, LanguageProfile] = {ZH_TW.code: ZH_TW, VI.code: VI}


def get_profile(code: str) -> LanguageProfile:
    """Strict lookup (casefolded). Raises ValueError for an unregistered code."""
    try:
        return _REGISTRY[str(code).strip().casefold()]
    except KeyError:
        raise ValueError(f"no language profile registered for {code!r}") from None


def resolve_profile(code: str | None) -> LanguageProfile:
    """Lenient lookup: casefold, and fall back to zh-tw for any unregistered code."""
    return _REGISTRY.get(str(code or "").strip().casefold(), ZH_TW)
