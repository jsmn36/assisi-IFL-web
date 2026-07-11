# The Channel Manager Constitution: State Machines

**Version:** 1.0
**Status:** BINDING

## 7.1 ExternalEvent State Machine

**States:**
```
pending → processing → validated → forwarding → processed
                   ↓                        ↓
                rejected                 failed
```

**Transitions:**
- `pending → processing`: Background worker picks up event (Intent Validation Gate)
- `processing → validated`: Validation passes (Intent Validation Gate)
- `processing → rejected`: Validation fails (Intent Validation Gate)
- `validated → forwarding`: Sent to PMS (Forwarding Gate)
- `forwarding → processed`: PMS accepts (PMS Verdict Gate)
- `forwarding → rejected`: PMS rejects (PMS Verdict Gate)
- `forwarding → failed`: PMS timeout (Forwarding Gate)
- `failed → forwarding`: Retry (Forwarding Gate)

*Terminal States:* `processed`, `rejected`, `failed` (after max retries).

## 7.2 ChannelSync State Machine

**States:**
```
pending → in_flight → succeeded
              ↓
           failed → abandoned
```

**Transitions:**
- `pending → in_flight`: Start sync job
- `in_flight → succeeded`: OTA API success
- `in_flight → failed`: OTA API failure
- `failed → in_flight`: Retry (with exponential backoff)
- `failed → abandoned`: Max retries exceeded
