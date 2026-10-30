# Practilizate — Technical Specification

## 1. Summary

Practilizate is an open, reproducible observatory of pre-professional internship offers in Peru. It ingests public listings from practicas.pe, normalizes them, validates data quality, loads a star schema into PostgreSQL, exports a Power BI-ready dataset and an Excel workbook, and publishes a bilingual dashboard.

The product answers questions such as:

- Which skills are most requested by career and district?
- Which companies publish the most internship offers?
- What salary ranges appear by role and career?
- Which offers are about to expire?
- How complete and reliable is the published data?

## 2. Problem

Students apply to internships without comparable data about salaries, companies, required skills, deadlines, or career fit. University career centers also lack a current, structured view of the market.

The 73 offers used during the initial exploration are only a pilot subset: Systems Engineering, Lima, pre-professional. The product must support all careers.

## 3. Users

- Students looking for internships.
- University career centers and employability teams.
- Researchers and journalists analyzing the Peruvian internship market.
- The project author, as a portfolio product for data/BI roles.

## 4. Scope

### v0.1

- All careers available in the practicas.pe career filter.
- Department: Lima.
- Modality: pre-professional.
- Sort: newest offers.
- Public listings only.
- Bilingual dashboard (Spanish primary, English toggle).
- Excel workbook in Spanish.
- CSV snapshot for Power BI plus optional PostgreSQL connection.

### v0.2

- All departments.
- Professional internship modality.
- Historical snapshots and trend comparisons.

### Non-goals for v0.1

- Applying to offers from the product.
- Automatic CV matching.
- User accounts.
- Mobile app.
- Real-time streaming.
- Publishing raw scraped data.

## 5. Data sources

Primary source: `https://www.practicas.pe/resultados-busqueda.php`.

Filters:

- `modalidad=PREPROFESIONAL`
- `dep=15` (Lima)
- `carrera=<id>` for every career returned by the site filter
- `sort=1-fecha_publicacion`
- `page=<n>`

The ingestion layer must:

- discover career IDs from the filter form,
- iterate careers and pages,
- deduplicate offers by URL,
- associate one offer with multiple careers when applicable,
- cache responses and rate-limit requests,
- record the fetch timestamp and source URL.

Legal and ethical constraints:

- Respect `robots.txt` and site terms.
- Use a clear User-Agent.
- Do not collect personal data.
- Do not republish raw HTML or full raw listings in the public repository.
- Use synthetic or curated fixtures for tests.
- Publish only aggregated data unless permission is granted.
- Attribute practicas.pe and state that the project is not affiliated.

## 6. Data contract

Each normalized offer must expose:

- `offer_id`
- `url`
- `title`
- `company`
- `company_normalized`
- `location`
- `district`
- `department`
- `modality`
- `attendance`
- `salary_text`
- `salary_amount`
- `salary_currency`
- `published_at`
- `deadline_at`
- `status`
- `careers` (list)
- `skills` (list)
- `requirements_text`
- `source_fetched_at`

## 7. Pipeline

```text
practicas.pe
    |
    v
[ingest] raw snapshots + cache
    |
    v
[normalize] canonical offer records
    |
    v
[quality] pass/fail rules + quality report
    |
    v
[load] PostgreSQL star schema
    |
    +--> [export] dashboard_dataset.csv
    +--> [export] practilizate.xlsx
    +--> [powerbi] practilizate.pbip
```

Modes:

- `--source fixtures` for deterministic tests and demos.
- `--source live` for real ingestion.
- `--as-of YYYY-MM-DD` to make date-based tests reproducible.

## 8. Data model

### Dimensions

- `dim_fecha(date_id, date, year, month, day, weekday, is_weekend)`
- `dim_empresa(company_id, name, normalized_name)`
- `dim_ubicacion(location_id, district, province, department)`
- `dim_carrera(career_id, name, normalized_name)`
- `dim_habilidad(skill_id, name, normalized_name)`
- `dim_modalidad(modality_id, name)`
- `dim_asistencia(attendance_id, name)`

### Facts

- `fact_ofertas(offer_id, title, company_id, location_id, date_id, modality_id, attendance_id, salary_amount, salary_text, published_at, deadline_at, status, url, quality_score)`

### Bridges

- `bridge_oferta_carrera(offer_id, career_id)`
- `bridge_oferta_habilidad(offer_id, skill_id)`

### Why bridges

One offer can require multiple careers and multiple skills. The bridge tables preserve those relationships without duplicating offers.

## 9. Data quality rules

Implement at least these rules and report pass/fail counts with examples:

