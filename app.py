from flask import Flask, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)


roles = ["teacher", "student"]
language_mapping = {"ENG":"English", "FIN":"Finnish", "SWE":"Swedish"}
level_mapping = {"BAS":"Basic", "INT":"Intermediate", "ADV":"Advanced"}


################################################## LOGGING ##################################################

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    
    # Check username and password
    sql = "SELECT password FROM users WHERE username=:username"
    password_in_db = db.session.execute(sql, {"username":username}).fetchone()
    if password_in_db == None: # incorrect username
        return render_template("error-login.html", message="Incorrect username")
    else:
        password_hash = password_in_db[0]
        if check_password_hash(password_hash, password): # correct username and password
            session["username"] = username
            role = db.session.execute("SELECT role FROM users WHERE username=:username", {"username":username}).fetchone()[0]
            if role == "teacher":
                return redirect("/teacher")
            else: # student
                return redirect("/student")
        else: # incorrect password
            return render_template("error-login.html", message="Incorrect password")


@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")


@app.route("/createuser")
def createuser():
    return render_template("createuser.html")


@app.route("/createuser/action", methods=["POST"])
def createuser_action():
    username = request.form["username"]
    password = request.form["password"]
    if "role" not in request.form:
        return render_template("error-createuser.html", message="Role not chosen")
    else:
        role = request.form["role"]
    
    # Check username
    sql = "SELECT username FROM users WHERE username=:username"
    username_in_db = db.session.execute(sql, {"username":username}).fetchone()
    if username_in_db != None or username.strip() == "": # username in use or empty
        return render_template("error-createuser.html", message="Username in use")
    
    # Check password
    if password.strip() == "":
        return render_template("error-createuser.html", message="Password empty")
    
    # Insert new user into db
    password_hash = generate_password_hash(password)
    sql = "INSERT INTO users (username, password, role) VALUES (:username, :password, :role)"
    db.session.execute(sql, {"username":username, "password":password_hash, "role":role})
    db.session.commit()
    
    # Redirect to Teacher or Student -view
    session["username"] = username
    if role == "teacher":
        return redirect("/teacher")
    else: # student
        return redirect("/student")


################################################## TEACHER ##################################################

@app.route("/teacher")
def teacher():
    # Authenticate
    try:
        username = session["username"]
        user_id, role = db.session.execute("SELECT id, role FROM users WHERE username=:username", {"username":username}).fetchone()
        if role != "teacher":
            return redirect("/")
    except: # user not logged in
        return redirect("/")
    
    visible_courses_from_db = db.session.execute("SELECT id, code, name, lang, lev, ects, lim FROM courses WHERE teacher_id=:teacher_id AND visible=:visible", {"teacher_id":user_id, "visible":1}).fetchall()
    hidden_courses_from_db = db.session.execute("SELECT id, code, name, lang, lev, ects, lim FROM courses WHERE teacher_id=:teacher_id AND visible=:visible", {"teacher_id":user_id, "visible":0}).fetchall()
    
    visible_courses = []
    for course in visible_courses_from_db:
        string = course[1] + " " + course[2] + " (" + language_mapping[course[3]] + ", " + level_mapping[course[4]] + ", " + str(course[5]) + " ECTS, " + str(course[6]) + " % to complete)"
        visible_courses.append((string, course[0]))
    hidden_courses = []
    for course in hidden_courses_from_db:
        string = course[1] + " " + course[2] + " (" + language_mapping[course[3]] + ", " + level_mapping[course[4]] + ", " + str(course[5]) + " ECTS, " + str(course[6]) + " % to complete)"
        hidden_courses.append((string, course[0]))
    visible_courses.sort()
    hidden_courses.sort() 
    
    return render_template("teacher.html", visible_courses=visible_courses, hidden_courses=hidden_courses)


@app.route("/teacher/createcourse")
def createcourse():
    return render_template("createcourse.html")


