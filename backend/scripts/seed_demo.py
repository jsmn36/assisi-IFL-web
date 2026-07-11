import sys
import os
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

# Load .env BEFORE importing any app modules
from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.property import Property
from app.models.room_type import RoomType
from app.models.room import Room
from app.models.guest import Guest
from app.models.reservation import Reservation
from app.models.stay import Stay
from app.models.user import User
from app.models.enums import ReservationStatus, StayStatus, OccupancyState, ConditionState, GuestType
from app.core.security import get_password_hash

# POS Imports
from app.pos.database import POSSessionLocal, pos_engine, POSBase
from app.pos.models import Department, DepartmentType, MenuCategory, MenuItem, RestaurantTable, Order, OrderItem, OrderStatus

# Inventory Imports
from app.inventory.database import InventorySessionLocal, inventory_engine, InventoryBase
from app.inventory.models import InventoryCategory, InventoryItem, Vendor

def seed_pms(db: Session):
    print("Seeding PMS...")
    
    # 1. Users
    roles = [
        ("admin", "ADMIN", "admin123"),
        ("recep", "RECEPTIONIST", "recep123"),
        ("chef", "CHEF", "chef123"),
        ("waiter", "WAITER", "waiter123"),
        ("stock", "INVENTORY STAFF", "stock123"),
        ("finance", "ACCOUNTANT", "finance123"),
        ("sales", "SALES STAFF", "sales123"),
        ("manager", "MANAGER", "manager123"),
    ]
    
    for username, role, password in roles:
        if not db.query(User).filter(User.username == username).first():
            user = User(
                username=username,
                email=f"{username}@hotel.com",
                hashed_password=get_password_hash(password),
                role=role,
                first_name=username.capitalize(),
                last_name="Demo",
                is_active=True
            )
            db.add(user)
    
    # 2. Property
    prop = db.query(Property).first()
    if not prop:
        prop = Property(name="Grand Horizon Hotel", code="GHH", address="123 Beachfront-Ave, Miami, FL", timezone="UTC")
        db.add(prop)
        db.flush()
    
    # 3. Room Types
    rt_deluxe = db.query(RoomType).filter(RoomType.code == "DLX").first()
    if not rt_deluxe:
        rt_deluxe = RoomType(property_id=prop.id, name="Deluxe Sea View", code="DLX", base_price=Decimal("150.00"), capacity=2)
        db.add(rt_deluxe)
        
    rt_suite = db.query(RoomType).filter(RoomType.code == "SUI").first()
    if not rt_suite:
        rt_suite = RoomType(property_id=prop.id, name="Executive Suite", code="SUI", base_price=Decimal("350.00"), capacity=4)
        db.add(rt_suite)
    
    db.flush()
    
    # 4. Rooms
    if db.query(Room).count() == 0:
        for i in range(101, 111):
            db.add(Room(property_id=prop.id, room_type_id=rt_deluxe.id, room_number=str(i), floor="1", occupancy_state="vacant", condition_state="clean"))
        for i in range(201, 206):
            db.add(Room(property_id=prop.id, room_type_id=rt_suite.id, room_number=str(i), floor="2", occupancy_state="vacant", condition_state="clean"))
    
    # 5. Guests
    guest_names = [("John", "Doe"), ("Jane", "Smith"), ("Alice", "Johnson"), ("Bob", "Brown"), ("Charlie", "Davis")]
    guests = []
    for f, l in guest_names:
        g = db.query(Guest).filter(Guest.email == f"{f.lower()}.{l.lower()}@example.com").first()
        if not g:
            g = Guest(first_name=f, last_name=l, email=f"{f.lower()}.{l.lower()}@example.com", phone="123456789", guest_type=GuestType.INDIVIDUAL)
            db.add(g)
        guests.append(g)
    db.flush()
    
    # 6. Reservations (Current)
    now = datetime.now(timezone.utc)
    if db.query(Reservation).count() == 0:
        for i, g in enumerate(guests):
            res = Reservation(
                property_id=prop.id,
                guest_id=g.id,
                room_type_id=rt_deluxe.id,
                check_in_date=(now - timedelta(days=i)).date(),
                check_out_date=(now + timedelta(days=2)).date(),
                status=ReservationStatus.CHECKED_IN,
                total_amount=Decimal("300.00"),
                source="direct"
            )
            db.add(res)
            db.flush()
            
            # Create Stay
            room = db.query(Room).filter(Room.occupancy_state == "vacant").first()
            if room:
                room.occupancy_state = "occupied"
                stay = Stay(
                    reservation_id=res.id,
                    guest_id=g.id,
                    room_id=room.id,
                    check_in_time=now - timedelta(hours=5),
                    status=StayStatus.ACTIVE,
                    total_charges=Decimal("150.00")
                )
                db.add(stay)
    
    db.commit()

