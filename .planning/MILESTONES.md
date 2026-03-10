# Project Milestones: ecotone-common

## v0.1 CI/CD & Documentation (Shipped: 2026-02-10)

**Delivered:** CI/CD automation (GitHub Actions with pytest + ruff) and full documentation (README + CHANGELOG) for the shared auth utilities package.

**Phases completed:** 1-2 (4 plans total)

**Key accomplishments:**

- GitHub Actions CI with pytest matrix (Python 3.11/3.12/3.13) and ruff linting
- Annotated v0.1.0 git tag for production release tracking
- README.md with install instructions and working code examples for all 4 modules
- CHANGELOG.md (Keep a Changelog format) with v0.1.0 release entry
- Zero lint violations, 32 passing tests, fully formatted codebase

**Stats:**

- 33 files created/modified
- 593 lines of Python
- 2 phases, 4 plans
- 1 day from start to ship

**Git range:** `b83c40b` -> `4859f83`

**What's next:** v0.2 Robustness (error handling, credential masking, error case tests)

---

## Future: ecotone-assistant (Candidate Package)

**Status:** Not planned; documented as possibility.

**Context:** mn-nonprofit-tool is implementing a contextual AI assistant for the Logic Model Builder: a chat panel where users ask questions and the agent produces structured edits to the page state. The pattern (message + state in, reply + edits out) is generic.

**If extracted to ecotone-common:**
- New package: `ecotone-assistant` (or module in ecotone-common)
- Portable: Chat UI shell, API contract, `AssistantService` (prompt builder, LLM call, response parsing)
- Project-specific: State shape, edit schema, edit interpreter
- Candidate consumers: ecotone-esg, ecotone-impact, better-futures-materials

**Trigger:** Extract when at least one other project needs a similar assistant. Do not implement until then.

---
