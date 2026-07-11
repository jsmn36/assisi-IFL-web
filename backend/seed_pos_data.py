import os
import sys
from decimal import Decimal

# Add backend to path so imports work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.inventory.database import get_inventory_db, init_inventory_db
from app.pos.database import get_pos_db, init_pos_db
from app.inventory.models import InventoryCategory, InventoryItem, Vendor, RecipeIngredient
from app.pos.models import Department, MenuCategory, MenuItem, RestaurantTable

def seed_pos():
    print("Initializing POS & Inventory DBs...")
    init_pos_db()
    init_inventory_db()

    # We need sessions
    pos_gen = get_pos_db()
    pos_db = next(pos_gen)

    inv_gen = get_inventory_db()
    inv_db = next(inv_gen)

    try:
        # 1. Create POS Departments
        print("Seeding POS Departments...")
        rest = pos_db.query(Department).filter_by(name="The Grand Restaurant").first()
        if not rest:
            rest = Department(name="The Grand Restaurant", tax_rate=0.05, service_charge_rate=0.10)
            pos_db.add(rest)
            pos_db.commit()
            pos_db.refresh(rest)

        bar = pos_db.query(Department).filter_by(name="Skyline Bar").first()
        if not bar:
            bar = Department(name="Skyline Bar", tax_rate=0.18, service_charge_rate=0.10)
            pos_db.add(bar)
            pos_db.commit()
            pos_db.refresh(bar)

        # 2. Create POS Categories
        print("Seeding POS Categories...")
        starters = pos_db.query(MenuCategory).filter_by(name="Starters", department_id=rest.id).first()
        if not starters:
            starters = MenuCategory(department_id=rest.id, name="Starters", display_order=1)
            pos_db.add(starters)

        mains = pos_db.query(MenuCategory).filter_by(name="Main Course", department_id=rest.id).first()
        if not mains:
            mains = MenuCategory(department_id=rest.id, name="Main Course", display_order=2)
            pos_db.add(mains)

        cocktails = pos_db.query(MenuCategory).filter_by(name="Signature Cocktails", department_id=bar.id).first()
        if not cocktails:
            cocktails = MenuCategory(department_id=bar.id, name="Signature Cocktails", display_order=1)
            pos_db.add(cocktails)

        pos_db.commit()

        # 3. Create Inventory Category & Items
        print("Seeding Inventory Items...")
        food_cat = inv_db.query(InventoryCategory).filter_by(name="Food & Beverage").first()
        if not food_cat:
            food_cat = InventoryCategory(name="Food & Beverage")
            inv_db.add(food_cat)
            inv_db.commit()
            inv_db.refresh(food_cat)

        vendor = inv_db.query(Vendor).filter_by(name="Local Farms").first()
        if not vendor:
            vendor = Vendor(name="Local Farms", contact_name="Farmer Joe")
            inv_db.add(vendor)
            inv_db.commit()
            inv_db.refresh(vendor)

        # Base Ingredients
        inventory_data = [
            ("L001", "Pasta (Penne)", "kg", 150.00, 50.00),
            ("L002", "Truffle Oil", "liter", 1200.00, 5.00),
            ("L003", "Bourbon Whiskey", "ml", 2.50, 10000.00),  # price per ml
            ("L004", "Angostura Bitters", "dash", 1.00, 1000.00),
            ("L005", "Sugar Cubes", "piece", 0.50, 2000.00),
            ("L006", "Coke (Can)", "box", 12.00, 100.00),
        ]

        inv_items_map = {}
        for sku, name, unit, cost, qty in inventory_data:
            item = inv_db.query(InventoryItem).filter_by(sku=sku).first()
            if not item:
                item = InventoryItem(
                    sku=sku, name=name, unit=unit, unit_cost=Decimal(str(cost)), 
                    current_quantity=Decimal(str(qty)), category_id=food_cat.id,
                    vendor_id=vendor.id, reorder_point=Decimal("5.0"), reorder_quantity=Decimal("10.0")
                )
                inv_db.add(item)
            inv_items_map[sku] = item

        inv_db.commit()

        # 4. Create POS Menu Items & Link Recipes
        print("Seeding POS Menu Items & Recipes...")
        
        # Truffle Penne Pasta
        pasta_item = pos_db.query(MenuItem).filter_by(name="Truffle Penne Pasta").first()
        if not pasta_item:
            pasta_item = MenuItem(category_id=mains.id, name="Truffle Penne Pasta", price=Decimal("450.00"), requires_kds=True)
            pos_db.add(pasta_item)
            pos_db.commit()
            pos_db.refresh(pasta_item)

            # Recipe
            inv_db.add(RecipeIngredient(pos_menu_item_id=pasta_item.id, inventory_item_id=inv_items_map["L001"].id, quantity=Decimal("0.150")))  # 150g
            inv_db.add(RecipeIngredient(pos_menu_item_id=pasta_item.id, inventory_item_id=inv_items_map["L002"].id, quantity=Decimal("0.010")))  # 10ml

        # Old Fashioned
        of_item = pos_db.query(MenuItem).filter_by(name="Smoked Old Fashioned").first()
        if not of_item:
            of_item = MenuItem(category_id=cocktails.id, name="Smoked Old Fashioned", price=Decimal("650.00"), requires_kds=True)
            pos_db.add(of_item)
            pos_db.commit()
            pos_db.refresh(of_item)

            # Recipe
            inv_db.add(RecipeIngredient(pos_menu_item_id=of_item.id, inventory_item_id=inv_items_map["L003"].id, quantity=Decimal("60.0")))  # 60ml
            inv_db.add(RecipeIngredient(pos_menu_item_id=of_item.id, inventory_item_id=inv_items_map["L004"].id, quantity=Decimal("1.0")))   # 1 dash
            inv_db.add(RecipeIngredient(pos_menu_item_id=of_item.id, inventory_item_id=inv_items_map["L005"].id, quantity=Decimal("1.0")))   # 1 cube

        # Direct mapped item (Coke)
        coke_item = pos_db.query(MenuItem).filter_by(name="Classic Coke").first()
        if not coke_item:
            coke_item = MenuItem(category_id=cocktails.id, name="Classic Coke", price=Decimal("120.00"), requires_kds=False)
            pos_db.add(coke_item)
            pos_db.commit()
            pos_db.refresh(coke_item)
            
            # Map directly via pos_menu_item_id on InventoryItem
            inv_items_map["L006"].pos_menu_item_id = coke_item.id

        pos_db.commit()
        inv_db.commit()

        # 5. Create Tables
        print("Seeding Tables...")
        for i in range(1, 11):
            num = f"R{i}"
            if not pos_db.query(RestaurantTable).filter_by(table_number=num).first():
                pos_db.add(RestaurantTable(department_id=rest.id, table_number=num, capacity=4))
        
        for i in range(1, 6):
            num = f"B{i}"
            if not pos_db.query(RestaurantTable).filter_by(table_number=num).first():
                pos_db.add(RestaurantTable(department_id=bar.id, table_number=num, capacity=2))
        
        pos_db.commit()
        print("SUCCESS: POS & Inventory database seeded with high-quality data.")

    except Exception as e:
        print(f"ERROR: {e}")
        pos_db.rollback()
        inv_db.rollback()
    finally:
        pos_db.close()
        inv_db.close()

if __name__ == "__main__":
    seed_pos()
