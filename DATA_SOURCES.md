# Data Sources and Attribution

## Primary source

Practilizate uses public internship listings from:

- Site: https://www.practicas.pe/
- Search endpoint: https://www.practicas.pe/resultados-busqueda.php
- Filters used in v0.1: all careers, Lima (`dep=15`), pre-professional modality, newest first.
- Access date: 2026-10-29.

## Attribution

> Data source: practicas.pe. Practilizate is an independent educational project and is not affiliated with, endorsed by, or sponsored by practicas.pe.

Attribution must appear in:

- `README.md`
- `README.es.md`
- the Power BI report footer,
- the Excel `Portada` sheet,
- this file and `NOTICE.md`.

## Permitted use and limitations

- The project uses publicly accessible listings for educational and research purposes.
- The collector must respect `robots.txt`, site terms, rate limits, and caching.
- Do not collect personal data.
- Do not republish raw HTML or complete raw listings in a public repository.
- Publish only aggregated or derived data unless explicit permission is obtained.
- If practicas.pe requests removal of data or code, comply promptly.

## Repository policy

Private repository:

- May contain curated fixtures and aggregated outputs.
- Must not contain secrets, personal data, or raw production databases.

Public repository:

- Code: MIT.
- Data: not covered by the MIT license.
- No raw scraped HTML.
- Only synthetic or curated fixtures.
- Only aggregated outputs with attribution.

## Legal note

This document is a good-faith data-handling policy, not legal advice. Review the site terms and applicable Peruvian law before publishing data or making the repository public.
