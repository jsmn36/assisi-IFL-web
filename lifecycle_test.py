"""Full PMS lifecycle test — run from backend directory with venv activated."""
import json
import requests
import sys

BASE = "http://localhost:8000/api/v1"
RESULTS = {}

def req(method, path, token=None, json_body=None, params=None, follow=True):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.request(method, BASE + path, headers=headers,
                            json=json_body, params=params,
                            allow_redirects=follow)
    return resp

# ─── AUTH ────────────────────────────────────────────────────────────────────
print("\n=== AUTH ===")
r = req("POST", "/auth/login", json_body={"username": "admin", "password": "admin123"})
print(f"Login: {r.status_code}")
TOKEN = r.json()["access_token"]
RESULTS["auth_login"] = r.status_code

# ─── CREATE RESERVATION ──────────────────────────────────────────────────────
print("\n=== CREATE RESERVATION ===")
r = req("POST", "/reservations", TOKEN, {
    "property_id": 1, "guest_id": 1, "room_type_id": 4,
    "check_in_date": "2026-09-10", "check_out_date": "2026-09-12", "num_adults": 2
})
print(f"Status: {r.status_code}  Body: {r.text[:200]}")
RESULTS["create_reservation"] = r.status_code
if r.status_code != 201:
    print("FAILED - stopping lifecycle"); sys.exit(1)
RES_ID = r.json()["id"]
print(f">> Reservation ID: {RES_ID}")

# ─── CONFIRM ─────────────────────────────────────────────────────────────────
print("\n=== CONFIRM RESERVATION ===")
r = req("POST", f"/reservations/{RES_ID}/confirm", TOKEN)
print(f"Status: {r.status_code}  res_status: {r.json().get('status')}")
RESULTS["confirm_reservation"] = r.status_code

# ─── CHECK-IN ────────────────────────────────────────────────────────────────
print("\n=== CHECK-IN ===")
r = req("POST", "/operations/check-in", TOKEN, {"reservation_id": RES_ID, "room_id": 8})
print(f"Status: {r.status_code}")
d = r.json()
print(f"  success={d.get('success')} room={d.get('room_number')} stay_id={d.get('stay_id')}")
RESULTS["check_in"] = r.status_code
STAY_ID = d.get("stay_id")

# Fallback: find stay_id from /stays
if not STAY_ID:
    print("  stay_id missing — fetching from /stays...")
    r2 = req("GET", "/stays", TOKEN)
    RESULTS["get_stays"] = r2.status_code
    stays = r2.json()
    for s in stays:
        if s.get("reservation_id") == RES_ID:
            STAY_ID = s["id"]
            break
    print(f"  Found stay_id={STAY_ID} from /stays (BUG: not in check-in response)")
else:
    print(f"  stay_id={STAY_ID} present in check-in response (FIXED)")

# ─── ADD CHARGES ─────────────────────────────────────────────────────────────
print("\n=== ADD CHARGES ===")
r = req("POST", f"/stays/{STAY_ID}/charges", TOKEN, {
    "charge_type": "RESTAURANT", "description": "Room service", "amount": 350
})
print(f"Status: {r.status_code}  {r.json()}")
RESULTS["add_charge"] = r.status_code

# ─── POST ROOM CHARGES ───────────────────────────────────────────────────────
print("\n=== POST ROOM CHARGES ===")
r = req("POST", f"/stays/{STAY_ID}/post-room-charges", TOKEN)
print(f"Status: {r.status_code}  {r.text[:150]}")
RESULTS["post_room_charges"] = r.status_code

# ─── GET STAY ────────────────────────────────────────────────────────────────
print("\n=== GET STAY ===")
r = req("GET", f"/stays/{STAY_ID}", TOKEN)
print(f"Status: {r.status_code}")
d = r.json()
print(f"  total_charges={d.get('total_charges')} balance_due={d.get('balance_due')} status={d.get('status')}")
RESULTS["get_stay"] = r.status_code

