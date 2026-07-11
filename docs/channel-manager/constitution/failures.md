# The Channel Manager Constitution: Failures

**Version:** 1.0
**Status:** BINDING

## The Operational Failure Doctrine

The CM is transient middleware. In the event of catastrophic or partial systemic failure, it must enforce the following fail states:

1. **Fail Closed (Outbound):** 
   If the CM is unsure if pricing or availability from the PMS is valid (i.e. if checksum validation fails, TTL expires, or PMS timeouts occur), it MUST stop syncing to OTAs. It must never cache or guess values.
2. **Fail Open (Inbound Intake):**
   When OTAs submit reservation intents, the CM MUST forcefully log and accept the intent payload unconditionally, replying synchronously with a `202 Accepted` to the OTA prior to any processing. Intent validation occurs asymptotically. If downstream systems (worker/PMS) are partitioned, intents sit safely in the `external_events` queue.
3. **Disposable Safety:**
   The CM database assumes it will be deleted every 24 hours. No authoritative resolution relies on the CM state existing. Operations must always pass a `can_rebuild_cm_from_pms()` theoretical parity check.
