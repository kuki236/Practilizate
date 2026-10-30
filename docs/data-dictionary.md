# Data Dictionary — Practilizate

This dictionary describes the normalized offer contract, the PostgreSQL star
schema, the CSV snapshot for Power BI, and the run artifacts.

## Normalized offer contract

The pipeline exposes one record per unique offer URL.

| Field | Type | Description |
|---|---|---|
| `offer_id` | text | Numeric suffix from the practicas.pe URL when present (for example `90001`), otherwise a stable hash. |
| `url` | text | Canonical public offer URL. Used as the deduplication key. |
| `title` | text | Published title, cleaned and whitespace-normalized. |
| `company` | text or null | Published company name. |
| `company_normalized` | text or null | Lowercase, accent-free key with legal suffixes removed. |
| `location` | text or null | District and department, for example `San Isidro, Lima`. |
| `district` | text or null | District as published. |
| `department` | text or null | Department/region as published. |
| `modality` | text or null | `Preprofesional` or `Profesional`. |
| `attendance` | text or null | `Presencial`, `Híbrido`, `Virtual`, or a kept unknown source value. |
| `salary_text` | text or null | Display text such as `S/ 1,230.00`; null when the source does not publish a salary. |
| `salary_amount` | number or null | Monthly amount in the published currency. Zero is treated as undisclosed. |
| `salary_currency` | text or null | ISO currency code, usually `PEN`. |
| `published_at` | date or null | Publication date; null when the source value is invalid. |
| `deadline_at` | date or null | Application deadline; null when absent. |
| `status` | text | `active`, `expiring_soon` (within 7 days of the reference date), `expired`, or `unknown`. |
| `quality_score` | number | Share of applicable quality rules passed by the offer, from 0 to 1. |
| `careers` | list of objects | Each item has `id` and `name`; preserved from every career query that returned the URL. |
| `skills` | list of text | Canonical skills extracted from the listing requirements. |
| `requirements_text` | text | Requirements and conditions with emails and phone numbers removed. |
| `source_fetched_at` | timestamp | Fetch timestamp of the detail page (fixtures use the deterministic reference date). |

## PostgreSQL star schema

The DDL is in `sql/schema.sql`. All loads run in one transaction and replace the
previous snapshot.

### `dim_fecha`

| Column | Type | Description |
|---|---|---|
| `date_id` | integer | `YYYYMMDD` key. |
| `date` | date | Calendar date. |
| `year`, `month`, `day` | integer | Calendar parts. |
| `weekday` | integer | ISO weekday, 1 = Monday and 7 = Sunday. |
| `is_weekend` | boolean | True for Saturday and Sunday. |

### `dim_empresa`

| Column | Type | Description |
|---|---|---|
| `company_id` | bigint | Stable key derived from `normalized_name`. |
| `name` | text | Display name from the first offer. |
| `normalized_name` | text | Normalized comparison key. |

### `dim_ubicacion`

| Column | Type | Description |
|---|---|---|
| `location_id` | bigint | Stable key derived from district and department. |
| `district` | text | District. |
| `province` | text | Province; v0.1 uses the department value. |
| `department` | text | Department. |

### `dim_carrera`

| Column | Type | Description |
|---|---|---|
| `career_id` | bigint | practicas.pe numeric career ID. |
| `name` | text | Career name as published by the filter. |
| `normalized_name` | text | Lowercase, accent-free name. |

### `dim_habilidad`

| Column | Type | Description |
|---|---|---|
| `skill_id` | bigint | Stable key derived from the canonical skill. |
| `name` | text | Canonical skill name. |
| `normalized_name` | text | Lowercase, accent-free name. |

### `dim_modalidad` and `dim_asistencia`

| Column | Type | Description |
|---|---|---|
| `modality_id` / `attendance_id` | bigint | Stable key derived from the name. |
| `name` | text | Published value. Unknown attendance values are kept for audit. |

### `fact_ofertas`

| Column | Type | Description |
|---|---|---|
| `offer_id` | bigint | Numeric source ID when available, otherwise a stable hash. |
| `title` | text | Offer title. |
| `company_id` | bigint or null | FK to `dim_empresa`. |
| `location_id` | bigint or null | FK to `dim_ubicacion`. |
| `date_id` | integer or null | FK to `dim_fecha` for the publication date. |
| `modality_id` | bigint or null | FK to `dim_modalidad`. |
| `attendance_id` | bigint or null | FK to `dim_asistencia`. |
| `salary_amount` | numeric(12,2) or null | Parsed monthly salary. |
| `salary_text` | text or null | Published salary text. |
| `published_at` | date or null | Publication date. |
| `deadline_at` | date or null | Application deadline. |
| `status` | text | `active`, `expiring_soon`, `expired`, or `unknown`. |
| `url` | text | Unique public URL. |
| `quality_score` | numeric(5,4) | 0–1 offer quality score. |

