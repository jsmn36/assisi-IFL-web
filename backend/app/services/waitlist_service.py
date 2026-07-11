from app.services.base_service import BaseService, BusinessRuleError
from app.models import Reservation, ReservationStatus, Guest, RoomType
from datetime import date
from typing import List, Optional


class WaitlistEntry:
    pass


class WaitlistService(BaseService):
    def add_to_waitlist(
        self,
        property_id,
        guest_id,
        room_type_id,
        check_in_date,
        check_out_date,
        num_adults,
        num_children=0,
        priority=0,
        created_by=None,
    ):
        return {}

    def get_waitlist(self, property_id, room_type_id=None, check_in_date=None):
        return []

    def promote_from_waitlist(self, waitlist_id, promoted_by):
        return self.get_or_404(Reservation, waitlist_id)

    def remove_from_waitlist(self, waitlist_id, removed_by):
        return True
