# LLM Codebase Context: PMS Hotel Desktop

Generated on: 2026-03-05  
Scope: `C:\Users\akash\pms-hotel-desktop`  
Purpose: high-fidelity context injection for other LLMs.

## 1) What This Repository Is

This repo is a multi-part hotel PMS project with:

- A Python/FastAPI backend in `backend/`
- A React/Vite frontend in `frontend/`
- An Electron shell in `electron/`
- Channel Manager architecture docs and draft code in `docs/channel-manager/` and `backend/app/cm/`
- A nested scaffold/older copy in `pms-hotel-desktop/`

Important: the codebase contains parallel implementations, partial merges, and stale paths. You should treat this as an in-progress monorepo, not a fully consistent production baseline.

## 2) Repository Topology (Active vs Legacy)

## Active Primary Directories

- `backend/`: primary backend code and tests
- `frontend/`: primary frontend code
- `electron/`: desktop wrapper
- `.github/workflows/`: CI definitions
- `docs/channel-manager/constitution/`: architecture contracts for CM behavior

## Legacy/Scaffold Directory

- `pms-hotel-desktop/`: appears to be a scaffold/older copy with typos and incomplete code. It is not used by main runtime paths.

## Generated/Cache/Artifact Directories

- `venv/`, `backend/venv/`
- `backend/__pycache__/`, `backend/.pytest_cache/`, `backend/htmlcov/`
- `frontend/node_modules/`

## 3) Runtime Architecture (Observed)

High-level flow:

1. Electron loads frontend (dev server in dev mode, static build in prod).
2. Frontend calls backend HTTP APIs.
3. Backend exposes:
   - Root endpoints (`/`, `/health`, `/database/info`)
   - Versioned API under `/api/v1` (currently minimal legacy endpoint set)
   - Channel Manager webhook endpoints under `/cm/webhook/*`

Key runtime entrypoint:

- `backend/app/main.py`

## 4) Backend Deep Dive

## 4.1 Backend Boot and App Wiring

File: `backend/app/main.py`

Main behaviors:

- Creates FastAPI app with title `PMS Hotel API`, version `1.0.0`
- Adds CORS for localhost dev origins (3000/5173 on localhost and 127.0.0.1)
- Registers service and validation exception handlers
- Registers a global exception handler for `Exception`
- Includes routers:
  - `api_router` from `app.api.v1.api` at `/api/v1`
  - CM webhook router from `app.cm.api.webhooks` (no extra prefix beyond router prefix)
- Exposes root endpoints:
  - `GET /` -> message/version/docs/database/status
  - `GET /health`
  - `GET /database/info`

Startup behavior:

- Calls `init_db()` at startup
- Also calls `Base.metadata.create_all(bind=engine)` at import time

## 4.2 Database Layer and Critical Split-Brain

There are two DB stacks:

- `backend/app/database.py`
- `backend/app/db/base.py` + `backend/app/db/session.py`

### `app/database.py`

- Loads `.env`
- If `PYTEST_CURRENT_TEST` exists: forces SQLite `sqlite:///./test.db`
- Else if `DATABASE_URL` set: uses PostgreSQL engine settings
- Else: defaults to SQLite file at `~/.pms-hotel/pms.db`
- Exposes:
  - `engine`
  - `SessionLocal`
  - `Base = declarative_base()`
  - `get_db()`
  - `init_db()`
  - `get_db_info()`
  - `get_database_url()`

### `app/db/base.py`

- Defines a different SQLAlchemy base:
  - `class Base(DeclarativeBase)`

### Critical mismatch

Most ORM models inherit from `app.db.base.Base`, but app startup and Alembic env commonly use `app.database.Base`. That means metadata ownership is split and table creation/migration behavior can diverge.

## 4.3 API Layer and Route Reality

### Mounted router

`backend/app/api/v1/api.py` mounts routers from:

- `app.api.v1.endpoints.reservations`
- `app.api.v1.endpoints.guests`
- `app.api.v1.endpoints.rooms`

These are the routes effectively mounted under `/api/v1`.

### Active `/api/v1` routes (mounted)

Guests (`backend/app/api/v1/endpoints/guests.py`):

- `POST /api/v1/guests`
- `GET /api/v1/guests`
- `GET /api/v1/guests/email/{email}`

Reservations (`backend/app/api/v1/endpoints/reservations.py`):

- `POST /api/v1/reservations`
- `GET /api/v1/reservations/{reservation_id}`
- `POST /api/v1/reservations/{reservation_id}/confirm`

