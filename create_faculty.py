from app import create_app, db
from app.models import Faculty
from app.utils import hash_password

app = create_app()

with app.app_context():
    # Check if faculty already exists
    existing = Faculty.query.filter_by(email="faculty@example.com").first()
    if existing:
        print(f"Faculty already exists: {existing.full_name}")
    else:
        # Create a new faculty member
        faculty = Faculty(
            full_name="Test Faculty",
            email="faculty@example.com",
            mobile_number="1234567890",
            password=hash_password("password123")
        )
        db.session.add(faculty)
        db.session.commit()
        print(f"Faculty created successfully!")
        print(f"Email: faculty@example.com")
        print(f"Password: password123")
