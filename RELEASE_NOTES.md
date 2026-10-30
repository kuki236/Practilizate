# Practilizate v0.1.0

Reproducible observatory of pre-professional internship offers in Lima, Peru.

## Highlights

- Multi-career ingestion from public practicas.pe listings with cache and rate limiting.
- Normalization of company, location, salary, dates, careers, and skills.
- 17 data quality rules with a visible report and critical-rule gating.
- PostgreSQL star schema with offer-career and offer-skill bridges.
- Spanish Excel workbook with tables, formulas, charts, validation, and conditional formatting.
- Bilingual Power BI report with six pages, ES/EN toggle, alt text, accessible colors, and a clear-filters action.
- E2E suite with a medium-to-hard fixture set and reproducible artifacts.

## Verified metrics (fixture snapshot, `--as-of 2026-10-29`)

| Metric | Value |
|---|---|
| Offers processed | 12 |
| Companies | 10 |
| Careers | 3 |
| Skills | 21 |
| Quality score | 94.3% |
| Offers expiring within 7 days | 1 |
| Pipeline runtime | ~1.5 s including PostgreSQL |

Quality report: 10 warning rules, no critical failures.

## Artifacts

The release asset is the E2E bundle `practilizate-v0.1.0-e2e.zip`, built from
`artifacts/e2e/` and containing:

- `run_manifest.json`
- `quality_report.json`
- `normalized_offers.json`
- `database_load.json`
- `export_report.json`
- `practilizate.xlsx`
- `dashboard_dataset.csv`
- Power BI support CSVs (`offer_careers.csv`, `offer_skills.csv`, `quality_rules.csv`, `run_metadata.csv`, `dim_idioma.csv`, `dim_estado.csv`)
- `checksums.sha256`

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

Open `powerbi/practilizate.pbip` after the pipeline writes `data/processed/`.

## Data source and scope

Data comes from public listings on [practicas.pe](https://www.practicas.pe/).
Practilizate is not affiliated with practicas.pe. v0.1 covers Lima and the
pre-professional modality. Only aggregated data is published; raw HTML and
personal data are not included. See `DATA_SOURCES.md` and `NOTICE.md`.

## Known notes

- Fixture counts are deterministic and smaller than a live snapshot.
- The Power BI model reads the snapshot through the `DataFolder` parameter; update it if the repository moves.
- The live source depends on the public site structure; the fixtures protect the test suite.
