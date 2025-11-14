from flask import Blueprint, request, jsonify
from app import db
from app.models import Attendance, Student
from app.utils import hash_password, verify_password, generate_tokens
from app.utils.session_manager import SessionManager
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from datetime import datetime, timezone
import logging

student_bp = Blueprint("student", __name__)
session_manager = SessionManager()

@student_bp.route("/register", methods=["POST"])
def register_student():
    data = request.get_json()
    required_fields = ["full_name", "roll_number", "division", "mobile_number", "email", "password"]
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing fields"}), 400
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

@student_bp.route("/login", methods=["POST"])
def login_student():
    data = request.get_json()
    student = Student.query.filter_by(roll_number=data["roll_number"]).first()
    if student and verify_password(student.password, data["password"]):
        access_token, refresh_token = generate_tokens(
            identity=str(student.id),
            additional_claims={"type": "student", "email": student.email}
        )
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "student_id": student.id,
            "student": {
                "id": student.id,
                "full_name": student.full_name,
                "roll_number": student.roll_number,
                "division": student.division,
                "email": student.email
            },
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@student_bp.route("/api/profile", methods=["GET"])
@jwt_required()
def student_profile():
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    
    if claims.get("type") != "student":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    
    student = Student.query.get(current_user_id)
    
    if not student:
        return jsonify({"status": "error", "message": "Student not found"}), 404
    
    return jsonify({
        "status": "success",
        "student": {
            "id": student.id,
            "full_name": student.full_name,
            "roll_number": student.roll_number,
            "division": student.division,
            "email": student.email,
            "mobile_number": student.mobile_number
        }
    })

@student_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_student_token():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    if claims.get("type") != "student":
        return jsonify({"status": "error", "message": "Invalid token type"}), 401
    new_access_token = create_access_token(
        identity=current_user_id,
        additional_claims={"type": "student", "email": claims.get("email")}
    )
    return jsonify({"status": "success", "access_token": new_access_token})

@student_bp.route("/mark_attendance", methods=["POST"])
@jwt_required()
def mark_attendance():
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    if claims.get("type") != "student":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    data = request.get_json()
    otp = data.get("otp", "").strip()
    subject = data.get("subject", "").strip()
    if not otp or not subject:
        return jsonify({"status": "error", "message": "OTP and subject are required"}), 400
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if latitude is None or longitude is None:
        return jsonify({"status": "error", "message": "Location data is required"}), 400
    student_location = {"latitude": latitude, "longitude": longitude, "accuracy": data.get("accuracy")}
    session = session_manager.get_session_by_otp(otp)
    if not session:
        return jsonify({"status": "error", "message": "Invalid OTP"}), 400
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return jsonify({"status": "error", "message": "OTP has expired"}), 400
    if session.subject != subject:
        return jsonify({"status": "error", "message": f"Subject mismatch. This OTP is for {session.subject}"}), 400
    
    # Check student GPS accuracy before processing (must be < 150m)
    student_accuracy = student_location.get("accuracy")
    if student_accuracy and student_accuracy > 150:
        return jsonify({
            "status": "error", 
            "message": f"GPS accuracy too poor ({int(student_accuracy)}m). Please go outdoors or enable high-accuracy GPS.",
            "accuracy": student_accuracy,
            "max_allowed": 150
        }), 400
    
    try:
        attendance = session_manager.validate_and_mark_attendance(otp, current_user_id, student_location)
        return jsonify({
            "status": "success",
            "message": f"Attendance marked successfully for {attendance.subject}!",
            "subject": attendance.subject,
            "distance": round(attendance.distance_from_faculty, 2) if attendance.distance_from_faculty else None
        })
    except ValueError as e:
        # Specific validation errors with clear messages
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Attendance marking error: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to mark attendance. Please try again."}), 500
