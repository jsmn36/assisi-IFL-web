from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.cm import schemas as cm_schemas

router = APIRouter(prefix="/pms/integration", tags=["Integration"])


@router.post("/ingest", status_code=status.HTTP_200_OK)
def ingest_reservation(
    proposal: cm_schemas.ReservationProposal, db: Session = Depends(get_db)
):
    """
    CM proposes a booking to PMS for validation.
    Enforces CM-INV-004.
    """
    try:
        # 1. Resolve guest (get or create)
        from app.models.guest import Guest

        guest = (
            db.query(Guest).filter(Guest.email == proposal.guest_email).first()
            if proposal.guest_email
            else None
        )
        if not guest:
            names = proposal.guest_name.split(" ", 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else "Unknown"
            guest = Guest(
                first_name=first_name,
                last_name=last_name,
                email=proposal.guest_email,
                phone=proposal.guest_phone,
            )
            db.add(guest)
            db.flush()

        # We need a property_id (int). Using default 1 for this MVP mapping since CM has UUIDs.
        pms_property_id = 1

        # 2. Check availability (would normally use locks here, e.g., SELECT FOR UPDATE)
        # ReservationConfirmationGate logic
        from app.models.room_type import RoomType

        room_type = (
            db.query(RoomType).filter(RoomType.id == proposal.room_type_id).first()
        )

        from app.models.reservation import Reservation
        from app.models.enums import ReservationStatus, ReservationSource
        import uuid
        from decimal import Decimal

        nights = max((proposal.check_out - proposal.check_in).days, 1)
        nightly_rate = room_type.base_price if room_type else Decimal("100.00")

        db_res = Reservation(
            property_id=pms_property_id,
            guest_id=guest.id,
            room_type_id=proposal.room_type_id,
            confirmation_number=f"RES-{uuid.uuid4().hex[:8].upper()}",
            check_in_date=proposal.check_in,
            check_out_date=proposal.check_out,
            number_of_nights=nights,
            num_adults=proposal.guests,
            nightly_rate=nightly_rate,
            total_amount=nightly_rate * nights,
            status=ReservationStatus.CONFIRMED,  # Auto confirmed by PMS gate
            source=ReservationSource.OTA
            if proposal.channel in ["booking_com", "expedia"]
            else ReservationSource.DIRECT,
            internal_notes=f"Correlation ID: {proposal.correlation_id}",
            notes=f"External Reference: {proposal.external_reference}",
        )

        def _action(session):
            session.add(db_res)
            # DO NOT invoke commit here. TransactionCoordinator handles it.

        context = {
            "proposal": proposal,
            "guest": guest,
            "room_type": room_type,
            "operation": "pms_integration_ingest",
            "triggered_by": "channel_manager",
        }

        from app.gates.__init__ import (
            IngressGate,
            IdentityGate,
            InventoryGate,
            RateGate,
            ConfirmGate,
            InStayGate,
            NightAuditGate,
            OverrideGate,
            DayCloseGate,
        )

        gates = [
            IngressGate(),
            IdentityGate(),
            InventoryGate(),
            RateGate(),
            ConfirmGate(),
            InStayGate(),
            NightAuditGate(),
            OverrideGate(),
            DayCloseGate(),
        ]

        from app.core.transaction_coordinator import TransactionCoordinator

        tc = TransactionCoordinator(db)
        success, exec_result = tc.execute_write(gates, context, _action)

        if not success:
            failures = [
                f"{r.gate_name}: {r.message}" for r in exec_result.get_failures()
            ]
            return {
                "success": False,
                "error_code": "GATE_REJECTION",
                "message": "Gating failed: " + " | ".join(failures),
            }

        db.refresh(db_res)

        return {
            "success": True,
            "reservation_id": db_res.id,
            "confirmation_code": db_res.confirmation_number,
            "message": "Reservation confirmed",
        }
    except Exception as e:
        # Standard fallback for catastrophic action failures
        db.rollback()
        return {"success": False, "error_code": "INTERNAL_ERROR", "message": str(e)}
