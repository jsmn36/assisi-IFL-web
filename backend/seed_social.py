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

        # Purge non-Gurukula institutions
        allowed_usernames = {
            "liebhaus", "bethsleeha", "pala_gurukula", "greccio",
            "stalphonsa", "traumhaus", "ashramam", "stclare",
            "assisimount", "assisivagamon", "thopramkudy"
        }
        existing_inst_users = db.query(User).filter(User.role == "institution").all()
        for u in existing_inst_users:
            if u.username not in allowed_usernames:
                print(f"Purging old institution account: {u.username}")
                db.query(Post).filter(Post.institution_id == u.id).delete(synchronize_session=False)
                db.query(InstitutionProfile).filter(InstitutionProfile.user_id == u.id).delete(synchronize_session=False)
                db.query(UserTenant).filter(UserTenant.user_id == u.id).delete(synchronize_session=False)
                db.delete(u)
        db.commit()

        # Institutions list to seed - Exclusively 11 Gurukula Branches with Individual Passwords
        institutions_to_seed = [
            {
                "username": "liebhaus",
                "password": "Liebhaus@2026",
                "email": "liebhaus.kidangoor@assisi.edu",
                "name": "Liebhaus Gurukula, Kidangoor",
                "location": "Kidangoor",
                "about": "Liebhaus Gurukula in Kidangoor is dedicated to academic excellence, value-oriented education, and comprehensive student mentoring.",
                "phone": "+91 94471 10001",
                "website_url": "https://liebhaus.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1513364776144-60967b0f800f?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Orientation & Welcome Ceremony 2026",
                        "content": "Liebhaus Gurukula Kidangoor welcomes all new students for the upcoming academic session. Join us at the main auditorium.",
                        "type": "news",
                        "is_pinned": True,
                        "hashtags": "liebhaus, kidangoor, orientation"
                    }
                ]
            },
            {
                "username": "bethsleeha",
                "password": "Bethsleeha@2026",
                "email": "bethsleeha.kaduthuruthy@assisi.edu",
                "name": "Bethsleeha Gurukula, Kaduthuruthy",
                "location": "Kaduthuruthy",
                "about": "Bethsleeha Gurukula located in Kaduthuruthy provides a balanced learning atmosphere fostering moral development and scholastic achievement.",
                "phone": "+91 94471 10002",
                "website_url": "https://bethsleeha.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Youth Leadership Seminar at Bethsleeha",
                        "content": "A special seminar on leadership development and moral values will be hosted at Bethsleeha Gurukula, Kaduthuruthy.",
                        "type": "event",
                        "is_pinned": True,
                        "hashtags": "bethsleeha, kaduthuruthy, leadership"
                    }
                ]
            },
            {
                "username": "pala_gurukula",
                "password": "PalaGurukula@2026",
                "email": "pala.gurukula@assisi.edu",
                "name": "Pala Gurukula, Pala",
                "location": "Pala",
                "about": "Pala Gurukula in Pala is a center of educational discipline, sports encouragement, and foundational skill development.",
                "phone": "+91 94471 10003",
                "website_url": "https://pala.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Annual Science & Tech Fair 2026",
                        "content": "Pala Gurukula invites student teams across all branches to participate in the regional Science Fair hosted at Pala campus.",
                        "type": "event",
                        "is_pinned": True,
                        "hashtags": "pala, sciencefair, tech"
                    }
                ]
            },
            {
                "username": "greccio",
                "password": "Greccio@2026",
                "email": "greccio.kizhaparayar@assisi.edu",
                "name": "Greccio Gurukula, Kizhaparayar",
                "location": "Kizhaparayar",
                "about": "Greccio Gurukula at Kizhaparayar nurtures students with spiritual grounding, environmental awareness, and top academic standards.",
                "phone": "+91 94471 10004",
                "website_url": "https://greccio.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Green Campus Plantation Drive",
                        "content": "Greccio Gurukula, Kizhaparayar initiates an eco-friendly campus tree planting drive this Saturday.",
                        "type": "notice",
                        "is_pinned": False,
                        "hashtags": "greccio, kizhaparayar, eco"
                    }
                ]
            },
            {
                "username": "stalphonsa",
                "password": "StAlphonsa@2026",
                "email": "stalphonsa.bharanaganam@assisi.edu",
                "name": "St.Alphonsa Gurukula, Bharanaganam",
                "location": "Bharanaganam",
                "about": "St.Alphonsa Gurukula in Bharanaganam inspires young learners with noble values, compassion, and academic rigor.",
                "phone": "+91 94471 10005",
                "website_url": "https://stalphonsa.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Cultural Fest & Merit Day 2026",
                        "content": "St.Alphonsa Gurukula Bharanaganam will celebrate its Annual Merit Day honoring outstanding scholastic performances.",
                        "type": "announcement",
                        "is_pinned": True,
                        "hashtags": "stalphonsa, bharanaganam, meritday"
                    }
                ]
            },
            {
                "username": "traumhaus",
                "password": "Traumhaus@2026",
                "email": "traumhaus.bharanaganam@assisi.edu",
                "name": "Traumhaus Gurukula, Bharanaganam",
                "location": "Bharanaganam",
                "about": "Traumhaus Gurukula at Bharanaganam focuses on creative arts, modern skill education, and experimental research.",
                "phone": "+91 94471 10006",
                "website_url": "https://traumhaus.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1580582932707-520aed937b7b?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1568667256549-094345857637?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Creative Arts & Design Exhibition",
                        "content": "Traumhaus Gurukula Bharanaganam presents the annual showcase of student artistic and technological design projects.",
                        "type": "event",
                        "is_pinned": True,
                        "hashtags": "traumhaus, bharanaganam, design"
                    }
                ]
            },
            {
                "username": "ashramam",
                "password": "Ashramam@2026",
                "email": "ashramam.bharanaganam@assisi.edu",
                "name": "Ashramam Gurukula, Bharanaganam",
                "location": "Bharanaganam",
                "about": "Ashramam Gurukula in Bharanaganam offers a peaceful educational retreat fostering deep focus, discipline, and wisdom.",
                "phone": "+91 94471 10007",
                "website_url": "https://ashramam.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1512290923902-8a9f81dc236c?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Mindfulness & Yoga Workshop",
                        "content": "Join our weekly health and mindfulness session organized by Ashramam Gurukula Bharanaganam.",
                        "type": "news",
                        "is_pinned": False,
                        "hashtags": "ashramam, wellness, focus"
                    }
                ]
            },
            {
                "username": "stclare",
                "password": "StClare@2026",
                "email": "stclare.poovathodu@assisi.edu",
                "name": "St.Clare Gurukula, Poovathodu, Bharanaganam",
                "location": "Poovathodu, Bharanaganam",
                "about": "St.Clare Gurukula at Poovathodu, Bharanaganam is committed to excellence in student guidance, social responsibility, and academics.",
                "phone": "+91 94471 10008",
                "website_url": "https://stclare.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Social Outreach & Service Campaign",
                        "content": "St.Clare Gurukula Poovathodu initiates community assistance and learning support programs.",
                        "type": "notice",
                        "is_pinned": True,
                        "hashtags": "stclare, poovathodu, service"
                    }
                ]
            },
            {
                "username": "assisimount",
                "password": "AssisiMount@2026",
                "email": "assisimount.melampara@assisi.edu",
                "name": "Assisi Mount Gurukula, Melampara, Bharanaganam",
                "location": "Melampara, Bharanaganam",
                "about": "Assisi Mount Gurukula in Melampara, Bharanaganam is set amidst scenic hills offering state-of-the-art learning infrastructure.",
                "phone": "+91 94471 10009",
                "website_url": "https://assisimount.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1562774053-701939374585?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Inter-Gurukula Athletic Meet 2026",
                        "content": "Assisi Mount Gurukula, Melampara is hosting the annual track & field tournament for all Gurukula branches.",
                        "type": "event",
                        "is_pinned": True,
                        "hashtags": "assisimount, melampara, sports"
                    }
                ]
            },
            {
                "username": "assisivagamon",
                "password": "Mitraniketan@2026",
                "email": "mitraniketan.vagamon@assisi.edu",
                "name": "Mitraniketan Boys Gurukula, Vagamon",
                "location": "Vagamon",
                "about": "Mitraniketan Boys Gurukula in Vagamon provides residential education, leadership training, and physical development in hill country.",
                "phone": "+91 94471 10010",
                "website_url": "https://mitraniketan.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Admissions Open for Vagamon Residential Campus 2026",
                        "content": "Admissions are officially open for our premium residential programs at Mitraniketan Boys Gurukula, Vagamon.",
                        "type": "news",
                        "is_pinned": True,
                        "hashtags": "mitraniketan, vagamon, admissions"
                    }
                ]
            },
            {
                "username": "thopramkudy",
                "password": "Thopramkudy@2026",
                "email": "thopramkudy.gurukula@assisi.edu",
                "name": "Thopramkudy Gurukula, Thopramkudy",
                "location": "Thopramkudy",
                "about": "Thopramkudy Gurukula in Thopramkudy delivers quality rural education, empowering young minds to reach high achievements.",
                "phone": "+91 94471 10011",
                "website_url": "https://thopramkudy.assisi.edu",
                "logo_url": "https://images.unsplash.com/photo-1571260899304-425eee4c7efc?auto=format&fit=crop&q=80&w=200",
                "banner_url": "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&q=80&w=800",
                "posts": [
                    {
                        "title": "Digital Literacy & Coding Bootcamp",
                        "content": "Thopramkudy Gurukula launches a specialized digital literacy and coding bootcamp for students.",
                        "type": "event",
                        "is_pinned": True,
                        "hashtags": "thopramkudy, coding, bootcamp"
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
                    location=data.get("location"),
                    contact_email=data["email"],
                    phone=data["phone"],
                    website_url=data["website_url"],
                    about=data["about"],
                    logo_url=data["logo_url"],
                    banner_url=data["banner_url"]
                )
                db.add(profile)
                db.commit()
            else:
                # Update user password and location for existing accounts
                user.hashed_password = get_password_hash(data["password"])
                if user.profile:
                    user.profile.location = data.get("location")
                db.commit()

    print("✅ Database successfully seeded with 1 Super Admin, 11 Gurukula Branches, Profiles, and official social posts!")

except Exception as e:
    db.rollback()
    print("❌ ERROR SEEDING DATABASE:", str(e))
    sys.exit(1)
finally:
    db.close()
