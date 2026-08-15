# Soul

## Core Identity

video2Text's Claude harness is a curated, project-scoped fork of [Everything Claude Code (ECC)](https://github.com/): 14 agents, 35 skills, 21 commands, and a layered rule set — cut down from ECC's full multi-language catalog to exactly what this project needs: **Python (FastAPI backend + RAG/ML pipeline) + React (frontend) + AWS (deployment) + Claude Code (agent harness)**.

This is a course project for the NUS M.Tech AIS Pattern Recognition module. The harness exists to keep implementation disciplined across a small team working on a video → transcript → retrieval pipeline, not to be a general-purpose plugin.

## Core Principles

1. **Spec-First** — before code, a spec exists (see `skills/spec-driven-development`). No behavior ships that isn't traceable to a Requirement or Invariant.
2. **Contracts Freeze Before Parallel Work Starts** — frontend and backend/RAG-service boundaries are pinned to one authoritative artifact before both sides build in parallel (see `skills/contract-freeze`, built on top of the imported `contract-first` skill).
3. **Nothing Ships Without Clearing the DoD Gate** — a deterministic, mechanically-checked Definition of Done gate runs before any change is called finished (see `skills/definition-of-done-gate`).
4. **Test-Driven** — write or refresh tests before trusting implementation changes (`tdd-workflow`, `tdd-guide` agent).
5. **Security-First** — validate inputs, protect secrets and AWS credentials, keep safe defaults (`security-review`, `security-scan`, `security-reviewer` agent).
6. **Agent-First** — route work to the right specialist as early as possible instead of doing everything in one long freeform session.

## Agent Orchestration Philosophy

Specialists are invoked proactively: `planner`/`architect` for design, `spec-miner` to extract specs from existing code, `python-reviewer`/`fastapi-reviewer`/`react-reviewer` for language-specific review, `security-reviewer` before anything touching auth/secrets/IAM, `database-reviewer` for schema and pgvector/Postgres migrations, and `code-explorer` before planning changes in unfamiliar code.

## Provenance

Everything under `agents/`, `commands/`, `skills/` (excluding `skills/spec-driven-development`, `skills/contract-freeze`, `skills/definition-of-done-gate`), and `rules/` is pinned from ECC with `origin: ECC` in frontmatter where applicable. See `MANIFEST.md` for the exact pinned set and what was deliberately left out.
