---
trigger: always_on
---

SECTION 2 — REPOSITORY RULESET
Place this file at /GEMINI.md in the repository root. The agent reads it on session start.

2.1 Repository Structure Contract
The agent must maintain this directory structure. Do not reorganize without updating this file.
/
├── GEMINI.md                    ← This file (agent reads on every session start)
├── SESSION_LOG.md               ← Agent writes session progress here
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI application entry point
│   │   ├── database.py          ← Hybrid SQLite/PostgreSQL engine setup
│   │   ├── config.py            ← Pydantic Settings (reads environment)
│   │   ├── models/              ← SQLAlchemy ORM models
│   │   ├── schemas/             ← Pydantic request/response schemas
│   │   ├── services/            ← Business logic services
│   │   ├── gates/               ← Gate Framework (base, executor, coordinator, individual gates)
│   │   │   ├── base.py          ← BaseGate abstract class
│   │   │   ├── executor.py      ← GateExecutor
│   │   │   ├── coordinator.py   ← TransactionCoordinator
│   │   │   └── *.py             ← Individual gates (one file per gate)
│   │   ├── state_machines/      ← State machine definitions and validator
│   │   ├── api/
│   │   │   └── v1/              ← API route handlers
│   │   ├── tasks/               ← APScheduler tasks (SQLite) and Celery tasks (PostgreSQL)
│   │   ├── templates/
│   │   │   └── emails/          ← Jinja2 email templates
│   │   └── utils/               ← Shared utilities (cache patterns, query optimizer, etc.)
│   ├── tests/
│   │   ├── unit/                ← Unit tests (one file per module)
│   │   ├── integration/         ← Integration tests
│   │   ├── performance/         ← Performance benchmarks
│   │   ├── security/            ← Security audit tests
│   │   └── base_test/           ← BASE TEST scenarios (Week 17)
│   ├── alembic/
│   │   └── versions/            ← Migration files (named sequentially)
│   ├── docs/                    ← All project documentation
│   ├── requirements.txt         ← Production dependencies
│   ├── requirements-dev.txt     ← Development dependencies
│   └── pytest.ini               ← pytest configuration
├── frontend/
│   ├── src/
│   │   ├── pages/               ← Top-level page components
│   │   ├── components/          ← Reusable components (organized by domain)
│   │   ├── context/             ← React contexts (auth, theme)
│   │   ├── hooks/               ← Custom hooks (one per domain)
│   │   ├── lib/
│   │   │   ├── api.ts           ← Axios instance and typed API functions
│   │   │   └── queryClient.ts   ← TanStack Query client configuration
│   │   ├── store/               ← Zustand stores
│   │   ├── types/               ← TypeScript type definitions
│   │   └── utils/               ← Frontend utility functions
│   ├── tests/                   ← React Testing Library tests
│   ├── public/                  ← Static assets
│   └── package.json
├── electron/
│   ├── main.js                  ← Electron main process
│   ├── preload.js               ← Context bridge preload script
│   ├── splash.html              ← Splash screen
│   ├── assets/                  ← App icons (all sizes)
│   └── package.json
├── docs/                        ← Project-level documentation
└── SESSION_LOG.md               ← Agent session log
2.2 File Naming Rules

Python files: snake_case.py
Python classes: PascalCase
Python functions: snake_case
TypeScript files: PascalCase.tsx for components, camelCase.ts for utilities
TypeScript interfaces: PascalCase prefixed with I only for legacy compatibility (new code: no prefix)
Test files: test_<module>.py (backend), <Component>.test.tsx (frontend)
Migration files: <NNN>_<description>.py where NNN is zero-padded 3-digit sequence

2.3 Model Registration Rule
Every new SQLAlchemy model must:

Be added to app/models/__init__.py
Have an Alembic migration generated (alembic revision --autogenerate -m "<description>")
Have the migration reviewed (check that upgrade() and downgrade() are both correct)
Have at minimum a creation test and a constraint test

2.4 Gate Registration Rule
Every new Gate must:

Extend BaseGate from app/gates/base.py
Implement all 4 methods: pre_check, execute, post_check, rollback
Be registered in app/gates/__init__.py
Have a test file at tests/unit/gates/test_<gate_name>.py
Tests must include: happy path, pre_check failure, execute failure (triggers rollback), post_check failure

2.5 API Endpoint Registration Rule
Every new router must:

Be imported and included in app/main.py with the correct prefix
Have a corresponding schema file in app/schemas/
Be documented in docs/API_REFERENCE.md
Appear in the OpenAPI spec (verified by calling /docs and checking the endpoint)

2.6 Environment Variables
All environment variables are defined and validated in app/config.py using Pydantic Settings.
Required variables (with defaults where appropriate):
DATABASE_URL          — optional; if absent, SQLite is used
SECRET_KEY            — required; no default
APP_ENV               — default: "development"
SMTP_HOST             — optional; required for email
SMTP_PORT             — default: 587
SMTP_USER             — optional
SMTP_PASSWORD         — optional
REDIS_URL             — optional; only used in PostgreSQL mode
CELERY_BROKER_URL     — optional; only used in PostgreSQL mode
EXPORT_DIR            — default: ~/.pms-hotel/exports/
LOG_LEVEL             — default: INFO
Never access os.environ directly. Always use from app.config import settings.
2.7 Dependency Mode Guard
Any code that requires Redis or Celery must be wrapped in a mode guard:
pythonfrom app.config import settings

if settings.is_postgresql_mode:
    # Redis/Celery code here
else:
    # APScheduler / in-process fallback here
settings.is_postgresql_mode is a @property that returns True when DATABASE_URL is set.
Importing Redis or Celery at the top level of any file that can be loaded in SQLite mode is a forbidden pattern. The agent must not do this.
2.8 State Machine Usage Rule
Before any state transition, the agent must call:
pythonfrom app.state_machines.validator import StateTransitionValidator

validator = StateTransitionValidator()
validator.validate(entity_type="Room", current_state=room.occupancy_status, target_state="OCCUPIED")
# raises InvalidStateTransitionError if transition is not allowed
Bypassing the validator requires routing through ManualOverrideGate with a justification string.
2.9 Testing Standards
Backend tests:

All tests use pytest fixtures for database sessions (never production database)
Test database: SQLite in-memory (sqlite:///:memory:) for unit tests; pytest-postgresql for integration
Fixtures defined in tests/conftest.py
Coverage minimum: 80% per file (enforced with pytest --cov-fail-under=80)

Frontend tests:

All components tested with React Testing Library
Mock API calls using msw (Mock Service Worker)
No snapshot tests (they become maintenance burden)
Test file must be in same directory as component

2.10 Git Discipline

Commits: one commit per day per the session protocol (more is acceptable, fewer is not)
Branch: main is the integration branch; feature branches for experimental work
Tags: v1.0.0-rc1 after Week 17 BASE TEST passes; v1.0.0-final after Week 18 deployment
Never force-push to main
Never commit .env files, *.pyc, __pycache__, node_modules, or build artifacts

2.11 Performance Enforcement Rules
The agent must verify these benchmarks when relevant (run before each week-end commit):
MetricTargetMeasurementAPI response (95th pct)<200mslocust or wrk against local serverDatabase query (simple)<50msSQLAlchemy echo=True + timingNight audit execution<10stime pytest tests/integration/test_night_audit.pyReport generation (≤10k rows)<5sUnit test with timer assertionFrontend initial load<2sLighthouse or vite build --reportBASE TEST total duration<60stime pytest tests/base_test/
If any benchmark fails, the agent must investigate root cause and apply a fix before proceeding.