"""
Tests for StockMovementService and PurchaseOrderService.
Uses in-memory SQLite — no PMS DB involved.
"""
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models FIRST so metadata is populated before create_all
from app.inventory.models import (
    InventoryCategory,
    InventoryItem,
    StockMovement,
    PurchaseOrder,
    PurchaseOrderLine,
    StockAlert,
    Vendor,
)
from app.inventory.database import InventoryBase
from app.inventory.services import StockMovementService, PurchaseOrderService


@pytest.fixture(scope="function")
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    InventoryBase.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _make_item(
    db,
    name="TestItem",
    sku="SKU-001",
    current_quantity=10,
    reorder_point=5,
    reorder_quantity=20,
):
    cat = InventoryCategory(name="Test Cat")
    db.add(cat)
    db.flush()
    item = InventoryItem(
        category_id=cat.id,
        name=name,
        sku=sku,
        unit="piece",
        unit_cost=Decimal("5.00"),
        current_quantity=Decimal(str(current_quantity)),
        reorder_point=Decimal(str(reorder_point)),
        reorder_quantity=Decimal(str(reorder_quantity)),
    )
    db.add(item)
    db.flush()
    return item


# ─── StockMovementService ───────────────────────────────────────────────────


def test_purchase_increases_quantity(db):
    item = _make_item(db, current_quantity=10)
    svc = StockMovementService()
    movement = svc.record_movement(
        db=db,
        item_id=item.id,
        movement_type="purchase",
        quantity_delta=Decimal("20"),
        unit_cost=Decimal("5.00"),
        reference=None,
        notes=None,
        created_by="test",
    )
    db.refresh(item)
    assert item.current_quantity == Decimal("30")
    assert movement.movement_type == "purchase"
    assert movement.quantity_delta == Decimal("20")


def test_depletion_decreases_quantity(db):
    item = _make_item(db, current_quantity=10, reorder_point=5)
    svc = StockMovementService()
    svc.record_movement(
        db=db,
        item_id=item.id,
        movement_type="depletion",
        quantity_delta=Decimal("-3"),
        unit_cost=Decimal("5.00"),
        reference=None,
        notes=None,
        created_by="test",
    )
    db.refresh(item)
    assert item.current_quantity == Decimal("7")
    # 7 > 5 reorder point — no alert
    alerts = db.query(StockAlert).filter(StockAlert.item_id == item.id).all()
    assert len(alerts) == 0


def test_depletion_triggers_low_stock_alert(db):
    item = _make_item(db, current_quantity=6, reorder_point=5)
    svc = StockMovementService()
    svc.record_movement(
        db=db,
        item_id=item.id,
        movement_type="depletion",
        quantity_delta=Decimal("-2"),
        unit_cost=Decimal("5.00"),
        reference=None,
        notes=None,
        created_by="test",
    )
    db.refresh(item)
    assert item.current_quantity == Decimal("4")
    alert = db.query(StockAlert).filter(StockAlert.item_id == item.id).first()
    assert alert is not None
    assert alert.alert_type == "low_stock"


def test_depletion_triggers_out_of_stock_alert(db):
    item = _make_item(db, current_quantity=2, reorder_point=5)
    svc = StockMovementService()
    svc.record_movement(
        db=db,
        item_id=item.id,
        movement_type="depletion",
        quantity_delta=Decimal("-3"),
        unit_cost=Decimal("5.00"),
        reference=None,
        notes=None,
        created_by="test",
    )
    db.refresh(item)
    assert item.current_quantity == Decimal("-1")
    alert = db.query(StockAlert).filter(StockAlert.item_id == item.id).first()
    assert alert is not None
    assert alert.alert_type == "out_of_stock"


def test_alert_not_duplicated(db):
    item = _make_item(db, current_quantity=4, reorder_point=5)
    svc = StockMovementService()
    # First depletion — already below reorder_point
    svc.record_movement(
        db=db,
        item_id=item.id,
        movement_type="depletion",
        quantity_delta=Decimal("-1"),
        unit_cost=Decimal("5.00"),
        reference=None,
        notes=None,
        created_by="test",
    )
    # Second depletion
    svc.record_movement(
        db=db,
        item_id=item.id,
        movement_type="depletion",
        quantity_delta=Decimal("-1"),
        unit_cost=Decimal("5.00"),
        reference=None,
        notes=None,
        created_by="test",
    )
    unacked = (
        db.query(StockAlert)
        .filter(
            StockAlert.item_id == item.id,
            StockAlert.acknowledged_at.is_(None),
        )
        .count()
    )
    # Should be at most 1 unacknowledged alert (may escalate to out_of_stock but not duplicate low_stock)
    assert unacked <= 1


def test_receive_purchase_order_updates_status_received(db):
    vendor = Vendor(name="Acme")
    db.add(vendor)
    db.flush()
    item = _make_item(db, current_quantity=0)

    po = PurchaseOrder(
        vendor_id=vendor.id,
        status="sent",
        order_date=datetime.now(timezone.utc),
        total_amount=Decimal("100"),
    )
    db.add(po)
    db.flush()

    line1 = PurchaseOrderLine(
        purchase_order_id=po.id,
        item_id=item.id,
        quantity_ordered=Decimal("10"),
        quantity_received=Decimal("0"),
        unit_cost=Decimal("5"),
    )
    line2 = PurchaseOrderLine(
        purchase_order_id=po.id,
        item_id=item.id,
        quantity_ordered=Decimal("10"),
        quantity_received=Decimal("0"),
        unit_cost=Decimal("5"),
    )
    db.add_all([line1, line2])
    db.flush()

    svc = StockMovementService()
    result = svc.receive_purchase_order(
        db,
        po.id,
        [
            {
                "purchase_order_line_id": line1.id,
                "quantity_received": Decimal("10"),
                "unit_cost": Decimal("5"),
            },
            {
                "purchase_order_line_id": line2.id,
                "quantity_received": Decimal("10"),
                "unit_cost": Decimal("5"),
            },
        ],
    )
    assert result.status == "received"
    assert result.received_date is not None


def test_receive_purchase_order_partial(db):
    vendor = Vendor(name="Acme")
    db.add(vendor)
    db.flush()
    item = _make_item(db, current_quantity=0, sku="SKU-P")

    po = PurchaseOrder(
        vendor_id=vendor.id,
        status="sent",
        order_date=datetime.now(timezone.utc),
        total_amount=Decimal("100"),
    )
    db.add(po)
    db.flush()

    line1 = PurchaseOrderLine(
        purchase_order_id=po.id,
        item_id=item.id,
        quantity_ordered=Decimal("10"),
        quantity_received=Decimal("0"),
        unit_cost=Decimal("5"),
    )
    line2 = PurchaseOrderLine(
        purchase_order_id=po.id,
        item_id=item.id,
        quantity_ordered=Decimal("10"),
        quantity_received=Decimal("0"),
        unit_cost=Decimal("5"),
    )
    db.add_all([line1, line2])
    db.flush()

    svc = StockMovementService()
    result = svc.receive_purchase_order(
        db,
        po.id,
        [
            {
                "purchase_order_line_id": line1.id,
                "quantity_received": Decimal("10"),
                "unit_cost": Decimal("5"),
            },
            # line2 not received
        ],
    )
    assert result.status == "partial"


def test_stock_movement_service_has_no_update_method():
    """StockMovement is append-only — no update method on service."""
    svc = StockMovementService()
    assert not hasattr(svc, "update_movement")
    assert not hasattr(svc, "delete_movement")
