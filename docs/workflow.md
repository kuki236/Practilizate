# Development Workflow

Practilizate follows a spec-first workflow designed to keep agent output small, reviewable, and reproducible.

## 1. Spec

Write or update `SPECS.md` before implementation. The spec defines scope, data sources, data model, quality rules, UI, testing, and acceptance criteria.

## 2. Roadmap

`ROADMAP.md` breaks the spec into checkpoints. Each checkpoint has:

- a small deliverable,
- an acceptance criterion,
- a suggested conventional commit.

## 3. README

`README.md` describes the finished project. It is written before the code so the target state is clear. Metrics and screenshots are placeholders until the checkpoints are complete.

## 4. Code style

`CODESTYLE.md` defines language, formatting, naming, logging, testing, and commit conventions.

## 5. Execution

Start a new agent session and run:

```text
/goal Complete this project. Read ./SPECS.md | README.md | CODESTYLE.md | ROADMAP.md.
```

The command is defined in `.opencode/command/goal.md`.

The agent must:

1. read the docs,
2. work checkpoint by checkpoint,
3. run E2E after each checkpoint,
4. update the roadmap,
5. format and lint,
6. commit.

## 6. Review

At the end:

- run the full E2E,
- review `docs/heuristics-review.md`,
- check README metrics and screenshots,
- review the repository for secrets and raw data,
- tag `v0.1.0`.

## Why this works

- The spec prevents scope drift.
- The roadmap prevents the agent from jumping around.
- The README forces a user-facing definition of done.
- The code style prevents inconsistent output.
- E2E with artifacts proves the result instead of trusting a summary.
