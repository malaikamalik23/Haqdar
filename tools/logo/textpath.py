"""Turn shaped Urdu (Nastaliq) text into an SVG path, so it looks identical on every device."""
import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

from pathlib import Path

FONT = str(Path(__file__).with_name("NotoNastaliqUrdu.ttf"))
_blob = hb.Blob.from_file_path(FONT)
_face = hb.Face(_blob)


def _font(wght):
    f = hb.Font(_face)
    f.set_variations({"wght": wght})
    return f


def _shape(text, wght):
    font = _font(wght)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, "calt": True, "mark": True, "mkmk": True, "curs": True})
    return font, buf.glyph_infos, buf.glyph_positions


def _glyph_run(text, wght):
    font, infos, poss = _shape(text, wght)
    x = y = 0
    run = []
    for info, pos in zip(infos, poss):
        run.append((info.codepoint, x + pos.x_offset, y + pos.y_offset))
        x += pos.x_advance
        y += pos.y_advance
    return font, run


def text_path(text, wght=700, height=None, width=None, ox=0.0, oy=0.0):
    """Returns (d, w, h): path data placed with its top-left at (ox, oy), scaled to the given height or width."""
    font, run = _glyph_run(text, wght)
    bp = BoundsPen(None)
    for gid, gx, gy in run:
        font.draw_glyph_with_pen(gid, TransformPen(bp, (1, 0, 0, -1, gx, -gy)))
    minx, miny, maxx, maxy = bp.bounds
    bw, bh = maxx - minx, maxy - miny
    s = (height / bh) if height else (width / bw)
    pen = SVGPathPen(None, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    for gid, gx, gy in run:
        font.draw_glyph_with_pen(
            gid, TransformPen(pen, (s, 0, 0, -s, (gx - minx) * s + ox, (-gy - miny) * s + oy))
        )
    return pen.getCommands(), bw * s, bh * s