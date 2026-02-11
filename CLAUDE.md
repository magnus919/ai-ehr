# CLAUDE.md -- AI Development Process Guide

This file is loaded automatically by Claude Code at the start of every session.
It captures lessons learned from building this project and defines the process
that AI agents should follow to produce high-quality, CI-clean code.

## Project Overview

OpenMedRecord is an open-source EHR system. See [README.md](README.md) for
architecture, setup, and usage.

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
**Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TanStack Query
**Infra:** AWS CDK, Docker Compose, GitHub Actions CI

## Build and Test Commands

```bash
make dev                # Start local dev environment (Docker)
make test               # Run all tests
make test-unit          # Backend unit tests only
make test-frontend      # Frontend tests only
make lint               # Ruff (backend) + ESLint (frontend)
make security-scan      # Bandit + pip-audit + npm audit
make type-check         # TypeScript type checking
```

## Code Conventions

### Python / Backend

- All models use `from __future__ import annotations` and must import
  forward-referenced classes under `TYPE_CHECKING`:
  ```python
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from app.models.patient import Patient
  ```
- Never construct SQL via f-strings with unsanitized input. Use
  `_validate_schema_name()` from `app.core.database` for any value
  interpolated into DDL or SET statements.
- Never use bare `except: pass`. Always log the exception, even when
  the error must be swallowed to avoid breaking a request.
- Default `HOST` is `127.0.0.1`. Only bind `0.0.0.0` via env vars in
  Docker or production configs.
- Use `# nosec B105` (with justification) for Bandit false positives
  on secrets loaded from environment variables.

### TypeScript / Frontend

- Components go in `src/frontend/src/components/<Domain>/`.
- Hooks use TanStack Query with structured query key factories.
- All forms use `react-hook-form` + `zod` for validation.

## AI Development Process

### The Workflow

When generating or modifying code, follow this sequence:

```
Plan  -->  Implement  -->  Validate  -->  Review  -->  Commit
```

Never skip from Implement directly to Commit. The Validate and Review
steps exist because AI-generated code has predictable failure modes
(see below).

### Mandatory Validation Before Commit

After writing code, always run these checks before staging:

1. **Lint:** `make lint` (catches unused imports, undefined names, style)
2. **Security scan:** `make security-scan` (catches hardcoded secrets, injection, risky patterns)
3. **Type check:** `make type-check` (catches TypeScript errors)
4. **Unit tests:** `make test-unit` (catches runtime errors in business logic)

If any check fails, fix the issues and re-run. Do not commit code that
fails these checks.

### Use the Project Agents

This project defines five custom agents in `.claude/agents/`. Use them
as a quality gate after implementation, before committing.

| Agent | Role | When to use |
|---|---|---|
| `code-reviewer` | Senior code reviewer | After any non-trivial code changes |
| `qa-engineer` | QA validation (lint, test, scan) | Before every commit -- catches CI failures locally |
| `security-engineer` | Security and HIPAA compliance | After changes to auth, encryption, PHI handling, infra |
| `tech-lead` | Architecture and cross-file consistency | After multi-file changes or new patterns |
| `devops-engineer` | Build/deploy infrastructure validation | After changes to Docker, CI, CDK, scripts, Makefile |

**Minimum for every commit:** Run `qa-engineer` to validate lint/test/scan.
**For significant changes:** Also run `code-reviewer` and the relevant
specialist agent (`security-engineer`, `tech-lead`, or `devops-engineer`).

### Common AI Code Generation Pitfalls

These are patterns that AI agents (including Claude) frequently get wrong.
Pay extra attention to these areas during review:

1. **Unused imports** -- AI generates imports for things it planned to use
   but didn't. Run `ruff check` to catch F401.

2. **Forward reference types** -- When using `from __future__ import annotations`,
   type-only references (like SQLAlchemy `Mapped["X"]`) need `TYPE_CHECKING`
   imports. AI often forgets this. Run `ruff check` to catch F821.

3. **Cross-file consistency** -- When the same pattern appears in many files
   (e.g., 8 ORM models), AI may get it right in some and wrong in others.
   After fixing a bug in one file, grep for the same pattern everywhere.

4. **SQL injection in dynamic SQL** -- AI freely uses f-strings for SQL.
   Any user-influenced value in SQL must be parameterized or validated.

5. **Silent exception swallowing** -- AI writes `except Exception: pass`
   when told "don't break the main flow." Always log the exception.

6. **Hardcoded development defaults** -- AI sets `0.0.0.0`, weak secrets,
   and permissive CORS as defaults. Defaults should be secure; development
   overrides should come from env vars or `.env` files.

7. **Missing file permissions** -- AI creates shell scripts without execute
   bits. Run `chmod +x` on `.sh` files.

8. **Test artifacts** -- AI writes test files but may not verify they
   actually run. Always execute the test suite at least once.

## File Structure

Key paths for navigation:

```
docs/requirements/PRD.md              # Product requirements
docs/architecture/ARCHITECTURE.md     # System architecture
docs/compliance/COMPLIANCE.md         # HIPAA/SOC2/HITRUST controls
src/backend/app/core/                 # Config, DB, security, audit
src/backend/app/models/               # SQLAlchemy ORM models
src/backend/app/api/routes/           # FastAPI route handlers
src/backend/app/services/             # Business logic layer
src/backend/app/utils/                # Encryption, validators
src/frontend/src/components/          # React components by domain
src/frontend/src/hooks/               # TanStack Query hooks
src/frontend/src/store/               # Zustand state stores
infrastructure/cdk/stacks/            # AWS CDK stacks
infrastructure/docker/                # Docker Compose configs
.github/workflows/                    # CI/CD pipelines
```
