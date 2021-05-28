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

language_mapping = {"ENG":"English", "FIN":"Finnish", "SWE":"Swedish"}
level_mapping = {"BEG":"Beginner", "INT":"Intermediate", "ADV":"Advanced"}


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
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql1 = "SELECT id, code, name, lang, lev, ects, lim FROM courses WHERE teacher_id=:teacher_id AND visible=:visible AND deleted=:deleted"
    result1 = db.session.execute(sql1, {"teacher_id":teacher_id, "visible":"1", "deleted":"0"})
    sql2 = "SELECT id, code, name, lang, lev, ects, lim FROM courses WHERE teacher_id=:teacher_id AND visible=:visible AND deleted=:deleted"
    result2 = db.session.execute(sql1, {"teacher_id":teacher_id, "visible":"0", "deleted":"0"})
    
    visiblecourses_str = []
    for result in result1:
        string = result[1] + " " + result[2] + " (" + language_mapping[result[3]] + ", " + level_mapping[result[4]] + ", " + str(result[5]) + " ECTS, " + str(result[6]) + " % to completion)"
        visiblecourses_str.append((string, result[0]))
    hiddencourses_str = []
    for result in result2:
        string = result[1] + " " + result[2] + " (" + language_mapping[result[3]] + ", " + level_mapping[result[4]] + ", " + str(result[5]) + " ECTS, " + str(result[6]) + " % to completion)"
        hiddencourses_str.append((string, result[0]))
    visiblecourses_str.sort()
    hiddencourses_str.sort()
    
    return render_template("teacher.html", visiblecourses=visiblecourses_str, hiddencourses=hiddencourses_str)

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


@app.route("/changecourse/<int:id>")
def changecourse(id):
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "SELECT code, name, lang, lev, ects, lim FROM courses WHERE teacher_id=:teacher_id AND id=:id"
    result = db.session.execute(sql, {"teacher_id":teacher_id, "id":id}).fetchone()
    
    
    if result[2] == "SWE":
        if result[3] == "ADV":
            return render_template("changecourse-i.html", id=id, coursename=result[1], coursecode=result[0], ects=result[4], limit=result[5])
        elif result[3] == "INT":
            return render_template("changecourse-h.html", id=id, coursename=result[1], coursecode=result[0], ects=result[4], limit=result[5])
        else:
            return render_template("changecourse-g.html", id=id, coursename=result[1], coursecode=result[0], ects=result[4], limit=result[5])
    elif result[2] == "FIN":
        if result[3] == "ADV":
            return render_template("changecourse-f.html", id=id, coursename=result[1], coursecode=result[0], ects=result[4], limit=result[5])
        elif result[3] == "INT":
            return render_template("changecourse-e.html", id=id, coursename=result[1], coursecode=result[0], ects=result[4], limit=result[5])
        else:
            return render_template("changecourse-d.html", id=id, coursename=result[1], coursecode=result[0], ects=result[4], limit=result[5])
    else:
        if result[3] == "ADV":
            return render_template("changecourse-c.html", id=id, coursename=result[1], coursecode=result[0], ects=result[4], limit=result[5])
        elif result[3] == "INT":
            return render_template("changecourse-b.html", id=id, coursename=result[1], coursecode=result[0], ects=result[4], limit=result[5])
        else:
            return render_template("changecourse-a.html", id=id, coursename=result[1], coursecode=result[0], ects=result[4], limit=result[5])

@app.route("/modifycourse/<int:id>", methods=["POST"])
def modifycourse(id):
    coursename = request.form["coursename"]
    coursecode = request.form["coursecode"]
    language = request.form["language"]
    level = request.form["level"]
    ects = request.form["ects"]
    limit = request.form["limit"]
    
    # Check coursename
    if coursename.strip() == "":
        return render_template("error-mod-coursename-not-given.html", id=id)
    # Check coursecode
    old_code = db.session.execute("SELECT code FROM courses WHERE id=:id", {"id":id}).fetchone()[0]
    sql = "SELECT code FROM courses WHERE code=:coursecode"
    result = db.session.execute(sql, {"coursecode":coursecode})
    code = result.fetchone()
    if (code != None and code[0] != old_code) or coursecode.strip() == "": # coursecode in use or empty
        return render_template("error-mod-coursecode-in-use.html", id=id)
    # Check ects
    try:
        ects = int(ects)
        if ects < 0:
            return render_template("error-mod-ects-invalid.html", id=id)
    except:
        return render_template("error-mod-ects-invalid.html", id=id)
    # Check limit
    try:
        limit = int(limit)
        if limit < 0 or limit > 100:
            return render_template("error-mod-limit-invalid.html", id=id)
    except:
        return render_template("error-mod-limit-invalid.html", id=id)

    # Modify course in db
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET code=:coursecode, name=:coursename, lang=:language, lev=:level, ects=:ects, lim=:limit WHERE teacher_id = :teacher_id and id = :id"
    db.session.execute(sql, {"coursecode":coursecode, "coursename":coursename, "language":language, "level":level, "ects":ects, "limit":limit, "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")









