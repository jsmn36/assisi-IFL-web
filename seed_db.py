from app.database import SessionLocal, engine
from app.models import Base, Room, User
from passlib.hash import bcrypt

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# 1. Add Admin User
if not db.query(User).filter(User.username == "admin").first():
    admin = User(
        username="admin",
        hashed_password=bcrypt.hash("admin123"),
        role="admin"
    )
    db.add(admin)

# 2. Add Rooms
room_data = [
    ("101", "Single", 100.0), ("102", "Single", 100.0),
    ("201", "Double", 150.0), ("202", "Double", 150.0),
    ("301", "Suite", 300.0), ("302", "Suite", 300.0),
]

for num, rtype, price in room_data:
    if not db.query(Room).filter(Room.room_number == num).first():
        room = Room(room_number=num, room_type=rtype, price_per_night=price, status="clean")
        db.add(room)

db.commit()
db.close()
print("✅ Database seeded with Admin user and 6 Rooms!")
