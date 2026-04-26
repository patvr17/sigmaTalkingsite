import bcrypt
from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "dev-secret-key"  # needed for login sessions


def init_db():
    conn = sqlite3.connect("posts.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            username TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/like/<int:post_id>")
def like(post_id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("posts.db")
    c = conn.cursor()

    # prevent duplicate likes
    c.execute("SELECT * FROM likes WHERE post_id=? AND username=?",
              (post_id, session["user"]))
    existing = c.fetchone()

    if not existing:
        c.execute("INSERT INTO likes (post_id, username) VALUES (?, ?)",
                  (post_id, session["user"]))

    conn.commit()
    conn.close()

    return redirect("/")
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("posts.db")
    c = conn.cursor()

    c.execute("SELECT id, username, message, timestamp FROM posts ORDER BY id DESC")
    posts = c.fetchall()

    # attach like counts
    post_data = []
    for p in posts:
        c.execute("SELECT COUNT(*) FROM likes WHERE post_id=?", (p[0],))
        likes = c.fetchone()[0]

        post_data.append((p[0], p[1], p[2], p[3], likes))

    conn.close()

    return render_template("index.html", posts=post_data, user=session["user"])


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = sqlite3.connect("posts.db")
        c = conn.cursor()

        try:
            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_pw)
            )
            conn.commit()
        except:
            pass

        conn.close()
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("posts.db")
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[0]):
            session["user"] = username
            return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/submit", methods=["POST"])
def submit():
    if "user" not in session:
        return redirect("/login")

    message = request.form["message"]
    user = session["user"]
    time = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect("posts.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO posts (username, message, timestamp) VALUES (?, ?, ?)",
        (user, message, time)
    )
    conn.commit()
    conn.close()

    return redirect("/")
@app.route("/delete/<int:post_id>")
def delete(post_id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("posts.db")
    c = conn.cursor()

    # Only delete your own posts
    c.execute(
        "DELETE FROM posts WHERE id=? AND username=?",
        (post_id, session["user"])
    )

    conn.commit()
    conn.close()

    return redirect("/")
@app.route("/user/<username>")
def profile(username):
    conn = sqlite3.connect("posts.db")
    c = conn.cursor()

    c.execute("""
        SELECT id, username, message, timestamp
        FROM posts
        WHERE username=?
        ORDER BY id DESC
    """, (username,))

    posts = c.fetchall()
    conn.close()

    return render_template("profile.html", posts=posts, username=username)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)