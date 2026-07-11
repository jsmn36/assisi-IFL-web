from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.services.base_service import BaseService
from app.services.rate_plan_service import RatePlanService
from app.models import Room, Stay, DiscountCode


class PricingEngine(BaseService):
    def __init__(self, db: Session):
        super().__init__(db)
        self.rate_plan_service = RatePlanService(db)

    # -------------------------------
    # BEST RATE
    # -------------------------------
    def calculate_best_rate(
        self,
        property_id: int,
        room_type_id: int,
        check_in_date: date,
        check_out_date: date,
        num_adults: int,
        discount_code: Optional[str] = None,
    ) -> Dict:
        num_nights = (check_out_date - check_in_date).days

        available_plans = self.rate_plan_service.get_available_rate_plans(
            property_id, room_type_id, check_in_date, check_out_date, num_nights
        )

        if not available_plans:
            raise ValueError("No rate plans available")

        # ✅ Ensure sorting by lowest total price
        available_plans.sort(key=lambda x: x["pricing"]["total"])

        # Apply discount
        if discount_code:
            discount = self._get_discount_code(property_id, discount_code)

            if discount:
                for plan in available_plans:
                    plan["pricing"] = self._apply_discount(
                        pricing=plan["pricing"].copy(),  # ✅ avoid mutation bug
                        discount=discount,
                        num_nights=num_nights,
                    )

                # ✅ Re-sort after discount applied
                available_plans.sort(key=lambda x: x["pricing"]["total"])

        return {
            "best_rate": available_plans[0],
            "all_rates": available_plans,
            "num_options": len(available_plans),
        }

    # -------------------------------
    # OCCUPANCY
    # -------------------------------
    def calculate_occupancy_rate(self, property_id: int, target_date: date) -> Dict:
        total_rooms = (
            self.db.query(Room)
            .filter(Room.property_id == property_id, Room.is_active == True)
            .count()
        )

        occupied_rooms = (
            self.db.query(Stay)
            .filter(
                Stay.property_id == property_id,
                Stay.check_in_date <= target_date,
                Stay.check_out_date > target_date,
                Stay.status.in_(["checked_in", "reserved"]),
            )
            .count()
        )

        # ✅ Safe division
        occupancy_rate = (occupied_rooms / total_rooms) * 100 if total_rooms > 0 else 0

        return {
            "date": str(target_date),
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "available_rooms": max(total_rooms - occupied_rooms, 0),
            "occupancy_rate": round(occupancy_rate, 2),
        }

    # -------------------------------
    # SMART PRICING
    # -------------------------------
    def suggest_optimal_price(
        self, property_id: int, room_type_id: int, target_date: date, base_rate: Decimal
    ) -> Dict:
        occupancy = self.calculate_occupancy_rate(property_id, target_date)
        occupancy_rate = occupancy["occupancy_rate"]

        suggested_rate = Decimal(base_rate)
        reasons = []

        # Demand-based pricing
        if occupancy_rate >= 90:
            suggested_rate *= Decimal("1.25")
            reasons.append("High demand (+25%)")
        elif occupancy_rate >= 75:
            suggested_rate *= Decimal("1.15")
            reasons.append("Good demand (+15%)")
        elif occupancy_rate >= 50:
            suggested_rate *= Decimal("1.05")
            reasons.append("Normal demand (+5%)")
        elif occupancy_rate < 30:
            suggested_rate *= Decimal("0.85")
            reasons.append("Low demand (-15%)")

        # Time-based pricing
        days_until = (target_date - date.today()).days

        if days_until <= 3 and occupancy_rate < 60:
            suggested_rate *= Decimal("0.9")
            reasons.append("Last minute (-10%)")
        elif days_until > 60:
            suggested_rate *= Decimal("0.95")
            reasons.append("Early booking (-5%)")

        return {
            "base_rate": float(base_rate),
            "suggested_rate": float(suggested_rate),
            "change_percent": float((suggested_rate - base_rate) / base_rate * 100),
            "occupancy_rate": occupancy_rate,
            "days_until": days_until,
            "reasons": reasons,
        }

    # -------------------------------
    # DISCOUNT FETCH
    # -------------------------------
    def _get_discount_code(self, property_id: int, code: str) -> Optional[DiscountCode]:
        discount = (
            self.db.query(DiscountCode)
            .filter(
                DiscountCode.property_id == property_id,
                DiscountCode.code == code,
                DiscountCode.is_active == True,
            )
            .first()
        )

        if not discount:
            return None

        today = date.today()

        if discount.valid_from and today < discount.valid_from:
            return None

        if discount.valid_until and today > discount.valid_until:
            return None

        if discount.max_uses and discount.uses_count >= discount.max_uses:
            return None

        return discount

    # -------------------------------
    # APPLY DISCOUNT
    # -------------------------------
    def _apply_discount(
        self, pricing: Dict, discount: DiscountCode, num_nights: int
    ) -> Dict:
        original_total = Decimal(str(pricing["total"]))
        discount_amount = Decimal("0")

        # ✅ Ensure adjustments exists
        pricing.setdefault("adjustments", [])

        if discount.discount_type == "percentage":
            discount_amount = original_total * (Decimal(discount.discount_value) / 100)

        elif discount.discount_type == "fixed":
            discount_amount = Decimal(discount.discount_value)

        elif discount.discount_type == "nights_free":
            free_nights = int(discount.discount_value)
            if num_nights >= free_nights:
                nightly_rate = Decimal(str(pricing["nightly_rate"]))
                discount_amount = nightly_rate * free_nights

        new_total = max(original_total - discount_amount, Decimal("0"))

        pricing.update(
            {
                "discount_code": discount.code,
                "discount_amount": float(discount_amount),
                "original_total": float(original_total),
                "total": float(new_total),
            }
        )

        pricing["adjustments"].append(
            {
                "type": "discount",
                "name": f"Discount code: {discount.code}",
                "adjustment": -float(discount_amount),
            }
        )

        return pricing

    # -------------------------------
    # RATE CALENDAR
    # -------------------------------
    def get_rate_calendar(
        self, property_id: int, room_type_id: int, start_date: date, num_days: int = 30
    ) -> List[Dict]:
        calendar = []

        rate_plans = self.rate_plan_service.get_rate_plans(property_id, room_type_id)
        if not rate_plans:
            # Fall back to property-wide plans (room_type_id = NULL)
            rate_plans = self.rate_plan_service.get_rate_plans(property_id, None)

        if not rate_plans:
            return []

        default_plan = rate_plans[0]

        for i in range(num_days):
            current_date = start_date + timedelta(days=i)
            next_date = current_date + timedelta(days=1)

            try:
                rate_calc = self.rate_plan_service.calculate_rate(
                    default_plan.id, current_date, next_date
                )

                occupancy = self.calculate_occupancy_rate(property_id, current_date)

                calendar.append(
                    {
                        "date": str(current_date),
                        "day_of_week": current_date.strftime("%A"),
                        "rate": rate_calc["nightly_rate"],
                        "occupancy_rate": occupancy["occupancy_rate"],
                        "available_rooms": occupancy["available_rooms"],
                    }
                )

            except Exception:
                # ✅ Skip silently but safe
                continue

        return calendar
