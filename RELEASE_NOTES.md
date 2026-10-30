# Practilizate v0.1.1

Reproducible observatory of pre-professional internship offers in Lima, Peru.
This release replaces the fixture-only demo with a **live snapshot** taken on
2026-10-29 while keeping the deterministic synthetic E2E artifact.

## Live snapshot (2026-10-29)

- 65 careers discovered from the practicas.pe filter.
- 389 unique offers after deduplication (1,358 listing references merged).
- 83 companies, 24 canonical skills, 51 locations.
- Quality score: **97.7%**, with no critical rule failures.
- 330 offers expire within 7 days of the cutoff.
- Pipeline runtime: 530.6 s (~8.8 min) including PostgreSQL load and exports.
- Salary is published for 156 of 389 offers; averages exclude missing values
  and outliers above S/ 12,000.

Quality warnings:

- **R06** — 1 offer with a deadline before its publication date.
- **R14** — 38 duplicate title + company + deadline groups.
- **R15** — 113 offers with detailed requirements but no skill from the current
  lexicon.

## Highlights

- Multi-career live ingestion from public practicas.pe listings with cache and
  a 1 s rate limit.
- Normalization of company, location, salary, dates, careers, and skills.
- 17 data quality rules with a visible report and critical-rule gating.
- PostgreSQL star schema with offer-career and offer-skill bridges.
- Spanish Excel workbook with tables, formulas, charts, validation, and
  conditional formatting; the live workbook contains 389 offers.
- Bilingual Power BI report with six pages, ES/EN toggle, alt text, accessible
  colors, top-10 charts for 65 careers / 24 skills / 83 companies, and a
  clear-filters action.
- E2E suite with a medium-to-hard synthetic fixture set and reproducible
  artifacts.

## Release assets

- `practilizate-v0.1.1-live-evidence.zip` — live `run_manifest.json`,
  `quality_report.json`, ingest/load/export summaries, and aggregate metadata.
  It does **not** include the raw offer CSV, normalized offer JSON, Excel
  workbook, or support bridge CSVs.
- `practilizate-v0.1.1-e2e-fixtures.zip` — synthetic E2E artifacts
  (`run_manifest.json`, `quality_report.json`, `practilizate.xlsx`,
  `dashboard_dataset.csv`, support CSVs, and checksums). This is test data,
  not the live snapshot.
- Both assets include SHA-256 checksum files.

The live CSV and Excel workbook remain local in `data/processed/` and are not
published in the public repository. The public screenshots show aggregate
counts only.

## Screenshots

- `docs/assets/dashboard-es.png`
- `docs/assets/dashboard-en.png`
- `docs/assets/excel-summary.png`
- `docs/assets/quality-report.png`

## Setup

```powershell
git clone <repository-url>
cd practilizate
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
docker compose up -d db
Copy-Item .env.example .env
python -m practilizate run --source fixtures --as-of 2026-10-29
pytest tests/e2e
```

For the live snapshot:

```powershell
python -m practilizate run --source live --as-of 2026-10-29
```

Open `powerbi/practilizate.pbip` after the pipeline writes `data/processed/`.
The semantic model reads the snapshot through the `DataFolder` parameter.

## Data source and scope

Data comes from public listings on [practicas.pe](https://www.practicas.pe/).
Practilizate is not affiliated with practicas.pe. v0.1 covers Lima and the
pre-professional modality. Only aggregated data is published; raw HTML and
personal data are not included. See `DATA_SOURCES.md` and `NOTICE.md`.

## Known notes

- The live snapshot is point-in-time; counts and expiring offers change.
- The skill lexicon covers 24 canonical skills. Expanding it is a v0.2 task.
- Missing salary and duplicate content are visible in the quality report, not
  silently removed.
- The E2E suite uses synthetic fixtures for deterministic CI and never calls
  the public site.
