# The Channel Manager Constitution: Data Contracts

**Version:** 1.0
**Status:** BINDING

Data handled by the CM falls under the disposable schema strategy. 

## CM Core Data Schema Types

### external_events
- **Scope**: Append-only log of all inbound intents.
- **Contract**: Events CANNOT be deleted or mutated. `raw_payload` is strictly immutable. Validated via `checksum`.

### channel_mappings
- **Scope**: External reference ID maps pointing to single source PMS ID structures.
- **Contract**: Maps external room type to PMS room type.

### availability_cache & pricing_cache
- **Scope**: Projection caches representing PMS output. 
- **Contract**: Restricted by TTL limits (5 min availability, 1 hour pricing). Assessed by `pms_checksum` / `pms_rate_version`.

### channel_sync_log
- **Scope**: Tracking API transmissions back to external agencies.
- **Contract**: Records request footprint and success state metrics.

### idempotency_records
- **Scope**: Duplicate prevention index.
- **Contract**: Requires unique constraint keys generated via schema (`{channel}:{external_reference}:{timestamp_hash}`). TTL constraints apply.
