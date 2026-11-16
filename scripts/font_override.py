"""Make a finished bilingual EPUB show Vietnamese correctly, replacing a font only if it must be replaced.

The source book's fonts (Adobe Caslon Pro, DIN Next ...) often lack the Latin Extended Additional letters
Vietnamese needs (ạ ế ợ ữ ...). Mixing a second font in for single letters makes words look odd, so the
rule is per font, not per letter: a font that supports every Vietnamese letter is kept as the book has
it; any other font is replaced as a whole by Be Vietnam Pro, in every text style that uses it.

How a font is judged:
* embedded in the EPUB: its file is read and every Vietnamese letter must have a glyph;
* named but not embedded (the book says "Adobe Caslon Pro" but ships no file): it cannot be checked, so
  it counts as unsupported, unless it is on KNOWN_VIETNAMESE_FONTS (fonts known to carry Vietnamese);
* a font-family list is kept only if every named font in it is supported; otherwise Be Vietnam Pro goes
  first in the list and the rest stays as the fallback.

If every font is supported the EPUB is left as it is and no font is added.

It runs after `assemble.py`, so the shared assembly code is untouched:

    python -m scripts.font_override --epub in.epub --out out.epub [--fonts assets/fonts/BeVietnamPro]

Running it again on its own output changes nothing.
"""
from __future__ import annotations

import argparse
import posixpath
import re
import shutil
import struct
import zipfile
from pathlib import Path
from typing import Callable

FAMILY = "Be Vietnam Pro"
FONT_FILES = (
    "BeVietnamPro-Regular.ttf",
    "BeVietnamPro-Italic.ttf",
    "BeVietnamPro-Bold.ttf",
    "BeVietnamPro-BoldItalic.ttf",
)
LICENSE_FILE = "OFL-BeVietnamPro.txt"
DEFAULT_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "BeVietnamPro"
MARKER = "/* book-translator: Vietnamese font */"
END_MARKER = "/* end book-translator: Vietnamese font */"
OLD_MARKER = "/* book-translator: Vietnamese font override */"  # first version: put a rule at the end of the file
# second version: companion faces for single letters (looked odd inside a word); removed on the next run
INTERIM_MARKER = "/* book-translator: Vietnamese letters fallback */"
INTERIM_END = "/* end book-translator: Vietnamese letters fallback */"

# The precomposed Vietnamese letters, upper and lower case.
VIETNAMESE: frozenset[int] = frozenset(
    ord(c)
    for c in "ĂÂĐÊÔƠƯăâđêôơưÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ"
    "áàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
)

# Fonts that carry Vietnamese wherever they are installed. A font named in a book's CSS but absent from the
# reader falls through to the next one, so this is a statement about the font, not about the reader.
KNOWN_VIETNAMESE_FONTS = frozenset({
    "georgia", "times new roman", "times", "arial", "verdana", "tahoma", "trebuchet ms", "segoe ui",
    "calibri", "cambria", "be vietnam pro",
})
_CSS_KEYWORDS = {"inherit", "initial", "unset", "revert"}
_GENERIC = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-serif", "ui-sans-serif", "ui-monospace"}


# ---- reading a font file (sfnt cmap, formats 4 and 12) ----

def _cmap_subtables(data: bytes) -> list[bytes]:
    num_tables = struct.unpack(">H", data[4:6])[0]
    for i in range(num_tables):
        rec = 12 + 16 * i
        if data[rec:rec + 4] == b"cmap":
            offset, length = struct.unpack(">II", data[rec + 8:rec + 16])
            cmap = data[offset:offset + length]
            n = struct.unpack(">H", cmap[2:4])[0]
            subs = []
            for j in range(n):
                platform, _enc, sub_off = struct.unpack(">HHI", cmap[4 + 8 * j:12 + 8 * j])
                if platform in (0, 3):
                    subs.append(cmap[sub_off:])
            return subs
    return []


def _covers_format4(sub: bytes, codes: set[int]) -> set[int]:
    seg = struct.unpack(">H", sub[6:8])[0] // 2
    end = struct.unpack(f">{seg}H", sub[14:14 + 2 * seg])
    base = 16 + 2 * seg
    start = struct.unpack(f">{seg}H", sub[base:base + 2 * seg])
    delta = struct.unpack(f">{seg}h", sub[base + 2 * seg:base + 4 * seg])
    ro_pos = base + 4 * seg
    range_off = struct.unpack(f">{seg}H", sub[ro_pos:ro_pos + 2 * seg])
    found = set()
    for c in codes:
        if c > 0xFFFF:
            continue
        for i in range(seg):
            if end[i] >= c:
                if start[i] <= c:
                    if range_off[i] == 0:
                        glyph = (c + delta[i]) & 0xFFFF
                    else:
                        addr = ro_pos + 2 * i + range_off[i] + 2 * (c - start[i])
                        glyph = struct.unpack(">H", sub[addr:addr + 2])[0]
                        if glyph:
                            glyph = (glyph + delta[i]) & 0xFFFF
                    if glyph:
                        found.add(c)
                break
    return found


