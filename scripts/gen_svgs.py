"""Generate the animated SVGs for the GitHub profile README.

Text is shaped with HarfBuzz (kerning + Inter's cv11/ss01/ss03, same as the site) and
converted to outlines, so nothing depends on fonts loading inside an <img>.
Usage: python gen_svgs.py <inter-variable.woff2> <out_dir>
"""
import io
import sys

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

FONT, OUT = sys.argv[1], sys.argv[2]
FEATURES = {"kern": True, "liga": True, "cv11": True, "ss01": True, "ss03": True}

THEMES = {
    "dark": dict(card="#000000", hi="#ffffff", lo="#a1a1a6", text="#f5f5f7", muted="#86868b",
                 hair="rgba(255,255,255,0.14)", glow="rgba(80,100,160,0.34)", glow2="rgba(40,40,70,0.10)",
                 sheen="rgba(255,255,255,0.95)", lo2="#8e8e93"),
    "light": dict(card="#f5f5f7", hi="#1d1d1f", lo="#6e6e73", text="#1d1d1f", muted="#6e6e73",
                  hair="rgba(0,0,0,0.10)", glow="rgba(255,255,255,0.95)", glow2="rgba(255,255,255,0.35)",
                  sheen="rgba(255,255,255,0.85)", lo2="#86868b"),
}
EASE = "cubic-bezier(0.22,1,0.36,1)"

_fonts = {}


def font(weight):
    if weight not in _fonts:
        tt = TTFont(FONT)
        inst = instantiateVariableFont(tt, {"wght": weight})
        buf = io.BytesIO()
        inst.flavor = None
        inst.save(buf)
        data = buf.getvalue()
        face = hb.Face(data)
        hbf = hb.Font(face)
        tt2 = TTFont(io.BytesIO(data))
        _fonts[weight] = (hbf, tt2.getGlyphSet(), tt2["head"].unitsPerEm, tt2.getGlyphOrder())
    return _fonts[weight]


def shape(text, weight, size, track=0.0):
    """Returns ([(glyph_name, x, y_offset)], width) in px for a single line."""
    hbf, _, upm, order = font(weight)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbf, buf, FEATURES)
    s = size / upm
    x, out = 0.0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((order[info.codepoint], x + pos.x_offset * s, pos.y_offset * s))
        x += pos.x_advance * s + track * size
    return out, x - track * size


def glyph_path(name, weight, size, x, baseline):
    _, gs, upm, _ = font(weight)
    s = size / upm
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    gs[name].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
    return pen.getCommands()


def text_paths(text, weight, size, x0, baseline, track=0.0):
    """One <path> per glyph; returns (list of path-d strings, width)."""
    glyphs, w = shape(text, weight, size, track)
    ds = []
    for name, x, yo in glyphs:
        d = glyph_path(name, weight, size, x0 + x, baseline - yo)
        ds.append(d)
    return ds, w


