# Simple script to add a test faculty member
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Get all models to find Employee
    Employee = None
    for name, model in db.Model._decl_class_registry.items():
        if hasattr(model, '__tablename__') and model.__tablename__ == 'employees':
            Employee = model
            break
    
    if Employee is None:
        print("Employee model not found!")
        sys.exit(1)
    
    # Check if test faculty exists
    test_fac = Employee.query.filter_by(name='test_faculty').first()
    
    if not test_fac:
        # Create test faculty
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
        print("\nLogin Credentials:")
        print("-" * 40)
        print("Username: test_faculty")
        print("Password: test123")
        print("-" * 40)
    else:
        print("✓ Test faculty member already exists!")
        print("\nLogin Credentials:")
        print("-" * 40)
        print("Username: test_faculty")
        print("Password: test123")
        print("-" * 40)
