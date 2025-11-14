"""
Database migration: Add performance indexes
This script can be run on Railway or any production environment
"""
from app import create_app, db
import sys

def migrate():
    app = create_app()
    with app.app_context():
        print("🔄 Starting database migration...")
        
        with db.engine.connect() as conn:
            try:
                # Add indexes to Attendance table
                print("  Adding indexes to Attendance table...")
                conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_student_id ON attendance(student_id)"))
                conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_faculty_id ON attendance(faculty_id)"))
                conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_date ON attendance(date)"))
                conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_session_student ON attendance(session_id, student_id)"))
                conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_faculty_date ON attendance(faculty_id, date)"))
                
                # Add indexes to Student table
                print("  Adding indexes to Student table...")
                conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_roll_number ON student(roll_number)"))
                conn.execute(db.text("CREATE INDEX IF NOT EXISTS idx_division ON student(division)"))
                
                conn.commit()
                print("✅ Migration completed successfully!")
                return 0
                
            except Exception as e:
                conn.rollback()
                print(f"❌ Migration failed: {str(e)}")
                return 1

if __name__ == "__main__":
    sys.exit(migrate())
