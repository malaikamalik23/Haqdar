# Threat model

This page explains what Haqdar protects, who and what it defends against, and, just as important, **what it does not defend against**. Last reviewed on the date of the latest commit that touches this file.

## What we protect

| Asset | Why it matters |
|---|---|
| What people type, paste or upload (notices, CNIC, phone numbers) | Personal and sometimes financial details |
| The correctness of answers | A wrong step could cost someone money or a deadline |
| The links in answers | A link to a fake site would send people to scammers |
| The server and its container | Must not be used to attack others or leak data |

## Who and what we worry about

- **Curious or careless handling of personal data**, including our own mistakes.
- **A malicious user** sending crafted files, huge requests or floods of requests.
- **A malicious web page or text** trying to run script in someone's browser.
- **Scammers**, both as senders of fake notices that users bring to Haqdar and as people who might try to get a bad link into an answer.
- **Weak spots in other people's code**: libraries, base images and the downloaded search model.

## Where data goes

1. The browser masks personal details in typed or pasted text, shows the result with black bars, and sends only what the person confirms.
2. A photo or PDF goes to our own server, is checked, read, masked and returned for review. A text file never leaves the browser until review.
3. The server builds an answer from the verified procedure packs. **No outside AI service is called**, and nothing is sent to any third party.
4. Nothing the person types or uploads is stored by the application. Photos and PDFs are read in memory; the web server's access log records the address and path of a request, never its content.

## Threats and defences

| # | Threat | Defence | Left over |
|---|---|---|---|
| 1 | Personal data reaches a third party | No outside AI or analytics service. Details masked in the browser before sending (CNIC, phone, email, IBAN, labelled reference numbers; English and Urdu digits) and on the server for photos and PDFs. The person reviews before anything is analysed. | Names and addresses are not masked automatically. Reference numbers are only recognised after English labels such as "Consumer No". The review screen is the safety net. |
| 2 | Personal data kept on the server | The app writes nothing to disk. The container filesystem is read-only. Large uploads and OCR may use a temporary file in a memory-only `tmpfs`, deleted right after. | The access log holds IP address and path. Temporary files exist for a moment. |
| 3 | A malicious file (disguised type, huge image, broken or hostile PDF) | The real type is read from the file's first bytes, not its name. 8 MB limit. Image size limit. Images are re-encoded (metadata removed, rotation applied). PDFs are read only from their text, first 3 pages, nothing is run or opened, encrypted and broken PDFs are refused with a generic message. Tests in `backend/tests/`. | A bug in Pillow, pypdf or Tesseract could still matter. A crafted PDF could keep one worker busy; this is limited by 2 concurrent reads, rate limits, and the container's CPU and memory limits. |
| 4 | Overload and abuse | 64 KB request limit (8 MB plus form overhead for the upload route only). Rate limits per client: 20 writes, 60 reads, 6 uploads per minute. At most 2 files read at once. | The limiter is in memory, per process, and resets on restart. Behind a proxy the setting `HAQDAR_TRUST_PROXY` must be correct. A distributed attack is not covered. |
| 5 | Script injection in the browser | Strict Content-Security-Policy, no third-party requests. Server text is shown with `textContent`. `tools/check_web.py` fails CI if a page has an inline script or style, or a weaker policy. | None known. |
| 6 | Prompt injection | No language model is called, so there is nothing to inject into. `backend/security/payload.py` is ready for a future model step and is not used today. | Revisit if a model is ever added. |
| 7 | Wrong or invented answers | Answers come only from verified pack steps, with sources. Below a confidence threshold, Haqdar refuses. Measured by `eval/` (41 of 42 correct, 9 of 10 out-of-scope refused). | One evaluation answer was wrong. Packs go out of date. The app says it is information, not legal advice. |
| 8 | A pack linking to a fake or unofficial site | `tools/validate_packs.py` accepts only domains on the official list, and CI runs it. | An official site can change or be compromised. |
| 9 | A scam notice that looks genuine | The warning-sign check (official domains, look-alikes, shorteners, IP links, wallet and gift-card payment requests, urgent language) always says "warning signs, not proof". | A good fake can pass. People should confirm with the office. |
| 10 | Leaks through errors and headers | Errors never repeat what was sent. The server banner is hidden. Security headers on every API response. The interactive API docs are off in production. | None known. |
| 11 | Other websites calling the API | A list of allowed origins. No cookies or logins to steal. | The API is public and has no authentication. |
| 12 | A vulnerable or malicious dependency, image or model | Bandit, pip-audit and a secret scan in CI. Dockerfile lint and an image scan (informational). Dependabot for the workflow actions. | Library versions are not locked. The search model is downloaded at build time from a public model hub and is not pinned to a hash. |
| 13 | Container compromise | Non-root user, read-only filesystem, all Linux capabilities dropped, no new privileges, memory, CPU and process limits, `noexec` temporary space. | The container still shares the host's kernel. |
| 14 | Secrets in the repository | None are needed. gitleaks runs in CI. | None known. |

## Not covered (known gaps)

- No sign-in and no per-person quotas: this is a public tool.
- No formal penetration test. An optional automated OWASP ZAP scan can be added to CI, and its findings would be informational.
- Photo and PDF reading is only as good as the OCR and the file: Urdu-script photos are often misread (20% in our test), and a scanned PDF has no text.
- No audit logging and no alerting.
- No protection against someone who controls the computer running the browser.

## Assumptions

- The person runs a current browser.
- When deployed on the internet, it is served over HTTPS with the production settings in the README.
- The procedure packs are reviewed by a person before they are merged.

## Keeping this true

CI runs on every change: tests (including the security tests), Bandit, pip-audit, gitleaks, the pack and web checkers, and the Docker checks. Any change to `backend/security/`, the upload route or the container settings should update this page.
