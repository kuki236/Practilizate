# Practilizate

**Observatorio de prácticas preprofesionales del Perú.**

Practilizate convierte avisos públicos de prácticas en un producto de datos reproducible: un modelo estrella validado en PostgreSQL, un dashboard en Power BI, un libro Excel y un informe de calidad de datos.

> **Estado:** documentación y roadmap listos. La implementación se sigue en [ROADMAP.md](ROADMAP.md).
> **English:** [README.md](README.md)

## Por qué Practilizate

Los estudiantes postulan sin datos comparables sobre sueldos, empresas, habilidades requeridas o fechas límite. Los centros de empleabilidad tampoco tienen una vista estructurada y actualizada del mercado.

Practilizate responde:

- ¿Qué habilidades se piden más por carrera y distrito?
- ¿Qué empresas publican más ofertas?
- ¿Qué rangos de subvención aparecen por rol y carrera?
- ¿Qué ofertas están por vencer?
- ¿Qué tan completa y confiable es la información publicada?

El análisis inicial de 73 ofertas era solo de Ingeniería de Sistemas en Lima. El producto está diseñado para **todas las carreras**.

## Qué incluye

- Ingesta multi-carrera desde practicas.pe.
- Normalización de empresa, ubicación, sueldo, fechas, carreras y habilidades.
- Reglas de calidad con informe visible.
- Modelo estrella en PostgreSQL con tablas puente de carrera y habilidad.
- Reporte Power BI con toggle español/inglés.
- Libro Excel en español.
- Test E2E repetible con artefacto y manifiesto.
- Documentación bilingüe.

## Arquitectura

```text
practicas.pe
    |
    v
[ingest] caché + rate limit
    |
    v
[normalize] ofertas canónicas
    |
    v
[quality] reglas + informe
    |
    v
[load] modelo estrella PostgreSQL
    |
    +--> [export] dashboard_dataset.csv
    +--> [export] practilizate.xlsx
    +--> [powerbi] practilizate.pbip
```

## Demo

![Resumen ejecutivo en Excel](docs/assets/excel-summary.png)

![Informe de calidad de datos](docs/assets/quality-report.png)

- Dashboard en español: `docs/assets/dashboard-es.png`
- Dashboard en inglés: `docs/assets/dashboard-en.png`
- Resumen Excel: `docs/assets/excel-summary.png`
- Informe de calidad: `docs/assets/quality-report.png`

## Fuente y atribución

Los datos provienen de avisos públicos de [practicas.pe](https://www.practicas.pe/).

- Practilizate **no está afiliado** a practicas.pe.
- Se usan datos públicos con fines educativos y de investigación.
- Solo se publican datos agregados. No se incluyen HTML crudo ni datos personales.
- El recolector respeta `robots.txt`, límites de tasa y caché.
- Ver [DATA_SOURCES.md](DATA_SOURCES.md) y [NOTICE.md](NOTICE.md).

## Inicio rápido

```powershell
git clone <repository-url>
cd practilizate
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
docker compose up -d db
Copy-Item .env.example .env
python -m practilizate run --source fixtures
pytest tests/e2e
```

El modo `fixtures` es determinista y no llama al sitio en vivo.

## Power BI

Abre `powerbi/practilizate.pbip` en Power BI Desktop y guárdalo como `.pbix` si lo necesitas.

- v0.1 usa `data/processed/dashboard_dataset.csv` para que sea portable.
- PostgreSQL queda documentado como fuente opcional en vivo.
- El reporte incluye toggle ES/EN y colores accesibles.

## Excel

El libro se genera en `data/processed/practilizate.xlsx` e incluye:

- `Portada`
- `Datos`
- `Resumen`
- `Habilidades`
- `Empresas`
- `Calidad`
- `Diccionario`

## Testing

- Solo E2E. Sin unit tests.
- El E2E ejecuta el pipeline completo contra una base PostgreSQL desechable.
- Usa un escenario medio-difícil: ofertas multi-carrera, duplicados, sueldo faltante, fechas inválidas, outliers y campos faltantes.
- Cada ejecución escribe un artefacto repetible en `artifacts/e2e/`:

```text
artifacts/e2e/
├─ run_manifest.json
├─ quality_report.json
├─ practilizate.xlsx
├─ dashboard_dataset.csv
└─ checksums.sha256
```

## Resultados

> Las métricas se completarán con el snapshot real y la ejecución E2E.

| Métrica | Valor |
|---|---|
| Ofertas procesadas | `[N]` |
| Empresas | `[M]` |
| Carreras | `[C]` |
| Habilidades | `[S]` |
| Calidad de datos | `[Q]%` |
| Ofertas que vencen en 7 días | `[D]` |
| Tiempo del pipeline | `[T]` |

## Heurísticas de Nielsen

El producto sigue las 10 heurísticas de usabilidad documentadas en [docs/heuristics.md](docs/heuristics.md). La evidencia se registra en [docs/heuristics-review.md](docs/heuristics-review.md).

## Estructura del proyecto

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
├─ excel/
├─ docker-compose.yml
├─ pyproject.toml
├─ .env.example
└─ .github/workflows/ci.yml
```

## Limitaciones

- v0.1 cubre Lima y prácticas preprofesionales.
- Los avisos pueden no publicar sueldo, fecha límite o requisitos detallados.
- La estructura del sitio puede cambiar; los fixtures protegen el test suite.
- Es un observatorio, no un tracker de postulaciones.
- La calidad de datos se reporta, no se oculta.

## Licencia

Código: MIT. Ver [LICENSE](LICENSE).

Los datos y datasets derivados no están cubiertos por la licencia MIT. Ver [DATA_SOURCES.md](DATA_SOURCES.md).
