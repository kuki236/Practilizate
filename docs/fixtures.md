# Fixtures and Expected Outcomes

The fixture set is synthetic. It imitates the practicas.pe search and detail pages so the
real parser is exercised without scraping during tests. Files live under `data/fixtures/`.

## Layout

```text
data/fixtures/
├─ filter.html                       # career filter form used for discovery
├─ search/
│  ├─ 1-page-1.html                  # Administración (career 1)
│  ├─ 10-page-1.html                 # Ingeniería de Sistemas (career 10), page 1
│  ├─ 10-page-2.html                 # Ingeniería de Sistemas, page 2
│  └─ 34-page-1.html                 # Arquitectura (career 34)
└─ detail/
   ├─ oferta-...-90001.html          # JobPosting JSON-LD per offer
   └─ ...
```

The fixture source discovers careers from `filter.html`, reads pages until a file is
missing, and maps each offer URL to `detail/<last-path-segment>`.

## Offers

| ID | Title | Company | Careers | Key case |
|---|---|---|---|---|
| 90001 | Practicante de Análisis de Datos | Banco Andino | 1, 10 | Multi-career and duplicate URL across queries |
| 90002 | Practicante de Marketing Digital | Tienda Perú | 1 | Missing salary; expires within 7 days |
| 90003 | Practicante de Soporte TI | Municipalidad de Lima | 10 | Missing deadline |
| 90004 | Practicante de Análisis Financiero | Finanzas del Sur | 1 | Invalid published date |
| 90005 | Practicante de Automatización | Minera Cerro Verde | 10 | Salary outlier |
| 90006 | Practicante de Gestión Humana | *(missing)* | 1 | Missing company |
| 90007 | Practicante de Análisis de Datos | Banco Andino | 10 | Duplicate title + company + deadline |
| 90008 | Practicante de Ciberseguridad | Telecom Andina | 10 | Deadline before publication |
| 90009 | Practicante de Logística | Grupo Mercado | 1 | Missing location |
| 90010 | Practicante de Arquitectura Sostenible | Estudio Verde | 34 | Unknown attendance |
| 90011 | Practicante de Derecho Corporativo | Estudio Legal | 1 | Detailed requirements, no skills |
| 90012 | Practicante de Contabilidad | Estudio Contable | 1 | Clean baseline |

Thirteen listing references resolve to twelve unique offers. Offer 90001 appears in two
career queries and must be stored once with two career links.

## Expected quality results (as of 2026-10-29)

| Rule | Expected result | Offers |
|---|---|---|
| R01 Required fields | Fail | 90006 |
| R02 Unique offer URL | Pass | — |
| R03 Absolute URL | Pass | — |
| R04 Valid published date | Fail | 90004 |
| R05 Valid deadline | Fail | 90003 |
| R06 Deadline ≥ published | Fail | 90008 |
| R07 Salary numeric or null | Pass | 90002 uses an explicit null |
| R08 Salary bounds | Fail | 90005 |
| R09 Company not empty | Fail | 90006 |
| R10 Location present | Fail | 90009 |
| R11 Modality allowed | Pass | — |
| R12 Attendance allowed | Fail | 90010 |
| R13 At least one career | Pass | — |
| R14 Duplicate title + company + deadline | Fail | 90001, 90007 |
| R15 Skills with detailed requirements | Fail | 90011 |
| R16 Fetch timestamp present | Pass | — |
| R17 UTF-8 normalized | Pass | — |

## Expected database rows

- `fact_ofertas`: 12 rows.
- `dim_carrera`: 3 rows.
- `dim_empresa`: 10 rows (two offers share Banco Andino; one company missing).
- `dim_ubicacion`: 8 rows (offers share districts; one missing location).
- `bridge_oferta_carrera`: 13 rows.
- `bridge_oferta_habilidad`: 34 rows with the current lexicon.
- Duplicate URL 90001 is not duplicated.

## Expected statuses (as of 2026-10-29)

- `expiring_soon`: 90002 (deadline 2026-11-02).
- `expired`: 90008 (deadline 2026-10-20).
- `unknown`: 90003 (no deadline).
- `active`: the remaining offers, including 90004 whose invalid publication date is a
  quality failure but does not remove the offer.

## Determinism

The E2E suite passes `--as-of 2026-10-29`. Changing the reference date changes statuses
and the expiring-soon metric, never the raw records.
