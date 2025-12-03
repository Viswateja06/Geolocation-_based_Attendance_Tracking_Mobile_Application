from app import create_app
from werkzeug.security import generate_password_hash

def add_test_faculty():
    app = create_app()
    with app.app_context():
        from app import db
        
        # Import the Employee model from the app context
        Employee = None
        for model in db.Model._decl_class_registry.values():
            if hasattr(model, '__tablename__') and model.__tablename__ == 'employees':
                Employee = model
                break
                
        if not Employee:
            print("Error: Could not find Employee model in registry")
            return

        # Check if test faculty already exists
        test_fac = db.session.query(Employee).filter_by(name='test_faculty').first()
        
        if not test_fac:
            try:
                # Create a new faculty member
                test_fac = Employee(
                    name='test_faculty',
                    email='test@example.com',
                    password_hash=generate_password_hash('test123'),
                    role='faculty',
                    position='Test Professor'
                )
                db.session.add(test_fac)
                db.session.commit()
                print("Test faculty member added successfully!")
                print("-" * 50)
                print("Login with these credentials:")
                print("Username: test_faculty")
                print("Password: test123")
                print("-" * 50)
            except Exception as e:
                print(f"Error adding test faculty: {str(e)}")
                db.session.rollback()
        else:
            print("Test faculty member already exists.")
            print("-" * 50)
            print("Use these credentials to login:")
            print("Username: test_faculty")
            print("Password: test123")
            print("-" * 50)
            
            # Print current password hash for debugging
            print("Current password hash:", test_fac.password_hash)
            print("-" * 50)

if __name__ == "__main__":
    add_test_faculty()
