# create_faculty.py
from app import create_app, db
from app.models import Faculty
from app.utils import hash_password

app = create_app()

with app.app_context():
    # Change these values as you like
    f1 = Faculty(full_name="krisha", email="krisha@gmail.com", password=hash_password("krisha123"))
    f2 = Faculty(full_name="kalyani", email="kalyani@gmail.com", password=hash_password("kalyani123"))
    f3 = Faculty(full_name="pritesh", email="pritesh@gmail.com", password=hash_password("pritesh123"))
    f4 = Faculty(full_name="vrusabh", email="vrusabh@gmail.com", password=hash_password("vrusabh123"))
    db.session.add(f1)
    db.session.add(f2)
    db.session.add(f3)
    db.session.add(f4)
    db.session.commit()
    print("Created faculty:", f1.id, f1.email)
    print("Created faculty:", f2.id, f2.email)
    print("Created faculty:", f3.id, f3.email)
    print("Created faculty:", f4.id, f4.email)