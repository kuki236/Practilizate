# Practilizate — Roadmap

Work through the checkpoints in order. After each checkpoint, run E2E, update the checkbox, format, and commit.

## CP0 — Repository and documentation

- [ ] Create the project structure.
- [ ] Add `AGENTS.md`, `SPECS.md`, `ROADMAP.md`, `README.md`, `README.es.md`, `CODESTYLE.md`.
- [ ] Add `DATA_SOURCES.md`, `NOTICE.md`, `LICENSE`.
- [ ] Add `docs/heuristics.md`, `docs/heuristics-review.md`, `docs/data-dictionary.md`.
- [ ] Add `.gitignore`, `.env.example`, and `.opencode/command/goal.md`.
- [ ] Initialize git and make the first commit.

**Acceptance:** documentation is complete, git is clean, and the repository has no secrets or raw data.

**Suggested commit:** `docs: initialize practilizate project`

## CP1 — Scaffold and local infrastructure

- [x] Create `pyproject.toml` with Python 3.13, dependencies, ruff, and pytest.
- [x] Create `src/practilizate/` package and CLI entry point.
- [x] Create `docker-compose.yml` for PostgreSQL.
- [x] Create `.github/workflows/ci.yml`.
- [x] Add a minimal `python -m practilizate --help`.

**Acceptance:** `python -m practilizate --help` works; `docker compose up -d db` starts PostgreSQL; CI runs.

**Suggested commit:** `chore: scaffold python project and postgres`

## CP2 — Failure modes and fixtures

- [x] Write `docs/failure-modes.md` before implementing parsing or quality logic.
- [x] Add multi-career fixtures with the medium-hard cases from `SPECS.md`.
- [x] Add a fixture loader and deterministic `--as-of` date.
- [x] Document expected fixture outcomes.

**Acceptance:** fixtures cover duplicates, multi-career, missing salary, invalid dates, outliers, missing company, no deadline, and multiple skills.

**Suggested commit:** `test: add medium-hard e2e fixtures`

## CP3 — Ingestion and normalization

- [x] Implement live ingestion with cache, rate limit, and career pagination.
- [x] Implement fixture ingestion.
- [x] Normalize company, location, modality, attendance, salary, dates, careers, and skills.
- [x] Deduplicate offers by URL and preserve multi-career links.

**Acceptance:** fixture run produces the expected normalized records and career associations.

**Suggested commit:** `feat: add multi-career ingestion and normalization`

## CP4 — Data quality

- [x] Implement the quality rules from `SPECS.md`.
- [x] Generate `quality_report.json` with counts, samples, and overall score.
- [x] Fail the run when critical rules fail.
- [x] Add E2E assertions for expected quality failures.

**Acceptance:** quality report identifies the expected fixture failures and passes the rest.

**Suggested commit:** `feat: add data quality rules and report`

## CP5 — PostgreSQL star schema

- [x] Create schema and migrations.
- [x] Load dimensions, facts, and bridge tables.
- [x] Add indexes and a dashboard view.
- [x] Add E2E database assertions.

**Acceptance:** expected rows exist in `fact_ofertas`, dimensions, and bridge tables; duplicate URLs are not duplicated.

**Suggested commit:** `feat: load star schema into postgres`

## CP6 — Excel and dashboard dataset

- [x] Generate `practilizate.xlsx` with the required Spanish sheets.
- [x] Add formulas, tables, conditional formatting, and charts.
- [x] Export `dashboard_dataset.csv`.
- [x] Add E2E artifact checks.

**Acceptance:** workbook opens without repair warnings and contains the required sheets; CSV has the expected schema.

**Suggested commit:** `feat: export excel workbook and dashboard dataset`

## CP7 — Power BI report

- [x] Create `powerbi/practilizate.pbip` using the CSV snapshot.
- [x] Add executive summary, skills, companies/salaries, deadlines, and quality pages.
- [x] Add ES/EN toggle with `dim_idioma` and DAX `SWITCH`.
- [x] Add accessible colors, alt text, and source footer.
- [x] Capture screenshots in `docs/assets/`.

**Acceptance:** `.pbip` opens, both languages work, screenshots exist, and the report uses the exported dataset.

**Suggested commit:** `feat: add bilingual power bi report`

## CP8 — Heuristics, README, and final E2E

- [x] Complete `docs/heuristics-review.md` with screenshots and pass/fail evidence.
- [x] Update `README.md` and `README.es.md` with real metrics, screenshots, and setup.
- [x] Run the full E2E and write artifacts with checksums.
- [x] Run `ruff format` and `ruff check`.
- [x] Tag `v0.1.0`.

**Acceptance:** E2E passes, CI is green, README is accurate, and heuristics evidence is complete.

**Suggested commit:** `docs: finalize readme and heuristics review`

## CP9 — GitHub release

- [x] Review repository for secrets and raw data.
- [ ] Push the private repository. (user action)
- [ ] Create a release with the E2E artifact. (user action)
- [ ] Decide whether the repository can become public. (user action)

**Acceptance:** private repo is up to date and the release contains the verified artifact.

**Suggested commit:** `chore: prepare v0.1.0 release`
