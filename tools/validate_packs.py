"""Checks every procedure pack in packs/. Run by CI, and safe to run by hand:

    python tools/validate_packs.py

A pack is a YAML file such as packs/electricity-bill-dispute.yaml. The rules protect users:
every step must cite a source, every source must be an https link to an official domain from
backend/security/official_domains.json, and quotes must be short excerpts.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parent.parent
PACKS_DIR = ROOT / "packs"
DOMAINS_FILE = ROOT / "backend" / "security" / "official_domains.json"
SLUG = re.compile(r"^[a-z0-9_-]{1,64}$")
STEP_ID = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
MAX_QUOTE = 300


def load_domains(path=DOMAINS_FILE):
    return [d.lower() for d in json.loads(Path(path).read_text(encoding="utf-8"))]


def is_official(host, domains):
    host = (host or "").lower().rstrip(".")
    return bool(host) and any(host == d or host.endswith("." + d) for d in domains)


def _text(value):
    return isinstance(value, str) and value.strip() != ""


def validate_pack(data, domains, filename=None):
    """Returns (errors, warnings). An empty errors list means the pack is valid."""
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["the file must contain a mapping (key: value pairs)"], warnings

    pack_id = data.get("id")
    if not isinstance(pack_id, str) or not SLUG.match(pack_id):
            errors.append("id must be lowercase letters, digits, hyphens or underscores (up to 64 characters)")
    elif filename and pack_id != Path(filename).stem:
        errors.append(f"id '{pack_id}' must match the file name '{Path(filename).stem}'")

    for key in ("title_ur", "title_en", "office"):
        if not _text(data.get(key)):
            errors.append(f"{key} is required")
    if not isinstance(data.get("documents_needed"), list) or not all(isinstance(d, str) for d in data.get("documents_needed", [])):
        errors.append("documents_needed must be a list of text items (it may be empty)")

    sources = data.get("sources")
    source_ids = {}
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        sources = []
    for i, src in enumerate(sources, 1):
        label = f"source #{i}"
        if not isinstance(src, dict):
            errors.append(f"{label} must be a mapping")
            continue
        sid = src.get("id")
        if not isinstance(sid, str) or not STEP_ID.match(sid):
            errors.append(f"{label}: id is required (letters, digits, - and _)")
            continue
        label = f"source '{sid}'"
        if sid in source_ids:
            errors.append(f"{label}: duplicate source id")
        source_ids[sid] = 0
        parsed = urlparse(src.get("url") or "")
        if parsed.scheme != "https":
            errors.append(f"{label}: url must start with https://")
        elif not is_official(parsed.hostname, domains):
            errors.append(f"{label}: {parsed.hostname} is not in official_domains.json (verify it on the department's own site, then add it)")
        quote = src.get("quote")
        if not _text(quote):
            errors.append(f"{label}: quote is required (a short exact excerpt)")
        elif len(quote) > MAX_QUOTE:
            errors.append(f"{label}: quote is {len(quote)} characters; keep excerpts under {MAX_QUOTE}")

    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("steps must be a non-empty list")
        steps = []
    seen_steps = set()
    for i, step in enumerate(steps, 1):
        label = f"step #{i}"
        if not isinstance(step, dict):
            errors.append(f"{label} must be a mapping")
            continue
        sid = step.get("id")
        if not isinstance(sid, str) or not STEP_ID.match(sid):
            errors.append(f"{label}: id is required (letters, digits, - and _)")
        elif sid in seen_steps:
            errors.append(f"{label}: duplicate step id '{sid}'")
        else:
            seen_steps.add(sid)
            label = f"step '{sid}'"
        for key in ("text_ur", "text_en"):
            if not _text(step.get(key)):
                errors.append(f"{label}: {key} is required")
        cited = step.get("source_id")
        if cited not in source_ids:
            errors.append(f"{label}: source_id '{cited}' is not listed under sources")
        else:
            source_ids[cited] += 1

    for sid, count in source_ids.items():
        if count == 0:
            warnings.append(f"source '{sid}' is never cited by a step")
    return errors, warnings


def main(argv=None):
    argv = argv or sys.argv
    packs_dir = Path(argv[1]) if len(argv) > 1 else PACKS_DIR
    try:
        domains = load_domains()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL cannot read {DOMAINS_FILE}: {exc}")
        return 1

    files = sorted(list(packs_dir.glob("*.yaml")) + list(packs_dir.glob("*.yml")))
    if not files:
        print("no packs found yet: nothing to validate")
        return 0

    failed, seen_ids = False, {}
    for path in files:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError) as exc:
            print(f"FAIL {path.name}\n     - not valid YAML: {exc}")
            failed = True
            continue
        errors, warnings = validate_pack(data, domains, path.name)
        pid = data.get("id") if isinstance(data, dict) else None
        if pid in seen_ids:
            errors.append(f"id '{pid}' is already used by {seen_ids[pid]}")
        elif pid:
            seen_ids[pid] = path.name
        print(("FAIL " if errors else "ok   ") + path.name)
        for message in errors:
            print("     -", message)
        for message in warnings:
            print("     (warning)", message)
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())