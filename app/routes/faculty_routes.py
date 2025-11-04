from flask import Blueprint, request, jsonify
from app import db
from app.models import Attendance, Faculty, Student
from app.utils import verify_password, generate_tokens
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from datetime import datetime, timezone, timedelta
import random

faculty_bp = Blueprint("faculty_bp", __name__)

# Temporary storages
otp_sessions = {}  # {faculty_id: {otp, expiry}}
faculty_locations = {}  # {faculty_id: (lat, lon)}
otp_to_faculty = {}  # {otp: faculty_id} - reverse lookup for OTP to faculty mapping
otp_used_by_students = {}  # {(otp, student_id): True} - track which students have used which OTP

# -------------------------------
# Faculty Login
# -------------------------------
@faculty_bp.route('/login', methods=['POST'])
def faculty_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    faculty = Faculty.query.filter_by(email=email).first()

    if not faculty or not verify_password(faculty.password, password):
        return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401

    # Generate JWT tokens
    access_token, refresh_token = generate_tokens(
        identity=str(faculty.id),
        additional_claims={"type": "faculty", "email": faculty.email}
    )
    
    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'faculty_id': faculty.id,
        'access_token': access_token,
        'refresh_token': refresh_token
    })

# -------------------------------
# Faculty Refresh Token
# -------------------------------
@faculty_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_faculty_token():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Verify it's a faculty token
    if claims.get("type") != "faculty":
        return jsonify({"status": "error", "message": "Invalid token type"}), 401
    
    # Generate new access token
    new_access_token = create_access_token(
        identity=current_user_id,
        additional_claims={"type": "faculty", "email": claims.get("email")}
    )
    
    return jsonify({
        "status": "success",
        "access_token": new_access_token
    })


# -------------------------------
# Generate OTP
# -------------------------------
@faculty_bp.route('/generate_otp', methods=['POST'])
@jwt_required()
def generate_otp():
    # Get faculty ID from JWT token
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    
    # Verify it's a faculty token
    if claims.get("type") != "faculty":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    faculty_id = current_user_id
    
    # Get subject from request body
    data = request.get_json() or {}
    subject = data.get("subject", "").strip()
    
    if not subject:
        return jsonify({"status": "error", "message": "Subject is required to generate OTP"}), 400

    otp = str(random.randint(1000, 9999))
    expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    # Remove old OTP mapping if exists (in case of regeneration)
    old_otp_info = otp_sessions.get(faculty_id)
    if old_otp_info and 'otp' in old_otp_info:
        old_otp = old_otp_info['otp']
        otp_to_faculty.pop(old_otp, None)
        # Clean up old OTP usage tracking - remove all entries for this OTP
        keys_to_remove = [k for k in otp_used_by_students.keys() if k[0] == old_otp]
        for key in keys_to_remove:
            otp_used_by_students.pop(key, None)

    # Store OTP with subject
    otp_sessions[faculty_id] = {'otp': otp, 'expiry': expiry, 'subject': subject}
    otp_to_faculty[otp] = faculty_id  # Store reverse lookup

    return jsonify({
        'status': 'success',
        'otp': otp,
        'subject': subject,
        'expires_in': '5 minutes'
    })


# -------------------------------
# Update Live Location
# -------------------------------
@faculty_bp.route('/update_location', methods=['POST'])
@jwt_required()
def update_location():
    # Get faculty ID from JWT token
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    
    # Verify it's a faculty token
    if claims.get("type") != "faculty":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if latitude is None or longitude is None:
        return jsonify({'status': 'error', 'message': 'Missing location data'}), 400

    faculty_locations[current_user_id] = (float(latitude), float(longitude))

    return jsonify({'status': 'success', 'message': 'Location updated successfully'})

# -----------------------------------------
# 🧾 Route: View Attendance Reports
# -----------------------------------------
@faculty_bp.route("/view_reports", methods=["GET"])
@jwt_required()
def view_reports():
    # Get faculty ID from JWT token (optional: can filter by query param too)
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    
    # Verify it's a faculty token
    if claims.get("type") != "faculty":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    # Use authenticated faculty ID, but allow query param override for admin purposes
    faculty_id_param = request.args.get("faculty_id")
    if not faculty_id_param:
        faculty_id = current_user_id
    else:
        try:
            faculty_id = int(faculty_id_param)
        except (ValueError, TypeError):
            faculty_id = current_user_id
    
    subject = request.args.get("subject")
    date = request.args.get("date")  # format: YYYY-MM-DD
    division = request.args.get("division")

    query = Attendance.query

    # Optional filters
    if faculty_id:
        query = query.filter_by(faculty_id=faculty_id)
    if subject:
        query = query.filter_by(subject=subject)
    if date:
        query = query.filter(Attendance.date.like(f"%{date}%"))
    if division:
        query = query.join(Student).filter(Student.division == division)

    records = query.all()

    report_data = []
    for record in records:
        student = Student.query.get(record.student_id)
        faculty_name = record.faculty.full_name if record.faculty else "N/A"
        report_data.append({
            "student_name": student.full_name,
            "roll_number": student.roll_number,
            "division": student.division,
            "faculty_name": faculty_name,
            "subject": record.subject,
            "date": record.date,
            "status": record.status
        })

    return jsonify({
        "status": "success",
        "count": len(report_data),
        "records": report_data
    })