def _covers_format12(sub: bytes, codes: set[int]) -> set[int]:
    groups = struct.unpack(">L", sub[12:16])[0]
    found = set()
    for g in range(groups):
        start, end, glyph = struct.unpack(">LLL", sub[16 + 12 * g:28 + 12 * g])
        found.update(c for c in codes if start <= c <= end and glyph + (c - start))
    return found


def supported(data: bytes, codepoints) -> set[int]:
    """The code points that the font file has a glyph for. Anything unreadable counts as not supported."""
    codes = set(codepoints)
    found: set[int] = set()
    try:
        for sub in _cmap_subtables(data):
            fmt = struct.unpack(">H", sub[:2])[0]
            if fmt == 4:
                found |= _covers_format4(sub, codes)
            elif fmt == 12:
                found |= _covers_format12(sub, codes)
    except (struct.error, IndexError, ValueError):
        return set()
    return found


# ---- stylesheet edits ----

def _base_faces(rel_font_dir: str) -> str:
    specs = (("normal", 400, 0), ("italic", 400, 1), ("normal", 700, 2), ("italic", 700, 3))
    return "".join(
        f'@font-face {{ font-family: "{FAMILY}"; font-style: {style}; font-weight: {weight}; '
        f'src: url("{rel_font_dir}/{FONT_FILES[i]}"); }}\n'
        for style, weight, i in specs
    )


_FACE_RE = re.compile(r"@font-face\s*\{[^}]*\}")
_FAMILY_RE = re.compile(r"(font-family\s*:\s*)([^;}]+)")


def _own_faces(css: str):
    """(family, url) of each @font-face of the book itself."""
    for m in _FACE_RE.finditer(css):
        props = dict((k.lower(), v.strip().strip("\"'")) for k, v in re.findall(r"([\w-]+)\s*:\s*([^;]+);?", m.group(0).split("{", 1)[1]))
        url = re.search(r"url\(\s*[\"']?([^\"')]+)", props.get("src", ""))
        family = props.get("font-family", "")
        if url and family and family != FAMILY:
            yield family, url.group(1)


def verified_families(css: str, css_dir: str, read: Callable[[str], bytes | None],
                      coverage: Callable[[bytes], set[int]]) -> set[str]:
    """Lower-case names of the fonts that support Vietnamese: the known list plus embedded fonts
    whose every face has a glyph for every Vietnamese letter."""
    state: dict[str, bool] = {}
    for family, url in _own_faces(css):
        data = read(posixpath.normpath(posixpath.join(css_dir, url)))
        ok = data is not None and VIETNAMESE <= coverage(data)
        state[family.lower()] = state.get(family.lower(), True) and ok
    return {name for name, ok in state.items() if ok} | set(KNOWN_VIETNAMESE_FONTS)


def restyle(css: str, verified: set[str]) -> str:
    """Put Be Vietnam Pro first in each font-family list that has a font not known to support Vietnamese.

    @font-face rules are left alone, so are monospace lists and CSS keywords (inherit ...), and a list
    of only supported fonts is kept as written. A Be Vietnam Pro entry left by an earlier run is moved.
    """
    def fix(m: re.Match) -> str:
        value = m.group(2)
        trailing = value[len(value.rstrip()):]
        body = value.rstrip()
        important = ""
        im = re.search(r"\s*!important\s*$", body, re.I)
        if im:
            important, body = im.group(0), body[:im.start()]
        names = [n.strip() for n in body.split(",") if n.strip()]
        bare = [n.strip("\"' ").lower() for n in names]
        if not names or "monospace" in bare or any(b in _CSS_KEYWORDS for b in bare):
            return m.group(0)
        kept = [n for n, b in zip(names, bare) if b != FAMILY.lower()]
        named = [b for b in bare if b not in _GENERIC and b != FAMILY.lower()]
        if named and all(b in verified for b in named):
            return m.group(0) if len(kept) == len(names) else m.group(1) + ", ".join(kept) + important + trailing
        return m.group(1) + ", ".join([f'"{FAMILY}"'] + kept) + important + trailing

    out, pos = [], 0
    for face in _FACE_RE.finditer(css):
        out.append(_FAMILY_RE.sub(fix, css[pos:face.start()]))
        out.append(face.group(0))
        pos = face.end()
    out.append(_FAMILY_RE.sub(fix, css[pos:]))
    return "".join(out)


def _strip_old_blocks(css: str) -> str:
    for start, end in ((MARKER, END_MARKER), (INTERIM_MARKER, INTERIM_END)):
        css = re.sub(re.escape(start) + r".*?" + re.escape(end) + r"\n?", "", css, flags=re.S)
    if OLD_MARKER in css:
        css = css[:css.index(OLD_MARKER)].rstrip("\n") + "\n"
    return css


# ---- the whole step ----

