from flask import Blueprint, request, jsonify
from app import db
from app.models import Attendance, Student
from app.routes.faculty_routes import otp_sessions, faculty_locations
from datetime import datetime, timezone
import math, time

student_bp = Blueprint("student", __name__)

# Store student locations temporarily in memory
student_locations = {}

# Helper: Calculate distance between two lat-long points (in meters)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# -------------------------------
# 1️⃣ Register a new student
# -------------------------------
@student_bp.route("/register", methods=["POST"])
def register_student():
    data = request.get_json()
    required_fields = ["full_name", "roll_number", "division", "mobile_number", "email", "password"]

    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    # Check if email already exists
    if Student.query.filter_by(email=data["email"]).first():
        return jsonify({"status": "error", "message": "Email already registered"}), 400

    student = Student(
        full_name=data["full_name"],
        roll_number=data["roll_number"],
        division=data["division"],
        mobile_number=data["mobile_number"],
        email=data["email"],
        password=data["password"],
    )

    db.session.add(student)
    db.session.commit()
    return jsonify({"status": "success", "message": "Student registered successfully!"})

# -------------------------------
# 2️⃣ Login
# -------------------------------
@student_bp.route("/login", methods=["POST"])
def login_student():
    data = request.get_json()
    student = Student.query.filter_by(email=data["email"], password=data["password"]).first()
    if student:
        return jsonify({"status": "success", "message": "Login successful", "student_id": student.id})
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

# -------------------------------
# 3️⃣ Update student location
# -------------------------------
@student_bp.route("/update_location", methods=["POST"])
def update_student_location():
    data = request.get_json()
    student_id = data.get("student_id")
    lat = data.get("latitude")
    lon = data.get("longitude")

    if not all([student_id, lat, lon]):
        return jsonify({"status": "error", "message": "Missing location data"}), 400

    student_locations[student_id] = (lat, lon)
    return jsonify({"status": "success", "message": "Location updated successfully"})

# -------------------------------
# 4️⃣ Fill attendance
# -------------------------------
@student_bp.route("/fill_attendance", methods=["POST"])
def fill_attendance():
    data = request.get_json()
    student_id = data.get("student_id")
    faculty_id = data.get("faculty_id")
    otp = data.get("otp")
    subject = data.get("subject")

    # Validate presence of data
    if not all([student_id, faculty_id, otp, subject]):
        return jsonify({"status": "error", "message": "Missing required data"}), 400

    # Convert to integers
    try:
        student_id = int(student_id)
        faculty_id = int(faculty_id)
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid ID format"}), 400

    # Check OTP validity
    otp_info = otp_sessions.get(faculty_id)
    if not otp_info:
        return jsonify({"status": "error", "message": "No active OTP session"}), 400
    if otp_info["otp"] != otp:
        return jsonify({"status": "error", "message": "Invalid OTP"}), 400
    if datetime.now(timezone.utc) > otp_info["expiry"]:
        return jsonify({"status": "error", "message": "OTP expired"}), 400

    # Validate location range (<= 100 meters)
    faculty_loc = faculty_locations.get(faculty_id)
    student_loc = student_locations.get(student_id)

    if not faculty_loc or not student_loc:
        return jsonify({"status": "error", "message": "Location data missing"}), 400

    distance = calculate_distance(faculty_loc[0], faculty_loc[1], student_loc[0], student_loc[1])
    if distance > 100:
        return jsonify({"status": "error", "message": "Out of range"}), 403

    # Wait 20 seconds before marking attendance
    time.sleep(10)

    attendance = Attendance(
    student_id=student_id,
    faculty_id=faculty_id,
    subject=subject,
    date=datetime.now(timezone.utc).date(),
    status="Present")

    db.session.add(attendance)
    db.session.commit()

    # For now just return a success message — later we’ll add Attendance table
    return jsonify({"status": "success", "message": f"Attendance marked for subject {subject}!"})