def seed_pos(db: Session):
    print("Seeding POS...")
    # 1. Departments
    depts = [
        ("The Blue Terrace", DepartmentType.RESTAURANT),
        ("Sky High Bar", DepartmentType.BAR),
        ("In-Room Dining", DepartmentType.ROOM_SERVICE)
    ]
    
    department_objs = []
    for name, dtype in depts:
        d = db.query(Department).filter(Department.name == name).first()
        if not d:
            d = Department(name=name, dept_type=dtype, tax_rate=Decimal("10.00"), service_charge_rate=Decimal("5.00"))
            db.add(d)
        department_objs.append(d)
    db.flush()
    
    # 2. Categories & Items
    restaurant = department_objs[0]
    cats = ["Appetizers", "Main Course", "Beverages"]
    for cat_name in cats:
        cat = db.query(MenuCategory).filter(MenuCategory.name == cat_name, MenuCategory.department_id == restaurant.id).first()
        if not cat:
            cat = MenuCategory(department_id=restaurant.id, name=cat_name)
            db.add(cat)
            db.flush()
            
            # Simple items
            for i in range(1, 4):
                item = MenuItem(
                    category_id=cat.id,
                    name=f"{cat_name} Item {i}",
                    price=Decimal(str(10 + i * 5)),
                    requires_kds=True
                )
                db.add(item)
    
    # 3. Tables
    if db.query(RestaurantTable).count() == 0:
        for i in range(1, 11):
            db.add(RestaurantTable(department_id=restaurant.id, table_number=str(i), capacity=4))
            
    db.commit()

def seed_inventory(db: Session):
    print("Seeding Inventory...")
    # 1. Vendors
    vendor_names = ["Central Grocers", "Wine & Co", "EcoSupplies"]
    for vname in vendor_names:
        if not db.query(Vendor).filter(Vendor.name == vname).first():
            db.add(Vendor(name=vname))
    db.flush()
    
    # 2. Categories
    categories = ["Food", "Beverage", "Cleaning", "Linens"]
    for cname in categories:
        if not db.query(InventoryCategory).filter(InventoryCategory.name == cname).first():
            db.add(InventoryCategory(name=cname))
    db.flush()
    
    # 3. Items
    food_cat = db.query(InventoryCategory).filter(InventoryCategory.name == "Food").first()
    if db.query(InventoryItem).count() == 0:
        items = [
            ("Tomato", "KG", "2.50", "100"),
            ("Chicken Breast", "KG", "8.00", "50"),
            ("Cooking Oil", "Liter", "4.00", "20"),
            ("Table Salt", "Box", "1.00", "10")
        ]
        for name, unit, cost, qty in items:
            db.add(InventoryItem(
                category_id=food_cat.id,
                name=name,
                sku=name.upper()[:4] + "-001",
                unit=unit,
                unit_cost=Decimal(cost),
                current_quantity=Decimal(qty),
                reorder_point=Decimal("10"),
                reorder_quantity=Decimal("50")
            )
        )
    
    db.commit()

if __name__ == "__main__":
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    POSBase.metadata.create_all(bind=pos_engine)
    InventoryBase.metadata.create_all(bind=inventory_engine)
    
    pms_db = SessionLocal()
    pos_db = POSSessionLocal()
    inv_db = InventorySessionLocal()
    
    try:
        seed_pms(pms_db)
        seed_pos(pos_db)
        seed_inventory(inv_db)
        print("\nDEMO DATA SEEDED SUCCESSFULLY!")
    finally:
        pms_db.close()
        pos_db.close()
        inv_db.close()
