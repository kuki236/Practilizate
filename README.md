# Practilizate

**Observatorio de prácticas preprofesionales del Perú.**

Practilizate turns public internship listings into a reproducible data product: a validated PostgreSQL star schema, a Power BI dashboard, an Excel workbook, and a data quality report.

> **Status:** v0.1 complete. The fixture pipeline, PostgreSQL star schema, Excel workbook, bilingual Power BI report, and E2E artifacts are in the repository.
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

![Dashboard in Spanish](docs/assets/dashboard-es.png)

![Dashboard in English](docs/assets/dashboard-en.png)

![Excel executive summary](docs/assets/excel-summary.png)

![Data quality report](docs/assets/quality-report.png)

- Dashboard (Spanish): `docs/assets/dashboard-es.png`
- Dashboard (English): `docs/assets/dashboard-en.png`
- Excel summary: `docs/assets/excel-summary.png`
- Data quality report: `docs/assets/quality-report.png`
- Power BI guide: [powerbi/README.md](powerbi/README.md)

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
python -m practilizate run --source fixtures --as-of 2026-10-29
pytest tests/e2e
```

The default `fixtures` mode is deterministic and does not call the live site.
Docker Compose maps PostgreSQL to host port **5433**; `.env.example` already
uses that port. `python -m practilizate ingest --source live` uses the public
site with a cache and a configurable rate limit.

## Power BI

Open `powerbi/practilizate.pbip` in Power BI Desktop and save it as `.pbix` if needed.

- v0.1 uses `data/processed/dashboard_dataset.csv` plus the support CSVs for portability.
- The model reads the snapshot through the `DataFolder` parameter; update it if the repository moves.
- The six pages cover executive summary, skills, companies and compensation, deadlines, quality, and a bilingual help page.
- The report includes an ES/EN toggle (`Idioma` table and DAX `SWITCH` measures), alt text, accessible colors, a source footer, and a `Limpiar filtros` button.
- PostgreSQL is documented as an optional live source in [powerbi/README.md](powerbi/README.md).

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
├─ normalized_offers.json
├─ database_load.json
├─ export_report.json
├─ practilizate.xlsx
├─ dashboard_dataset.csv
├─ offer_careers.csv
├─ offer_skills.csv
├─ quality_rules.csv
├─ run_metadata.csv
├─ dim_idioma.csv
├─ dim_estado.csv
└─ checksums.sha256
```

`artifacts/e2e/` is generated and gitignored; CI uploads it as an artifact and
the release attaches it.

## Results

> Fixture snapshot (`--as-of 2026-10-29`). Live mode produces different counts.

| Metric | Value |
|---|---|
| Offers processed | 12 |
| Companies | 10 |
| Careers | 3 |
| Skills | 21 |
| Quality score | 94.3% |
| Offers expiring within 7 days | 1 |
| Pipeline runtime | ~1.5 s (fixture, PostgreSQL included) |

The quality report flags 10 warning rules and no critical rule. See
[docs/fixtures.md](docs/fixtures.md) for the expected fixture outcomes and
[docs/data-dictionary.md](docs/data-dictionary.md) for field definitions.

## Nielsen heuristics

The product follows the 10 usability heuristics in [docs/heuristics.md](docs/heuristics.md). Review evidence is complete in [docs/heuristics-review.md](docs/heuristics-review.md), using the screenshots above, the Excel workbook, the quality report, and the E2E manifest.

## Data dictionary

Field definitions for the star schema, CSV snapshot, quality report, and manifest are in [docs/data-dictionary.md](docs/data-dictionary.md).

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
├─ scripts/
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
