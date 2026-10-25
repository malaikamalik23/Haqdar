import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlparse

OFFICIAL = [
    d.lower()
    for d in json.loads(
        Path(__file__).with_name("official_domains.json").read_text(encoding="utf-8")
    )
]

SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "cutt.ly", "is.gd", "rb.gy"}
WALLET = re.compile(r"(easypaisa|jazzcash|sadapay|nayapay|western union|gift ?card)", re.I)
URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>\"']+")


def extract_links(text: str) -> list:
    return [m.group(0).rstrip(".,;:!?)]}") for m in URL_RE.finditer(text)]


def _host(link: str) -> str:
    link = link.strip()
    try:
        parsed = urlparse(link if "://" in link else "//" + link)
        return (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def is_official(host: str) -> bool:
    # Exact match or a true subdomain, so "fbr.gov.pk.evil.com" and "evilfbr.gov.pk" fail.
    return bool(host) and any(host == d or host.endswith("." + d) for d in OFFICIAL)


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def check_notice(text: str, links=None, scam_score: float = 0.0, sender: str = "") -> dict:
    """Returns {"label": "genuine" | "suspicious" | "unclear", "reasons": [...]}.

    "genuine" only means the evidence looks consistent with an official source.
    It is never proof of authenticity, and the reasons say so.
    """
    all_links = list(dict.fromkeys((links or []) + extract_links(text)))
    flags, official_evidence = [], 0

    for link in all_links:
        host = _host(link)
        if not host:
            flags.append(f"Could not read the link: {link[:60]}")
        elif is_official(host):
            official_evidence += 1
        elif _is_ip(host):
            flags.append("A link points to a raw IP address instead of a website name")
        elif host in SHORTENERS:
            flags.append(f"A link uses the URL shortener {host}, which hides the real destination")
        elif "xn--" in host:
            flags.append(f"Link {host} uses disguised (punycode) characters")
        else:
            flags.append(f"Link {host} is not an official government domain")

    if "@" in sender:
        sender_host = sender.rsplit("@", 1)[-1].strip().lower().rstrip(".")
        if is_official(sender_host):
            official_evidence += 1
        else:
            flags.append(f"Sender domain {sender_host} is not an official government domain")

    if WALLET.search(text):
        flags.append("Asks for payment through a mobile wallet, gift card or transfer service")
    if scam_score >= 0.7:
        flags.append("Urgent or threatening language")

    if flags:
        return {"label": "suspicious", "reasons": list(dict.fromkeys(flags))}
    if official_evidence:
        return {
            "label": "genuine",
            "reasons": [
                "Links or sender match official domains. This is not proof: "
                "confirm with the office directly before paying."
            ],
        }
    return {"label": "unclear", "reasons": ["Not enough evidence either way"]}