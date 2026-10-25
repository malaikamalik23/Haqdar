from pathlib import Path

from textpath import text_path
from build_logo import seal_group, GREEN, GREEN_D, GOLD

OUT = Path(__file__).resolve().parents[2] / "web"

INK, GRAY, LIGHT, LINE = "#16211c", "#c9d2cc", "#e1e7e3", "#d3dbd5"
TINT, AMBER_T, AMBER, RED, REDT = "#e1f0e8", "#fdf0d9", "#d9a441", "#a6261d", "#fbe6e3"


def wrap(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">'
            f"<title>{label}</title>{body}</svg>\n")


def bar(x_right, y, w, color, h=11):
    return f'<rect x="{x_right - w:.1f}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{color}"/>'


def line(x_right, y, segs, gap=8):
    out, x = [], x_right
    for w, c in segs:
        out.append(bar(x, y, w, c))
        x -= w + gap
    return "".join(out)


def star(cx, cy, r, color):
    k = r * 0.28
    return (f'<path d="M{cx} {cy-r} L{cx+k} {cy-k} L{cx+r} {cy} L{cx+k} {cy+k} L{cx} {cy+r} '
            f'L{cx-k} {cy+k} L{cx-r} {cy} L{cx-k} {cy-k}Z" fill="{color}"/>')


def check_circle(cx, cy, r, fill=GREEN):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'
            f'<path d="M{cx-r*0.45:.1f} {cy+r*0.02:.1f} L{cx-r*0.1:.1f} {cy+r*0.38:.1f} L{cx+r*0.5:.1f} {cy-r*0.36:.1f}" '
            f'fill="none" stroke="#fff" stroke-width="{r*0.24:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')


# ---------------- Hero ----------------
b = [f'<circle cx="330" cy="268" r="236" fill="{TINT}"/>',
     f'<circle cx="548" cy="64" r="26" fill="{TINT}"/>',
     f'<circle cx="60" cy="470" r="18" fill="{TINT}"/>',
     star(600, 96, 17, GOLD), star(54, 52, 10, GREEN)]

