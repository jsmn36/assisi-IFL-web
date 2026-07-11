from typing import Optional, List
from app.services.base_service import BaseService, ValidationError, NotFoundError
from app.models import Guest, GuestType, Reservation


class GuestService(BaseService):
    def create_guest(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        guest_type: GuestType = GuestType.INDIVIDUAL,
        **kwargs,
    ) -> Guest:
        if email:
            existing = self.db.query(Guest).filter(Guest.email == email).first()
            if existing:
                raise ValidationError(
                    f"Guest with email {email} already exists",
                    {"existing_guest_id": existing.id},
                )
        guest = Guest(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            guest_type=guest_type,
            **kwargs,
        )
        self.db.add(guest)
        self.commit()
        self.refresh(guest)
        self._log_action("create_guest", "guest", guest.id)
        return guest

    def delete_guest(self, guest_id: int) -> None:
        guest = self.get_or_404(Guest, guest_id)
        self.db.delete(guest)
        self.commit()

    def update_guest(self, guest_id: int, **kwargs) -> Guest:
        guest = self.get_or_404(Guest, guest_id)
        for key, value in kwargs.items():
            if hasattr(guest, key):
                setattr(guest, key, value)
        self.commit()
        self.refresh(guest)
        self._log_action("update_guest", "guest", guest.id)
        return guest

    def get_guest(
        self, guest_id: Optional[int] = None, email: Optional[str] = None
    ) -> Guest:
        if guest_id:
            return self.get_or_404(Guest, guest_id)
        if email:
            guest = self.db.query(Guest).filter(Guest.email == email).first()
            if not guest:
                raise NotFoundError(f"Guest with email {email} not found")
            return guest
        raise ValidationError("Must provide guest_id or email")

    def search_guests(
        self,
        query: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        guest_type: Optional[GuestType] = None,
        is_vip: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Guest]:
        db_query = self.db.query(Guest)
        if query:
            db_query = db_query.filter(
                (Guest.first_name.ilike(f"%{query}%"))
                | (Guest.last_name.ilike(f"%{query}%"))
                | (Guest.email.ilike(f"%{query}%"))
            )
        if email:
            db_query = db_query.filter(Guest.email == email)
        if phone:
            db_query = db_query.filter(Guest.phone == phone)
        if guest_type:
            db_query = db_query.filter(Guest.guest_type == guest_type)
        if is_vip is not None:
            db_query = db_query.filter(Guest.is_vip == is_vip)
        return db_query.limit(limit).all()

    def get_guest_reservations(
        self, guest_id: int, limit: int = 50
    ) -> List[Reservation]:
        self.get_or_404(Guest, guest_id)
        return (
            self.db.query(Reservation)
            .filter(Reservation.guest_id == guest_id)
            .limit(limit)
            .all()
        )

    def blacklist_guest(
        self, guest_id: int, reason: str, blacklisted_by: str = None
    ) -> Guest:
        guest = self.get_or_404(Guest, guest_id)
        guest.blacklist(reason)
        self.commit()
        self._log_action("blacklist_guest", "guest", guest.id, blacklisted_by)
        return guest

    def remove_from_blacklist(self, guest_id: int, removed_by: str = None) -> Guest:
        guest = self.get_or_404(Guest, guest_id)
        guest.remove_from_blacklist()
        self.commit()
        self._log_action("remove_from_blacklist", "guest", guest.id, removed_by)
        return guest
