"""K4 evaluation: OCR + field extraction on synthetic notice images (owner: Malaika Khan).

Renders sample notices with KNOWN fields into images (clean and degraded: smaller,
blurred, rotated), runs OCR (K4a) + field extraction (K4b), and reports how many
fields were recovered exactly. Urdu-script notices are included when Pillow can
shape Urdu text (needs libraqm); otherwise they are skipped and reported.

All notices are synthetic, with fake names and numbers.

Run from the repo root:
    python eval/ocr_eval.py
Writes eval/ocr_results.md
"""

import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from ai import extract, ocr  # noqa: E402

URDU_FONT = ROOT / "web" / "tools" / "logo" / "NotoNastaliqUrdu.ttf"
# Pre-rendered Urdu notice images, for machines whose Pillow cannot shape Urdu
# (e.g. the standard Windows build has no libraqm). Create them with:
#     python eval/ocr_eval.py --render-urdu     (on a machine where Urdu shaping works)
SAMPLES_DIR = ROOT / "eval" / "ocr_samples"
FIELDS = ("sender", "date", "deadline", "amount")

NOTICES = [
    {"lang": "en", "lines": ["IESCO Electricity Bill", "Bill Date: 05-11-2026", "Amount Payable: Rs 18,500",
                             "Due Date: 20-11-2026", "Please pay before the due date."],
     "expected": {"sender": "IESCO", "date": "05-11-2026", "deadline": "20-11-2026", "amount": "18,500"}},
    {"lang": "en", "lines": ["Federal Board of Revenue", "Dated: 02-10-2026", "Notice under section 114",
                             "File your return not later than 30-10-2026."],
     "expected": {"sender": "FBR", "date": "02-10-2026", "deadline": "30-10-2026", "amount": ""}},
    {"lang": "en", "lines": ["LESCO", "Bill Date: 01-11-2026", "Total amount payable: Rs 7,250",
                             "Due Date: 15-11-2026"],
     "expected": {"sender": "LESCO", "date": "01-11-2026", "deadline": "15-11-2026", "amount": "7,250"}},
    {"lang": "roman", "lines": ["MEPCO bill", "Bill Date: 03-11-2026", "Raqam: Rs 12,400",
                                "Aakhri tareekh 18-11-2026 tak jama karwa dein."],
     "expected": {"sender": "MEPCO", "date": "03-11-2026", "deadline": "18-11-2026", "amount": "12,400"}},
    {"lang": "ur", "lines": ["آئیسکو", "بل کی رقم: 18,500 روپے", "آخری تاریخ: 20-11-2026", "براہِ کرم بل ادا کریں۔"],
     "expected": {"sender": "IESCO", "date": "", "deadline": "20-11-2026", "amount": "18,500"}},
    {"lang": "ur", "lines": ["نادرا", "آپ کا شناختی کارڈ 30-11-2026 تک تجدید کروائیں۔"],
     "expected": {"sender": "NADRA", "date": "", "deadline": "30-11-2026", "amount": ""}},
]

VARIANTS = {
    "clean": lambda im: im,
    "small": lambda im: im.resize((im.width // 2, im.height // 2)),
    "blurred": lambda im: im.filter(ImageFilter.GaussianBlur(1.6)),
    "rotated": lambda im: im.rotate(3, expand=True, fillcolor="white"),
}


def render(notice):
    image = Image.new("RGB", (1400, 110 + 95 * len(notice["lines"])), "white")
    draw = ImageDraw.Draw(image)
    if notice["lang"] == "ur":
        font = ImageFont.truetype(str(URDU_FONT), 46, layout_engine=ImageFont.Layout.RAQM)
        for i, line in enumerate(notice["lines"]):
            draw.text((1360, 40 + i * 95), line, fill="black", font=font, anchor="ra", direction="rtl")
    else:
        font = ImageFont.load_default(size=46)
        for i, line in enumerate(notice["lines"]):
            draw.text((40, 40 + i * 95), line, fill="black", font=font)
    return image


def to_png(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def urdu_image(n_i, notice, variant, fn, can_render):
    """Render Urdu live if possible, else load the pre-rendered sample (or None)."""
    if can_render:
        return fn(render(notice))
    path = SAMPLES_DIR / f"notice{n_i}_{variant}.png"
    return Image.open(path) if path.exists() else None


def render_urdu_samples():
    SAMPLES_DIR.mkdir(exist_ok=True)
    for n_i, notice in enumerate(NOTICES, 1):
        if notice["lang"] == "ur":
            base = render(notice)
            for variant, fn in VARIANTS.items():
                fn(base).save(SAMPLES_DIR / f"notice{n_i}_{variant}.png")
    print(f"Saved Urdu samples to {SAMPLES_DIR}")


def main():
    if "--render-urdu" in sys.argv:
        render_urdu_samples()
        return
    if not ocr.is_available():
        print("Tesseract is not installed; cannot run the OCR evaluation.")
        sys.exit(1)
    can_render = features.check("raqm") and URDU_FONT.exists()

    rows, skipped, urdu_source = [], 0, "rendered live" if can_render else "pre-rendered samples"
    for n_i, notice in enumerate(NOTICES, 1):
        base = render(notice) if notice["lang"] != "ur" else None
        for variant, fn in VARIANTS.items():
            if notice["lang"] == "ur":
                image = urdu_image(n_i, notice, variant, fn, can_render)
                if image is None:
                    skipped += 1
                    continue
            else:
                image = fn(base)
            got = extract.extract_fields(ocr.extract_text(to_png(image)))
            for field in FIELDS:
                expected = notice["expected"][field]
                if expected:  # only score fields that exist in the notice
                    rows.append((n_i, notice["lang"], variant, field, expected, got[field], got[field] == expected))

    def rate(items):
        ok = sum(r[6] for r in items)
        return f"{100 * ok / len(items):.0f}% ({ok}/{len(items)})" if items else "n/a"

    lines = ["# OCR + field extraction results (synthetic notices)", "",
             f"Tesseract languages: `{ocr.LANGS}` · Urdu-script notices: "
             f"{'included (' + urdu_source + ')' if not skipped else f'{skipped} images skipped (no Urdu shaping and no samples)'}", "",
             "## Fields recovered exactly", "", "| | Result |", "|---|---|", f"| **All fields** | **{rate(rows)}** |"]
    for variant in VARIANTS:
        lines.append(f"| {variant} images | {rate([r for r in rows if r[2] == variant])} |")
    lines += ["", "| Language | Result |", "|---|---|"]
    for lang, name in (("en", "English"), ("roman", "Roman Urdu"), ("ur", "Urdu script")):
        lines.append(f"| {name} | {rate([r for r in rows if r[1] == lang])} |")
    lines += ["", "| Field | Result |", "|---|---|"]
    for field in FIELDS:
        lines.append(f"| {field} | {rate([r for r in rows if r[3] == field])} |")
    misses = [r for r in rows if not r[6]]
    lines += ["", "## Misses", ""]
    lines += [f"- notice {r[0]} ({r[1]}, {r[2]}): {r[3]} expected `{r[4]}`, got `{r[5] or '(nothing)'}`" for r in misses] or ["- none"]

    (ROOT / "eval" / "ocr_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:30]))
    print("\nFull report: eval/ocr_results.md")


if __name__ == "__main__":
    main()
