"""
Test Rate Management Services
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from app.services import RatePlanService, DiscountCodeService, SeasonalRateService
from app.services.pricing_engine import PricingEngine
from app.models import (
    Property,
    RoomType,
    Room,
    RatePlan,
    RatePlanType,
    SeasonalRate,
    SeasonType,
    DiscountCode,
)


@pytest.fixture
def setup_rate_test_data(test_db):
    """Setup test data for rate tests"""
    property = Property(
        name="Rate Hotel",
        code="RATE",
        address_line1="123",
        city="C",
        state="S",
        postal_code="12345",
    )
    test_db.add(property)
    test_db.commit()

    room_type = RoomType(
        property_id=property.id,
        code="STD",
        name="Standard",
        base_price=Decimal("100"),
        max_occupancy=2,
        max_adults=2,
        max_children=1,
    )
    test_db.add(room_type)
    test_db.commit()

    return property, room_type


def test_create_rate_plan(test_db, setup_rate_test_data):
    """Test creating rate plan"""
    property, room_type = setup_rate_test_data

    service = RatePlanService(test_db)
    rate_plan = service.create_rate_plan(
        property_id=property.id,
        room_type_id=room_type.id,
        code="CORP",
        name="Corporate Rate",
        type=RatePlanType.CORPORATE,
        base_rate=Decimal("90"),
        adjustment_type="percentage",
        adjustment_value=Decimal("-10"),
        min_nights=2,
        created_by="manager",
    )

    assert rate_plan.code == "CORP"
    assert rate_plan.base_rate == Decimal("90")
    assert rate_plan.min_length_of_stay == 2


def test_calculate_rate_with_adjustment(test_db, setup_rate_test_data):
    """Test rate calculation with percentage adjustment"""
    property, room_type = setup_rate_test_data

    service = RatePlanService(test_db)
    rate_plan = service.create_rate_plan(
        property_id=property.id,
        room_type_id=room_type.id,
        code="AAA",
        name="AAA Rate",
        type=RatePlanType.AAA,
        base_rate=Decimal("100"),
        adjustment_type="percentage",
        adjustment_value=Decimal("-15"),
        created_by="manager",
    )

    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=2)

    pricing = service.calculate_rate(
        rate_plan.id, check_in, check_out, apply_seasonal=False, apply_dynamic=False
    )

    assert pricing["base_rate"] == 100.0
    assert pricing["nightly_rate"] == 85.0
    assert pricing["num_nights"] == 2
    assert pricing["total"] == 170.0


def test_create_seasonal_rate(test_db, setup_rate_test_data):
    """Test creating seasonal rate"""
    property, room_type = setup_rate_test_data

    service = SeasonalRateService(test_db)
    seasonal = service.create_seasonal_rate(
        property_id=property.id,
        name="Summer Peak",
        season_type=SeasonType.PEAK,
        start_date=date(2024, 6, 1),
        end_date=date(2024, 8, 31),
        adjustment_type="percentage",
        adjustment_value=Decimal("25"),
        priority=1,
        created_by="manager",
    )

    assert seasonal.name == "Summer Peak"
    assert seasonal.season_type == SeasonType.PEAK
    assert seasonal.adjustment_value == Decimal("25")


def test_create_discount_code(test_db, setup_rate_test_data):
    """Test creating discount code"""
    property, room_type = setup_rate_test_data

    service = DiscountCodeService(test_db)
    discount = service.create_discount_code(
        property_id=property.id,
        code="SAVE20",
        description="20% off summer special",
        discount_type="percentage",
        discount_value=Decimal("20"),
        min_nights=3,
        max_uses=100,
        created_by="manager",
    )

    assert discount.code == "SAVE20"
    assert discount.discount_value == Decimal("20")
    assert discount.min_nights == 3


def test_validate_discount_code(test_db, setup_rate_test_data):
    """Test discount code validation"""
    property, room_type = setup_rate_test_data

    service = DiscountCodeService(test_db)
    discount = service.create_discount_code(
        property_id=property.id,
        code="TEST20",
        description="Test discount",
        discount_type="percentage",
        discount_value=Decimal("20"),
        min_nights=2,
        min_amount=Decimal("100"),
        created_by="manager",
    )

    # Valid case
    result = service.validate_discount_code(
        property_id=property.id,
        code="TEST20",
        booking_amount=Decimal("200"),
        num_nights=3,
    )

    assert result["valid"] is True
    assert result["discount_amount"] == 40.0

    # Invalid - min nights not met
    result = service.validate_discount_code(
        property_id=property.id,
        code="TEST20",
        booking_amount=Decimal("200"),
        num_nights=1,
    )

    assert result["valid"] is False
    assert "Minimum 2 nights" in result["error"]

    # Invalid - min amount not met
    result = service.validate_discount_code(
        property_id=property.id,
        code="TEST20",
        booking_amount=Decimal("50"),
        num_nights=3,
    )

    assert result["valid"] is False
    assert "Minimum booking amount" in result["error"]


def test_pricing_engine_best_rate(test_db, setup_rate_test_data):
    """Test pricing engine best rate calculation"""
    property, room_type = setup_rate_test_data

    rate_service = RatePlanService(test_db)

    standard = rate_service.create_rate_plan(
        property_id=property.id,
        room_type_id=room_type.id,
        code="STD",
        name="Standard Rate",
        type=RatePlanType.STANDARD,
        base_rate=Decimal("100"),
        created_by="manager",
    )

    corporate = rate_service.create_rate_plan(
        property_id=property.id,
        room_type_id=room_type.id,
        code="CORP",
        name="Corporate Rate",
        type=RatePlanType.CORPORATE,
        base_rate=Decimal("100"),
        adjustment_type="percentage",
        adjustment_value=Decimal("-15"),
        created_by="manager",
    )

    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=2)

    engine = PricingEngine(test_db)
    result = engine.calculate_best_rate(
        property_id=property.id,
        room_type_id=room_type.id,
        check_in_date=check_in,
        check_out_date=check_out,
        num_adults=2,
    )

    assert result["num_options"] == 2
    assert result["best_rate"]["rate_plan"].code == "CORP"


def test_generate_discount_code(test_db, setup_rate_test_data):
    """Test generating random discount code"""
    property, room_type = setup_rate_test_data

    service = DiscountCodeService(test_db)
    code = service.generate_discount_code(
        property_id=property.id, prefix="PROMO", length=8
    )

    assert code.startswith("PROMO")
    assert len(code) == 13


def test_get_available_rate_plans(test_db, setup_rate_test_data):
    """Test getting available rate plans with restrictions"""
    property, room_type = setup_rate_test_data

    service = RatePlanService(test_db)

    service.create_rate_plan(
        property_id=property.id,
        room_type_id=room_type.id,
        code="WEEK",
        name="Weekly Rate",
        type=RatePlanType.STANDARD,
        base_rate=Decimal("80"),
        min_nights=3,
        created_by="manager",
    )

    service.create_rate_plan(
        property_id=property.id,
        room_type_id=room_type.id,
        code="FLEX",
        name="Flexible Rate",
        type=RatePlanType.STANDARD,
        base_rate=Decimal("100"),
        min_nights=1,
        created_by="manager",
    )

    check_in = date.today() + timedelta(days=7)
    check_out = check_in + timedelta(days=2)

    available = service.get_available_rate_plans(
        property_id=property.id,
        room_type_id=room_type.id,
        check_in_date=check_in,
        check_out_date=check_out,
        num_nights=2,
    )

    assert len(available) == 1
    assert available[0]["rate_plan"].code == "FLEX"
