from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
app.secret_key = "secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    work = db.Column(db.String(200), nullable=False)
    session = db.Column(db.String(10), nullable=False)
    submitted_time = db.Column(db.String(10), nullable=False)

def format_time():
    return datetime.now().strftime("%H:%M")

def format_date():
    return datetime.now().strftime("%y-%m-%d")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student', methods=['GET', 'POST'])
def student():
    if request.method == 'POST':
        session_type = request.form.get('session')
        date = request.form.get('date') or format_date()
        name = request.form.get('name')
        work = request.form.get('work')
        submitted_time = format_time()

        if not date or not name or not work or not session_type:
            flash('All fields are required', 'danger')
            return redirect(url_for('student'))

        attendance = Attendance(date=date, name=name, work=work, session=session_type, submitted_time=submitted_time)
        db.session.add(attendance)
        db.session.commit()

        flash('Details submitted successfully!', 'success')
        return redirect(url_for('student'))

    return render_template('student.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        date = request.form.get('date')
        session_type = request.form.get('session')

        if not date or not session_type:
            flash('Date and session are required', 'danger')
            return redirect(url_for('admin'))

        attendance = Attendance.query.filter_by(date=date, session=session_type).all()
        return render_template('admin.html', attendance=attendance, date=date, session=session_type)

    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('index'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
