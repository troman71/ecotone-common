# Requirements: ecotone-common

**Defined:** 2026-02-10
**Core Value:** Every Ecotone app uses identical, well-tested auth primitives — no drift, no duplication, one place to fix bugs.

## v1 Requirements

### CI/CD

- [ ] **CICD-01**: GitHub Actions workflow runs pytest on push and PR
- [ ] **CICD-02**: Linting enforced in CI (ruff or flake8)
- [ ] **CICD-03**: v0.1.0 git tag created for release tracking

### Documentation

- [ ] **DOCS-01**: README.md with install instructions and usage examples for each module
- [ ] **DOCS-02**: CHANGELOG.md tracking changes per version

## v2 Requirements

### Robustness

- **RBST-01**: Email backends wrap SMTP/SendGrid errors with try/except, return False on failure
- **RBST-02**: `__repr__` on backends masks credentials to prevent log/debugger leaks
- **RBST-03**: Error case tests (SMTP failures, SendGrid non-2xx, connection timeouts)

## Out of Scope

| Feature | Reason |
|---------|--------|
| DB helpers / tenant isolation | App-specific, stays in each app |
| Config loading / env parsing | Apps handle their own config |
| Flask integration (decorators, middleware) | Must remain a plain Python library |
| PyPI publishing | Overkill for 3 internal apps |
| Async support | All consuming apps are sync Flask |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CICD-01 | TBD | Pending |
| CICD-02 | TBD | Pending |
| CICD-03 | TBD | Pending |
| DOCS-01 | TBD | Pending |
| DOCS-02 | TBD | Pending |

**Coverage:**
- v1 requirements: 5 total
- Mapped to phases: 0
- Unmapped: 5

---
*Requirements defined: 2026-02-10*
*Last updated: 2026-02-10 after initial definition*
