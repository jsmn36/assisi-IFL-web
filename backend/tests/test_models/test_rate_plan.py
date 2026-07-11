import pytest
from app.models import Property, RoomType, RatePlan
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def setup_rate_plan_data(test_db):
    """Create property and room type for rate plan tests"""
    hotel = Property(
        name="Test Hotel",
        code="TEST001",
        address_line1="123 Test St",
        city="Test City",
        state="TC",
        postal_code="12345",
    )
    test_db.add(hotel)
    test_db.commit()
    test_db.refresh(hotel)

    room_type = RoomType(
        property_id=hotel.id,
        code="STD",
        name="Standard Room",
        base_price=Decimal("99.99"),
    )
    test_db.add(room_type)
    test_db.commit()
    test_db.refresh(room_type)

    return hotel, room_type


def test_create_rate_plan(test_db, setup_rate_plan_data):
    """Test creating a rate plan"""
    hotel, room_type = setup_rate_plan_data

    rate_plan = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="BAR",
        name="Best Available Rate",
        description="Standard rate available to all guests",
        base_rate=Decimal("129.99"),
        valid_from=date.today(),
        valid_to=date.today() + timedelta(days=365),
    )
    test_db.add(rate_plan)
    test_db.commit()
    test_db.refresh(rate_plan)

    assert rate_plan.id is not None
    assert rate_plan.code == "BAR"
    assert rate_plan.base_rate == Decimal("129.99")
    assert rate_plan.version == 1
    assert rate_plan.is_active is True
    assert rate_plan.is_superseded is False


def test_rate_plan_weekend_rate(test_db, setup_rate_plan_data):
    """Test rate plan with different weekend rates"""
    hotel, room_type = setup_rate_plan_data

    rate_plan = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="BAR",
        name="Best Available Rate",
        base_rate=Decimal("100.00"),
        weekend_rate=Decimal("150.00"),
        valid_from=date(2024, 1, 1),
        valid_to=date(2025, 12, 31),
    )
    test_db.add(rate_plan)
    test_db.commit()
    test_db.refresh(rate_plan)

    monday = date(2024, 1, 15)
    assert rate_plan.get_rate_for_date(monday) == Decimal("100.00")

    saturday = date(2024, 1, 20)
    assert rate_plan.get_rate_for_date(saturday) == Decimal("150.00")


def test_rate_plan_validity_dates(test_db, setup_rate_plan_data):
    """Test rate plan validity period"""
    hotel, room_type = setup_rate_plan_data

    current_plan = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="SUMMER",
        name="Summer Rate",
        base_rate=Decimal("150.00"),
        valid_from=date.today() - timedelta(days=30),
        valid_to=date.today() + timedelta(days=30),
    )
    test_db.add(current_plan)
    test_db.commit()
    test_db.refresh(current_plan)
    assert current_plan.is_currently_valid is True

    future_plan = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="WINTER",
        name="Winter Rate",
        base_rate=Decimal("200.00"),
        valid_from=date.today() + timedelta(days=60),
        valid_to=date.today() + timedelta(days=150),
    )
    test_db.add(future_plan)
    test_db.commit()
    test_db.refresh(future_plan)
    assert future_plan.is_currently_valid is False

    past_plan = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="SPRING",
        name="Spring Rate",
        base_rate=Decimal("120.00"),
        valid_from=date.today() - timedelta(days=120),
        valid_to=date.today() - timedelta(days=60),
    )
    test_db.add(past_plan)
    test_db.commit()
    test_db.refresh(past_plan)
    assert past_plan.is_currently_valid is False


def test_rate_plan_versioning(test_db, setup_rate_plan_data):
    """Test rate plan superseding/versioning"""
    hotel, room_type = setup_rate_plan_data

    v1 = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="CORP",
        name="Corporate Rate",
        base_rate=Decimal("100.00"),
        valid_from=date.today() - timedelta(days=365),
    )
    test_db.add(v1)
    test_db.commit()
    test_db.refresh(v1)

    assert v1.version == 1
    assert v1.is_superseded is False

    v2 = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="CORP",
        name="Corporate Rate v2",
        base_rate=Decimal("110.00"),
        valid_from=date.today(),
    )
    test_db.add(v2)
    test_db.commit()
    test_db.refresh(v2)

    v1.supersede_with_new_version(v2)
    test_db.commit()
    test_db.refresh(v1)
    test_db.refresh(v2)

    assert v1.is_superseded is True
    assert v1.superseded_by_id == v2.id
    assert v2.supersedes_id == v1.id
    assert v2.version == 2

    v3 = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="CORP",
        name="Corporate Rate v3",
        base_rate=Decimal("115.00"),
        valid_from=date.today() + timedelta(days=30),
    )
    test_db.add(v3)
    test_db.commit()
    test_db.refresh(v3)

    v2.supersede_with_new_version(v3)
    test_db.commit()
    test_db.expire_all()
    test_db.refresh(v2)
    test_db.refresh(v3)

    assert v2.is_superseded is True
    assert v3.version == 3
    assert v3.supersedes_id == v2.id
    assert v2.supersedes_id == v1.id


