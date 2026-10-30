# Practilizate — Power BI

Bilingual Power BI report for the Practilizate snapshot.

## Files

```text
powerbi/
├─ practilizate.pbip
├─ practilizate.Report/
│  ├─ definition/                 # PBIR pages and visuals
│  ├─ StaticResources/            # base theme and registered custom theme
│  └─ definition.pbir             # byPath binding to ../practilizate.SemanticModel
└─ practilizate.SemanticModel/
   ├─ definition/                 # TMDL model
   └─ definition.pbism
```

## Open the report

1. Run the pipeline once from the repository root:

   ```powershell
   python -m practilizate run --source fixtures --as-of 2026-10-29
   ```

   This writes the CSV snapshot to `data/processed/`.

2. Open `powerbi/practilizate.pbip` in Power BI Desktop. The report is saved as
   a project so it can be reviewed in Git; save it as `.pbix` if you need a
   single-file copy.

3. If the report asks for a refresh, use **Inicio → Actualizar**. The model is
   in Import mode and reads the CSV snapshot.

## Data source

The semantic model uses a Power Query parameter named `DataFolder`. Its default
is the absolute path to this repository's `data/processed` folder. If the
repository moves to another machine, update `DataFolder` in **Transformar
datos → Editar parámetros** before refreshing.

The model reads:

- `dashboard_dataset.csv` — one row per offer.
- `offer_careers.csv` — offer-to-career bridge.
- `offer_skills.csv` — offer-to-skill bridge.
- `quality_rules.csv` — the 17 quality rules and their results.
- `run_metadata.csv` — run timestamp and headline counts.
- `dim_idioma.csv` and `dim_estado.csv` — bilingual labels.

The CSV export is portable. PostgreSQL is an optional live source.

## Optional PostgreSQL connection

The star schema is created in `sql/schema.sql`. To refresh from PostgreSQL
instead of the CSV, point a new Power Query source at the `v_dashboard_ofertas`
view or at the facts and dimensions:

```text
postgresql://practilizate:practilizate@localhost:5433/practilizate
```

The Docker Compose service maps host port **5433** to avoid a local PostgreSQL
on 5432. Document the credentials in `.env`, never in the report.

## Pages

1. **Resumen ejecutivo** — KPIs, offers by career, status mix.
2. **Habilidades** — skills demand and coverage by career.
3. **Empresas** — company concentration and average compensation.
4. **Vencimientos** — offers ordered by deadline.
5. **Calidad** — the 17 quality rules, failures, and sample offer IDs.
6. **Cómo leer** — glossary, reset instructions, attribution, and limitations.

## Spanish / English toggle

Each page includes a `Idioma / Language` slicer backed by the disconnected
`Idioma` table. DAX measures use `SWITCH` over `SELECTEDVALUE(Idioma[Idioma])`:

- `Mensaje Ejecutivo`
- `Actualizado`

Page titles and KPI titles are bilingual by design. Source category labels
(careers, status, skills) stay in their published Spanish form; the toggle
changes the dynamic narrative and footer. The screenshots show both states.

## Accessibility

- The palette avoids red/green as the only signal; labels and legends are
  always visible.
- Every chart, table, card, and slicer has alt text.
- The report uses descriptive titles, a source footer, and a
  `Limpiar filtros` action button (`ClearAllSlicers`).
- The report is 1280×720 and fits a 1366×768 screen.

## Validation and regeneration

Validate the PBIR with the Microsoft authoring CLI:

```powershell
powerbi-report-author validate powerbi
```

The report was opened and validated with Power BI Desktop `2.159.883.0`.

To regenerate pages after editing `scripts/build_powerbi_report.py`:

```powershell
python scripts/build_powerbi_report.py
powerbi-report-author validate powerbi
```

The model is edited through the `powerbi-modeling` MCP and exported to
`practilizate.SemanticModel/definition`; do not hand-edit the TMDL while the
model is loaded in the MCP.

## Snapshot and screenshots

The checked-in screenshots use the live `live-20261029` snapshot: 389 offers,
83 companies, 65 careers, 24 skills, 97.7% quality, and 330 offers expiring
within 7 days. The report uses top-10 charts for careers, skills, and companies
so 65 careers and 83 companies remain readable.

- `docs/assets/dashboard-es.png`
- `docs/assets/dashboard-en.png`
- `docs/assets/excel-summary.png`
- `docs/assets/quality-report.png`

## Attribution

Data comes from public listings on [practicas.pe](https://www.practicas.pe/).
Practilizate is not affiliated with practicas.pe. Only aggregated data is
published; raw HTML and personal data are not included. See
[../DATA_SOURCES.md](../DATA_SOURCES.md) and [../NOTICE.md](../NOTICE.md).
