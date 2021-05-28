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
        return render_template("error-login.html", message="Incorrect username")
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
            return render_template("error-login.html", message="Incorrect password")
@app.route("/newuser")
def newuser():
    return render_template("newuser.html")

@app.route("/createuser", methods=["POST"])
def createuser():
    username = request.form["username"]
    password = request.form["password"]
    if "teacher" not in request.form:
        return render_template("error-createuser.html", message="Role not chosen")
    else:
        teacher = request.form["teacher"]
    
    # Check username
    sql = "SELECT username FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user != None or username.strip() == "": # username in use or empty
        return render_template("error-createuser.html", message="Username already in use")
    
    # Check password
    if password.strip() == "":
        return render_template("error-createuser.html", message="Password empty")
    
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
    result2 = db.session.execute(sql2, {"teacher_id":teacher_id, "visible":"0", "deleted":"0"})
    
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
    student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    visible_courses = "(SELECT id, code, name, lang, lev, ects, lim FROM courses WHERE visible=:visible AND deleted=:cdeleted)"
    
    sql1 = "SELECT c.id, c.code, c.name, c.lang, c.lev, c.ects, c.lim FROM " + visible_courses + " as c, courses_students as cs WHERE c.id = cs.course_id AND cs.student_id=:student_id AND cs.completed=:completed AND cs.deleted=:sdeleted"
    result1 = db.session.execute(sql1, {"visible":"1", "cdeleted":"0", "student_id":student_id, "completed":"0", "sdeleted":"0"})
    sql2 = "SELECT c.id, c.code, c.name, c.lang, c.lev, c.ects, c.lim FROM " + visible_courses + " as c, courses_students as cs WHERE c.id = cs.course_id AND cs.student_id=:student_id AND cs.completed=:completed AND cs.deleted=:sdeleted"
    result2 = db.session.execute(sql2, {"visible":"1", "cdeleted":"0", "student_id":student_id, "completed":"1", "sdeleted":"0"})
    
    ongoingcourses_str = []
    for result in result1:
        string = result[1] + " " + result[2] + " (" + language_mapping[result[3]] + ", " + level_mapping[result[4]] + ", " + str(result[5]) + " ECTS, " + str(result[6]) + " % to completion)"
        ongoingcourses_str.append((string, result[0]))
    completedcourses_str = []
    for result in result2:
        string = result[1] + " " + result[2] + " (" + language_mapping[result[3]] + ", " + level_mapping[result[4]] + ", " + str(result[5]) + " ECTS, " + str(result[6]) + " % to completion)"
        completedcourses_str.append((string, result[0]))
    ongoingcourses_str.sort()
    completedcourses_str.sort()
    
    return render_template("student.html", ongoingcourses=ongoingcourses_str, completedcourses=completedcourses_str)

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
        return render_template("error-createcourse.html", message="Language not chosen")
    else:
        language = request.form["language"]
    if "level" not in request.form:
        return render_template("error-createcourse.html", message="Level not chosen")
    else:
        level = request.form["level"]
    ects = request.form["ects"]
    limit = request.form["limit"]
    
    # Check coursename
    if coursename.strip() == "":
        return render_template("error-createcourse.html", message="Course name not given")
    # Check coursecode
    sql = "SELECT code FROM courses WHERE code=:coursecode"
    result = db.session.execute(sql, {"coursecode":coursecode})
    code = result.fetchone()
    if code != None or coursecode.strip() == "": # coursecode in use or empty
        return render_template("error-createcourse.html", message="Course code already in use")
    # Check ects
    try:
        ects = int(ects)
        if ects < 0:
            return render_template("error-createcourse.html", message="Amount of ECTS entered incorrectly (enter integer, >=0)")
    except:
        return render_template("error-createcourse.html", message="Amount of ECTS entered incorrectly (enter integer, >=0)")
    # Check limit
    try:
        limit = int(limit)
        if limit < 0 or limit > 100:
            return render_template("error-createcourse.html", message="Completion limit in % entered incorrectly (enter integer, >=0 and <=100)")
    except:
        return render_template("error-createcourse.html", message="Completion limit in % entered incorrectly (enter integer, >=0 and <=100)")

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
        ENG, FIN, SWE = ("", "", "checked")
    elif result[2] == "FIN":
        ENG, FIN, SWE = ("", "checked", "")
    else:
        ENG, FIN, SWE = ("checked", "", "")
    
    if result[3] == "ADV":
        BEG, INT, ADV = ("", "", "checked")
    elif result[3] == "INT":
        BEG, INT, ADV = ("", "checked", "")
    else:
        BEG, INT, ADV = ("checked", "", "")
    
    return render_template("changecourse.html", id=id, coursename=result[1], coursecode=result[0], ENG=ENG, FIN=FIN, SWE=SWE, BEG=BEG, INT=INT, ADV=ADV, ects=result[4], limit=result[5])

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
        return render_template("error-modifycourse.html", message="Course name not given", id=id)
    # Check coursecode
    old_code = db.session.execute("SELECT code FROM courses WHERE id=:id", {"id":id}).fetchone()[0]
    sql = "SELECT code FROM courses WHERE code=:coursecode"
    result = db.session.execute(sql, {"coursecode":coursecode})
    code = result.fetchone()
    if (code != None and code[0] != old_code) or coursecode.strip() == "": # coursecode in use or empty
        return render_template("error-modifycourse.html", message="Course code already in use", id=id)
    # Check ects
    try:
        ects = int(ects)
        if ects < 0:
            return render_template("error-modifycourse.html", message="Amount of ECTS entered incorrectly (enter integer, >=0)", id=id)
    except:
        return render_template("error-modifycourse.html", message="Amount of ECTS entered incorrectly (enter integer, >=0)", id=id)
    # Check limit
    try:
        limit = int(limit)
        if limit < 0 or limit > 100:
            return render_template("error-modifycourse.html", message="Completion limit in % entered incorrectly (enter integer, >=0 and <=100)", id=id)
    except:
        return render_template("error-modifycourse.html", message="Completion limit in % entered incorrectly (enter integer, >=0 and <=100)", id=id)

    # Modify course in db
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET code=:coursecode, name=:coursename, lang=:language, lev=:level, ects=:ects, lim=:limit WHERE teacher_id = :teacher_id and id = :id"
    db.session.execute(sql, {"coursecode":coursecode, "coursename":coursename, "language":language, "level":level, "ects":ects, "limit":limit, "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/publishcourse/<int:id>")
def publishcourse(id):
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET visible=:visible WHERE teacher_id = :teacher_id and id = :id"
    db.session.execute(sql, {"visible":"1", "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")

@app.route("/hidecourse/<int:id>")
def hidecourse(id):
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET visible=:visible WHERE teacher_id = :teacher_id and id = :id"
    db.session.execute(sql, {"visible":"0", "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/removecourse/<int:id>")
def removecourse(id):
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "SELECT code, name, lang, lev, ects, lim FROM courses WHERE teacher_id=:teacher_id AND id=:id"
    result = db.session.execute(sql, {"teacher_id":teacher_id, "id":id}).fetchone()
    string = result[0] + " " + result[1] + " (" + language_mapping[result[2]] + ", " + level_mapping[result[3]] + ", " + str(result[4]) + " ECTS, " + str(result[5]) + " % to completion)"
    return render_template("removecourse.html", id=id, course_description=string)
    
@app.route("/deletecourse/<int:id>", methods=["POST"])
def deletecourse(id):
    deletion = request.form["deletion"]
    if deletion == "yes":
        teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
        sql = "UPDATE courses SET deleted=:deleted WHERE teacher_id = :teacher_id and id = :id"
        db.session.execute(sql, {"deleted":"1", "teacher_id":teacher_id, "id":id})
        db.session.commit()
    return redirect("/teacher")


@app.route("/courses")
def courses():
    student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    visible_courses = "(SELECT id, code, name, lang, lev, ects, lim FROM courses WHERE visible=:visible AND deleted=:cdeleted)"
    enrolled_courses = "(SELECT course_id FROM courses_students WHERE student_id=:student_id)"
    
    sql1 = "SELECT vc.id, vc.code, vc.name, vc.lang, vc.lev, vc.ects, vc.lim FROM " + visible_courses + " as vc WHERE vc.id NOT IN " + enrolled_courses
    sql2 = "(SELECT c.id, c.code, c.name, c.lang, c.lev, c.ects, c.lim FROM " + visible_courses + " as c, courses_students as cs WHERE c.id = cs.course_id AND cs.student_id=:student_id AND cs.deleted=:sdeleted)"
    sql3 = sql1 + " UNION " + sql2
    result1 = db.session.execute(sql3, {"visible":"1", "cdeleted":"0", "student_id":student_id, "sdeleted":"1"})
    sql4 = "SELECT c.id, c.code, c.name, c.lang, c.lev, c.ects, c.lim FROM " + visible_courses + " as c, courses_students as cs WHERE c.id = cs.course_id AND cs.student_id=:student_id AND cs.deleted=:sdeleted"
    result2 = db.session.execute(sql4, {"visible":"1", "cdeleted":"0", "student_id":student_id, "sdeleted":"0"})
    
    newcourses_str = []
    for result in result1:
        string = result[1] + " " + result[2] + " (" + language_mapping[result[3]] + ", " + level_mapping[result[4]] + ", " + str(result[5]) + " ECTS, " + str(result[6]) + " % to completion)"
        newcourses_str.append((string, result[0]))
    enrolledcourses_str = []
    for result in result2:
        string = result[1] + " " + result[2] + " (" + language_mapping[result[3]] + ", " + level_mapping[result[4]] + ", " + str(result[5]) + " ECTS, " + str(result[6]) + " % to completion)"
        enrolledcourses_str.append((string, result[0]))
    newcourses_str.sort()
    enrolledcourses_str.sort()
    
    return render_template("courses.html", newcourses=newcourses_str, enrolledcourses=enrolledcourses_str)


@app.route("/joincourse/<int:id>")
def joincourse(id):
    student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    left_course = db.session.execute("SELECT * FROM courses_students WHERE course_id=:id AND student_id=:student_id", {"id":id, "student_id":student_id}).fetchone()
    if left_course != None:
        sql = "UPDATE courses_students SET deleted=:deleted WHERE course_id = :course_id and student_id = :student_id"
        db.session.execute(sql, {"deleted":"0", "course_id":id, "student_id":student_id})
    else:
        sql = "INSERT INTO courses_students (course_id, student_id, completed, deleted) VALUES (:course_id, :student_id, :completed, :deleted)"
        db.session.execute(sql, {"course_id":id, "student_id":student_id, "completed":"0", "deleted":"0"})
    db.session.commit()
    
    return redirect("/student")


@app.route("/quitcourse/<int:id>")
def quitcourse(id):
    student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "SELECT c.code, c.name, c.lang, c.lev, c.ects, c.lim FROM courses as c, courses_students as cs WHERE c.id = cs.course_id AND cs.student_id=:student_id AND c.id=:id"
    result = db.session.execute(sql, {"student_id":student_id, "id":id}).fetchone()
    string = result[0] + " " + result[1] + " (" + language_mapping[result[2]] + ", " + level_mapping[result[3]] + ", " + str(result[4]) + " ECTS, " + str(result[5]) + " % to completion)"
    return render_template("quitcourse.html", id=id, course_description=string)
    
@app.route("/leavecourse/<int:id>", methods=["POST"])
def leavecourse(id):
    leaving = request.form["leaving"]
    if leaving == "yes":
        student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
        sql = "UPDATE courses_students SET deleted=:deleted WHERE student_id = :student_id and course_id = :course_id"
        db.session.execute(sql, {"deleted":"1", "student_id":student_id, "course_id":id})
        db.session.commit()
    return redirect("/student")




