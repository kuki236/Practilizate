import re
import unicodedata

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?51[\s-]?)?9\d{2}[\s-]?\d{3}[\s-]?\d{3}(?!\d)")
LANDLINE_RE = re.compile(r"(?<!\d)\(?01\)?[\s-]?\d{3}[\s-]?\d{4}(?!\d)")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

LEGAL_SUFFIXES = (
    "sociedad anonima cerrada",
    "sociedad anonima abierta",
    "sociedad anonima",
    "sociedad de responsabilidad limitada",
    "s a c",
    "s a a",
    "s a",
    "s r l",
    "e i r l",
    "sac",
    "saa",
    "srl",
    "eirl",
    "cia ltda",
    "ltda",
    "limitada",
    "corporation",
    "corp",
    "inc",
    "llc",
    "sa",
)

_CONNECTORS = {"de", "del", "la", "las", "los", "y", "e"}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", value)
    text = text.replace("\xa0", " ")
    text = CONTROL_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_company(value: str | None) -> str | None:
    key = normalize_key(value or "")
    if not key:
        return None
    for suffix in LEGAL_SUFFIXES:
        if key == suffix:
            return None
        if key.endswith(f" {suffix}"):
            key = key[: -(len(suffix) + 1)].strip()
    return key or None


def smart_title(value: str | None) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    words = text.split(" ")
    titled = [
        word.lower()
        if index and word.lower() in _CONNECTORS
        else word[:1].upper() + word[1:].lower()
        for index, word in enumerate(words)
    ]
    return " ".join(titled)


def strip_personal_data(value: str) -> str:
    text = EMAIL_RE.sub("[contacto eliminado]", value)
    text = PHONE_RE.sub("[contacto eliminado]", text)
    return LANDLINE_RE.sub("[contacto eliminado]", text)
