from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
import os
import shutil

app = Flask(__name__)
app.secret_key = "secret_key"

# Add this after your imports and before app configuration
@app.template_filter()
def format_time(value):
    """Format datetime object for display"""
    if not value:
        return ''
    if isinstance(value, datetime):
        # Convert to IST timezone if not already
        if value.tzinfo is None:
            value = IST.localize(value)
       
            return value.strftime("%I:%M %p IST")
    return str(value)

# Make the format function available to templates
app.jinja_env.filters['format_time'] = format_time
# Set the absolute path for the database file
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'attendance.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Set timezone for India
IST = pytz.timezone('Asia/Kolkata')

# Backup directory
backup_dir = os.path.join(basedir, 'backups')
os.makedirs(backup_dir, exist_ok=True)

def create_backup():
    """Create a backup of the database file with a timestamp."""
    try:
        timestamp = datetime.now(IST).strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'attendance_backup_{timestamp}.db')
        shutil.copy(os.path.join(basedir, 'attendance.db'), backup_path)
        print(f"Backup created: {backup_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")

# Database Models with improved data types and timestamp handling
class MorningAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    work_started_on = db.Column(db.Text, nullable=False)
    morning_submitted_time = db.Column(db.DateTime(timezone=True), nullable=False)  # Store as timezone-aware
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(IST))

class EveningAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    work_done_on = db.Column(db.Text, nullable=False)
    evening_submitted_time = db.Column(db.DateTime(timezone=True), nullable=False)  # Store as timezone-aware
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(IST))

# Helper functions for time handling
def get_ist_time():
    """Get current time in IST"""
    return datetime.now(IST)

def format_time_for_display(dt):
    """Format datetime object to Indian Standard Time with AM/PM"""
    if not dt:
        return ''

    # Convert to IST if not already
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, '%H:%M')
            dt = IST.localize(dt.replace(year=datetime.now().year))
        except ValueError:
            return dt
    elif not dt.tzinfo:
        dt = IST.localize(dt)

    return dt.strftime("%I:%M %p ")  # Returns like "10:30 AM IST"

def format_date():
    """Get current date in IST"""
    return get_ist_time().date()

# Your existing ADMINS and STUDENT_NAMES
ADMINS = {
    "admin1": "password1",
    "admin2": "password2",
    "admin3": "password3"
}

STUDENT_NAMES = ["N.Prathima", "R.Pavani Tirupathamma", "v.Pavani", "M.Siva Mahalakshmi", 
                "R.Gayathri", "S.Sanjana", "R.Lakshmi Surekha", "Sk.Husne Fathima", "S.Varshitha",
                "S.Venkata Pavani", "A.Pranathi", "Y.Sri lakshmi", "Y.Lakshmi Deepthi", 
                "K.Mahalakshmi", "Sk.Shakeela", "K.Manoj"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student', methods=['GET', 'POST'])
def student():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            session_type = request.form.get('session')
            work = request.form.get('work')
            
            # Get current IST time
            current_time = get_ist_time()
            
            if not all([name, session_type, work]):
                flash('All fields are required', 'danger')
                return redirect(url_for('student'))

            if session_type == 'morning':
                attendance = MorningAttendance(
                    date=current_time.date(),
                    name=name,
                    work_started_on=work,
                    morning_submitted_time=current_time
                )
            else:
                attendance = EveningAttendance(
                    date=current_time.date(),
                    name=name,
                    work_done_on=work,
                    evening_submitted_time=current_time
                )

            db.session.add(attendance)
            db.session.commit()

            # Create a backup after every successful attendance submission
            create_backup()
            
            # Show exact IST time in flash message
            formatted_time = format_time_for_display(current_time)
            flash(f'Attendance submitted successfully at {formatted_time}!', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting attendance: {str(e)}', 'danger')
            
        return redirect(url_for('student'))

    # Add current IST time to template
    current_ist = format_time_for_display(get_ist_time())
    return render_template('student.html', 
                         student_names=STUDENT_NAMES,
                         current_time=current_ist)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        all_attendance = None
        statistics = []
        attended_days = 0
        absent_days = 0

        if request.method == 'POST':
            all_view_date = request.form.get('all_view_date')
            all_view_session = request.form.get('all_view_session')
            specific_student = request.form.get('specific_student')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            specific_action = request.form.get('specific_action')

            # View attendance for all students
            if all_view_date and all_view_session:
                query_date = datetime.strptime(all_view_date, '%Y-%m-%d').date()
                if all_view_session == 'morning':
                    all_attendance = MorningAttendance.query.filter_by(date=query_date).all()
                else:
                    all_attendance = EveningAttendance.query.filter_by(date=query_date).all()
                
                # Format time for all_attendance records
                if all_attendance:
                    for record in all_attendance:
                        if hasattr(record, 'morning_submitted_time'):
                            record.morning_submitted_time = format_time_for_display(record.morning_submitted_time)
                        if hasattr(record, 'evening_submitted_time'):
                            record.evening_submitted_time = format_time_for_display(record.evening_submitted_time)

            # View attendance or statistics for a specific student
            if specific_student and start_date and end_date:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

                morning_records = MorningAttendance.query.filter(
                    MorningAttendance.name == specific_student,
                    MorningAttendance.date >= start_date_obj,
                    MorningAttendance.date <= end_date_obj
                ).all()

                evening_records = EveningAttendance.query.filter(
                    EveningAttendance.name == specific_student,
                    EveningAttendance.date >= start_date_obj,
                    EveningAttendance.date <= end_date_obj
                ).all()

                if specific_action == 'view_statistics':
                    all_dates = set(record.date for record in morning_records + evening_records)
                    for date in sorted(all_dates):
                        morning = next((r for r in morning_records if r.date == date), None)
                        evening = next((r for r in evening_records if r.date == date), None)
                        stat = {
                            "date": date.strftime('%Y-%m-%d'),
                            "work_started_on": morning.work_started_on if morning else '',
                            "morning_submitted_time": format_time_for_display(morning.morning_submitted_time) if morning else '',
                            "work_done_on": evening.work_done_on if evening else '',
                            "evening_submitted_time": format_time_for_display(evening.evening_submitted_time) if evening else ''
                        }
                        statistics.append(stat)

                elif specific_action == 'view_attendance':
                    total_days = (end_date_obj - start_date_obj).days + 1
                    attended_days = len(set(record.date for record in morning_records + evening_records))
                    absent_days = total_days - attended_days

        return render_template(
            'admin.html',
            student_names=STUDENT_NAMES,
            all_attendance=all_attendance,
            statistics=statistics,
            attended_days=attended_days,
            absent_days=absent_days,
            current_time=format_time_for_display(get_ist_time())
        )

    except Exception as e:
        flash(f'Error retrieving data: {str(e)}', 'danger')
        return redirect(url_for('admin'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in ADMINS and ADMINS[username] == password:
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username/password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        # Create the database directory if it doesn't exist
        os.makedirs(basedir, exist_ok=True)
        
        # Create all database tables
        db.create_all()

        # Create an initial backup of the database
        create_backup()
        
    app.run(debug=True)
