import json
import unicodedata
from collections import Counter
from datetime import date
from html import escape
from pathlib import Path

from practilizate.export import ExportContext
from practilizate.logging import get_logger
from practilizate.models import Offer

LOGGER = get_logger("practilizate.report")

STATUS_ORDER = {"expiring_soon": 0, "active": 1, "unknown": 2, "expired": 3}
STATUS_LABELS_ES = {
    "active": "Vigente",
    "expiring_soon": "Por vencer",
    "expired": "Vencida",
    "unknown": "Sin fecha",
}

SOURCE_ES = {"fixtures": "Fixtures sintéticos", "live": "practicas.pe (en vivo)"}


def _days_to_deadline(offer: Offer, as_of: date) -> int | None:
    if offer.deadline_at is None:
        return None
    return (offer.deadline_at - as_of).days


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _sorted_offers(offers: list[Offer], as_of: date) -> list[Offer]:
    def key(offer: Offer) -> tuple[int, int, str]:
        days = _days_to_deadline(offer, as_of)
        return (
            STATUS_ORDER.get(offer.status, 9),
            days if days is not None else 99999,
            offer.title.casefold(),
        )

    return sorted(offers, key=key)


def _career_counts(offers: list[Offer]) -> list[dict[str, object]]:
    counts = Counter(career.name for offer in offers for career in offer.careers)
    return [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _skill_counts(offers: list[Offer]) -> list[dict[str, object]]:
    counts = Counter(skill for offer in offers for skill in offer.skills)
    return [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _average_salary(offers: list[Offer], salary_max: float) -> tuple[int, float]:
    reported = [offer.salary_amount for offer in offers if offer.salary_amount is not None]
    usable = [amount for amount in reported if amount <= salary_max]
    average = round(sum(usable) / len(usable), 2) if usable else 0.0
    return len(reported), average


def build_payload(offers: list[Offer], context: ExportContext) -> dict[str, object]:
    ordered = _sorted_offers(offers, context.as_of)
    careers = _career_counts(ordered)
    skills = _skill_counts(ordered)
    statuses = Counter(offer.status for offer in ordered)
    salary_count, salary_average = _average_salary(ordered, context.salary_max)
    return {
        "run": {
            "id": context.run_id,
            "source": context.source,
            "as_of": context.as_of.isoformat(),
            "generated_at": context.generated_at.isoformat(timespec="seconds"),
            "quality_score": context.quality.overall_score,
            "salary_max": context.salary_max,
        },
        "stats": {
            "offers": len(ordered),
            "companies": len({offer.company for offer in ordered if offer.company}),
            "careers": len({career.id for offer in ordered for career in offer.careers}),
            "skills": len({skill for offer in ordered for skill in offer.skills}),
            "expiring_soon": statuses.get("expiring_soon", 0),
            "expired": statuses.get("expired", 0),
            "salary_count": salary_count,
            "salary_average": salary_average,
        },
        "careers": careers,
        "skills": skills,
        "offers": [
            {
                "offer_id": offer.offer_id,
                "title": offer.title,
                "company": offer.company or "",
                "location": offer.location or "",
                "modality": offer.modality or "",
                "attendance": offer.attendance or "",
                "salary_amount": offer.salary_amount,
                "salary_text": offer.salary_text or "",
                "published_at": offer.published_at.isoformat() if offer.published_at else None,
                "deadline_at": offer.deadline_at.isoformat() if offer.deadline_at else None,
                "days_to_deadline": _days_to_deadline(offer, context.as_of),
                "status": offer.status,
                "careers": [career.name for career in offer.careers],
                "skills": offer.skills,
                "url": offer.url,
                "quality_score": round(offer.quality_score, 4),
            }
            for offer in ordered
        ],
    }


def _kpi(
    label_key: str,
    label_text: str,
    value: str,
    note_key: str = "",
    note_text: str = "",
) -> str:
    note_html = (
        f'<span class="kpi-note" data-i18n="{note_key}">{escape(note_text)}</span>'
        if note_key
        else ""
    )
    return (
        '<li class="kpi">'
        f'<span class="kpi-label" data-i18n="{label_key}">{escape(label_text)}</span>'
        f'<strong class="kpi-value">{escape(value)}</strong>'
        f"{note_html}"
        "</li>"
    )


def _bars(rows: list[dict[str, object]], limit: int, css_class: str) -> str:
    if not rows:
        return ""
    maximum = max(int(row["count"]) for row in rows)
    items = []
    for row in rows[:limit]:
        count = int(row["count"])
        width = round(count / maximum * 100, 1) if maximum else 0
        items.append(
            "<li>"
            f'<span class="bar-label">{escape(str(row["name"]))}</span>'
            '<span class="bar-track" aria-hidden="true">'
            f'<span class="bar" style="width: {width}%"></span></span>'
            f'<span class="bar-value">{count}</span>'
            "</li>"
        )
    return f'<ul class="bars {css_class}">{"".join(items)}</ul>'


def _card(offer: dict[str, object]) -> str:
    title = escape(str(offer["title"]))
    url = escape(str(offer["url"]), quote=True)
    status = str(offer["status"])
    status_label = STATUS_LABELS_ES.get(status, "Sin fecha")
    salary = offer["salary_amount"]
    deadline = offer["deadline_at"]
    days = offer["days_to_deadline"]
    quality = round(float(offer["quality_score"]) * 100)

    if offer["company"]:
        company = f'<p class="company">{escape(str(offer["company"]))}</p>'
    else:
        company = '<p class="company missing" data-missing="company">Empresa no publicada</p>'

    place = offer["location"]
    place_html = (
        escape(str(place))
        if place
        else '<span data-missing="location">Ubicación no publicada</span>'
    )
    details = " · ".join(
        part for part in (place_html, escape(str(offer["attendance"] or ""))) if part
    )

    if salary is not None:
        salary_html = f"<strong>S/ {float(salary):,.0f}</strong>"
    else:
        salary_html = '<strong data-missing="salary">No publicada</strong>'

    if deadline:
        day_text = f"{days} días" if days is not None else ""
        deadline_html = (
            f"<strong>{date.fromisoformat(str(deadline)).strftime('%d/%m/%Y')}</strong>"
            f'<span class="days" data-days="{days if days is not None else ""}">{day_text}</span>'
        )
    else:
        deadline_html = '<strong data-i18n="table.no_date">Sin fecha</strong>'

    careers = "".join(f'<span class="chip">{escape(name)}</span>' for name in offer["careers"])
    skills = "".join(f'<span class="chip skill">{escape(name)}</span>' for name in offer["skills"])
    chips = ""
    if careers or skills:
        chips = f'<div class="chips">{careers}{skills}</div>'

    search = _fold(
        " ".join(
            [
                str(offer["title"]),
                str(offer["company"]),
                str(offer["location"]),
                str(offer["modality"]),
                " ".join(str(name) for name in offer["careers"]),
                " ".join(str(name) for name in offer["skills"]),
            ]
        )
    )
    career_names = "|".join(str(name) for name in offer["careers"])

    return (
        '<article class="offer" '
        f'data-offer data-offer-id="{escape(str(offer["offer_id"]))}" '
        f'data-status="{escape(status)}" data-salary="{1 if salary is not None else 0}" '
        f'data-careers="{escape(career_names, quote=True)}" '
        f'data-search="{escape(search, quote=True)}">'
        '<div class="offer-top">'
        f'<span class="badge {escape(status)}" data-status-label="{escape(status)}">'
        f"{escape(status_label)}</span>"
        f'<span class="quality"><span data-i18n="card.quality">Calidad</span> {quality}%</span>'
        "</div>"
        f'<h3><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>'
        f"{company}"
        f'<p class="meta">{details}</p>'
        '<div class="facts">'
        '<div class="fact">'
        '<span class="fact-label" data-i18n="table.salary">Subvención</span>'
        f"{salary_html}"
        "</div>"
        '<div class="fact">'
        '<span class="fact-label" data-i18n="table.deadline">Vence</span>'
        f"{deadline_html}"
        "</div>"
        "</div>"
        f"{chips}"
        "</article>"
    )


def _career_options(careers: list[dict[str, object]]) -> str:
    return "".join(
        f'<option value="{escape(str(row["name"]), quote=True)}">'
        f"{escape(str(row['name']))} ({int(row['count'])})</option>"
        for row in careers
    )


def _status_options() -> str:
    return "".join(
        f'<option value="{status}" data-status-option="{status}">{label}</option>'
        for status, label in STATUS_LABELS_ES.items()
    )


def _html(payload: dict[str, object], context: ExportContext) -> str:
    stats = payload["stats"]
    careers = payload["careers"]
    skills = payload["skills"]
    ordered = payload["offers"]
    assert isinstance(stats, dict) and isinstance(careers, list) and isinstance(skills, list)
    assert isinstance(ordered, list)

    quality = f"{context.quality.overall_score * 100:.1f}%"
    average = f"S/ {float(stats['salary_average']):,.0f}"
    kpis = "".join(
        [
            _kpi("kpi.offers", "Ofertas", str(stats["offers"])),
            _kpi("kpi.companies", "Empresas", str(stats["companies"])),
            _kpi("kpi.careers", "Carreras", str(stats["careers"])),
            _kpi("kpi.skills", "Habilidades", str(stats["skills"])),
            _kpi("kpi.quality", "Calidad de datos", quality),
            _kpi(
                "kpi.expiring",
                "Vencen en 7 días",
                str(stats["expiring_soon"]),
                "kpi.expiring_note",
                "≤ 7 días",
            ),
            _kpi(
                "kpi.salary",
                "Subvención promedio",
                average,
                "kpi.salary_note",
                "sin atípicos",
            ),
        ]
    )
    cards = "".join(_card(offer) for offer in ordered)
    generated = context.generated_at.strftime("%d/%m/%Y %H:%M")
    run_meta = (
        f"Run {escape(context.run_id)} · "
        f"{escape(SOURCE_ES.get(context.source, context.source))} · "
        f"corte {context.as_of.strftime('%d/%m/%Y')}"
    )
    payload_json = json.dumps(payload, ensure_ascii=False, default=str).replace("</", "<\\/")

    html = _TEMPLATE
    html = html.replace("__KPIS__", kpis)
    html = html.replace("__CARDS__", cards)
    html = html.replace("__CAREER_BARS__", _bars(careers, 8, "careers"))
    html = html.replace("__SKILL_BARS__", _bars(skills, 8, "skills"))
    html = html.replace("__CAREER_OPTIONS__", _career_options(careers))
    html = html.replace("__STATUS_OPTIONS__", _status_options())
    html = html.replace("__TOTAL__", str(stats["offers"]))
    html = html.replace("__RUN_META__", run_meta)
    html = html.replace("__GENERATED__", generated)
    return html.replace("__DATA__", payload_json)


def write_html_report(offers: list[Offer], context: ExportContext, path: Path) -> int:
    payload = build_payload(offers, context)
    path.parent.mkdir(parents=True, exist_ok=True)
    html = _html(payload, context)
    temp_path = path.with_suffix(".html.tmp")
    temp_path.write_text(html, encoding="utf-8", newline="\n")
    temp_path.replace(path)
    LOGGER.info(
        "html report written",
        extra={"path": str(path), "offers": len(offers), "bytes": len(html.encode("utf-8"))},
    )
    return len(offers)


_TEMPLATE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Reporte portátil de ofertas de prácticas preprofesionales en Perú.">
<title>Practilizate · Observatorio de prácticas</title>
<style>
:root {
  --navy: #17324d;
  --blue: #2e75b6;
  --ink: #1f2937;
  --muted: #5b6776;
  --bg: #f4f7fb;
  --card: #ffffff;
  --line: #dbe3ee;
  --green: #2f6b1f;
  --green-bg: #e2efda;
  --amber: #8a5a00;
  --amber-bg: #fff2cc;
  --red: #a11b1b;
  --red-bg: #fce4e4;
  --gray: #4b5563;
  --gray-bg: #eef1f5;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  color: var(--ink);
  background: var(--bg);
  font-family: "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif;
  line-height: 1.5;
}
a { color: var(--blue); }
.wrap { width: min(1180px, calc(100% - 2rem)); margin-inline: auto; }
.skip-link {
  position: absolute;
  left: 1rem;
  top: -3rem;
  z-index: 10;
  padding: .6rem 1rem;
  background: #fff;
  color: var(--navy);
  border-radius: .5rem;
}
.skip-link:focus { top: 1rem; }
.hero {
  background: linear-gradient(135deg, #132b42, #245a8a);
  color: #fff;
  padding: 2.4rem 0 3.2rem;
}
.hero-row { display: flex; justify-content: space-between; gap: 1.5rem; align-items: flex-start; }
.eyebrow {
  margin: 0 0 .4rem;
  text-transform: uppercase;
  letter-spacing: .14em;
  font-size: .74rem;
  font-weight: 700;
  color: #a9cdf0;
}
.hero h1 { margin: 0; font-size: clamp(1.6rem, 3vw, 2.4rem); line-height: 1.15; }
.lede { margin: .6rem 0 0; max-width: 60ch; color: #dbe9f7; }
.run-meta { margin: .9rem 0 0; font-size: .82rem; color: #b9d2e8; }
.lang { display: inline-flex; border: 1px solid rgba(255,255,255,.45); border-radius: 999px; overflow: hidden; }
.lang-btn {
  background: transparent;
  color: #fff;
  border: 0;
  padding: .4rem .85rem;
  font: inherit;
  font-weight: 700;
  font-size: .82rem;
  cursor: pointer;
}
.lang-btn[aria-pressed="true"] { background: #fff; color: var(--navy); }
main { padding: 0 0 3rem; }
.kpis {
  list-style: none;
  margin: -1.6rem 0 1.6rem;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr));
  gap: .8rem;
}
.kpi {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: .9rem;
  padding: .9rem 1rem;
  box-shadow: 0 6px 16px rgba(15, 35, 60, .08);
}
.kpi-label { display: block; font-size: .74rem; font-weight: 700; letter-spacing: .03em; text-transform: uppercase; color: var(--muted); }
.kpi-value { display: block; font-size: 1.55rem; line-height: 1.2; color: var(--navy); }
.kpi-note { display: block; font-size: .72rem; color: var(--muted); }
.panels { display: grid; grid-template-columns: repeat(auto-fit, minmax(21rem, 1fr)); gap: 1rem; margin-bottom: 1.4rem; }
.panel {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: .9rem;
  padding: 1rem 1.1rem 1.2rem;
}
.panel h2 { margin: 0; font-size: 1.05rem; color: var(--navy); }
.panel p { margin: .25rem 0 .9rem; font-size: .8rem; color: var(--muted); }
.bars { list-style: none; margin: 0; padding: 0; display: grid; gap: .55rem; }
.bars li { display: grid; grid-template-columns: minmax(7rem, 12rem) 1fr 2.2rem; gap: .6rem; align-items: center; font-size: .82rem; }
.bar-label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-track { height: .55rem; border-radius: 999px; background: #e8eef6; overflow: hidden; }
.bar { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, #4a90d9, var(--navy)); }
.bars.skills .bar { background: linear-gradient(90deg, #6ea54d, var(--green)); }
.bar-value { text-align: right; font-variant-numeric: tabular-nums; color: var(--muted); }
.filters {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: .9rem;
  padding: 1rem 1.1rem;
  margin-bottom: 1.4rem;
}
.filter-grid { display: grid; grid-template-columns: 2fr 1.2fr 1fr auto auto; gap: .8rem; align-items: end; }
.field { display: grid; gap: .3rem; font-size: .78rem; font-weight: 700; color: var(--muted); }
.field input, .field select {
  width: 100%;
  padding: .55rem .65rem;
  border: 1px solid #b9c6d8;
  border-radius: .55rem;
  background: #fff;
  color: var(--ink);
  font: inherit;
  font-size: .9rem;
}
.field input:focus, .field select:focus, button:focus-visible, a:focus-visible {
  outline: 3px solid rgba(46, 117, 182, .45);
  outline-offset: 1px;
}
.check { display: flex; align-items: center; gap: .45rem; font-size: .82rem; color: var(--ink); padding-bottom: .55rem; }
.check input { width: 1rem; height: 1rem; }
.reset {
  padding: .55rem .85rem;
  border: 1px solid #b9c6d8;
  border-radius: .55rem;
  background: #f7f9fc;
  color: var(--navy);
  font: inherit;
  font-size: .85rem;
  font-weight: 700;
  cursor: pointer;
}
.reset:hover { background: #edf3fa; }
.section-head { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; margin-bottom: .7rem; }
.section-head h2 { margin: 0; font-size: 1.25rem; color: var(--navy); }
#result-count { margin: 0; font-size: .82rem; color: var(--muted); }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr)); gap: 1rem; }
.offer {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: .9rem;
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: .5rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .05);
}
.offer[hidden] { display: none; }
.offer-top { display: flex; justify-content: space-between; align-items: center; gap: .5rem; }
.offer h3 { margin: 0; font-size: 1.05rem; line-height: 1.3; }
.offer h3 a { color: var(--navy); text-decoration: none; }
.offer h3 a:hover { text-decoration: underline; }
.company { margin: 0; font-weight: 600; }
.meta { margin: 0; color: var(--muted); font-size: .85rem; }
.missing { color: var(--muted); font-style: italic; font-weight: 500; }
.facts { display: flex; gap: 1.6rem; flex-wrap: wrap; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: .55rem 0; }
.fact { display: grid; gap: .1rem; }
.fact-label { font-size: .68rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); }
.fact strong { color: var(--ink); font-variant-numeric: tabular-nums; }
.days { display: block; font-size: .74rem; color: var(--muted); }
.chips { display: flex; flex-wrap: wrap; gap: .3rem; margin-top: auto; padding-top: .15rem; }
.chip { font-size: .72rem; padding: .16rem .5rem; border-radius: 999px; background: #edf3fa; color: #245a8a; }
.chip.skill { background: #eef6ea; color: #3f6428; }
.badge { font-size: .72rem; font-weight: 700; padding: .2rem .55rem; border-radius: 999px; border: 1px solid transparent; }
.badge.active { background: var(--green-bg); color: var(--green); }
.badge.expiring_soon { background: var(--amber-bg); color: var(--amber); }
.badge.expired { background: var(--red-bg); color: var(--red); }
.badge.unknown { background: var(--gray-bg); color: var(--gray); }
.quality { font-size: .72rem; color: var(--muted); }
#empty-state { margin: 1.5rem 0; padding: 1.2rem; text-align: center; background: var(--card); border: 1px dashed #b9c6d8; border-radius: .9rem; color: var(--muted); }
.footer { background: #132b42; color: #c7d8e8; padding: 1.6rem 0 2rem; font-size: .82rem; }
.footer p { margin: .25rem 0; }
.footer strong { color: #fff; }
.fine { color: #9fb8ce; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
@media (max-width: 900px) {
  .filter-grid { grid-template-columns: 1fr 1fr; }
  .check { padding-bottom: 0; }
}
@media (max-width: 620px) {
  .hero-row { flex-direction: column; }
  .filter-grid { grid-template-columns: 1fr; }
  .bars li { grid-template-columns: minmax(5rem, 8rem) 1fr 2rem; }
}
@media print {
  .hero { background: #fff; color: #000; padding-bottom: 1rem; }
  .lede, .run-meta, .lang, .filters, .skip-link { display: none; }
  .kpis { margin-top: .5rem; }
  .kpi, .panel, .offer { box-shadow: none; break-inside: avoid; }
  .footer { background: #fff; color: #000; }
}
</style>
</head>
<body>
<a class="skip-link" href="#ofertas" data-i18n="skip">Saltar a las ofertas</a>
<header class="hero">
  <div class="wrap hero-row">
    <div>
      <p class="eyebrow">Practilizate</p>
      <h1 data-i18n="hero.title">Observatorio de prácticas preprofesionales</h1>
      <p class="lede" data-i18n="hero.subtitle">Ofertas públicas de practicas.pe, normalizadas y auditadas.</p>
      <p class="run-meta">__RUN_META__</p>
    </div>
    <div class="lang" role="group" aria-label="Idioma / Language">
      <button type="button" class="lang-btn" data-lang="es" aria-pressed="true">ES</button>
      <button type="button" class="lang-btn" data-lang="en" aria-pressed="false">EN</button>
    </div>
  </div>
</header>
<main class="wrap">
  <h2 class="sr-only" data-i18n="kpi.title">Indicadores</h2>
  <ul class="kpis">__KPIS__</ul>
  <div class="panels">
    <section class="panel" aria-labelledby="careers-chart-title">
      <h2 id="careers-chart-title" data-i18n="charts.careers">Ofertas por carrera</h2>
      <p data-i18n="charts.careers_hint">Una oferta puede cubrir varias carreras.</p>
      <div id="careers-chart">__CAREER_BARS__</div>
    </section>
    <section class="panel" aria-labelledby="skills-chart-title">
      <h2 id="skills-chart-title" data-i18n="charts.skills">Habilidades más pedidas</h2>
      <p data-i18n="charts.skills_hint">Ofertas que mencionan cada habilidad.</p>
      <div id="skills-chart">__SKILL_BARS__</div>
    </section>
  </div>
  <section class="filters" aria-labelledby="filters-title">
    <h2 id="filters-title" class="sr-only" data-i18n="filters.title">Filtros</h2>
    <div class="filter-grid">
      <label class="field">
        <span data-i18n="filters.search">Buscar</span>
        <input id="q" type="search" placeholder="Cargo, empresa, carrera o habilidad" data-i18n-placeholder="filters.placeholder" autocomplete="off">
      </label>
      <label class="field">
        <span data-i18n="filters.career">Carrera</span>
        <select id="career-filter">
          <option value="" data-i18n="filters.all_careers">Todas las carreras</option>
          __CAREER_OPTIONS__
        </select>
      </label>
      <label class="field">
        <span data-i18n="filters.status">Estado</span>
        <select id="status-filter">
          <option value="" data-i18n="filters.all_statuses">Todos los estados</option>
          __STATUS_OPTIONS__
        </select>
      </label>
      <label class="check"><input id="salary-only" type="checkbox"> <span data-i18n="filters.salary_only">Solo con subvención</span></label>
      <button type="button" id="reset-filters" class="reset" data-i18n="filters.reset">Limpiar filtros</button>
    </div>
  </section>
  <section id="ofertas" aria-labelledby="offers-title">
    <div class="section-head">
      <h2 id="offers-title" data-i18n="offers.title">Ofertas</h2>
      <p id="result-count" aria-live="polite">__TOTAL__ de __TOTAL__ ofertas</p>
    </div>
    <div class="grid">__CARDS__</div>
    <p id="empty-state" hidden data-i18n="offers.empty">No hay ofertas que coincidan con los filtros.</p>
  </section>
</main>
<footer class="footer">
  <div class="wrap">
    <p><strong>Practilizate</strong> · <span data-i18n="footer.built">Reporte generado</span> __GENERATED__</p>
    <p data-i18n="footer.source">Datos públicos de practicas.pe.</p>
    <p data-i18n="footer.note">Practilizate no está afiliado a practicas.pe. Solo se publican datos agregados; no se incluyen datos personales.</p>
    <p class="fine">__RUN_META__</p>
  </div>
</footer>
<script id="practilizate-data" type="application/json">__DATA__</script>
<script>
(function () {
  "use strict";
  const I18N = {
    es: {
      "skip": "Saltar a las ofertas",
      "hero.title": "Observatorio de prácticas preprofesionales",
      "hero.subtitle": "Ofertas públicas de practicas.pe, normalizadas y auditadas.",
      "kpi.title": "Indicadores",
      "kpi.offers": "Ofertas",
      "kpi.companies": "Empresas",
      "kpi.careers": "Carreras",
      "kpi.skills": "Habilidades",
      "kpi.quality": "Calidad de datos",
      "kpi.expiring": "Vencen en 7 días",
      "kpi.expiring_note": "≤ 7 días",
      "kpi.salary": "Subvención promedio",
      "kpi.salary_note": "sin atípicos",
      "charts.careers": "Ofertas por carrera",
      "charts.careers_hint": "Una oferta puede cubrir varias carreras.",
      "charts.skills": "Habilidades más pedidas",
      "charts.skills_hint": "Ofertas que mencionan cada habilidad.",
      "filters.title": "Filtros",
      "filters.search": "Buscar",
      "filters.placeholder": "Cargo, empresa, carrera o habilidad",
      "filters.career": "Carrera",
      "filters.all_careers": "Todas las carreras",
      "filters.status": "Estado",
      "filters.all_statuses": "Todos los estados",
      "filters.salary_only": "Solo con subvención",
      "filters.reset": "Limpiar filtros",
      "results": "{shown} de {total} ofertas",
      "offers.title": "Ofertas",
      "offers.empty": "No hay ofertas que coincidan con los filtros.",
      "table.salary": "Subvención",
      "table.deadline": "Vence",
      "table.no_date": "Sin fecha",
      "card.quality": "Calidad",
      "days": "{n} días",
      "status.active": "Vigente",
      "status.expiring_soon": "Por vencer",
      "status.expired": "Vencida",
      "status.unknown": "Sin fecha",
      "missing.company": "Empresa no publicada",
      "missing.location": "Ubicación no publicada",
      "missing.salary": "No publicada",
      "footer.built": "Reporte generado",
      "footer.source": "Datos públicos de practicas.pe.",
      "footer.note": "Practilizate no está afiliado a practicas.pe. Solo se publican datos agregados; no se incluyen datos personales."
    },
    en: {
      "skip": "Skip to offers",
      "hero.title": "Pre-professional internship observatory",
      "hero.subtitle": "Public practicas.pe listings, normalized and audited.",
      "kpi.title": "Indicators",
      "kpi.offers": "Offers",
      "kpi.companies": "Companies",
      "kpi.careers": "Careers",
      "kpi.skills": "Skills",
      "kpi.quality": "Data quality",
      "kpi.expiring": "Expiring in 7 days",
      "kpi.expiring_note": "≤ 7 days",
      "kpi.salary": "Average salary",
      "kpi.salary_note": "outliers excluded",
      "charts.careers": "Offers by career",
      "charts.careers_hint": "One offer can cover several careers.",
      "charts.skills": "Most requested skills",
      "charts.skills_hint": "Offers that mention each skill.",
      "filters.title": "Filters",
      "filters.search": "Search",
      "filters.placeholder": "Role, company, career, or skill",
      "filters.career": "Career",
      "filters.all_careers": "All careers",
      "filters.status": "Status",
      "filters.all_statuses": "All statuses",
      "filters.salary_only": "With salary only",
      "filters.reset": "Clear filters",
      "results": "{shown} of {total} offers",
      "offers.title": "Offers",
      "offers.empty": "No offers match the current filters.",
      "table.salary": "Salary",
      "table.deadline": "Deadline",
      "table.no_date": "No date",
      "card.quality": "Quality",
      "days": "{n} days",
      "status.active": "Active",
      "status.expiring_soon": "Expiring soon",
      "status.expired": "Expired",
      "status.unknown": "No date",
      "missing.company": "Company not published",
      "missing.location": "Location not published",
      "missing.salary": "Not published",
      "footer.built": "Report generated",
      "footer.source": "Public data from practicas.pe.",
      "footer.note": "Practilizate is not affiliated with practicas.pe. Only aggregated data is published; no personal data is included."
    }
  };
  const cards = Array.from(document.querySelectorAll("[data-offer]"));
  const search = document.getElementById("q");
  const career = document.getElementById("career-filter");
  const status = document.getElementById("status-filter");
  const salaryOnly = document.getElementById("salary-only");
  const resultCount = document.getElementById("result-count");
  const emptyState = document.getElementById("empty-state");
  let visibleCount = cards.length;
  let language = "es";

  function fold(value) {
    return value.normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase();
  }

  function updateCount() {
    const template = I18N[language].results;
    resultCount.textContent = template
      .replace("{shown}", String(visibleCount))
      .replace("{total}", String(cards.length));
    emptyState.hidden = visibleCount !== 0;
  }

  function applyFilters() {
    const query = fold(search.value.trim());
    const selectedCareer = career.value;
    const selectedStatus = status.value;
    const needsSalary = salaryOnly.checked;
    let shown = 0;
    cards.forEach(function (card) {
      const matchesQuery = !query || (card.getAttribute("data-search") || "").indexOf(query) !== -1;
      const careers = (card.getAttribute("data-careers") || "").split("|");
      const matchesCareer = !selectedCareer || careers.indexOf(selectedCareer) !== -1;
      const matchesStatus = !selectedStatus || card.getAttribute("data-status") === selectedStatus;
      const matchesSalary = !needsSalary || card.getAttribute("data-salary") === "1";
      const visible = matchesQuery && matchesCareer && matchesStatus && matchesSalary;
      card.hidden = !visible;
      if (visible) shown += 1;
    });
    visibleCount = shown;
    updateCount();
  }

  function setLanguage(next) {
    language = I18N[next] ? next : "es";
    const dict = I18N[language];
    document.documentElement.lang = language;
    document.querySelectorAll("[data-i18n]").forEach(function (element) {
      const key = element.getAttribute("data-i18n");
      if (dict[key]) element.textContent = dict[key];
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(function (element) {
      const key = element.getAttribute("data-i18n-placeholder");
      if (dict[key]) element.setAttribute("placeholder", dict[key]);
    });
    document.querySelectorAll("[data-status-label]").forEach(function (element) {
      const key = "status." + element.getAttribute("data-status-label");
      if (dict[key]) element.textContent = dict[key];
    });
    document.querySelectorAll("[data-status-option]").forEach(function (element) {
      const key = "status." + element.getAttribute("data-status-option");
      if (dict[key]) element.textContent = dict[key];
    });
    document.querySelectorAll("[data-days]").forEach(function (element) {
      const value = element.getAttribute("data-days");
      element.textContent = value === "" ? dict["table.no_date"] : dict.days.replace("{n}", value);
    });
    document.querySelectorAll("[data-missing]").forEach(function (element) {
      const key = "missing." + element.getAttribute("data-missing");
      if (dict[key]) element.textContent = dict[key];
    });
    document.querySelectorAll("[data-lang]").forEach(function (button) {
      button.setAttribute("aria-pressed", String(button.getAttribute("data-lang") === language));
    });
    try {
      window.localStorage.setItem("practilizate-lang", language);
    } catch (error) {
      /* storage can be unavailable in private contexts */
    }
    updateCount();
  }

  document.querySelectorAll("[data-lang]").forEach(function (button) {
    button.addEventListener("click", function () {
      setLanguage(button.getAttribute("data-lang"));
    });
  });
  [search, career, status, salaryOnly].forEach(function (control) {
    control.addEventListener("input", applyFilters);
    control.addEventListener("change", applyFilters);
  });
  document.getElementById("reset-filters").addEventListener("click", function () {
    search.value = "";
    career.value = "";
    status.value = "";
    salaryOnly.checked = false;
    applyFilters();
    search.focus();
  });
  document.addEventListener("keydown", function (event) {
    const tag = document.activeElement ? document.activeElement.tagName : "";
    if (event.key === "/" && tag !== "INPUT" && tag !== "SELECT" && tag !== "TEXTAREA") {
      event.preventDefault();
      search.focus();
    }
  });

  let saved = "es";
  try {
    saved = window.localStorage.getItem("practilizate-lang") || "es";
  } catch (error) {
    saved = "es";
  }
  setLanguage(saved);
  applyFilters();
})();
</script>
</body>
</html>
"""
