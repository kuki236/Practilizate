# Nielsen's 10 Usability Heuristics — Practilizate

This document maps the 10 heuristics to concrete product decisions. It is a practical checklist, not a theoretical essay.

## 1. Visibility of system status

**Principle:** The system keeps users informed about what is happening.

**Practilizate implementation:**

- Dashboard shows `Última actualización` and the source.
- Loading states for data refresh and filters.
- Active filters are visible as chips.
- E2E run writes `run_manifest.json` with counts, timestamp, and checksums.
- Excel `Portada` shows source, date, and quality score.

**Acceptance:**

- A user can tell when the data was last updated and which filters are active.
- A pipeline run always leaves a manifest.

## 2. Match between system and the real world

**Principle:** Use the user's language and familiar concepts.

**Practilizate implementation:**

- Spanish primary labels: `Subvención`, `Carrera`, `Ciclo`, `Modalidad`, `Vence`.
- Familiar Peruvian terms: `prácticas preprofesionales`, `convocatoria`, `subvención`.
- English toggle for international reviewers.
- No internal codes in user-facing labels.

**Acceptance:**

- A Peruvian student understands the dashboard without reading technical docs.
- Both ES and EN labels are reviewed.

## 3. User control and freedom

**Principle:** Users need a clear exit, undo, or reset.

**Practilizate implementation:**

- `Limpiar filtros` button.
- Clear navigation between report pages.
- No destructive action without confirmation.
- Filters do not trap the user in an empty state.

**Acceptance:**

- Reset returns the dashboard to its initial state.
- Empty states explain how to recover.

## 4. Consistency and standards

**Principle:** The same words and actions should mean the same thing.

**Practilizate implementation:**

- Shared glossary across dashboard, Excel, README, and data dictionary.
- Same colors and labels for careers, skills, and quality status.
- Consistent date format: `dd/mm/yyyy`.
- Consistent currency format: `S/ 1,230.00`.
- Power BI, Excel, and README use the same metric names.

**Acceptance:**

- A term has one meaning across the product.
- ES/EN toggle does not change the meaning of a metric.

## 5. Error prevention

**Principle:** Prevent errors before they happen.

**Practilizate implementation:**

- Data quality rules validate dates, salaries, URLs, and required fields.
- Dashboard filters show only valid values.
- Excel uses data validation and protected calculation sheets.
- CLI validates source and date arguments before running.

**Acceptance:**

- Invalid dates and negative salaries are flagged, not silently displayed.
- Users cannot select nonexistent careers or departments.

## 6. Recognition rather than recall

**Principle:** Make options visible; do not force users to remember.

**Practilizate implementation:**

- Visible filter lists and search.
- Legends and tooltips on charts.
- `Cómo leer` help page.
- Data dictionary in Excel and docs.
- Suggested empty-state actions.

**Acceptance:**

- A user can interpret a chart without memorizing the data model.
- Help is reachable from the dashboard.

## 7. Flexibility and efficiency of use

**Principle:** Support both novice and expert users.

**Practilizate implementation:**

- Quick filters by career, company, district, and deadline.
- Search and bookmarks in Power BI.
- CSV/Excel export for advanced users.
- CLI flags for automated runs.
- Optional PostgreSQL connection for live refresh.

**Acceptance:**

- A student can filter in a few clicks.
- An analyst can export or query the data directly.

## 8. Aesthetic and minimalist design

**Principle:** Remove irrelevant information.

**Practilizate implementation:**

- One main question per report page.
- Limited KPI cards and charts.
- No 3D charts, decorative gradients, or chartjunk.
- Consistent whitespace and typography.

**Acceptance:**

- Every visual has a clear purpose.
- The dashboard remains readable at 1366×768.

## 9. Help users recognize, diagnose, and recover from errors

**Principle:** Error messages should be clear, specific, and actionable.

**Practilizate implementation:**

- Quality report lists rule, failed count, and sample offer IDs.
- Empty states explain why there is no data and how to reset.
- CLI errors include the failing stage and a suggested fix.
- Excel `Calidad` sheet highlights failed rules.

**Acceptance:**

- A failed rule is understandable without reading source code.
- The user can recover without restarting the whole process.

## 10. Help and documentation

**Principle:** Provide task-focused help even if the system is easy to use.

**Practilizate implementation:**

- `README.md` and `README.es.md`.
- `docs/data-dictionary.md`.
- `Cómo leer` page in Power BI.
- Tooltips in the dashboard.
- `--help` for every CLI command.

**Acceptance:**

- A new user can run the project from the README.
- A reviewer can understand the data model from the dictionary.

## Review evidence

Manual review and screenshots are tracked in `docs/heuristics-review.md`.
