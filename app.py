from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = 'mysecretkey'   

# DATABASE PATH (works local + Render)
DB_PATH = 'users.db'
if os.environ.get('RENDER'):
    DB_PATH = '/tmp/users.db'


# DATABASE FUNCTION
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
            password TEXT
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

        # STRONG number VALIDATION
        if not re.fullmatch(r'[6-9][0-9]{9}', mobile):
            message = "Enter valid 10-digit Indian mobile number ❌"
            return render_template('register.html', message=message)

        if len(password) < 4:
            message = "Password must be at least 4 characters ❌"
            return render_template('register.html', message=message)

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (mobile, password) VALUES (?, ?)", 
                        (mobile, hashed_password))
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

        # VALIDATION
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
    if 'user' in session:
        return render_template('home.html', user=session['user'])
    return redirect('/')


# EXTRA PAGES 
@app.route('/explore')
def explore():
    if 'user' in session:
        return "<h2>Explore Page 🚀 (You can design UI)</h2>"
    return redirect('/')


@app.route('/profile')
def profile():
    if 'user' in session:
        return f"<h2>Profile Page 👤<br>User: {session['user']}</h2>"
    return redirect('/')


@app.route('/settings')
def settings():
    if 'user' in session:
        return "<h2>Settings Page ⚙️</h2>"
    return redirect('/')



# LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


# RUN APP

if __name__ == '__main__':
    app.run(debug=True)