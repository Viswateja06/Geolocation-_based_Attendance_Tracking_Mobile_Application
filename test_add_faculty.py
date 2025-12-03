# Test script to add a faculty member
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app and create it
from app import create_app, db
from werkzeug.security import generate_password_hash

# Create app and get context
app, Employee = create_app()
with app.app_context():
    # Now add the test faculty
    test_fac = Employee.query.filter_by(name='test_faculty').first()
    
    if not test_fac:
        test_fac = Employee(
            name='test_faculty',
            email='test@example.com',
            password_hash=generate_password_hash('test123'),
            role='faculty',
            position='Test Professor'
        )
        db.session.add(test_fac)
        db.session.commit()
        print("✓ Test faculty member added successfully!")
    else:
        print("✓ Test faculty member already exists!")
    
    print("\nLogin Credentials:")
    print("-" * 40)
    print("Username: test_faculty")
    print("Password: test123")
    print("-" * 40)