# Back sheet: the confusing notice
nx, ny, nw, nh, r_edge = 36, 60, 280, 370, 292
b.append('<g transform="rotate(-5 176 245)">')
b.append(f'<rect x="{nx+7}" y="{ny+9}" width="{nw}" height="{nh}" rx="14" fill="#0d6b4a" opacity=".12"/>')
b.append(f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="14" fill="#fff" stroke="{LINE}" stroke-width="2"/>')
b.append(f'<rect x="{nx}" y="{ny}" width="{nw}" height="54" rx="14" fill="{INK}"/>')
b.append(f'<rect x="{nx}" y="{ny+30}" width="{nw}" height="24" fill="{INK}"/>')
d, w, h = text_path("نوٹس", wght=700, height=28)
d, w, h = text_path("نوٹس", wght=700, height=28, ox=r_edge - w, oy=ny + 13)
b.append(f'<path d="{d}" fill="#fff"/>')
rows = [
    [(200, GRAY)], [(220, GRAY)], [(60, GRAY), (90, INK), (50, GRAY)], [(210, GRAY)],
    [(150, AMBER)], [(190, GRAY)], [(40, GRAY), (120, INK), (60, GRAY)], [(200, GRAY)], [(90, GRAY)],
]
y = ny + 82
for segs in rows:
    if segs[0][1] == AMBER:
        b.append(f'<rect x="{nx+22}" y="{y-8}" width="{nw-44}" height="27" rx="8" fill="{AMBER_T}"/>')
    b.append(line(r_edge, y, segs))
    y += 27
b.append("</g>")

# Front card: the clear answer
cx0, cy0, cw, ch, c_edge = 318, 104, 290, 392, 584
b.append('<g transform="rotate(3 463 288)">')
b.append(f'<rect x="{cx0+7}" y="{cy0+9}" width="{cw}" height="{ch}" rx="18" fill="#0d6b4a" opacity=".16"/>')
b.append(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="18" fill="#fff" stroke="{GREEN}" stroke-width="2.5"/>')
b.append(f'<rect x="{c_edge-150}" y="{cy0+22}" width="150" height="38" rx="19" fill="{GREEN}"/>')
d, w, h = text_path("اقدامات", wght=700, height=20)
d, w, h = text_path("اقدامات", wght=700, height=20, ox=c_edge - 75 - w / 2, oy=cy0 + 31)
b.append(f'<path d="{d}" fill="#fff"/>')
y = cy0 + 96
for i in range(3):
    b.append(check_circle(c_edge - 17, y + 17, 17))
    b.append(bar(c_edge - 46, y + 3, 150 - i * 10, GRAY, 12))
    b.append(bar(c_edge - 46, y + 24, 105 - i * 8, LIGHT, 12))
    if i < 2:
        b.append(f'<rect x="{cx0+24}" y="{y+52}" width="{cw-48}" height="2" rx="1" fill="#e6ebe7"/>')
    y += 70
b.append(f'<rect x="{cx0+24}" y="{y-10}" width="{cw-48}" height="2" rx="1" fill="#e6ebe7"/>')
b.append(seal_group(cx0 + 56, y + 40, 25))
b.append(f'<rect x="{c_edge-150}" y="{y+28}" width="150" height="26" rx="13" fill="{TINT}"/>')
b.append(bar(c_edge - 16, y + 36, 100, "#9ec3b0", 10))
b.append("</g>")

# Stamp over the notice
sx, sy = 124, 392
b.append(f'<g transform="rotate(-13 {sx} {sy})">')
b.append(f'<rect x="{sx-70}" y="{sy-30}" width="140" height="60" rx="10" fill="#fff" fill-opacity=".92" stroke="{RED}" stroke-width="4"/>')
b.append(f'<rect x="{sx-63}" y="{sy-23}" width="126" height="46" rx="6" fill="none" stroke="{RED}" stroke-width="1.6"/>')
d, w, h = text_path("مشکوک", wght=800, height=30)
d, w, h = text_path("مشکوک", wght=800, height=30, ox=sx - w / 2, oy=sy - h / 2)
b.append(f'<path d="{d}" fill="{RED}"/>')
b.append("</g>")
open(OUT / "hero.svg", "w", encoding="utf-8").write(wrap(640, 520, "".join(b),
        "A confusing notice with hidden personal details and a suspicious stamp, next to a clear step-by-step answer"))

# ---------------- Spot: ask ----------------
b = [f'<circle cx="90" cy="90" r="84" fill="{TINT}"/>', star(142, 34, 9, GOLD)]
b.append(f'<path d="M26 40 h86 a14 14 0 0 1 14 14 v44 a14 14 0 0 1 -14 14 h-52 l-20 18 v-18 h-14 a14 14 0 0 1 -14 -14 v-44 a14 14 0 0 1 14 -14z" fill="#fff" stroke="{GREEN}" stroke-width="4" stroke-linejoin="round"/>')
d, w, h = text_path("سوال", wght=700, height=30)
d, w, h = text_path("سوال", wght=700, height=30, ox=76 - w / 2, oy=56)
b.append(f'<path d="{d}" fill="{GREEN_D}"/>')
b.append(f'<path d="M80 126 h58 a12 12 0 0 1 12 12 v10 a12 12 0 0 1 -12 12 h-8 v14 l-16 -14 h-34 a12 12 0 0 1 -12 -12 v-10 a12 12 0 0 1 12 -12z" fill="{GREEN}"/>')
b.append(check_circle(115, 143, 11, fill="#fff").replace('stroke="#fff"', f'stroke="{GREEN}"'))
open(OUT / "spot-ask.svg", "w", encoding="utf-8").write(wrap(180, 180, "".join(b), "A question and a checked answer"))

# ---------------- Spot: notice ----------------
b = [f'<circle cx="90" cy="90" r="84" fill="{TINT}"/>', star(30, 40, 9, GOLD)]
b.append(f'<g transform="rotate(-6 80 90)"><rect x="40" y="26" width="92" height="124" rx="10" fill="#fff" stroke="{LINE}" stroke-width="3"/>')
b.append(f'<rect x="40" y="26" width="92" height="28" rx="10" fill="{INK}"/><rect x="40" y="42" width="92" height="12" fill="{INK}"/>')
for i, (wdt, col) in enumerate([(62, GRAY), (70, GRAY), (40, INK), (66, GRAY), (50, GRAY)]):
    b.append(bar(122, 66 + i * 15, wdt, col, 8))
b.append("</g>")
b.append(f'<circle cx="108" cy="112" r="34" fill="#fff" fill-opacity=".55" stroke="{GREEN}" stroke-width="8"/>')
b.append(f'<path d="M133 137 L160 164" stroke="{GREEN}" stroke-width="12" stroke-linecap="round"/>')
b.append(check_circle(108, 112, 15))
open(OUT / "spot-notice.svg", "w", encoding="utf-8").write(wrap(180, 180, "".join(b), "A notice under a magnifying glass"))
print("art built")