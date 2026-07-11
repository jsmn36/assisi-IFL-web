# The Channel Manager Constitution: Observability

**Version:** 1.0
**Status:** BINDING

Every new logic block must adhere to the observability and telemetry framework. Monitoring must track exact metrics to ensure operational compliance.

## Required Metrics Additions
Every new function must wrap its logic using Prometheus Metric calls corresponding to:

### Inbound Metrics
- `cm_webhooks_received_total`
- `cm_webhooks_accepted_total`
- `cm_webhooks_rejected_total`
- `cm_webhooks_duplicate_total`
- `cm_processing_duration_seconds`

### PMS Integration Metrics
- `cm_pms_proposals_sent_total`
- `cm_pms_proposals_accepted_total`
- `cm_pms_proposals_rejected_total`
- `cm_pms_timeouts_total`
- `cm_pms_response_duration_seconds`

### Cache Metrics
- `cm_cache_hits_total`
- `cm_cache_misses_total`
- `cm_cache_size`
- `cm_cache_hit_ratio`

### Business Metrics
- `cm_reservations_created_total`
- `cm_reservations_rejected_total`
- `cm_events_pending_total`
- `cm_booking_e2e_duration_seconds`

Any modification or introduction of a feature without corresponding metric injections constitutes a Failure Fault.
