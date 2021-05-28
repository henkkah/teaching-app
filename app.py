from flask import Flask
from flask import redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    
    # Check username and password
    sql = "SELECT password FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user == None: # wrong username
        return render_template("error-username-incorrect.html")
    else:
        password_hash = user[0]
        if check_password_hash(password_hash, password): # correct username and password
            session["username"] = username
            teacher = db.session.execute("SELECT teacher FROM users WHERE username=:username", {"username":username}).fetchone()[0]
            if teacher == "1": # teacher
                return redirect("/teacher")
            else: # student
                return redirect("/student")
        else: # wrong password
            return render_template("error-password-incorrect.html")

@app.route("/newuser")
def newuser():
    return render_template("newuser.html")

@app.route("/createuser", methods=["POST"])
def createuser():
    username = request.form["username"]
    password = request.form["password"]
    if "teacher" not in request.form:
        return render_template("error-role-not-chosen.html")
    else:
        teacher = request.form["teacher"]
    
    # Check username
    sql = "SELECT username FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user != None or username.strip() == "": # username in use or empty
        return render_template("error-username-in-use.html")
    
    # Check password
    if password.strip() == "":
        return render_template("error-password-empty.html")
    
    password_hash = generate_password_hash(password)
    sql = "INSERT INTO users (username, password, teacher) VALUES (:username, :password, :teacher)"
    db.session.execute(sql, {"username":username, "password":password_hash, "teacher":teacher})
    db.session.commit()
    
    session["username"] = username
    if teacher == "1": # teacher
        return redirect("/teacher")
    else: # student
        return redirect("/student")


@app.route("/teacher")
def teacher():
    return render_template("teacher.html")

@app.route("/student")
def student():
    return render_template("student.html")

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")


@app.route("/newcourse")
def newcourse():
    return render_template("newcourse.html")

@app.route("/createcourse", methods=["POST"])
def createcourse():
    coursename = request.form["coursename"]
    coursecode = request.form["coursecode"]
    if "language" not in request.form:
        return render_template("error-language-not-chosen.html")
    else:
        language = request.form["language"]
    if "level" not in request.form:
        return render_template("error-level-not-chosen.html")
    else:
        level = request.form["level"]
    ects = request.form["ects"]
    limit = request.form["limit"]
    
    # Check coursename
    if coursename.strip() == "":
        return render_template("error-coursename-not-given.html")
    # Check coursecode
    sql = "SELECT code FROM courses WHERE code=:coursecode"
    result = db.session.execute(sql, {"coursecode":coursecode})
    code = result.fetchone()
    if code != None or coursecode.strip() == "": # coursecode in use or empty
        return render_template("error-coursecode-in-use.html")
    # Check ects
    try:
        ects = int(ects)
        if ects < 0:
            return render_template("error-ects-invalid.html")
    except:
        return render_template("error-ects-invalid.html")
    # Check limit
    try:
        limit = int(limit)
        if limit < 0 or limit > 100:
            return render_template("error-limit-invalid.html")
    except:
        return render_template("error-limit-invalid.html")

    # Add new course to db
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "INSERT INTO courses (code, name, teacher_id, lang, lev, ects, lim, visible, deleted) VALUES (:coursecode, :coursename, :teacher_id, :language, :level, :ects, :limit, :visible, :deleted)"
    db.session.execute(sql, {"coursecode":coursecode, "coursename":coursename, "teacher_id":teacher_id, "language":language, "level":level, "ects":ects, "limit":limit, "visible":"0", "deleted":"0"})
    db.session.commit()
    
    return redirect("/teacher")