def test_rate_plan_restrictions(test_db, setup_rate_plan_data):
    """Test rate plan booking restrictions"""
    hotel, room_type = setup_rate_plan_data

    rate_plan = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="ADVANCE",
        name="Advance Purchase Rate",
        base_rate=Decimal("89.99"),
        valid_from=date.today(),
        min_length_of_stay=2,
        max_length_of_stay=7,
        min_advance_booking=14,
        max_advance_booking=90,
    )
    test_db.add(rate_plan)
    test_db.commit()
    test_db.refresh(rate_plan)

    assert rate_plan.min_length_of_stay == 2
    assert rate_plan.max_length_of_stay == 7
    assert rate_plan.min_advance_booking == 14
    assert rate_plan.max_advance_booking == 90


def test_rate_plan_channel_flags(test_db, setup_rate_plan_data):
    """Test rate plan booking channel flags"""
    hotel, room_type = setup_rate_plan_data

    public_rate = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="BAR",
        name="Best Available Rate",
        base_rate=Decimal("129.99"),
        valid_from=date.today(),
        is_public=True,
    )
    test_db.add(public_rate)
    test_db.commit()
    test_db.refresh(public_rate)
    assert public_rate.is_public is True

    corp_rate = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="CORP",
        name="Corporate Rate",
        base_rate=Decimal("99.99"),
        valid_from=date.today(),
        is_public=False,
        is_corporate=True,
    )
    test_db.add(corp_rate)
    test_db.commit()
    test_db.refresh(corp_rate)
    assert corp_rate.is_corporate is True

    gov_rate = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="GOV",
        name="Government Rate",
        base_rate=Decimal("95.00"),
        valid_from=date.today(),
        is_public=False,
        is_government=True,
    )
    test_db.add(gov_rate)
    test_db.commit()
    test_db.refresh(gov_rate)
    assert gov_rate.is_government is True


def test_rate_plan_cancellation_policy(test_db, setup_rate_plan_data):
    """Test rate plan cancellation policies"""
    hotel, room_type = setup_rate_plan_data

    flexible = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="FLEX",
        name="Flexible Rate",
        base_rate=Decimal("149.99"),
        valid_from=date.today(),
        cancellation_policy="flexible",
        cancellation_hours=24,
        cancellation_fee_percent=Decimal("0.00"),
    )
    test_db.add(flexible)
    test_db.commit()
    test_db.refresh(flexible)

    assert flexible.cancellation_policy == "flexible"
    assert flexible.cancellation_hours == 24
    assert flexible.cancellation_fee_percent == Decimal("0.00")

    strict = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="STRICT",
        name="Non-Refundable Rate",
        base_rate=Decimal("99.99"),
        valid_from=date.today(),
        cancellation_policy="strict",
        cancellation_hours=0,
        cancellation_fee_percent=Decimal("100.00"),
    )
    test_db.add(strict)
    test_db.commit()
    test_db.refresh(strict)

    assert strict.cancellation_policy == "strict"
    assert strict.cancellation_fee_percent == Decimal("100.00")


def test_rate_plan_is_valid_for_date(test_db, setup_rate_plan_data):
    """Test checking if rate plan is valid for specific date"""
    hotel, room_type = setup_rate_plan_data

    rate_plan = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="SUMMER",
        name="Summer Special",
        base_rate=Decimal("129.99"),
        valid_from=date(2024, 6, 1),
        valid_to=date(2024, 8, 31),
    )
    test_db.add(rate_plan)
    test_db.commit()
    test_db.refresh(rate_plan)

    assert rate_plan.is_valid_for_date(date(2024, 6, 1)) is True
    assert rate_plan.is_valid_for_date(date(2024, 7, 15)) is True
    assert rate_plan.is_valid_for_date(date(2024, 8, 31)) is True
    assert rate_plan.is_valid_for_date(date(2024, 5, 31)) is False
    assert rate_plan.is_valid_for_date(date(2024, 9, 1)) is False


def test_rate_plan_relationships(test_db, setup_rate_plan_data):
    """Test rate plan relationships"""
    hotel, room_type = setup_rate_plan_data

    rate_plan = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="BAR",
        name="Best Available Rate",
        base_rate=Decimal("129.99"),
        valid_from=date.today(),
    )
    test_db.add(rate_plan)
    test_db.commit()
    test_db.refresh(rate_plan)

    assert rate_plan.hotel_property.name == "Test Hotel"
    assert rate_plan.room_type.name == "Standard Room"


def test_rate_plan_to_dict(test_db, setup_rate_plan_data):
    """Test rate plan to_dict method"""
    hotel, room_type = setup_rate_plan_data

    rate_plan = RatePlan(
        property_id=hotel.id,
        room_type_id=room_type.id,
        code="CORP",
        name="Corporate Rate",
        base_rate=Decimal("110.00"),
        weekend_rate=Decimal("130.00"),
        valid_from=date.today(),
        min_length_of_stay=1,
        version=2,
    )
    test_db.add(rate_plan)
    test_db.commit()
    test_db.refresh(rate_plan)

    rp_dict = rate_plan.to_dict()

    assert rp_dict["code"] == "CORP"
    assert rp_dict["base_rate"] == 110.00
    assert rp_dict["weekend_rate"] == 130.00
    assert rp_dict["version"] == 2
    assert rp_dict["is_active"] is True
