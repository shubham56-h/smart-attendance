# create_faculty.py
from app import create_app, db
from app.models import Faculty

app = create_app()

with app.app_context():
    # Change these values as you like
    f = Faculty(full_name="Prof Test", email="prof@test.edu", password="secret123")
    db.session.add(f)
    db.session.commit()
    print("Created faculty:", f.id, f.email)
