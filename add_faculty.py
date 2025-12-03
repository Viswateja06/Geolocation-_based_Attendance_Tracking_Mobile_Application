from app import create_app, db
from werkzeug.security import generate_password_hash

def add_faculty_members():
    app, Employee = create_app()
    with app.app_context():
        # Faculty data: name, email, password, subject
        faculty_data = [
            {"name": "dbms_faculty", "email": "dbms@example.com", "password": "dbms@123", "subject": "DBMS"},
            {"name": "genai_faculty", "email": "genai@example.com", "password": "genai@123", "subject": "Generative AI"},
            {"name": "maths_m1_faculty", "email": "maths@example.com", "password": "maths@123", "subject": "Maths M1"},
            {"name": "cloudsec_faculty", "email": "cloudsec@example.com", "password": "cloudsec@123", "subject": "Cloud Security"},
            {"name": "nlp_faculty", "email": "nlp@example.com", "password": "nlp@123", "subject": "NLP"},
            {"name": "java_faculty", "email": "java@example.com", "password": "java@123", "subject": "Java Full Stack"},
            {"name": "python_faculty", "email": "python@example.com", "password": "python@123", "subject": "Python"}
        ]

        for fac in faculty_data:
            # Check if faculty already exists
            existing = Employee.query.filter_by(email=fac["email"]).first()
            if not existing:
                try:
                    faculty = Employee(
                        name=fac["name"],
                        email=fac["email"],
                        position=f"Professor - {fac['subject']}",
                        password_hash=generate_password_hash(fac["password"]),
                        role='faculty'
                    )
                    db.session.add(faculty)
                    print(f"Added faculty for {fac['subject']}")
                except Exception as e:
                    print(f"Error adding {fac['name']}: {str(e)}")
                    db.session.rollback()
            else:
                print(f"Faculty {fac['name']} already exists")

        db.session.commit()
        print("\nFaculty members added successfully!")
        print("\nFaculty Login Credentials:")
        print("-" * 50)
        for fac in faculty_data:
            print(f"Subject: {fac['subject']}")
            print(f"Username: {fac['name']}")
            print(f"Password: {fac['password']}")
            print("-" * 50)

if __name__ == "__main__":
    add_faculty_members()
