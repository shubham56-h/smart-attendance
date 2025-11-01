from flask import Blueprint, request, jsonify
from app import db
from app.models import Attendance, Faculty, Student
from app.utils import verify_password
from datetime import datetime, timezone, timedelta
import random

faculty_bp = Blueprint("faculty_bp", __name__)

# Temporary storages
otp_sessions = {}  # {faculty_id: {otp, expiry}}
faculty_locations = {}  # {faculty_id: (lat, lon)}

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

    return jsonify({'status': 'success', 'message': 'Login successful', 'faculty_id': faculty.id})


# -------------------------------
# Generate OTP
# -------------------------------
@faculty_bp.route('/generate_otp', methods=['POST'])
def generate_otp():
    data = request.get_json()
    faculty_id = data.get('faculty_id')

    otp = str(random.randint(1000, 9999))
    expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    otp_sessions[faculty_id] = {'otp': otp, 'expiry': expiry}

    return jsonify({
        'status': 'success',
        'otp': otp,
        'expires_in': '5 minutes'
    })


# -------------------------------
# Update Live Location
# -------------------------------
@faculty_bp.route('/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    faculty_id = data.get('faculty_id')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not faculty_id or latitude is None or longitude is None:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400

    faculty_locations[faculty_id] = (float(latitude), float(longitude))

    return jsonify({'status': 'success', 'message': 'Location updated successfully'})

# -----------------------------------------
# 🧾 Route: View Attendance Reports
# -----------------------------------------
@faculty_bp.route("/view_reports", methods=["GET"])
def view_reports():
    faculty_id = request.args.get("faculty_id")
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
        report_data.append({
            "student_name": student.full_name,
            "roll_number": student.roll_number,
            "division": student.division,
            "subject": record.subject,
            "date": record.date,
            "status": record.status
        })

    return jsonify({
        "status": "success",
        "count": len(report_data),
        "records": report_data
    })