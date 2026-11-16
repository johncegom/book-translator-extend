"""scripts/font_override.py: replace a whole font by Be Vietnam Pro only when it does not fully support Vietnamese."""
from __future__ import annotations

import zipfile
from pathlib import Path

from scripts import font_override as fo

OPF = (
    '<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0"><manifest>'
    '<item href="css/s.css" id="css" media-type="text/css"/>'
    '<item href="fonts/Old.otf" id="old" media-type="font/otf"/>'
    '<item href="a.xhtml" id="a" media-type="application/xhtml+xml"/>'
    '</manifest><spine><itemref idref="a"/></spine></package>'
)
OLD_FACE = '@font-face {\nfont-family: "Old";\nfont-style: italic;\nfont-weight: bold;\nsrc : url("../fonts/Old.otf");\n}\n'
CSS = OLD_FACE + 'p { font-family: "Adobe Caslon Pro", "Georgia", serif; }\nh1 { font-family: "Old", sans-serif; }\ncode { font-family: monospace; }\n'

FULL = lambda data: set(fo.VIETNAMESE)  # noqa: E731  a font that has every Vietnamese letter
PARTIAL = lambda data: set(fo.VIETNAMESE) - {0x1EA0, 0x1EA1}  # noqa: E731  a font missing two of them


def _epub(path: Path, css: str = CSS) -> Path:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", '<container><rootfiles><rootfile full-path="OEBPS/b.opf"/></rootfiles></container>')
        z.writestr("OEBPS/b.opf", OPF)
        z.writestr("OEBPS/css/s.css", css)
        z.writestr("OEBPS/fonts/Old.otf", b"old")
        z.writestr("OEBPS/a.xhtml", "<html><body><p>x</p></body></html>")
    return path


def _fonts(tmp_path: Path) -> Path:
    d = tmp_path / "fonts"
    d.mkdir(exist_ok=True)
    for n in fo.FONT_FILES:
        (d / n).write_bytes(b"ttf-" + n.encode())
    (d / fo.LICENSE_FILE).write_text("OFL text", encoding="utf-8")
    return d


def _css_of(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        return z.read("OEBPS/css/s.css").decode("utf-8")


# ---- reading a font file ----

def test_be_vietnam_pro_covers_every_vietnamese_letter_and_not_han():
    data = (fo.DEFAULT_FONT_DIR / "BeVietnamPro-Regular.ttf").read_bytes()
    assert fo.supported(data, fo.VIETNAMESE) == fo.VIETNAMESE
    assert fo.supported(data, {0x4E2D}) == set()  # a Han character is not in it


def test_unreadable_font_data_supports_nothing_it_cannot_prove():
    assert fo.supported(b"not a font", fo.VIETNAMESE) == set()


# ---- which fonts count as supporting Vietnamese ----

def test_an_embedded_font_is_verified_only_if_every_face_covers_all_letters():
    css = OLD_FACE
    z = {"OEBPS/fonts/Old.otf": b"old"}
    assert fo.verified_families(css, "OEBPS/css", z.get, FULL) == {"old"} | fo.KNOWN_VIETNAMESE_FONTS
    assert "old" not in fo.verified_families(css, "OEBPS/css", z.get, PARTIAL)
    assert "old" not in fo.verified_families(css, "OEBPS/css", {}.get, FULL)  # a face whose file is missing is unverified


# ---- stylesheet edits ----

def test_a_list_with_an_unverified_font_gets_be_vietnam_pro_first():
    out = fo.restyle(CSS, {"georgia"})
    assert 'p { font-family: "Be Vietnam Pro", "Adobe Caslon Pro", "Georgia", serif; }' in out
    assert 'h1 { font-family: "Be Vietnam Pro", "Old", sans-serif; }' in out
    assert "code { font-family: monospace; }" in out  # monospace is left alone
    assert out.startswith(OLD_FACE)  # @font-face rules are left alone
    assert fo.restyle(out, {"georgia"}) == out  # idempotent


def test_a_list_of_only_verified_fonts_is_untouched():
    css = 'p { font-family: "Old", Georgia, serif; }'
    assert fo.restyle(css, {"old", "georgia"}) == css


def test_a_list_from_an_older_run_is_normalised():
    css = 'p { font-family: "Adobe Caslon Pro", "Georgia", "Be Vietnam Pro", serif; }'
    assert fo.restyle(css, {"georgia"}) == 'p { font-family: "Be Vietnam Pro", "Adobe Caslon Pro", "Georgia", serif; }'


# ---- the whole step ----

def test_apply_replaces_unverified_fonts_whole_and_embeds_the_font(tmp_path):
    out = tmp_path / "out.epub"
    report = fo.apply(_epub(tmp_path / "in.epub"), out, _fonts(tmp_path), coverage=PARTIAL)
    css = _css_of(out)
    assert css.startswith(OLD_FACE)
    assert 'p { font-family: "Be Vietnam Pro", "Adobe Caslon Pro", "Georgia", serif; }' in css
    assert "unicode-range" not in css and "!important" not in css  # never a mix inside a word
    assert css.count("@font-face") == 1 + len(fo.FONT_FILES)
    assert report["changed"] is True and "Old" in report["unverified"]
    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert names[0] == "mimetype" and z.getinfo("mimetype").compress_type == zipfile.ZIP_STORED
        for n in fo.FONT_FILES:
            assert f"OEBPS/fonts/{n}" in names
        assert f"OEBPS/fonts/{fo.LICENSE_FILE}" in names
        opf = z.read("OEBPS/b.opf").decode("utf-8")
        assert all(f'href="fonts/{n}"' in opf for n in fo.FONT_FILES)
        assert z.read("OEBPS/fonts/Old.otf") == b"old"


def test_apply_changes_nothing_when_every_font_already_supports_vietnamese(tmp_path):
    css = OLD_FACE + 'p { font-family: "Old", Georgia, serif; }\n'
    src, out = _epub(tmp_path / "in.epub", css), tmp_path / "out.epub"
    report = fo.apply(src, out, _fonts(tmp_path), coverage=FULL)
    assert report["changed"] is False
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(out) as b:
        assert sorted(a.namelist()) == sorted(b.namelist())  # no font files added
        assert a.read("OEBPS/css/s.css") == b.read("OEBPS/css/s.css")
        assert a.read("OEBPS/b.opf") == b.read("OEBPS/b.opf")


def test_apply_is_idempotent_and_replaces_older_blocks(tmp_path):
    first, second = tmp_path / "o1.epub", tmp_path / "o2.epub"
    older = f'\n{fo.OLD_MARKER}\nbody {{ font-family: "Be Vietnam Pro" !important; }}\n'
    interim = (f'\n{fo.INTERIM_MARKER}\n@font-face {{ font-family: "Old"; unicode-range: U+1EA0; '
               f'src: url("../fonts/BeVietnamPro-Bold.ttf"); }}\n{fo.INTERIM_END}\n')
    fo.apply(_epub(tmp_path / "in.epub", CSS + interim + older), first, _fonts(tmp_path), coverage=PARTIAL)
    assert fo.OLD_MARKER not in _css_of(first) and "!important" not in _css_of(first)
    assert fo.INTERIM_MARKER not in _css_of(first) and "unicode-range" not in _css_of(first)
    fo.apply(first, second, tmp_path / "fonts", coverage=PARTIAL)
    assert _css_of(first) == _css_of(second)
    with zipfile.ZipFile(first) as a, zipfile.ZipFile(second) as b:
        assert a.read("OEBPS/b.opf") == b.read("OEBPS/b.opf")
        assert sorted(a.namelist()) == sorted(b.namelist())
