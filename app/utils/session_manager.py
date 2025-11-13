import random
import string
import math
from datetime import datetime, timedelta, timezone

from app import db
from app.models import AttendanceSession, Attendance, Faculty


def generate_otp(length=4):
    """Generate a unique 4-digit OTP"""
    characters = string.digits
    while True:
        otp = ''.join(random.choice(characters) for _ in range(length))
        # Check if OTP is unique
        if not AttendanceSession.query.filter_by(otp=otp).first():
            return otp


def generate_session_code(length=10):
    """Generate a unique session code"""
    characters = string.ascii_uppercase + string.digits
    while True:
        session_code = ''.join(random.choice(characters) for _ in range(length))
        if not AttendanceSession.query.filter_by(session_code=session_code).first():
            return session_code


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two lat-long points using Haversine formula (in meters)"""
    if any(v is None for v in [lat1, lon1, lat2, lon2]):
        return None
    
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class SessionManager:
    """Service class for managing attendance sessions"""
    
    def create_session(self, faculty_id: int, subject: str, location_data: dict, expires_in_minutes: int = 5) -> AttendanceSession:
        """Create a new attendance session"""
        # Generate unique OTP and session code
        otp = generate_otp()
        session_code = generate_session_code()
        
        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

        # Create new session
        session = AttendanceSession(
            session_code=session_code,
            otp=otp,
            faculty_id=faculty_id,
            subject=subject,
            faculty_latitude=location_data.get('latitude'),
            faculty_longitude=location_data.get('longitude'),
            faculty_location_accuracy=location_data.get('accuracy'),
            faculty_location_timestamp=datetime.now(timezone.utc) if location_data.get('latitude') else None,
            expires_at=expires_at
        )
        db.session.add(session)
        db.session.commit()
        return session

    def get_active_session(self, faculty_id: int) -> AttendanceSession | None:
        """Get the active session for a faculty member"""
        now = datetime.now(timezone.utc)
        # Get session without time filter first
        session = AttendanceSession.query.filter(
            AttendanceSession.faculty_id == faculty_id,
            AttendanceSession.status == 'active'
        ).first()
        
        if not session:
            return None
        
        # Handle timezone-naive datetime from SQLite
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        # Check if expired
        if expires_at <= now:
            return None
        
        return session

    def get_session_by_otp(self, otp: str) -> AttendanceSession | None:
        """Get an active session by OTP"""
        now = datetime.now(timezone.utc)
        # Get session without time filter first
        session = AttendanceSession.query.filter(
            AttendanceSession.otp == otp,
            AttendanceSession.status == 'active'
        ).first()
        
        if not session:
            return None
        
        # Handle timezone-naive datetime from SQLite
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        # Check if expired
        if expires_at <= now:
            return None
        
        return session

    def validate_and_mark_attendance(self, otp: str, student_id: int, student_location: dict) -> Attendance | None:
        """Validate OTP and location, then mark attendance"""
        session = self.get_session_by_otp(otp)

        if not session:
            return None  # Session not found or expired

        # Check if student already marked attendance for this session
        existing_attendance = Attendance.query.filter_by(
            session_id=session.id,
            student_id=student_id
        ).first()
        if existing_attendance:
            return None  # Attendance already marked

        # Validate location if faculty location is available
        distance = None
        faculty_has_location = session.faculty_latitude is not None and session.faculty_longitude is not None
        student_has_location = student_location.get('latitude') is not None and student_location.get('longitude') is not None

        if faculty_has_location:
            # If faculty has location, student must also provide location
            if not student_has_location:
                logging.warning("Student location missing when faculty has location")
                return None  # Student location required when faculty has location
            
            # Check student GPS accuracy - reject if too poor (> 150m)
            student_accuracy = student_location.get('accuracy')
            if student_accuracy and student_accuracy > 150:
                import logging
                logging.warning(f"Student GPS accuracy too poor: {student_accuracy}m (max 150m)")
                return None  # GPS accuracy too poor, location unreliable
            
            distance = calculate_distance(
                session.faculty_latitude,
                session.faculty_longitude,
                student_location.get('latitude'),
                student_location.get('longitude')
            )

            if distance is None:
                return None  # Failed to calculate distance
            
            # Get allowed radius (minimum 500 meters for mobile GPS tolerance)
            # Mobile GPS can be very inaccurate, especially indoors, in urban areas, or different buildings
            # This accounts for GPS drift, different devices, and indoor/outdoor differences
            # Use the LARGER of: database value or 500m default
            allowed_radius = max(session.expected_location_radius or 0, 500.0)
            
            # Add accuracy buffer if both locations have accuracy data
            if session.faculty_location_accuracy and student_location.get('accuracy'):
                accuracy_buffer = float(session.faculty_location_accuracy) + float(student_location.get('accuracy'))
                # Use the larger of: base radius or accuracy buffer + 100m safety margin
                allowed_radius = max(allowed_radius, accuracy_buffer + 100.0)
            
            # Only log if validation fails (moved below)
            if distance > allowed_radius:
                import logging
                logging.warning(f"Location validation failed: {distance}m > {allowed_radius}m")
                return None  # Student too far from faculty location

        # Create attendance record
        attendance = Attendance(
            student_id=student_id,
            session_id=session.id,
            subject=session.subject,
            faculty_id=session.faculty_id,
            student_latitude=student_location.get('latitude'),
            student_longitude=student_location.get('longitude'),
            student_location_accuracy=student_location.get('accuracy'),
            distance_from_faculty=distance,
            status='Present'
        )
        db.session.add(attendance)
        db.session.commit()
        return attendance

    def close_session(self, session_id: int) -> bool:
        """Close a session"""
        session = AttendanceSession.query.get(session_id)
        if session:
            session.status = 'closed'
            session.closed_at = datetime.now(timezone.utc)
            db.session.commit()
            return True
        return False

    def expire_old_sessions(self) -> int:
        """Expire sessions that have passed their expiration time"""
        now = datetime.now(timezone.utc)
        expired_sessions = AttendanceSession.query.filter(
            AttendanceSession.expires_at < now,
            AttendanceSession.status == 'active'
        ).all()
        for session in expired_sessions:
            session.status = 'expired'
        db.session.commit()
        return len(expired_sessions)

    def delete_old_sessions(self, older_than_days: int = 7) -> int:
        """Delete old sessions that are closed or expired"""
        now = datetime.now(timezone.utc)
        threshold_date = now - timedelta(days=older_than_days)

        # Find sessions that are either closed or expired and are older than the threshold
        old_sessions = AttendanceSession.query.filter(
            AttendanceSession.status.in_(['closed', 'expired']),
            AttendanceSession.expires_at < threshold_date
        ).all()

        deleted_count = 0
        for session in old_sessions:
            # Also delete associated attendance records to maintain data integrity
            Attendance.query.filter_by(session_id=session.id).delete()
            db.session.delete(session)
            deleted_count += 1
        db.session.commit()
        return deleted_count

    def get_session_statistics(self, faculty_id: int, start_date: datetime, end_date: datetime) -> dict:
        """Get session statistics for a faculty member"""
        total_sessions = AttendanceSession.query.filter(
            AttendanceSession.faculty_id == faculty_id,
            AttendanceSession.created_at >= start_date,
            AttendanceSession.created_at <= end_date
        ).count()

        active_sessions = AttendanceSession.query.filter(
            AttendanceSession.faculty_id == faculty_id,
            AttendanceSession.status == 'active'
        ).count()

        total_attendance_records = db.session.query(Attendance).join(AttendanceSession).filter(
            AttendanceSession.faculty_id == faculty_id,
            Attendance.marked_at >= start_date,
            Attendance.marked_at <= end_date
        ).count()

        # Calculate average students per session (avoid division by zero)
        average_per_session = total_attendance_records / total_sessions if total_sessions else 0

        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'total_attendance': total_attendance_records,
            'average_per_session': round(average_per_session, 2)
        }

