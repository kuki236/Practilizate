import json
import re
from datetime import date, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from practilizate.logging import get_logger
from practilizate.models import Career, DetailData, ListingCard
from practilizate.text import clean_text, smart_title

LOGGER = get_logger("practilizate.parsing")

BASE_URL = "https://www.practicas.pe/"
ATTENDANCE_MAP = {
    "presencial": "Presencial",
    "hibrido": "Híbrido",
    "semipresencial": "Híbrido",
    "virtual": "Virtual",
    "remoto": "Virtual",
    "a distancia": "Virtual",
}
MODALITY_MAP = {
    "preprofesional": "Preprofesional",
    "pre profesional": "Preprofesional",
    "pre-profesional": "Preprofesional",
    "profesional": "Profesional",
}


def parse_careers(html: str) -> list[Career]:
    soup = BeautifulSoup(html, "html.parser")
    careers: dict[str, Career] = {}
    for field in soup.select('input[name="carrera"]'):
        career_id = (field.get("value") or "").strip()
        name = (field.get("data-nombre") or "").strip()
        if not career_id or not name or career_id in careers:
            continue
        careers[career_id] = Career(id=career_id, name=name)
    return list(careers.values())


def parse_date_value(value: str | None) -> date | None:
    text = clean_text(value)
    if not text:
        return None
    candidates = [text]
    iso_match = re.search(r"\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?", text)
    if iso_match:
        candidates.insert(0, iso_match.group(0))
    latin_match = re.search(r"\d{2}/\d{2}/\d{4}", text)
    if latin_match:
        candidates.insert(0, latin_match.group(0))
    for candidate in candidates:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(candidate).date()
        except ValueError:
            continue
    return None


def parse_amount(value: object) -> float | None:
    if isinstance(value, dict):
        return parse_amount(value.get("value"))
    if isinstance(value, list):
        return parse_amount(value[0]) if value else None
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    text = clean_text(str(value))
    text = re.sub(r"[^\d,.\-]", "", text)
    if not text:
        return None
    if "," in text and "." in text:
        decimal = "," if text.rfind(",") > text.rfind(".") else "."
        thousands = "." if decimal == "," else ","
        text = text.replace(thousands, "").replace(decimal, ".")
    elif "," in text:
        _, _, fraction = text.rpartition(",")
        text = text.replace(",", "") if len(fraction) == 3 else text.replace(",", ".")
    elif text.count(".") == 1:
        _, _, fraction = text.rpartition(".")
        if len(fraction) == 3 and len(text.split(".")[0]) > 3:
            text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return None


def format_salary(amount: float | None, currency: str | None) -> str | None:
    if amount is None:
        return None
    code = (currency or "PEN").upper()
    prefix = "S/" if code == "PEN" else code
    return f"{prefix} {amount:,.2f}"


def canonical_attendance(value: str | None) -> str | None:
    key = clean_text(value).casefold()
    for alias, canonical in ATTENDANCE_MAP.items():
        if key == alias or key.startswith(f"{alias} "):
            return canonical
    return clean_text(value) or None


def canonical_modality(value: str | None) -> str | None:
    key = clean_text(value).casefold().replace("-", " ")
    key = re.sub(r"\s+", " ", key).strip()
    return MODALITY_MAP.get(key, clean_text(value) or None)


def _label_value(soup: BeautifulSoup, label: str) -> str | None:
    wanted = label.casefold().rstrip(":")
    for strong in soup.find_all("strong"):
        text = clean_text(strong.get_text(" ", strip=True)).rstrip(":")
        if text.casefold() != wanted or strong.parent is None:
            continue
        parent = clean_text(strong.parent.get_text(" ", strip=True))
        if ":" in parent:
            value = parent.split(":", 1)[1].strip()
            return value or None
    return None


def _job_posting(html: str) -> dict[str, object] | None:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        try:
            payload = json.loads(raw, strict=False)
        except json.JSONDecodeError:
            LOGGER.warning("json-ld payload is not valid json")
            continue
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                return item
    return None


def _description_soup(posting: dict[str, object] | None, page: BeautifulSoup) -> BeautifulSoup:
    if posting and isinstance(posting.get("description"), str):
        return BeautifulSoup(posting["description"], "html.parser")
    return page


def _address_value(posting: dict[str, object]) -> dict[str, str]:
    location = posting.get("jobLocation") or {}
    if not isinstance(location, dict):
        return {}
    address = location.get("address") or {}
    if not isinstance(address, dict):
        return {}
    return {
        "district": clean_text(str(address.get("addressLocality") or "")),
        "department": clean_text(str(address.get("addressRegion") or "")),
    }


