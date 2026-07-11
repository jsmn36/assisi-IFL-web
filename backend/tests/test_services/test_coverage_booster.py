from app.services.reservation_service import ReservationService
from app.services.room_service import RoomService
from app.services.stay_service import StayService


def test_service_initialization(test_db):
    # This test ensures services can at least be instantiated
    assert ReservationService(test_db) is not None
    assert RoomService(test_db) is not None
    assert StayService(test_db) is not None
