# Practilizate — Code Style

## Language

- Code, identifiers, docstrings, comments, commit messages, and internal docs: English.
- User-facing dashboard and Excel workbook: Spanish primary.
- Dashboard: Spanish/English toggle.
- `README.md`: English.
- `README.es.md`: Spanish.

## Python

- Python 3.13.
- `src/` layout.
- Type hints on public functions.
- Pydantic settings for configuration.
- Structured logging with the standard `logging` module. No `print()`.
- Prefer small, composable functions over large scripts.
- Avoid comments that restate the code. Comment only non-obvious decisions.
- Do not swallow exceptions. Add context and fail loudly when the pipeline cannot continue.
- Keep secrets in `.env`; never commit them.

## Formatting and linting

- `ruff format`
- `ruff check`
- No unused imports or variables.
- Maximum line length: 100.
- Use double quotes.
- Use `pathlib.Path` for filesystem paths.

## Naming

- Python modules: `snake_case`.
- Classes: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE`.
- Database tables and columns: `snake_case`.
- Power BI measures: English names, Spanish display labels via DAX.
- Excel sheets: Spanish user-facing names.

## SQL

- Lowercase SQL keywords.
- One clause per line for non-trivial queries.
- Use explicit column lists.
- Use CTEs for readability.
- Add indexes for join and filter columns.
- Never use `SELECT *` in production code.

## Testing

- E2E only. No unit tests.
- If a component must be tested in isolation, write `docs/failure-modes.md` first.
- No tautological tests.
- No change-detector tests.
- Do not add regression tests without a genuine behavior gap.
- E2E scenarios must be medium-to-hard.
- Every E2E run must produce a repeatable artifact under `artifacts/e2e/`.

## Git

- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`.
- Commit at every significant checkpoint.
- Do not commit generated databases, raw HTML, `.env`, or secrets.
- Keep commits focused.

## Data

- Normalize text to UTF-8.
- Keep raw snapshots outside the repository.
- Use synthetic or curated fixtures for tests.
- Make quality failures visible.
- Document data limitations in the README.

## UI and accessibility

- Spanish primary labels; English toggle.
- Sufficient color contrast.
- Alt text for visuals.
- Clear empty states and error messages.
- Reset filters and clear navigation.
- Follow `docs/heuristics.md`.
- No chartjunk or decorative visuals without information value.

## Power BI

- Use the `powerbi-report-cli` skill for report lifecycle work.
- Use `powerbi-modeling` MCP for semantic model and DAX work.
- Keep report pages focused: one main question per page.
- Use a consistent theme and naming convention.
- Provide screenshots and a short `powerbi/README.md`.
