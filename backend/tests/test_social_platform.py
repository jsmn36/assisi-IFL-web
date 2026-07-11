import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.user import User
from app.models.institution import InstitutionProfile
from app.models.post import Post
from app.core.security import create_access_token, get_password_hash

from app.database import get_db as db_get_db
from app.api.dependencies import get_db as dep_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_db(test_db):
    client.cookies.clear()
    app.dependency_overrides[db_get_db] = lambda: test_db
    app.dependency_overrides[dep_get_db] = lambda: test_db
    yield
    app.dependency_overrides.pop(db_get_db, None)
    app.dependency_overrides.pop(dep_get_db, None)

@pytest.fixture
def seed_data(test_db: Session):
    # Create super admin
    admin = User(
        username="superadmin",
        email="admin@assisi.edu",
        hashed_password=get_password_hash("adminpass"),
        role="admin",
        is_active=True,
        is_superuser=True
    )
    test_db.add(admin)

    # Create institution user
    inst_user = User(
        username="assisi_eng",
        email="contact@assisi.edu",
        hashed_password=get_password_hash("instpass"),
        role="institution",
        is_active=True
    )
    test_db.add(inst_user)
    test_db.commit()

    # Create institution profile
    profile = InstitutionProfile(
        user_id=inst_user.id,
        name="Assisi Engineering College",
        about="Leading center for scientific and technical education.",
        contact_email="contact@assisi.edu",
        phone="+91 99999 88888",
        website_url="https://assisi.edu"
    )
    test_db.add(profile)

    # Create posts
    post1 = Post(
        title="Welcome to Campus",
        content="We are thrilled to welcome our new batch of engineering students!",
        type="news",
        hashtags="welcome, engineering",
        institution_id=inst_user.id,
        is_pinned=True
    )
    post2 = Post(
        title="Holiday Notice",
        content="Please note that campus will remain closed on Friday for the annual college fest preparations.",
        type="notice",
        hashtags="notice, fest",
        institution_id=inst_user.id,
        is_pinned=False
    )
    test_db.add(post1)
    test_db.add(post2)
    test_db.commit()

    return {
        "admin": admin,
        "inst_user": inst_user,
        "profile": profile,
        "post1": post1,
        "post2": post2
    }

