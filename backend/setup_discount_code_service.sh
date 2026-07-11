#!/bin/bash

cd ~/pms-hotel-desktop/backend

cat > app/services/discount_code_service.py << 'EOF'
"""
DiscountCodeService
Manages discount codes and promotions
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from app.services.base_service import BaseService, ValidationError, BusinessRuleError
from app.models import DiscountCode, Property, Guest
import secrets
import string


class DiscountCodeService(BaseService):
    """
    Service for discount codes

    Methods:
        - create_discount_code: Create new discount code
        - validate_discount_code: Validate code for use
        - apply_discount_code: Apply code to reservation
        - get_discount_codes: Get all codes
        - deactivate_code: Deactivate code
    """

    def create_discount_code(
        self,
        property_id: int,
        code: str,
        description: str,
        discount_type: str,
        discount_value: Decimal,
        min_nights: int = 1,
        min_amount: Optional[Decimal] = None,
        max_uses: Optional[int] = None,
        max_uses_per_guest: int = 1,
        valid_from: Optional[date] = None,
        valid_until: Optional[date] = None,
        created_by: Optional[str] = None
    ) -> DiscountCode:
        """
        Create discount code

        Args:
            property_id: Property ID
            code: Discount code (must be unique)
            description: Code description
            discount_type: percentage, fixed, nights_free
            discount_value: Discount amount
            min_nights: Minimum nights required
            min_amount: Minimum booking amount
            max_uses: Maximum total uses
            max_uses_per_guest: Max uses per guest
            valid_from: Start date
            valid_until: End date
            created_by: User creating

        Returns:
            Created discount code
        """
        # Verify property exists
        self.get_or_404(Property, property_id)

        # Validate code format
        code = code.upper().strip()
        if not code or len(code) < 3:
            raise ValidationError("Code must be at least 3 characters")

        # Check for duplicate
        existing = self.db.query(DiscountCode).filter(
            DiscountCode.code == code
        ).first()

        if existing:
            raise ValidationError(f"Discount code '{code}' already exists")

        # Validate discount type
        if discount_type not in ["percentage", "fixed", "nights_free"]:
            raise ValidationError("Invalid discount type")

        # Validate discount value
        if discount_value <= 0:
            raise ValidationError("Discount value must be positive")

        if discount_type == "percentage" and discount_value > 100:
            raise ValidationError("Percentage discount cannot exceed 100%")

        # Validate dates
        if valid_from and valid_until and valid_until <= valid_from:
            raise ValidationError("End date must be after start date")

        discount_code = DiscountCode(
            property_id=property_id,
            code=code,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            min_nights=min_nights,
            min_amount=min_amount,
            max_uses=max_uses,
            max_uses_per_guest=max_uses_per_guest,
            valid_from=valid_from,
            valid_until=valid_until,
            created_by=created_by
        )

        self.db.add(discount_code)
        self.commit()
        self.refresh(discount_code)

        self._log_action("create_discount_code", "discount_code", discount_code.id, created_by)

        return discount_code

    def generate_discount_code(
        self,
        property_id: int,
        prefix: str = "PROMO",
        length: int = 8
    ) -> str:
        """
        Generate random unique discount code

        Args:
            property_id: Property ID
            prefix: Code prefix
            length: Code length (excluding prefix)

        Returns:
            Generated code
        """
        while True:
            chars = string.ascii_uppercase + string.digits
            random_part = ''.join(secrets.choice(chars) for _ in range(length))
            code = f"{prefix}{random_part}"

            existing = self.db.query(DiscountCode).filter(
                DiscountCode.code == code
            ).first()

            if not existing:
                return code

    def validate_discount_code(
        self,
        property_id: int,
        code: str,
        booking_amount: Decimal,
        num_nights: int,
        guest_id: Optional[int] = None
    ) -> dict:
        """
        Validate discount code for use

        Args:
            property_id: Property ID
            code: Discount code
            booking_amount: Total booking amount
            num_nights: Number of nights
            guest_id: Optional guest ID

        Returns:
            Validation result with discount details
        """
        code = code.upper().strip()

        discount = self.db.query(DiscountCode).filter(
            DiscountCode.property_id == property_id,
            DiscountCode.code == code
        ).first()

        if not discount:
            return {"valid": False, "error": "Discount code not found"}

        if not discount.is_active:
            return {"valid": False, "error": "Discount code is no longer active"}

        today = date.today()
        if discount.valid_from and today < discount.valid_from:
            return {"valid": False, "error": f"Code not valid until {discount.valid_from}"}

        if discount.valid_until and today > discount.valid_until:
            return {"valid": False, "error": "Code has expired"}

        if discount.max_uses and discount.uses_count >= discount.max_uses:
            return {"valid": False, "error": "Code has reached maximum uses"}

        if num_nights < discount.min_nights:
            return {"valid": False, "error": f"Minimum {discount.min_nights} nights required"}

        if discount.min_amount and booking_amount < discount.min_amount:
            return {"valid": False, "error": f"Minimum booking amount ${discount.min_amount} required"}

        if guest_id and discount.max_uses_per_guest:
            from app.models import Reservation
            guest_uses = self.db.query(Reservation).filter(
                Reservation.guest_id == guest_id,
                Reservation.discount_code == code
            ).count()

            if guest_uses >= discount.max_uses_per_guest:
                return {"valid": False, "error": "You have already used this code"}

        discount_amount = self._calculate_discount_amount(
            discount,
            booking_amount,
            num_nights
        )

        return {
            "valid": True,
            "discount_code": discount,
            "discount_amount": float(discount_amount),
            "new_total": float(booking_amount - discount_amount),
            "discount_type": discount.discount_type,
            "discount_value": float(discount.discount_value)
        }

    def apply_discount_code(
        self,
        discount_id: int,
        guest_id: Optional[int] = None
    ) -> DiscountCode:
        """
        Apply discount code (increment usage count)

        Args:
            discount_id: Discount code ID
            guest_id: Optional guest ID

        Returns:
            Updated discount code
        """
        discount = self.get_or_404(DiscountCode, discount_id)
        discount.uses_count += 1
        self.commit()
        self.refresh(discount)
        return discount

    def _calculate_discount_amount(
        self,
        discount: DiscountCode,
        booking_amount: Decimal,
        num_nights: int
    ) -> Decimal:
        """Calculate discount amount"""
        if discount.discount_type == "percentage":
            return booking_amount * (discount.discount_value / 100)
        elif discount.discount_type == "fixed":
            return min(discount.discount_value, booking_amount)
        elif discount.discount_type == "nights_free":
            nightly_rate = booking_amount / num_nights
            free_nights = min(int(discount.discount_value), num_nights)
            return nightly_rate * free_nights

        return Decimal("0")

    def get_discount_codes(
        self,
        property_id: int,
        active_only: bool = True
    ) -> List[DiscountCode]:
        """Get all discount codes"""
        query = self.db.query(DiscountCode).filter(
            DiscountCode.property_id == property_id
        )

        if active_only:
            query = query.filter(DiscountCode.is_active == True)

        return query.order_by(DiscountCode.created_at.desc()).all()

    def deactivate_code(
        self,
        discount_id: int,
        deactivated_by: str
    ) -> DiscountCode:
        """Deactivate discount code"""
        discount = self.get_or_404(DiscountCode, discount_id)
        discount.is_active = False
        self.commit()
        self.refresh(discount)
        self._log_action("deactivate_discount_code", "discount_code", discount_id, deactivated_by)
        return discount
EOF

echo "✅ Discount code service created"
