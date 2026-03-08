from flask import Flask, render_template, request, redirect, session
import os
import sqlite3

app = Flask(__name__)
app.secret_key = "studenttracker_secret"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ================= DATABASE SETUP ================= #

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        filename TEXT
    )
    """)

    # Default teacher
    cursor.execute("SELECT * FROM teachers")
    if not cursor.fetchall():
        cursor.execute(
            "INSERT INTO teachers(username,password) VALUES(?,?)",
            ("admin", "1234")
        )

    conn.commit()
    conn.close()


init_db()


# ================= TEACHER LOGIN ================= #

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM teachers WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["teacher"] = username
            return redirect("/dashboard")

        return "Invalid Login"

    return render_template("login.html")


# ================= TEACHER DASHBOARD ================= #

@app.route("/dashboard")
def dashboard():
    if "teacher" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()

    subject_files = {}

    for subject in subjects:
        cursor.execute(
            "SELECT * FROM files WHERE subject_id=?",
            (subject[0],)
        )
        subject_files[subject[0]] = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        subjects=subjects,
        subject_files=subject_files
    )


# ================= ADD SUBJECT ================= #

@app.route("/add_subject", methods=["POST"])
def add_subject():
    if "teacher" not in session:
        return redirect("/")

    subject = request.form["subject"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subjects(name) VALUES(?)", (subject,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ================= UPLOAD MULTIPLE FILES ================= #

@app.route("/upload/<int:subject_id>", methods=["POST"])
def upload_files(subject_id):
    if "teacher" not in session:
        return redirect("/")

    files = request.files.getlist("files")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    for file in files:
        if file and file.filename != "":
            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                file.filename
            )
            file.save(filepath)

            cursor.execute(
                "INSERT INTO files(subject_id, filename) VALUES(?,?)",
                (subject_id, file.filename)
            )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ================= DELETE SUBJECT ================= #

@app.route("/delete_subject/<int:subject_id>")
def delete_subject(subject_id):
    if "teacher" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT filename FROM files WHERE subject_id=?",
        (subject_id,)
    )
    files = cursor.fetchall()

    # Delete files from folder
    for file in files:
        path = os.path.join(app.config["UPLOAD_FOLDER"], file[0])
        if os.path.exists(path):
            os.remove(path)

    cursor.execute(
        "DELETE FROM files WHERE subject_id=?",
        (subject_id,)
    )

    cursor.execute(
        "DELETE FROM subjects WHERE id=?",
        (subject_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ================= DELETE FILE ================= #

@app.route("/delete_file/<int:file_id>")
def delete_file(file_id):
    if "teacher" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT filename FROM files WHERE id=?",
        (file_id,)
    )
    file = cursor.fetchone()

    if file:
        path = os.path.join(app.config["UPLOAD_FOLDER"], file[0])
        if os.path.exists(path):
            os.remove(path)

        cursor.execute(
            "DELETE FROM files WHERE id=?",
            (file_id,)
        )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ================= STUDENT DIRECT ACCESS ================= #

@app.route("/student")
def student():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()

    subject_files = {}

    for subject in subjects:
        cursor.execute(
            "SELECT * FROM files WHERE subject_id=?",
            (subject[0],)
        )
        subject_files[subject[0]] = cursor.fetchall()

    conn.close()

    return render_template(
        "student.html",
        subjects=subjects,
        subject_files=subject_files
    )


# ================= LOGOUT ================= #

@app.route("/logout")
def logout():
    session.pop("teacher", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)