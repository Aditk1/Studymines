"""Create test data for dashboard and leaderboard testing."""
import sys
import os
sys.path.insert(0, os.getcwd())

from app.database import SessionLocal
from app.models import User, Upload, Performance

db = SessionLocal()

# Create test users
users_data = [
    ("Alice Johnson", "alice@guest.local", "undergraduate"),
    ("Bob Smith", "bob@guest.local", "high_school"),
    ("Carol White", "carol@guest.local", "postgraduate"),
]

created_users = []
for name, email, level in users_data:
    existing = db.query(User).filter(User.email == email).first()
    if not existing:
        user = User(name=name, email=email, student_level=level)
        db.add(user)
        db.flush()
        created_users.append(user)
    else:
        created_users.append(existing)

db.commit()

# Get all users and add uploads and performance
all_users = db.query(User).all()
subjects = ["Mathematics", "Biology", "History", "Chemistry"]
topics = ["Algebra", "Photosynthesis", "WW2", "Periodic Table"]

for i, user in enumerate(all_users):
    # Create uploads
    for j in range(i + 2):
        upload = Upload(
            user_id=user.id,
            file_name=f"document_{j+1}.pdf",
            file_type="pdf",
            subject=subjects[j % len(subjects)],
            topic=topics[j % len(topics)]
        )
        db.add(upload)
    db.flush()
    
    # Create performance records
    uploads = db.query(Upload).filter(Upload.user_id == user.id).all()
    if uploads:
        for score in [85, 90, 78, 92, 88]:
            perf = Performance(
                user_id=user.id,
                upload_id=uploads[0].id,
                score=score
            )
            db.add(perf)

db.commit()

# Display summary
print("✓ Test data created successfully")
print(f"Users: {len(db.query(User).all())}")
print(f"Uploads: {len(db.query(Upload).all())}")
print(f"Performance records: {len(db.query(Performance).all())}")

db.close()
