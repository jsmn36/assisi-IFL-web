"""
Seed Users Script
Create initial users for testing
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.auth_service import AuthService


def seed_users():
    """Create initial users"""
    db: Session = SessionLocal()
    service = AuthService(db)

    users = [
        {
            "username": "admin",
            "email": "admin@pmshotel.com",
            "password": "admin123",
            "role": "admin",
            "first_name": "Admin",
            "last_name": "User",
        },
        {
            "username": "manager",
            "email": "manager@pmshotel.com",
            "password": "manager123",
            "role": "manager",
            "first_name": "Manager",
            "last_name": "User",
        },
        {
            "username": "frontdesk",
            "email": "frontdesk@pmshotel.com",
            "password": "frontdesk123",
            "role": "front_desk",
            "first_name": "Front Desk",
            "last_name": "User",
        },
        {
            "username": "housekeeper",
            "email": "housekeeper@pmshotel.com",
            "password": "housekeeper123",
            "role": "housekeeper",
            "first_name": "Housekeeper",
            "last_name": "User",
        },
        {
            "username": "maintenance",
            "email": "maintenance@pmshotel.com",
            "password": "maintenance123",
            "role": "maintenance",
            "first_name": "Maintenance",
            "last_name": "User",
        },
        {
            "username": "accountant",
            "email": "accountant@pmshotel.com",
            "password": "accountant123",
            "role": "accountant",
            "first_name": "Accountant",
            "last_name": "User",
        },
        {
            "username": "staff",
            "email": "staff@pmshotel.com",
            "password": "staff123",
            "role": "staff",
            "first_name": "Staff",
            "last_name": "User",
        },
    ]

    print("Creating users...")
    for user_data in users:
        try:
            user = service.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password=user_data["password"],
                role=user_data["role"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                created_by="system",
            )
            print(f"✅ Created user: {user.username} ({user.role})")
        except ValueError as e:
            print(f"⚠️  User {user_data['username']} already exists")

    db.close()
    print("\n✅ User seeding complete!")
    print("\nDemo Credentials:")
    print("─" * 50)
    for user_data in users:
        print(
            f"{user_data['username']:15} / {user_data['password']:15} ({user_data['role']})"
        )
    print("─" * 50)


if __name__ == "__main__":
    seed_users()
