"""Module K1: Pack loader.

Reads procedure packs (YAML files in packs/), checks they follow the pack
format, and splits them into chunks for retrieval (K2).

Each chunk carries pack_id, step_id and source_id so every answer can be
traced back to an official source.
"""

from pathlib import Path
from urllib.parse import urlparse

import yaml

# Repo root is two levels above this file: backend/ai/pack_loader.py
PACKS_DIR = Path(__file__).resolve().parents[2] / "packs"

# Only these official domains may be used as sources.
# A source URL is allowed if its host equals one of these or ends with "." + one of these.
# To add a DISCO or other official site, add its domain here after checking it is official.
ALLOWED_SOURCE_DOMAINS = (
    "gov.pk",        # any Government of Pakistan site (fbr.gov.pk, nadra.gov.pk, ...)
    "nepra.org.pk",  # National Electric Power Regulatory Authority
)

REQUIRED_PACK_FIELDS = ("id", "title_ur", "title_en", "steps", "documents_needed", "office", "sources")
REQUIRED_STEP_FIELDS = ("id", "text_ur", "text_en", "source_id")
REQUIRED_SOURCE_FIELDS = ("id", "url", "quote")


class PackError(ValueError):
    """Raised when a pack file is missing fields or has invalid sources."""


def is_allowed_url(url: str) -> bool:
    """True if url is https and its host is on the official allowlist."""
    parsed = urlparse(str(url).strip())
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_SOURCE_DOMAINS)


def _has_todo(value) -> bool:
    return isinstance(value, str) and "TODO" in value


def validate_pack(pack: dict) -> list[str]:
    """Return a list of problems with the pack. An empty list means the pack is valid."""
    if not isinstance(pack, dict):
        return ["pack is not a YAML mapping"]

    errors = []
    pack_id = pack.get("id", "<no id>")

    for field in REQUIRED_PACK_FIELDS:
        if field not in pack or pack[field] in (None, "", []):
            errors.append(f"{pack_id}: missing field '{field}'")

    for field in ("id", "title_ur", "title_en", "office"):
        if _has_todo(pack.get(field)):
            errors.append(f"{pack_id}: field '{field}' still contains TODO")
    for doc in pack.get("documents_needed") or []:
        if _has_todo(doc):
            errors.append(f"{pack_id}: documents_needed still contains TODO")

    # Sources
    source_ids = set()
    for i, src in enumerate(pack.get("sources") or []):
        sid = src.get("id", f"<source #{i + 1}>") if isinstance(src, dict) else f"<source #{i + 1}>"
        if not isinstance(src, dict):
            errors.append(f"{pack_id}: source #{i + 1} is not a mapping")
            continue
        for field in REQUIRED_SOURCE_FIELDS:
            if not src.get(field):
                errors.append(f"{pack_id}: source '{sid}' missing '{field}'")
            elif _has_todo(src[field]):
                errors.append(f"{pack_id}: source '{sid}' field '{field}' still contains TODO")
        if sid in source_ids:
            errors.append(f"{pack_id}: duplicate source id '{sid}'")
        source_ids.add(sid)
        url = src.get("url")
        if url and not _has_todo(url) and not is_allowed_url(url):
            errors.append(f"{pack_id}: source '{sid}' url is not an allowed official https domain: {url}")

    # Steps
    step_ids = set()
    for i, step in enumerate(pack.get("steps") or []):
        if not isinstance(step, dict):
            errors.append(f"{pack_id}: step #{i + 1} is not a mapping")
            continue
        stid = step.get("id", f"<step #{i + 1}>")
        for field in REQUIRED_STEP_FIELDS:
            if not step.get(field):
                errors.append(f"{pack_id}: step '{stid}' missing '{field}'")
            elif _has_todo(step[field]):
                errors.append(f"{pack_id}: step '{stid}' field '{field}' still contains TODO")
        if stid in step_ids:
            errors.append(f"{pack_id}: duplicate step id '{stid}'")
        step_ids.add(stid)
        if step.get("source_id") and step["source_id"] not in source_ids:
            errors.append(f"{pack_id}: step '{stid}' points to unknown source '{step['source_id']}'")

    return errors


def load_pack(path) -> dict:
    """Load one pack file and validate it. Raises PackError if invalid."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        pack = yaml.safe_load(f)
    errors = validate_pack(pack)
    if errors:
        raise PackError(f"{path.name} is invalid:\n  - " + "\n  - ".join(errors))
    return pack


def load_all_packs(packs_dir=PACKS_DIR) -> list[dict]:
    """Load every *.yaml / *.yml pack in packs_dir. Raises PackError on the first invalid pack."""
    packs_dir = Path(packs_dir)
    files = sorted(list(packs_dir.glob("*.yaml")) + list(packs_dir.glob("*.yml")))
    return [load_pack(p) for p in files]


def pack_to_chunks(pack: dict) -> list[dict]:
    """Split a pack into one chunk per step.

    Chunk format: {pack_id, step_id, source_id, text_ur, text_en, title_ur, step_keywords}
    (K2 adds 'score' when returning search results.)
    """
    return [
        {
            "pack_id": pack["id"],
            "step_id": step["id"],
            "source_id": step["source_id"],
            "text_ur": step["text_ur"],
            "text_en": step["text_en"],
            "title_ur": pack["title_ur"],
            "step_keywords": [str(k) for k in step.get("keywords", [])],
        }
        for step in pack["steps"]
    ]


def load_chunks(packs_dir=PACKS_DIR) -> list[dict]:
    """Load all packs and return all their chunks (input for the retrieval engine)."""
    chunks = []
    for pack in load_all_packs(packs_dir):
        chunks.extend(pack_to_chunks(pack))
    return chunks


def get_source(pack: dict, source_id: str) -> dict | None:
    """Return the source entry {id, url, quote} for source_id, or None."""
    for src in pack.get("sources", []):
        if src.get("id") == source_id:
            return src
    return None
