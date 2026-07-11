import sys
import os
from datetime import datetime, date, timedelta

# Add backend to path so imports work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal, init_db
from app.models.property import Property
from app.models.room_type import RoomType
from app.models.room import Room, RoomStatus, ConditionState
from app.models.guest import Guest
from app.models.reservation import Reservation, ReservationStatus, ReservationSource
from app.models.stay import Stay, StayStatus
from app.models.charge import Charge, ChargeType, ChargeStatus
from app.services.analytics.etl import run_etl_job


def seed_db():
    print("Initialize DB...")
    init_db()

    db = SessionLocal()

    try:
        # Check if we already seeded
        existing = db.query(Property).first()
        if existing:
            print("Database already has properties, but we'll add some fresh data.")

        # 1. Create Property
        prop = db.query(Property).filter_by(code="TEST1").first()
        if not prop:
            prop = Property(
                name="Test Resort & Spa",
                code="TEST1",
                address_line1="123 Ocean Drive",
                city="Miami",
                state="FL",
                postal_code="33101",
                country="USA",
                timezone="America/New_York",
                currency="USD",
            )
            db.add(prop)
            db.commit()
            db.refresh(prop)
        print(f"Property ID: {prop.id}")

        # 2. Create Room Type
        rt = db.query(RoomType).filter_by(code="DLX").first()
        if not rt:
            rt = RoomType(
                property_id=prop.id,
                name="Deluxe Ocean View",
                code="DLX",
                description="A nice room",
                capacity=2,
                max_occupancy=4,
                base_price=250.00,
            )
            db.add(rt)
            db.commit()
            db.refresh(rt)

        # 3. Create Room
        room = db.query(Room).filter_by(room_number="101").first()
        if not room:
            room = Room(
                property_id=prop.id,
                room_type_id=rt.id,
                room_number="101",
                floor="1",
                status=RoomStatus.OCCUPIED,
                condition_state=ConditionState.CLEAN,
            )
            db.add(room)
            db.commit()
            db.refresh(room)

        # 4. Create Guest
        guest = db.query(Guest).filter_by(email="john.doe@example.com").first()
        if not guest:
            guest = Guest(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone="+15551234567",
                country="USA",
                loyalty_tier="Gold",
            )
            db.add(guest)
            db.commit()
            db.refresh(guest)

        # 5. Create Reservation
        today = date.today()
        db_res = Reservation(
            property_id=prop.id,
            guest_id=guest.id,
            room_type_id=rt.id,
            confirmation_number=f"CONF{int(datetime.now().timestamp())}",
            status=ReservationStatus.CHECKED_IN,
            check_in_date=today - timedelta(days=2),
            check_out_date=today + timedelta(days=1),
            num_adults=2,
            num_children=0,
            source=ReservationSource.DIRECT,
            total_amount=750.00,
        )
        db.add(db_res)
        db.commit()
        db.refresh(db_res)

        # 6. Create Stay
        db_stay = Stay(
            reservation_id=db_res.id,
            property_id=prop.id,
            guest_id=guest.id,
            room_id=room.id,
            status=StayStatus.CHECKED_IN,
            check_in_date=db_res.check_in_date,
            check_out_date=db_res.check_out_date,
            actual_check_in_time=datetime.utcnow() - timedelta(days=2),
        )
        db.add(db_stay)
        db.commit()
        db.refresh(db_stay)

        # 7. Create Charges
        charge1 = Charge(
            stay_id=db_stay.id,
            property_id=prop.id,
            charge_type=ChargeType.ROOM,
            amount=500.00,
            description="Room Charge - Night 1 & 2",
            status=ChargeStatus.POSTED,
        )
        charge2 = Charge(
            stay_id=db_stay.id,
            property_id=prop.id,
            charge_type=ChargeType.RESTAURANT,
            amount=150.00,
            description="Room Service",
            status=ChargeStatus.POSTED,
        )
        db.add_all([charge1, charge2])
        db.commit()

        print("Successfully seeded PMS database.")

        print("Triggering ETL job...")
        run_etl_job()
        print("ETL job completed.")

    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
