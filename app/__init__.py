from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from datetime import timedelta
import os
import secrets
import threading
import time

# Initialize SQLAlchemy
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configure database (SQLite for now)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'attendance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Generate a secure random secret key if not set
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_urlsafe(32))
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))
    # Access tokens expire in 1 hour, refresh tokens expire in 30 days
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    # Security: CSRF protection for cookies (if using cookies)
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Register JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'status': 'error', 'message': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'status': 'error', 'message': 'Authorization token is missing'}), 401

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({'status': 'error', 'message': 'Fresh token required'}), 401

    # Import and register blueprints (routes)
    from app.routes.faculty_routes import faculty_bp
    from app.routes.student_routes import student_bp

    app.register_blueprint(faculty_bp, url_prefix="/faculty")
    app.register_blueprint(student_bp, url_prefix="/student")

    # -------------------------------
    # Frontend page routes
    # -------------------------------
    from flask import render_template, redirect

    @app.route("/")
    def home_page():
        return render_template("index.html")

    # Student pages
    @app.route("/student/login")
    def student_login_page():
        return render_template("student/login.html")

    @app.route("/student/register")
    def student_register_page():
        return render_template("student/register.html")

    @app.route("/student/dashboard")
    def student_dashboard_page():
        return render_template("student/dashboard.html")

    @app.route("/student/mark_attendance")
    def student_mark_attendance_page():
        return render_template("student/mark_attendance.html")

    # Faculty pages
    @app.route("/faculty/login")
    def faculty_login_page():
        return render_template("faculty/login.html")

    @app.route("/faculty/dashboard")
    def faculty_dashboard_page():
        return render_template("faculty/dashboard.html")

    @app.route("/faculty/take_attendance")
    def faculty_take_attendance_page():
        return render_template("faculty/take_attendance.html")

    @app.route("/faculty/reports")
    def faculty_reports_page():
        return render_template("faculty/reports.html")

    # -------------------------------
    # Background task for session cleanup
    # -------------------------------
    def run_session_cleanup():
        """Background task to periodically clean up expired sessions"""
        from app.utils.session_manager import SessionManager
        from sqlalchemy.exc import OperationalError
        import sqlite3
        
        # Wait a bit for database to be initialized
        time.sleep(5)
        session_manager = SessionManager()
        
        while True:
            try:
                with app.app_context():
                    # Check if tables exist before trying to clean up
                    try:
                        # Expire old sessions
                        expired_count = session_manager.expire_old_sessions()
                        # Delete old closed/expired sessions (older than 7 days)
                        deleted_count = session_manager.delete_old_sessions(older_than_days=7)
                        if expired_count > 0 or deleted_count > 0:
                            print(f"Session cleanup: Expired {expired_count} sessions, Deleted {deleted_count} old sessions")
                    except (OperationalError, sqlite3.OperationalError) as e:
                        # Table doesn't exist yet or database not ready, skip this cycle
                        pass
            except Exception as e:
                # Log other errors but don't crash
                print(f"Error in session cleanup: {str(e)}")
            
            # Run cleanup every 5 minutes
            time.sleep(300)

    # Start session cleanup thread
    session_cleanup_thread = threading.Thread(target=run_session_cleanup, daemon=True)
    session_cleanup_thread.start()

    return app
