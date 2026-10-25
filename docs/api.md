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

## Limits, errors and headers

- Request bodies larger than 64 KB are rejected with `413`.
- `question` and `text` are limited to 4000 characters; `pack_id` must match `^[a-z0-9-]{1,64}$`; `/letter` accepts at most 20 `fields`, with keys up to 40 and values up to 300 characters.
- Unknown request fields are rejected, so clients may send only the fields documented here.
- Clients are limited to 20 POST requests and 60 GET requests per minute. Beyond that the API returns `429` with a `Retry-After` header (seconds).
- Invalid requests return `422` with `{"detail": "Invalid request", "errors": [{"field": "...", "problem": "..."}]}`. Error bodies never repeat what the user sent.
- Every response carries `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store` and a strict `Content-Security-Policy`.
- `GET /health` returns `{"status": "ok"}`.