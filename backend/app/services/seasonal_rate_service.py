from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.services.base_service import BaseService, ValidationError
from app.models import SeasonalRate, SeasonType, Property, RoomType


class SeasonalRateService(BaseService):
    # -------------------------------
    # CREATE SEASON
    # -------------------------------
    def create_seasonal_rate(
        self,
        property_id: int,
        name: str,
        season_type: SeasonType,
        start_date: date,
        end_date: date,
        adjustment_type: str,
        adjustment_value: Decimal,
        room_type_id: Optional[int] = None,
        priority: int = 0,
        created_by: Optional[str] = None,
    ) -> SeasonalRate:
        # Validate property
        self.get_or_404(Property, property_id)

        if room_type_id:
            self.get_or_404(RoomType, room_type_id)

        # -------------------------------
        # VALIDATIONS
        # -------------------------------
        if end_date <= start_date:
            raise ValidationError("End date must be after start date")

        if adjustment_type not in ["percentage", "fixed"]:
            raise ValidationError("Invalid adjustment type")

        if adjustment_value < 0:
            raise ValidationError("Adjustment value cannot be negative")

        if adjustment_type == "percentage" and adjustment_value > 100:
            raise ValidationError("Percentage cannot exceed 100")

        # -------------------------------
        # OVERLAP CHECK (CRITICAL FIX)
        # -------------------------------
        overlap_query = self.db.query(SeasonalRate).filter(
            SeasonalRate.property_id == property_id,
            SeasonalRate.is_active == True,
            or_(
                SeasonalRate.room_type_id == room_type_id,
                SeasonalRate.room_type_id.is_(None),
            ),
            and_(
                SeasonalRate.start_date <= end_date, SeasonalRate.end_date >= start_date
            ),
        )

        if overlap_query.first():
            raise ValidationError("Overlapping seasonal rate exists")

        # -------------------------------
        # CREATE
        # -------------------------------
        seasonal_rate = SeasonalRate(
            property_id=property_id,
            room_type_id=room_type_id,
            name=name,
            season_type=season_type,
            start_date=start_date,
            end_date=end_date,
            adjustment_type=adjustment_type,
            adjustment_value=adjustment_value,
            priority=priority,
            created_by=created_by,
        )

        try:
            self.db.add(seasonal_rate)
            self.commit()
            self.refresh(seasonal_rate)
        except Exception:
            self.db.rollback()
            raise

        self._log_action(
            "create_seasonal_rate", "seasonal_rate", seasonal_rate.id, created_by
        )

        return seasonal_rate

    # -------------------------------
    # GET ALL SEASONS
    # -------------------------------
    def get_seasonal_rates(
        self,
        property_id: int,
        room_type_id: Optional[int] = None,
        active_only: bool = True,
    ) -> List[SeasonalRate]:
        query = self.db.query(SeasonalRate).filter(
            SeasonalRate.property_id == property_id
        )

        if room_type_id:
            query = query.filter(
                or_(
                    SeasonalRate.room_type_id == room_type_id,
                    SeasonalRate.room_type_id.is_(None),  # ✅ FIX
                )
            )

        if active_only:
            query = query.filter(SeasonalRate.is_active.is_(True))  # ✅ FIX

        return query.order_by(SeasonalRate.start_date.asc()).all()

    # -------------------------------
    # ACTIVE SEASONS FOR DATE
    # -------------------------------
    def get_active_seasons(
        self, property_id: int, target_date: date, room_type_id: Optional[int] = None
    ) -> List[SeasonalRate]:
        query = self.db.query(SeasonalRate).filter(
            SeasonalRate.property_id == property_id,
            SeasonalRate.is_active.is_(True),  # ✅ FIX
            SeasonalRate.start_date <= target_date,
            SeasonalRate.end_date >= target_date,
        )

        if room_type_id:
            query = query.filter(
                or_(
                    SeasonalRate.room_type_id == room_type_id,
                    SeasonalRate.room_type_id.is_(None),  # ✅ FIX
                )
            )

        # ✅ IMPORTANT: higher priority applied later
        return query.order_by(SeasonalRate.priority.desc()).all()
