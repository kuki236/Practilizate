from datetime import date, datetime

from practilizate.ids import offer_external_id
from practilizate.models import Career, DetailData, ListingCard, Offer
from practilizate.parsing import canonical_attendance, canonical_modality, parse_date_value
from practilizate.skills import extract_skills
from practilizate.text import (
    clean_text,
    normalize_company,
    smart_title,
    strip_personal_data,
)


def offer_status(deadline: date | None, as_of: date) -> str:
    if deadline is None:
        return "unknown"
    if deadline < as_of:
        return "expired"
    if (deadline - as_of).days <= 7:
        return "expiring_soon"
    return "active"


def build_offer(
    *,
    url: str,
    card: ListingCard,
    detail: DetailData | None,
    careers: list[Career],
    as_of: date,
    fetched_at: datetime,
) -> Offer:
    has_detail = detail is not None
    data = detail or DetailData()
    title = clean_text(data.title or card.title) or "Sin título"

    if has_detail:
        company = clean_text(data.company or card.company) or None
        district = smart_title(data.district)
        department = smart_title(data.department)
        if data.location:
            location = data.location
        elif district:
            location = f"{district}, {department}" if department else district
        else:
            location = None
        attendance = data.attendance or canonical_attendance(card.attendance)
        modality = data.modality or canonical_modality(card.modality)
    else:
        company = clean_text(card.company) or None
        district = None
        department = None
        location = smart_title(card.location)
        attendance = canonical_attendance(card.attendance)
        modality = canonical_modality(card.modality)

    deadline = data.deadline_at
    if deadline is None and data.deadline_raw is None and card.deadline_text:
        deadline = parse_date_value(card.deadline_text)

    requirements_parts = [card.requirements or "", data.requirements_text]
    requirements_text = clean_text(" | ".join(part for part in requirements_parts if part))
    requirements_text = strip_personal_data(requirements_text)

    salary_amount = data.salary_amount
    salary_currency = data.salary_currency
    if salary_amount is not None and not salary_currency:
        salary_currency = "PEN"

    sorted_careers = sorted(
        careers, key=lambda career: int(career.id) if career.id.isdigit() else 0
    )

    skill_source = " ".join(part for part in (card.requirements or "", data.skills_text) if part)

    return Offer(
        offer_id=offer_external_id(url),
        url=url,
        title=title,
        company=company,
        company_normalized=normalize_company(company),
        location=location,
        district=district,
        department=department,
        modality=modality,
        attendance=attendance,
        salary_text=data.salary_text,
        salary_amount=salary_amount,
        salary_currency=salary_currency,
        published_at=data.published_at,
        deadline_at=deadline,
        status=offer_status(deadline, as_of),
        careers=sorted_careers,
        skills=extract_skills(skill_source),
        requirements_text=requirements_text,
        source_fetched_at=fetched_at,
    )
