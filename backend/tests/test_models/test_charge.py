"""
Tests for Charge model
Run: pytest tests/test_models/test_charge.py -v
"""
import pytest
from decimal import Decimal
from datetime import date
from app.models import Charge, ChargeType, ChargeStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_charge(test_db, **kwargs):
    charge = Charge(
        property_id=kwargs.get("property_id", 1),
        guest_id=kwargs.get("guest_id", 1),
        charge_type=kwargs.get("charge_type", ChargeType.ROOM),
        description=kwargs.get("description", "Room charge"),
        amount=kwargs.get("amount", Decimal("100.00")),
        tax_amount=kwargs.get("tax_amount", Decimal("0.00")),
        total_amount=kwargs.get("total_amount", Decimal("100.00")),
        status=kwargs.get("status", ChargeStatus.PENDING),
        charge_date=kwargs.get("charge_date", date.today()),
    )
    for k, v in kwargs.items():
        if hasattr(charge, k):
            setattr(charge, k, v)
    test_db.add(charge)
    test_db.commit()
    test_db.refresh(charge)
    return charge


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


def test_charge_type_values():
    assert ChargeType.ROOM == "room"
    assert ChargeType.TAX == "tax"
    assert ChargeType.CANCELLATION_FEE == "cancellation_fee"
    assert ChargeType.NO_SHOW_FEE == "no_show_fee"
    assert ChargeType.MINIBAR == "minibar"
    assert ChargeType.SPA == "spa"
    assert ChargeType.PARKING == "parking"
    assert ChargeType.DAMAGE == "damage"
    assert ChargeType.OTHER == "other"


def test_charge_status_values():
    assert ChargeStatus.PENDING == "pending"
    assert ChargeStatus.POSTED == "posted"
    assert ChargeStatus.PAID == "paid"
    assert ChargeStatus.VOIDED == "voided"
    assert ChargeStatus.DISPUTED == "disputed"


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


def test_create_basic_charge(test_db):
    charge = make_charge(test_db)
    assert charge.id is not None
    assert charge.charge_type == ChargeType.ROOM
    assert charge.status == ChargeStatus.PENDING
    assert charge.amount == Decimal("100.00")


def test_create_charge_all_types(test_db):
    for ct in ChargeType:
        c = make_charge(test_db, charge_type=ct, description=f"{ct.value} charge")
        assert c.charge_type == ct


def test_charge_defaults(test_db):
    charge = make_charge(test_db)
    assert charge.is_voided is False
    assert charge.status == ChargeStatus.PENDING
    assert charge.charge_date == date.today()


# ---------------------------------------------------------------------------
# calculate_total
# ---------------------------------------------------------------------------


def test_calculate_total_basic(test_db):
    c = make_charge(test_db, amount=Decimal("100.00"), tax_amount=Decimal("10.00"))
    result = c.calculate_total()
    assert result == Decimal("110.00")
    assert c.total_amount == Decimal("110.00")


def test_calculate_total_zero_tax(test_db):
    c = make_charge(test_db, amount=Decimal("50.00"), tax_amount=Decimal("0.00"))
    assert c.calculate_total() == Decimal("50.00")


def test_calculate_total_none_amount(test_db):
    c = make_charge(test_db, amount=Decimal("0.00"), tax_amount=Decimal("5.00"))
    c.amount = None
    assert c.calculate_total() == Decimal("5.00")


def test_calculate_total_none_tax(test_db):
    c = make_charge(test_db, amount=Decimal("80.00"))
    c.tax_amount = None
    assert c.calculate_total() == Decimal("80.00")


# ---------------------------------------------------------------------------
# calculate_tax
# ---------------------------------------------------------------------------


def test_calculate_tax_ten_percent(test_db):
    c = make_charge(test_db, amount=Decimal("200.00"))
    tax = c.calculate_tax(10)
    assert tax == Decimal("20.00")
    assert c.tax_rate == Decimal("10")
    assert c.total_amount == Decimal("220.00")


def test_calculate_tax_zero(test_db):
    c = make_charge(test_db, amount=Decimal("100.00"))
    assert c.calculate_tax(0) == Decimal("0.00")


def test_calculate_tax_fractional(test_db):
    c = make_charge(test_db, amount=Decimal("100.00"))
    tax = c.calculate_tax(7.5)
    assert tax == Decimal("7.5")


def test_calculate_tax_sets_rate(test_db):
    c = make_charge(test_db, amount=Decimal("100.00"))
    c.calculate_tax(15)
    assert c.tax_rate == Decimal("15")


# ---------------------------------------------------------------------------
# post
# ---------------------------------------------------------------------------


def test_post_pending_charge(test_db):
    c = make_charge(test_db, status=ChargeStatus.PENDING)
    result = c.post()
    assert result is True
    assert c.status == ChargeStatus.POSTED
    assert c.post_date == date.today()


def test_cannot_post_already_posted(test_db):
    c = make_charge(test_db, status=ChargeStatus.POSTED)
    assert c.post() is False
    assert c.status == ChargeStatus.POSTED


def test_cannot_post_paid(test_db):
    c = make_charge(test_db, status=ChargeStatus.PAID)
    assert c.post() is False


def test_cannot_post_voided(test_db):
    c = make_charge(test_db, status=ChargeStatus.VOIDED)
    assert c.post() is False


# ---------------------------------------------------------------------------
# mark_paid
# ---------------------------------------------------------------------------