Rooms (`backend/app/api/v1/endpoints/rooms.py`):

- `GET /api/v1/rooms/available`
- `POST /api/v1/rooms/{room_id}/clean`

### Richer v1 modules exist but are not mounted

These files implement many additional endpoints but are not wired into `api_router`:

- `backend/app/api/v1/guests.py`
- `backend/app/api/v1/reservations.py`
- `backend/app/api/v1/rooms.py`
- `backend/app/api/v1/stays.py`
- `backend/app/api/v1/operations.py`

Additional issues in richer v1 modules:

- They import dependency providers not defined in `backend/app/api/dependencies.py`:
  - `get_guest_service`, `get_reservation_service`, `get_room_service`, `get_stay_service`, `get_check_in_service`, `get_check_out_service`, `get_current_user`
- `backend/app/api/v1/rooms.py` contains unresolved merge conflict markers (`=======`), causing syntax failure.

### API schema duplication

Two schema sets coexist:

- `backend/app/api/schemas.py` (large, rich schema set)
- `backend/app/api/schemas/operations.py` + `backend/app/api/schemas/__init__.py` (minimal compatibility set)

## 4.4 Domain Model Map

All model files are under `backend/app/models/`.

### `property.py`

- Table: `properties`
- Basic property identity, contact, timezone, currency, status
- Relationship: `rooms`

### `guest.py`

- Table: `guests`
- Rich profile fields: personal, contact, loyalty, privacy, identity
- Includes methods: `full_name`, `age`, `blacklist`, `remove_from_blacklist`, `update_stay_statistics`, `to_dict`
- Defines its own `GuestType` enum (lowercase values)

### `room_type.py`

- Table: `room_types`
- Capacity/pricing metadata and amenities
- Relationships: `property`, `rooms`

### `room.py`

- Table: `rooms`
- Occupancy/condition dual-state fields
- Methods for operational transitions:
  - `is_available`
  - `mark_clean`, `mark_dirty`, `mark_inspected`
  - `take_out_of_order`, `return_to_service`
  - `check_in`, `check_out`

### `rate_plan.py`

- Table: `rate_plans`
- Pricing with weekend support, validity windows, cancellation policy, version/supersede links
- Methods: validity checks, date rate resolution, supersede helper

### `reservation.py`

- Table: `reservations`
- Confirmation, date span, room/room type/rate plan links, occupancy counts, financial totals, status
- Methods:
  - lifecycle helpers: `confirm`, `check_in`, `check_out`, `cancel`, `mark_no_show`
  - pricing helpers: `calculate_nights`, `calculate_total_amount`
  - temporal properties: `is_future`, `is_past`, `is_current`, etc.

### `stay.py`

- Table: `stays`
- Runtime occupancy entity linked to reservation and room
- Tracks check-in/out timestamps, charge totals, housekeeping flags
- Methods include lifecycle transitions and charge addition helpers

### `charge.py`

- Table: `charges`
- Supports charge type/state workflows and payment lifecycle
- Methods: `calculate_total`, `calculate_tax`, `post`, `mark_paid`, `void`, `dispute`, status properties

### `business_day.py`

- Table: `business_days`
- Minimal open/closing status model in current file

### `state_transition_history.py`

- Table: `state_transition_history`
- Generic transition audit record with context serialization helpers and `to_dict`

### `gate_history.py` / `gate_execution_history.py`

- Gate-related execution/audit tables

### Enum duplication and inconsistency risk

Enums are defined in multiple places:

- `models/enums.py`
- `models/guest.py`
- `models/room.py`
- `models/stay.py`
- `models/charge.py`

Values differ (uppercase vs lowercase in some cases), which increases risk of invalid comparisons and status assignment mismatches.

## 4.5 State Machines

Files:

- `backend/app/state_machines/reservation_state_machine.py`
- `backend/app/state_machines/stay_state_machine.py`
- `backend/app/state_machines/state_machines.py` (legacy simplified duplicate)

Active exports in `backend/app/state_machines/__init__.py` point to the dedicated reservation/stay files, not `state_machines.py`.

### ReservationStateMachine (dedicated file)

- Defines valid transitions:
  - `pending -> confirmed/cancelled`
  - `confirmed -> checked_in/cancelled/no_show`
  - `checked_in -> checked_out/cancelled`
- Records all attempts to `StateTransitionHistory`
- Commits during transition
- Convenience methods: `confirm`, `check_in`, `check_out`, `cancel`, `mark_no_show`

