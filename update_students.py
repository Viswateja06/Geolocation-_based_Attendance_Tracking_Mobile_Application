import os
import csv
from werkzeug.security import generate_password_hash
from app import create_app, db
from app import Employee  # Import your models

def update_student_data():
    app = create_app()
    with app.app_context():
        # Clear existing student data (optional, uncomment if you want to start fresh)
        # Employee.query.filter_by(role='student').delete()
        
        # Read CSV and update students
        csv_path = r"C:\Users\nalla\Downloads\student_details_200.csv"
        updated_count = 0
        created_count = 0
        
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Check if student exists
                student = Employee.query.filter_by(
                    name=row['name'],
                    role='student'
                ).first()
                
                if student:
                    # Update existing student
                    student.email = row['email']
                    student.phone = row['phone']
                    student.password_hash = generate_password_hash(row['password'])
                    updated_count += 1
                else:
                    # Create new student
                    student = Employee(
                        name=row['name'],
                        email=row['email'],
                        phone=row['phone'],
                        password_hash=generate_password_hash(row['password']),
                        role='student',
                        position='student'
                    )
                    db.session.add(student)
                    created_count += 1
            
            # Commit all changes
            db.session.commit()
            
        print(f"Update complete! Created: {created_count}, Updated: {updated_count} students.")

if __name__ == "__main__":
    update_student_data()
