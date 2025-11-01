from app import db
from datetime import datetime, timezone

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), nullable=False)
    division = db.Column(db.String(50), nullable=False)
    mobile_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    attendances = db.relationship('Attendance', backref='student', lazy=True)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    status = db.Column(db.String(20), nullable=False)  # "Present" or "Absent"
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=True)

    faculty = db.relationship('Faculty', backref='attendances', lazy=True)
