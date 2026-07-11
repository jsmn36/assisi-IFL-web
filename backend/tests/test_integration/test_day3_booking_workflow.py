"""
Day 3 Integration Test
Test complete booking workflow: Reservation → Stay → Charges
"""
import pytest
from app.models import *
from datetime import date, datetime, timedelta
from decimal import Decimal


def test_complete_booking_workflow(test_db):
    """
    Integration test: Complete booking workflow from reservation to checkout
    """
    print("\n" + "=" * 60)
    print("🎫 DAY 3 INTEGRATION TEST: BOOKING WORKFLOW")
    print("=" * 60)

    # ============================================================
    # SETUP: Create hotel infrastructure
    # ============================================================

    # 1. Property
    property = Property(
        name="Luxury Beach Resort",
        code="BEACH001",
        address_line1="100 Ocean Drive",
        city="Miami Beach",
        state="FL",
        country="USA",
        postal_code="33139",
    )
    test_db.add(property)
    test_db.commit()
    print(f"\n✅ Property: {property.name}")

    # 2. Room Type
    deluxe_type = RoomType(
        property_id=property.id,
        code="DLX",
        name="Deluxe Ocean View",
        base_price=Decimal("199.99"),
        max_occupancy=2,
    )
    test_db.add(deluxe_type)
    test_db.commit()
    print(f"✅ Room Type: {deluxe_type.name} (${deluxe_type.base_price}/night)")

    # 3. Rooms
    room_201 = Room(
        property_id=property.id, room_type_id=deluxe_type.id, room_number="201", floor=2
    )
    room_202 = Room(
        property_id=property.id, room_type_id=deluxe_type.id, room_number="202", floor=2
    )
    test_db.add_all([room_201, room_202])
    test_db.commit()
    print(f"✅ Rooms: 201, 202 (both available)")

    # 4. Guest
    guest = Guest(
        first_name="Sarah",
        last_name="Anderson",
        email="sarah.anderson@example.com",
        phone="+1-555-0123",
    )
    test_db.add(guest)
    test_db.commit()
    print(f"✅ Guest: {guest.full_name}")

    # 5. Rate Plan
    summer_rate = RatePlan(
        property_id=property.id,
        room_type_id=deluxe_type.id,
        code="SUMMER",
        name="Summer Special",
        base_rate=Decimal("179.99"),
        weekend_rate=Decimal("219.99"),
        valid_from=date.today() - timedelta(days=30),
        valid_to=date.today() + timedelta(days=60),
        cancellation_policy="flexible",
        cancellation_hours=24,
    )
    test_db.add(summer_rate)
    test_db.commit()
    print(f"✅ Rate Plan: {summer_rate.name} (${summer_rate.base_rate}/night)")

    # ============================================================
    # STEP 1: CREATE RESERVATION
    # ============================================================
    print("\n📋 STEP 1: Creating Reservation...")

    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=3)

    reservation = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=deluxe_type.id,
        rate_code=summer_rate.code,
        confirmation_number="SUMMER2024001",
        check_in_date=check_in,
        check_out_date=check_out,
        num_adults=2,
        num_children=0,
        nightly_rate=summer_rate.base_rate,
        total_amount=Decimal("0"),
        source=ReservationSource.DIRECT,
    )

    # Calculate amounts
    reservation.calculate_nights()
    reservation.calculate_total_amount()

    test_db.add(reservation)
    test_db.commit()
    test_db.refresh(reservation)

    print(f"   ✅ Confirmation: {reservation.confirmation_number}")
    print(f"   ✅ Check-in: {reservation.check_in_date}")
    print(f"   ✅ Check-out: {reservation.check_out_date}")
    print(f"   ✅ Nights: {reservation.number_of_nights}")
    print(f"   ✅ Total: ${reservation.total_amount}")
    print(f"   ✅ Status: {reservation.status.value}")

    assert reservation.number_of_nights == 3
    assert reservation.total_amount == Decimal("539.97")  # 179.99 * 3
    assert reservation.status == ReservationStatus.PENDING

    # ============================================================
    # STEP 2: CONFIRM RESERVATION
    # ============================================================
    print("\n✅ STEP 2: Confirming Reservation...")

    result = reservation.confirm(confirmed_by="receptionist@resort.com")
    test_db.commit()

    print(f"   ✅ Status changed: {reservation.status.value}")
    print(f"   ✅ Confirmed by: {reservation.confirmed_by}")
    print(f"   ✅ Confirmed at: {reservation.confirmed_at}")

    assert result is True
    assert reservation.status == ReservationStatus.CONFIRMED

    # ============================================================
    # STEP 3: CHECK-IN (Create Stay)
    # ============================================================
    print("\n🏨 STEP 3: Check-In Process...")

    # Assign room
    stay = Stay(
        property_id=property.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room_201.id,
        check_in_date=reservation.check_in_date,
        check_out_date=reservation.check_out_date,
        num_adults=reservation.num_adults,
        nightly_rate=reservation.nightly_rate,
    )
    test_db.add(stay)
    test_db.commit()

    print(f"   ✅ Assigned room: {room_201.room_number}")

    # Check in guest
    stay.check_in(checked_in_by="frontdesk")
    test_db.commit()

    # Update room status
    room_201.check_in()
    test_db.commit()

    # Update reservation status
    reservation.check_in()
    test_db.commit()

    print(f"   ✅ Stay status: {stay.status.value}")
    print(f"   ✅ Room occupancy: {room_201.occupancy_state.value}")
    print(f"   ✅ Room condition: {room_201.condition_state.value}")
    print(f"   ✅ Reservation status: {reservation.status.value}")

    assert stay.status == StayStatus.CHECKED_IN
    assert room_201.occupancy_state == OccupancyState.OCCUPIED
    assert reservation.status == ReservationStatus.CHECKED_IN

    # ============================================================
    # STEP 4: POST ROOM CHARGES (manual tracking, no Charge model)
    # ============================================================
    print("\n💰 STEP 4: Posting Room Charges...")

    night_rate = reservation.nightly_rate
    stay.add_room_charge(night_rate)
    stay.add_room_charge(night_rate)
    stay.add_room_charge(night_rate)
    test_db.commit()

    print(f"   ✅ 3 nights @ ${night_rate}/night")
    print(f"   ✅ Total room charges: ${stay.total_room_charges}")

    # ============================================================
    # STEP 5: POST INCIDENTAL CHARGES (manual tracking, no Charge model)
    # ============================================================
    print("\n🍔 STEP 5: Posting Incidental Charges...")

    stay.add_other_charge(Decimal("45.00"))  # Minibar
    stay.add_other_charge(Decimal("65.00"))  # Room service
    stay.add_other_charge(Decimal("90.00"))  # Parking
    test_db.commit()

    print(f"   ✅ Minibar: $45.00")
    print(f"   ✅ Room Service: $65.00")
    print(f"   ✅ Parking: $90.00")
    print(f"   ✅ Total other charges: ${stay.total_other_charges}")

    # ============================================================
    # STEP 6: CHECK-OUT
    # ============================================================
    print("\n👋 STEP 6: Check-Out Process...")

    print(f"\n   📊 FINAL BILL:")
    print(f"   Room charges:  ${stay.total_room_charges}")
    print(f"   Other charges: ${stay.total_other_charges}")
    print(f"   ─────────────────────────")
    print(f"   TOTAL:         ${stay.total_charges}")

    # Check out guest
    stay.check_out(checked_out_by="frontdesk")
    test_db.commit()

    # Update room status
    room_201.check_out()  # Marks as vacant + dirty
    test_db.commit()

    # Update reservation status
    reservation.check_out()
    test_db.commit()

    print(f"\n   ✅ Stay status: {stay.status.value}")
    print(f"   ✅ Room occupancy: {room_201.occupancy_state.value}")
    print(f"   ✅ Room condition: {room_201.condition_state.value}")
    print(f"   ✅ Reservation status: {reservation.status.value}")
    print(
        f"   ✅ Room needs cleaning: {room_201.condition_state == ConditionState.DIRTY}"
    )

    assert stay.status == StayStatus.CHECKED_OUT
    assert room_201.occupancy_state == OccupancyState.VACANT
    assert room_201.condition_state == ConditionState.DIRTY
    assert reservation.status == ReservationStatus.CHECKED_OUT

    # ============================================================
    # STEP 7: HOUSEKEEPING
    # ============================================================
    print("\n🧹 STEP 7: Housekeeping...")

    room_201.mark_clean()
    test_db.commit()

    print(f"   ✅ Room {room_201.room_number} cleaned")
    print(f"   ✅ Room condition: {room_201.condition_state.value}")
    print(f"   ✅ Room available: {room_201.is_available()}")

    assert room_201.condition_state == ConditionState.CLEAN
    assert room_201.is_available() is True

    # ============================================================
    # STEP 8: UPDATE GUEST STATISTICS
    # ============================================================
    print("\n📈 STEP 8: Updating Guest Statistics...")

    guest.update_stay_statistics(nights_stayed=3)
    test_db.commit()

    print(f"   ✅ Total stays: {guest.total_stays}")
    print(f"   ✅ Total nights: {guest.total_nights}")
    print(f"   ✅ Last stay: {guest.last_stay_date}")

    assert guest.total_stays == 1
    assert guest.total_nights == 3

    # ============================================================
    # FINAL VERIFICATION
    # ============================================================
    print("\n" + "=" * 60)
    print("📊 FINAL VERIFICATION")
    print("=" * 60)

    test_db.refresh(reservation)
    test_db.refresh(stay)

    print(f"\n✅ Reservation → Stays: {len(reservation.stays)} stay(s)")
    assert len(reservation.stays) == 1

    print(f"✅ Stay → Room: Room {stay.room.room_number}")
    assert stay.room.room_number == "201"

    print(f"✅ Reservation → Guest: {reservation.guest.full_name}")
    assert reservation.guest.id == guest.id

    print(f"✅ Rate Plan used: {summer_rate.name}")

    print(f"\n💰 Financial Summary:")
    print(f"   Room charges:  ${stay.total_room_charges}")
    print(f"   Other charges: ${stay.total_other_charges}")
    print(f"   Total:         ${stay.total_charges}")

    print("\n" + "=" * 60)
    print("✅ BOOKING WORKFLOW TEST COMPLETE!")
    print("=" * 60)


