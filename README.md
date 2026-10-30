# Practilizate

**Observatorio de prácticas preprofesionales del Perú.**

Practilizate turns public internship listings into a reproducible data product: a validated PostgreSQL star schema, a Power BI dashboard, an Excel workbook, and a data quality report.

> **Status:** documentation and roadmap are ready. The implementation is tracked in [ROADMAP.md](ROADMAP.md).
> **Español:** [README.es.md](README.es.md)

## Why Practilizate

Students apply to internships without comparable data about salaries, companies, required skills, or deadlines. Career centers also lack a current, structured view of the market.

Practilizate answers:

- Which skills are most requested by career and district?
- Which companies publish the most internship offers?
- What salary ranges appear by role and career?
- Which offers are about to expire?
- How complete and reliable is the published data?

The initial 73-offer analysis was limited to Systems Engineering in Lima. The product is designed for **all careers**.

## What it includes

- Multi-career ingestion from practicas.pe.
- Normalization of company, location, salary, dates, careers, and skills.
- Data quality rules with a visible report.
- PostgreSQL star schema with career and skill bridges.
- Power BI report with Spanish/English toggle.
- Excel workbook in Spanish.
- Repeatable E2E test and artifact manifest.
- Bilingual documentation.

## Architecture

```text
practicas.pe
    |
    v
[ingest] cache + rate limit
    |
    v
[normalize] canonical offers
    |
    v
[quality] rules + report
    |
    v
[load] PostgreSQL star schema
    |
    +--> [export] dashboard_dataset.csv
    +--> [export] practilizate.xlsx
    +--> [powerbi] practilizate.pbip
```

## Demo

> Screenshots will be added after the Power BI and Excel checkpoints.

- Dashboard (Spanish): `docs/assets/dashboard-es.png`
- Dashboard (English): `docs/assets/dashboard-en.png`
- Excel summary: `docs/assets/excel-summary.png`
- Data quality report: `docs/assets/quality-report.png`

## Data source and attribution

Data comes from public listings on [practicas.pe](https://www.practicas.pe/).

- Practilizate is **not affiliated** with practicas.pe.
- The project uses public data for educational and research purposes.
- Only aggregated data is published. Raw scraped HTML and personal data are not included.
- The collector respects `robots.txt`, rate limits, and caching.
- See [DATA_SOURCES.md](DATA_SOURCES.md) and [NOTICE.md](NOTICE.md).

## Quickstart

```powershell
git clone <repository-url>
cd practilizate
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
docker compose up -d db
Copy-Item .env.example .env
python -m practilizate run --source fixtures
pytest tests/e2e
```

The default `fixtures` mode is deterministic and does not call the live site.

## Power BI

Open `powerbi/practilizate.pbip` in Power BI Desktop and save it as `.pbix` if needed.

- v0.1 uses `data/processed/practilizate_dashboard.csv` for portability.
- PostgreSQL is documented as an optional live source.
- The report includes an ES/EN language toggle and accessible colors.

## Excel

The workbook is generated at `data/processed/practilizate.xlsx` and includes:

- `Portada`
- `Datos`
- `Resumen`
- `Habilidades`
- `Empresas`
- `Calidad`
- `Diccionario`

## Testing

- E2E only. No unit tests.
- The E2E suite runs the full pipeline against a disposable PostgreSQL database.
- It uses a medium-to-hard fixture set: multi-career offers, duplicates, missing salary, invalid dates, outliers, and missing fields.
- Each run writes a repeatable artifact to `artifacts/e2e/`:

```text
artifacts/e2e/
├─ run_manifest.json
├─ quality_report.json
├─ practilizate.xlsx
├─ dashboard_dataset.csv
└─ checksums.sha256
```

## Results

> Metrics will be filled after the live snapshot and E2E run.

| Metric | Value |
|---|---|
| Offers processed | `[N]` |
| Companies | `[M]` |
| Careers | `[C]` |
| Skills | `[S]` |
| Quality score | `[Q]%` |
| Offers expiring within 7 days | `[D]` |
| Pipeline runtime | `[T]` |

## Nielsen heuristics

The product follows the 10 usability heuristics in [docs/heuristics.md](docs/heuristics.md). Review evidence is tracked in [docs/heuristics-review.md](docs/heuristics-review.md).

## Project structure

```text
practilizate/
├─ AGENTS.md
├─ SPECS.md
├─ ROADMAP.md
├─ README.md
├─ README.es.md
├─ CODESTYLE.md
├─ DATA_SOURCES.md
├─ NOTICE.md
├─ LICENSE
├─ docs/
├─ src/practilizate/
├─ sql/
├─ tests/e2e/
├─ data/fixtures/
├─ data/processed/
├─ artifacts/e2e/
├─ powerbi/
├─ excel/
├─ docker-compose.yml
├─ pyproject.toml
├─ .env.example
└─ .github/workflows/ci.yml
```

## Limitations

- v0.1 covers Lima and pre-professional internships.
- Public listings may omit salary, deadlines, or detailed requirements.
- The site structure can change; fixtures protect the test suite.
- The project is an observatory, not an application tracker.
- Data quality is reported, not hidden.

## License

Code: MIT. See [LICENSE](LICENSE).

Data and derived datasets are not covered by the MIT license. See [DATA_SOURCES.md](DATA_SOURCES.md).
