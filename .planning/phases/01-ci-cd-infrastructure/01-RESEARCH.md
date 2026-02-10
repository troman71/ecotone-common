# Phase 01: CI/CD Infrastructure - Research

**Researched:** 2026-02-10
**Domain:** GitHub Actions, Python Testing, Code Quality
**Confidence:** HIGH

## Summary

Phase 01 focuses on implementing continuous integration for the ecotone-common Python package. The research examined current best practices for Python CI/CD in 2026, focusing on GitHub Actions workflows, linting tools, testing frameworks, and version management.

Key findings indicate that **Ruff has emerged as the dominant linting solution** for Python in 2026, offering 50-150x performance improvements over Flake8 while implementing 800+ lint rules natively. For testing, **pytest remains the standard** with mature GitHub Actions integration. Version management should follow **semantic versioning with annotated Git tags** starting at v0.1.0 for initial release.

The standard approach is a single GitHub Actions workflow that runs on push and pull_request events, testing with pytest and enforcing linting with Ruff, all configured through pyproject.toml.

**Primary recommendation:** Use GitHub Actions with Ruff for linting and pytest for testing, configured entirely through pyproject.toml to align with modern Python packaging standards.

## Standard Stack

The established tools for Python CI/CD in 2026:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| GitHub Actions | N/A | CI/CD orchestration | Native GitHub integration, free for public repos, mature Python support |
| pytest | 7.0+ | Test framework | De facto standard for Python testing, excellent plugin ecosystem |
| Ruff | Latest | Linting & formatting | 50-150x faster than Flake8, 800+ rules, replaces multiple tools |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest-cov | Latest | Coverage reporting | When tracking code coverage metrics (optional for v0.1.0) |
| actions/setup-python | v5 | Python environment setup | All Python workflows |
| astral-sh/ruff-action | v3 | Ruff integration | Simplified Ruff execution in workflows |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Ruff | Flake8 + Black + isort | 150x slower, more configuration files, but supports custom plugins |
| GitHub Actions | GitLab CI, CircleCI | Better if not using GitHub, but adds complexity for GitHub repos |
| pytest | unittest | Stdlib-only, but less expressive and harder to extend |

**Installation:**
```bash
pip install ruff pytest pytest-cov
```

## Architecture Patterns

### Recommended Project Structure
```
ecotone-common/
├── .github/
│   └── workflows/
│       └── ci.yml           # Single workflow for all checks
├── src/
│   └── ecotone_common/      # Source code
├── tests/                   # Test files (test_*.py)
├── pyproject.toml           # All configuration
└── .gitignore
```

### Pattern 1: Single Unified Workflow

**What:** One GitHub Actions workflow file that runs all quality checks (linting + testing) on every push and PR.

**When to use:** Small to medium packages where checks complete in < 5 minutes (ecotone-common fits this perfectly).

**Example:**
```yaml
# Source: https://docs.github.com/actions/guides/building-and-testing-python
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest ruff

      - name: Lint with ruff
        run: ruff check .

      - name: Test with pytest
        run: pytest tests/
```

### Pattern 2: pyproject.toml Centralized Configuration

**What:** All tool configuration (build, pytest, ruff) lives in pyproject.toml, eliminating separate config files.

**When to use:** Always for Python 3.11+ projects in 2026 (modern packaging standard).

**Example:**
```toml
# Source: https://docs.astral.sh/ruff/configuration/
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ecotone-common"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
addopts = ["--import-mode=importlib"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "B"]
ignore = ["E501"]  # Line too long (let formatter handle it)
```

### Pattern 3: Matrix Testing for Multiple Python Versions

**What:** Test the same codebase against multiple Python versions in parallel using GitHub Actions matrix strategy.

**When to use:** When supporting multiple Python versions (ecotone-common supports 3.11+).

**Example:**
```yaml
# Source: https://codefresh.io/learn/github-actions/github-actions-matrix/
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
  fail-fast: false  # Continue testing other versions if one fails

steps:
  - uses: actions/setup-python@v5
    with:
      python-version: ${{ matrix.python-version }}
```

### Pattern 4: Optional Dependencies Testing

**What:** Install and test with optional dependencies (like sendgrid) to ensure they work when users install extras.

**When to use:** When package defines optional-dependencies in pyproject.toml.

**Example:**
```yaml
# Source: https://til.simonwillison.net/github-actions/running-tests-against-multiple-verisons-of-dependencies
strategy:
  matrix:
    extras: ["", "[sendgrid]", "[all]"]

steps:
  - name: Install with extras
    run: pip install -e .${{ matrix.extras }}
```

