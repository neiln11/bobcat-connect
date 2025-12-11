import pandas as pd
import os
from app import app, db
from models import Club, Post, User, PostLike
from datetime import datetime, timedelta, timezone
import random

# --- DEMO DATA: PRE-WRITTEN POSTS ---
DEMO_POSTS = [
    # 1. Machine Learning Club (Your MLC Images)
    {
        "club": "Machine Learning Club",
        "image": "MLC_GM_2.jpg",  # General Meeting
        "caption": "Join us for our monthly General Meeting! We'll be discussing plans for the semester and open officer positions.",
        "is_event": True,
        "title": "Monthly General Meeting",
        "location": "COB2 140",
        "offset": 2, # In 2 days
        "likes": 15
    },
    {
        "club": "Machine Learning Club",
        "image": "MLC_WS_3.jpg", # Workshop
        "caption": "Deep Dive into Neural Networks. Bring your laptop!",
        "is_event": True,
        "title": "Neural Networks Workshop",
        "location": "COB1 105",
        "offset": 7, # In 1 week
        "likes": 22
    },
    {
        "club": "Machine Learning Club",
        "image": "MLC_Fun.png", # Fun Post
        "caption": "Great vibes at our social yesterday! 🍕 Thanks to everyone who came out.",
        "is_event": False,
        "offset": -2, # 2 days ago
        "likes": 8
    },

    # 2. Association for Computing Machinery (ACM) - Using LLM.png
    {
        "club": "Association for Computing Machinery", # Exact name from CSV
        "image": "LLM.png",
        "caption": "Exploring the capabilities of Large Language Models in our latest tech talk. The future of browsing is here.",
        "is_event": False,
        "offset": -1, # Yesterday
        "likes": 45
    },

    # 3. Pre-Veterinary Club - Using birds.jpg
    {
        "club": "Pre-Veterinary Club", # Exact name from CSV
        "image": "birds.jpg",
        "caption": "Our field trip to the local avian sanctuary was a success! Look at these beautiful feathered friends. 🦜📸",
        "is_event": False,
        "offset": -5, # 5 days ago
        "likes": 30
    }
]

def seed_everything():
    with app.app_context():
        print("1. Resetting Database...")
        db.drop_all()
        db.create_all()

        # --- STEP 1: CREATE DUMMY USERS (For random likes) ---
        print("2. Creating Dummy Users...")
        dummy_users = []
        # Create a few generic students so we can assign likes
        for i in range(10):
            u = User(email=f'student{i}@ucmerced.edu', password_hash='hashed_placeholder', role='student')
            db.session.add(u)
            dummy_users.append(u)
        
        # Create a default admin account for you to use immediately
        admin = User(email='admin@ucmerced.edu', password_hash='$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWUNKbAt/C.M.Oa.E.2.tS.z/C.y/C', role='admin') # password: password
        db.session.add(admin)
        
        db.session.commit()

        # --- STEP 2: LOAD CLUBS FROM CSV ---
        base_dir = os.path.abspath(os.path.dirname(__file__))
        csv_path = os.path.join(base_dir, 'scraped_clubs.csv')

        print(f"3. Loading Clubs from {csv_path}...")
        try:
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path).fillna('')
                for index, row in df.iterrows():
                    # Only add if it doesn't exist
                    if not Club.query.filter_by(name=row['name']).first():
                        # Parse member count safely
                        count_val = 0
                        raw_count = str(row['member_count'])
                        if raw_count.replace('.','',1).isdigit(): 
                            count_val = int(float(raw_count))

                        new_club = Club(
                            name=row['name'],
                            category=row['category'],
                            meeting_time=row['meeting_time'],
                            location=row['location'],
                            member_count=count_val,
                            description=row['description'],
                            verified=True, # Auto-verify CSV clubs so they appear
                            officer_verified=False 
                        )
                        db.session.add(new_club)
                db.session.commit()
                print("   - CSV Clubs loaded.")
            else:
                print("   ! CSV not found. Skipping CSV load.")
        except Exception as e:
            print(f"   ! Error loading CSV: {e}")

        # --- STEP 3: SEED DEMO POSTS ---
        print("4. Seeding Demo Posts...")
        
        for p in DEMO_POSTS:
            # 1. Find the club (fuzzy match to be safe)
            club = Club.query.filter(Club.name.ilike(f"%{p['club']}%")).first()
            
            if not club:
                # If the club isn't in the CSV, create it so the post has a home
                print(f"   + Creating missing club: {p['club']}")
                club = Club(
                    name=p['club'],
                    category="General",
                    description=f"Official page for {p['club']}.",
                    verified=True,
                    officer_verified=True, 
                    member_count=10
                )
                db.session.add(club)
                db.session.commit() 

            # 2. Calculate Post Time
            post_time = datetime.now(timezone.utc)
            if not p['is_event']:
                # Social posts go back in time
                post_time = post_time + timedelta(days=p['offset'])
            
            # 3. Create the Post
            new_post = Post(
                club_id=club.id,
                image_file=p['image'],
                caption=p['caption'],
                is_event=p['is_event'],
                created_at=post_time
            )

            if p['is_event']:
                new_post.event_title = p.get('title', 'General Meeting')
                new_post.event_location = p.get('location', 'TBD')
                # Event date is future/past based on offset
                new_post.event_date = datetime.now(timezone.utc) + timedelta(days=p['offset'])

            db.session.add(new_post)
            db.session.commit() # Commit to generate ID

            # 4. Add Fake Likes
            # Reload users to attach to session
            users = User.query.filter(User.role == 'student').all()
            if users:
                num_likes = min(p.get('likes', 0), len(users))
                selected_users = random.sample(users, num_likes)
                for u in selected_users:
                    like = PostLike(user_id=u.id, post_id=new_post.id)
                    db.session.add(like)
                db.session.commit()

            print(f"   + Post added for {club.name}")

        print("Done! Database is fully seeded with demo content.")

if __name__ == "__main__":
    seed_everything()