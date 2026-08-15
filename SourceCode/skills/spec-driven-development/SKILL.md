---
name: spec-driven-development
description: Use before writing any non-trivial code in video2Text — video ingestion, transcription, embedding/retrieval, RAG answer generation, or the React frontend. Governs how a feature goes from problem statement to a flat, machine-checkable spec (Requirement/Invariant blocks) to an implementation plan to code, so nothing ships that isn't traceable to a written behavior.
metadata:
  origin: project
  status: active
---

# Spec-Driven Development (video2Text)

Every non-trivial change in this repo follows one pipeline: **problem → spec → plan → code → verify**. No phase is skipped, and no phase is done out of order. This skill is the umbrella that sequences the pinned ECC assets already in this repo — it does not reimplement them.

This skill governs *sequencing*. `skills/contract-freeze` governs cross-boundary agreement within the plan/implement phases. `skills/definition-of-done-gate` governs what "done" means at the end.

## When to Activate

- Starting any feature: a new ingestion step, a retrieval strategy change, a new API route, a new frontend view.
- Onboarding an existing, undocumented module (brownfield) before modifying it.
- A bug fix that reveals the spec was wrong, missing, or never written.
- Any PR that touches `backend/`, `frontend/`, `rag/`, `ml/`, or infra without a corresponding spec change.

Do not invoke this for a one-line typo fix, a config value tweak, or a change with no observable behavior difference.

## The Pipeline

### 1. Problem → PRD (when the ask is fuzzy)

If the feature request is a vague idea rather than a concrete requirement, run `/prp-prd` first. It is problem-first and hypothesis-driven: it will refuse to invent requirements and will mark unknowns `TBD - needs research` instead. Do not proceed to a plan on top of invented requirements.

If the request is already concrete (a specific behavior, a specific bug), skip straight to step 2.

### 2. Spec: Requirement / Invariant blocks

Every behavior in this codebase is one of two things:

- **Requirement** — triggered: `WHEN <condition> THEN <observable outcome>`. Has at least one `#### Scenario:`.
- **Invariant** — always true, not triggered. Has no Scenarios; may have `<!-- verified_by: -->`.

There are no other block types. No "API Contracts" chapter, no "Business Rules" chapter — see the `spec-miner` agent's output format for the exact structure (`### Requirement:` / `### Invariant:`, `<!-- id -->`, `<!-- entities -->`, `<!-- enforced -->`, `<!-- depends_on -->`, `<!-- triggers -->`).

- **New feature, no existing spec for the area**: write the spec by hand first, in the `spec-miner` output format, under `openspec/specs/<capability>/spec.md`. Example capabilities for this project: `video-ingestion`, `transcription`, `embedding-index`, `retrieval`, `rag-answer`, `frontend-chat`, `auth`.
- **Existing code, no spec yet (brownfield)**: run the `spec-miner` agent against the module first. Never hand-write a spec for code you haven't read — mine it, then edit.
- **Changing existing behavior**: don't edit the Requirement in place and lose history. Add `## MODIFIED Requirements` matched by `<!-- id: -->` (the id is stable and does not change when the human-readable name changes). Add `## ADDED Requirements` / `## REMOVED Requirements` for net-new or deleted behavior.

Every Requirement must have `entities` and `enforced` at minimum — an unsearchable spec is a dead spec. If the code's contract is unclear, write `<!-- uncertainty: <reason> -->` — never guess.

### 3. Plan

Once the spec exists (or the PRD phase is concrete enough), run `/prp-plan <spec or feature description>`. The plan must pass its own "No Prior Knowledge Test": a developer unfamiliar with this codebase should be able to implement using only the plan, without searching the codebase or asking questions.

If the plan crosses a service/component boundary (frontend ↔ backend, backend ↔ RAG service, backend ↔ AWS-managed service), stop here and run `skills/contract-freeze` before implementation starts. Parallel work on both sides of an unfrozen boundary is the single most common source of integration breakage in this project's history — don't reintroduce it.

### 4. Implement (TDD)

Run `/prp-implement <plan-path>`, which drives `skills/tdd-workflow`: convert every planned behavior into a testable guarantee (RED), implement (GREEN), refactor. Each Requirement's `#### Scenario:` blocks become the test cases directly — don't invent new scenarios that aren't in the spec, and don't skip a scenario that is.

### 5. Verify and close

Before calling anything done, run `skills/definition-of-done-gate`. This includes checking that:

- the spec now matches the code (`spec-miner`'s `enforced:` pointers resolve, `Last verified` is updated with the current commit),
- `code-reviewer` / language-specific reviewer agents have reviewed the diff,
- `verification-loop` (build/type/lint/test) is green,
- any frozen contract this change touches was updated through the contract-freeze protocol, not bypassed.

## Anti-Patterns

- FAIL: Writing code first, spec later. A spec written after the fact records what happened; it doesn't coordinate parallel work or catch design mistakes.
- FAIL: Skipping the plan phase for anything larger than "Small" complexity (see `/prp-plan`'s complexity table) because "it's obvious what to do."
- FAIL: Classifying spec content into type chapters ("Business Rules", "API Contracts") instead of flat `### Requirement:` / `### Invariant:` blocks.
- FAIL: Starting frontend work against an API you expect the backend to build, without a frozen contract (`skills/contract-freeze`) backing the assumption.
- FAIL: Mining every existing module's spec in one sitting "to be thorough." Spec rot starts when specs outpace actual usage — mine one capability at a time, as it's touched.

## Completion Checklist

- [ ] A spec exists for the touched capability (mined or hand-written), in Requirement/Invariant format.
- [ ] The spec was updated (`ADDED`/`MODIFIED`/`REMOVED`) before or alongside the code change, not after.
- [ ] A plan exists for anything beyond a trivial change, and passes the No Prior Knowledge Test.
- [ ] Any crossed service/component boundary went through `skills/contract-freeze`.
- [ ] Implementation followed TDD (`skills/tdd-workflow`); every Scenario has a corresponding test.
- [ ] `skills/definition-of-done-gate` passed before the change is called done.

## Related Skills

- `skills/contract-freeze` — freezing the boundary artifact before parallel implementation
- `skills/definition-of-done-gate` — the final mechanical + review gate
- `skills/tdd-workflow` — test-first implementation discipline (step 4)
- `skills/verification-loop` — build/type/lint/test checks used by the DoD gate
- `agents/spec-miner.md` — extracts Requirement/Invariant specs from existing code
- `agents/planner.md`, `agents/architect.md` — used during the plan phase
- `commands/prp-prd.md`, `commands/prp-plan.md`, `commands/prp-implement.md`, `commands/prp-commit.md`, `commands/prp-pr.md` — the command-level pipeline this skill sequences
