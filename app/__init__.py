from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configure database (SQLite for now)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'attendance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'smartattende'

    # Initialize database
    db.init_app(app)

    # Import and register blueprints (routes)
    from app.routes.faculty_routes import faculty_bp
    from app.routes.student_routes import student_bp

    app.register_blueprint(faculty_bp, url_prefix="/faculty")
    app.register_blueprint(student_bp, url_prefix="/student")

    return app
