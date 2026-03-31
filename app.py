from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)  

app.secret_key = 'mysecretkey'   

def init_db():
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO users (mobile, password) VALUES (?, ?)", (mobile, password))
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    message = ""

    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = sqlite3.connect('/tmp/users.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE mobile=? AND password=?", (mobile, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session['user'] = mobile
            return redirect('/dashboard')
        else:
            message = "Invalid Details"

    return render_template('login.html', message=message)

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    else:
        return redirect('/')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')



if __name__ == '__main__':
    app.run(debug=True)