def test_login(test_db: Session, seed_data):
    # Happy path
    response = client.post("/api/v1/auth/login", json={
        "username": "assisi_eng",
        "password": "instpass"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "institution"

    # Invalid password
    response = client.post("/api/v1/auth/login", json={
        "username": "assisi_eng",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_public_institutions_listing(test_db: Session, seed_data):
    response = client.get("/api/v1/institutions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Assisi Engineering College"

def test_public_posts_feed(test_db: Session, seed_data):
    # Get all posts
    response = client.get("/api/v1/posts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Welcome to Campus" # Should be ordered by is_pinned first

    # Filtering by type
    response = client.get("/api/v1/posts?type=notice")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Holiday Notice"

    # Search keyword
    response = client.get("/api/v1/posts?search=welcome")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Welcome to Campus"

def test_create_and_manage_post(test_db: Session, seed_data):
    inst_token = create_access_token(data={"sub": str(seed_data["inst_user"].id), "role": "institution"})
    headers = {"Authorization": f"Bearer {inst_token}"}

    # Create new post
    response = client.post("/api/v1/posts", json={
        "title": "Semester Registration",
        "content": "Make sure to register for courses before Saturday night.",
        "type": "event",
        "hashtags": "semester, courses"
    }, headers=headers)
    assert response.status_code == 201
    post_data = response.json()
    assert post_data["title"] == "Semester Registration"

    # Update post
    response = client.put(f"/api/v1/posts/{post_data['id']}", json={
        "title": "Updated Semester Registration",
        "content": "Registrations extended till Sunday night!"
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Semester Registration"

    # Delete post
    response = client.delete(f"/api/v1/posts/{post_data['id']}", headers=headers)
    assert response.status_code == 204

def test_update_institution_profile(test_db: Session, seed_data):
    inst_token = create_access_token(data={"sub": str(seed_data["inst_user"].id), "role": "institution"})
    headers = {"Authorization": f"Bearer {inst_token}"}

    response = client.put(f"/api/v1/institutions/{seed_data['profile'].id}", json={
        "name": "Assisi University of Technology",
        "phone": "+91 12345 67890"
    }, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Assisi University of Technology"

def test_admin_provision_and_analytics(test_db: Session, seed_data):
    admin_token = create_access_token(data={"sub": str(seed_data["admin"].id), "role": "admin"})
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Register new institution
    response = client.post("/api/v1/admin/institutions", json={
        "username": "assisi_arts",
        "email": "arts@assisi.edu",
        "password": "artspassword",
        "name": "Assisi Arts College",
        "about": "Premier institute for humanities.",
        "phone": "+91 88888 77777",
        "website_url": "https://arts.assisi.edu"
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Assisi Arts College"

    # Check analytics
    response = client.get("/api/v1/admin/analytics", headers=headers)
    assert response.status_code == 200
    analytics_data = response.json()
    assert analytics_data["total_institutions"] == 2
    assert analytics_data["total_posts"] == 2

def test_student_registration_and_flow(test_db: Session, seed_data):
    # Register valid admission number
    from app.models.student import StudentAdmission
    test_db.add(StudentAdmission(admission_number="2026-001", student_name="Alice Student", is_registered=False))
    test_db.commit()

    # Try registering student - happy path
    response = client.post("/api/v1/auth/register-student", json={
        "username": "alice",
        "email": "alice@assisi.edu",
        "password": "studentpassword",
        "admission_number": "2026-001",
        "student_name": "Alice Student",
        "class_or_department": "Computer Science"
    })
    assert response.status_code == 200
    
    # Registration creates user in pending state. Log in should fail initially
    response = client.post("/api/v1/auth/login", json={
        "username": "alice",
        "password": "studentpassword"
    })
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

    # Let Admin approve student
    admin_token = create_access_token(data={"sub": str(seed_data["admin"].id), "role": "admin"})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # List pending
    response = client.get("/api/v1/admin/pending-students", headers=admin_headers)
    assert response.status_code == 200
    pending_list = response.json()
    assert len(pending_list) == 1
    student_user_id = pending_list[0]["id"]

    # Approve student
    response = client.post(f"/api/v1/admin/students/{student_user_id}/approve", headers=admin_headers)
    assert response.status_code == 200

    # Log in should now succeed
    response = client.post("/api/v1/auth/login", json={
        "username": "alice",
        "password": "studentpassword"
    })
    assert response.status_code == 200
    alice_token = response.json()["access_token"]
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    client.cookies.clear()

    # Verify student profile retrieved
    response = client.get("/api/v1/students/profile/alice", headers=alice_headers)
    assert response.status_code == 200
    assert response.json()["student_name"] == "Alice Student"

    # Create another student
    test_db.add(StudentAdmission(admission_number="2026-002", student_name="Bob Student", is_registered=False))
    test_db.commit()
    response = client.post("/api/v1/auth/register-student", json={
        "username": "bob",
        "email": "bob@assisi.edu",
        "password": "bobpassword",
        "admission_number": "2026-002",
        "student_name": "Bob Student"
    })
    # Query Bob user ID directly from DB
    bob_user = test_db.query(User).filter(User.username == "bob").first()
    bob_user_id = bob_user.id
    # Auto-approve Bob via admin
    approve_resp = client.post(f"/api/v1/admin/students/{bob_user_id}/approve", headers=admin_headers)
    assert approve_resp.status_code == 200, f"Approve Bob failed: {approve_resp.status_code} {approve_resp.text}"

    # Bob logs in
    response = client.post("/api/v1/auth/login", json={
        "username": "bob",
        "password": "bobpassword"
    })
    bob_token = response.json()["access_token"]
    bob_headers = {"Authorization": f"Bearer {bob_token}"}
    client.cookies.clear()

    # Alice follows Bob
    response = client.post(f"/api/v1/students/follow/{bob_user_id}", headers=alice_headers)
    assert response.status_code == 200

    # Verify followers list
    response = client.get(f"/api/v1/students/followers/{bob_user_id}", headers=bob_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["username"] == "alice"

    # Alice unfollows Bob
    response = client.post(f"/api/v1/students/unfollow/{bob_user_id}", headers=alice_headers)
    assert response.status_code == 200

    # DM Chat between Alice and Bob
    response = client.post("/api/v1/chat/send", json={"receiver_id": bob_user_id, "content": "Hi Bob!"}, headers=alice_headers)
    assert response.status_code == 201

    response = client.get(f"/api/v1/chat/history/{student_user_id}", headers=bob_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["content"] == "Hi Bob!"

    # Stories & Highlights
    response = client.post("/api/v1/stories", json={
        "media_url": "https://images.unsplash.com/photo-1518156677180-95a2893f3e9f"
    }, headers=alice_headers)
    assert response.status_code == 201
    story_id = response.json()["id"]

    # Create Highlight
    response = client.post("/api/v1/highlights", json={
        "name": "Academics",
        "cover_url": "https://images.unsplash.com/photo-1518156677180-95a2893f3e9f",
        "story_ids": [story_id]
    }, headers=alice_headers)
    assert response.status_code == 201

    # Classrooms and Collaboration Groups
    response = client.post("/api/v1/groups", json={
        "name": "Maths 101",
        "description": "Calculus and linear algebra",
        "is_classroom": True,
        "class_or_department": "Maths"
    }, headers=alice_headers)
    assert response.status_code == 201
    group_id = response.json()["id"]

    # Bob joins the group
    response = client.post(f"/api/v1/groups/{group_id}/join", headers=bob_headers)
    assert response.status_code == 200

    # Alice posts assignment
    response = client.post(f"/api/v1/groups/{group_id}/assignments", json={
        "title": "Homework 1",
        "description": "Solve Chapter 2 questions",
        "due_date": "2026-08-01T23:59:59"
    }, headers=alice_headers)
    assert response.status_code == 201

    # Alice schedules classroom event
    response = client.post(f"/api/v1/groups/{group_id}/events", json={
        "title": "Exam Review session",
        "description": "Classroom review",
        "date": "2026-07-20T10:00:00",
        "location": "Room 401"
    }, headers=alice_headers)
    assert response.status_code == 201