### Anti-Patterns to Avoid

- **Don't use setup.py for configuration:** It's deprecated in 2026; migrate everything to pyproject.toml
- **Don't run linting and testing in separate workflows:** Creates unnecessary delay and complexity for small packages
- **Don't use actions/checkout@v2:** It's deprecated; use v4+
- **Don't forget cache: 'pip':** Doubles workflow runtime without pip caching
- **Don't use python setup.py test:** It's deprecated and bypasses pip security

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Python linting | Custom AST parser + style rules | Ruff | 800+ rules already implemented, actively maintained, 150x faster |
| Test discovery | Custom test finder | pytest discovery | Handles edge cases (import paths, fixtures, parametrization) |
| Coverage reporting | Custom code analysis | pytest-cov | Integrates with pytest, handles multiprocessing, mature |
| Git version tagging | Custom versioning script | Manual annotated tags + GitHub releases | Semantic versioning is standard, simple is better |
| CI/CD setup | Custom bash scripts | GitHub Actions | Free, integrated, extensive marketplace, yaml config |
| Branch protection | Manual PR review only | GitHub required status checks | Enforces checks before merge, configurable |

**Key insight:** Python tooling ecosystem has consolidated around standard solutions. Custom solutions add maintenance burden and miss edge cases that took years to discover and fix in standard tools.

## Common Pitfalls

### Pitfall 1: Ruff Rule Code Confusion

**What goes wrong:** Developers expect Flake8 rule codes (like `I252`) but Ruff uses different codes (like `TID252`) for the same rules from plugins.

**Why it happens:** Ruff reimplements plugins natively in Rust and uses unique prefixes to avoid conflicts and allow toggling entire plugin sets.

**How to avoid:**
- Check Ruff's rule documentation when migrating from Flake8 plugins
- Use `ruff check --select TID` to toggle entire plugin families
- Run `ruff check --show-source` to see which rule triggered

**Warning signs:**
- Error codes not found in Ruff docs
- Rules not firing when expected

