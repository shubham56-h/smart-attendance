from flask import Blueprint, request, jsonify
from app import db
from app.models import Attendance, Faculty, Student
from app.utils import verify_password, generate_tokens
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, get_jwt
from datetime import datetime, timezone, timedelta, time, date as date_cls
import io
import csv
import random

faculty_bp = Blueprint("faculty_bp", __name__)

# Temporary storages
otp_sessions = {}  # {faculty_id: {otp, expiry}}
# {faculty_id: {"latitude": float, "longitude": float, "timestamp": datetime, "accuracy": float|None}}
faculty_locations = {}
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
    
    data = request.get_json() or {}
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    accuracy = data.get('accuracy')

    if latitude is None or longitude is None:
        return jsonify({'status': 'error', 'message': 'Missing location data'}), 400

    try:
        lat_val = float(latitude)
        lon_val = float(longitude)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid location format'}), 400

    accuracy_val = None
    if accuracy is not None:
        try:
            accuracy_val = float(accuracy)
        except (TypeError, ValueError):
            accuracy_val = None

    timestamp = datetime.now(timezone.utc)
    faculty_locations[current_user_id] = {
        'latitude': lat_val,
        'longitude': lon_val,
        'timestamp': timestamp,
        'accuracy': accuracy_val
    }

    return jsonify({
        'status': 'success',
        'message': 'Location updated successfully',
        'timestamp': timestamp.isoformat(),
        'accuracy': accuracy_val
    })

# -----------------------------------------
# 📋 Route: List Faculty (for dropdowns)
# -----------------------------------------
@faculty_bp.route('/list', methods=['GET'])
@jwt_required()
def list_faculty():
    claims = get_jwt()
    if claims.get("type") != "faculty":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    # Optional name filter for typeahead clients
    name_q = (request.args.get('q') or '').strip()
    query = Faculty.query
    if name_q:
        query = query.filter(Faculty.full_name.ilike(f"%{name_q}%"))

    faculty_list = [
        {"id": f.id, "full_name": f.full_name}
        for f in query.order_by(Faculty.full_name.asc()).all()
    ]
    return jsonify({"status": "success", "count": len(faculty_list), "faculty": faculty_list})

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
    
    # Allow viewing all faculty by default; optionally filter by faculty_id or faculty_name
    faculty_id = None
    faculty_id_param = request.args.get("faculty_id")
    if faculty_id_param:
        try:
            faculty_id = int(faculty_id_param)
        except (ValueError, TypeError):
            faculty_id = None

    subject = request.args.get("subject")
    date = request.args.get("date")  # legacy single date filter
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    division = request.args.get("division")
    faculty_name = request.args.get("faculty_name")
    status = request.args.get("status")

    # Pagination & sorting
    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        size = int(request.args.get("size", 15))
    except (TypeError, ValueError):
        size = 15
    size = max(1, min(size, 100))  # guardrails
    sort = (request.args.get("sort") or "date").strip().lower()
    order = (request.args.get("order") or "desc").strip().lower()

    query = Attendance.query

    # Optional filters
    if faculty_id is not None:
        query = query.filter_by(faculty_id=faculty_id)
    if subject:
        query = query.filter_by(subject=subject)
    if start_date and end_date:
        try:
            # Attendance.date is a DATE column; compare using date objects inclusively
            sd = date_cls.fromisoformat(start_date)
            ed = date_cls.fromisoformat(end_date)
            query = query.filter(Attendance.date >= sd, Attendance.date <= ed)
        except ValueError:
            # fallback to legacy date filtering when invalid
            if date:
                query = query.filter(Attendance.date.like(f"%{date}%"))
    elif date:
        query = query.filter(Attendance.date.like(f"%{date}%"))
    if division:
        query = query.join(Student).filter(Student.division == division)
    if faculty_name:
        # Ensure join to Faculty for name-based filtering
        query = query.join(Faculty, Attendance.faculty).filter(Faculty.full_name.ilike(f"%{faculty_name}%"))
    if status:
        query = query.filter(Attendance.status == status)

    # Sorting
    if sort == "student":
        query = query.join(Student, Attendance.student_id == Student.id)
        sort_col = Student.full_name
    elif sort == "subject":
        sort_col = Attendance.subject
    elif sort == "division":
        query = query.join(Student, Attendance.student_id == Student.id)
        sort_col = Student.division
    elif sort == "roll":
        query = query.join(Student, Attendance.student_id == Student.id)
        sort_col = Student.roll_number
    elif sort == "status":
        sort_col = Attendance.status
    else:  # default: date
        sort_col = Attendance.date

    if order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Total before pagination
    total = query.count()

    # Pagination
    items = query.offset((page - 1) * size).limit(size).all()

    report_data = []
    for record in items:
        student = Student.query.get(record.student_id)
        faculty_name = record.faculty.full_name if record.faculty else "N/A"
        report_data.append({
            "id": record.id,
            "student_name": student.full_name,
            "roll_number": student.roll_number,
            "division": student.division,
            "faculty_name": faculty_name,
            "subject": record.subject,
            "date": record.date.isoformat() if record.date else None,
            "status": record.status
        })

    return jsonify({
        "status": "success",
        "count": len(report_data),
        "total": total,
        "page": page,
        "size": size,
        "records": report_data
    })

