import sys
import os
import random
from datetime import date, timedelta
from decimal import Decimal

# Add the backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.accounting.database import SessionLocal
from app.accounting.chart_of_accounts import seed_chart_of_accounts
from app.accounting.services.journal_service import JournalService
from app.accounting.models import EntrySource

def seed_accounting_data():
    db = SessionLocal()
    try:
        print("--- Seeding Chart of Accounts ---")
        seed_chart_of_accounts(db, force=False)
        
        service = JournalService(db)
        
        # Seed for last 30 days
        today = date.today()
        print(f"--- Generating Night Audit entries for the last 30 days ---")
        
        for i in range(30, 0, -1):
            audit_date = today - timedelta(days=i)
            
            # Random but realistic hospitality numbers
            room_revenue = Decimal(random.randint(2000, 5000)).quantize(Decimal("0.01"))
            fb_revenue = Decimal(random.randint(500, 1500)).quantize(Decimal("0.01"))
            spa_revenue = Decimal(random.randint(100, 400)).quantize(Decimal("0.01"))
            other_revenue = Decimal(random.randint(50, 150)).quantize(Decimal("0.01"))
            
            room_tax = (room_revenue * Decimal("0.12")).quantize(Decimal("0.01"))
            other_tax = ((fb_revenue + spa_revenue + other_revenue) * Decimal("0.08")).quantize(Decimal("0.01"))
            
            # Assume 95% of revenue is paid same day
            total_payments = ((room_revenue + fb_revenue + spa_revenue + other_revenue + room_tax + other_tax) * Decimal("0.95")).quantize(Decimal("0.01"))
            
            try:
                service.generate_night_audit_entry(
                    audit_date=audit_date,
                    room_revenue=room_revenue,
                    fb_revenue=fb_revenue,
                    spa_revenue=spa_revenue,
                    other_revenue=other_revenue,
                    room_tax=room_tax,
                    other_tax=other_tax,
                    total_payments=total_payments,
                    created_by="seeder"
                )
                print(f"  [+] Seeded entry for {audit_date}")
            except Exception as e:
                print(f"  [!] Skipped {audit_date}: {e}")

        # Seed some operating expenses for the current month
        print("--- Seeding Operating Expenses ---")
        opex_entries = [
            {"code": "6000", "name": "Monthly Salaries", "amount": 15000, "description": "Staff Payroll - Base"},
            {"code": "6100", "name": "Electricity & Water", "amount": 2400, "description": "Utility Bill - March"},
            {"code": "6300", "name": "Google Ads", "amount": 1200, "description": "Search Marketing Campaign"},
            {"code": "6600", "name": "Office Supplies", "amount": 450, "description": "Stationery and Toner"},
        ]
        
        for opex in opex_entries:
            try:
                service.create_entry(
                    entry_date=today.replace(day=1),
                    description=opex["description"],
                    lines=[
                        {"debit_code": opex["code"], "credit_code": "1000", "amount": opex["amount"]}
                    ],
                    source=EntrySource.MANUAL,
                    created_by="seeder",
                    auto_post=True
                )
                print(f"  [+] Seeded OpEx: {opex['name']}")
            except Exception as e:
                print(f"  [!] Skipped OpEx {opex['name']}: {e}")

        print("--- Accounting Seeding Complete ---")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_accounting_data()
