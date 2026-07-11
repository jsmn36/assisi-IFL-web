"""
Day 6 Integration Test
Test complete service layer workflow
"""
import pytest
from app.services import *
from app.models import Property, RoomType, Room, Guest, ReservationStatus, StayStatus
from datetime import date, timedelta
from decimal import Decimal


def test_complete_hotel_workflow_with_services(test_db):
    """
    Integration test: Complete hotel workflow using services
    """
    print("\n" + "=" * 60)
    print("🏨 DAY 6 INTEGRATION: COMPLETE SERVICES WORKFLOW")
    print("=" * 60)

    # Setup: Create hotel infrastructure
    property = Property(
        name="Services Hotel",
        code="SRV",
        address_line1="123 Service St",
        city="Miami",
        state="FL",
        postal_code="33101",
    )
    test_db.add(property)
    test_db.commit()

    room_type = RoomType(
        property_id=property.id,
        code="DLX",
        name="Deluxe",
        base_price=Decimal("200"),
        capacity=3,
    )
    test_db.add(room_type)
    test_db.commit()

    room = Room(property_id=property.id, room_type_id=room_type.id, room_number="401")
    test_db.add(room)
    test_db.commit()

    print(f"\n✅ Hotel setup: {property.name}, Room {room.room_number}")

    # Step 1: Create guest
    guest_service = GuestService(test_db)
    guest = guest_service.create_guest(
        first_name="Complete",
        last_name="Workflow",
        email="workflow@example.com",
        phone="+1-555-9999",
    )
    print(f"✅ Guest created: {guest.full_name}")

    # Step 2: Create reservation
    res_service = ReservationService(test_db)
    reservation = res_service.create_reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=3),
        num_adults=2,
        num_children=1,
        created_by="online_booking",
    )
    print(f"✅ Reservation created: {reservation.confirmation_number}")
    assert reservation.status == ReservationStatus.PENDING

    # Step 3: Confirm reservation
    confirmed = res_service.confirm_reservation(reservation.id, "receptionist")
    print(f"✅ Reservation confirmed: {confirmed.status.value}")
    assert confirmed.status == ReservationStatus.CONFIRMED

    # Step 4: Check in
    check_in_service = CheckInService(test_db)
    check_in_result = check_in_service.check_in(
        confirmation_number=reservation.confirmation_number,
        room_id=room.id,
        checked_in_by="frontdesk",
        post_room_charges=True,
    )
    print(f"✅ Checked in: {check_in_result['message']}")
    assert check_in_result["success"] is True
    assert check_in_result["stay"].status == StayStatus.CHECKED_IN
    assert check_in_result["charges_posted"] == 3

    stay = check_in_result["stay"]

    # Step 5: Add incidental charges
    stay_service = StayService(test_db)
    from app.models import ChargeType

    minibar = stay_service.add_charge(
        stay_id=stay.id,
        charge_type=ChargeType.MINIBAR,
        description="Minibar items",
        amount=Decimal("50.00"),
        created_by="frontdesk",
    )
    print(f"✅ Added minibar charge: ${minibar.total_amount}")

    # Step 6: Check out
    check_out_service = CheckOutService(test_db)
    check_out_result = check_out_service.check_out(
        stay_id=stay.id,
        checked_out_by="frontdesk",
        payment_method="credit_card",
        force_checkout=True,
    )
    print(f"✅ Checked out: {check_out_result['message']}")
    assert check_out_result["success"] is True
    assert check_out_result["stay"].status == StayStatus.CHECKED_OUT

    # Step 7: Verify final bill
    bill = check_out_result["bill"]
    print(f"\n📊 Final Bill:")
    print(f"   Room charges: ${bill['charges_by_type']['room']['subtotal']}")
    print(
        f"   Other charges: ${bill['charges_by_type'].get('minibar', {}).get('subtotal', 0)}"
    )
    print(f"   Total: ${bill['total']}")
    print(f"   Payment: {bill['payment_status']}")

    # Step 8: Verify guest statistics
    test_db.refresh(guest)
    print(f"\n👤 Guest Statistics:")
    print(f"   Total stays: {guest.total_stays}")
    print(f"   Total nights: {guest.total_nights}")

    assert guest.total_stays == 1
    assert guest.total_nights == 3

    # Step 9: Verify room status
    room_service = RoomService(test_db)
    test_db.refresh(room)
    print(f"\n🚪 Room Status:")
    print(f"   Occupancy: {room.occupancy_state.value}")
    print(f"   Condition: {room.condition_state.value}")

    from app.models import OccupancyState, ConditionState

    assert room.occupancy_state == OccupancyState.VACANT
    assert room.condition_state == ConditionState.DIRTY

    # Step 10: Clean room
    cleaned = room_service.mark_room_clean(room.id, "housekeeper")
    print(f"✅ Room cleaned and available: {cleaned.is_available()}")
    assert cleaned.is_available() is True

    print("\n" + "=" * 60)
    print("✅ COMPLETE WORKFLOW TEST PASSED!")
    print("=" * 60)
