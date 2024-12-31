from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class MorningAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    work_started_on = db.Column(db.String(200), nullable=False)
    morning_submitted_time = db.Column(db.String(10), nullable=False)

class EveningAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    work_done_on = db.Column(db.String(200), nullable=False)
    evening_submitted_time = db.Column(db.String(10), nullable=False)

# Helper functions
def format_time():
    return datetime.now().strftime("%H:%M")

def format_date():
    return datetime.now().strftime("%Y-%m-%d")

# Predefined admin credentials
ADMINS = {
    "admin1": "password1",
    "admin2": "password2",
    "admin3": "password3"
}

# Predefined student names
STUDENT_NAMES = [ "N.Prathima","R.Pavani Tirupathamma","v.Pavani","M.Siva Mahalakshmi","R.Gayathri","S.Sanjana","R.Lakshmi Surekha","Sk.Husne Fathima","S.Varshitha",
                 "S.Venkata Pavani","A.Pranathi","Y.Sri lakshmi","Y.Lakshmi Deepthi","K.Mahalakshmi","Sk.Shakeela","K.Manoj"]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student', methods=['GET', 'POST'])
def student():
    if request.method == 'POST':
        name = request.form.get('name')
        session_type = request.form.get('session')
        work = request.form.get('work')
        date = format_date()
        submitted_time = format_time()

        if not name or not session_type or not work:
            flash('All fields are required', 'danger')
            return redirect(url_for('student'))

        if session_type == 'morning':
            attendance = MorningAttendance(date=date, name=name, work_started_on=work, morning_submitted_time=submitted_time)
        else:
            attendance = EveningAttendance(date=date, name=name, work_done_on=work, evening_submitted_time=submitted_time)

        db.session.add(attendance)
        db.session.commit()

        flash('Attendance submitted successfully!', 'success')
        return redirect(url_for('student'))

    return render_template('student.html', student_names=STUDENT_NAMES)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Variables for form inputs
    student_names = STUDENT_NAMES
    all_attendance = None
    statistics = []
    attended_days = 0
    absent_days = 0

    # Variables for specific functionality
    all_view_date = request.form.get('all_view_date')
    all_view_session = request.form.get('all_view_session')

    specific_student = request.form.get('specific_student')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    specific_action = request.form.get('specific_action')

    # View attendance for all students
    if request.method == 'POST' and all_view_date and all_view_session:
        if all_view_session == 'morning':
            all_attendance = MorningAttendance.query.filter_by(date=all_view_date).all()
        else:
            all_attendance = EveningAttendance.query.filter_by(date=all_view_date).all()

    # View attendance or statistics for a specific student
    if request.method == 'POST' and specific_student and start_date and end_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

        morning_records = MorningAttendance.query.filter(
            MorningAttendance.name == specific_student,
            MorningAttendance.date >= start_date,
            MorningAttendance.date <= end_date
        ).all()
        evening_records = EveningAttendance.query.filter(
            EveningAttendance.name == specific_student,
            EveningAttendance.date >= start_date,
            EveningAttendance.date <= end_date
        ).all()

        if specific_action == 'view_statistics':
            all_dates = set(record.date for record in morning_records + evening_records)
            for date in sorted(all_dates):
                morning = next((record for record in morning_records if record.date == date), None)
                evening = next((record for record in evening_records if record.date == date), None)
                statistics.append({
                    "date": date,
                    "work_started_on": morning.work_started_on if morning else '',
                    "morning_submitted_time": morning.morning_submitted_time if morning else '',
                    "work_done_on": evening.work_done_on if evening else '',
                    "evening_submitted_time": evening.evening_submitted_time if evening else ''
                })

        elif specific_action == 'view_attendance':
            total_days = (end_date_obj - start_date_obj).days + 1
            attended_days = len(set(record.date for record in morning_records + evening_records))
            absent_days = total_days - attended_days

    return render_template(
        'admin.html',
        student_names=student_names,
        all_attendance=all_attendance,
        all_view_date=all_view_date,
        all_view_session=all_view_session,
        specific_student=specific_student,
        start_date=start_date,
        end_date=end_date,
        statistics=statistics,
        attended_days=attended_days,
        absent_days=absent_days
    )

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
    flash("Logged out successfully!", "info")
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
