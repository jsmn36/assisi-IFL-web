import sys
from sqlalchemy import create_engine
from app.database import SessionLocal, engine, Base
from app.models import User, UserTenant, DEFAULT_TENANT_ID, DEFAULT_TENANT_SLUG, Post
from app.models.student import StudentAdmission, StudentProfile
from app.models.social_relations import Follow, PostLike, PostComment, Message
from app.models.stories import Story, Highlight, HighlightStory
from app.models.groups import Group, GroupMember, Event, Assignment
from app.core.security import get_password_hash
from app.core.tenant_context import bypass_tenant_filter
from datetime import datetime, timedelta, timezone

print("Running student demo seeding...")
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    with bypass_tenant_filter():
        # 1. Seed Admission Numbers
        admissions_to_seed = [
            {"admission_number": "2026-001", "student_name": "Alice Miller", "class_or_department": "Computer Science"},
            {"admission_number": "2026-002", "student_name": "Bob Smith", "class_or_department": "Business Administration"},
            {"admission_number": "2026-003", "student_name": "Charlie Jones", "class_or_department": "Design & Architecture"},
            {"admission_number": "2026-004", "student_name": "David Brown", "class_or_department": "Hospitality & Tourism"},
            {"admission_number": "2026-005", "student_name": "Eva Watson", "class_or_department": "Computer Science"},
            {"admission_number": "2026-006", "student_name": "Frank Miller", "class_or_department": "Nursing"},
            {"admission_number": "2026-007", "student_name": "Grace Davis", "class_or_department": "Liberal Humanities"},
            {"admission_number": "2026-008", "student_name": "Henry Wilson", "class_or_department": "Business Administration"},
            {"admission_number": "2026-009", "student_name": "Ivy Taylor", "class_or_department": "Design & Architecture"},
            {"admission_number": "2026-010", "student_name": "Jack Evans", "class_or_department": "Computer Science"}
        ]

        for adm_data in admissions_to_seed:
            adm = db.query(StudentAdmission).filter(StudentAdmission.admission_number == adm_data["admission_number"]).first()
            if not adm:
                print(f"Seeding admission: {adm_data['admission_number']}")
                adm = StudentAdmission(
                    admission_number=adm_data["admission_number"],
                    student_name=adm_data["student_name"],
                    class_or_department=adm_data["class_or_department"],
                    is_registered=False
                )
                db.add(adm)
        db.commit()

        # Helper to create student account
        def create_student(username, email, password, name, admission_num, active=True):
            user = db.query(User).filter(User.username == username).first()
            if not user:
                print(f"Creating student user: {username}")
                name_parts = name.split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                user = User(
                    username=username,
                    email=email,
                    hashed_password=get_password_hash(password),
                    role="student",
                    is_active=active,
                    first_name=first_name,
                    last_name=last_name
                )
                db.add(user)
                db.flush()

                # Assign membership
                membership = UserTenant(
                    user_id=user.id,
                    tenant_id=DEFAULT_TENANT_ID,
                    role="student",
                    is_default=True
                )
                db.add(membership)

                # Update admission registration status
                adm = db.query(StudentAdmission).filter(StudentAdmission.admission_number == admission_num).first()
                if adm:
                    adm.is_registered = active

                # Create Profile
                profile = StudentProfile(
                    user_id=user.id,
                    admission_number=admission_num,
                    class_or_department=adm.class_or_department if adm else "General",
                    bio=f"Hey there! I am studying {adm.class_or_department if adm else 'General'} at Assisi.",
                    profile_pic_url=f"https://api.dicebear.com/7.x/adventurer/svg?seed={username}",
                    cover_photo_url="https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&q=80&w=800",
                    privacy_settings="public"
                )
                db.add(profile)
                db.commit()
            return user

        # 2. Seed active and pending student users
        u1 = create_student("student1", "alice@assisi.edu", "student123@", "Alice Miller", "2026-001", active=True)
        u2 = create_student("student2", "bob@assisi.edu", "student123@", "Bob Smith", "2026-002", active=True)
        u3 = create_student("student3", "charlie@assisi.edu", "student123@", "Charlie Jones", "2026-003", active=True)
        u4 = create_student("student4", "david@assisi.edu", "student123@", "David Brown", "2026-004", active=False) # pending

        # 3. Seed Follow Relations
        def add_follow(follower_id, following_id):
            f = db.query(Follow).filter(Follow.follower_id == follower_id, Follow.following_id == following_id).first()
            if not f:
                f = Follow(follower_id=follower_id, following_id=following_id)
                db.add(f)
        
        add_follow(u1.id, u2.id)
        add_follow(u2.id, u1.id)
        add_follow(u1.id, u3.id)
        add_follow(u3.id, u1.id)
        add_follow(u2.id, u3.id)
        db.commit()

        # 4. Seed Posts
        posts_to_seed = [
            {"user_id": u1.id, "title": "First post from Alice!", "content": "Just joined the student community here. Excited to connect with you all! Check out this campus library photo.", "media_url": "https://images.unsplash.com/photo-1568667256549-094345857637?auto=format&fit=crop&q=80&w=800", "hashtags": "newbie, campus, library"},
            {"user_id": u2.id, "title": "Study Group Session", "content": "Hey class, we are hosting a group study session for the upcoming business management midterm this Wednesday in block B.", "media_url": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&q=80&w=800", "hashtags": "study, midterm, business"},
            {"user_id": u3.id, "title": "My Design Prototype", "content": "Check out my new eco-friendly architectural classroom layout! What do you think?", "media_url": "https://images.unsplash.com/photo-1512290923902-8a9f81dc236c?auto=format&fit=crop&q=80&w=800", "hashtags": "design, architecture, green"}
        ]

        for p_data in posts_to_seed:
            post = db.query(Post).filter(Post.title == p_data["title"]).first()
            if not post:
                print(f"Creating post: {p_data['title']}")
                post = Post(
                    institution_id=p_data["user_id"],
                    title=p_data["title"],
                    content=p_data["content"],
                    type="image",
                    media_url=p_data["media_url"],
                    hashtags=p_data["hashtags"]
                )
                db.add(post)
                db.flush()

                # Add a comment & like
                like = PostLike(post_id=post.id, user_id=u3.id if p_data["user_id"] != u3.id else u1.id)
                db.add(like)

                comment = PostComment(
                    post_id=post.id,
                    user_id=u2.id if p_data["user_id"] != u2.id else u1.id,
                    content="This looks super cool!"
                )
                db.add(comment)
        db.commit()

        # 5. Seed Stories (within last 24h)
        story = db.query(Story).filter(Story.user_id == u2.id).first()
        if not story:
            print("Seeding active stories...")
            s1 = Story(user_id=u2.id, media_url="https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&q=80&w=600", type="image", created_at=datetime.now(timezone.utc) - timedelta(hours=2))
            s2 = Story(user_id=u3.id, media_url="https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&q=80&w=600", type="image", created_at=datetime.now(timezone.utc) - timedelta(hours=5))
            db.add(s1)
            db.add(s2)
            db.commit()

        # 6. Seed Chat Messages
        msg = db.query(Message).filter(Message.sender_id == u1.id).first()
        if not msg:
            print("Seeding chat messages...")
            m1 = Message(sender_id=u1.id, receiver_id=u2.id, content="Hey Bob, did you complete the homework?")
            m2 = Message(sender_id=u2.id, receiver_id=u1.id, content="Hey Alice! Yes, I did. I will send you my notes shortly.")
            db.add(m1)
            db.add(m2)
            db.commit()

        # 7. Seed Classrooms/Groups
        group = db.query(Group).filter(Group.name == "Computer Science 2026").first()
        if not group:
            print("Seeding classroom group...")
            group = Group(
                name="Computer Science 2026",
                description="Official classroom for Computer Science batch of 2026. Assignments, study material, and event updates will be shared here.",
                created_by=u1.id,
                is_classroom=True,
                class_or_department="Computer Science"
            )
            db.add(group)
            db.flush()

            # Join u1 (admin) and u2 (member)
            gm1 = GroupMember(group_id=group.id, user_id=u1.id, role="admin")
            gm2 = GroupMember(group_id=group.id, user_id=u2.id, role="member")
            db.add(gm1)
            db.add(gm2)

            # Share assignment
            assign = Assignment(
                title="Python Advanced OOP Assignment",
                description="Implement a custom decorator structure matching the hotel booking validator patterns. Submit file link by next Monday.",
                due_date=datetime.now(timezone.utc) + timedelta(days=7),
                group_id=group.id,
                created_by=u1.id
            )
            db.add(assign)

            # Share event
            evt = Event(
                title="OOP Coding Hackathon",
                description="24-hour programming challenge in the lab. Prizes for top 3 teams.",
                date=datetime.now(timezone.utc) + timedelta(days=3),
                location="Main Programming Lab Block C",
                created_by=u1.id,
                group_id=group.id
            )
            db.add(evt)
            db.commit()

    print("✅ Student demo database successfully seeded!")

except Exception as e:
    db.rollback()
    print("❌ ERROR SEEDING STUDENT DEMO DATABASE:", str(e))
    sys.exit(1)
finally:
    db.close()
