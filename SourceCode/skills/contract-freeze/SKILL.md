---
name: contract-freeze
description: Use before frontend and backend, or backend and RAG-service, work proceeds in parallel on video2Text — or before any change to an existing frozen boundary. Defines the freeze ceremony on top of the imported contract-first skill — how a boundary artifact gets proposed, reviewed, frozen, versioned, and later thawed, so parallel work never drifts from what the other side actually built.
metadata:
  origin: project
  status: active
---

# Contract Freeze (video2Text)

`skills/contract-first` (pinned from ECC, `origin: ECC`) defines *what* a good boundary artifact is and *how* to verify both sides against it. This skill defines *when it gets locked* and *what "locked" means* for this project's three boundaries:

1. **Frontend ↔ Backend API** — OpenAPI (`openapi.yaml`), consumed by the React app.
2. **Backend ↔ RAG service** (if split into a separate process/service) — the retrieval request/response schema and the answer-generation payload shape.
3. **Backend ↔ AWS-managed services** — S3 object key/metadata conventions, any event payloads (e.g., S3 → Lambda → ingestion trigger), IAM-scoped resource contracts.

If the RAG pipeline lives in-process with the backend (no service boundary), boundary 2 doesn't apply — only 1 and 3 do. Confirm which boundaries exist for the current architecture before applying this skill.

## When to Activate

- Frontend and backend implementation is about to start in parallel (per the plan from `skills/spec-driven-development`).
- A new AWS-triggered flow is being designed (e.g., video upload → S3 event → transcription job).
- Someone requests changing a field, enum, or error shape on an already-frozen boundary.
- Two people (or a person and an agent working unattended) will independently implement the two sides of a boundary in the same work session.

Do not freeze a boundary that has exactly one consumer and one implementer working atomically in the same commit — that's premature process for a change with no coordination risk. Use `contract-first`'s own activation guidance to judge this.

## The Freeze Ceremony

### 1. Propose

The person/agent who understands the consumer's job (usually whoever is building the frontend view, or whoever defined the Requirement in the spec) proposes the boundary artifact — following `contract-first`'s "Consumer-First Workflow": describe consumer jobs before designing fields, define the smallest useful contract, make nullability/enums/errors explicit.

### 2. Review

The provider owner reviews the proposed artifact against what's actually buildable — no consumer gets to dictate an implementation detail (e.g., a raw database column) as if it were a contract requirement. Disagreements get resolved by the boundary's named owner (see `contract-first` → "Identify Consumers and Owners"), not by whoever implements first.

### 3. Freeze

Once agreed:

- Commit the artifact (`openapi.yaml` or equivalent) to the repo at its canonical path.
- Tag the commit message: `contract(freeze): <boundary-name> vN`.
- Record the freeze in the relevant spec's Requirement as `<!-- enforced: openapi.yaml#OperationId -->` or equivalent — the contract and the spec must point at each other.
- From this point, **implementation on either side treats the artifact as read-only**. Generate types/mocks from it (`contract-first` step 4); do not hand-edit generated output.

### 4. Build in Parallel

Both sides build against the frozen artifact. The consumer never needs to wait on the provider's implementation; the provider never needs to guess what the consumer expects — both already agreed on it in step 2. This is the entire point of freezing: it converts a sequential dependency into two independent, verifiable tracks.

### 5. Verify Before Integration

Before merging either side: run `contract-first`'s integration checklist (types generate cleanly, consumer fixtures validate against the contract, provider responses validate against the contract, at least one end-to-end happy path passes, no consumer uses an undocumented field). Do not merge on "my tests pass" alone — merge on "both sides pass against the same artifact."

### 6. Thaw (change protocol)

A frozen contract is not immutable forever — it's immutable *without going through this protocol*. To change it:

1. Propose the need and compatibility impact (additive vs. breaking) — same as `contract-first`'s "Contract Change Protocol."
2. Get sign-off from the affected consumer owner(s), not just the provider.
3. Update the artifact, bump the freeze tag (`contract(freeze): <boundary-name> vN+1`), regenerate types/mocks.
4. Re-run verification on both sides before merging the change.

Never change the implementation first and update the contract "to match" afterward — that's the exact drift this skill exists to prevent.

## AWS Boundary Notes

For the S3/event/IAM boundary specifically, the "artifact" is often a JSON Schema for the event payload plus a documented S3 key convention (e.g., `videos/{video_id}/raw.mp4`, `videos/{video_id}/transcript.json`). Freeze these the same way: named owner, committed schema, versioned changes. A silent key-naming change breaks the consumer (the ingestion Lambda/worker) exactly like a silent API field rename breaks a frontend.

## Anti-Patterns

- FAIL: Starting the React view before the API contract is frozen, then treating whatever the backend ships as the contract retroactively.
- FAIL: One person freezing a contract alone without the other side's owner reviewing it — this just moves the guesswork earlier, it doesn't remove it.
- FAIL: Editing a frozen `openapi.yaml` directly to "unblock" a merge without bumping the freeze tag or notifying the other side.
- FAIL: Treating AWS event payloads and S3 key conventions as implementation details instead of contracts, because they're not an HTTP API.

## Completion Checklist

- [ ] Boundary owners identified (consumer + provider) before proposing the artifact.
- [ ] Artifact committed at its canonical path and tagged `contract(freeze): <boundary> vN`.
- [ ] Spec Requirement(s) cross-reference the frozen artifact via `<!-- enforced: -->`.
- [ ] Both sides generated types/mocks from the artifact — no hand-maintained duplicate copies.
- [ ] Verification (types, fixtures, provider responses, happy-path e2e) passed on both sides before merge.
- [ ] Any post-freeze change went through the thaw protocol, not a silent edit.

## Related Skills

- `skills/contract-first` — the underlying mechanics this ceremony wraps (canonical artifact choice, consumer-first design, verification)
- `skills/spec-driven-development` — the pipeline that triggers a contract freeze at the plan → implement handoff
- `skills/api-design` — resource/response/error/pagination/versioning design for the HTTP boundary
- `skills/database-migrations` — for schema changes that back a frozen contract
