"""Quick test to reproduce rate plan creation error"""
import traceback
from app.database import SessionLocal
from app.services.rate_plan_service import RatePlanService
from app.models import RatePlanType

db = SessionLocal()
svc = RatePlanService(db)
try:
    plan = svc.create_rate_plan(
        property_id=1,
        room_type_id=None,
        code="TSTZZ3",
        name="Test Plan",
        type=RatePlanType.STANDARD,
        base_rate=100.0,
        created_by="1",
    )
    print(f"OK: id={plan.id}")
except Exception as e:
    with open("_error.txt", "w") as f:
        traceback.print_exc(file=f)
    print("ERROR - see _error.txt")
finally:
    db.close()
