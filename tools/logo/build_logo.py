import math
from pathlib import Path

from textpath import text_path

OUT = Path(__file__).resolve().parents[2] / "web"

GREEN, GREEN_D, INK_G, GOLD, MUTED = "#0d6b4a", "#0a5239", "#0b4d37", "#f0c14b", "#56635c"


def scallop(cx, cy, R, a, n, pts=360):
    out = []
    for i in range(pts):
        t = 2 * math.pi * i / pts
        r = R - a + a * (0.5 + 0.5 * math.cos(n * t))  # smooth rosette edge
        out.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in out) + "Z"


def norm(v):
    l = math.hypot(*v)
    return (v[0] / l, v[1] / l)


def calligraphic_check(scale, cx, cy):
    """A check mark whose long arm tapers like a pen stroke. Returns path data."""
    S, V, T = (-0.44, 0.06), (-0.12, 0.38), (0.46, -0.36)
    u1, u2 = norm((V[0] - S[0], V[1] - S[1])), norm((T[0] - V[0], T[1] - V[1]))
    n1, n2 = (-u1[1], u1[0]), (-u2[1], u2[0])
    wS, wV, wT = 0.20, 0.20, 0.03
    m = norm((n1[0] + n2[0], n1[1] + n2[1]))
    k = (wV / 2) / (m[0] * n1[0] + m[1] * n1[1])
    pts = [
        (S[0] + n1[0] * wS / 2, S[1] + n1[1] * wS / 2),
        (V[0] + m[0] * k, V[1] + m[1] * k),
        (T[0] + n2[0] * wT / 2, T[1] + n2[1] * wT / 2),
        (T[0] - n2[0] * wT / 2, T[1] - n2[1] * wT / 2),
        (V[0] - m[0] * k, V[1] - m[1] * k),
        (S[0] - n1[0] * wS / 2, S[1] - n1[1] * wS / 2),
    ]
    # centre the shape visually
    ox, oy = 0.01, -0.01
    return "M" + " L".join(f"{cx + (x + ox) * scale:.1f} {cy + (y + oy) * scale:.1f}" for x, y in pts) + "Z"


def seal_group(cx, cy, R, bg=GREEN, fg="#fff", ring=GOLD, inner=GREEN_D):
    """The seal: rosette edge, inner disc, thin ring, calligraphic check."""
    return (
        f'<path d="{scallop(cx, cy, R, R * 0.045, 22)}" fill="{bg}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{R * 0.80:.1f}" fill="{inner}"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{R * 0.80:.1f}" fill="none" stroke="{ring}" stroke-width="{R * 0.03:.1f}"/>'
        f'<path d="{calligraphic_check(R * 0.82, cx, cy)}" fill="{fg}"/>'
    )


def svg(w, h, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">'
        f"<title>{title}</title>{body}</svg>\n"
    )




def main():
    # 1. Mark only
    mark = svg(200, 200, seal_group(100, 100, 98), "حقدار")
    open(OUT / "logo-mark.svg", "w", encoding="utf-8").write(mark)

    # 2. Horizontal lockup: seal on the right (where Urdu reading starts), wordmark on the left
    H = 120
    wd, ww, wh = text_path("حقدار", wght=700, height=84)
    gap = 20
    W = ww + gap + H
    wm_y = (H - wh) / 2
    wd, ww, wh = text_path("حقدار", wght=700, height=84, ox=0, oy=wm_y)
    body = f'<path d="{wd}" fill="{INK_G}"/>' + seal_group(ww + gap + H / 2, H / 2, H / 2 - 1)
    open(OUT / "logo.svg", "w", encoding="utf-8").write(svg(round(W), H, body, "حقدار"))
    light = f'<path d="{wd}" fill="#ffffff"/>' + seal_group(
        ww + gap + H / 2, H / 2, H / 2 - 1, bg="#ffffff", fg="#ffffff", ring=GOLD, inner=GREEN
    )
    open(OUT / "logo-light.svg", "w", encoding="utf-8").write(svg(round(W), H, light, "حقدار"))
    print("horizontal", round(W), H)

    # 3. Stacked lockup with Urdu tagline, for the big home-page logo
    SW = 360
    seal_r = 92
    y = 6
    body = seal_group(SW / 2, y + seal_r, seal_r)
    y += seal_r * 2 + 18
    wd, ww, wh = text_path("حقدار", wght=700, height=104)
    wd, ww, wh = text_path("حقدار", wght=700, height=104, ox=(SW - ww) / 2, oy=y)
    body += f'<path d="{wd}" fill="{INK_G}"/>'
    y += wh + 20
    td, tw, th = text_path("آپ کا حق، آسان زبان میں", wght=500, width=250)
    td, tw, th = text_path("آپ کا حق، آسان زبان میں", wght=500, width=250, ox=(SW - tw) / 2, oy=y)
    body += f'<path d="{td}" fill="{MUTED}"/>'
    y += th + 8
    open(OUT / "logo-stacked.svg", "w", encoding="utf-8").write(svg(SW, round(y), body, "حقدار: آپ کا حق، آسان زبان میں"))
    print("stacked", SW, round(y), "tagline", round(tw), round(th))

    # 4. App icon: white seal on a green square
    icon = (
        '<rect width="512" height="512" fill="#0d6b4a"/>'
        + seal_group(256, 256, 214, bg="#ffffff", fg="#ffffff", ring=GOLD, inner=GREEN)
    )
    open(OUT / "icon.svg", "w", encoding="utf-8").write(svg(512, 512, icon, "حقدار"))


if __name__ == "__main__":
    main()