def svg(w, h, body, css, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{label}"><title>{label}</title><style>{css}</style>{body}</svg>')


# ---------------------------------------------------------------- header
def header(t):
    W, H = 1280, 400
    name, eyebrow = "Asaf Arusi.", "AI Software Engineer at Dig AI"
    nsize, esize = 150, 24
    _, nw = shape(name, 600, nsize, -0.045)
    _, ew = shape(eyebrow, 600, esize, -0.01)
    nx, ny = (W - nw) / 2, 282
    ex, ey = (W - ew) / 2, 142
    name_ds, _ = text_paths(name, 600, nsize, nx, ny, -0.045)
    eye_ds, _ = text_paths(eyebrow, 600, esize, ex, ey, -0.01)

    chars = "".join(
        f'<path class="ch" style="animation-delay:{0.35 + i * 0.07:.2f}s" d="{d}"/>'
        for i, d in enumerate(name_ds) if d
    )
    clip = "".join(f'<path d="{d}"/>' for d in name_ds if d)
    css = f"""
.card{{fill:{t['card']}}}
.edge{{fill:none;stroke:{t['hair']};stroke-width:1.5;stroke-dasharray:1;stroke-dashoffset:1;animation:trace 2.6s {EASE} .1s forwards}}
.glow{{transform-box:fill-box;transform-origin:50% 50%;opacity:0;animation:glowin 3s ease .2s forwards,breathe 9s ease-in-out 3.2s infinite alternate}}
.eye{{fill:{t['muted']};opacity:0;animation:fade 1.2s {EASE} .15s forwards}}
.ch{{fill:url(#g);opacity:0;transform-box:fill-box;transform-origin:50% 100%;animation:rise 1.7s {EASE} both}}
.sheen{{animation:sweep 8s cubic-bezier(.65,0,.35,1) 2.6s infinite;transform:translateX(-520px)}}
.cue{{animation:cue 2.6s cubic-bezier(.65,0,.35,1) 2s infinite;transform:translateY(-44px)}}
@keyframes trace{{to{{stroke-dashoffset:0}}}}
@keyframes glowin{{to{{opacity:1}}}}
@keyframes breathe{{from{{transform:scale(1) translate(0,0)}}to{{transform:scale(1.18) translate(-30px,12px)}}}}
@keyframes fade{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes rise{{0%{{opacity:0;transform:translateY(70px) scaleY(1.25);filter:blur(14px)}}55%{{opacity:1}}100%{{opacity:1;transform:none;filter:blur(0)}}}}
@keyframes sweep{{0%{{transform:translateX(-520px)}}32%,100%{{transform:translateX({W + 200}px)}}}}
@keyframes cue{{0%{{transform:translateY(-44px)}}55%,100%{{transform:translateY(44px)}}}}
"""
    body = f"""
<defs>
  <linearGradient id="g" x1="0" y1="{ny - nsize * 0.75:.0f}" x2="0" y2="{ny + 6}" gradientUnits="userSpaceOnUse">
    <stop offset="0.3" stop-color="{t['hi']}"/><stop offset="1" stop-color="{t['lo']}"/>
  </linearGradient>
  <radialGradient id="r"><stop offset="0" stop-color="{t['glow']}"/><stop offset="0.55" stop-color="{t['glow2']}"/><stop offset="1" stop-color="{t['glow2']}" stop-opacity="0"/></radialGradient>
  <linearGradient id="s" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="{t['sheen']}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <linearGradient id="c" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t['muted']}" stop-opacity="0"/><stop offset="1" stop-color="{t['muted']}"/></linearGradient>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath>
  <clipPath id="name">{clip}</clipPath>
  <clipPath id="cuebox"><rect x="{W / 2 - 1}" y="{H - 76}" width="2" height="44"/></clipPath>
</defs>
<g clip-path="url(#card)">
  <rect class="card" width="{W}" height="{H}"/>
  <ellipse class="glow" cx="{W / 2}" cy="{H * 0.48}" rx="560" ry="300" fill="url(#r)"/>
  <g class="eye">{''.join(f'<path d="{d}"/>' for d in eye_ds if d)}</g>
  {chars}
  <g clip-path="url(#name)"><rect class="sheen" x="0" y="0" width="260" height="{H}" fill="url(#s)"/></g>
  <g clip-path="url(#cuebox)"><rect class="cue" x="{W / 2 - 0.5}" y="{H - 76}" width="1" height="44" fill="url(#c)"/></g>
</g>
<rect class="edge" x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="27.5" pathLength="1"/>
"""
    return svg(W, H, body, css, "Asaf Arusi. AI Software Engineer at Dig AI.")


# ---------------------------------------------------------------- statement
def statement(t):
    W = 1280
    text = ("I build products end to end. The interface you touch, the API behind it, "
            "the data underneath, and the AI that ties it all together.")
    size, track, lh = 52, -0.03, 1.16
    space = shape(" ", 600, size, track)[1] + track * size
    words = text.split(" ")
    lines, cur, cw = [], [], 0.0
    for w in words:
        ww = shape(w, 600, size, track)[1]
        add = ww if not cur else cw + space + ww
        if cur and add > W:
            lines.append(cur)
            cur, cw = [w], ww
        else:
            cur.append(w)
            cw = add
    lines.append(cur)
    H = int(len(lines) * size * lh + size * 0.35)
    parts, i = [], 0
    for li, line in enumerate(lines):
        x = 0.0
        base = size * 0.95 + li * size * lh
        for w in line:
            ds, ww = text_paths(w, 600, size, x, base, track)
            parts.append(f'<g class="w" style="animation-delay:{0.3 + i * 0.13:.2f}s">'
                         + "".join(f'<path d="{d}"/>' for d in ds if d) + "</g>")
            x += ww + space
            i += 1
    css = f"""
.w{{fill:{t['text']};transform-box:fill-box;animation:lit 12s {EASE} infinite both}}
@keyframes lit{{
  0%{{opacity:.14;transform:translateY(10px);filter:blur(3px)}}
  9%{{opacity:1;transform:none;filter:blur(0)}}
  78%{{opacity:1;transform:none;filter:blur(0)}}
  90%,100%{{opacity:.14;transform:translateY(10px);filter:blur(3px)}}
}}
"""
    return svg(W, H, "".join(parts), css, text)


# ---------------------------------------------------------------- stack ticker
def ticker(t):
    W, H = 1280, 72
    items = ["TypeScript", "React", "Node.js", "PostgreSQL", "Python", "C", "C++", "Java", "AWS", "GCP"]
    size, gap = 30, 64
    x, parts = 0.0, []
    for _ in range(2):
        for it in items:
            ds, w = text_paths(it, 500, size, x, 46, -0.02)
            parts.append("".join(f'<path d="{d}"/>' for d in ds if d))
            x += w + gap / 2
            parts.append(f'<circle cx="{x:.1f}" cy="36" r="2.5" class="dot"/>')
            x += gap / 2
    loop = x / 2
    css = f"""
.row{{fill:{t['text']};animation:slide 38s linear infinite}}
.dot{{fill:{t['muted']}}}
.in{{opacity:0;animation:fade 1.6s {EASE} .2s forwards}}
@keyframes slide{{from{{transform:translateX(0)}}to{{transform:translateX(-{loop:.1f}px)}}}}
@keyframes fade{{to{{opacity:1}}}}
"""
    body = f"""
<defs>
  <linearGradient id="f" x1="0" x2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.14" stop-color="#fff"/>
    <stop offset="0.86" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#f)"/></mask>
</defs>
<g class="in" mask="url(#m)"><g class="row">{''.join(parts)}</g></g>
"""
    return svg(W, H, body, css, "Stack: " + ", ".join(items))


# ---------------------------------------------------------------- closer
def closer(t):
    W, H = 1280, 340
    text, size = "Let’s build something.", 112
    _, w = shape(text, 600, size, -0.05)
    x, base = (W - w) / 2, 205
    ds, _ = text_paths(text, 600, size, x, base, -0.05)
    sub = "asafarusi.co.il"
    _, sw = shape(sub, 500, 26, -0.01)
    sds, _ = text_paths(sub, 500, 26, (W - sw) / 2, 272, -0.01)
    glyphs = "".join(f'<path d="{d}"/>' for d in ds if d)
    css = f"""
.card{{fill:{t['card']}}}
.edge{{fill:none;stroke:{t['hair']};stroke-width:1.5}}
.t{{fill:url(#g);transform-box:fill-box;transform-origin:50% 60%;animation:zoom 2.4s {EASE} .3s both}}
.sub{{fill:{t['muted']};animation:fade 1.4s {EASE} 1.3s both}}
.glow{{transform-box:fill-box;transform-origin:50% 50%;animation:breathe 10s ease-in-out infinite alternate}}
.sheen{{animation:sweep 8s cubic-bezier(.65,0,.35,1) 3s infinite;transform:translateX(-520px)}}
@keyframes zoom{{from{{opacity:0;transform:scale(.72) translateY(30px);filter:blur(18px)}}to{{opacity:1;transform:none;filter:blur(0)}}}}
@keyframes fade{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
@keyframes breathe{{from{{transform:scale(1)}}to{{transform:scale(1.2) translate(24px,-10px)}}}}
@keyframes sweep{{0%{{transform:translateX(-520px)}}32%,100%{{transform:translateX({W + 200}px)}}}}
"""
    body = f"""
<defs>
  <linearGradient id="g" x1="0" y1="{base - size * 0.75:.0f}" x2="0" y2="{base + size * 0.22:.0f}" gradientUnits="userSpaceOnUse">
    <stop offset="0.3" stop-color="{t['hi']}"/><stop offset="1" stop-color="{t['lo2']}"/>
  </linearGradient>
  <radialGradient id="r"><stop offset="0" stop-color="{t['glow']}"/><stop offset="0.55" stop-color="{t['glow2']}"/><stop offset="1" stop-color="{t['glow2']}" stop-opacity="0"/></radialGradient>
  <linearGradient id="s" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="{t['sheen']}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="28"/></clipPath>
  <clipPath id="txt">{glyphs}</clipPath>
</defs>
<g clip-path="url(#card)">
  <rect class="card" width="{W}" height="{H}"/>
  <ellipse class="glow" cx="{W / 2}" cy="{H * 0.55}" rx="520" ry="260" fill="url(#r)"/>
  <g class="t">{glyphs}<g clip-path="url(#txt)"><rect class="sheen" x="0" y="0" width="260" height="{H}" fill="url(#s)"/></g></g>
  <g class="sub">{''.join(f'<path d="{d}"/>' for d in sds if d)}</g>
</g>
<rect class="edge" x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="27.5"/>
"""
    return svg(W, H, body, css, "Let’s build something. asafarusi.co.il")


for theme, t in THEMES.items():
    for name, fn in [("header", header), ("statement", statement), ("stack", ticker), ("contact", closer)]:
        out = f"{OUT}/{name}-{theme}.svg"
        data = fn(t)
        with open(out, "w") as f:
            f.write(data)
        print(f"{out}  {len(data) / 1024:.1f} KB")
