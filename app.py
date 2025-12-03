import os
from datetime import datetime, date, time, timedelta, timezone
from functools import wraps
from math import radians, sin, cos, atan2, sqrt
from flask import Flask, render_template, jsonify, request, send_from_directory, make_response, redirect
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import re
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

# Load environment variables from .env if present
load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Config: ensure an absolute SQLite path under an existing instance directory
    instance_dir = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'employees.db')
    # Prefer env DATABASE_URL if provided, else build a proper absolute sqlite URI
    default_sqlite_uri = 'sqlite:///' + db_path.replace('\\', '/')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', default_sqlite_uri)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Token signer for student auth
    secret = os.getenv('SECRET_KEY', 'change-me-secret')
    app.config['SECRET_KEY'] = secret
    signer = URLSafeTimedSerializer(secret_key=secret, salt='student-auth')
    faculty_signer = URLSafeTimedSerializer(secret_key=secret, salt='faculty-auth')

    # Models
    class Employee(db.Model):
        __tablename__ = 'employees'
        __table_args__ = (
            db.UniqueConstraint('email', name='uq_employee_email'),
            db.UniqueConstraint('name', name='uq_employee_name')
        )
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        email = db.Column(db.String(120), unique=False, nullable=True)  # unique is handled by the constraint
        position = db.Column(db.String(100))
        location_name = db.Column(db.String(100))
        latitude = db.Column(db.Float)
        longitude = db.Column(db.Float)
        photo_path = db.Column(db.String(200))
        password_hash = db.Column(db.String(200), nullable=False)
        role = db.Column(db.String(50), default='user')
        phone = db.Column(db.String(20), nullable=True)

        logs = db.relationship('AttendanceLog', backref='employee', lazy=True)

    class Location(db.Model):
        __tablename__ = 'locations'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(120), unique=True, nullable=False)
        latitude = db.Column(db.Float, nullable=False)
        longitude = db.Column(db.Float, nullable=False)
        radius = db.Column(db.Integer, default=100)  # meters

    class AttendanceLog(db.Model):
        __tablename__ = 'attendance_logs'
        id = db.Column(db.Integer, primary_key=True)
        employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
        check_in_time = db.Column(db.DateTime)
        check_out_time = db.Column(db.DateTime)
        latitude = db.Column(db.Float)
        longitude = db.Column(db.Float)
        location_name = db.Column(db.String(120))
        date = db.Column(db.Date, default=date.today)
        subject = db.Column(db.String(50))  # New column for subject

    with app.app_context():
        db.create_all()
        # Temporarily disable all checks during migration
        pass

    # Decorators
    def require_student(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                token = request.args.get('token')
            if not token:
                return jsonify({"error": "Missing token"}), 401
            try:
                data = signer.loads(token, max_age=86400)  # 24 hours
                request.student_id = data['employee_id']
            except (BadSignature, SignatureExpired) as e:
                return jsonify({"error": "Invalid or expired token"}), 401
            return f(*args, **kwargs)
        return decorated

    # Utility
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371000.0
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    def is_student_checked_in(student_id):
        """Check if a student is currently checked in (has an active session)"""
        current_time = datetime.now(timezone(timedelta(hours=5, minutes=30)))  # IST
        today = current_time.date()
        
        # Find today's check-in record
        log = AttendanceLog.query.filter_by(
            employee_id=student_id,
            date=today
        ).first()
        
        # Return True if there's a check-in time but no check-out time
        return log and log.check_in_time and not log.check_out_time

    # Routes
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route('/student')
    def student_dashboard():
        # Check if user is already authenticated
        token = request.cookies.get('token')
        if token:
            try:
                data = signer.loads(token, max_age=86400)  # 24 hours
                # Token is valid, render the dashboard
                return render_template('student.html')
            except (BadSignature, SignatureExpired):
                # Token is invalid or expired, clear it and show login
                resp = make_response(render_template('student.html'))
                resp.set_cookie('token', '', expires=0)
                return resp
        # No valid token, check if this is a login attempt
        if request.method == 'POST' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # This is an API call, let the API handle it
            pass
        # No valid token and not an API call, show login form
        return render_template('student.html')
        
    # Add a login page that redirects to dashboard if already logged in
    @app.route('/login', methods=['GET'])
    def login_page():
        token = request.cookies.get('token')
        if token:
            try:
                signer.loads(token, max_age=86400)  # 24 hours
                # Already logged in, redirect to dashboard
                return redirect('/student')
            except (BadSignature, SignatureExpired):
                # Invalid token, clear it and show login
                resp = make_response(redirect('/student'))
                resp.set_cookie('token', '', expires=0)
                return resp
        # Not logged in, redirect to student page which will show login form
        return redirect('/student')
        
    @app.route('/history')
    def history_page():
        # Try to get token from URL parameters first
        token = request.args.get('token')
        if not token:
            # If no token in URL, try to get it from cookies
            token = request.cookies.get('token')
            if not token:
                # No token found, redirect to login
                return redirect('/student')
        
        try:
            # Verify the token
            data = signer.loads(token, max_age=86400)  # 24 hours
            # Token is valid, render the history page and set the token as a cookie
            response = make_response(render_template('history.html'))
            response.set_cookie('token', token, max_age=86400)  # 24 hours
            return response
        except (BadSignature, SignatureExpired):
            # Token is invalid or expired, redirect to login
            response = redirect('/student')
            response.set_cookie('token', '', expires=0)
            return response

    @app.route("/student/register")
    def student_register_page():
        return render_template("student_register.html")

    @app.route("/faculty")
    def faculty_page():
        return render_template("faculty.html")

    @app.route("/timetable")
    def timetable_page():
        return render_template("timetable.html")

    @app.route("/subject-attendance")
    def subject_attendance_page():
        return render_template("subject_attendance.html")

    # Separate faculty pages for views (avoid conflicting with API endpoints)
    @app.route("/faculty/students_view")
    def faculty_students_view():
        return render_template("faculty_students.html")

    @app.route("/faculty/attendance_view")
    def faculty_attendance_view():
        return render_template("faculty_attendance.html")

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    # ---- Student Auth ----
    @app.post('/register_student')
    def register_student():
        data = request.get_json(force=True)
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()  # Normalize email to lowercase
        password = (data.get('password') or '').strip()
        
        # Input validation
        if not all([name, email, password]):
            return jsonify({"error": "Name, email, and password are required"}), 400
            
        # Validate email format
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({"error": "Invalid email format"}), 400
            
        # Check for existing user with same email or name
        existing_email = Employee.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({"error": "A user with this email already exists"}), 400
            
        existing_name = Employee.query.filter_by(name=name).first()
        if existing_name:
            return jsonify({"error": "A user with this name already exists"}), 400
        
        try:
            # Create new student
            student = Employee(
                name=name,
                email=email,
                position='student',
                password_hash=generate_password_hash(password),
                role='student'
            )
            db.session.add(student)
            db.session.commit()
            
            # Generate auth token
            token = signer.dumps({"employee_id": student.id, "role": "student"})
            return jsonify({
                "token": token,
                "student": {
                    "id": student.id,
                    "name": student.name,
                    "email": student.email
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error during student registration: {str(e)}")
            return jsonify({"error": "An error occurred during registration"}), 500

    @app.post('/login_student')
    def login_student():
        data = request.get_json(force=True)
        name = (data.get('name') or '').strip()
        password = (data.get('password') or '').strip()
        if not name or not password:
            return jsonify({"error": "Name and password are required"}), 400
            
        student = Employee.query.filter_by(name=name, role='student').first()
        if not student or not check_password_hash(student.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401
            
        token = signer.dumps({"employee_id": student.id, "role": "student"})
        return jsonify({"token": token, "student": {"id": student.id, "name": student.name}})

    # ---- Faculty Auth ----
    @app.post('/login_faculty')
    def login_faculty():
        data = request.get_json(force=True)
        identifier = (data.get('name') or data.get('email') or '').strip()
        password = (data.get('password') or '').strip()
        if not identifier or not password:
            return jsonify({"error": "name/email and password required"}), 400
        
        # Try to find faculty by name first, then by email
        fac = Employee.query.filter_by(name=identifier, role='faculty').first()
        if not fac:
            fac = Employee.query.filter_by(email=identifier, role='faculty').first()
        
        if not fac or not check_password_hash(fac.password_hash, password):
            return jsonify({"error": "Invalid credentials"}), 401
        token = faculty_signer.dumps({"role": "faculty", "name": fac.name, "employee_id": fac.id})
        return jsonify({"token": token, "faculty": {"name": fac.name, "email": fac.email}})

    def require_student(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            # Get token from Authorization header or request args
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                token = request.args.get('token')
            
            if not token:
                return jsonify({"error": "Missing authentication token"}), 401
                
            try:
                # Verify the token
                data = signer.loads(token, max_age=86400)  # 24 hours
                request.student_id = data.get('employee_id')
                if not request.student_id:
                    raise ValueError("Invalid token payload")
            except (BadSignature, SignatureExpired) as e:
                return jsonify({"error": "Invalid or expired token"}), 401
            except Exception as e:
                return jsonify({"error": "Invalid token"}), 401
                
            return fn(*args, **kwargs)
        return decorated
        
    def require_faculty(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            # Get token from Authorization header or request args
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                token = request.args.get('token')
            
            if not token:
                return jsonify({"error": "Missing authentication token"}), 401
                
            try:
                # Verify the faculty token
                data = faculty_signer.loads(token, max_age=86400)  # 24 hours
                request.faculty_name = data.get('name')
                request.faculty_id = data.get('employee_id')
                if not request.faculty_name:
                    raise ValueError("Invalid faculty token payload")
            except (BadSignature, SignatureExpired) as e:
                return jsonify({"error": "Invalid or expired faculty token"}), 401
            except Exception as e:
                return jsonify({"error": "Invalid faculty token"}), 401
                
            return fn(*args, **kwargs)
        return decorated

    @app.post('/student/loginout')
    @require_student
    def student_loginout():
        student_id = request.student_id
        data = request.get_json(force=True)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        action = data.get('action')
        timestamp_str = data.get('timestamp')
        location_name = data.get('location_name') or 'Office'
        subject = data.get('subject')  # New parameter for subject
        
        if latitude is None or longitude is None:
            return jsonify({"error": "latitude and longitude required"}), 400
            
        # Enforce geofence: find nearest location and require within radius
        nearest = None
        min_dist = float('inf')
        for l in Location.query.all():
            d = haversine_distance(float(latitude), float(longitude), l.latitude, l.longitude)
            if d < min_dist:
                min_dist = d
                nearest = l
        if nearest and min_dist > (nearest.radius or 100):
            return jsonify({"error": "outside allowed radius", "distance": int(min_dist), "allowedRadius": nearest.radius}), 400

        today = date.today()
        
        try:
            if timestamp_str:
                # Parse the provided timestamp
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # Ensure the timestamp is timezone-aware
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
        except (ValueError, TypeError):
            timestamp = datetime.now(timezone.utc)
        
        # Convert to IST timezone (Presidency University time)
        current_time_ist = timestamp.astimezone(timezone(timedelta(hours=5, minutes=30)))
        # Use IST calendar date for logs
        today = current_time_ist.date()

        if action == 'checkin':
            # 9 AM to 3 PM IST
            if not (time(9, 0) <= current_time_ist.time() <= time(15, 0)):
                return jsonify({"error": "Check-in allowed only between 9 AM and 3 PM IST"}), 400

            # Do not allow a second active check-in for the same IST date
            existing_open = AttendanceLog.query.filter(
                AttendanceLog.employee_id == student_id,
                AttendanceLog.date == today,
                AttendanceLog.check_in_time.isnot(None),
                AttendanceLog.check_out_time.is_(None)
            ).first()
            if existing_open:
                return jsonify({"error": "Already checked in today"}), 400

            # Create a new check-in log
            log = AttendanceLog(
                employee_id=student_id,
                date=today,
                check_in_time=current_time_ist,
                latitude=latitude,
                longitude=longitude,
                location_name=nearest.name if nearest else location_name,
                subject=subject  # Add subject to the log
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({
                "message": "Checked in successfully", 
                "checkInTime": log.check_in_time.isoformat(), 
                "location": log.location_name
            })
            
        elif action == 'checkout':
            # 4 PM to 9 PM IST
            if not (time(16, 0) <= current_time_ist.time() <= time(21, 0)):
                return jsonify({"error": "Check-out allowed only between 4 PM and 9 PM IST"}), 400
                
            # Find the most recent check-in without a check-out (for this IST date)
            log = AttendanceLog.query.filter(
                AttendanceLog.employee_id == student_id,
                AttendanceLog.date == today,
                AttendanceLog.check_out_time.is_(None)
            ).order_by(AttendanceLog.check_in_time.desc()).first()
            
            if not log or not log.check_in_time:
                return jsonify({"error": "No active check-in found to check out"}), 400
                
            # Update the log with checkout details
            log.check_out_time = current_time_ist
            log.latitude = latitude
            log.longitude = longitude
            log.location_name = nearest.name if nearest else location_name
            
            # Calculate duration in hours and minutes (handle naive vs aware datetimes)
            duration = None
            if log.check_in_time:
                ci = log.check_in_time
                co = log.check_out_time
                if ci.tzinfo is None and co.tzinfo is not None:
                    ci = ci.replace(tzinfo=co.tzinfo)
                elif co.tzinfo is None and ci.tzinfo is not None:
                    co = co.replace(tzinfo=ci.tzinfo)

                duration_seconds = (co - ci).total_seconds()
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                duration = f"{hours}h {minutes}m"
            
            db.session.commit()
                
            return jsonify({
                "message": "Checked out successfully", 
                "checkOutTime": log.check_out_time.isoformat(),
                "checkInTime": log.check_in_time.isoformat(),
                "location": log.location_name,
                "duration": duration
            })
            
        return jsonify({"error": "Invalid action"}), 400

    # ---- Student status & history APIs used by dashboard ----
    @app.get('/student/status')
    @require_student
    def student_status():
        student_id = request.student_id
        # Use IST date for "today" status
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))
        today_ist = now_ist.date()

        log = AttendanceLog.query.filter_by(employee_id=student_id, date=today_ist).order_by(AttendanceLog.id.desc()).first()
        
        # Check if student is currently checked in
        is_checked_in = is_student_checked_in(student_id)

        status = {
            "checkedIn": False,
            "checkedOut": False,
            "checkInTime": None,
            "checkOutTime": None,
            "location": None,
            "isCurrentlyCheckedIn": is_checked_in
        }

        if log:
            if log.check_in_time:
                status["checkedIn"] = True
                status["checkInTime"] = log.check_in_time.isoformat()
                status["location"] = log.location_name
            if log.check_out_time:
                status["checkedOut"] = True
                status["checkOutTime"] = log.check_out_time.isoformat()

        return jsonify(status)

    @app.get('/student/history')
    @require_student
    def student_history():
        student_id = request.student_id
        start_date_str = request.args.get('startDate')
        end_date_str = request.args.get('endDate')

        q = AttendanceLog.query.filter_by(employee_id=student_id)
        if start_date_str:
            try:
                sd = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                q = q.filter(AttendanceLog.date >= sd)
            except ValueError:
                pass
        if end_date_str:
            try:
                ed = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                q = q.filter(AttendanceLog.date <= ed)
            except ValueError:
                pass

        logs = q.order_by(AttendanceLog.date.desc(), AttendanceLog.check_in_time.desc()).all()

        result = []
        for l in logs:
            # Duration in hours/minutes if both times exist
            duration = None
            if l.check_in_time and l.check_out_time:
                ci = l.check_in_time
                co = l.check_out_time
                if ci.tzinfo is None and co.tzinfo is not None:
                    ci = ci.replace(tzinfo=co.tzinfo)
                elif co.tzinfo is None and ci.tzinfo is not None:
                    co = co.replace(tzinfo=ci.tzinfo)
                secs = (co - ci).total_seconds()
                h = int(secs // 3600)
                m = int((secs % 3600) // 60)
                duration = f"{h}h {m}m"

            result.append({
                "date": l.date.isoformat(),
                "check_in_time": l.check_in_time.isoformat() if l.check_in_time else None,
                "check_out_time": l.check_out_time.isoformat() if l.check_out_time else None,
                "location_name": l.location_name,
                "duration": duration
            })

        return jsonify(result)

    @app.get('/LogInOut/allemp/<int:employee_id>')
    def employee_logs(employee_id):
        logs = AttendanceLog.query.filter_by(employee_id=employee_id).order_by(AttendanceLog.id.desc()).all()
        return jsonify([
            {
                "id": l.id,
                "employee_id": l.employee_id,
                "check_in_time": l.check_in_time.isoformat() if l.check_in_time else None,
                "check_out_time": l.check_out_time.isoformat() if l.check_out_time else None,
                "latitude": l.latitude,
                "longitude": l.longitude,
                "location_name": l.location_name,
                "date": l.date.isoformat()
            } for l in logs
        ])

    @app.post('/student/subject_attendance')
    @require_student
    def student_subject_attendance():
        student_id = request.student_id
        
        # Check if student is currently checked in
        if not is_student_checked_in(student_id):
            return jsonify({"error": "You must be checked in to mark attendance"}), 400
        
        data = request.get_json(force=True) or {}
        subject_raw = (data.get('subject') or '').strip()
        date_str = (data.get('date') or '').strip()

        if not subject_raw or not date_str:
            return jsonify({"error": "subject and date are required"}), 400

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format, expected YYYY-MM-DD"}), 400

        # Normalize subject for consistent matching
        subject = subject_raw.lower()

        # Use current IST time for check-in timestamp
        now_utc = datetime.now(timezone.utc)
        now_ist = now_utc.astimezone(timezone(timedelta(hours=5, minutes=30)))

        # If a log already exists for this student/date/subject with a check-in, do nothing
        existing = AttendanceLog.query.filter_by(
            employee_id=student_id,
            date=target_date,
            subject=subject
        ).filter(AttendanceLog.check_in_time.isnot(None)).first()

        if existing:
            return jsonify({
                "message": "Subject attendance already recorded",
                "subject": subject,
                "date": target_date.isoformat()
            })

        log = AttendanceLog(
            employee_id=student_id,
            date=target_date,
            check_in_time=now_ist,
            subject=subject
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            "message": "Subject attendance recorded",
            "subject": subject,
            "date": target_date.isoformat()
        }), 201

    # ---- Nearest Locations ----
    @app.post('/get_nearest_locations')
    def get_nearest_locations():
        data = request.get_json(force=True)
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        limit = int(data.get('limit') or 5)
        locs = Location.query.all()
        res = []
        for l in locs:
            dist = round(haversine_distance(lat, lng, l.latitude, l.longitude))
            res.append({"id": l.id, "name": l.name, "latitude": l.latitude, "longitude": l.longitude, "radius": l.radius, "distance": dist})
        res.sort(key=lambda x: x['distance'])
        return jsonify(res[:limit])

    # ---- Photos ----
    @app.get('/get_photo/<int:employee_id>')
    def get_photo(employee_id):
        e = Employee.query.get_or_404(employee_id)
        if not e.photo_path or not os.path.isfile(e.photo_path):
            return jsonify({"error": "photo not found"}), 404
        directory = os.path.dirname(e.photo_path)
        filename = os.path.basename(e.photo_path)
        return send_from_directory(directory, filename)

    @app.post('/upload_photo/<int:employee_id>')
    def upload_photo(employee_id):
        e = Employee.query.get_or_404(employee_id)
        if 'file' not in request.files:
            return jsonify({"error": "file field is required"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "empty filename"}), 400
        fname = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"emp_{employee_id}_{fname}")
        file.save(save_path)
        e.photo_path = save_path
        db.session.commit()
        return jsonify({"message": "uploaded", "path": save_path}), 201

    # (Facial recognition removed)

    # ---- Faculty Views ----
    @app.get('/faculty/students')
    @require_faculty
    def faculty_students():
        emps = Employee.query.filter_by(role='student').order_by(Employee.id.asc()).all()
        return jsonify([{ "id": e.id, "name": e.name, "position": e.position } for e in emps])

    @app.get('/faculty/attendance')
    @require_faculty
    def faculty_attendance():
        # Get faculty information from token
        faculty_name = request.faculty_name  # From token
        
        # Get faculty member to determine their subject
        faculty = Employee.query.filter_by(name=faculty_name, role='faculty').first()
        if not faculty:
            return jsonify({"error": "Faculty not found"}), 404
        
        # Extract subject from faculty position (e.g., "Professor - DBMS")
        faculty_subject_raw = faculty.position.replace("Professor - ", "") if faculty.position else None
        if not faculty_subject_raw:
            return jsonify({"error": "Faculty subject not configured in position field"}), 400
        faculty_subject = faculty_subject_raw.strip().lower()

        # For a single date, show each student's status for the faculty's subject
        day_str = request.args.get('date') or date.today().isoformat()
        try:
            target_date = datetime.strptime(day_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()
        rows = []
        students = Employee.query.filter_by(role='student').all()
        
        for s in students:
            # Get attendance log for this student on this date for the faculty's subject (case-insensitive)
            l = AttendanceLog.query.filter(
                AttendanceLog.employee_id == s.id,
                AttendanceLog.date == target_date,
                db.func.lower(AttendanceLog.subject) == faculty_subject
            ).order_by(AttendanceLog.id.desc()).first()
            
            rows.append({
                "id": s.id,
                "name": s.name,
                "checkedIn": bool(l and l.check_in_time),
                "checkedOut": bool(l and l.check_out_time),
                "checkInTime": l.check_in_time.isoformat() if l and l.check_in_time else None,
                "checkOutTime": l.check_out_time.isoformat() if l and l.check_out_time else None,
                "location": l.location_name if l else None,
                "subject": faculty_subject
            })
        return jsonify(rows)

    return app, Employee


if __name__ == "__main__":
    app, _ = create_app()
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