1. Required fields: title, company, URL.
2. Unique offer URL.
3. Valid absolute URL.
4. Valid published date.
5. Valid deadline date.
6. Deadline is not earlier than published date.
7. Salary is numeric or explicitly null.
8. Salary outlier detection (configurable bounds).
9. Company name is not empty after normalization.
10. Location is present.
11. Modality is in the allowed set.
12. Attendance is in the allowed set.
13. At least one career is associated.
14. Duplicate title + company + deadline detection.
15. Skills are present when the offer publishes detailed requirements.
16. Source fetch timestamp exists.
17. Text is valid UTF-8 and normalized.

The quality report must include:

- rule id,
- description,
- checked count,
- failed count,
- pass rate,
- sample failed offer IDs,
- overall quality score.

## 10. CLI

```text
python -m practilizate ingest --source fixtures
python -m practilizate run --source fixtures --as-of 2026-10-29
python -m practilizate quality --run-id <id>
python -m practilizate load --run-id <id>
python -m practilizate export --format excel,csv
```

Requirements:

- Clear help text.
- Non-zero exit code on failure.
- Structured logs.
- No secrets in logs.
- `run` executes the full pipeline and writes artifacts.

## 11. Excel workbook

The workbook is user-facing and Spanish-first.

Sheets:

- `Portada`: title, source, date, quality score.
- `Datos`: normalized offers table.
- `Resumen`: KPIs and charts.
- `Habilidades`: top skills by career.
- `Empresas`: offers by company.
- `Calidad`: quality rule results.
- `Diccionario`: field definitions.

Use:

- Excel tables,
- formulas such as `SUMIFS`, `COUNTIFS`, `XLOOKUP` or `BUSCARX`,
- data validation,
- conditional formatting,
- charts,
- a dashboard-style `Resumen` sheet.

Pivot tables are optional if Excel COM automation is available. The workbook must open without repair warnings.

## 12. Power BI

Deliver:

- `powerbi/practilizate.pbip`
- theme file
- report pages
- screenshots in `docs/assets/`
- optional PostgreSQL connection documented in `powerbi/README.md`

Pages:

1. Executive summary.
2. Skills demand.
3. Companies and salaries.
4. Deadlines and opportunities.
5. Data quality.

Requirements:

- Spanish primary labels with ES/EN toggle.
- Accessible colors and alt text.
- No chartjunk.
- Clear filters and reset.
- Last updated timestamp.
- Source attribution.

Data source for v0.1: CSV snapshot at `data/processed/practilizate_dashboard.csv` for portability. PostgreSQL is optional for live refresh.

## 13. Bilingual behavior

- Dashboard: ES/EN toggle using a disconnected `dim_idioma` table and DAX `SWITCH` measures.
- Excel: Spanish labels.
- README: English + Spanish.
- CLI and logs: English.
- Code and database schema: English.

## 14. Nielsen heuristics

The product must comply with the 10 heuristics documented in `docs/heuristics.md`. The review evidence goes in `docs/heuristics-review.md`.

## 15. Testing strategy

- E2E only. No unit tests.
- Fixtures represent a medium-to-hard scenario:
  - multi-career offers,
  - duplicate URLs across career queries,
  - missing salary,
  - invalid date,
  - salary outlier,
  - missing company,
  - no deadline,
  - multiple skills.
- E2E runs the full CLI against a disposable PostgreSQL database.
- E2E asserts behavior and artifacts, not implementation details.
- E2E writes:
  - `artifacts/e2e/run_manifest.json`
  - `artifacts/e2e/quality_report.json`
  - `artifacts/e2e/practilizate.xlsx`
  - `artifacts/e2e/dashboard_dataset.csv`
  - checksums.

## 16. Acceptance criteria

- `python -m practilizate run --source fixtures` completes without errors.
- PostgreSQL contains the expected fact, dimension, and bridge rows.
- Quality report identifies the expected failures.
- Excel workbook exists, opens, and contains the required sheets.
- Dashboard dataset has the required columns and rows.
- Power BI `.pbip` opens and screenshots exist.
- E2E passes in CI.
- README and README.es contain real metrics and screenshots.
- Heuristics review is complete.
- No secrets or raw scraped data in the repository.

## 17. Metrics

- Offers processed.
- Companies.
- Careers.
- Skills.
- Quality score.
- Duplicate rate.
- Offers expiring within 7 days.
- Top 10 skills.
- Salary range by career.
- Pipeline runtime.

## 18. Risks

- Site structure changes: isolate selectors and add fixtures.
- Terms of use: keep repo private until reviewed; publish aggregated data only.
- Data quality: make failures visible, do not hide them.
- Scope creep: v0.1 is Lima + pre-professional; all departments is v0.2.
- Power BI portability: use CSV snapshot and document the PostgreSQL path.
- Bilingual complexity: keep labels in DAX measures and review both languages.
