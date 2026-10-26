"""Draws the Haqdar app icons (PNG) with Pillow only: the white seal on a green square."""
import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "web"
GREEN, GOLD, WHITE = (13, 107, 74), (240, 193, 75), (255, 255, 255)


def scallop(cx, cy, R, a, n, pts=720):
    """Outline of the rosette edge."""
    out = []
    for i in range(pts):
        t = 2 * math.pi * i / pts
        r = R - a + a * (0.5 + 0.5 * math.cos(n * t))
        out.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return out


def norm(v):
    length = math.hypot(*v)
    return (v[0] / length, v[1] / length)


def check_polygon(scale, cx, cy):
    """A check mark whose long arm tapers like a pen stroke."""
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
    return [(cx + (x + 0.01) * scale, cy + (y - 0.01) * scale) for x, y in pts]


def make_icon(size, seal_ratio):
    """seal_ratio is the seal's diameter as a share of the icon (smaller leaves a safe margin)."""
    big = size * 4  # draw large, then shrink for smooth edges
    im = Image.new("RGB", (big, big), GREEN)
    d = ImageDraw.Draw(im)
    c = big / 2
    R = big * seal_ratio / 2
    d.polygon(scallop(c, c, R, R * 0.045, 22), fill=WHITE)
    ring_r, ring_w = R * 0.80, R * 0.03
    d.ellipse([c - ring_r - ring_w / 2, c - ring_r - ring_w / 2, c + ring_r + ring_w / 2, c + ring_r + ring_w / 2], fill=GOLD)
    d.ellipse([c - ring_r + ring_w / 2, c - ring_r + ring_w / 2, c + ring_r - ring_w / 2, c + ring_r - ring_w / 2], fill=GREEN)
    d.polygon(check_polygon(R * 0.82, c, c), fill=WHITE)
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    make_icon(192, 0.836).save(OUT / "icon-192.png")
    make_icon(512, 0.836).save(OUT / "icon-512.png")
    make_icon(512, 0.625).save(OUT / "icon-maskable-512.png")  # extra margin for Android's round crop
    make_icon(180, 0.836).save(OUT / "apple-touch-icon.png")
    print("icons written to", OUT)