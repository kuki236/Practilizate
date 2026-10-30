# Practilizate v0.1.2

Reproducible observatory of pre-professional internship offers in Lima, Peru.
This patch keeps the live `live-20261029` snapshot and fixes the Power BI table
headers so the report is fully understandable in Spanish.

## What changed in v0.1.2

- Power BI tables now use Spanish display names: `Oferta`, `Empresa`, `Vence`,
  `Días`, `Estado`, `Subvención`, `Regla`, `Descripción`, `Severidad`,
  `Revisadas`, `Fallidas`, `Tasa de aprobación`, and `Ejemplos`.
- The saved `.pbix` was regenerated from the fixed PBIP with live data.
- No data or metric changes. The E2E suite still passes.

## Live snapshot (2026-10-29)

- 65 careers discovered from the practicas.pe filter.
- 389 unique offers after deduplication (1,358 listing references merged).
- 83 companies, 24 canonical skills, 51 locations.
- Quality score: **97.7%**, with no critical rule failures.
- 330 offers expire within 7 days of the cutoff.
- Pipeline runtime: 530.6 s (~8.8 min) including PostgreSQL load and exports.
- Salary is published for 156 of 389 offers; averages exclude missing values
  and outliers above S/ 12,000.

Quality warnings: R06 (1 deadline before publication), R14 (38 duplicate
title + company + deadline groups), and R15 (113 offers with detailed
requirements but no lexicon skill).

## How to use it

**1. Review without installing anything**

Open the screenshots in `docs/assets/` and the PBIP in Power BI Desktop. The
PBIP is the report source; save it as `.pbix` for a portable single file. The
public release also contains aggregate live evidence and a synthetic E2E
fixture bundle.

**2. Run the pipeline locally**

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

For live data:

```powershell
python -m practilizate run --source live --as-of 2026-10-29
```

The live run discovers all careers, caches responses, respects the 1 s rate
limit, loads PostgreSQL, and writes the CSV and Excel deliverables.

**3. Use the deliverables**

- `data/processed/practilizate.xlsx` — Spanish workbook for students and career centers.
- `data/processed/dashboard_dataset.csv` — snapshot for Power BI and analysts.
- `powerbi/practilizate.pbip` — bilingual report source.
- PostgreSQL `v_dashboard_ofertas` — optional live-analysis view.

**4. Share it online**

The current product is a local CLI + Power BI Desktop + Excel workflow, not a
hosted web application. Publish the PBIP to a Power BI workspace (requires an
account/license) or build a web app on top of the CSV/PostgreSQL data. The
public repository publishes aggregate screenshots and evidence; the live CSV
and workbook stay local.

**5. Automate a refresh**

Schedule `python -m practilizate run --source live --as-of <date>` with Task
Scheduler or cron. The collector caches responses and respects the rate limit.

## Release assets

- `practilizate-v0.1.2-live-evidence.zip` — live manifest, quality report,
  ingest/load/export summaries, aggregate metadata, and rule-level results.
  It excludes raw offers, normalized offer JSON, Excel, and bridge CSVs.
- `practilizate-v0.1.2-e2e-fixtures.zip` — synthetic E2E artifacts with
  checksums; this is test data, not the live snapshot.
- Both assets include SHA-256 checksum files.

The live `.pbix` is not attached because it contains the live listing cache;
regenerate it from `powerbi/practilizate.pbip` after running the pipeline.

## Screenshots

- `docs/assets/dashboard-es.png`
- `docs/assets/dashboard-en.png`
- `docs/assets/excel-summary.png`
- `docs/assets/quality-report.png`

## Data source and scope

Data comes from public listings on [practicas.pe](https://www.practicas.pe/).
Practilizate is not affiliated with practicas.pe. v0.1 covers Lima and the
pre-professional modality. Only aggregated data is published; raw HTML and
personal data are not included. See `DATA_SOURCES.md` and `NOTICE.md`.

## Known notes

- The live snapshot is point-in-time; counts and expiring offers change.
- The skill lexicon covers 24 canonical skills; expanding it is a v0.2 task.
- Missing salary and duplicate content are visible in the quality report, not
  silently removed.
- The E2E suite uses synthetic fixtures for deterministic CI and never calls
  the public site.