def _organization_name(posting: dict[str, object]) -> str | None:
    organization = posting.get("hiringOrganization") or {}
    if not isinstance(organization, dict):
        return None
    return clean_text(str(organization.get("name") or "")) or None


def _salary(posting: dict[str, object]) -> tuple[float | None, str | None, str | None]:
    salary = posting.get("baseSalary") or {}
    if not isinstance(salary, dict):
        return None, None, None
    currency = clean_text(str(salary.get("currency") or "")) or None
    amount = parse_amount(salary.get("value"))
    if amount is not None and amount <= 0:
        return None, None, currency
    return amount, format_salary(amount, currency), currency


def _strip_education(text: str) -> str:
    return re.sub(
        r"Formaci[oó]n acad[eé]mica:.*?(?="
        r"Otros requisitos:|Requisitos:|Funciones:|Conocimientos:|Beneficios:|"
        r"Plazo para postular:|Lugar de prácticas:|$)",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )


def parse_detail(html: str) -> DetailData:
    page = BeautifulSoup(html, "html.parser")
    posting = _job_posting(html)
    description = _description_soup(posting, page)

    if posting is None:
        title_node = page.find("h1")
        title = clean_text(title_node.get_text(" ", strip=True)) if title_node else None
        fallback_text = clean_text(page.get_text("\n", strip=True))
        return DetailData(
            title=title,
            requirements_text=fallback_text,
            skills_text=_strip_education(fallback_text),
        )

    address = _address_value(posting)
    amount, salary_text, currency = _salary(posting)
    published_raw = clean_text(str(posting.get("datePosted") or ""))
    deadline_raw = clean_text(str(posting.get("validThrough") or ""))
    district = smart_title(address.get("district"))
    department = smart_title(address.get("department"))
    location = None
    if district:
        location = f"{district}, {department}" if department else district

    attendance = _label_value(description, "Modalidad")
    modality = _label_value(description, "Modalidad de prácticas")
    requirements_text = clean_text(description.get_text("\n", strip=True))
    skills_text = clean_text(_strip_education(requirements_text))

    return DetailData(
        title=clean_text(str(posting.get("title") or "")) or None,
        company=_organization_name(posting),
        district=district,
        department=department,
        location=location,
        modality=canonical_modality(modality),
        attendance=canonical_attendance(attendance),
        salary_text=salary_text,
        salary_amount=amount,
        salary_currency=currency,
        published_at=parse_date_value(published_raw),
        published_raw=published_raw or None,
        deadline_at=parse_date_value(deadline_raw),
        deadline_raw=deadline_raw or None,
        requirements_text=requirements_text,
        skills_text=skills_text,
    )


def _value_after_label(text: str, label: str) -> str | None:
    prefix = f"{label}:"
    if prefix not in text:
        return None
    return clean_text(text.split(prefix, 1)[1]) or None


def parse_listing_cards(html: str) -> list[ListingCard]:
    soup = BeautifulSoup(html, "html.parser")
    cards: list[ListingCard] = []
    seen: set[str] = set()

    for article in soup.select("article"):
        title_link = article.select_one("h3 a[href]") or article.select_one(
            "a.btn--mas-informacion[href]"
        )
        if title_link is None:
            continue
        url = urljoin(BASE_URL, (title_link.get("href") or "").strip())
        if not url.startswith("https://www.practicas.pe/") or url in seen:
            continue
        seen.add(url)

        title = clean_text(title_link.get_text(" ", strip=True))
        company = None
        requirements = None
        for paragraph in article.select("p.text-dark-gray"):
            text = clean_text(paragraph.get_text(" ", strip=True))
            if text.startswith("Entidad:"):
                company = _value_after_label(text, "Entidad")
            elif text.startswith("Se requiere:"):
                requirements = _value_after_label(text, "Se requiere")

        location = None
        modality = None
        attendance = None
        deadline_text = None
        for badge in article.select(".badge"):
            classes = badge.get("class") or []
            text = clean_text(badge.get_text(" ", strip=True))
            if "badge--blue" in classes:
                location = text or None
            elif "badge--green" in classes:
                modality = text or None
            elif "badge--cyan" in classes:
                attendance = text or None
            elif "badge--orange" in classes:
                deadline_text = text or None

        cards.append(
            ListingCard(
                url=url,
                title=title,
                company=company,
                requirements=requirements,
                location=location,
                modality=modality,
                attendance=attendance,
                deadline_text=deadline_text,
            )
        )
    return cards


def parse_last_page(html: str) -> int | None:
    soup = BeautifulSoup(html, "html.parser")
    pages: list[int] = []
    for anchor in soup.select(".pagination a"):
        text = clean_text(anchor.get_text(" ", strip=True))
        if text.isdigit():
            pages.append(int(text))
    return max(pages) if pages else None
