import sys
from sqlalchemy import create_engine
from app.database import SessionLocal, engine, Base
from app.models import User, UserTenant, Tenant, DEFAULT_TENANT_ID, DEFAULT_TENANT_SLUG, InstitutionProfile, Post
from app.core.security import get_password_hash
from app.core.tenant_context import bypass_tenant_filter

# Initialize DB
print("Initializing database tables...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    with bypass_tenant_filter():
        # 1. Create Default Tenant
        tenant = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
        if not tenant:
            print("Creating default tenant...")
            tenant = Tenant(
                id=DEFAULT_TENANT_ID,
                slug=DEFAULT_TENANT_SLUG,
                name="Assisi Network",
                is_active=True
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

        # 2. Add Super Admin
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Creating admin user...")
            admin = User(
                username="admin",
                email="admin@assisi.edu",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_superuser=True,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

            # Assign membership
            admin_membership = UserTenant(
                user_id=admin.id,
                tenant_id=DEFAULT_TENANT_ID,
                role="admin",
                is_default=True
            )
            db.add(admin_membership)
            db.commit()

        # Institutions list to seed
        institutions_to_seed = [
            {
                "username": "assisivagamon",
                "password": "assisi123@",
                "email": "vagamon@assisi.edu",
                "name": "Assisi Vagamon Campus",
                "about": "Situated in the beautiful hills of Vagamon, this premium residential campus offers world-class management, business administration, and hospitality studies.",
                "phone": "+91 94471 23456",
                "website_url": "https://vagamon.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Admissions Open for Vagamon Campus 2026",
                        "content": "Admissions are officially open for our premium MBA and Tourism Management courses at Assisi Vagamon. Experience education amidst serene hills and state-of-the-art facilities!",
                        "type": "news",
                        "is_pinned": True,
                        "hashtags": "admissions, vagamon, mba"
                    },
                    {
                        "title": "International Hospitality Workshop",
                        "content": "A three-day workshop on Global Hospitality Standards will be held next Tuesday in the main seminar hall, led by foreign industry experts.",
                        "type": "event",
                        "is_pinned": False,
                        "hashtags": "workshop, hospitality, vagamon"
                    }
                ]
            },
            {
                "username": "liebhaus",
                "password": "assisi123@",
                "email": "liebhaus@assisi.edu",
                "name": "Liebhaus Institute of Design",
                "about": "Liebhaus is a premier specialized architecture and industrial design workspace, encouraging pure creative research, sustainability, and green construction.",
                "phone": "+91 94479 87654",
                "website_url": "https://liebhaus.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Expressions 2026: Green Design Expo",
                        "content": "The annual Liebhaus student design exhibition 'Expressions' is now open. Come witness breathtaking scale models, sustainable architecture, and mixed-media design concepts.",
                        "type": "news",
                        "is_pinned": True,
                        "hashtags": "greendesign, expo, architecture"
                    }
                ]
            },
            {
                "username": "assisikottayam",
                "password": "assisi123@",
                "email": "kottayam@assisi.edu",
                "name": "Assisi Kottayam Campus",
                "about": "Our prominent Kottayam campus features advanced technical sciences, nursing programs, and liberal humanities studies under a unified modern framework.",
                "phone": "+91 94477 11223",
                "website_url": "https://kottayam.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Campus Placement Drive 2026",
                        "content": "Assisi Kottayam is hosting a mega corporate placement drive this Friday! 20+ top tier healthcare, technological, and educational organizations are hiring on the spot.",
                        "type": "event",
                        "is_pinned": True,
                        "hashtags": "placements, jobs, kottayam"
                    }
                ]
            }
        ]

        for data in institutions_to_seed:
            user = db.query(User).filter(User.username == data["username"]).first()
            if not user:
                print(f"Creating {data['username']} user...")
                user = User(
                    username=data["username"],
                    email=data["email"],
                    hashed_password=get_password_hash(data["password"]),
                    role="institution",
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)

                # Assign membership
                membership = UserTenant(
                    user_id=user.id,
                    tenant_id=DEFAULT_TENANT_ID,
                    role="institution",
                    is_default=True
                )
                db.add(membership)
                db.commit()

                # Create Profile
                profile = InstitutionProfile(
                    user_id=user.id,
                    name=data["name"],
                    contact_email=data["email"],
                    phone=data["phone"],
                    website_url=data["website_url"],
                    about=data["about"],
                    logo_url=data["logo_url"],
                    banner_url=data["banner_url"]
                )
                db.add(profile)
                db.commit()

                # Create posts
                for pdata in data["posts"]:
                    post = Post(
                        institution_id=user.id,
                        title=pdata["title"],
                        content=pdata["content"],
                        type=pdata["type"],
                        is_pinned=pdata["is_pinned"],
                        hashtags=pdata["hashtags"]
                    )
                    db.add(post)
                db.commit()

    print("✅ Database successfully seeded with 1 Super Admin, 3 Custom Institutions, 3 Profiles, and 4 social posts!")

except Exception as e:
    db.rollback()
    print("❌ ERROR SEEDING DATABASE:", str(e))
    sys.exit(1)
finally:
    db.close()
