from datetime import timezone

"""
Test Guest Model
"""
import pytest
from app.models.guest import Guest, GuestType
from datetime import date, datetime, timedelta
from sqlalchemy.exc import DataError


def test_create_guest_basic(test_db):
    """Test creating a basic guest"""
    guest = Guest(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+1-555-0100",
    )

    test_db.add(guest)
    test_db.commit()
    test_db.refresh(guest)

    assert guest.id is not None
    assert guest.first_name == "John"
    assert guest.last_name == "Doe"
    assert guest.full_name == "John Doe"
    assert guest.email == "john.doe@example.com"
    assert guest.guest_type == GuestType.INDIVIDUAL
    assert guest.is_vip is False
    assert guest.is_active is True


def test_guest_full_name_property(test_db):
    """Test full_name property with and without middle name"""
    guest1 = Guest(first_name="Jane", last_name="Smith")
    assert guest1.full_name == "Jane Smith"
    guest2 = Guest(first_name="John", middle_name="Michael", last_name="Doe")
    assert guest2.full_name == "John Michael Doe"


def test_guest_age_calculation(test_db):
    """Test age calculation from date of birth"""
    dob = date(date.today().year - 30, date.today().month, date.today().day)
    guest = Guest(first_name="Test", last_name="Person", date_of_birth=dob)
    test_db.add(guest)
    test_db.commit()
    assert guest.age == 30
    guest2 = Guest(first_name="Another", last_name="Person")
    assert guest2.age is None


def test_guest_corporate_type(test_db):
    """Test corporate guest"""
    guest = Guest(
        first_name="Sarah",
        last_name="Johnson",
        email="sarah.johnson@acme.com",
        guest_type=GuestType.CORPORATE,
        company_name="Acme Corporation",
    )
    test_db.add(guest)
    test_db.commit()
    test_db.refresh(guest)
    assert guest.guest_type == GuestType.CORPORATE
    assert guest.company_name == "Acme Corporation"


def test_guest_vip_status(test_db):
    """Test VIP guest with loyalty program"""
    guest = Guest(
        first_name="Robert",
        last_name="Williams",
        email="robert.williams@example.com",
        is_vip=True,
        loyalty_number="LOY12345",
        loyalty_tier="platinum",
    )
    test_db.add(guest)
    test_db.commit()
    test_db.refresh(guest)
    assert guest.is_vip is True
    assert guest.loyalty_number == "LOY12345"
    assert guest.loyalty_tier == "platinum"


def test_guest_stay_statistics(test_db):
    """Test updating guest stay statistics"""
    guest = Guest(first_name="Emily", last_name="Brown")
    test_db.add(guest)
    test_db.commit()
    assert guest.total_stays == 0
    assert guest.total_nights == 0
    assert guest.last_stay_date is None
    guest.update_stay_statistics(3)
    test_db.commit()
    assert guest.total_stays == 1
    assert guest.total_nights == 3
    assert guest.last_stay_date == date.today()
    guest.update_stay_statistics(5)
    test_db.commit()
    assert guest.total_stays == 2
    assert guest.total_nights == 8


def test_guest_blacklist(test_db):
    """Test blacklisting a guest"""
    guest = Guest(first_name="Bad", last_name="Guest")
    test_db.add(guest)
    test_db.commit()
    assert guest.is_blacklisted is False
    assert guest.blacklist_reason is None
    guest.blacklist("Damaged property")
    test_db.commit()
    assert guest.is_blacklisted is True
    assert guest.blacklist_reason == "Damaged property"
    guest.remove_from_blacklist()
    test_db.commit()
    assert guest.is_blacklisted is False
    assert guest.blacklist_reason is None


def test_guest_contact_information(test_db):
    """Test guest with complete contact information"""
    guest = Guest(
        first_name="Michael",
        last_name="Davis",
        email="michael.davis@example.com",
        phone="+1-555-0100",
        mobile="+1-555-0200",
        address_line1="123 Main Street",
        address_line2="Apt 4B",
        city="New York",
        state="NY",
        country="USA",
        postal_code="10001",
    )
    test_db.add(guest)
    test_db.commit()
    test_db.refresh(guest)
    assert guest.email == "michael.davis@example.com"
    assert guest.phone == "+1-555-0100"
    assert guest.mobile == "+1-555-0200"
    assert guest.city == "New York"
    assert guest.postal_code == "10001"


def test_guest_identification(test_db):
    """Test guest with identification documents"""
    guest = Guest(
        first_name="Anna",
        last_name="Martinez",
        passport_number="P12345678",
        id_type="passport",
        id_number="P12345678",
        id_country="USA",
        nationality="American",
    )
    test_db.add(guest)
    test_db.commit()
    test_db.refresh(guest)
    assert guest.passport_number == "P12345678"
    assert guest.id_type == "passport"
    assert guest.nationality == "American"


def test_guest_special_needs(test_db):
    """Test guest with special needs and preferences"""
    guest = Guest(
        first_name="David",
        last_name="Lee",
        special_requests="Late check-in, quiet room",
        dietary_restrictions="Vegetarian, no nuts",
        accessibility_needs="Wheelchair accessible room",
    )
    test_db.add(guest)
    test_db.commit()
    test_db.refresh(guest)
    assert "quiet room" in guest.special_requests
    assert "Vegetarian" in guest.dietary_restrictions
    assert "Wheelchair" in guest.accessibility_needs


def test_guest_privacy_settings(test_db):
    """Test guest privacy and marketing settings"""
    guest = Guest(
        first_name="Lisa",
        last_name="Wilson",
        marketing_opt_in=True,
        data_consent=True,
        data_consent_date=datetime.now(timezone.utc),
    )
    test_db.add(guest)
    test_db.commit()
    test_db.refresh(guest)
    assert guest.marketing_opt_in is True
    assert guest.data_consent is True
    assert guest.data_consent_date is not None


def test_guest_to_dict(test_db):
    """Test guest to_dict method"""
    guest = Guest(
        first_name="Test",
        last_name="Guest",
        email="test@example.com",
        is_vip=True,
        total_stays=5,
        total_nights=25,
    )
    test_db.add(guest)
    test_db.commit()
    guest_dict = guest.to_dict()
    assert guest_dict["first_name"] == "Test"
    assert guest_dict["last_name"] == "Guest"
    assert guest_dict["full_name"] == "Test Guest"
    assert guest_dict["email"] == "test@example.com"
    assert guest_dict["is_vip"] is True
    assert guest_dict["total_stays"] == 5
    assert guest_dict["total_nights"] == 25
