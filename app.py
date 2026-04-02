from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = 'mysecretkey'

# DATABASE PATH (works local + Render)
DB_PATH = 'users.db'
if os.environ.get('RENDER'):
    DB_PATH = '/tmp/users.db'

# UPLOAD CONFIG
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# DATABASE CONNECTION
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# CREATE DATABASE
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT UNIQUE,
            password TEXT,
            profile_pic TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""

    if request.method == 'POST':
        mobile = request.form['mobile'].strip()
        password = request.form['password'].strip()

        # VALIDATION
        if not re.fullmatch(r'[6-9][0-9]{9}', mobile):
            message = "Enter valid 10-digit mobile number ❌"
            return render_template('register.html', message=message)

        if len(password) < 4:
            message = "Password must be at least 4 characters ❌"
            return render_template('register.html', message=message)

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            default_pic = 'default.png'

            cur.execute(
                "INSERT INTO users (mobile, password, profile_pic) VALUES (?, ?, ?)",
                (mobile, hashed_password, default_pic)
            )

            conn.commit()
            conn.close()

            message = "Registration Successful ✅"

        except sqlite3.IntegrityError:
            message = "Mobile already registered ❌"

    return render_template('register.html', message=message)


# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    message = ""

    if request.method == 'POST':
        mobile = request.form['mobile'].strip()
        password = request.form['password'].strip()

        if not re.fullmatch(r'[6-9][0-9]{9}', mobile):
            message = "Invalid Mobile Format ❌"
            return render_template('login.html', message=message)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = mobile
            return redirect('/home')
        else:
            message = "Invalid Details ❌"

    return render_template('login.html', message=message)



# HOME (DASHBOARD)
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE mobile=?", (session['user'],))
    user = cur.fetchone()
    conn.close()

    return render_template(
        'home.html',
        user=user['mobile'],
        profile_pic=user['profile_pic']
    )


# PROFILE
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        file = request.files.get('profile_pic')

        if file and file.filename != '':
            filename = secure_filename(file.filename)

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            cur.execute(
                "UPDATE users SET profile_pic=? WHERE mobile=?",
                (filename, session['user'])
            )
            conn.commit()

    cur.execute("SELECT * FROM users WHERE mobile=?", (session['user'],))
    user = cur.fetchone()
    conn.close()

    return render_template('profile.html', user=user)


# EXPLORE (UPGRADED UI PAGE)
@app.route('/explore')
def explore():
    if 'user' not in session:
        return redirect('/')

    return render_template('explore.html')


# SETTINGS
@app.route('/settings')
def settings():
    if 'user' not in session:
        return redirect('/')

    return render_template('settings.html')



# LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')



# RUN APP
if __name__ == '__main__':
    app.run(debug=True)