import re
import unicodedata

_HONORIFICS = {
    "mr", "mrs", "ms", "miss", "mx", "dr", "prof", "professor",
    "sir", "dame", "rev", "fr", "sr", "br",
}

_SUFFIXES = {
    "jr", "sr", "ii", "iii", "iv", "v",
    "phd", "md", "esq", "cpa", "mba",
}

_PUNCT_RE = re.compile(r"[.,'\"`]")
_WS_RE = re.compile(r"\s+")


def canonicalize(name: str) -> str:
    """Normalize a person's name for dedupe matching.

    1. Lowercase.
    2. Strip accents (NFKD).
    3. Strip honorifics (Mr, Ms, Dr, ...).
    4. Strip suffixes (Jr, Sr, II, ...).
    5. Collapse whitespace.
    """
    if not name:
        return ""

    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = _PUNCT_RE.sub("", s)

    parts = [p for p in _WS_RE.split(s.strip()) if p]
    while parts and parts[0].rstrip(".") in _HONORIFICS:
        parts.pop(0)
    while parts and parts[-1].rstrip(".") in _SUFFIXES:
        parts.pop()

    return " ".join(parts)


def org_key(org: str | None) -> str:
    """Lowercase and trim an org for dedupe key composition."""
    if not org:
        return ""
    return _WS_RE.sub(" ", org.strip().lower())