### StayStateMachine (dedicated file)

- Defines transitions:
  - `reserved -> checked_in/cancelled`
  - `checked_in -> checked_out`
- Records transition history
- Updates room occupancy/condition on successful check-in/check-out

## 4.6 Gate Framework

Canonical gate framework:

- `backend/app/gates/base_gate.py`
- `backend/app/gates/gate_executor.py`

Canonical gate implementations:

- `check_in_gate.py`
- `check_out_gate.py`
- `date_validation_gate.py`
- `availability_gate.py`
- `occupancy_gate.py`
- `payment_gate.py`
- `rate_validation_gate.py`
- `reservation_cancellation_gate.py`
- `room_assignment_gate.py`

Additional duplicate/stub gate modules also exist:

- `gates.py` (separate gate framework shape)
- `date_gates.py`
- `occupancy_gates.py`
- `payment_gates.py`
- `rate_gates.py`
- `room_gates.py`
- `status_gates.py`
- `workflow_gates.py`

`backend/app/gates/__init__.py` exports a mix of canonical and stub classes, so import intent should be reviewed before relying on wildcard exports.

## 4.7 Service Layer

### `base_service.py`

- Defines:
  - `ServiceError`, `ValidationError`, `NotFoundError`, `BusinessRuleError`
  - Commit/rollback helper
  - `get_or_404`
  - basic audit-style logger

### `guest_service.py`

- Guest creation/update/fetch/search
- Blacklist flows
- Reservation lookup for guest

### `reservation_service.py`

- Supports two create modes:
  - schema object (`res_in`)
  - kwargs filtered into `schemas.ReservationCreate`
- Generates confirmation number and computes nights/total
- Methods: create, confirm, fetch, cancel, modify
- Uses reservation state machine for cancellation

### `room_service.py`

- Room fetch by id/number
- Availability checks with optional date overlap against stays
- Room status transitions and housekeeping summary
- Uses `RoomAssignmentGate` in assignment flow

### `stay_service.py`

- Stay create/check-in/check-out updates
- Charge posting and room charge batch posting

### `check_in_service.py`

Orchestrates check-in:

1. Resolve reservation
2. Resolve or auto-select room
3. Assign room via room service/gate
4. Resolve or create stay
5. Run gate executor (`CheckInGate`, `RoomAssignmentGate`, `PaymentGate`)
6. Transition reservation state
7. Check in stay
8. Optionally post room charges

### `check_out_service.py`

Orchestrates check-out:

1. Resolve stay by stay_id/reservation_id/room_id
2. Compute final bill
3. Run gates (`CheckOutGate`, `PaymentGate`)
4. Optionally settle charges
5. Check out stay and reservation
6. Update guest statistics

### Non-importable services (syntax/indentation issues)

- `backend/app/services/no_show_service.py`
- `backend/app/services/waitlist_service.py`

Observed issues:

- Indentation is broken
- `WaitlistEntry` uses `def init` instead of `def __init__`
- `NoShowService.mark_no_show` calls `sm.no_show(...)` but state machine exposes `mark_no_show(...)`

## 4.8 Channel Manager Module (`backend/app/cm/`)

Status: appears in active imports (main includes CM webhooks) but directory is currently untracked in git status, suggesting in-progress work.

### CM DB isolation

`backend/app/cm/database.py`:

- Uses separate DB URL hardcoded as:
  - `postgresql://user:password@localhost/cm_database`
- Not connected to main PMS DB module

### CM models

- `ExternalEvent` (append-only inbound intent log)
- `ChannelMapping`
- `AvailabilityCache`
- `PricingCache`
- `ChannelSyncLog`
- `IdempotencyRecord`

### CM gates

- `InboundIngestionGate`: schema validation, auth check (`test-key`), checksum/idempotency generation, external_events insert
- `IntentValidationGate`: idempotency guard, channel normalizer application, date sanity check, event status update

### CM API

`backend/app/cm/api/webhooks.py`:

- `POST /cm/webhook/booking.com`
- `POST /cm/webhook/generic`
- Returns `202 Accepted` on successful gate ingestion

### CM worker

`backend/app/cm/worker.py`:

- Uses Redis + RQ worker queue
- Polls pending events and runs IntentValidationGate

Dependency gap:

- Backend requirements do not list `redis` or `rq`, though worker imports them.

## 4.9 Alembic and Migration State

Files:

