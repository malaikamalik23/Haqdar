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

## Rules
- Documents are never stored and never logged.
- Every step must cite a source_id that exists in `sources`.
- Use fake data only when testing.