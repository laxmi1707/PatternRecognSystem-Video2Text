# MANIFEST

This is the source of truth for what's in this repo's Claude Code harness (`agents/`, `skills/`, `commands/`, `rules/`) versus the full [Everything Claude Code (ECC)](https://github.com/) catalog it was cut down from.

**Upstream source pinned at**: ECC `v2.1.0`.

**Scope discipline**: only Python (FastAPI backend + ML/RAG pipeline) + React (frontend) + AWS (deployment) + Claude Code (this harness) + the general engineering workflow layer (TDD, spec-driven dev, contract discipline, DoD gate) were kept. Everything for other languages, frameworks, and domains (Go, Rust, Java/Kotlin/Spring, Vue/Angular, mobile, homelab networking, supply chain, healthcare, prediction markets, etc.) was deliberately discarded — do not re-add it piecemeal; if a new need shows up, pin it deliberately here.

Re-syncing from upstream ECC should be a deliberate, reviewed diff against this file — not a bulk re-copy.

## Skills (35 total: 32 pinned `origin: ECC` + 3 authored `origin: project`)

### Project-authored (`origin: project`)

| Skill | Purpose |
|---|---|
| `spec-driven-development` | Sequences problem → spec → plan → code → verify for this project |
| `contract-freeze` | Freeze ceremony for frontend/backend/AWS boundaries, built on `contract-first` |
| `definition-of-done-gate` | Project-specific DoD checklist gate, built on `verification-loop` + `delivery-gate` |

### Workflow / engineering discipline (`origin: ECC`)

| Skill | Why pinned |
|---|---|
| `tdd-workflow` | Test-first discipline used by `spec-driven-development` step 4 |
| `verification-loop` | Build/type/lint/test phases used by `definition-of-done-gate` |
| `contract-first` | Underlying mechanics wrapped by `contract-freeze` |
| `delivery-gate` | Mechanical Stop-hook hygiene checks (disk, learning-library staleness) |
| `git-workflow` | Commit/branch conventions |
| `coding-standards` | Language-agnostic baseline standards |
| `api-design` | Resource/response/error/pagination/versioning design for the HTTP API |
| `error-handling` | Cross-cutting error handling conventions |
| `architecture-decision-records` | ADR format for recording design decisions |
| `security-review` | Security review checklist |
| `security-scan` | Automated security scanning workflow |
| `database-migrations` | Migration discipline (used with `postgres-patterns`) |
| `eval-harness` | Eval-driven development for the RAG/ML pipeline |
| `ai-regression-testing` | Regression tests for prompt/model/response-shape drift |

### RAG / LLM pipeline (`origin: ECC`)

| Skill | Why pinned |
|---|---|
| `iterative-retrieval` | Retrieval strategy patterns for the RAG pipeline |
| `deep-research` | Structured research workflow (literature review, dataset/library research) |
| `cost-aware-llm-pipeline` | Cost control for LLM/embedding call patterns |
| `prompt-optimizer` | Prompt engineering/optimization workflow |

### Python (`origin: ECC`)

| Skill | Why pinned |
|---|---|
| `python-patterns` | Core Python idioms and structure |
| `python-testing` | pytest conventions and test structure |
| `fastapi-patterns` | Backend API framework patterns |

### React / Frontend (`origin: ECC`)

| Skill | Why pinned |
|---|---|
| `react-patterns` | Core React idioms and component structure |
| `react-testing` | React testing conventions |
| `react-performance` | Performance patterns (rendering, bundle size) |
| `frontend-patterns` | Cross-cutting frontend architecture patterns |

### Backend / Data (`origin: ECC`)

| Skill | Why pinned |
|---|---|
| `backend-patterns` | Service/API-layer architecture patterns |
| `postgres-patterns` | Postgres (incl. pgvector-style usage) patterns |

### ML / Pattern Recognition (`origin: ECC`)

| Skill | Why pinned |
|---|---|
| `mle-workflow` | Production ML workflow: data contracts, reproducible training, eval, deploy, monitor, rollback |
| `pytorch-patterns` | PyTorch patterns for the pattern-recognition model |

### Skill-Creator Subsystem (`origin: ECC`)

| Skill | Why pinned |
|---|---|
| `skill-comply` | TDD-style compliance harness that grades whether a skill's guidance is actually followed |
| `skill-scout` | Find/suggest an existing skill before authoring a new one |
| `skill-stocktake` | Audits which skills exist and their state |

**Not pinned, deliberately**: no AWS-specific skill exists upstream in ECC v2.1.0 — there was nothing to pin. AWS conventions for this project live in `contract-freeze` (boundary 3) and `definition-of-done-gate` for now; promote to a standalone `skills/aws-*` skill via `skill-scout` → author → `skill-comply` once there's enough project-specific AWS guidance to justify it.

## Commands (21, all `origin: ECC`)

| Command | Purpose |
|---|---|
| `plan.md` | Quick conversational planning, no artifact |
| `plan-prd.md` | Planning from a PRD |
| `prp-prd.md` | Interactive PRD generator |
| `prp-plan.md` | Detailed implementation plan with codebase pattern extraction |
| `prp-implement.md` | Execute a plan with validation loops |
| `prp-commit.md` | Commit step of the PRP pipeline |
| `prp-pr.md` | PR step of the PRP pipeline |
| `quality-gate.md` | Formatter quality gate (ruff / Biome / Prettier) |
| `test-coverage.md` | Coverage check |
| `security-scan.md` | Security scan |
| `code-review.md` | General code review |
| `python-review.md` | Python-specific review |
| `react-review.md` | React-specific review |
| `react-build.md` | Frontend build |
| `react-test.md` | Frontend test run |
| `fastapi-review.md` | FastAPI-specific review |
| `feature-dev.md` | End-to-end feature workflow |
| `project-init.md` | Bootstrap a new module |
| `skill-create.md` | Generate a skill from git history (skill-creator subsystem) |
| `skill-health.md` | Check installed skills for staleness/drift (skill-creator subsystem) |
| `update-docs.md` | Refresh docs after a change |

## Agents (14, all `origin: ECC`)

| Agent | Purpose |
|---|---|
| `architect.md` | System/architecture design |
| `planner.md` | Implementation planning |
| `spec-miner.md` | Extract Requirement/Invariant specs from existing code |
| `tdd-guide.md` | TDD guidance |
| `code-reviewer.md` | General code review |
| `security-reviewer.md` | Security analysis |
| `python-reviewer.md` | Python-specific review |
| `fastapi-reviewer.md` | FastAPI-specific review |
| `react-reviewer.md` | React-specific review |
| `react-build-resolver.md` | Fix React/frontend build errors |
| `database-reviewer.md` | Schema/migration/query review |
| `performance-optimizer.md` | Performance analysis |
| `code-explorer.md` | Fast codebase search/mapping |
| `doc-updater.md` | Documentation updates |

## Rules (`origin: ECC`, layered)

| Directory | Purpose |
|---|---|
| `rules/common/` | Universal defaults (agents, code-review, coding-style, development-workflow, git-workflow, hooks, patterns, performance, security, testing) |
| `rules/python/` | Overrides for Python, includes `fastapi.md` |
| `rules/react/` | Overrides for React — references `../typescript/` directly |
| `rules/typescript/` | Pulled in solely as a dependency of `rules/react/*.md` |

See `rules/README.md` for the precedence model (language-specific overrides common) and how to add `rules/aws/` later.

## Explicitly Discarded

Everything else in ECC v2.1.0: other language rule/skill/agent sets (Go, Rust, Java/Kotlin, Swift, PHP, Ruby, C#/F#, Perl, Dart/Flutter, Vue/Angular/Nuxt, ArkTS/HarmonyOS), domain-specific skill families (healthcare, supply chain, prediction markets, homelab networking, customs/trade, energy procurement), `hooks/` runtime + `scripts/` CI/install tooling (ECC's own build infrastructure, not project-portable), `.claude/homunculus` (continuous-learning/instinct evolution subsystem), locale-translated docs, and non-Claude harness adapters (`.codex`, `.cursor`, `.gemini`, `.kiro`, `.trae`, `.zed`, `.qwen`, `.kimi`, `.hermes`, `.openclaw`, `.opencode`, `.codebuddy`, `.agents`).