def test_room_change_scenario(test_db):
    """
    Test scenario: Guest changes rooms mid-stay
    One reservation, multiple stays
    """
    print("\n🔄 TESTING ROOM CHANGE SCENARIO")

    # Setup
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

    room_101 = Room(
        property_id=property.id, room_type_id=room_type.id, room_number="101"
    )
    room_102 = Room(
        property_id=property.id, room_type_id=room_type.id, room_number="102"
    )
    test_db.add_all([room_101, room_102])
    test_db.commit()

    guest = Guest(first_name="Alice", last_name="Brown", email="alice@example.com")
    test_db.add(guest)
    test_db.commit()

    # Reservation for 3 nights
    reservation = Reservation(
        property_id=property.id,
        guest_id=guest.id,
        room_type_id=room_type.id,
        confirmation_number="CHANGE001",
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=3),
        number_of_nights=3,
        nightly_rate=Decimal("100"),
        total_amount=Decimal("300"),
        status=ReservationStatus.CONFIRMED,
    )
    test_db.add(reservation)
    test_db.commit()

    # Stay 1: Nights 1-2 in room 101
    stay1 = Stay(
        property_id=property.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room_101.id,
        check_in_date=date.today(),
        check_out_date=date.today() + timedelta(days=2),
        nightly_rate=Decimal("100"),
        status=StayStatus.CHECKED_OUT,
    )
    test_db.add(stay1)
    test_db.commit()

    # Stay 2: Night 3 in room 102 (guest moved)
    stay2 = Stay(
        property_id=property.id,
        reservation_id=reservation.id,
        guest_id=guest.id,
        room_id=room_102.id,
        check_in_date=date.today() + timedelta(days=2),
        check_out_date=date.today() + timedelta(days=3),
        nightly_rate=Decimal("100"),
        status=StayStatus.CHECKED_IN,
    )
    test_db.add(stay2)
    test_db.commit()

    # Verify
    test_db.refresh(reservation)
    assert len(reservation.stays) == 2
    assert reservation.stays[0].room.room_number == "101"
    assert reservation.stays[1].room.room_number == "102"

    print("   ✅ One reservation, two stays (room change)")
    print(f"   ✅ Stay 1: Room {stay1.room.room_number} (checked out)")
    print(f"   ✅ Stay 2: Room {stay2.room.room_number} (checked in)")


def test_rate_plan_superseding(test_db):
    """
    Test rate plan versioning/superseding
    """
    print("\n📋 TESTING RATE PLAN SUPERSEDING")

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

    # Original rate plan
    v1 = RatePlan(
        property_id=property.id,
        room_type_id=room_type.id,
        code="CORP",
        name="Corporate Rate v1",
        base_rate=Decimal("90.00"),
        valid_from=date.today() - timedelta(days=365),
        version=1,
    )
    test_db.add(v1)
    test_db.commit()

    # New rate plan (price increase)
    v2 = RatePlan(
        property_id=property.id,
        room_type_id=room_type.id,
        code="CORP",
        name="Corporate Rate v2",
        base_rate=Decimal("95.00"),
        valid_from=date.today(),
    )
    test_db.add(v2)
    test_db.commit()

    # Supersede v1 with v2
    v1.supersede_with_new_version(v2)
    test_db.commit()

    print(f"   ✅ v1 superseded: {v1.is_superseded}")
    print(f"   ✅ v2 version: {v2.version}")
    print(f"   ✅ v2 supersedes v1: {v2.supersedes_id == v1.id}")

    assert v1.is_superseded is True
    assert v2.version == 2
    assert v2.supersedes_id == v1.id