# -----------------------------------------
# 📤 Route: Export Attendance Reports (All Filtered Rows)
# -----------------------------------------
@faculty_bp.route("/export_reports", methods=["GET"])
@jwt_required()
def export_reports():
    current_user_id = int(get_jwt_identity())
    claims = get_jwt()
    if claims.get("type") != "faculty":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    # Filters (same as view_reports)
    faculty_id = None
    faculty_id_param = request.args.get("faculty_id")
    if faculty_id_param:
        try:
            faculty_id = int(faculty_id_param)
        except (ValueError, TypeError):
            faculty_id = None

    subject = request.args.get("subject")
    date = request.args.get("date")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    division = request.args.get("division")
    faculty_name = request.args.get("faculty_name")
    status = request.args.get("status")
    fmt = (request.args.get("format") or "csv").strip().lower()

    query = Attendance.query
    if faculty_id is not None:
        query = query.filter_by(faculty_id=faculty_id)
    if subject:
        query = query.filter_by(subject=subject)
    if start_date and end_date:
        try:
            sd = date_cls.fromisoformat(start_date)
            ed = date_cls.fromisoformat(end_date)
            query = query.filter(Attendance.date >= sd, Attendance.date <= ed)
        except ValueError:
            if date:
                query = query.filter(Attendance.date.like(f"%{date}%"))
    elif date:
        query = query.filter(Attendance.date.like(f"%{date}%"))
    if division:
        query = query.join(Student).filter(Student.division == division)
    if faculty_name:
        query = query.join(Faculty, Attendance.faculty).filter(Faculty.full_name.ilike(f"%{faculty_name}%"))
    if status:
        query = query.filter(Attendance.status == status)

    # Always join student to avoid N+1 when exporting
    query = query.join(Student, Attendance.student_id == Student.id)
    query = query.order_by(Attendance.date.desc())
    items = query.all()

    headers = ["Student", "Roll", "Division", "Faculty", "Subject", "Date", "Status"]

    if fmt == "excel":
        # Simple HTML table (Excel-compatible)
        rows_html = []
        for record in items:
            student = record.student or Student.query.get(record.student_id)
            rows_html.append(
                "<tr>" +
                f"<td>{(student.full_name if student else '')}</td>" +
                f"<td>{(student.roll_number if student else '')}</td>" +
                f"<td>{(student.division if student else '')}</td>" +
                f"<td>{(record.faculty.full_name if record.faculty else 'N/A')}</td>" +
                f"<td>{(record.subject or '')}</td>" +
                f"<td>{(record.date.isoformat() if record.date else '')}</td>" +
                f"<td>{(record.status or '')}</td>" +
                "</tr>"
            )
        table_html = (
            "<table>" +
            "<tr>" + ''.join([f"<th>{h}</th>" for h in headers]) + "</tr>" +
            ''.join(rows_html) +
            "</table>"
        )
        html_doc = (
            "<!DOCTYPE html><html><head><meta charset=\"utf-8\"></head>" +
            f"<body>{table_html}</body></html>"
        )
        ts = datetime.now().strftime("%Y-%m-%d")
        return (
            html_doc,
            200,
            {
                "Content-Type": "application/vnd.ms-excel;charset=utf-8;",
                "Content-Disposition": f"attachment; filename=attendance-{ts}.xls",
            },
        )

    # Default CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for record in items:
        student = record.student or Student.query.get(record.student_id)
        writer.writerow([
            (student.full_name if student else ''),
            (student.roll_number if student else ''),
            (student.division if student else ''),
            (record.faculty.full_name if record.faculty else 'N/A'),
            (record.subject or ''),
            (record.date.isoformat() if record.date else ''),
            (record.status or ''),
        ])
    csv_content = output.getvalue()
    output.close()
    ts = datetime.now().strftime("%Y-%m-%d")
    return (
        csv_content,
        200,
        {
            "Content-Type": "text/csv;charset=utf-8;",
            "Content-Disposition": f"attachment; filename=attendance-{ts}.csv",
        },
    )

# -----------------------------------------
# 🧹 Route: Delete Attendance (Mark Absent)
# -----------------------------------------
@faculty_bp.route("/attendance/<int:attendance_id>", methods=["DELETE"])
@jwt_required()
def delete_attendance(attendance_id: int):
    claims = get_jwt()
    if claims.get("type") != "faculty":
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    record = Attendance.query.get(attendance_id)
    if not record:
        return jsonify({"status": "error", "message": "Record not found"}), 404

    # Optional: restrict deletion to the same faculty who marked it
    # current_user_id = int(get_jwt_identity())
    # if record.faculty_id and record.faculty_id != current_user_id:
    #     return jsonify({"status": "error", "message": "Forbidden"}), 403

    db.session.delete(record)
    db.session.commit()
    return jsonify({"status": "success", "message": "Attendance marked absent (deleted)."})