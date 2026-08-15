# Rules

## Structure

Rules are organized into a **common** layer plus **language-specific** directories, curated down to what this project (video2Text: Python + React + AWS, RAG pipeline) actually uses:

```
rules/
├── common/          # Language-agnostic principles (always applies)
│   ├── agents.md
│   ├── code-review.md
│   ├── coding-style.md
│   ├── development-workflow.md
│   ├── git-workflow.md
│   ├── hooks.md
│   ├── patterns.md
│   ├── performance.md
│   ├── security.md
│   └── testing.md
├── python/          # Backend, ingestion pipeline, RAG service (FastAPI)
├── react/           # Frontend
└── typescript/      # react/*.md reference ../typescript/ — kept as a dependency, not installed standalone
```

- **common/** contains universal principles — no language-specific code examples.
- **Language directories** extend the common rules with framework-specific patterns, tools, and code examples. Each file references its common counterpart with `> This file extends [common/xxx.md](../common/xxx.md) ...`.
- `react/*.md` also references `../typescript/*.md` directly, so `typescript/` is carried along even though this project has no standalone TypeScript-only surface.

There is no AWS-specific rule directory upstream in ECC — AWS conventions for this project (S3, Lambda/Fargate, Bedrock/Transcribe, IAM least-privilege) live in the project-authored skills (`skills/spec-driven-development`, `skills/contract-freeze`, `skills/definition-of-done-gate`) and should be added here as `rules/aws/` if/when enough project-specific AWS guidance accumulates to justify a standalone ruleset (see "Adding a New Language" below).

## Rules vs Skills

- **Rules** define standards, conventions, and checklists that apply broadly (e.g., "80% test coverage", "no hardcoded secrets", "never commit `.env`").
- **Skills** (`skills/` directory) provide deep, actionable reference material for specific tasks (e.g., `python-patterns`, `react-patterns`, `iterative-retrieval`).

Rules tell you _what_ to do; skills tell you _how_ to do it.

## Rule Priority

When language-specific rules and common rules conflict, **language-specific rules take precedence** (specific overrides general) — the same layered pattern as CSS specificity or `.gitignore` precedence.

- `rules/common/` defines universal defaults applicable to all projects.
- `rules/python/`, `rules/react/`, `rules/typescript/` override those defaults where language/framework idioms differ.

### Example

`common/coding-style.md` recommends immutability as a default principle. `python/coding-style.md` and `react/coding-style.md` may override specifics (e.g., idiomatic FastAPI dependency-injection patterns, or React state-update patterns) — see [common/coding-style.md](common/coding-style.md) for the general principle first.

### Common rules with override notes

Rules in `rules/common/` that may be overridden by language-specific files are marked with:

> **Language note**: This rule may be overridden by language-specific rules for languages where this pattern is not idiomatic.

## Installation

This is a project-local rule set (not a global `~/.claude/rules/` install). Claude Code (and compatible tools) should read `rules/` directly from the repo root — no copy step required. If you also want these available as user-level defaults:

```bash
mkdir -p ~/.claude/rules/video2text
cp -r rules/common ~/.claude/rules/video2text/
cp -r rules/python ~/.claude/rules/video2text/
cp -r rules/react ~/.claude/rules/video2text/
cp -r rules/typescript ~/.claude/rules/video2text/
```

> Copy entire directories — do NOT flatten with `/*`. Common and language-specific directories contain files with the same names; flattening breaks the relative `../common/` and `../typescript/` references.

## Adding a New Language or Domain (e.g., `aws/`)

1. Create `rules/aws/`.
2. Add files that extend the common rules: `coding-style.md` (IaC/CDK conventions), `patterns.md` (S3/Lambda/Bedrock usage patterns), `hooks.md` (lint/deploy checks), `security.md` (IAM least-privilege, secrets in Secrets Manager, no long-lived keys).
3. Each file should start with:
   ```
   > This file extends [common/xxx.md](../common/xxx.md) with AWS-specific content.
   ```
4. Reference existing skills where available (none exist upstream for AWS in this template — author one under `skills/` first, per `skills/skill-scout` guidance, before writing the rule).

## Source

Curated from [Everything Claude Code (ECC)](../MANIFEST.md) — see `MANIFEST.md` at the repo root for exactly which files were pinned and why.
