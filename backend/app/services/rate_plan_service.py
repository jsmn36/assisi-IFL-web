from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.services.base_service import BaseService, ValidationError
from app.models import (
    RatePlan,
    RatePlanType,
    SeasonalRate,
    PricingRule,
    Property,
    RoomType,
)


class RatePlanService(BaseService):
    def create_rate_plan(
        self,
        property_id: int,
        room_type_id: Optional[int],
        code: str,
        name: str,
        type: RatePlanType,
        base_rate: Decimal,
        description: Optional[str] = None,
        adjustment_type: Optional[str] = None,
        adjustment_value: Optional[Decimal] = None,
        min_nights: int = 1,
        created_by: Optional[str] = None,
    ) -> RatePlan:
        self.get_or_404(Property, property_id)
        if room_type_id is not None:
            self.get_or_404(RoomType, room_type_id)

        existing = (
            self.db.query(RatePlan)
            .filter(RatePlan.property_id == property_id, RatePlan.code == code)
            .first()
        )

        if existing:
            raise ValidationError(f"Rate plan with code {code} already exists")

        rate_plan = RatePlan(
            property_id=property_id,
            room_type_id=room_type_id,
            code=code,
            name=name,
            description=description,
            plan_type=type,
            base_rate=base_rate,
            adjustment_type=adjustment_type,
            adjustment_value=adjustment_value,
            min_length_of_stay=min_nights,
            created_by=created_by,
        )

        self.db.add(rate_plan)
        self.commit()
        self.refresh(rate_plan)

        self._log_action("create_rate_plan", "rate_plan", rate_plan.id, created_by)

        return rate_plan

    def get_rate_plans(
        self,
        property_id: int,
        room_type_id: Optional[int] = None,
        active_only: bool = True,
    ) -> List[RatePlan]:
        query = self.db.query(RatePlan).filter(RatePlan.property_id == property_id)

        if room_type_id:
            query = query.filter(RatePlan.room_type_id == room_type_id)

        if active_only:
            query = query.filter(RatePlan.is_active.is_(True))

        return query.all()

    def calculate_rate(
        self,
        rate_plan_id: int,
        check_in_date: date,
        check_out_date: date,
        apply_seasonal: bool = True,
        apply_dynamic: bool = True,
    ) -> Dict:
        rate_plan = self.get_or_404(RatePlan, rate_plan_id)

        num_nights = (check_out_date - check_in_date).days
        if num_nights < 1:
            raise ValidationError("Check-out must be after check-in")

        nightly_rate = Decimal(rate_plan.base_rate)
        adjustments = []

        # ✅ Rate Plan Adjustment
        if rate_plan.adjustment_type and rate_plan.adjustment_value:
            if rate_plan.adjustment_type == "percentage":
                adjustment = nightly_rate * (
                    rate_plan.adjustment_value / Decimal("100")
                )
            else:
                adjustment = rate_plan.adjustment_value

            nightly_rate += adjustment

            adjustments.append(
                {
                    "type": "rate_plan",
                    "name": rate_plan.name,
                    "adjustment": float(adjustment),
                }
            )

        # ✅ Seasonal
        if apply_seasonal:
            result = self._apply_seasonal_adjustments(
                rate_plan.property_id,
                rate_plan.room_type_id,
                check_in_date,
                nightly_rate,
            )
            if result:
                nightly_rate = result["new_rate"]
                adjustments.extend(result["adjustments"])

        # ✅ Dynamic
        if apply_dynamic:
            result = self._apply_dynamic_pricing(
                rate_plan.property_id,
                rate_plan.room_type_id,
                check_in_date,
                nightly_rate,
            )
            if result:
                nightly_rate = result["new_rate"]
                adjustments.extend(result["adjustments"])

        total = nightly_rate * num_nights

        return {
            "rate_plan_id": rate_plan.id,
            "rate_plan_name": rate_plan.name,
            "base_rate": float(rate_plan.base_rate),
            "nightly_rate": float(nightly_rate),
            "num_nights": num_nights,
            "total": float(total),
            "adjustments": adjustments,
        }

    def _apply_seasonal_adjustments(
        self,
        property_id: int,
        room_type_id: int,
        check_in_date: date,
        current_rate: Decimal,
    ) -> Optional[Dict]:
        seasonal_rates = (
            self.db.query(SeasonalRate)
            .filter(
                SeasonalRate.property_id == property_id,
                SeasonalRate.is_active.is_(True),
                SeasonalRate.start_date <= check_in_date,
                SeasonalRate.end_date >= check_in_date,
                or_(
                    SeasonalRate.room_type_id == room_type_id,
                    SeasonalRate.room_type_id.is_(None),
                ),
            )
            .order_by(SeasonalRate.priority.asc())
            .all()
        )

        if not seasonal_rates:
            return None

        new_rate = current_rate
        adjustments = []

        for seasonal in seasonal_rates:
            if seasonal.adjustment_type == "percentage":
                adjustment = new_rate * (seasonal.adjustment_value / Decimal("100"))
            else:
                adjustment = seasonal.adjustment_value

            new_rate += adjustment

            adjustments.append(
                {
                    "type": "seasonal",
                    "name": seasonal.name,
                    "adjustment": float(adjustment),
                }
            )

        return {"new_rate": new_rate, "adjustments": adjustments}

    def _apply_dynamic_pricing(
        self,
        property_id: int,
        room_type_id: int,
        check_in_date: date,
        current_rate: Decimal,
    ) -> Optional[Dict]:
        rules = (
            self.db.query(PricingRule)
            .filter(
                PricingRule.property_id == property_id,
                PricingRule.is_active.is_(True),
                or_(
                    PricingRule.room_type_id == room_type_id,
                    PricingRule.room_type_id.is_(None),
                ),
            )
            .order_by(PricingRule.priority.asc())
            .all()
        )

        if not rules:
            return None

        new_rate = current_rate
        adjustments = []

        for rule in rules:
            if not self._evaluate_pricing_rule(rule, check_in_date):
                continue

            if rule.adjustment_type == "percentage":
                adjustment = new_rate * (rule.adjustment_value / Decimal("100"))
            else:
                adjustment = rule.adjustment_value

            new_rate += adjustment

            adjustments.append(
                {"type": "dynamic", "name": rule.name, "adjustment": float(adjustment)}
            )

        if not adjustments:
            return None

        return {"new_rate": new_rate, "adjustments": adjustments}

    def _evaluate_pricing_rule(self, rule: PricingRule, check_in_date: date) -> bool:
        today = datetime.now(timezone.utc).date()

        if rule.rule_type == "days_before":
            days_until = (check_in_date - today).days

            if rule.condition_operator == "lt":
                return days_until < int(rule.condition_value)
            elif rule.condition_operator == "gt":
                return days_until > int(rule.condition_value)

        elif rule.rule_type == "day_of_week":
            return check_in_date.strftime("%A").lower() == rule.condition_value.lower()

        return False

    def get_available_rate_plans(
        self,
        property_id: int,
        room_type_id: int,
        check_in_date,
        check_out_date,
        num_nights: int,
    ) -> list:
        plans = self.get_rate_plans(property_id, room_type_id, active_only=True)
        available = []
        for plan in plans:
            min_stay = plan.min_length_of_stay or 1
            max_stay = plan.max_length_of_stay
            if num_nights < min_stay:
                continue
            if max_stay and num_nights > max_stay:
                continue
            pricing = self.calculate_rate(
                plan.id,
                check_in_date,
                check_out_date,
                apply_seasonal=True,
                apply_dynamic=True,
            )
            available.append({"rate_plan": plan, "pricing": pricing})
        return available