def test_mark_paid_posted_charge(test_db):
    c = make_charge(test_db, status=ChargeStatus.POSTED)
    result = c.mark_paid("credit_card", "REF123")
    assert result is True
    assert c.status == ChargeStatus.PAID
    assert c.payment_method == "credit_card"
    assert c.payment_reference == "REF123"
    assert c.payment_date == date.today()


def test_mark_paid_without_reference(test_db):
    c = make_charge(test_db, status=ChargeStatus.POSTED)
    result = c.mark_paid("cash")
    assert result is True
    assert c.payment_reference is None


def test_cannot_pay_pending(test_db):
    c = make_charge(test_db, status=ChargeStatus.PENDING)
    assert c.mark_paid("cash") is False


def test_cannot_pay_voided(test_db):
    c = make_charge(test_db, status=ChargeStatus.VOIDED)
    assert c.mark_paid("cash") is False


# ---------------------------------------------------------------------------
# void
# ---------------------------------------------------------------------------


def test_void_pending_charge(test_db):
    c = make_charge(test_db, status=ChargeStatus.PENDING)
    result = c.void("manager", "Duplicate charge")
    assert result is True
    assert c.status == ChargeStatus.VOIDED
    assert c.is_voided is True
    assert c.voided_by == "manager"
    assert c.void_reason == "Duplicate charge"
    assert c.voided_at is not None


def test_void_posted_charge(test_db):
    c = make_charge(test_db, status=ChargeStatus.POSTED)
    assert c.void("admin", "Error") is True


def test_cannot_void_paid(test_db):
    c = make_charge(test_db, status=ChargeStatus.PAID)
    assert c.void("admin", "test") is False


def test_cannot_void_already_voided(test_db):
    c = make_charge(test_db, status=ChargeStatus.VOIDED)
    assert c.void("admin", "again") is False


def test_void_disputed_charge(test_db):
    c = make_charge(test_db, status=ChargeStatus.DISPUTED)
    assert c.void("admin", "resolved") is True


# ---------------------------------------------------------------------------
# dispute
# ---------------------------------------------------------------------------


def test_dispute_posted_charge(test_db):
    c = make_charge(test_db, status=ChargeStatus.POSTED)
    assert c.dispute() is True
    assert c.status == ChargeStatus.DISPUTED


def test_cannot_dispute_pending(test_db):
    c = make_charge(test_db, status=ChargeStatus.PENDING)
    assert c.dispute() is False


def test_cannot_dispute_paid(test_db):
    c = make_charge(test_db, status=ChargeStatus.PAID)
    assert c.dispute() is False


def test_cannot_dispute_voided(test_db):
    c = make_charge(test_db, status=ChargeStatus.VOIDED)
    assert c.dispute() is False


# ---------------------------------------------------------------------------
# Properties: is_paid, is_pending
# ---------------------------------------------------------------------------


def test_is_paid_true(test_db):
    c = make_charge(test_db, status=ChargeStatus.PAID)
    assert c.is_paid is True


def test_is_paid_false(test_db):
    c = make_charge(test_db, status=ChargeStatus.PENDING)
    assert c.is_paid is False


def test_is_pending_true(test_db):
    c = make_charge(test_db, status=ChargeStatus.PENDING)
    assert c.is_pending is True


def test_is_pending_false(test_db):
    c = make_charge(test_db, status=ChargeStatus.POSTED)
    assert c.is_pending is False


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------


def test_to_dict_basic(test_db):
    c = make_charge(
        test_db,
        amount=Decimal("100.00"),
        tax_amount=Decimal("10.00"),
        total_amount=Decimal("110.00"),
        status=ChargeStatus.PENDING,
        charge_type=ChargeType.ROOM,
    )
    d = c.to_dict()
    assert d["amount"] == 100.0
    assert d["tax_amount"] == 10.0
    assert d["total_amount"] == 110.0
    assert d["status"] == "pending"
    assert d["charge_type"] == "room"
    assert d["is_paid"] is False
    assert d["is_voided"] is False


def test_to_dict_dates(test_db):
    today = date.today()
    c = make_charge(test_db, status=ChargeStatus.PENDING, charge_date=today)
    c.post()
    d = c.to_dict()
    assert d["charge_date"] == today.isoformat()
    assert d["post_date"] == today.isoformat()


def test_to_dict_all_keys_present(test_db):
    c = make_charge(test_db)
    d = c.to_dict()
    expected = {
        "id",
        "property_id",
        "reservation_id",
        "stay_id",
        "guest_id",
        "charge_type",
        "description",
        "amount",
        "tax_amount",
        "total_amount",
        "status",
        "charge_date",
        "post_date",
        "payment_date",
        "is_paid",
        "is_voided",
    }
    assert expected.issubset(set(d.keys()))


def test_to_dict_paid_charge(test_db):
    c = make_charge(test_db, status=ChargeStatus.POSTED)
    c.mark_paid("credit_card", "REF999")
    d = c.to_dict()
    assert d["is_paid"] is True
    assert d["payment_date"] == date.today().isoformat()


def test_to_dict_null_dates(test_db):
    c = make_charge(test_db)
    d = c.to_dict()
    assert d["post_date"] is None
    assert d["payment_date"] is None


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_repr(test_db):
    c = make_charge(test_db, charge_type=ChargeType.ROOM)
    r = repr(c)
    assert "room" in r
    assert "Charge" in r
