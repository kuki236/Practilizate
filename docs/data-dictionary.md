# Data Dictionary — Practilizate

## `dim_fecha`

| Column | Type | Description |
|---|---|---|
| `date_id` | integer | Date key in `YYYYMMDD` format. |
| `date` | date | Calendar date. |
| `year` | integer | Year. |
| `month` | integer | Month number. |
| `day` | integer | Day of month. |
| `weekday` | integer | 1 = Monday, 7 = Sunday. |
| `is_weekend` | boolean | True for Saturday and Sunday. |

## `dim_empresa`

| Column | Type | Description |
|---|---|---|
| `company_id` | integer | Surrogate key. |
| `name` | text | Original company name. |
| `normalized_name` | text | Lowercase, accent-free, punctuation-normalized name. |

## `dim_ubicacion`

| Column | Type | Description |
|---|---|---|
| `location_id` | integer | Surrogate key. |
| `district` | text | District, when available. |
| `province` | text | Province, when available. |
| `department` | text | Department, when available. |

## `dim_carrera`

| Column | Type | Description |
|---|---|---|
| `career_id` | text | practicas.pe career filter ID. |
| `name` | text | Career name. |
| `normalized_name` | text | Lowercase, accent-free name. |

## `dim_habilidad`

| Column | Type | Description |
|---|---|---|
| `skill_id` | integer | Surrogate key. |
| `name` | text | Canonical skill name. |
| `normalized_name` | text | Lowercase, accent-free name. |

## `dim_modalidad`

| Column | Type | Description |
|---|---|---|
| `modality_id` | integer | Surrogate key. |
| `name` | text | `Preprofesional` or `Profesional`. |

## `dim_asistencia`

| Column | Type | Description |
|---|---|---|
| `attendance_id` | integer | Surrogate key. |
| `name` | text | `Presencial`, `Híbrido`, `Remoto`, or `No especificada`. |

## `fact_ofertas`

| Column | Type | Description |
|---|---|---|
| `offer_id` | text | Offer ID extracted from the URL or source. |
| `title` | text | Offer title. |
| `company_id` | integer | FK to `dim_empresa`. |
| `location_id` | integer | FK to `dim_ubicacion`. |
| `date_id` | integer | FK to `dim_fecha` based on publication date. |
| `modality_id` | integer | FK to `dim_modalidad`. |
| `attendance_id` | integer | FK to `dim_asistencia`. |
| `salary_amount` | numeric | Parsed monthly salary, null when unavailable. |
| `salary_text` | text | Original salary text. |
| `published_at` | timestamp | Publication timestamp. |
| `deadline_at` | timestamp | Application deadline. |
| `status` | text | `Vigente`, `Atención`, `Concluido`, etc. |
| `url` | text | Canonical offer URL. |
| `quality_score` | numeric | 0–100 score for the offer. |

## `bridge_oferta_carrera`

| Column | Type | Description |
|---|---|---|
| `offer_id` | text | FK to `fact_ofertas`. |
| `career_id` | text | FK to `dim_carrera`. |

## `bridge_oferta_habilidad`

| Column | Type | Description |
|---|---|---|
| `offer_id` | text | FK to `fact_ofertas`. |
| `skill_id` | integer | FK to `dim_habilidad`. |

## `dashboard_dataset.csv`

Flat export for Power BI. Required columns:

```text
offer_id
title
company
company_normalized
district
province
department
career
skill
modality
attendance
salary_amount
salary_text
published_at
deadline_at
status
url
quality_score
source_fetched_at
```

## `quality_report.json`

```json
{
  "run_id": "string",
  "generated_at": "ISO-8601",
  "total_offers": 0,
  "overall_score": 0.0,
  "rules": [
    {
      "rule_id": "string",
      "description": "string",
      "checked": 0,
      "failed": 0,
      "pass_rate": 0.0,
      "sample_offer_ids": []
    }
  ]
}
```

## `run_manifest.json`

```json
{
  "run_id": "string",
  "source": "fixtures",
  "as_of": "YYYY-MM-DD",
  "started_at": "ISO-8601",
  "finished_at": "ISO-8601",
  "counts": {
    "offers": 0,
    "companies": 0,
    "careers": 0,
    "skills": 0
  },
  "artifacts": {
    "quality_report": "path",
    "excel": "path",
    "dashboard_dataset": "path"
  },
  "checksums": {}
}
```
