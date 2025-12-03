# Migration script to add subject column to attendance_logs table
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'employees.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if subject column exists
        cursor.execute("PRAGMA table_info(attendance_logs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'subject' not in columns:
            # Add subject column
            cursor.execute("ALTER TABLE attendance_logs ADD COLUMN subject VARCHAR(50)")
            print("✓ Added subject column to attendance_logs table")
        else:
            print("✓ Subject column already exists")
        
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
else:
    print("Database file not found. Run the app first to create it.")
