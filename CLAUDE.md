# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**video2Text** — NUS M.Tech AIS Pattern Recognition project. A video → transcript → retrieval (RAG) pipeline: Python backend (FastAPI + ML/PyTorch pattern-recognition + retrieval pipeline), React frontend, deployed on AWS.

This repo's `.claude`-style harness (`agents/`, `skills/`, `commands/`, `rules/`) is a curated fork of [Everything Claude Code (ECC)](https://github.com/), cut down to Python + React + AWS + Claude Code scope only. See `SOUL.md` for the mental model and `MANIFEST.md` for exactly what was pinned and why.

## Prompt Defense Baseline

See `RULES.md` → "Prompt Defense Baseline". Applies to every agent and skill in this repo.

## Architecture

- **agents/** — 14 specialized subagents for delegation (planner, architect, spec-miner, reviewers, build-resolver, etc.)
- **skills/** — 35 skills: 32 pinned from ECC (workflow discipline, Python, React, RAG/LLM, ML) + 3 authored for this project (`spec-driven-development`, `contract-freeze`, `definition-of-done-gate`)
- **commands/** — 21 slash commands (`/plan`, `/prp-plan`, `/quality-gate`, `/python-review`, `/react-review`, `/skill-create`, etc.)
- **rules/** — layered always-follow guidelines: `common/` (universal) + `python/`, `react/`, `typescript/` (language-specific, override common — see `rules/README.md`)
- **MANIFEST.md** — the pinned/curated inventory; the source of truth for what's in this repo vs. the full ECC catalog

No `hooks/`, `scripts/`, or CI validator infrastructure was ported — those are ECC's own build tooling, not project-portable. Hook *conventions* are documented in `rules/*/hooks.md` for when this project is ready to automate formatting/lint checks.

## Key Commands

- `/plan`, `/prp-plan`, `/prp-prd`, `/prp-implement` — spec-driven planning and implementation (see `skills/spec-driven-development`)
- `/quality-gate` — formatter quality gate (ruff for Python, Biome/Prettier for TS/React)
- `/test-coverage` — coverage check
- `/security-scan` — security scan
- `/code-review`, `/python-review`, `/react-review`, `/fastapi-review` — language-specific review
- `/react-build`, `/react-test` — frontend build/test
- `/feature-dev` — end-to-end feature workflow
- `/project-init` — bootstrap a new module
- `/skill-create`, `/skill-health` — skill-creator subsystem (see below)
- `/update-docs` — refresh docs after a change

## Skill-Creator Subsystem

Ported from ECC as-is (`origin: ECC`), this is how new skills get created, evaluated, and kept honest over time:

- `/skill-create` — generate a new skill from git history / observed patterns
- `/skill-health` — check installed skills for staleness or drift
- `skills/skill-scout` — find/suggest an existing skill before writing a new one
- `skills/skill-comply` — TDD-style compliance harness that grades whether a skill's guidance actually gets followed (spec generator, scenario generator, classifier, grader — full Python tool under `skills/skill-comply/scripts/`)
- `skills/skill-stocktake` — audits which skills exist and their state (`scripts/scan.sh`, `scripts/quick-diff.sh`, `scripts/save-results.sh`)

Use `skill-scout` before authoring anything new; use `skill-comply` to validate a new or edited skill; use `skill-stocktake` periodically to catch drift.

## Development Notes

- Backend: Python (FastAPI), package manager per `pyproject.toml` once created.
- Frontend: React (+ TypeScript — `rules/typescript/` is carried as a dependency of `rules/react/*.md`).
- ML/retrieval: PyTorch for the pattern-recognition model, `skills/iterative-retrieval` + `skills/mle-workflow` for the retrieval/serving pipeline discipline.
- Cloud: AWS. No AWS-specific skill exists upstream in ECC — add project AWS conventions to `rules/aws/` (see `rules/README.md` → "Adding a New Language or Domain") as they solidify.
- Agent format: Markdown with YAML frontmatter (name, description, tools, model).
- Skill format: Markdown with clear sections (When to Use, How It Works, Examples) and `metadata.origin: ECC | project`.
- File naming: lowercase with hyphens (e.g., `python-reviewer.md`, `spec-driven-development`).

## Skills-to-File Mapping

| File(s) | Skill / Command |
|---------|------------------|
| `**/*.py` (backend, RAG pipeline) | `skills/python-patterns`, `skills/python-testing` — for FastAPI routes also `skills/fastapi-patterns`; invoke `/python-review`, `/fastapi-review` |
| `**/*.tsx`, `**/*.jsx`, `frontend/src/components/**` | `skills/react-patterns`, `skills/react-testing`, `skills/react-performance`, `skills/frontend-patterns`; invoke `/react-review`, `/react-build`, `/react-test` |
| `**/models/**`, `**/training/**` (PyTorch) | `skills/pytorch-patterns`, `skills/mle-workflow` |
| `**/retrieval/**`, `**/rag/**` | `skills/iterative-retrieval`, `skills/cost-aware-llm-pipeline`, `skills/prompt-optimizer` |
| `**/migrations/**`, `**/*.sql` | `skills/database-migrations`, `skills/postgres-patterns`; invoke `database-reviewer` agent |
| `openapi.yaml`, shared API/event schemas | `skills/contract-freeze` (builds on `skills/contract-first`) |
| New feature before any code | `skills/spec-driven-development`, `/prp-plan` or `/plan` |
| Before marking a task done | `skills/definition-of-done-gate`, `/quality-gate`, `/test-coverage` |
| `README.md` | `/update-docs` |

When spawning subagents, always pass conventions from the respective skill into the agent's prompt.
