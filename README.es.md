# Practilizate

**Observatorio de prácticas preprofesionales del Perú.**

Practilizate convierte avisos públicos de prácticas en un producto de datos reproducible: un modelo estrella validado en PostgreSQL, un dashboard en Power BI, un libro Excel y un informe de calidad de datos.

> **Estado:** v0.1.2 con snapshot live (`live-20261029`). El modelo estrella en PostgreSQL, el libro Excel, el reporte bilingüe en Power BI y los artefactos E2E están en el repositorio.
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

![Dashboard en español](docs/assets/dashboard-es.png)

![Dashboard en inglés](docs/assets/dashboard-en.png)

![Resumen ejecutivo en Excel](docs/assets/excel-summary.png)

![Informe de calidad de datos](docs/assets/quality-report.png)

- Dashboard en español: `docs/assets/dashboard-es.png`
- Dashboard en inglés: `docs/assets/dashboard-en.png`
- Resumen Excel: `docs/assets/excel-summary.png`
- Informe de calidad: `docs/assets/quality-report.png`
- Guía de Power BI: [powerbi/README.md](powerbi/README.md)

## Fuente y atribución

Los datos provienen de avisos públicos de [practicas.pe](https://www.practicas.pe/).

- Practilizate **no está afiliado** a practicas.pe.
- Se usan datos públicos con fines educativos y de investigación.
- Solo se publican datos agregados. No se incluyen HTML crudo ni datos personales.
- El CSV y el libro Excel live quedan fuera de Git (`data/processed/`); las
  capturas públicas solo muestran conteos agregados.
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
python -m practilizate run --source fixtures --as-of 2026-10-29
pytest tests/e2e
```

El modo `fixtures` es determinista y no llama al sitio en vivo.
Para el snapshot live:

```powershell
python -m practilizate run --source live --as-of 2026-10-29
```

Docker Compose publica PostgreSQL en el puerto **5433**; `.env.example` ya usa
ese puerto. La ingesta live usa caché, un límite de tasa configurable y el
filtro de carreras del sitio (65 carreras en la fecha del snapshot).

## Cómo usar Practilizate

**1. Revisar el resultado sin instalar nada**

Abre el release de GitHub, las capturas y `powerbi/practilizate.pbip` en Power
BI Desktop. El PBIP contiene la definición del reporte; guárdalo como `.pbix`
si necesitas un archivo único.

**2. Ejecutar el pipeline localmente**

Sigue el inicio rápido. El modo `fixtures` es determinista y sirve para
verificar la instalación. Usa `--source live` para avisos reales.

**3. Usar los entregables**

- `data/processed/practilizate.xlsx` — libro en español para estudiantes y centros de empleabilidad.
- `data/processed/dashboard_dataset.csv` — snapshot para Power BI/analistas.
- `powerbi/practilizate.pbip` — fuente del reporte bilingüe.
- Vista PostgreSQL `v_dashboard_ofertas` — análisis opcional en vivo.

**4. Compartirlo en línea**

El producto actual es un flujo local CLI + Power BI Desktop + Excel, no una
aplicación web alojada. Para compartir el dashboard, publica el PBIP en un
workspace de Power BI (requiere cuenta/licencia) o monta una aplicación web
sobre el CSV/PostgreSQL. El repositorio público publica capturas y evidencia
agregada; el CSV/Excel live quedan locales.

**5. Automatizar una actualización**

Programa `python -m practilizate run --source live --as-of <fecha>` con Task
Scheduler o cron. El recolector usa caché y respeta el límite de tasa. El E2E
usa fixtures y nunca llama al sitio público.

## Power BI

Abre `powerbi/practilizate.pbip` en Power BI Desktop y guárdalo como `.pbix` si lo necesitas.

- v0.1 usa `data/processed/dashboard_dataset.csv` y los CSV de soporte para que sea portable.
- El modelo lee el snapshot mediante el parámetro `DataFolder`; actualízalo si mueves el repositorio.
- Las seis páginas cubren resumen ejecutivo, habilidades, empresas y subvenciones, vencimientos, calidad y una guía bilingüe.
- El reporte incluye toggle ES/EN (tabla `Idioma` y medidas `SWITCH`), texto alternativo, colores accesibles, pie de fuente y botón `Limpiar filtros`.
- PostgreSQL queda documentado como fuente opcional en vivo en [powerbi/README.md](powerbi/README.md).

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

- Solo E2E. Sin tests unitarios.
- El E2E ejecuta el pipeline completo contra una base PostgreSQL desechable.
- Usa un escenario **sintético** medio-difícil: ofertas multi-carrera, duplicados, sueldo faltante, fechas inválidas, outliers y campos faltantes.
- El snapshot live se valida aparte; CI no consulta el sitio público.
- Cada ejecución E2E escribe un artefacto sintético repetible en `artifacts/e2e/`:

```text
artifacts/e2e/
├─ run_manifest.json
├─ quality_report.json
├─ normalized_offers.json
├─ database_load.json
├─ export_report.json
├─ practilizate.xlsx
├─ dashboard_dataset.csv
├─ offer_careers.csv
├─ offer_skills.csv
├─ quality_rules.csv
├─ run_metadata.csv
├─ dim_idioma.csv
├─ dim_estado.csv
└─ checksums.sha256
```

`artifacts/e2e/` se genera y está en `.gitignore`; CI lo sube como artefacto y
el release adjunta el paquete.

## Resultados

> Snapshot live `live-20261029` (`--source live --as-of 2026-10-29`), obtenido
> del sitio público con límite de 1 s. Los conteos son de un momento dado.

| Métrica | Valor |
|---|---|
| Ofertas procesadas | 389 |
| Empresas | 83 |
| Carreras | 65 |
| Habilidades | 24 |
| Calidad de datos | 97.7% |
| Ofertas que vencen en 7 días | 330 |
| Tiempo del pipeline | 530.6 s (~8.8 min, PostgreSQL incluido) |

El informe de calidad marca 3 reglas con advertencias y ninguna regla crítica:
R06 (1 oferta con vencimiento anterior a la publicación), R14 (38 grupos
duplicados por título + empresa + vencimiento) y R15 (113 ofertas con requisitos
detallados pero sin habilidad del léxico). La subvención se publica en 156 de
389 ofertas; los promedios excluyen faltantes y valores atípicos mayores a
S/ 12,000. Ver [docs/fixtures.md](docs/fixtures.md) para el contrato E2E
sintético y [docs/data-dictionary.md](docs/data-dictionary.md) para los campos.

## Heurísticas de Nielsen

El producto sigue las 10 heurísticas de usabilidad documentadas en [docs/heuristics.md](docs/heuristics.md). La evidencia está completa en [docs/heuristics-review.md](docs/heuristics-review.md), con las capturas, el libro Excel, el informe de calidad y el manifiesto E2E.

## Diccionario de datos

Las definiciones del modelo estrella, el CSV, el informe de calidad y el manifiesto están en [docs/data-dictionary.md](docs/data-dictionary.md).

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
├─ scripts/
├─ docker-compose.yml
├─ pyproject.toml
├─ .env.example
└─ .github/workflows/ci.yml
```

## Limitaciones

- v0.1 cubre Lima y prácticas preprofesionales.
- Los avisos pueden no publicar sueldo, fecha límite o requisitos detallados. En
  el snapshot live, 233 de 389 ofertas no publican subvención.
- El léxico de habilidades cubre 24 habilidades canónicas; 113 ofertas live
  tienen requisitos detallados pero ninguna coincidencia. Ampliar el léxico es
  una tarea de v0.2.
- El snapshot live es de un momento dado; 330 ofertas vencen dentro de 7 días
  de la fecha de corte porque muchas fechas límite se concentran.
- R14 marca 38 grupos duplicados por título + empresa + vencimiento; se mantienen
  visibles para auditoría en lugar de eliminarse en silencio.
- La estructura del sitio puede cambiar; los fixtures protegen el test suite.
- Es un observatorio, no un tracker de postulaciones.
- La calidad de datos se reporta, no se oculta.

## Licencia

Código: MIT. Ver [LICENSE](LICENSE).

Los datos y datasets derivados no están cubiertos por la licencia MIT. Ver [DATA_SOURCES.md](DATA_SOURCES.md).
