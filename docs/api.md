# Haqdar API Contract

Single source of truth. If a shape changes, update this file and tell the other person BEFORE changing code.

## POST /ask
Request:
```json
{ "question": "bijli ka bill zyada aya hai", "lang": "ur" }
```
Response:
```json
{
  "answer_ur": "string",
  "steps": [{ "text_ur": "string", "source_id": "string" }],
  "sources": [{ "id": "string", "url": "string", "quote": "string" }],
  "confidence": 0.0,
  "abstained": false
}
```
If `abstained` is true, `steps` is empty and `answer_ur` explains which office to contact.

## POST /analyze
Request: an uploaded image (multipart) or `{ "text": "string" }`
Response:
```json
{
  "fields": { "sender": "", "date": "", "deadline": "", "amount": "", "demand": "" },
  "explanation_ur": "string",
  "steps": [{ "text_ur": "string", "source_id": "string" }],
  "sources": [{ "id": "string", "url": "string", "quote": "string" }],
  "verdict": { "label": "genuine | suspicious | unclear", "reasons": ["string"] },
  "abstained": false
}
```

## POST /letter
Request: `{ "pack_id": "string", "fields": { "name": "", "account_no": "" } }`
Response: `{ "letter_text": "string" }`

## GET /procedures
Response: `[{ "id": "electricity-bill-dispute", "title_ur": "string" }]`

## Pack format (YAML)
```yaml
id: electricity-bill-dispute
title_ur: ""
title_en: ""
steps:
  - id: s1
    text_ur: ""
    text_en: ""
    source_id: src1
documents_needed: []
office: ""
sources:
  - id: src1
    url: "https://..."
    quote: "short exact excerpt"
```
## Languages (Urdu and English)

Requests to `/ask`, `/analyze` and `/letter` carry an optional `lang` field: `"ur"` (default) or `"en"`. Any other value is rejected with a 422 error.

English fields are optional additions. Urdu fields are unchanged and always present.

| Endpoint | English fields |
|---|---|
| `/ask` | `answer_en`, and `text_en` on each step |
| `/analyze` | `explanation_en`, and `text_en` on each step |
| `/procedures` | `title_en` |
| `/letter` | `letter_text` is returned in the requested `lang` |

Rules:
- Return the language the request asked for. When a pack has no English text for a step, omit `text_en`; the web app then shows the Urdu text with a note.
- Source quotes stay in the original language of the official source.
- Verdict reasons from the notice check are currently English only.
- `security.payload.build_payload(redacted_text, lang)` whitelists `lang` to `"ur"` or `"en"` before it reaches any LLM.