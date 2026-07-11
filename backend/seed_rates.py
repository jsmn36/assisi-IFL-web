import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models import RatePlan, SeasonalRate, RatePlanType, SeasonType
from decimal import Decimal
from datetime import date

db = SessionLocal()

# Clear old property-wide plans that have no room_type_id
old = db.query(RatePlan).filter(RatePlan.property_id == 1, RatePlan.room_type_id == None).all()
for p in old:
    print(f"Removing property-wide plan: {p.name} (id={p.id})")
    db.delete(p)
db.commit()

# Room types and their realistic rack rates
room_types = [
    (1, "Standard Single",   89.0),
    (2, "Standard Double",  119.0),
    (3, "Deluxe Double",    159.0),
    (4, "Suite",            249.0),
    (5, "Deluxe Sea View",  199.0),
    (6, "Executive Suite",  349.0),
]

plans_created = []
for rt_id, rt_name, rack in room_types:
    # Rack rate (standard)
    rack_code = f"RACK-RT{rt_id}"
    existing = db.query(RatePlan).filter(RatePlan.property_id==1, RatePlan.code==rack_code).first()
    if not existing:
        p = RatePlan(
            property_id=1, room_type_id=rt_id, code=rack_code,
            name=f"{rt_name} — Rack Rate",
            plan_type=RatePlanType.STANDARD,
            base_rate=Decimal(str(rack)),
            min_length_of_stay=1, created_by="1", is_active=True,
        )
        db.add(p); db.flush()
        plans_created.append(p)
        print(f"Created: {p.name}  ${rack}")

    # B&B rate (+20%)
    bb_code = f"BB-RT{rt_id}"
    existing = db.query(RatePlan).filter(RatePlan.property_id==1, RatePlan.code==bb_code).first()
    if not existing:
        bb = round(rack * 1.20, 2)
        p = RatePlan(
            property_id=1, room_type_id=rt_id, code=bb_code,
            name=f"{rt_name} — Bed & Breakfast",
            plan_type=RatePlanType.STANDARD,
            base_rate=Decimal(str(bb)),
            min_length_of_stay=1, created_by="1", is_active=True,
        )
        db.add(p); db.flush()
        plans_created.append(p)
        print(f"Created: {p.name}  ${bb}")

    # Advance purchase (7+ nights, -15%)
    adv_code = f"ADV-RT{rt_id}"
    existing = db.query(RatePlan).filter(RatePlan.property_id==1, RatePlan.code==adv_code).first()
    if not existing:
        adv = round(rack * 0.85, 2)
        p = RatePlan(
            property_id=1, room_type_id=rt_id, code=adv_code,
            name=f"{rt_name} — Advance Purchase",
            plan_type=RatePlanType.PROMOTIONAL,
            base_rate=Decimal(str(adv)),
            min_length_of_stay=3, created_by="1", is_active=True,
        )
        db.add(p); db.flush()
        plans_created.append(p)
        print(f"Created: {p.name}  ${adv}")

db.commit()
print(f"\nTotal plans created: {len(plans_created)}")

# Also set room_type base_rate while we're here
from app.models import RoomType
for rt_id, rt_name, rack in room_types:
    rt = db.query(RoomType).filter(RoomType.id==rt_id).first()
    if rt:
        rt.base_rate = Decimal(str(rack))
db.commit()
print("Room type base rates updated.")
db.close()
