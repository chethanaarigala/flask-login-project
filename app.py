from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import re

app = Flask(__name__)
app.secret_key = 'mysecretkey'

# DATABASE PATH
DB_PATH = 'users.db'
if os.environ.get('RENDER'):
    DB_PATH = '/tmp/users.db'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# database
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mobile TEXT UNIQUE,
        password TEXT,
        profile_pic TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        image TEXT,
        caption TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS comments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_mobile TEXT,
        comment TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS likes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        user_mobile TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS follows(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        follower TEXT,
        following TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        message TEXT
    )''')

    conn.commit()
    conn.close()

init_db()


# register
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""

    if request.method == 'POST':
        mobile = request.form['mobile'].strip()
        password = request.form['password'].strip()

        if not re.fullmatch(r'[6-9][0-9]{9}', mobile):
            return render_template('register.html', message="Invalid mobile ❌")

        if len(password) < 4:
            return render_template('register.html', message="Password too short ❌")

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users VALUES (NULL,?,?,?)",
                (mobile, generate_password_hash(password), 'default.png')
            )

            conn.commit()
            conn.close()

            message = "Registered ✅"
        except:
            message = "User already exists ❌"

    return render_template('register.html', message=message)


# login
@app.route('/', methods=['GET', 'POST'])
def login():
    message = ""

    if request.method == 'POST':
        mobile = request.form['mobile']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE mobile=?", (mobile,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user'] = mobile
            return redirect('/home')
        else:
            message = "Invalid login ❌"

    return render_template('login.html', message=message)


# home
@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE mobile=?", (session['user'],))
    user = cur.fetchone()
    conn.close()

    return render_template('home.html', user=user['mobile'], profile_pic=user['profile_pic'])


#proflie
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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            cur.execute("UPDATE users SET profile_pic=? WHERE mobile=?",
                        (filename, session['user']))
            conn.commit()

    cur.execute("SELECT * FROM users WHERE mobile=?", (session['user'],))
    user = cur.fetchone()
    conn.close()

    return render_template('profile.html', user=user)


# explore
@app.route('/explore')
def explore():
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()

    post_data = []

    for p in posts:
        cur.execute("SELECT * FROM comments WHERE post_id=?", (p['id'],))
        comments = cur.fetchall()

        cur.execute("SELECT COUNT(*) as count FROM likes WHERE post_id=?", (p['id'],))
        likes = cur.fetchone()['count']

        post_data.append({
            "post": p,
            "comments": comments,
            "likes": likes
        })

    conn.close()

    return render_template('explore.html', posts=post_data)


#upload post
@app.route('/upload_post', methods=['POST'])
def upload_post():
    if 'user' not in session:
        return redirect('/')

    file = request.files.get('image')
    caption = request.form.get('caption')

    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("INSERT INTO posts VALUES (NULL,?,?,?)",
                    (session['user'], filename, caption))

        conn.commit()
        conn.close()

    return redirect('/explore')


# comment
@app.route('/comment', methods=['POST'])
def comment():
    if 'user' not in session:
        return redirect('/')

    post_id = request.form['post_id']
    comment = request.form['comment']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO comments VALUES (NULL,?,?,?)",
                (post_id, session['user'], comment))

    cur.execute("SELECT user_mobile FROM posts WHERE id=?", (post_id,))
    owner = cur.fetchone()['user_mobile']

    if owner != session['user']:
        cur.execute("INSERT INTO notifications VALUES (NULL,?,?)",
                    (owner, f"{session['user']} commented on your post"))

    conn.commit()
    conn.close()

    return redirect('/explore')


# like
@app.route('/like/<int:post_id>')
def like(post_id):
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM likes WHERE post_id=? AND user_mobile=?",
                (post_id, session['user']))
    exists = cur.fetchone()

    if exists:
        cur.execute("DELETE FROM likes WHERE post_id=? AND user_mobile=?",
                    (post_id, session['user']))
    else:
        cur.execute("INSERT INTO likes VALUES (NULL,?,?)",
                    (post_id, session['user']))

    conn.commit()
    conn.close()

    return redirect('/explore')


# follow
@app.route('/follow/<user>')
def follow(user):
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO follows VALUES (NULL,?,?)",
                (session['user'], user))

    conn.commit()
    conn.close()

    return redirect('/explore')


# notifications
@app.route('/notifications')
def notifications():
    if 'user' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM notifications WHERE user_mobile=?",
                (session['user'],))
    data = cur.fetchall()

    conn.close()

    return render_template('notifications.html', data=data)


# logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# Run
if __name__ == '__main__':
    app.run(debug=True)