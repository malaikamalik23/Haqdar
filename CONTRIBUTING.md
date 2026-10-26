# Contributing to Haqdar

Thank you for helping. Haqdar explains official procedures in plain Urdu and English, so clear words and careful sources matter more than clever code.

## Ways to help

- **Add or improve a procedure pack.** Each pack is written from official sources only.
- **Improve Urdu wording** on the pages or in a pack.
- **Test with real photos and notices** (made-up personal data only) and report what is misread.
- **Letter templates** for the CNIC and rent packs, which only have answers for now.
- **Accessibility and mobile** improvements.
- **Tests, documentation and bug fixes.**

## Set up

```bash
git clone https://github.com/malaikamalik23/Haqdar.git
cd Haqdar
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements-dev.txt faiss-cpu numpy pyyaml jinja2 scikit-learn pytesseract
```

That is enough to run every test: the AI tests use a small stand-in for the search model, so they do not need PyTorch.

- **Everything, with Docker:** `docker compose up --build`, then open http://localhost:5500.
- **Interface work without the AI libraries:** set `HAQDAR_AI_MODE=mock` (PowerShell: `$env:HAQDAR_AI_MODE="mock"`), run `uvicorn main:app --reload` inside `backend`, and `python -m http.server 5500` inside `web`. Mock mode returns fixed sample answers.
- **Real answers without Docker:** also run `pip install -r backend/ai/requirements.txt`. The first start downloads the search model (about 0.5 GB). Reading photos needs Tesseract with the Urdu language data.

## Before you open a pull request

```bash
cd backend && pytest -q tests ai      # API, security and AI tests
cd .. && python -m pytest tools/tests -q
python tools/build_pages.py            # only if you changed tools/build_pages.py or web/app.js
python tools/check_web.py
python tools/validate_packs.py
```

The pages in `web/` (`index.html`, `ask.html`, `notice.html`, `about.html`) are **generated**. Edit `tools/build_pages.py`, `web/app.js` or `web/style.css`, then run `python tools/build_pages.py`. Do not edit the HTML by hand: CI regenerates the pages and fails if they differ.

## Pull requests

1. Make a branch from `main`, for example `feat/letter-templates` or `fix/upload-message`.
2. Keep each pull request about one thing.
3. Add or update tests. A bug fix should come with a test that fails without it.
4. Write the description in plain words: what changed, why, and how you checked it.
5. Wait for the checks to pass. Stage files by name (`git add path/to/file`), and never commit `.env` files, keys, or real personal data.

Commit messages start with a type: `feat:`, `fix:`, `docs:`, `test:`, `ci:` or `chore:`.

## Adding a procedure pack

1. Copy an existing file in `packs/` and write the steps, the documents needed and the office.
2. Every step needs a source link on an official domain from `backend/security/official_domains.json`. If a site is genuinely official but missing from that list, add it in its own pull request and explain why.
3. Run `python tools/validate_packs.py`.
4. Add test questions to `eval/questions.yaml`: real questions in Urdu, Roman Urdu and English, and nearby questions that must be refused (another city, another service). Run `python eval/run_eval.py` (it needs the real search model, so use Docker or a computer where PyTorch works).
5. A pack is ready only when its questions are answered correctly and the nearby out-of-scope questions are refused.

## Security-sensitive changes

Changes to `backend/security/`, the upload route, the rate limits or the container settings need extra care: add tests for the bad cases, and update [docs/threat-model.md](docs/threat-model.md) if a defence changes. To report a vulnerability, follow [SECURITY.md](SECURITY.md) and do not open a public issue.

## Being kind

Be patient and respectful. Haqdar is for people who are worried about official paperwork, so keep language plain and never blame the user. Contributions are released under the [MIT licence](LICENSE).
