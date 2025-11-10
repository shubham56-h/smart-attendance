from app import create_app, db
from app.models import Faculty
from app.utils import hash_password

app = create_app()

def create_faculty_account(full_name, email, password):
    """Create a faculty account in the database"""
    with app.app_context():
        # Check if faculty already exists
        existing = Faculty.query.filter_by(email=email).first()
        if existing:
            print(f"❌ Faculty with email '{email}' already exists!")
            print(f"   Name: {existing.full_name}")
            return False
        
        # Create new faculty member
        faculty = Faculty(
            full_name=full_name,
            email=email,
            password=hash_password(password)
        )
        db.session.add(faculty)
        db.session.commit()
        
        print(f"✅ Faculty created successfully!")
        print(f"   Name: {full_name}")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        return True

if __name__ == "__main__":
    print("=== Create Faculty Account ===\n")
    
    # Option 1: Interactive mode
    print("Enter faculty details:")
    full_name = input("Full Name: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    
    if full_name and email and password:
        create_faculty_account(full_name, email, password)
    else:
        print("❌ All fields are required!")
    
    # Option 2: Create default test faculty (uncomment if needed)
    # create_faculty_account("Test Faculty", "faculty@example.com", "password123")
