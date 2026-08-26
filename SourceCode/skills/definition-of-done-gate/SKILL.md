---
name: definition-of-done-gate
description: Run before calling any video2Text task, PR, or session finished. A checklist gate combining mechanical checks (build/type/lint/test, imported from verification-loop and delivery-gate) with project-specific checks (spec updated, contract respected, security/AWS credential hygiene, model/retrieval eval where applicable). Nothing is "done" until every applicable row passes.
metadata:
  origin: project
  status: active
---

# Definition of Done Gate (video2Text)

A change is not done because the code runs once. It's done when it clears this gate. This skill composes the mechanical checks already pinned from ECC (`verification-loop`, `delivery-gate`) with checks specific to this project's stack (Python/FastAPI, React, AWS, RAG/ML), rather than re-deriving the mechanical parts from scratch.

Two layers, same pattern as `delivery-gate`'s own distinction:

- **Mechanical layer** — deterministic, scriptable, no judgment calls. Either it passes or it doesn't.
- **Review layer** — needs a reviewer (human or agent) to judge correctness, not just presence.

## When to Activate

- Before marking any task/ticket/PR as complete.
- Before running `/prp-commit` or `/prp-pr`.
- At the end of a Claude Code session that touched `backend/`, `frontend/`, `rag/`, `ml/`, or infra.
- Before a frozen contract change is merged (in addition to `skills/contract-freeze`'s own verification step).

## The Gate

### 1. Mechanical Checks (must all pass, no exceptions)

| Check | Command / Source | Blocks on |
|---|---|---|
| Backend build/type | `pyright .` or project equivalent | Any type error |
| Backend lint/format | `ruff format --check` + `ruff check` | Any violation |
| Backend tests | project test runner (`pytest` or equivalent) | Any failure, coverage regression |
| Frontend build | `npm run build` / project equivalent | Build failure |
| Frontend type check | `tsc --noEmit` | Any type error |
| Frontend lint/format | Biome or Prettier `--check` | Any violation |
| Frontend tests | `/react-test` | Any failure |
| Security scan | `/security-scan` | New high/critical finding, hardcoded secret, hardcoded AWS credential |
| Quality gate (formatter) | `/quality-gate` | Formatter check failure per file type |
| Disk / hygiene | `skills/delivery-gate` checks (if wired up as a Stop hook) | Critical disk space, stale learning libraries on a complex task |

Run `skills/verification-loop`'s phased approach (build → type → lint → test) rather than checks in an arbitrary order — a failure early in the phase order usually explains a failure later, and fixing out of order wastes cycles.

### 2. Project-Specific Checks

| Check | What it verifies | Owner |
|---|---|---|
| Spec updated | The touched capability's `openspec/specs/<capability>/spec.md` reflects the change (`ADDED`/`MODIFIED`/`REMOVED` Requirements, `Last verified` bumped with current commit) | Implementer |
| Contract respected | If a frozen boundary (`skills/contract-freeze`) was touched, the change went through propose→review→freeze/thaw, not a silent edit | `contract-freeze` boundary owner |
| No plaintext AWS credentials | No AWS access keys, session tokens, or secrets in code, logs, commit history, or `.env` files committed to the repo | Implementer + `security-reviewer` agent |
| IAM least-privilege | Any new IAM policy/role grants only the actions/resources actually needed, not `*` | `security-reviewer` agent |
| S3 key / event contract respected | Any change to ingestion key naming or event payloads went through the AWS boundary freeze protocol | Implementer |
| RAG/model eval, when applicable | If retrieval ranking, prompt template, or the pattern-recognition model changed, `skills/eval-harness` or `skills/ai-regression-testing` was run and did not regress the tracked metric | Implementer |
| Cost sanity, when applicable | If the LLM/embedding call pattern changed, `skills/cost-aware-llm-pipeline` was consulted — no accidental N+1 calls to the model API | Implementer |

### 3. Review Layer

- `code-reviewer` agent (or human) has reviewed the diff.
- The relevant language reviewer ran: `python-reviewer` / `fastapi-reviewer` for backend, `react-reviewer` for frontend, `database-reviewer` for any migration.
- For anything touching auth, secrets, or AWS IAM: `security-reviewer` agent, not skipped even under time pressure.

## Anti-Patterns

- FAIL: Treating "tests pass locally" as done without running the full mechanical layer (lint/type/security-scan skipped "because it's probably fine").
- FAIL: Marking a task done with a spec left stale — the next person (or agent) trusts `Last verified` and will build on a lie.
- FAIL: Merging a contract change because "the tests still pass on my side" without the other boundary owner's sign-off (see `skills/contract-freeze`).
- FAIL: Skipping the RAG/model eval check because "it's just a prompt tweak" — prompt changes are exactly what `ai-regression-testing` exists to catch.
- FAIL: Rationalizing a shortcut in the session transcript ("skip tests for now", "pre-existing bug, not my problem") instead of either fixing it or explicitly flagging it as out of scope in the PR description.

## Completion Checklist

- [ ] All rows in the Mechanical Checks table pass.
- [ ] All applicable rows in the Project-Specific Checks table pass (mark N/A explicitly for rows that don't apply, don't silently skip).
- [ ] Review layer completed by the appropriate reviewer agent(s).
- [ ] Nothing in this checklist was rationalized away — if a check was skipped, it's recorded with a reason, not silently omitted.

## Related Skills

- `skills/verification-loop` — the phased build/type/lint/test mechanics this gate runs
- `skills/delivery-gate` — mechanical Stop-hook checks (disk space, learning-library hygiene) if wired up
- `skills/spec-driven-development` — produces the spec this gate checks for freshness
- `skills/contract-freeze` — the boundary protocol this gate checks was respected
- `skills/security-review`, `skills/security-scan` — the security checks referenced above
- `skills/eval-harness`, `skills/ai-regression-testing` — RAG/model regression checks
- `skills/cost-aware-llm-pipeline` — cost sanity check for LLM/embedding call changes
