---
description: Complete Practilizate from the roadmap
agent: build
---

Complete this project. Read:

- `SPECS.md`
- `README.md`
- `CODESTYLE.md`
- `ROADMAP.md`
- `AGENTS.md`
- `docs/heuristics.md`

Work through the ROADMAP checkpoints in order. Do not skip checkpoints.

After each checkpoint:

1. Run the E2E suite and write artifacts to `artifacts/e2e/`.
2. Update the checkpoint checkbox in `ROADMAP.md`.
3. Update `README.md` and `README.es.md` metrics or screenshots if the checkpoint changes them.
4. Run `ruff format` and `ruff check`.
5. Commit with a conventional commit.

Rules:

- Do not write unit tests. Use E2E only.
- Do not modify fixtures to make tests pass.
- Do not commit secrets, raw scraped HTML, generated databases, or `.env`.
- Keep user-facing dashboard/Excel labels in Spanish; use the ES/EN toggle in Power BI.
- Follow `docs/heuristics.md`.
- Stop only when all roadmap checkpoints are complete and CI is green.
