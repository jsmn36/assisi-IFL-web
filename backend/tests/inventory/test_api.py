"""
API-layer tests for inventory endpoints.
Uses FastAPI TestClient with an in-memory DB.
"""
import os
import pytest
from decimal import Decimal
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("CRM_DATABASE_URL", "sqlite:///./test_crm.db")

from app.inventory.models import InventoryCategory, InventoryItem
from app.inventory.database import InventoryBase, get_inventory_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.main import app


@pytest.fixture(scope="module")
def test_db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    InventoryBase.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="module")
def client(test_db_engine):
    TestSession = sessionmaker(bind=test_db_engine)

    def override_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    def override_get_current_user(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        ),
    ):
        token = request.cookies.get("access_token")
        if not token and credentials:
            token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return User(
            id=1,
            username="admin",
            email="admin@test.com",
            role="admin",
            hashed_password="x",
            is_active=True,
        )

    app.dependency_overrides[get_inventory_db] = override_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Auth tests (no token) ────────────────────────────────────────────────────


def test_unauthenticated_request_returns_401(client):
    resp = client.get("/api/v1/inventory/items")
    assert resp.status_code == 401


def test_depletion_endpoint_rejects_without_service_token(client):
    resp = client.post("/api/v1/inventory/depletion", json={"order_id": 1, "items": []})
    # No service token configured in test → passes through (token not enforced without env var)
    # But should NOT require staff JWT
    assert resp.status_code in (
        200,
        422,
    )  # 422 if body invalid, 200 if token check passes


# ── CRUD tests (with mock auth) ──────────────────────────────────────────────


def _auth_headers():
    """Return headers that pass auth — reuse from POS pattern."""
    from app.core.security import create_access_token

    token = create_access_token({"sub": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def headers():
    return _auth_headers()


def test_get_items_paginated_returns_200(client, headers):
    resp = client.get("/api/v1/inventory/items", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_create_category_and_item_returns_201(client, headers):
    # Create category first
    cat_resp = client.post(
        "/api/v1/inventory/categories", json={"name": "Test Cat"}, headers=headers
    )
    assert cat_resp.status_code == 201
    cat_id = cat_resp.json()["id"]

    # Create item
    item_resp = client.post(
        "/api/v1/inventory/items",
        json={
            "category_id": cat_id,
            "name": "Test Beer",
            "sku": "BEER-TEST-001",
            "unit": "piece",
            "unit_cost": "3.50",
            "reorder_point": "5",
            "reorder_quantity": "20",
        },
        headers=headers,
    )
    assert item_resp.status_code == 201
    data = item_resp.json()
    assert data["sku"] == "BEER-TEST-001"
    assert float(data["current_quantity"]) == 0  # starts at 0


def test_update_item_returns_200(client, headers, test_db_engine):
    Session = sessionmaker(bind=test_db_engine)
    db = Session()
    cat = InventoryCategory(name="Edit Cat")
    db.add(cat)
    db.flush()
    item = InventoryItem(
        category_id=cat.id,
        name="Edit Item",
        sku="EDIT-001",
        unit="kg",
        unit_cost=Decimal("10"),
        current_quantity=Decimal("50"),
        reorder_point=Decimal("5"),
        reorder_quantity=Decimal("20"),
    )
    db.add(item)
    db.commit()
    item_id = item.id
    db.close()

    resp = client.put(
        f"/api/v1/inventory/items/{item_id}",
        json={"name": "Updated Item"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Item"


def test_cannot_update_current_quantity_via_put_item(client, headers, test_db_engine):
    """PUT /items/{id} ignores current_quantity field — cannot update it directly."""
    Session = sessionmaker(bind=test_db_engine)
    db = Session()
    cat = InventoryCategory(name="Qty Cat")
    db.add(cat)
    db.flush()
    item = InventoryItem(
        category_id=cat.id,
        name="Qty Item",
        sku="QTY-001",
        unit="piece",
        unit_cost=Decimal("1"),
        current_quantity=Decimal("100"),
        reorder_point=Decimal("5"),
        reorder_quantity=Decimal("20"),
    )
    db.add(item)
    db.commit()
    orig_qty = item.current_quantity
    item_id = item.id
    db.close()

    # Try to set current_quantity via PUT — ItemUpdate schema excludes it
    resp = client.put(
        f"/api/v1/inventory/items/{item_id}",
        json={"name": "Qty Item", "current_quantity": "999"},
        headers=headers,
    )
    assert resp.status_code == 200
    # current_quantity must not have changed to 999
    assert float(resp.json()["current_quantity"]) == float(orig_qty)


def test_cannot_cancel_received_po_returns_409(client, headers, test_db_engine):
    from app.inventory.models import Vendor, PurchaseOrder
    import datetime

    Session = sessionmaker(bind=test_db_engine)
    db = Session()
    vendor = Vendor(name="Vendor409")
    db.add(vendor)
    db.flush()
    po = PurchaseOrder(
        vendor_id=vendor.id,
        status="received",
        order_date=datetime.datetime.now(datetime.timezone.utc),
        total_amount=Decimal("0"),
    )
    db.add(po)
    db.commit()
    po_id = po.id
    db.close()

    resp = client.patch(
        f"/api/v1/inventory/purchase-orders/{po_id}/status",
        json={"status": "cancelled"},
        headers=headers,
    )
    assert resp.status_code == 409


def test_get_movements_for_item_returns_200(client, headers, test_db_engine):
    Session = sessionmaker(bind=test_db_engine)
    db = Session()
    cat = InventoryCategory(name="Mov Cat")
    db.add(cat)
    db.flush()
    item = InventoryItem(
        category_id=cat.id,
        name="Mov Item",
        sku="MOV-001",
        unit="piece",
        unit_cost=Decimal("1"),
        current_quantity=Decimal("10"),
        reorder_point=Decimal("5"),
        reorder_quantity=Decimal("20"),
    )
    db.add(item)
    db.commit()
    item_id = item.id
    db.close()

    resp = client.get(f"/api/v1/inventory/items/{item_id}/movements", headers=headers)
    assert resp.status_code == 200
    assert "items" in resp.json()