@app.route("/teacher/createcourse/action", methods=["POST"])
def createcourse_action():
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
    
    # Check coursecode
    if coursecode.strip() == "":
        return render_template("error-createcourse.html", message="Course code not given")
    # Check coursename
    if coursename.strip() == "":
        return render_template("error-createcourse.html", message="Course name not given")
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
            return render_template("error-createcourse.html", message="Limit to complete in % entered incorrectly (enter integer, >=0 and <=100)")
    except:
        return render_template("error-createcourse.html", message="Limit to complete in % entered incorrectly (enter integer, >=0 and <=100)")

    # Insert new course into db
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "INSERT INTO courses (code, name, teacher_id, lang, lev, ects, lim, visible) VALUES (:coursecode, :coursename, :teacher_id, :language, :level, :ects, :limit, :visible)"
    db.session.execute(sql, {"coursecode":coursecode, "coursename":coursename, "teacher_id":teacher_id, "language":language, "level":level, "ects":ects, "limit":limit, "visible":0})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/teacher/publishcourse/<int:id>")
def publishcourse(id):
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET visible=:visible WHERE teacher_id=:teacher_id and id=:id"
    db.session.execute(sql, {"visible":1, "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/teacher/hidecourse/<int:id>")
def hidecourse(id):
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET visible=:visible WHERE teacher_id=:teacher_id and id=:id"
    db.session.execute(sql, {"visible":0, "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/teacher/modifycourse/<int:id>")
def modifycourse(id):
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
        BAS, INT, ADV = ("", "", "checked")
    elif result[3] == "INT":
        BAS, INT, ADV = ("", "checked", "")
    else:
        BAS, INT, ADV = ("checked", "", "")
    
    return render_template("modifycourse.html", id=id, coursecode=result[0], coursename=result[1], ENG=ENG, FIN=FIN, SWE=SWE, BAS=BAS, INT=INT, ADV=ADV, ects=result[4], limit=result[5])


@app.route("/teacher/modifycourse/<int:id>/action", methods=["POST"])
def modifycourse_action(id):
    coursename = request.form["coursename"]
    coursecode = request.form["coursecode"]
    language = request.form["language"]
    level = request.form["level"]
    ects = request.form["ects"]
    limit = request.form["limit"]
    
    # Check coursecode
    if coursecode.strip() == "":
        return render_template("error-modifycourse.html", message="Course code not given", id=id)
    # Check coursename
    if coursename.strip() == "":
        return render_template("error-modifycourse.html", message="Course name not given", id=id)
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
            return render_template("error-modifycourse.html", message="Limit to complete in % entered incorrectly (enter integer, >=0 and <=100)", id=id)
    except:
        return render_template("error-modifycourse.html", message="Limit to complete in % entered incorrectly (enter integer, >=0 and <=100)", id=id)

    # Modify course in db
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET code=:coursecode, name=:coursename, lang=:language, lev=:level, ects=:ects, lim=:limit WHERE teacher_id=:teacher_id and id=:id"
    db.session.execute(sql, {"coursecode":coursecode, "coursename":coursename, "language":language, "level":level, "ects":ects, "limit":limit, "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/teacher/deletecourse/<int:id>")
def deletecourse(id):
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "SELECT code, name, lang, lev, ects, lim FROM courses WHERE teacher_id=:teacher_id AND id=:id"
    result = db.session.execute(sql, {"teacher_id":teacher_id, "id":id}).fetchone()
    string = result[0] + " " + result[1] + " (" + language_mapping[result[2]] + ", " + level_mapping[result[3]] + ", " + str(result[4]) + " ECTS, " + str(result[5]) + " % to complete)"
    return render_template("deletecourse.html", id=id, course_description=string)


@app.route("/teacher/deletecourse/<int:id>/action", methods=["POST"])
def deletecourse_action(id):
    deletion = request.form["deletion"]
    if deletion == "yes":
        teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
        sql = "DELETE FROM courses WHERE teacher_id=:teacher_id and id=:id"
        db.session.execute(sql, {"teacher_id":teacher_id, "id":id})
        db.session.commit()
    return redirect("/teacher")


##### Functionality for 2nd release

@app.route("/teacher/course/<int:id>")
def course_teacher(id):
    # Authenticate
    try:
        username = session["username"]
        user_id, role = db.session.execute("SELECT id, role FROM users WHERE username=:username", {"username":username}).fetchone()
        if role != "teacher":
            return redirect("/")
        course_teacher = db.session.execute("SELECT teacher_id FROM courses WHERE id=:id", {"id":id}).fetchone()[0]
        if course_teacher != user_id: # not own course
            return redirect("/")
    except: # user not logged in
        return redirect("/")
    
    # Course parameters
    sql = "SELECT code, name, lang, lev, ects, lim FROM courses WHERE id=:id"
    result = db.session.execute(sql, {"id":id}).fetchone()
    header = result[0] + " " + result[1]
    parameters = "(" + language_mapping[result[2]] + ", " + level_mapping[result[3]] + ", " + str(result[4]) + " ECTS, " + str(result[5]) + " % to complete)"
    
    # Course material
    material_from_db = db.session.execute("SELECT material FROM materials WHERE course_id=:course_id", {"course_id":id}).fetchone()
    if material_from_db == None:
        material = ""
    else:
        material = material_from_db[0]
    
    # Course assignments
    
    
    return render_template("course-teacher.html", id=id, header=header, parameters=parameters, material=material)


@app.route("/teacher/course/<int:id>/modifymaterial")
def modifymaterial(id):
    # Authenticate
    try:
        username = session["username"]
        user_id, role = db.session.execute("SELECT id, role FROM users WHERE username=:username", {"username":username}).fetchone()
        if role != "teacher":
            return redirect("/")
        course_teacher = db.session.execute("SELECT teacher_id FROM courses WHERE id=:id", {"id":id}).fetchone()[0]
        if course_teacher != user_id: # not own course
            return redirect("/")
    except: # user not logged in
        return redirect("/")
    
    # Course parameters
    sql = "SELECT code, name, lang, lev, ects, lim FROM courses WHERE id=:id"
    result = db.session.execute(sql, {"id":id}).fetchone()
    header = result[0] + " " + result[1]
    parameters = "(" + language_mapping[result[2]] + ", " + level_mapping[result[3]] + ", " + str(result[4]) + " ECTS, " + str(result[5]) + " % to complete)"
    
    # Course material
    material_from_db = db.session.execute("SELECT material FROM materials WHERE course_id=:course_id", {"course_id":id}).fetchone()
    if material_from_db == None:
        material = ""
    else:
        material = material_from_db[0]
    
    return render_template("modifymaterial.html", id=id, header=header, parameters=parameters, material=material)


@app.route("/teacher/course/<int:id>/modifymaterial/action", methods=["POST"])
def modifymaterial_action(id):
    # Authenticate
    try:
        username = session["username"]
        user_id, role = db.session.execute("SELECT id, role FROM users WHERE username=:username", {"username":username}).fetchone()
        if role != "teacher":
            return redirect("/")
        course_teacher = db.session.execute("SELECT teacher_id FROM courses WHERE id=:id", {"id":id}).fetchone()[0]
        if course_teacher != user_id: # not own course
            return redirect("/")
    except: # user not logged in
        return redirect("/")

    new_material = request.form["material"]
    print(new_material)
    id_in_db = db.session.execute("SELECT id FROM materials WHERE course_id=:course_id", {"course_id":id}).fetchone()
    if id_in_db == None: # no existing material
        print("ei vielä")
        db.session.execute("INSERT INTO materials (material, course_id) VALUES (:material, :course_id)", {"material":new_material, "course_id":id})
        db.session.commit()
    else:
        print("oli jo")
        id_in_db = id_in_db[0]
        db.session.execute("UPDATE materials SET material=:material WHERE id=:id", {"material":new_material, "id":id_in_db})
        db.session.commit()
    
    return redirect("/teacher/course/" + str(id))


################################################## STUDENT ##################################################

@app.route("/student")
def student():
    # Authenticate
    try:
        username = session["username"]
        user_id, role = db.session.execute("SELECT id, role FROM users WHERE username=:username", {"username":username}).fetchone()
        if role != "student":
            return redirect("/")
    except: # user not logged in
        return redirect("/")
    
    visible_courses = "(SELECT id, code, name, lang, lev, ects, lim, teacher_id FROM courses WHERE visible=:visible)"
    
    sql1 = "SELECT vc.id, vc.code, vc.name, vc.lang, vc.lev, vc.ects, vc.lim, vc.teacher_id FROM " + visible_courses + " as vc, courses_students as cs WHERE vc.id = cs.course_id AND cs.student_id=:user_id AND cs.completed=:completed"
    ongoing_courses_from_db = db.session.execute(sql1, {"visible":1, "user_id":user_id, "completed":0})
    sql2 = "SELECT vc.id, vc.code, vc.name, vc.lang, vc.lev, vc.ects, vc.lim, vc.teacher_id FROM " + visible_courses + " as vc, courses_students as cs WHERE vc.id = cs.course_id AND cs.student_id=:user_id AND cs.completed=:completed"
    completed_courses_from_db = db.session.execute(sql1, {"visible":1, "user_id":user_id, "completed":1})
    
    ongoing_courses = []
    for course in ongoing_courses_from_db:
        teacher_id = course[7]
        teacher = db.session.execute("SELECT username FROM users WHERE id=:id", {"id":teacher_id}).fetchone()[0]
        string = course[1] + " " + course[2] + " (" + language_mapping[course[3]] + ", " + level_mapping[course[4]] + ", " + str(course[5]) + " ECTS, " + str(course[6]) + " % to complete, teacher: " + teacher + ")"
        ongoing_courses.append((string, course[0]))
    completed_courses = []
    for course in completed_courses_from_db:
        teacher_id = course[7]
        teacher = db.session.execute("SELECT username FROM users WHERE id=:id", {"id":teacher_id}).fetchone()[0]
        string = course[1] + " " + course[2] + " (" + language_mapping[course[3]] + ", " + level_mapping[course[4]] + ", " + str(course[5]) + " ECTS, " + str(course[6]) + " % to complete, teacher: " + teacher + ")"
        completed_courses.append((string, course[0]))
    ongoing_courses.sort()
    completed_courses.sort()
    
    return render_template("student.html", ongoing_courses=ongoing_courses, completed_courses=completed_courses)


@app.route("/student/courses")
def courses():
    student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    
    visible_courses = "(SELECT id FROM courses WHERE visible=:visible)"
    
    sql_enrolled_courses = "(SELECT course_id FROM courses_students WHERE student_id=:student_id AND course_id IN " + visible_courses + ")"
    sql_available_courses = "(SELECT vc.id FROM " + visible_courses + " as vc WHERE vc.id NOT IN " + sql_enrolled_courses + ")"
    sql_enrolled_courses_fields = "SELECT id, code, name, lang, lev, ects, lim, teacher_id FROM courses WHERE id IN " + sql_enrolled_courses
    sql_available_courses_fields = "SELECT id, code, name, lang, lev, ects, lim, teacher_id FROM courses WHERE id IN " + sql_available_courses
    
    enrolled_courses_from_db = db.session.execute(sql_enrolled_courses_fields, {"visible":1, "student_id":student_id}).fetchall()
    available_courses_from_db = db.session.execute(sql_available_courses_fields, {"visible":1, "student_id":student_id}).fetchall()
    
    available_courses = []
    for course in available_courses_from_db:
        teacher_id = course[7]
        teacher = db.session.execute("SELECT username FROM users WHERE id=:id", {"id":teacher_id}).fetchone()[0]
        string = course[1] + " " + course[2] + " (" + language_mapping[course[3]] + ", " + level_mapping[course[4]] + ", " + str(course[5]) + " ECTS, " + str(course[6]) + " % to complete, teacher: " + teacher + ")"
        available_courses.append((string, course[0]))
    enrolled_courses = []
    for course in enrolled_courses_from_db:
        teacher_id = course[7]
        teacher = db.session.execute("SELECT username FROM users WHERE id=:id", {"id":teacher_id}).fetchone()[0]
        string = course[1] + " " + course[2] + " (" + language_mapping[course[3]] + ", " + level_mapping[course[4]] + ", " + str(course[5]) + " ECTS, " + str(course[6]) + " % to complete, teacher: " + teacher + ")"
        enrolled_courses.append((string, course[0]))
    available_courses.sort()
    enrolled_courses.sort()
    
    return render_template("courses.html", available_courses=available_courses, enrolled_courses=enrolled_courses)


@app.route("/student/joincourse/<int:id>")
def joincourse(id):
    student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "INSERT INTO courses_students (course_id, student_id, completed) VALUES (:course_id, :student_id, :completed)"
    db.session.execute(sql, {"course_id":id, "student_id":student_id, "completed":0})
    db.session.commit()
    
    return redirect("/student")


@app.route("/student/leavecourse/<int:id>")
def leavecourse(id):
    sql = "SELECT code, name, lang, lev, ects, lim, teacher_id FROM courses WHERE id=:id"
    result = db.session.execute(sql, {"id":id}).fetchone()
    teacher_id = result[6]
    teacher = db.session.execute("SELECT username FROM users WHERE id=:id", {"id":teacher_id}).fetchone()[0]
    string = result[0] + " " + result[1] + " (" + language_mapping[result[2]] + ", " + level_mapping[result[3]] + ", " + str(result[4]) + " ECTS, " + str(result[5]) + " % to complete, teacher: " + teacher + ")"
    return render_template("leavecourse.html", id=id, course_description=string)


@app.route("/student/leavecourse/<int:id>/action", methods=["POST"])
def leavecourse_action(id):
    leaving = request.form["leaving"]
    if leaving == "yes":
        student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
        sql = "DELETE FROM courses_students WHERE student_id=:student_id and course_id=:course_id"
        db.session.execute(sql, {"student_id":student_id, "course_id":id})
        db.session.commit()
    return redirect("/student")


##### Functionality for 2nd release

@app.route("/student/course/<int:id>")
def course_student(id):
    # Authenticate
    try:
        username = session["username"]
        user_id, role = db.session.execute("SELECT id, role FROM users WHERE username=:username", {"username":username}).fetchone()
        if role != "student":
            return redirect("/")
        enrolled = db.session.execute("SELECT student_id FROM courses_students WHERE student_id=:student_id AND course_id=:course_id", {"student_id":user_id, "course_id":id}).fetchone()
        if enrolled == None: # not enrolled
            return redirect("/")
    except: # user not logged in
        return redirect("/")
    
    # Course parameters
    sql = "SELECT code, name, lang, lev, ects, lim, teacher_id FROM courses WHERE id=:id"
    result = db.session.execute(sql, {"id":id}).fetchone()
    teacher_id = result[6]
    teacher = db.session.execute("SELECT username FROM users WHERE id=:id", {"id":teacher_id}).fetchone()[0]
    header = result[0] + " " + result[1]
    parameters = "(" + language_mapping[result[2]] + ", " + level_mapping[result[3]] + ", " + str(result[4]) + " ECTS, " + str(result[5]) + " % to complete, teacher: " + teacher + ")"
    
    # Course material
    material_from_db = db.session.execute("SELECT material FROM materials WHERE course_id=:course_id", {"course_id":id}).fetchone()
    if material_from_db == None:
        material = ""
    else:
        material = material_from_db[0]
    
    # Course assignments
    
    
    return render_template("course-student.html", id=id, header=header, parameters=parameters, material=material)




