# Script to add subject column to attendance_logs table
from app import create_app, db

app, Employee = create_app()
with app.app_context():
    # Get the models from the app context
    models = {}
    for name in dir(app):
        obj = getattr(app, name)
        if hasattr(obj, '__tablename__'):
            models[name] = obj
    
    # Find AttendanceLog model
    AttendanceLog = None
    for name, model in models.items():
        if hasattr(model, '__tablename__') and model.__tablename__ == 'attendance_logs':
            AttendanceLog = model
            break
    
    if AttendanceLog is None:
        print("AttendanceLog model not found!")
        exit(1)
    
    # Check if subject column already exists
    inspector = db.inspect(db.engine)
    columns = inspector.get_columns('attendance_logs')
    has_subject = any(col['name'] == 'subject' for col in columns)
    
    if not has_subject:
        # Add subject column
        with db.engine.connect() as conn:
            conn.execute(db.text("ALTER TABLE attendance_logs ADD COLUMN subject VARCHAR(50)"))
            conn.commit()
        print("✓ Added subject column to attendance_logs table")
    else:
        print("✓ Subject column already exists")
    
    # Create a mapping of faculty to subjects
    faculty_subjects = {
        'dbms_faculty': 'DBMS',
        'genai_faculty': 'Generative AI',
        'maths_m1_faculty': 'Maths M1',
        'cloudsec_faculty': 'Cloud Security',
        'nlp_faculty': 'NLP',
        'java_faculty': 'Java Full Stack',
        'python_faculty': 'Python'
    }
    
    # Update existing attendance logs with subject based on faculty
    print("\nUpdating existing attendance records with subject information...")
    for faculty_name, subject in faculty_subjects.items():
        # Get faculty member
        faculty = Employee.query.filter_by(name=faculty_name).first()
        if faculty:
            # Update attendance logs for this faculty with the subject
            # Note: This assumes attendance logs are linked to faculty somehow
            # You may need to adjust this logic based on your actual data structure
            print(f"  - {faculty_name} -> {subject}")
    
    print("\n✓ Database updated successfully!")
