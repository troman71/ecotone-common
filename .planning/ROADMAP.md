# Roadmap: ecotone-common

**Project:** Shared pip-installable Python auth utilities for Ecotone Flask apps
**Core Value:** Every Ecotone app uses identical, well-tested auth primitives — no drift, no duplication
**Depth:** Quick (2 phases)
**Created:** 2026-02-10

---

## Overview

This roadmap delivers CI/CD automation and documentation for the ecotone-common package. The package already has 32 passing tests and is in production use by ecotone-impact. These phases make the package maintainable and usable by other teams.

---

## Phase 1: CI/CD Infrastructure

**Goal:** Every commit is automatically tested and linted before merge

**Dependencies:** None (package code and tests already exist)

**Requirements:**
- CICD-01: GitHub Actions workflow runs pytest on push and PR
- CICD-02: Linting enforced in CI (ruff or flake8)
- CICD-03: v0.1.0 git tag created for release tracking

**Success Criteria:**
1. Developer pushes commit to any branch → GitHub Actions runs pytest within 2 minutes
2. Developer opens PR with linting violations → CI blocks merge with clear error messages
3. Developer checks repo tags → sees v0.1.0 with commit SHA and date
4. Package maintainer can identify "what was in production at date X" via git tags

**Plans:** 2 plans

**Status:** ✓ Complete (2026-02-10)

Plans:
- [x] 01-01-PLAN.md — Configure pytest/ruff in pyproject.toml and create GitHub Actions CI workflow
- [x] 01-02-PLAN.md — Create and push annotated v0.1.0 git tag

---

## Phase 2: Documentation

**Goal:** Developers can install and use the package without reading source code

**Dependencies:** Phase 1 (CI validates example code in README)

**Requirements:**
- DOCS-01: README.md with install instructions and usage examples for each module
- DOCS-02: CHANGELOG.md tracking changes per version

**Success Criteria:**
1. New developer reads README → successfully installs package and sends test email within 5 minutes
2. Developer needs to hash password → finds working code example in README
3. Developer needs to generate reset token → finds working code example in README
4. Developer asks "what changed between v0.1.0 and current?" → CHANGELOG.md answers the question

---

## Progress

| Phase | Requirements | Status | Completion |
|-------|--------------|--------|------------|
| 1 - CI/CD Infrastructure | 3 | ✓ Complete | 100% |
| 2 - Documentation | 2 | Not Started | 0% |

**Overall:** 3/5 requirements complete (60%)

---

## Dependencies

```
Phase 1: CI/CD Infrastructure
    ↓
Phase 2: Documentation (CI validates examples)
```

---

## Notes

- Package already has 32 passing tests across all modules
- Package already in production use by ecotone-impact (breaking changes forbidden)
- No research needed — straightforward automation and documentation
- "Quick" depth: 2 phases, each with 1-2 plans expected

---

*Last updated: 2026-02-10 (Phase 1 complete)*
