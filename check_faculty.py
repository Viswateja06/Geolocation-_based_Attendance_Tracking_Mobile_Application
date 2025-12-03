from app import create_app, db

app = create_app()
with app.app_context():
    # Get the Employee model from the app context
    Employee = db.Model._decl_class_registry.get('employee', None)
    if Employee is None:
        print("Error: Could not find Employee model")
    else:
        # Query all faculty members
        faculty = db.session.query(Employee).filter_by(role='faculty').all()
        if not faculty:
            print("No faculty members found in the database.")
        else:
            print("\nFaculty Members in Database:")
            print("-" * 50)
            for fac in faculty:
                print(f"Name: {fac.name}")
                print(f"Email: {fac.email}")
                print(f"Position: {fac.position}")
                print("-" * 50)
        
        # Check if test_faculty exists
        test_fac = db.session.query(Employee).filter_by(name='test_faculty').first()
        if not test_fac:
            print("\nTest faculty member not found. Adding test faculty...")
            try:
                from werkzeug.security import generate_password_hash
                test_fac = Employee(
                    name='test_faculty',
                    email='test@example.com',
                    password_hash=generate_password_hash('test123'),
                    role='faculty',
                    position='Test Professor'
                )
                db.session.add(test_fac)
                db.session.commit()
                print("Added test faculty member. You can log in with:")
                print("Username: test_faculty")
                print("Password: test123")
            except Exception as e:
                print(f"Error adding test faculty: {str(e)}")
                db.session.rollback()
        else:
            print("\nTest faculty member already exists.")
            print(f"Username: {test_fac.name}")
            print("Password: test123")
