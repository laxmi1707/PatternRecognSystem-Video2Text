# Agent Orchestration

## Available Agents

Located in `agents/` (this repo's curated set — Python + React + AWS RAG scope only):

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| planner | Implementation planning | Complex features, refactoring |
| architect | System design | Architectural decisions, service/data boundaries |
| spec-miner | Extract behavioral specs from existing code | Onboarding a brownfield module to spec-driven dev |
| tdd-guide | Test-driven development | New features, bug fixes |
| code-reviewer | Code review | After writing code |
| security-reviewer | Security analysis | Before commits, before touching auth/secrets/AWS IAM |
| python-reviewer | Python-specific code review | Backend/ingestion/RAG pipeline code |
| fastapi-reviewer | FastAPI-specific review | API route/schema changes |
| react-reviewer | React-specific code review | Frontend component/hook changes |
| react-build-resolver | Fix React/frontend build errors | When the frontend build fails |
| database-reviewer | Schema/migration/query review | Postgres/pgvector schema or migration changes |
| performance-optimizer | Performance analysis | Retrieval latency, ingestion throughput, bundle size |
| code-explorer | Fast codebase search/mapping | Before planning a change in unfamiliar code |
| doc-updater | Documentation | Updating docs after a change |

## Immediate Agent Usage

No user prompt needed:
1. Complex feature requests - Use **planner** agent
2. Code just written/modified - Use **code-reviewer** agent
3. Bug fix or new feature - Use **tdd-guide** agent
4. Architectural decision - Use **architect** agent

## Parallel Task Execution

ALWAYS use parallel Task execution for independent operations:

```markdown
# GOOD: Parallel execution
Launch 3 agents in parallel:
1. Agent 1: Security analysis of auth module
2. Agent 2: Performance review of cache system
3. Agent 3: Type checking of utilities

# BAD: Sequential when unnecessary
First agent 1, then agent 2, then agent 3
```

## Delegation Completion Contract

Applies to every agent at every depth (parent, child, grandchild):

1. **Your final message IS the deliverable.** Never end your turn with "waiting for background agents" — a spawned task is not a completed task. Ending your turn while children are running orphans their results (completed children cannot notify a parent whose turn has ended).
2. **If you delegate, you own collection.** Wait for results, integrate them, then return. Fire-and-forget delegation is forbidden.
3. **Decompose only when the work cannot fit in one context.** Do not re-delegate a task already sized for a single agent — depth is an outcome, not a plan.

> Rationale: observed failure mode — research agents followed "Parallel Task Execution" above, spawned children, and returned "waiting" as their final answer. All children completed successfully but their results were orphaned. The parallel rule without a completion contract produces zombie tasks.

## Multi-Perspective Analysis

For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker
