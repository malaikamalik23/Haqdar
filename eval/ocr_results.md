# OCR + field extraction results (synthetic notices)

Tesseract languages: `urd+eng` · Urdu-script notices: included (pre-rendered samples)

## Fields recovered exactly

| | Result |
|---|---|
| **All fields** | **74% (59/80)** |
| clean images | 80% (16/20) |
| small images | 70% (14/20) |
| blurred images | 80% (16/20) |
| rotated images | 65% (13/20) |

| Language | Result |
|---|---|
| English | 91% (40/44) |
| Roman Urdu | 94% (15/16) |
| Urdu script | 20% (4/20) |

| Field | Result |
|---|---|
| sender | 54% (13/24) |
| date | 100% (16/16) |
| deadline | 62% (15/24) |
| amount | 94% (15/16) |

## Misses

- notice 3 (en, clean): sender expected `LESCO`, got `(nothing)`
- notice 3 (en, small): sender expected `LESCO`, got `(nothing)`
- notice 3 (en, rotated): sender expected `LESCO`, got `(nothing)`
- notice 3 (en, rotated): deadline expected `15-11-2026`, got `(nothing)`
- notice 4 (roman, rotated): deadline expected `18-11-2026`, got `(nothing)`
- notice 5 (ur, clean): sender expected `IESCO`, got `(nothing)`
- notice 5 (ur, small): sender expected `IESCO`, got `(nothing)`
- notice 5 (ur, small): deadline expected `20-11-2026`, got `(nothing)`
- notice 5 (ur, small): amount expected `18,500`, got `8,500`
- notice 5 (ur, blurred): sender expected `IESCO`, got `(nothing)`
- notice 5 (ur, blurred): deadline expected `20-11-2026`, got `(nothing)`
- notice 5 (ur, rotated): sender expected `IESCO`, got `(nothing)`
- notice 5 (ur, rotated): deadline expected `20-11-2026`, got `(nothing)`
- notice 6 (ur, clean): sender expected `NADRA`, got `(nothing)`
- notice 6 (ur, clean): deadline expected `30-11-2026`, got `(nothing)`
- notice 6 (ur, small): sender expected `NADRA`, got `(nothing)`
- notice 6 (ur, small): deadline expected `30-11-2026`, got `(nothing)`
- notice 6 (ur, blurred): sender expected `NADRA`, got `(nothing)`
- notice 6 (ur, blurred): deadline expected `30-11-2026`, got `3-11-2026`
- notice 6 (ur, rotated): sender expected `NADRA`, got `(nothing)`
- notice 6 (ur, rotated): deadline expected `30-11-2026`, got `(nothing)`
