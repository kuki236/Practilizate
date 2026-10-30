import hashlib
import re
from datetime import date

OFFER_SUFFIX_RE = re.compile(r"-(\d+)(?:\.html?)?$")


def offer_external_id(url: str) -> str:
    match = OFFER_SUFFIX_RE.search(url)
    if match:
        return match.group(1)
    return stable_hex(url)


def stable_hex(value: str, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def stable_id(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") & 0x7FFF_FFFF_FFFF_FFFF


def date_id(value: date) -> int:
    return value.year * 10000 + value.month * 100 + value.day