- `backend/alembic/env.py`
- revisions in `backend/alembic/versions/`

Observed migration chain:

- `1574847754ef_initial_schema`
- `32557f7b55f8_day_3_add_reservation_stay_rateplan_`
- `9fbf27562b2f_day_4_add_statetransitionhistory_table` (empty `pass`)
- `f4d2372225aa_day_5_add_gateexecutionhistory_table` (empty `pass`)
- `2a05cdeeb5da_day_5_add_gateexecutionhistory_table` (empty `pass`)

Important:

- Several migration definitions do not match current model files.
- Multiple revisions are placeholders (`pass`), so DB schema drift is likely.

## 5) Frontend Deep Dive

## 5.1 Frontend Runtime Path

Entrypoints:

- `frontend/src/main.tsx`
- `frontend/src/App.tsx`

Current app shape:

- Simple dashboard showing:
  - backend health
  - database info
  - static day-1 progress checklist
- Uses React Query provider (`frontend/src/queryClient.ts`)
- Uses custom hooks:
  - `useHealthCheck`
  - `useDatabaseInfo`

## 5.2 API Client Split

### Active client in runtime path

`frontend/src/api.ts`:

- axios base URL hardcoded to `http://localhost:8000`
- methods:
  - `healthCheck()` -> `/health`
  - `getDatabaseInfo()` -> `/database-info` (note: backend uses `/database/info`)

### Secondary unused client

`frontend/src/lib/api.ts`:

- richer typed client for guests/reservations/rooms/stays/operations
- expects `VITE_API_URL` or `/api/v1`
- imports from alias `@/types/api`
- currently not used by `App.tsx`

## 5.3 Frontend Type Issues

`frontend/src/types/api.ts` defines many interfaces but does not define:

- `HealthCheckResponse`
- `DatabaseInfo`

Those missing interfaces are imported in hooks:

- `frontend/src/hooks/useHealthCheck.ts`
- `frontend/src/hooks/useDatabaseInfo.ts`

This is a likely TypeScript build error path.

## 5.4 Frontend Config and Duplication

Duplicated config files:

- `tailwind.config.js`
- `tailwind.config.cjs`
- `tailwind_copy.config.js`
- `postcss.config.js`
- `postcss.config.cjs`

Duplicated helper files:

- `src/queryClient.ts` (active)
- `src/lib/queryClient.ts` (unused)
- `src/utils.ts` (active for UI components)
- `src/lib/utils.ts` (unused richer utility set)

Env mismatch:

- `.env`/`.env.example` define `VITE_API_BASE_URL`
- active `src/api.ts` does not consume this variable

## 6) Electron Layer

File: `electron/main.js`

Behavior:

- Creates browser window (1200x800)
- Dev mode: loads `http://localhost:5173` and opens devtools
- Prod mode: loads `../frontend/dist/index.html`
- Handles standard macOS activation/quit behavior

Not implemented:

- backend process orchestration (does not spawn/monitor FastAPI process)
- preload script (commented out)

Build config in `electron/package.json`:

- app id: `com.pmshotel.desktop`
- includes `main.js` + `../frontend/dist/**/*`
- targets:
  - Windows NSIS
  - Linux AppImage/deb
  - mac category metadata

## 7) Tests and Validation Surface

Backend tests are extensive and organized by:

- `tests/test_api/`
- `tests/test_models/`
- `tests/test_gates/`
- `tests/test_state_machines/`
- `tests/test_services/`
- `tests/test_integration/`
- plus top-level tests (`test_main.py`, `test_database.py`, etc.)

Coverage config in `backend/pytest.ini`:

- focuses on `app/gates` and `app/models`
- `--cov-fail-under=80`

Notable test suite characteristics:

- Contains both older and newer expectation sets.
- Example mismatch:
  - tests often expect root response key `name`, but current `app/main.py` returns `message`.
  - tests mention API version `0.1.0`, while current app uses `1.0.0`.
- `test_gate_execution_history.py` is marked skipped.

## 8) CI Workflows

## Backend CI (`.github/workflows/backend.yml`)

- Python `3.12`
- install from `backend/requirements.txt`
- run `pytest --cov=app --cov-report=xml`
- upload coverage to Codecov

## Frontend CI (`.github/workflows/frontend.yml`)

- Node `20.x`
- `npm install`
- `npm run lint`
- `npm run build`

## 9) Static Health Findings (Current Snapshot)

Environment limits during this analysis:

- `pytest` not available in local backend environment
- `npm` not available in local environment