### Bridges

| Table | Key | Purpose |
|---|---|---|
| `bridge_oferta_carrera` | `(offer_id, career_id)` | One offer can belong to multiple careers. |
| `bridge_oferta_habilidad` | `(offer_id, skill_id)` | One offer can require multiple skills. |

### View

`v_dashboard_ofertas` joins the fact, dimensions, and bridges. It exposes
`careers` and `skills` as semicolon-separated strings, plus the publication year
and month. Use it for the optional PostgreSQL connection.

## `dashboard_dataset.csv`

Flat export for Power BI and other consumers. It is UTF-8 with BOM so Excel
opens accents correctly. `careers` and `skills` use `; ` separators.

```text
offer_id
url
title
company
company_normalized
location
district
department
modality
attendance
salary_text
salary_amount
salary_currency
published_at
deadline_at
status
career_count
careers
skill_count
skills
requirements_text
source_fetched_at
quality_score
days_to_deadline
```

`days_to_deadline` is `deadline_at - as_of`; negative values are expired offers.

## Power BI support CSV files

| File | Columns | Purpose |
|---|---|---|
| `offer_careers.csv` | `offer_id`, `career_id`, `career_name` | Career bridge for the semantic model. |
| `offer_skills.csv` | `offer_id`, `skill` | Skill bridge for the semantic model. |
| `quality_rules.csv` | `rule_id`, `description`, `description_es`, `severity`, `severity_es`, `checked`, `failed`, `pass_rate`, `sample_failed_offer_ids` | Quality page. |
| `run_metadata.csv` | `run_id`, `source`, `as_of`, `generated_at`, `runtime_seconds`, `offers`, `companies`, `careers`, `skills`, `quality_score`, `expiring`, `salary_average`, `last_updated` | Single-row metadata. |
| `dim_idioma.csv` | `Idioma`, `Etiqueta`, `Orden` | Disconnected ES/EN selector. |
| `dim_estado.csv` | `status`, `label_es`, `label_en`, `orden` | Bilingual status labels. |

## `quality_report.json`

```json
{
  "run_id": "string",
  "source": "fixtures",
  "as_of": "YYYY-MM-DD",
  "generated_at": "ISO-8601",
  "offers_checked": 12,
  "rules": [
    {
      "rule_id": "R01",
      "description": "Required fields: title, company, URL",
      "severity": "warning",
      "checked": 12,
      "failed": 1,
      "pass_rate": 0.9167,
      "sample_failed_offer_ids": ["90006"]
    }
  ],
  "overall_score": 0.9427,
  "critical_failures": [],
  "passed": true
}
```

Rule severities: `critical` for structural integrity (unique URL, absolute URL,
at least one career, fetch timestamp, normalized text) and `warning` for
publishable data gaps. Critical failures stop the pipeline.

## `run_manifest.json`

```json
{
  "run_id": "string",
  "source": "fixtures",
  "as_of": "YYYY-MM-DD",
  "started_at": "ISO-8601",
  "finished_at": "ISO-8601",
  "runtime_seconds": 1.47,
  "status": "completed",
  "quality": {
    "overall_score": 0.9427,
    "passed": true,
    "strict": false,
    "critical_failures": [],
    "failed_rules": ["R01", "R04"]
  },
  "counts": {
    "offers": 12,
    "careers": 3,
    "pages": 4,
    "listing_refs": 13,
    "duplicates": 1,
    "detail_failures": 0
  },
  "stages": {
    "ingest": {},
    "load": {},
    "export": {}
  },
  "artifacts": {},
  "outputs": {}
}
```

The E2E suite adds `checksums.sha256` and `checksum_count` to the manifest after
the run.

## Excel workbook

`practilizate.xlsx` is Spanish-first:

| Sheet | Content |
|---|---|
| `Portada` | Source, cutoff date, run ID, KPIs, reading guide, attribution. |
| `Datos` | Offer table with status and quality formatting. |
| `Resumen` | KPI cards, career filter, career/status tables and charts. |
| `Habilidades` | Skill demand and coverage by career. |
| `Empresas` | Company concentration and salary ranges. |
| `Calidad` | The 17 rules, failures, samples, and a failure chart. |
| `Diccionario` | Field definitions. |
| `Listas` | Hidden lists used by data validation. |

## Conventions

- Dates are stored as calendar dates; display format is `dd/mm/yyyy`.
- Currency display is `S/ 1,230.00`.
- Salary averages exclude values above `PRACTILIZATE_SALARY_MAX` (default `12000`).
- `province` is set to `department` in v0.1.
- Emails and phone numbers are replaced with `[contacto eliminado]` before
  persistence.
- Unknown source values are kept and flagged by the quality rules; they are not
  silently dropped.