**Source:** [Ruff FAQ](https://docs.astral.sh/ruff/faq/)

### Pitfall 2: Status Checks Not Appearing in Branch Protection

**What goes wrong:** After creating a GitHub Actions workflow, the checks don't appear in the branch protection "required status checks" dropdown.

**Why it happens:** GitHub only shows checks that have **actually run on the target branch** via a push event. Workflows that only run on pull_request events won't populate the dropdown.

**How to avoid:**
- Configure workflows to run on both push and pull_request
- Push a commit to the main branch to trigger the workflow
- Wait for workflow to complete before configuring branch protection
- Check workflow ran within last 7 days (GitHub requirement)

**Warning signs:**
- Empty dropdown in branch protection settings
- Workflow shows in Actions tab but not in protection settings

**Source:** [GitHub Discussions #26668](https://github.com/orgs/community/discussions/26668)

### Pitfall 3: pytest Import Mode for src Layout

**What goes wrong:** Tests fail with import errors when run in CI despite passing locally, or vice versa.

**Why it happens:** pytest's default import mode appends directories to sys.path, which can cause inconsistent behavior between development (with editable install) and CI (without).

**How to avoid:**
- Set `addopts = ["--import-mode=importlib"]` in pyproject.toml
- Add `pythonpath = ["src"]` to [tool.pytest.ini_options]
- Always install package with `pip install -e .` in CI
- Use src/ layout instead of flat layout

**Warning signs:**
- Tests pass locally but fail in CI
- Import errors for project modules
- "Module not found" errors

**Source:** [pytest Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)

### Pitfall 4: Ruff E501 (Line Too Long) with Black/Ruff Formatter

**What goes wrong:** Ruff's linter reports E501 violations even after running the Ruff formatter, causing CI to fail.

**Why it happens:** Ruff's formatter makes best-effort attempts to format lines but won't break long strings or comments. The linter then flags these as violations.

**How to avoid:**
- Add `ignore = ["E501"]` to [tool.ruff.lint] in pyproject.toml
- Set consistent `line-length` in [tool.ruff] (default 88, can customize)
- Let formatter handle line length; don't enforce with linter

**Warning signs:**
- CI fails after formatting with "line too long"
- E501 errors on strings or comments

**Source:** [Ruff FAQ](https://docs.astral.sh/ruff/faq/)

### Pitfall 5: Semantic Versioning Immutability Violations

**What goes wrong:** Team moves a git tag to point to a different commit, or releases v0.1.0 then realizes it should have been v0.2.0.

**Why it happens:** Git allows force-pushing tags, and developers don't understand semantic versioning's immutability requirement.

**How to avoid:**
- Use annotated tags (not lightweight): `git tag -a v0.1.0 -m "Release v0.1.0"`
- Never move or delete tags after pushing to remote
- If mistake made, release a new patch version (v0.1.1) instead
- Document that tags are immutable in CONTRIBUTING.md

**Warning signs:**
- Same version number points to different commits for different users
- Confusion about "what was in production at X date"

**Source:** [Semantic Versioning Spec](https://semver.org/)

### Pitfall 6: Optional Dependencies Not Tested

**What goes wrong:** Package releases with working core but broken optional features (e.g., sendgrid integration fails when installed).

**Why it happens:** CI only tests base dependencies, not optional extras, so code using optional imports never runs in CI.

**How to avoid:**
- Add matrix strategy testing with and without extras
- Install with `pip install -e .[sendgrid]` in separate job
- Use `pytest.importorskip("sendgrid")` for optional feature tests
- Document which tests require optional dependencies

**Warning signs:**
- Users report errors with optional features
- Tests skip without explanation
- Import errors only with extras installed

**Source:** [Python Packaging Guide](https://www.pyopensci.org/python-package-guide/package-structure-code/declare-dependencies.html)

## Code Examples

Verified patterns from official sources:

### Complete GitHub Actions Workflow
```yaml
# Source: https://docs.github.com/actions/guides/building-and-testing-python
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff
      - name: Lint with ruff
        run: |
          ruff check .
          ruff format --check .

  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
          pip install pytest

      - name: Test with pytest
        run: pytest tests/
```

### Complete pyproject.toml Configuration
```toml
# Source: https://docs.astral.sh/ruff/configuration/
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ecotone-common"
version = "0.1.0"
description = "Shared utilities for Ecotone Flask applications"
requires-python = ">=3.11"
dependencies = [
    "bcrypt>=4.0",
    "itsdangerous>=2.0",
]

[project.optional-dependencies]
sendgrid = ["sendgrid>=6.0"]
all = ["sendgrid>=6.0"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
addopts = ["--import-mode=importlib"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = [
    "E4",   # pycodestyle errors (import-related)
    "E7",   # pycodestyle errors (statement-related)
    "E9",   # pycodestyle errors (syntax)
    "F",    # Pyflakes
    "B",    # flake8-bugbear
]
ignore = [
    "E501",  # Line too long (handled by formatter)
]
```

### Creating Semantic Version Tag
```bash
# Source: https://semver.org/
# Create annotated tag (includes metadata: author, date, message)
git tag -a v0.1.0 -m "Release v0.1.0: Initial CI/CD infrastructure

- GitHub Actions workflow for pytest
- Ruff linting enforcement
- Python 3.11+ support"

# Push tag to remote
git push origin v0.1.0

# Verify tag
git show v0.1.0
```

### pytest with src Layout
```bash
# Source: https://docs.pytest.org/en/stable/explanation/goodpractices.html

# Install in editable mode (development)
pip install -e .

# Run tests with importlib mode
pytest tests/

# Run specific test file
pytest tests/test_passwords.py

# Run with verbose output
pytest -v tests/

# Run with coverage (if pytest-cov installed)
pytest --cov=ecotone_common tests/
```

### Ruff Usage Examples
```bash
# Source: https://docs.astral.sh/ruff/

# Check all files
ruff check .

# Check and auto-fix issues
ruff check --fix .

# Check formatting
ruff format --check .

# Format files
ruff format .

# Show source of violations
ruff check --show-source .

# Check specific rule family
ruff check --select F .
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flake8 + Black + isort (3 tools) | Ruff (1 tool) | 2023-2024 | 50-150x faster linting, single config file |
| setup.py for config | pyproject.toml for everything | 2021-2022 (PEP 621) | Standardized config, no more setup.py |
| unittest framework | pytest framework | 2015+ adoption | Better fixtures, parametrization, plugins |
| actions/checkout@v2 | actions/checkout@v4 | 2023 | Security, performance improvements |
| Manual pip install | setup-python cache: 'pip' | 2021 | 50% faster workflow runs |
| Python 3.7-3.10 | Python 3.11-3.13 | 2024-2026 | Performance, better error messages |

**Deprecated/outdated:**
- **python setup.py test**: Deprecated by setuptools, bypasses pip security - use pytest directly
- **setup.cfg for tool config**: Replaced by pyproject.toml (PEP 621)
- **Travis CI**: Still exists but GitHub Actions dominates for GitHub repos
- **Flake8 for new projects**: Ruff is now the recommended choice per Python community
- **unittest for new projects**: pytest is the ecosystem standard

## Open Questions

Things that couldn't be fully resolved:

1. **Coverage Reporting in v0.1.0**
   - What we know: pytest-cov exists, integrates with GitHub Actions, can comment on PRs
   - What's unclear: Is coverage tracking necessary for v0.1.0 or can it wait for Phase 02?
   - Recommendation: Skip for v0.1.0 - requirement CICD-01/02/03 don't mention coverage, add in future phase

2. **Python 3.13 Testing**
   - What we know: Python 3.13 is available, setup-python@v5 supports it
   - What's unclear: Are all dependencies (bcrypt, itsdangerous) compatible with 3.13?
   - Recommendation: Test 3.11, 3.12, 3.13 in matrix; if 3.13 fails, drop it and note in README

3. **Ruff Formatter vs Black**
   - What we know: Ruff includes formatter that's Black-compatible
   - What's unclear: Should we enforce formatting in CI or just linting?
   - Recommendation: Add `ruff format --check` to CI to enforce consistent formatting

4. **Branch Protection Timing**
   - What we know: Status checks must run on branch before appearing in protection settings
   - What's unclear: Should we configure branch protection as part of CICD-02 or separate manual step?
   - Recommendation: Include GitHub UI instructions in task verification but don't automate (requires admin access)

5. **Testing Optional Dependencies**
   - What we know: Package has optional sendgrid dependency
   - What's unclear: Do we need to test with/without sendgrid in matrix or just trust unit tests?
   - Recommendation: Start without matrix for extras; add if users report bugs with optional deps

## Sources

### Primary (HIGH confidence)
- [GitHub Docs: Building and Testing Python](https://docs.github.com/actions/guides/building-and-testing-python) - Official GitHub Actions for Python
- [Ruff Documentation](https://docs.astral.sh/ruff/) - Official Ruff docs, configuration, FAQ
- [pytest Documentation: Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) - Official pytest src layout guide
- [Semantic Versioning Spec](https://semver.org/) - Official semver specification
- [GitHub Docs: About Protected Branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) - Status check configuration

### Secondary (MEDIUM confidence)
- [Ruff vs Flake8 Performance](https://trunk.io/learn/comparing-ruff-flake8-and-pylint-linting-speed) - Independent benchmark comparison
- [GitHub Actions Matrix Strategy](https://codefresh.io/learn/github-actions/github-actions-matrix/) - Comprehensive tutorial
- [Python Packaging Guide: Dependencies](https://www.pyopensci.org/python-package-guide/package-structure-code/declare-dependencies.html) - PyOpenSci best practices
- [Migrating to Ruff from Flake8](https://mitches-got-glitches.github.io/developer_blog/2024/03/25/migrating-to-ruff-from-black-and-flake8/) - Real migration experience
- [Git Semantic Versioning](https://www.gitkraken.com/gitkon/semantic-versioning-git-tags) - Practical guide to semver with git

### Tertiary (LOW confidence)
- [Medium: Pytest with GitHub Actions](https://pytest-with-eric.com/integrations/pytest-github-actions/) - Community tutorial (good patterns but not authoritative)
- [Medium: Ruff Migration](https://medium.com/@zigtecx/why-you-should-replace-flake8-black-and-isort-with-ruff-the-ultimate-python-code-quality-tool-a9372d1ddc1e) - Opinion piece (validates findings but not primary source)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Ruff, pytest, GitHub Actions are clearly dominant in 2026 per official docs and ecosystem adoption
- Architecture: HIGH - Patterns verified against official GitHub and pytest documentation
- Pitfalls: HIGH - Sourced from official FAQs, GitHub issues, and documentation

**Research date:** 2026-02-10
**Valid until:** 2026-04-10 (60 days - stable ecosystem, Python tooling changes slowly except for Ruff which is fast-moving)

**Key assumptions:**
- GitHub repository is already set up (ecotone-common exists)
- Developer has GitHub write access (can create workflows)
- Repository is private (GH_PAT exists per PROJECT.md)
- Tests already pass locally (32 tests passing per PROJECT.md)
- Python 3.11+ is target (per pyproject.toml)
