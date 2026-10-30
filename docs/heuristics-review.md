# Heuristics Review — Practilizate

Use this checklist before the `v0.1.0` release. Add screenshots to `docs/assets/` and mark each item.

## Review setup

- Open the Power BI report in Spanish and English.
- Open the Excel workbook.
- Run the CLI with an invalid argument and with an empty fixture.
- Review the README in both languages.
- Test at 1366×768 and at 1920×1080.

## Checklist

| # | Heuristic | Evidence | Result |
|---|---|---|---|
| 1 | Visibility of system status | `docs/assets/heuristics-status.png`; `artifacts/e2e/run_manifest.json` | Pending |
| 2 | Match with real world | `docs/assets/heuristics-language-es.png`; `docs/assets/heuristics-language-en.png` | Pending |
| 3 | User control and freedom | `docs/assets/heuristics-reset.png`; empty-state screenshot | Pending |
| 4 | Consistency and standards | `docs/assets/heuristics-consistency.png`; glossary check | Pending |
| 5 | Error prevention | Quality report; invalid CLI argument screenshot | Pending |
| 6 | Recognition rather than recall | `docs/assets/heuristics-tooltips.png`; `Cómo leer` page | Pending |
| 7 | Flexibility and efficiency | Filter/search/export screenshots | Pending |
| 8 | Aesthetic and minimalist design | Full dashboard screenshot | Pending |
| 9 | Error recovery | Empty state and quality failure screenshots | Pending |
| 10 | Help and documentation | README, data dictionary, `--help` output | Pending |

## Manual checks

### Spanish and English

- [ ] All titles, labels, tooltips, and empty states are translated.
- [ ] Dates and currency keep the same format in both languages.
- [ ] The toggle does not leave blank labels or mixed-language pages.
- [ ] The source footer is visible in both languages.

### Data quality

- [ ] Failed rules are visible in the dashboard and Excel.
- [ ] Sample failed offer IDs are available.
- [ ] The quality score is explained.
- [ ] The user can distinguish a data limitation from a pipeline bug.

### Accessibility

- [ ] Color contrast is sufficient.
- [ ] Every chart has alt text or a text summary.
- [ ] Keyboard navigation works in Power BI.
- [ ] The report is readable without relying only on color.

### Help

- [ ] README quickstart works on Windows.
- [ ] `python -m practilizate --help` is clear.
- [ ] The data dictionary covers every dashboard field.
- [ ] The `Cómo leer` page explains the main metrics.

## Sign-off

- Reviewer: Sebastian Andree Tejeda Alata
- Date: `[YYYY-MM-DD]`
- Result: `[Pass / Pass with notes / Fail]`
- Notes:
