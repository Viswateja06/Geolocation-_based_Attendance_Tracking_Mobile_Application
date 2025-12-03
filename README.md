# GeoAttendance System

A comprehensive attendance management system for educational institutions with location-based check-in/check-out, subject-wise attendance tracking, and role-based access for students and faculty.

## Features

### Student Portal
- **Location-based Attendance**: Check-in/check-out using GPS location with geofencing
- **Subject-wise Attendance**: View attendance by subject across different time slots
- **Weekly Timetable**: View class schedule with subject-wise organization
- **Attendance History**: Track and view historical attendance data
- **Weekend Handling**: Automatic detection of weekends with "No Classes" display
- **Real-time Status**: Live attendance status updates

### Faculty Portal
- **Subject-specific Attendance**: View attendance for assigned subjects only
- **Visual Attendance Display**: Color-coded student names (green for present, red for absent)
- **Attendance Statistics**: Present/absent counts for each subject
- **Weekend Support**: "No Classes" message on weekends
- **Simplified Interface**: Clean dashboard without student management features

### Authentication & Security
- **Role-based Access**: Separate login systems for students and faculty
- **JWT Token Authentication**: Secure session management
- **Password Hashing**: Secure password storage
- **Time-based Restrictions**: Check-in (9 AM - 3 PM) and check-out (4 PM - 9 PM) windows

### Database Management
- **SQLite Database**: Lightweight, portable database solution
- **Migration Support**: Database schema versioning with Flask-Migrate
- **Subject Tracking**: Attendance logs with subject categorization

## Structure

- `app.py` — Main Flask application with all routes and models
- `templates/` — HTML templates for all pages
  - `student.html` — Student dashboard and login
  - `faculty.html` — Faculty login and dashboard
  - `faculty_attendance.html` — Faculty attendance view
  - `subject_attendance.html` — Subject-wise attendance view
  - `timetable.html` — Weekly timetable view
  - `history.html` — Attendance history view
- `static/` — JavaScript files for client-side functionality
  - `student.js` — Student portal logic
  - `faculty.js` — Faculty portal logic
  - `faculty_attendance.js` — Faculty attendance display
- `add_faculty.py` — Script to add faculty members
- `test_add_faculty.py` — Script to add test faculty member
- `migrate_subject_column.py` — Database migration script

## Setup

1. Create and activate a virtual environment (Windows PowerShell):
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. (Optional) Create a `.env` file:
   ```env
   PORT=5000
   FLASK_DEBUG=1
   ```

4. Run the app:
   ```powershell
   python app.py
   ```

5. Open http://localhost:5000 in your browser.

## Faculty Login Credentials

The system comes with pre-configured faculty accounts for different subjects:

| Subject | Username | Password |
|---------|----------|----------|
| DBMS | dbms_faculty | dbms@123 |
| Generative AI | genai_faculty | genai@123 |
| Maths M1 | maths_m1_faculty | maths@123 |
| Cloud Security | cloudsec_faculty | cloudsec@123 |
| NLP | nlp_faculty | nlp@123 |
| Java Full Stack | java_faculty | java@123 |
| Python | python_faculty | python@123 |

## Adding Faculty Members

To add new faculty members or reset existing ones:

```powershell
python add_faculty.py
```

This script will add all faculty members with their respective credentials.

## Database Schema

The system uses the following main tables:

- **employees**: Stores student and faculty information
- **attendance_logs**: Tracks check-in/check-out records with subject information
- **locations**: Defines valid check-in locations with geofence boundaries

## Time Restrictions

- **Check-in**: 9:00 AM - 3:00 PM (IST)
- **Check-out**: 4:00 PM - 9:00 PM (IST)
- **Weekends**: No classes on Saturday and Sunday

## Subject Schedule

The system follows a structured weekly schedule with subjects organized in time slots:

- **Monday-Friday**: Full day schedule with breaks and lunch
- **Subjects**: DBMS, Generative AI, Maths M1, Cloud Security, NLP, Java Full Stack, Python
- **Break Times**: 10:40-10:50 AM and 2:10-2:20 PM
- **Lunch**: 12:30-1:20 PM

## Technical Details

- **Backend**: Flask with SQLAlchemy ORM
- **Frontend**: Vanilla JavaScript with responsive HTML/CSS
- **Database**: SQLite with migration support
- **Authentication**: JWT tokens with role-based access
- **Location Services**: HTML5 Geolocation API with haversine distance calculations
