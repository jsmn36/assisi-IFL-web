"""
Tests for POSDepletionService and isolation invariants.
"""
import subprocess
import sys
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.inventory.models import (
    InventoryCategory,
    InventoryItem,
    StockMovement,
)
from app.inventory.database import InventoryBase
from app.inventory.services import POSDepletionService


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


def _make_item(db, pos_menu_item_id=42, current_quantity=50):
    cat = InventoryCategory(name="F&B")
    db.add(cat)
    db.flush()
    item = InventoryItem(
        category_id=cat.id,
        name="Beer",
        sku=f"BEER-{pos_menu_item_id}",
        unit="piece",
        unit_cost=Decimal("3.00"),
        current_quantity=Decimal(str(current_quantity)),
        reorder_point=Decimal("5"),
        reorder_quantity=Decimal("50"),
        pos_menu_item_id=pos_menu_item_id,
    )
    db.add(item)
    db.flush()
    return item


def test_depletion_from_pos_order(db):
    item = _make_item(db, pos_menu_item_id=42, current_quantity=50)
    svc = POSDepletionService()
    result = svc.handle_order_sent_to_kitchen(
        db=db,
        order_id=1,
        items=[{"pos_menu_item_id": 42, "quantity": 3}],
    )
    db.refresh(item)
    assert item.current_quantity == Decimal("47")
    assert result["processed"] == 1
    assert result["skipped"] == 0
    movement = (
        db.query(StockMovement)
        .filter(
            StockMovement.item_id == item.id,
            StockMovement.reference == "POS-ORDER-1",
        )
        .first()
    )
    assert movement is not None
    assert movement.quantity_delta == Decimal("-3")


def test_unlinked_menu_item_skips_gracefully(db):
    svc = POSDepletionService()
    result = svc.handle_order_sent_to_kitchen(
        db=db,
        order_id=99,
        items=[{"pos_menu_item_id": 9999, "quantity": 5}],
    )
    assert result["skipped"] == 1
    assert result["processed"] == 0
    assert isinstance(result["errors"], list)


def _check_imports(pattern: str) -> bool:
    import os
    found = False
    base_path = "backend/app/inventory/"
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    if pattern in f.read():
                        print(f"Violation in {os.path.join(root, file)}")
                        found = True
    return found


def test_no_pms_models_imported():
    assert not _check_imports("from app.models"), "PMS model import found in inventory"


def test_no_pms_db_session_imported():
    assert not _check_imports("from app.database import get_db"), "PMS DB session import found in inventory"
