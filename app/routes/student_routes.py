from flask import Blueprint, request, jsonify
from app import db
from app.models import Attendance, Student
from app.routes.faculty_routes import otp_sessions, faculty_locations, otp_to_faculty, otp_used_by_students
from app.utils import hash_password, verify_password, generate_tokens
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token, get_jwt
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
    if Student.query.filter_by(roll_number=data["roll_number"]).first():
        return jsonify({"status": "error", "message": "Student already registered"}), 400

    student = Student(
        full_name=data["full_name"],
        roll_number=data["roll_number"],
        division=data["division"],
        mobile_number=data["mobile_number"],
        email=data["email"],
        password=hash_password(data["password"]),
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
    student = Student.query.filter_by(roll_number=data["roll_number"]).first()
    if student and verify_password(student.password, data["password"]):
        # Generate JWT tokens
        access_token, refresh_token = generate_tokens(
            identity=str(student.id),
            additional_claims={"type": "student", "email": student.email}
        )
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "student_id": student.id,
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

# -------------------------------
# 2.5️⃣ Refresh Token
# -------------------------------
@student_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_student_token():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Verify it's a student token
    if claims.get("type") != "student":
        return jsonify({"status": "error", "message": "Invalid token type"}), 401
    
    # Generate new access token
    new_access_token = create_access_token(
        identity=current_user_id,
        additional_claims={"type": "student", "email": claims.get("email")}
    )
    
    return jsonify({
        "status": "success",
        "access_token": new_access_token
    })

# -------------------------------
# 3️⃣ Update student location
# -------------------------------
@student_bp.route("/update_location", methods=["POST"])
@jwt_required()
def update_student_location():
    # Get student ID from JWT token
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    
    # Verify it's a student token
    if claims.get("type") != "student":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    data = request.get_json()
    lat = data.get("latitude")
    lon = data.get("longitude")

    if not all([lat, lon]):
        return jsonify({"status": "error", "message": "Missing location data"}), 400

    student_locations[current_user_id] = (lat, lon)
    return jsonify({"status": "success", "message": "Location updated successfully"})

# -------------------------------
# 4️⃣ Fill attendance
# -------------------------------
@student_bp.route("/fill_attendance", methods=["POST"])
@jwt_required()
def fill_attendance():
    # Get student ID from JWT token
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    
    # Verify it's a student token
    if claims.get("type") != "student":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    data = request.get_json()
    otp = data.get("otp")
    subject = data.get("subject")

    # Validate presence of data
    if not all([otp, subject]):
        return jsonify({"status": "error", "message": "Missing required data (OTP and subject)"}), 400

    # Get faculty_id from OTP lookup
    faculty_id = otp_to_faculty.get(otp)
    if not faculty_id:
        return jsonify({"status": "error", "message": "Invalid OTP"}), 400

    # Convert to integers
    try:
        student_id = current_user_id  # Use authenticated student ID
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
    
    # Validate that the subject matches the OTP's subject
    otp_subject = otp_info.get("subject")
    if otp_subject and otp_subject != subject:
        return jsonify({"status": "error", "message": f"This OTP is for {otp_subject}, not {subject}"}), 400
    
    # Check if this student has already used this OTP for this subject
    otp_usage_key = (otp, student_id, subject)
    if otp_used_by_students.get(otp_usage_key):
        return jsonify({"status": "error", "message": "You have already marked attendance"}), 400

    # Validate location range (<= 100 meters)
    faculty_loc = faculty_locations.get(faculty_id)
    student_loc = student_locations.get(student_id)

    if not faculty_loc or not student_loc:
        return jsonify({"status": "error", "message": "Location data missing"}), 400

    distance = calculate_distance(faculty_loc[0], faculty_loc[1], student_loc[0], student_loc[1])
    if distance > 100:
        return jsonify({"status": "error", "message": "Out of range"}), 403

    # Check if student has already marked attendance for this subject today
    today = datetime.now(timezone.utc).date()
    existing_attendance = Attendance.query.filter_by(
        student_id=student_id,
        subject=subject,
        date=today
    ).first()
    
    if existing_attendance:
        return jsonify({"status": "error", "message": "Attendance already marked for this subject today"}), 400

    # Wait 20 seconds before marking attendance
    time.sleep(10)

    attendance = Attendance(
    student_id=student_id,
    faculty_id=faculty_id,
    subject=subject,
    date=today,
    status="Present")

    db.session.add(attendance)
    db.session.commit()
    
    # Mark this OTP as used by this student
    otp_used_by_students[otp_usage_key] = True

    # For now just return a success message — later we'll add Attendance table
    return jsonify({"status": "success", "message": f"Attendance marked for subject {subject}!"})
