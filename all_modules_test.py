"""
Full multi-module API test: PMS, CRM, POS, Accounting, Inventory, Channel Manager, Levagas
Run from: cd backend && python ../all_modules_test.py
"""
import json, requests, sys, uuid

PMS = "http://localhost:8000/api/v1"
CM  = "http://localhost:8000/cm"
LEV = "http://localhost:3000/api"
RESULTS = {}

def req(method, base, path, token=None, json_body=None, params=None, headers_extra=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if headers_extra:
        headers.update(headers_extra)
    r = requests.request(method, base + path, headers=headers, json=json_body,
                         params=params, allow_redirects=True, timeout=10)
    return r

def log(name, r, extra=""):
    ok = r.status_code in (200, 201, 202)
    RESULTS[name] = r.status_code
    mark = "OK " if ok else "FAIL"
    snip = r.text[:120].replace("\n", " ")
    print(f"  [{mark}] {r.status_code} {name}{' | '+extra if extra else ''}")
    if not ok:
        print(f"         ^ {snip}")
    return ok

# ── AUTH ──────────────────────────────────────────────────────────────────────
print("\n=== AUTH ===")
r = req("POST", PMS, "/auth/login", json_body={"username":"admin","password":"admin123"})
log("auth_login", r)
TOKEN = r.json()["access_token"]

# ── PMS CORE ──────────────────────────────────────────────────────────────────
print("\n=== PMS CORE ===")

r = req("GET", PMS, "/properties", TOKEN)
log("list_properties", r)

r = req("GET", PMS, "/room-types", TOKEN)
log("list_room_types", r)

r = req("GET", PMS, "/guests", TOKEN)
log("list_guests", r)

r = req("GET", PMS, "/rates/plans", TOKEN, params={"property_id": 1})
log("list_rate_plans", r)

r = req("GET", PMS, "/reservations", TOKEN)
log("list_reservations", r)

r = req("GET", PMS, "/stays", TOKEN)
log("list_active_stays", r)

r = req("GET", PMS, "/rooms/housekeeping/status/1", TOKEN)
log("housekeeping_status", r)

# Full lifecycle — find a clean vacant room of type 1
r = req("GET", PMS, "/rooms", TOKEN, params={"property_id": 1})
rooms = r.json() if isinstance(r.json(), list) else []
clean_room = next((rm for rm in rooms
                   if rm.get("room_type_id") == 1
                   and rm.get("occupancy_state") == "vacant"
                   and rm.get("condition_state") == "clean"), None)
CLEAN_ROOM_ID = clean_room["id"] if clean_room else 2  # fallback

r = req("POST", PMS, "/reservations", TOKEN, {
    "property_id":1,"guest_id":2,"room_type_id":1,
    "check_in_date":"2026-11-01","check_out_date":"2026-11-03","num_adults":2
})
log("create_reservation", r)
if r.status_code == 201:
    RES_ID = r.json()["id"]
    r = req("POST", PMS, f"/reservations/{RES_ID}/confirm", TOKEN)
    log("confirm_reservation", r)
    r = req("POST", PMS, "/operations/check-in", TOKEN, {"reservation_id": RES_ID, "room_id": CLEAN_ROOM_ID})
    log("check_in", r)
    STAY_ID = None
    if r.status_code == 200:
        STAY_ID = r.json().get("stay_id")
        if not STAY_ID:
            stays = req("GET", PMS, "/stays", TOKEN).json()
            for s in stays:
                if s.get("reservation_id") == RES_ID:
                    STAY_ID = s["id"]; break
        # Add charge
        if STAY_ID:
            r = req("POST", PMS, f"/stays/{STAY_ID}/charges", TOKEN,
                    {"charge_type":"restaurant","description":"Dinner","amount":180})
            log("add_charge", r)
            # Post room charges
            r = req("POST", PMS, f"/stays/{STAY_ID}/post-room-charges", TOKEN)
            log("post_room_charges", r)
            # Check-out
            r = req("POST", PMS, "/operations/check-out", TOKEN, {"stay_id": STAY_ID})
            log("check_out", r)

# Night audit
r = req("POST", PMS, "/operations/night-audit", TOKEN, params={"property_id":1,"audit_date":"2026-04-05"})
log("night_audit", r)

# Analytics
r = req("GET", PMS, "/analytics/occupancy", TOKEN, params={"property_id":1,"start_date":"2026-04-01","end_date":"2026-04-30"})
log("analytics_occupancy", r)
r = req("GET", PMS, "/analytics/revenue", TOKEN, params={"property_id":1,"start_date":"2026-04-01","end_date":"2026-04-30"})
log("analytics_revenue", r)
r = req("GET", PMS, "/analytics/kpis", TOKEN, params={"property_id":1,"start_date":"2026-04-01","end_date":"2026-04-30"})
log("analytics_kpis", r)
r = req("GET", PMS, "/analytics/channels", TOKEN, params={"property_id":1,"start_date":"2026-04-01","end_date":"2026-04-30"})
log("analytics_channels", r)

# Reports
r = req("GET", PMS, "/reports/revenue/summary", TOKEN, params={"property_id":1,"start_date":"2026-04-01","end_date":"2026-04-30"})
log("reports_revenue_summary", r)
r = req("GET", PMS, "/reports/templates", TOKEN)
log("report_templates", r)

# Rates — best-rate is POST with query params
r = req("POST", PMS, "/rates/best-rate", TOKEN,
        params={"property_id":1,"room_type_id":1,"check_in_date":"2026-10-10","check_out_date":"2026-10-12","num_adults":2})
log("rates_best_rate", r)
r = req("GET", PMS, "/rates/calendar", TOKEN, params={"property_id":1,"room_type_id":1,"start_date":"2026-10-01","end_date":"2026-10-30"})
log("rates_calendar", r)
r = req("GET", PMS, "/rates/occupancy", TOKEN, params={"property_id":1,"target_date":"2026-04-06"})
log("rates_occupancy", r)

# Search
r = req("GET", PMS, "/search/global", TOKEN, params={"q":"John","property_id":1})
log("search_global", r)

# ── CRM ───────────────────────────────────────────────────────────────────────
print("\n=== CRM ===")
r = req("GET", PMS, "/crm/guests", TOKEN)
log("crm_guests", r)
r = req("GET", PMS, "/crm/segments", TOKEN)
log("crm_segments", r)
r = req("GET", PMS, "/crm/campaigns", TOKEN)
log("crm_campaigns", r)
# CampaignCreate requires segment_name, not segment_id
r = req("POST", PMS, "/crm/campaigns", TOKEN, {
    "name":"Test Campaign","subject":"Hello","template_id":"welcome","segment_name":"all_guests"
})
log("crm_create_campaign", r)
# Only /crm/analytics/summary exists
r = req("GET", PMS, "/crm/analytics/summary", TOKEN)
log("crm_analytics_summary", r)

# ── POS ───────────────────────────────────────────────────────────────────────
print("\n=== POS ===")
r = req("GET", PMS, "/pos/departments", TOKEN)
log("pos_list_departments", r)
# Use unique name to avoid duplicate on re-run
r = req("POST", PMS, "/pos/departments", TOKEN, {"name":f"Bar-{uuid.uuid4().hex[:4]}","code":f"BAR{uuid.uuid4().hex[:4]}","description":"Hotel bar"})
log("pos_create_department", r)
DEPT_ID = None
if r.status_code in (200,201):
    DEPT_ID = r.json().get("id")

r = req("GET", PMS, "/pos/menu/items", TOKEN)
log("pos_list_menu_items", r)
r = req("POST", PMS, "/pos/categories", TOKEN, {"name":"Drinks","department_id":DEPT_ID or 1})
log("pos_create_category", r)
CAT_ID = r.json().get("id") if r.status_code in (200,201) else 1

r = req("POST", PMS, "/pos/menu/items", TOKEN, {
    "name":f"Gin Tonic {uuid.uuid4().hex[:4]}","price":450,"category_id":CAT_ID,"is_available":True
})
log("pos_create_menu_item", r)
ITEM_ID = r.json().get("id") if r.status_code in (200,201) else None

r = req("GET", PMS, "/pos/tables", TOKEN)
log("pos_list_tables", r)
r = req("POST", PMS, "/pos/tables", TOKEN, {"department_id":DEPT_ID or 1,"table_number":f"B{uuid.uuid4().hex[:3]}","capacity":2})
log("pos_create_table", r)
TABLE_ID = r.json().get("id") if r.status_code in (200,201) else None

r = req("POST", PMS, "/pos/orders", TOKEN, {"table_id":TABLE_ID or 1,"department_id":DEPT_ID or 1})
log("pos_create_order", r)
ORDER_ID = r.json().get("id") if r.status_code in (200,201) else None

if ORDER_ID and ITEM_ID:
    # Body must be a list of items, not a single object
    r = req("POST", PMS, f"/pos/orders/{ORDER_ID}/items", TOKEN,
            [{"item_id":ITEM_ID,"quantity":2,"modifiers":[]}])
    log("pos_add_order_item", r)

# KDS path is /kds/tickets, not /kds-tickets
r = req("GET", PMS, "/pos/kds/tickets", TOKEN)
log("pos_kds_tickets", r)

if ORDER_ID:
    r = req("POST", PMS, "/pos/bills", TOKEN, {"order_id":ORDER_ID})
    log("pos_create_bill", r)
    BILL_ID = r.json().get("id") if r.status_code in (200,201) else None
    if BILL_ID:
        # Path is /pay, payment_method is lowercase
        r = req("POST", PMS, f"/pos/bills/{BILL_ID}/pay", TOKEN,
                {"amount":900,"payment_method":"cash"})
        log("pos_pay_bill", r)

# ── ACCOUNTING ────────────────────────────────────────────────────────────────
print("\n=== ACCOUNTING ===")
r = req("POST", PMS, "/accounting/setup", TOKEN)
log("accounting_setup", r)
r = req("GET", PMS, "/accounting/accounts", TOKEN)
log("accounting_list_accounts", r)

ACCOUNTS = []
if r.status_code == 200:
    ACCOUNTS = r.json()
    if isinstance(ACCOUNTS, dict):
        ACCOUNTS = ACCOUNTS.get("accounts", [])

r = req("GET", PMS, "/accounting/journal-entries", TOKEN)
log("accounting_list_journal_entries", r)

import datetime as dt
if len(ACCOUNTS) >= 2:
    ACC1 = ACCOUNTS[0]["id"]
    ACC2 = ACCOUNTS[1]["id"]
    r = req("POST", PMS, "/accounting/journal-entries", TOKEN, {
        "description":"Test room revenue",
        "entry_date": dt.date.today().isoformat(),
        "lines":[
            {"account_id":ACC1,"debit":5000,"credit":0},
            {"account_id":ACC2,"debit":0,"credit":5000}
        ]
    })
    log("accounting_create_journal_entry", r)
    if r.status_code in (200,201):
        ENTRY_ID = r.json().get("id")
        r = req("POST", PMS, f"/accounting/journal-entries/{ENTRY_ID}/post", TOKEN)
        log("accounting_post_journal_entry", r)

r = req("GET", PMS, "/accounting/reports/balance-sheet", TOKEN, params={"year":2026,"month":4})
log("accounting_balance_sheet", r)
# income-statement → profit-and-loss
r = req("GET", PMS, "/accounting/reports/profit-and-loss", TOKEN, params={"year":2026,"month":4})
log("accounting_profit_and_loss", r)

# ── INVENTORY ─────────────────────────────────────────────────────────────────
print("\n=== INVENTORY ===")
r = req("GET", PMS, "/inventory/vendors", TOKEN)
log("inventory_list_vendors", r)
r = req("POST", PMS, "/inventory/vendors", TOKEN, {
    "name":"Metro Cash & Carry","contact_email":"metro@hotel.com","contact_person":"Raj"
})
log("inventory_create_vendor", r)
VENDOR_ID = r.json().get("id") if r.status_code in (200,201) else 1

r = req("GET", PMS, "/inventory/categories", TOKEN)
log("inventory_list_categories", r)
r = req("POST", PMS, "/inventory/categories", TOKEN, {"name":"Beverages","code":"BEV"})
log("inventory_create_category", r)
CAT_ID = r.json().get("id") if r.status_code in (200,201) else 1

# Use unique SKU to avoid duplicate on re-run
sku = f"WAT-{uuid.uuid4().hex[:6].upper()}"
r = req("POST", PMS, "/inventory/items", TOKEN, {
    "name":"Mineral Water 500ml","sku":sku,"category_id":CAT_ID,
    "vendor_id":VENDOR_ID,"unit":"bottle","current_stock":200,
    "reorder_point":30,"unit_cost":12
})
log("inventory_create_item", r)
ITEM_ID = r.json().get("id") if r.status_code in (200,201) else 1

r = req("GET", PMS, "/inventory/items", TOKEN)
log("inventory_list_items", r)

# quantity_delta not quantity
r = req("POST", PMS, "/inventory/movements", TOKEN, {
    "item_id":ITEM_ID,"movement_type":"ISSUE","quantity_delta":10,"reason":"Room minibar restocking"
})
log("inventory_create_movement", r)

r = req("GET", PMS, "/inventory/alerts", TOKEN)
log("inventory_list_alerts", r)

r = req("GET", PMS, "/inventory/purchase-orders", TOKEN)
log("inventory_list_purchase_orders", r)
# PO body uses 'lines' not 'items'
r = req("POST", PMS, "/inventory/purchase-orders", TOKEN, {
    "vendor_id":VENDOR_ID,"expected_delivery_date":"2026-04-15",
    "notes":"Urgent restocking",
    "lines":[{"item_id":ITEM_ID,"quantity_ordered":100,"unit_cost":11}]
})
log("inventory_create_po", r)

# Reports use /reports/ prefix
r = req("GET", PMS, "/inventory/reports/valuation", TOKEN)
log("inventory_valuation", r)
r = req("GET", PMS, "/inventory/reports/reorder-list", TOKEN)
log("inventory_reorder_report", r)

# ── CHANNEL MANAGER ───────────────────────────────────────────────────────────
print("\n=== CHANNEL MANAGER ===")
r = req("GET", CM, "/admin/mappings", TOKEN)
log("cm_list_mappings", r)

# BookingIntentPayload requires: reservation_id (str), property_id (UUID4),
# room_type (str), check_in, check_out, guests (int), total_price (float), currency (str)
fake_property_uuid = str(uuid.uuid4())
r = req("POST", CM, "/webhooks/booking.com",
        headers_extra={"X-Channel-API-Key":"test-key"},
        json_body={
            "reservation_id": "BDC-TEST-003",
            "property_id": fake_property_uuid,
            "room_type": "DELUXE",
            "check_in": "2026-11-01",
            "check_out": "2026-11-03",
            "guest_name": "OTA Guest",
            "guest_email": "ota@test.com",
            "guests": 2,
            "total_price": 300.0,
            "currency": "INR"
        })
log("cm_booking_webhook", r)

# Note: CM egress expects property_id as UUID4 — architectural mismatch with PMS integer IDs
# These will fail with 422 until the CM is updated to accept integer property IDs
r = req("GET", CM, "/availability", headers_extra={"X-Channel-API-Key":"test-key"},
        params={"property_id": fake_property_uuid, "check_in":"2026-11-01","check_out":"2026-11-05"})
log("cm_availability_egress", r)

r = req("GET", CM, "/pricing", headers_extra={"X-Channel-API-Key":"test-key"},
        params={"property_id": fake_property_uuid, "check_in":"2026-11-01","check_out":"2026-11-05"})
log("cm_pricing_egress", r)

# ── LEVAGAS ───────────────────────────────────────────────────────────────────
print("\n=== LEVAGAS WEBSITE ===")
r = req("POST", LEV, "/availability", json_body={"checkin":"2026-11-10","checkout":"2026-11-12","guests":2})
log("levagas_availability", r)
r = req("POST", LEV, "/submit-booking", json_body={
    "checkin":"2026-11-10","checkout":"2026-11-12","cottageSlug":"garden-retreat",
    "guestFirstName":"Test","guestLastName":"User",
    "guestEmail":"test@test.com","guestPhone":"+91-9999999999",
    "paymentIntentId":"pi_test_123","paymentProvider":"stripe","amount":15000
})
log("levagas_submit_booking", r)
if r.status_code in (200,201,202):
    REF = r.json().get("bookingRef") or r.json().get("reference") or "LV-2026-0001"
    r2 = req("GET", LEV, f"/booking-status/{REF}")
    log("levagas_booking_status", r2)

# ── SUMMARY ───────────────────────────────────────────────────────────────────
passed = sum(1 for v in RESULTS.values() if v in (200,201,202))
failed = [(k,v) for k,v in RESULTS.items() if v not in (200,201,202)]

print("\n" + "="*70)
print(f"TOTAL: {passed}/{len(RESULTS)} passed")
if failed:
    print(f"\nFAILED ({len(failed)}):")
    for k,v in failed:
        print(f"  HTTP {v}  {k}")