Static compilation check performed:

- Command: `python -m compileall backend/app`

Observed parse failures:

- `backend/app/api/v1/rooms.py` -> syntax error due to merge marker
- `backend/app/services/no_show_service.py` -> indentation error
- `backend/app/services/waitlist_service.py` -> indentation error

These files are currently non-importable.

## 10) Operational Commands (Intended)

From repository docs and code conventions:

Backend:

- `cd backend`
- `python -m venv venv`
- `pip install -r requirements.txt`
- `uvicorn app.main:app --reload`

Frontend:

- `cd frontend`
- `npm install`
- `npm run dev`

Electron:

- `cd electron`
- `npm install`
- `npm start`

## 11) LLM-Oriented Truth Hierarchy

When another LLM reasons about this codebase, use this source-of-truth order:

1. Runtime wiring in `backend/app/main.py` and mounted routers in `backend/app/api/v1/api.py`
2. Active frontend imports reachable from `frontend/src/main.tsx`
3. Service/model/state machine code in `backend/app/`
4. Tests (as intent signals), but verify against runtime wiring due staleness
5. `README.md` and `API.md` (informative but partially stale)

## 12) LLM Injection Block (Copy/Paste Template)

Use the following template when passing context to another LLM:

```text
Project: PMS Hotel Desktop (monorepo)

Active runtime:
- Backend entry: backend/app/main.py
- Mounted API: backend/app/api/v1/api.py -> app/api/v1/endpoints/*
- Frontend entry: frontend/src/main.tsx -> frontend/src/App.tsx
- Electron entry: electron/main.js

Important constraints:
- Codebase has parallel/legacy modules; not all files are mounted.
- Non-importable files currently exist:
  - backend/app/api/v1/rooms.py
  - backend/app/services/no_show_service.py
  - backend/app/services/waitlist_service.py
- DB layer has two Base definitions (app.database.Base vs app.db.base.Base).

Current API reality:
- Root: /, /health, /database/info
- /api/v1 routes currently come from backend/app/api/v1/endpoints/*
  (guests/reservations/rooms minimal subset)

Frontend reality:
- App is a diagnostics dashboard (health + DB info)
- Active API client is frontend/src/api.ts
- It calls /database-info (mismatch with backend /database/info)

When proposing changes:
- Preserve mounted paths and import graph first.
- Flag legacy/unused modules before editing.
- Treat tests as mixed-fidelity; validate against mounted runtime code.
```

## 13) File-Level Classification (High-Value Files)

## Core backend runtime

- `backend/app/main.py`: FastAPI app and router wiring
- `backend/app/database.py`: DB selection and session factory
- `backend/app/api/v1/api.py`: mounted API router aggregator
- `backend/app/api/v1/endpoints/*.py`: currently mounted v1 endpoint handlers
- `backend/app/services/*.py`: domain workflow services
- `backend/app/models/*.py`: SQLAlchemy models
- `backend/app/state_machines/*.py`: transition logic
- `backend/app/gates/*.py`: gate validations

## Backend in-progress or divergent

- `backend/app/api/v1/*.py` (non-endpoints versions): richer APIs not mounted
- `backend/app/api/v1/rooms.py`: broken syntax (merge marker)
- `backend/app/services/no_show_service.py`: broken indentation
- `backend/app/services/waitlist_service.py`: broken indentation
- `backend/app/state_machines/state_machines.py`: duplicate simplified state machine implementation
- `backend/app/gates/gates.py` and several `*_gates.py`: duplicate frameworks/stubs

## Frontend active path

- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/hooks/useHealthCheck.ts`
- `frontend/src/hooks/useDatabaseInfo.ts`
- `frontend/src/api.ts`
- `frontend/src/queryClient.ts`
- `frontend/src/components/ui/Button.tsx`
- `frontend/src/components/ui/Card.tsx`

## Frontend likely unused/legacy

- `frontend/src/lib/*` (richer typed API client and utils, currently not imported by App path)
- `frontend/src/index_copy.css`
- duplicated tailwind/postcss config variants

## Electron

- `electron/main.js`
- `electron/package.json`

## CM docs and implementation

- `docs/channel-manager/constitution/*.md`
- `backend/app/cm/*`

## Legacy scaffold tree

- `pms-hotel-desktop/` (nested directory with incomplete/typo-heavy scaffold code)

---

This document is intentionally explicit about inconsistencies so downstream LLMs can avoid false assumptions.
