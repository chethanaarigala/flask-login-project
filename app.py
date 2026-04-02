from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'mysecretkey'

# ✅ DATABASE PATH (works local + Render)
DB_PATH = 'users.db'
if os.environ.get('RENDER'):
    DB_PATH = '/tmp/users.db'

# ✅ CREATE DATABASE
def init_db():
    conn = sqlite3.connect(DB_PATH)
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

# ✅ REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""

    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        # 🔒 VALIDATION
        if len(mobile) != 10 or not mobile.isdigit():
            message = "Invalid Mobile Number ❌"
            return render_template('register.html', message=message)

        if len(password) < 4:
            message = "Password must be at least 4 characters ❌"
            return render_template('register.html', message=message)

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (mobile, password) VALUES (?, ?)", (mobile, hashed_password))
            conn.commit()
            conn.close()

            message = "Registration Successful ✅"

        except sqlite3.IntegrityError:
            message = "Mobile already registered ❌"

    return render_template('register.html', message=message)


# ✅ LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    message = ""

    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user'] = mobile
            return redirect('/home')   # ✅ Redirect to HOME
        else:
            message = "Invalid Details ❌"

    return render_template('login.html', message=message)


# ✅ HOME PAGE (NEW)
@app.route('/home')
def home():
    if 'user' in session:
        return render_template('home.html', user=session['user'])
    else:
        return redirect('/')


# ✅ LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


# ✅ RUN APP
if __name__ == '__main__':
    app.run(debug=True)