# ─── CHECK-OUT ───────────────────────────────────────────────────────────────
print("\n=== CHECK-OUT ===")
r = req("POST", "/operations/check-out", TOKEN, {"stay_id": STAY_ID})
print(f"Status: {r.status_code}  {r.text[:300]}")
RESULTS["check_out"] = r.status_code

# ─── HOUSEKEEPING STATUS ─────────────────────────────────────────────────────
print("\n=== HOUSEKEEPING STATUS ===")
r = req("GET", "/rooms/housekeeping/status/1", TOKEN)
print(f"Status: {r.status_code}  {r.json()}")
RESULTS["housekeeping_status"] = r.status_code

# ─── NIGHT AUDIT ─────────────────────────────────────────────────────────────
print("\n=== NIGHT AUDIT ===")
r = req("GET", "/operations/night-audit", TOKEN, params={"property_id": 1})
print(f"Status: {r.status_code}  {r.text[:200]}")
RESULTS["night_audit"] = r.status_code

# ─── ANALYTICS ───────────────────────────────────────────────────────────────
print("\n=== ANALYTICS KPIs ===")
r = req("GET", "/analytics/kpis", TOKEN, params={"property_id": 1, "start_date": "2026-04-01", "end_date": "2026-04-30"})
print(f"Status: {r.status_code}  {r.text[:200]}")
RESULTS["analytics_kpis"] = r.status_code

print("\n=== ANALYTICS OCCUPANCY ===")
r = req("GET", "/analytics/occupancy", TOKEN, params={"property_id": 1, "start_date": "2026-04-01", "end_date": "2026-04-30"})
print(f"Status: {r.status_code}  {r.text[:200]}")
RESULTS["analytics_occupancy"] = r.status_code

print("\n=== ANALYTICS REVENUE ===")
r = req("GET", "/analytics/revenue", TOKEN, params={"property_id": 1, "start_date": "2026-04-01", "end_date": "2026-04-30"})
print(f"Status: {r.status_code}  {r.text[:200]}")
RESULTS["analytics_revenue"] = r.status_code

# ─── REPORTS ─────────────────────────────────────────────────────────────────
print("\n=== REPORTS REVENUE SUMMARY ===")
r = req("GET", "/reports/revenue/summary", TOKEN, params={"property_id": 1})
print(f"Status: {r.status_code}  {r.text[:200]}")
RESULTS["reports_revenue"] = r.status_code

print("\n=== REPORT TEMPLATES ===")
r = req("GET", "/reports/templates", TOKEN)
print(f"Status: {r.status_code}  {r.text[:200]}")
RESULTS["report_templates"] = r.status_code

# ─── RATES ───────────────────────────────────────────────────────────────────
print("\n=== RATES BEST RATE ===")
r = req("POST", "/rates/best-rate", TOKEN, {"property_id": 1, "room_type_id": 1, "check_in_date": "2026-09-15", "check_out_date": "2026-09-17"})
print(f"Status: {r.status_code}  {r.text[:200]}")
RESULTS["rates_best_rate"] = r.status_code

print("\n=== RATE CALENDAR ===")
r = req("GET", "/rates/calendar", TOKEN, params={"property_id": 1, "room_type_id": 1})
print(f"Status: {r.status_code}  {r.text[:200]}")
RESULTS["rate_calendar"] = r.status_code

# ─── SEARCH ──────────────────────────────────────────────────────────────────
print("\n=== GLOBAL SEARCH ===")
r = req("GET", "/search", TOKEN, params={"q": "John", "property_id": 1})
print(f"Status: {r.status_code}  {r.text[:200]}")
RESULTS["search"] = r.status_code

# ─── SUMMARY ─────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("RESULTS SUMMARY:")
failed = []
for k, v in RESULTS.items():
    status = "OK" if v in (200, 201) else f"FAIL({v})"
    if v not in (200, 201):
        failed.append(k)
    print(f"  {status:12} {k}")
print(f"\nPassed: {len(RESULTS)-len(failed)}/{len(RESULTS)}")
if failed:
    print(f"Failed: {failed}")
