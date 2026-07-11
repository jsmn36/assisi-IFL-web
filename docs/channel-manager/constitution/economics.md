# The Channel Manager Constitution: Economics

**Version:** 1.0
**Status:** BINDING

The CM is an Intent Router and Projection Distributor. It is fully decoupled from economic decision-making.

## Economic Protection Lock

The CM is explicitly **forbidden** from:
- Storing authoritative prices
- Calculating discounts (e.g., 10% off for OTA promotions)
- Applying promotions or coupon codes
- Adjusting availability counts based on arbitrary rules

## Cache Projections
The CM is only permitted to cache pricing via strict TTL bounds (e.g., 1-hour TTL for pricing, 5-minute TTL for availability). If an OTA submits a webhook with a price mutation to complete a booking, the CM MUST forward it as an intent. Any economic discrepancies are handled solely by the sovereignty of the PMS logic.
