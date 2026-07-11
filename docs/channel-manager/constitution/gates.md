# The Channel Manager Constitution: Gates

**Version:** 1.0
**Status:** BINDING

## Gate Doctrine
A Gate is a deterministic validator + executor. It enforces all invariants, state machines, and data contracts.
A gate:
- Validates invariants
- Validates state machine legality
- Validates schema and idempotency
- Either commits atomically or rejects entirely

A gate DOES NOT:
- Perform business logic
- Infer outcomes
- Make decisions

## The 8 Gates

### 1. Inbound Ingestion Gate (CM)
- **Applies to**: All incoming webhooks
- **Purpose**: Validate and log external events
- **Enforces**: Schema validity, authentication, and checksum integrity.

### 2. Intent Validation Gate (CM)
- **Applies to**: Parsed booking intents
- **Purpose**: Validate data contract compliance and idempotency
- **Enforces**: Data contract compliance, idempotency key uniqueness, allowed intent types only.

### 3. Forwarding Gate / PMS Proposal Gate (CM)
- **Applies to**: Validated intents
- **Purpose**: Forward proposal to PMS for decision
- **Enforces**: PMS availability communication, timeout bounds, exactly-once forwarding, correlation ID attachment.

### 4. PMS Verdict Gate (CM)
- **Applies to**: PMS responses
- **Purpose**: Validate and record PMS decision
- **Enforces**: Correlation match, verdict authenticity, idempotent resolution.

### 5. Projection Publish Gate (CM)
- **Applies to**: Availability and pricing snapshots from PMS
- **Purpose**: Validate and cache PMS projections
- **Enforces**: PMS checksum validation, TTL assignment, version monotonicity.

### 6. Channel Sync Execution Gate (CM)
- **Applies to**: OTA Egress Pipeline
- **Purpose**: Push availability/pricing to channels
- **Enforces**: Idempotent pushing to OTA API, retry with backoff, sync status logging.

### 7. ReservationConfirmationGate (PMS Maintained)
- **Applies to**: Booking Proposals from CM
- **Purpose**: Authority checks and logic for reservation mutation
- **Enforces**: Date validation, lock availability check, DB writes (atomic COMMIT/ROLLBACK).

### 8. CheckOutGate (PMS Maintained)
- **Applies to**: Front desk interactions
- **Purpose**: Room state mutations
- **Enforces**: Invalidation of caches, publishes room.availability_changed event.
