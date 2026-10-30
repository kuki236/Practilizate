# Agent Instructions — Practilizate

## Read before changing anything

Read these files first:

- `SPECS.md`
- `ROADMAP.md`
- `CODESTYLE.md`
- `README.md`
- `docs/heuristics.md`

## Testing rules — mandatory

- NEVER write unit tests after you write code.
- Highly prefer E2E tests as the sole testing mechanism. Use them to verify complex features work. At the end of E2E tests, produce a verifiable and repeatable artifact.
- If you must test a system in isolation, FIRST write all the ways it could fail, THEN write the code.
- Tautological tests considered harmful.
- Change-detector tests considered harmful.
- Do not create regression tests for bug fixes without a genuine gap in behavior testing.
- When writing an E2E test, do not pick the simplest possible scenario to prove it works. Pick a medium-to-hard scenario that exercises the real behavior.
- Every E2E run must leave a repeatable artifact under `artifacts/e2e/` with counts, checksums, and a manifest.
- Do not modify fixtures to make tests pass. Fix the code or document a real source-data limitation.

## Workflow

1. Work through `ROADMAP.md` checkpoint by checkpoint.
2. Do not skip checkpoints.
3. After each checkpoint:
   - run the E2E suite,
   - update the checkbox in `ROADMAP.md`,
   - update README metrics/screenshots if the checkpoint changes them,
   - run formatting and lint,
   - commit with a conventional commit.
4. Use `git status` and `git diff` before committing.
5. Never commit secrets, `.env`, raw scraped HTML, or generated databases.
6. Stop only when all roadmap checkpoints are complete.

## Commit convention

Use conventional commits:

```text
feat: add multi-career ingestion
fix: handle missing salary values
docs: add Nielsen heuristics review
test: add medium-hard E2E fixture
chore: configure ruff and pytest
refactor: split normalization pipeline
```

## Language and code style

- Code, identifiers, docstrings, comments, commit messages, and internal docs: English.
- User-facing dashboard and Excel workbook: Spanish primary.
- The dashboard must include an ES/EN language toggle.
- `README.md`: English. `README.es.md`: Spanish.
- Comments only for non-obvious technical decisions. Do not narrate obvious code.
- No `print()`. Use structured logging.
- Use type hints and Pydantic settings.
- Format with `ruff format` and lint with `ruff check`.
- Do not abuse comments or tokens.

## Data and legal rules

- Source: `practicas.pe`.
- Respect `robots.txt`, terms of use, rate limits, and caching.
- Do not collect or publish personal data.
- Do not commit raw scraped HTML to the public repository.
- Use synthetic or curated fixtures for tests.
- Keep aggregated data outside the repository unless the license is clear.
- Add attribution in `DATA_SOURCES.md`, `NOTICE.md`, the dashboard footer, and the README.
- Practilizate is not affiliated with practicas.pe.

## Power BI rules

- Use the `powerbi-report-cli` skill for report lifecycle work.
- Use the `powerbi-modeling` MCP for semantic model and DAX work.
- Deliver a `.pbip` project plus screenshots. The user will save it as `.pbix`.
- Use a CSV snapshot for portability; document the optional PostgreSQL connection.
- Follow the accessibility and Nielsen checks in `docs/heuristics.md`.

## Definition of done

- All `ROADMAP.md` checkpoints are checked.
- E2E suite passes and produces `artifacts/e2e/run_manifest.json`.
- `README.md` and `README.es.md` include real screenshots and metrics.
- CI is green.
- `docs/heuristics-review.md` is completed with evidence.
- No unit tests, no tautological tests, no change-detector tests.
- No secrets, raw data dumps, or personal data in the repository.
