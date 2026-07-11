import pytest
from app.models import Property, RoomType, Room, Guest, BusinessDay
from app.models import OccupancyState, ConditionState, GuestType, DayStatus
from decimal import Decimal
from datetime import date
from app.database import SessionLocal, Base, engine


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_complete_hotel_setup(test_db):
    """
    Integration test: Set up a complete hotel with property, room types,
    rooms, guests, and business day
    """

    # 1. Create Property
    property = Property(
        name="Grand Test Hotel",
        code="GRAND001",
        address_line1="123 Luxury Lane",
        city="Miami",
        state="FL",
        country="USA",
        postal_code="33101",
        phone="+1-305-555-0100",
        email="info@grandtesthotel.com",
        timezone="America/New_York",
        currency="USD",
    )

    test_db.add(property)
    test_db.commit()
    test_db.refresh(property)

    assert property.id is not None

    # 2. Create Room Types
    standard_type = RoomType(
        property_id=property.id,
        code="STD",
        name="Standard Room",
        description="Comfortable standard room with city view",
        max_occupancy=2,
        max_adults=2,
        max_children=1,
        base_price=Decimal("129.99"),
        bed_type="Queen",
        num_beds=1,
        size_sqft=300,
    )

    deluxe_type = RoomType(
        property_id=property.id,
        code="DLX",
        name="Deluxe Room",
        description="Spacious deluxe room with ocean view",
        max_occupancy=3,
        max_adults=2,
        max_children=2,
        base_price=Decimal("199.99"),
        bed_type="King",
        num_beds=1,
        size_sqft=450,
    )

    suite_type = RoomType(
        property_id=property.id,
        code="STE",
        name="Executive Suite",
        description="Luxurious suite with living area",
        max_occupancy=4,
        max_adults=3,
        max_children=2,
        base_price=Decimal("349.99"),
        bed_type="King",
        num_beds=2,
        size_sqft=800,
    )

    test_db.add_all([standard_type, deluxe_type, suite_type])
    test_db.commit()

    # 3. Create Rooms
    rooms = []

    for i in range(1, 6):
        rooms.append(
            Room(
                property_id=property.id,
                room_type_id=standard_type.id,
                room_number=f"10{i}",
                floor=1,
                building="Main",
            )
        )

    for i in range(1, 4):
        rooms.append(
            Room(
                property_id=property.id,
                room_type_id=deluxe_type.id,
                room_number=f"20{i}",
                floor=2,
                building="Main",
            )
        )

    for i in range(1, 3):
        rooms.append(
            Room(
                property_id=property.id,
                room_type_id=suite_type.id,
                room_number=f"30{i}",
                floor=3,
                building="Main",
            )
        )

    test_db.add_all(rooms)
    test_db.commit()

    assert len(rooms) == 10

    # 4. Create Guests
    guest1 = Guest(
        first_name="John",
        last_name="Smith",
        email="john.smith@example.com",
        phone="+1-555-0101",
        guest_type=GuestType.INDIVIDUAL,
    )

    guest2 = Guest(
        first_name="Sarah",
        last_name="Johnson",
        email="sarah.johnson@acmecorp.com",
        phone="+1-555-0102",
        guest_type=GuestType.CORPORATE,
        company_name="Acme Corporation",
        is_vip=True,
        loyalty_number="LOY12345",
        loyalty_tier="gold",
    )

    guest3 = Guest(
        first_name="Robert",
        middle_name="James",
        last_name="Williams",
        email="robert.williams@example.com",
        phone="+1-555-0103",
        guest_type=GuestType.VIP,
        is_vip=True,
    )

    test_db.add_all([guest1, guest2, guest3])
    test_db.commit()

    assert guest1.id is not None
    assert guest2.full_name == "Sarah Johnson"
    assert guest3.full_name == "Robert James Williams"

    # 5. Create Business Day
    business_day = BusinessDay(property_id=property.id, business_date=date.today())

    business_day.open_day(opened_by="System")
    test_db.add(business_day)
    test_db.commit()

    assert business_day.status == DayStatus.OPEN

    # 6. Room Operations
    room_101 = rooms[0]

    assert room_101.is_available()

    room_101.check_in()
    test_db.commit()
    assert room_101.occupancy_state == OccupancyState.OCCUPIED

    room_101.check_out()
    test_db.commit()
    assert room_101.condition_state == ConditionState.DIRTY

    room_101.mark_clean()
    test_db.commit()
    assert room_101.is_available()

    # 7. Guest Statistics
    guest1.update_stay_statistics(nights_stayed=3)
    test_db.commit()
    assert guest1.total_stays == 1
    assert guest1.total_nights == 3

    # 8. Business Metrics
    business_day.total_revenue = Decimal("5000.00")
    business_day.room_revenue = Decimal("4500.00")
    business_day.total_occupancy = 8

    business_day.calculate_metrics(total_rooms=10)
    test_db.commit()

    assert business_day.adr == Decimal("562.50")
    assert business_day.occupancy_percent == Decimal("80.00")
    assert business_day.rev_par == Decimal("450.00")


def test_dual_state_scenarios(test_db):
    property = Property(
        name="Test",
        code="T",
        address_line1="123",
        city="C",
        state="S",
        postal_code="12345",
    )

    test_db.add(property)
    test_db.commit()

    room_type = RoomType(
        property_id=property.id, code="STD", name="Standard", base_price=Decimal("100")
    )

    test_db.add(room_type)
    test_db.commit()

    # Scenario 1: Vacant + Clean = Available
    room1 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="101",
        occupancy_state=OccupancyState.VACANT,
        condition_state=ConditionState.CLEAN,
    )
    assert room1.is_available()

    # Scenario 2: Occupied = Not Available
    room2 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="102",
        occupancy_state=OccupancyState.OCCUPIED,
    )
    assert not room2.is_available()

    # Scenario 3: Dirty = Not Available
    room3 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="103",
        condition_state=ConditionState.DIRTY,
    )
    assert not room3.is_available()

    # Scenario 4: Out of Order = Not Available
    room4 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="104",
        occupancy_state=OccupancyState.OUT_OF_ORDER,
    )
    assert not room4.is_available()

    # Scenario 5: Vacant + Inspected = Available
    room5 = Room(
        property_id=property.id,
        room_type_id=room_type.id,
        room_number="105",
        occupancy_state=OccupancyState.VACANT,
        condition_state=ConditionState.INSPECTED,
    )
    assert room5.is_available()
