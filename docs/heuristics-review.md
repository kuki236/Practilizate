# Heuristics Review — Practilizate v0.1.0

Review performed on the fixture snapshot with `--as-of 2026-10-29`, the Power BI
report in Power BI Desktop `2.159.883.0`, the generated Excel workbook, and the
full E2E artifact set.

## Evidence

| Evidence | Path |
|---|---|
| Dashboard, Spanish | `docs/assets/dashboard-es.png` |
| Dashboard, English | `docs/assets/dashboard-en.png` |
| Excel summary | `docs/assets/excel-summary.png` |
| Excel quality sheet | `docs/assets/quality-report.png` |
| E2E manifest and checksums | `artifacts/e2e/run_manifest.json`, `artifacts/e2e/checksums.sha256` |
| Quality report | `artifacts/e2e/quality_report.json` |
| Report guide | `powerbi/README.md` |
| Data dictionary | `docs/data-dictionary.md` |
| Fixture expectations | `docs/fixtures.md` |

The E2E suite runs the full CLI against a disposable PostgreSQL database, then
verifies the CSV schema, workbook structure, database counts, quality failures,
Power BI support CSVs, and artifact checksums.

## Checklist

| # | Heuristic | Evidence | Result |
|---|---|---|---|
| 1 | Visibility of system status | Dashboard message (`Hay 12 ofertas…`), `Actualizado al 29/10/2026`, source footer, `run_manifest.json` status/counts/checksums. | Pass |
| 2 | Match between system and real world | Spanish-first labels (`Ofertas`, `Subvención`, `Por vencer`), Peruvian terms, ES/EN toggle, dates `dd/mm/yyyy`, currency `S/`. | Pass with note |
| 3 | User control and freedom | `Limpiar filtros` action button (`ClearAllSlicers`), native slicer clear, page tabs, no destructive actions. | Pass |
| 4 | Consistency and standards | Same palette and metric names in Power BI and Excel; same date and currency formats; shared glossary. | Pass |
| 5 | Error prevention | 17 quality rules, critical-rule gating, `--strict` mode, salary bounds, `--as-of` determinism, argument validation. | Pass |
| 6 | Recognition rather than recall | Descriptions and legends on charts, KPI titles, `Cómo leer` page, data dictionary, native tooltips. | Pass |
| 7 | Flexibility and efficiency of use | Career/language slicers, CSV and Excel exports, `--source live`, optional PostgreSQL view. | Pass |
| 8 | Aesthetic and minimalist design | One question per page, 1280×720 canvas, six focused pages, no 3D charts, no decorative gradients. | Pass |
| 9 | Help users recover from errors | Quality report lists rule, failed count, and sample offer IDs; CLI reports failing stage; help page explains limitations. | Pass with note |
| 10 | Help and documentation | `README.md`, `README.es.md`, `docs/data-dictionary.md`, `powerbi/README.md`, `Cómo leer`, `--help`. | Pass |

## Manual checks

### Spanish and English

- [x] Dynamic message, footer, and KPI titles are present in both languages.
- [x] Dates and currency keep the same format in both languages.
- [x] The toggle does not leave blank labels or broken visuals.
- [x] The source footer is visible in both languages.
- [x] Note: published category labels (career names, status values, skills) stay
      in Spanish; the toggle changes the narrative, footer, and bilingual titles.

### Data quality

- [x] Failed rules are visible in the dashboard and the Excel `Calidad` sheet.
- [x] Sample failed offer IDs are available (`90006`, `90004`, `90003`, `90008`, `90005`, `90009`, `90010`, `90001/90007`, `90011`).
- [x] The quality score is explained as the average rule pass rate; the per-offer
      score is shown in `Datos`.
- [x] The user can distinguish a source limitation from a pipeline bug: the
      fixture contract in `docs/fixtures.md` names the expected failures.

### Accessibility

- [x] Contrast is sufficient for the navy/white header, white cards, and dark text.
- [x] Every chart, table, card, slicer, and button has alt text.
- [x] The report uses descriptive titles, labels, and legends; color is not the only signal.
- [x] Keyboard navigation uses native Power BI controls and a tab order; the page
      is 1280×720 and fits a 1366×768 viewport.
- [x] Note: custom empty-state copy is not authored; native visual empty states
      are used, while `Cómo leer` and `Calidad` explain recovery.

### Help

- [x] The README quickstart works on Windows with Docker Compose on port 5433.
- [x] `python -m practilizate --help` lists all five commands and their purpose.
- [x] The data dictionary covers every field in the database, CSV, report, and manifest.
- [x] The `Cómo leer` page explains the main metrics and reset action.

## Sign-off

- Reviewer: Sebastian Andree Tejeda Alata
- Date: 2026-10-29
- Result: Pass with notes
- Notes: The v0.1 fixture snapshot is validated and published end to end. Live
  mode is implemented but its counts depend on the public site; the report
  screenshots use the deterministic fixture snapshot. The Windows Desktop bridge
  screenshot CLI was unavailable in this environment, so screenshots were
  captured from the validated report window in Power BI Desktop.
