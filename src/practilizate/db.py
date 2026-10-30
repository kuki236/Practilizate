from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from practilizate.ids import date_id, stable_id
from practilizate.logging import get_logger
from practilizate.models import Offer
from practilizate.text import normalize_key

LOGGER = get_logger("practilizate.db")

TABLES_IN_TRUNCATE_ORDER = (
    "bridge_oferta_habilidad",
    "bridge_oferta_carrera",
    "fact_ofertas",
    "dim_fecha",
    "dim_empresa",
    "dim_ubicacion",
    "dim_carrera",
    "dim_habilidad",
    "dim_modalidad",
    "dim_asistencia",
)


@dataclass
class LoadResult:
    counts: dict[str, int]


def _apply_schema(connection: Connection, schema_sql: str) -> None:
    connection.exec_driver_sql(schema_sql)


def _weekday_fields(value: date) -> dict[str, object]:
    iso_weekday = value.isoweekday()
    return {
        "date_id": date_id(value),
        "date": value,
        "year": value.year,
        "month": value.month,
        "day": value.day,
        "weekday": iso_weekday,
        "is_weekend": iso_weekday >= 6,
    }


def _offer_fact_id(offer: Offer) -> int:
    if offer.offer_id.isdigit():
        return int(offer.offer_id)
    return stable_id(f"offer:{offer.url}")


