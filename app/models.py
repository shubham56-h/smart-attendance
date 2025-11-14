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
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_roll_number', 'roll_number'),  # For login lookups
        db.Index('idx_division', 'division'),        # For division filtering
    )


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('attendance_session.id'), nullable=True)  # Link to session
    subject = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    status = db.Column(db.String(20), nullable=False)  # "Present" or "Absent"
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=True)
    
    # Location tracking
    student_latitude = db.Column(db.Float, nullable=True)
    student_longitude = db.Column(db.Float, nullable=True)
    student_location_accuracy = db.Column(db.Float, nullable=True)
    distance_from_faculty = db.Column(db.Float, nullable=True)  # Distance in meters
    
    # Timestamps
    marked_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    student = db.relationship('Student', backref='attendances', lazy=True)
    faculty = db.relationship('Faculty', backref='attendances', lazy=True)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_student_id', 'student_id'),           # For student attendance history
        db.Index('idx_faculty_id', 'faculty_id'),           # For faculty reports
        db.Index('idx_date', 'date'),                       # For date-based filtering
        db.Index('idx_session_student', 'session_id', 'student_id'),  # For duplicate check
        db.Index('idx_faculty_date', 'faculty_id', 'date'), # For faculty daily reports
    )


class AttendanceSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Session Identification
    session_code = db.Column(db.String(20), unique=True, nullable=False)  # Unique session ID
    otp = db.Column(db.String(10), unique=True, nullable=False)
    
    # Faculty Information
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    
    # Location Data
    faculty_latitude = db.Column(db.Float, nullable=True)
    faculty_longitude = db.Column(db.Float, nullable=True)
    faculty_location_accuracy = db.Column(db.Float, nullable=True)
    faculty_location_timestamp = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Session Status & Timing
    status = db.Column(db.String(20), nullable=False, default='active')  # active, expired, closed, cancelled
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Session Metadata
    expected_division = db.Column(db.String(50), nullable=True)  # Optional: filter by division
    expected_location_radius = db.Column(db.Float, nullable=True, default=100.0)  # meters
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    faculty = db.relationship('Faculty', backref='attendance_sessions', lazy=True)
    attendances = db.relationship('Attendance', backref='session', lazy=True)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_session_code', 'session_code'),
        db.Index('idx_otp', 'otp'),
        db.Index('idx_faculty_status', 'faculty_id', 'status'),
        db.Index('idx_expires_at', 'expires_at'),
    )