def _opf_path(z: zipfile.ZipFile) -> str:
    m = re.search(r'full-path="([^"]+)"', z.read("META-INF/container.xml").decode("utf-8"))
    if not m:
        raise ValueError("no OPF path in META-INF/container.xml")
    return m.group(1)


def _css_hrefs(opf: str) -> list[str]:
    hrefs = []
    for m in re.finditer(r"<item\b[^>]*>", opf):
        if 'media-type="text/css"' in m.group(0):
            h = re.search(r'href="([^"]+)"', m.group(0))
            if h:
                hrefs.append(h.group(1))
    return hrefs


def _add_manifest_items(opf: str) -> str:
    items = ""
    for i, name in enumerate(FONT_FILES):
        if f'href="fonts/{name}"' not in opf:
            items += f'<item href="fonts/{name}" id="bevietnampro-{i}" media-type="font/ttf"/>'
    if f'href="fonts/{LICENSE_FILE}"' not in opf:
        items += f'<item href="fonts/{LICENSE_FILE}" id="bevietnampro-licence" media-type="text/plain"/>'
    return opf.replace("</manifest>", items + "</manifest>", 1) if items else opf


def apply(src: Path, out: Path, font_dir: Path = DEFAULT_FONT_DIR,
          coverage: Callable[[bytes], set[int]] | None = None) -> dict:
    """Write `out`: `src` with every font that does not support Vietnamese replaced by Be Vietnam Pro.

    Returns {"changed": bool, "unverified": [embedded fonts that lack letters], "verified": [...]}.
    """
    src, out, font_dir = Path(src), Path(out), Path(font_dir)
    cover = coverage or (lambda data: supported(data, VIETNAMESE))
    needed = list(FONT_FILES) + [LICENSE_FILE]
    missing_files = [n for n in needed if not (font_dir / n).is_file()]
    if missing_files:
        raise FileNotFoundError(f"missing in {font_dir}: {', '.join(missing_files)}")
    report: dict = {"changed": False, "unverified": [], "verified": []}
    with zipfile.ZipFile(src) as zin:
        opf_name = _opf_path(zin)
        opf_dir = posixpath.dirname(opf_name)
        opf = zin.read(opf_name).decode("utf-8")
        css_paths = {posixpath.normpath(posixpath.join(opf_dir, h)) for h in _css_hrefs(opf)}
        font_prefix = posixpath.join(opf_dir, "fonts")
        have = set(zin.namelist())
        read = lambda path: zin.read(path) if path in have else None  # noqa: E731

        new_css: dict[str, str] = {}
        needs_font = False
        for path in sorted(css_paths & have):
            original = zin.read(path).decode("utf-8")
            stripped = _strip_old_blocks(original)
            css_dir = posixpath.dirname(path)
            verified = verified_families(stripped, css_dir, read, cover)
            restyled = restyle(stripped, verified)
            own = {f for f, _u in _own_faces(stripped)}
            report["verified"] += sorted(f for f in own if f.lower() in verified)
            report["unverified"] += sorted(f for f in own if f.lower() not in verified)
            # a list that names Be Vietnam Pro needs the font and its @font-face, on a rerun too
            if re.search(r"font-family\s*:[^;}]*" + re.escape(FAMILY), restyled):
                needs_font = True
                rel = posixpath.relpath(font_prefix, css_dir)
                restyled = restyled.rstrip("\n") + f"\n{MARKER}\n{_base_faces(rel)}{END_MARKER}\n"
            if restyled != original:
                new_css[path] = restyled
        report["changed"] = needs_font
        if not new_css and not needs_font:
            if src.resolve() != out.resolve():
                shutil.copyfile(src, out)
            return report

        tmp = out.with_name(out.name + ".tmp")
        with zipfile.ZipFile(tmp, "w") as zout:
            zout.writestr("mimetype", zin.read("mimetype"), compress_type=zipfile.ZIP_STORED)
            for info in zin.infolist():
                if info.filename == "mimetype":
                    continue
                data = zin.read(info.filename)
                if info.filename == opf_name and needs_font:
                    data = _add_manifest_items(opf).encode("utf-8")
                elif info.filename in new_css:
                    data = new_css[info.filename].encode("utf-8")
                zout.writestr(info.filename, data, compress_type=zipfile.ZIP_DEFLATED)
            if needs_font:
                for name in needed:
                    target = posixpath.join(font_prefix, name)
                    if target not in have:
                        zout.writestr(target, (font_dir / name).read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
    tmp.replace(out)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Replace fonts that lack Vietnamese letters with Be Vietnam Pro in a bilingual EPUB.")
    ap.add_argument("--epub", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fonts", type=Path, default=DEFAULT_FONT_DIR)
    args = ap.parse_args(argv)
    report = apply(args.epub, args.out, args.fonts)
    print(args.out)
    print("replaced by Be Vietnam Pro:" if report["changed"] else "no change: every font supports Vietnamese")
    print("  embedded fonts that lack letters:", ", ".join(report["unverified"]) or "none")
    print("  embedded fonts that are complete:", ", ".join(report["verified"]) or "none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
