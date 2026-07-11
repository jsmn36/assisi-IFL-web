from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from app.services.base_service import BaseService, BusinessRuleError
from app.models import Stay, StayStatus, OccupancyState, ConditionState
from app.models.charge import Charge, ChargeType, ChargeStatus


class StayService(BaseService):
    def get_stay(self, stay_id: int) -> Stay:
        stay = self.db.query(Stay).get(stay_id)
        if not stay:
            raise BusinessRuleError(f"Stay {stay_id} not found")
        return stay

    def create_stay(
        self, reservation_id: int, room_id: int, created_by: str = None
    ) -> Stay:
        stay = Stay(
            reservation_id=reservation_id,
            room_id=room_id,
            status=StayStatus.RESERVED,
            created_by=created_by,
        )
        self.db.add(stay)
        self.commit()
        return stay

    def check_in_stay(self, stay_id: int, checked_in_by: str) -> Stay:
        stay = self.get_stay(stay_id)
        from app.state_machines.stay_state_machine import StayStateMachine

        sm = StayStateMachine(stay, self.db)
        success, error = sm.check_in(checked_in_by)
        if not success:
            raise BusinessRuleError(f"Check-in failed: {error}")
        return stay

    def check_out_stay(
        self, stay_id: int, checked_out_by: str, force_checkout: bool = False
    ) -> Stay:
        stay = self.get_stay(stay_id)
        from app.state_machines.stay_state_machine import StayStateMachine

        sm = StayStateMachine(stay, self.db)
        success, error = sm.check_out(checked_out_by)
        if not success:
            raise BusinessRuleError(f"Checkout failed: {error}")
        return stay

    def add_charge(
        self,
        stay_id: int,
        charge_type: ChargeType,
        description: str,
        amount: Decimal,
        created_by: str = None,
    ) -> Charge:
        charge = Charge(
            stay_id=stay_id,
            charge_type=charge_type,
            description=description,
            amount=amount,
            total_amount=amount,
            status=ChargeStatus.POSTED,
            created_by=created_by,
        )
        self.db.add(charge)
        self.commit()
        return charge

    def get_active_stays(
        self, property_id: Optional[int] = None, room_id: Optional[int] = None
    ) -> List[Stay]:
        query = self.db.query(Stay).filter(Stay.status == StayStatus.CHECKED_IN)
        if property_id is not None:
            query = query.filter(Stay.property_id == property_id)
        if room_id is not None:
            query = query.filter(Stay.room_id == room_id)
        return query.all()

    def get_stays_by_date(self, property_id: int, target_date: date) -> List[Stay]:
        return (
            self.db.query(Stay)
            .filter(
                Stay.property_id == property_id,
                Stay.check_in_date <= target_date,
                Stay.check_out_date >= target_date,
            )
            .all()
        )

    def post_room_charges(self, stay_id: int, posted_by: str) -> list:
        stay = self.get_stay(stay_id)
        nights = stay.reservation.number_of_nights if stay.reservation else 1
        nightly_rate = (
            stay.reservation.nightly_rate if stay.reservation else Decimal("0")
        )
        charges = []
        for i in range(nights):
            charge = Charge(
                stay_id=stay_id,
                charge_type=ChargeType.ROOM,
                description=f"Room charge night {i + 1}",
                amount=nightly_rate,
                total_amount=nightly_rate,
                status=ChargeStatus.POSTED,
                created_by=posted_by,
            )
            self.db.add(charge)
            charges.append(charge)
        self.commit()
        return charges
