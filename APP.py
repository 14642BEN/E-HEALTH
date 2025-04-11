from flask import Flask, render_template, redirect, url_for, request, flash, session, send_from_directory
import os
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        extra = request.form.get('extra')  # Age for patient / Specialty for doctor

        db = get_db()
        if user_type == 'patient':
            db.execute('INSERT INTO patients (username, password, name, age) VALUES (?, ?, ?, ?)',
                       (username, password, name, extra))
        elif user_type == 'doctor':
            db.execute('INSERT INTO doctors (username, password, name, specialty) VALUES (?, ?, ?, ?)',
                       (username, password, name, extra))
        db.commit()
        flash('Registered successfully!')
        return redirect(url_for('login', user_type=user_type))
    return render_template('register.html', user_type=user_type)

@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()

        user = None
        if user_type == 'patient':
            user = db.execute('SELECT * FROM patients WHERE username=? AND password=?',
                              (username, password)).fetchone()
        elif user_type == 'doctor':
            user = db.execute('SELECT * FROM doctors WHERE username=? AND password=?',
                              (username, password)).fetchone()

        if user:
            session['username'] = username
            session['user_type'] = user_type
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html', user_type=user_type)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    db = get_db()
    if session['user_type'] == 'patient':
        doctors = db.execute('SELECT * FROM doctors').fetchall()
        return render_template('dashboard_patient.html', doctors=doctors)
    else:
        appointments = db.execute('SELECT * FROM appointments WHERE doctor=?',
                                  (session['username'],)).fetchall()
        return render_template('dashboard_doctor.html', appointments=appointments)

@app.route('/book/<doctor_username>', methods=['POST'])
def book(doctor_username):
    if 'username' not in session:
        return redirect(url_for('index'))

    date = request.form['date']
    db = get_db()
    db.execute('INSERT INTO appointments (patient, doctor, date) VALUES (?, ?, ?)',
               (session['username'], doctor_username, date))
    db.commit()
    flash('Appointment booked!')
    return redirect(url_for('dashboard'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            db = get_db()
            db.execute('INSERT INTO uploads (username, filepath) VALUES (?, ?)',
                       (session['username'], filename))
            db.commit()
            flash('File uploaded!')
    return render_template('upload.html')

@app.route('/files')
def files():
    if 'username' not in session:
        return redirect(url_for('index'))
    db = get_db()
    rows = db.execute('SELECT * FROM uploads WHERE username=?', (session['username'],)).fetchall()
    return render_template('files.html', files=rows)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