def load_offers(offers: list[Offer], database_url: str, sql_dir: Path) -> LoadResult:
    schema_path = sql_dir / "schema.sql"
    if not schema_path.is_file():
        raise FileNotFoundError(f"schema file not found: {schema_path}")
    schema_sql = schema_path.read_text(encoding="utf-8")

    companies: dict[int, tuple[str, str]] = {}
    locations: dict[int, tuple[str | None, str | None, str | None]] = {}
    careers: dict[int, tuple[str, str]] = {}
    skills: dict[int, tuple[str, str]] = {}
    modalities: dict[int, str] = {}
    attendances: dict[int, str] = {}
    dates: dict[int, date] = {}

    for offer in offers:
        if offer.company_normalized:
            company_id = stable_id(f"company:{offer.company_normalized}")
            companies.setdefault(
                company_id, (offer.company or offer.company_normalized, offer.company_normalized)
            )
        if offer.district:
            location_key = f"{offer.district}|{offer.department or ''}"
            location_id = stable_id(f"location:{location_key}")
            locations.setdefault(
                location_id,
                (offer.district, offer.department, offer.department),
            )
        for career in offer.careers:
            career_key = int(career.id) if career.id.isdigit() else stable_id(f"career:{career.id}")
            careers.setdefault(career_key, (career.name, normalize_key(career.name)))
        for skill in offer.skills:
            skill_id = stable_id(f"skill:{normalize_key(skill)}")
            skills.setdefault(skill_id, (skill, normalize_key(skill)))
        if offer.modality:
            modality_id = stable_id(f"modality:{offer.modality}")
            modalities.setdefault(modality_id, offer.modality)
        if offer.attendance:
            attendance_id = stable_id(f"attendance:{offer.attendance}")
            attendances.setdefault(attendance_id, offer.attendance)
        for value in (offer.published_at, offer.deadline_at):
            if value is not None:
                dates.setdefault(date_id(value), value)

    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            _apply_schema(connection, schema_sql)
            connection.execute(
                text(
                    f"truncate table {', '.join(TABLES_IN_TRUNCATE_ORDER)} restart identity cascade"
                )
            )

            connection.execute(
                text(
                    "insert into dim_fecha "
                    "(date_id, date, year, month, day, weekday, is_weekend) "
                    "values (:date_id, :date, :year, :month, :day, :weekday, :is_weekend)"
                ),
                [_weekday_fields(value) for value in dates.values()],
            )
            connection.execute(
                text(
                    "insert into dim_empresa (company_id, name, normalized_name) "
                    "values (:company_id, :name, :normalized_name) on conflict do nothing"
                ),
                [
                    {"company_id": key, "name": name, "normalized_name": normalized}
                    for key, (name, normalized) in companies.items()
                ],
            )
            connection.execute(
                text(
                    "insert into dim_ubicacion (location_id, district, province, department) "
                    "values (:location_id, :district, :province, :department) on conflict do nothing"
                ),
                [
                    {
                        "location_id": key,
                        "district": district,
                        "province": province,
                        "department": department,
                    }
                    for key, (district, province, department) in locations.items()
                ],
            )
            connection.execute(
                text(
                    "insert into dim_carrera (career_id, name, normalized_name) "
                    "values (:career_id, :name, :normalized_name) on conflict do nothing"
                ),
                [
                    {"career_id": key, "name": name, "normalized_name": normalized}
                    for key, (name, normalized) in careers.items()
                ],
            )
            connection.execute(
                text(
                    "insert into dim_habilidad (skill_id, name, normalized_name) "
                    "values (:skill_id, :name, :normalized_name) on conflict do nothing"
                ),
                [
                    {"skill_id": key, "name": name, "normalized_name": normalized}
                    for key, (name, normalized) in skills.items()
                ],
            )
            connection.execute(
                text(
                    "insert into dim_modalidad (modality_id, name) "
                    "values (:modality_id, :name) on conflict do nothing"
                ),
                [{"modality_id": key, "name": name} for key, name in modalities.items()],
            )
            connection.execute(
                text(
                    "insert into dim_asistencia (attendance_id, name) "
                    "values (:attendance_id, :name) on conflict do nothing"
                ),
                [{"attendance_id": key, "name": name} for key, name in attendances.items()],
            )

            fact_rows = []
            bridge_career_rows = set()
            bridge_skill_rows = set()
            for offer in offers:
                fact_id = _offer_fact_id(offer)
                location_id = (
                    stable_id(f"location:{offer.district}|{offer.department or ''}")
                    if offer.district
                    else None
                )
                fact_rows.append(
                    {
                        "offer_id": fact_id,
                        "title": offer.title,
                        "company_id": (
                            stable_id(f"company:{offer.company_normalized}")
                            if offer.company_normalized
                            else None
                        ),
                        "location_id": location_id,
                        "date_id": date_id(offer.published_at) if offer.published_at else None,
                        "modality_id": (
                            stable_id(f"modality:{offer.modality}") if offer.modality else None
                        ),
                        "attendance_id": (
                            stable_id(f"attendance:{offer.attendance}")
                            if offer.attendance
                            else None
                        ),
                        "salary_amount": offer.salary_amount,
                        "salary_text": offer.salary_text,
                        "published_at": offer.published_at,
                        "deadline_at": offer.deadline_at,
                        "status": offer.status,
                        "url": offer.url,
                        "quality_score": offer.quality_score,
                    }
                )
                for career in offer.careers:
                    career_key = (
                        int(career.id) if career.id.isdigit() else stable_id(f"career:{career.id}")
                    )
                    bridge_career_rows.add((fact_id, career_key))
                for skill in offer.skills:
                    bridge_skill_rows.add((fact_id, stable_id(f"skill:{normalize_key(skill)}")))

            connection.execute(
                text(
                    "insert into fact_ofertas "
                    "(offer_id, title, company_id, location_id, date_id, modality_id, "
                    "attendance_id, salary_amount, salary_text, published_at, deadline_at, "
                    "status, url, quality_score) values "
                    "(:offer_id, :title, :company_id, :location_id, :date_id, :modality_id, "
                    ":attendance_id, :salary_amount, :salary_text, :published_at, :deadline_at, "
                    ":status, :url, :quality_score)"
                ),
                fact_rows,
            )
            connection.execute(
                text(
                    "insert into bridge_oferta_carrera (offer_id, career_id) "
                    "values (:offer_id, :career_id)"
                ),
                [
                    {"offer_id": offer_id, "career_id": career_id}
                    for offer_id, career_id in sorted(bridge_career_rows)
                ],
            )
            connection.execute(
                text(
                    "insert into bridge_oferta_habilidad (offer_id, skill_id) "
                    "values (:offer_id, :skill_id)"
                ),
                [
                    {"offer_id": offer_id, "skill_id": skill_id}
                    for offer_id, skill_id in sorted(bridge_skill_rows)
                ],
            )

            counts = {
                "fact_ofertas": len(fact_rows),
                "dim_fecha": len(dates),
                "dim_empresa": len(companies),
                "dim_ubicacion": len(locations),
                "dim_carrera": len(careers),
                "dim_habilidad": len(skills),
                "dim_modalidad": len(modalities),
                "dim_asistencia": len(attendances),
                "bridge_oferta_carrera": len(bridge_career_rows),
                "bridge_oferta_habilidad": len(bridge_skill_rows),
            }
    finally:
        engine.dispose()

    LOGGER.info("database load finished", extra={"counts": counts})
    return LoadResult(counts=counts)
