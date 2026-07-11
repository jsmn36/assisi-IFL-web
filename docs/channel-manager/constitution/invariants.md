# The Channel Manager Constitution: Invariants

**Version:** 1.0
**Status:** BINDING

These 30 invariants are non-negotiable. The Channel Manager (CM) is infrastructure, not logic. 
The CM has ZERO authority over truth.

## Authority Invariants
- **CM-INV-001**: CM is never a system of record
- **CM-INV-002**: PMS decisions override CM output without exception
- **CM-INV-003**: CM cannot assert availability, price, or reservation truth
- **CM-INV-004**: CM may only propose intents to PMS; it may not mutate core state
- **CM-INV-005**: CM failure must not block PMS operation

## Inventory & Reservation Invariants
- **CM-INV-006**: CM does not own inventory
- **CM-INV-007**: CM may not create, edit, or delete reservations directly
- **CM-INV-008**: CM cannot block, release, or reassign rooms
- **CM-INV-009**: All availability shown by CM is a projection received from PMS
- **CM-INV-010**: CM projections must carry timestamp and source checksum

## Pricing Invariants
- **CM-INV-011**: CM never computes prices
- **CM-INV-012**: CM may only transmit prices supplied by PMS
- **CM-INV-013**: CM cannot adjust prices for commission, rounding, or parity
- **CM-INV-014**: CM must not cache prices beyond declared TTL
- **CM-INV-015**: Any price mutation request from OTA is treated as invalid intent

## Temporal Invariants
- **CM-INV-016**: CM events are strictly ordered by receipt time
- **CM-INV-017**: CM cannot backdate, forward-date, or reorder PMS events
- **CM-INV-018**: CM retries must be idempotent and time-bounded
- **CM-INV-019**: CM holds expire automatically and cannot be extended unilaterally

## Isolation Invariants
- **CM-INV-020**: Each property_id is fully isolated
- **CM-INV-021**: OTA data must never mix across properties
- **CM-INV-022**: CM staging data cannot pollute PMS core tables
- **CM-INV-023**: CM cannot read PMS internal-only state

## Failure Invariants
- **CM-INV-024**: CM downtime must degrade gracefully to PMS-only operation
- **CM-INV-025**: CM must fail closed on outbound sync, open on inbound intake
- **CM-INV-026**: CM must never auto-correct or infer missing PMS responses
- **CM-INV-027**: CM state must be safely discardable without reconciliation loss

## Logging & Audit Invariants
- **CM-INV-028**: All inbound OTA intents are append-only logged
- **CM-INV-029**: CM logs are immutable and non-authoritative
- **CM-INV-030**: CM logs must reference PMS acknowledgment IDs

---
*Note: Any feature request violating these invariants will be rejected with the corresponding CM-INV-* code.*
