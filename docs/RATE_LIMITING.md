# Rate Limiting Documentation

## Overview

The Hotel PMS implements comprehensive rate limiting to protect against abuse, ensure fair resource allocation, and maintain system stability.

## Architecture

### Three-Layer Rate Limiting

1. **IP-Based Limits** (Always Applied)
   - Default: 60 requests/minute
   - Prevents anonymous abuse
   - Applied to all requests

2. **User-Based Limits** (Authenticated Users)
   - Tier-based limits
   - More generous than IP limits
   - Tied to user role

3. **Endpoint-Specific Limits** (Critical Endpoints)
   - Stricter limits for expensive operations
   - Prevents targeted abuse
   - Examples: login, exports, bulk operations

### Algorithm

Uses Token Bucket with Sliding Window:
- Implemented via Redis sorted sets
- Precise request counting
- Automatic cleanup of old requests
- Sub-millisecond performance

## Rate Limit Tiers

### IP-Based (Unauthenticated)
- 60 requests/minute
- 1,000 requests/hour
- 10,000 requests/day

### User Tiers

**FREE Tier** (Staff, Maintenance, Housekeeper)
- 100 requests/minute
- 2,000 requests/hour
- 20,000 requests/day

**BASIC Tier** (Front Desk, Accountant)
- 200 requests/minute
- 5,000 requests/hour
- 50,000 requests/day

**PREMIUM Tier** (Manager)
- 500 requests/minute
- 10,000 requests/hour
- 100,000 requests/day

**ADMIN Tier** (Admin)
- 1,000 requests/minute
- 50,000 requests/hour
- 500,000 requests/day

## Endpoint-Specific Limits

### Authentication
- `/auth/login`: 5 requests/minute
- `/auth/register`: 3 requests/hour
- `/auth/reset-password`: 3 requests/hour

### Search
- `/search/global`: 30 requests/minute
- `/search/reservations`: 60 requests/minute

### Exports
- `/reports/export`: 5 requests/5 minutes
- `/analytics/export`: 5 requests/5 minutes
- `/audit/logs/export`: 3 requests/5 minutes

### Bulk Operations
- `/reservations/bulk`: 5 requests/minute

## Response Headers

All responses include rate limit headers:
```
X-RateLimit-Limit: 100          # Maximum requests allowed
X-RateLimit-Remaining: 95       # Requests remaining in window
X-RateLimit-Reset: 1704067200   # Unix timestamp when limit resets
```

## Rate Limit Exceeded (429)

When rate limit is exceeded:

**Status Code**: `429 Too Many Requests`

**Response**:
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "limit": 100,
  "remaining": 0,
  "reset": 1704067200,
  "retry_after": 60
}
```

**Headers**:
```
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067200
```

## Abuse Detection

### Failed Authentication Tracking
- Tracks failed login attempts per IP+email
- Threshold: 5 failed attempts
- Action: Block IP for 1 hour
- Reset: On successful login

### IP Blocking
- Automatic blocking on abuse detection
- Default duration: 1 hour
- Manual blocking via admin API
- Unblock via admin API

### Suspicious Pattern Detection
- Monitors for unusual patterns
- Configurable thresholds
- Automatic flagging
- Admin notification (planned)

## Monitoring

### Admin Endpoints
```
GET  /api/v1/rate-limits/status         # Your current status
GET  /api/v1/rate-limits/config         # Configuration (admin)
POST /api/v1/rate-limits/reset/{user}   # Reset limit (admin)
GET  /api/v1/rate-limits/violations     # Violations (admin)

GET  /api/v1/rate-limit-monitoring/metrics      # Overall metrics
GET  /api/v1/rate-limit-monitoring/blocked-ips  # Blocked IPs
POST /api/v1/rate-limit-monitoring/block-ip     # Block IP
POST /api/v1/rate-limit-monitoring/unblock-ip   # Unblock IP
```

### Metrics
- Total requests processed
- Blocked requests
- Currently blocked IPs
- Top consumers
- Violation history

## Best Practices

### For API Consumers
- **Monitor Headers**: Check rate limit headers in responses
- **Implement Backoff**: Use exponential backoff on 429 responses
- **Respect Retry-After**: Wait specified time before retrying
- **Batch Operations**: Use bulk endpoints where available
- **Cache Responses**: Reduce unnecessary requests

### For Administrators
- **Monitor Violations**: Check violation logs regularly
- **Adjust Limits**: Tune limits based on usage patterns
- **Review Blocked IPs**: Investigate and unblock if needed
- **Track Trends**: Monitor request patterns over time
- **Alert on Abuse**: Set up alerts for suspicious activity

## Configuration

Rate limits configured in `app/core/rate_limit_config.py`:
```python
# Adjust limits
DEFAULT_LIMITS = {
    "per_minute": (60, 60),
    "per_hour": (1000, 3600),
    "per_day": (10000, 86400),
}

# Add endpoint-specific limit
ENDPOINT_LIMITS = {
    "/api/v1/my-endpoint": (30, 60),  # 30 per minute
}
```

## Troubleshooting

### "Rate limit exceeded" errors
- Check current usage: `GET /rate-limits/status`
- Wait for reset (check `X-RateLimit-Reset` header)
- Consider upgrading tier (if applicable)
- Contact admin if limit seems incorrect

### IP blocked
- Check if IP is blocked: Admin panel
- Contact administrator for unblock
- Review activity that triggered block
- Wait for automatic unblock (1 hour default)

### Legitimate high-volume usage
- Contact administrator
- Request tier upgrade
- Consider dedicated API key (future)
- Use bulk endpoints for batch operations

## Implementation Details

### Technology Stack
- **Redis**: Rate limit storage and counting
- **Token Bucket**: Algorithm implementation
- **Sliding Window**: Precise request tracking
- **FastAPI Middleware**: Automatic enforcement

### Performance
- Sub-millisecond rate limit checks
- Minimal overhead on requests
- Automatic cleanup of old data
- Graceful degradation (fail open)

### Reliability
- Redis failure: Fail open (allow requests)
- Multiple Redis instances: Planned
- Distributed rate limiting: Planned
- Backup counters: Planned

## Future Enhancements
- API key-based rate limits
- Custom limits per user
- WebSocket rate limiting
- Distributed rate limiting
- Advanced abuse detection (ML)
- Geographic rate limiting
- Time-of-day limits
- Rate limit analytics dashboard
