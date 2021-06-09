from flask import redirect, render_template, request, session


from app import app
from app import db
from app import roles
from app import language_mapping
from app import level_mapping
from logging_ import logout


def authenticate_for_teacher_page():
    try:
        user_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
        role = db.session.execute("SELECT role FROM users WHERE id=:id", {"id":user_id}).fetchone()[0]
        if role == "student":
            return "error1"
        return user_id
    except: # not logged in
        return "error0"


def authenticate_teacher_for_course(user_id, course_id):
    course_teacher = db.session.execute("SELECT teacher_id FROM courses WHERE id=:id", {"id":course_id}).fetchone()[0]
    if user_id != course_teacher: # not own course
        return "error2"
    return None


def get_course_parameters_for_teacher(course_id):
    parameters = db.session.execute("SELECT code, name, lang, lev, ects, lim FROM courses WHERE id=:id", {"id":course_id}).fetchone()
    return_list = []
    return_list.append(course_id) # index 0
    return_list.append(parameters[0] + " " + parameters[1]) # index 1
    return_list.append("[" + language_mapping[parameters[2]] + " | " + level_mapping[parameters[3]] + " | " + str(parameters[4]) + " ECTS | " + str(parameters[5]) + " % to complete]") # index 2
    return return_list


@app.route("/teacher")
def teacher():
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    
    visible_courses_from_db = db.session.execute("SELECT id FROM courses WHERE teacher_id=:teacher_id AND visible=:visible", {"teacher_id":user_id, "visible":1}).fetchall()
    hidden_courses_from_db = db.session.execute("SELECT id FROM courses WHERE teacher_id=:teacher_id AND visible=:visible", {"teacher_id":user_id, "visible":0}).fetchall()
    
    visible_courses = []
    for course in visible_courses_from_db:
        parameters = get_course_parameters_for_teacher(course[0])
        string = parameters[1] + " " + parameters[2]
        visible_courses.append((string, parameters[0]))
    hidden_courses = []
    for course in hidden_courses_from_db:
        parameters = get_course_parameters_for_teacher(course[0])
        string = parameters[1] + " " + parameters[2]
        hidden_courses.append((string, parameters[0]))
    visible_courses.sort()
    hidden_courses.sort() 
    
    return render_template("teacher.html", visible_courses=visible_courses, hidden_courses=hidden_courses)


@app.route("/teacher/createcourse")
def teacher_createcourse():
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    
    return render_template("teacher-createcourse.html")


@app.route("/teacher/createcourse/action", methods=["POST"])
def teacher_createcourse_action():
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    
    coursename = request.form["coursename"]
    coursecode = request.form["coursecode"]
    if "language" not in request.form:
        return render_template("teacher-error-createcourse.html", message="Language not chosen")
    else:
        language = request.form["language"]
    if "level" not in request.form:
        return render_template("teacher-error-createcourse.html", message="Level not chosen")
    else:
        level = request.form["level"]
    ects = request.form["ects"]
    limit = request.form["limit"]
    
    # Check coursecode
    if coursecode.strip() == "":
        return render_template("teacher-error-createcourse.html", message="Course code not given")
    # Check coursename
    if coursename.strip() == "":
        return render_template("teacher-error-createcourse.html", message="Course name not given")
    # Check ects
    try:
        ects = int(ects)
        if ects < 0:
            return render_template("teacher-error-createcourse.html", message="Amount of ECTS entered incorrectly (enter integer, >=0)")
    except:
        return render_template("teacher-error-createcourse.html", message="Amount of ECTS entered incorrectly (enter integer, >=0)")
    # Check limit
    try:
        limit = int(limit)
        if limit < 0 or limit > 100:
            return render_template("teacher-error-createcourse.html", message="Limit to complete in % entered incorrectly (enter integer, >=0 and <=100)")
    except:
        return render_template("teacher-error-createcourse.html", message="Limit to complete in % entered incorrectly (enter integer, >=0 and <=100)")

    # Insert new course into db
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "INSERT INTO courses (code, name, teacher_id, lang, lev, ects, lim, visible) VALUES (:coursecode, :coursename, :teacher_id, :language, :level, :ects, :limit, :visible)"
    db.session.execute(sql, {"coursecode":coursecode, "coursename":coursename, "teacher_id":teacher_id, "language":language, "level":level, "ects":ects, "limit":limit, "visible":0})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/teacher/publishcourse/<int:id>")
def teacher_publishcourse(id):
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    if authenticate_teacher_for_course(user_id, id) == "error2":
        return redirect("/teacher")
    
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET visible=:visible WHERE teacher_id=:teacher_id and id=:id"
    db.session.execute(sql, {"visible":1, "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/teacher/hidecourse/<int:id>")
def teacher_hidecourse(id):
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    if authenticate_teacher_for_course(user_id, id) == "error2":
        return redirect("/teacher")
    
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET visible=:visible WHERE teacher_id=:teacher_id and id=:id"
    db.session.execute(sql, {"visible":0, "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/teacher/modifycourse/<int:id>")
def teacher_modifycourse(id):
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    if authenticate_teacher_for_course(user_id, id) == "error2":
        return redirect("/teacher")
    
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
    
    return render_template("teacher-modifycourse.html", id=id, coursecode=result[0], coursename=result[1], ENG=ENG, FIN=FIN, SWE=SWE, BAS=BAS, INT=INT, ADV=ADV, ects=result[4], limit=result[5])


@app.route("/teacher/modifycourse/<int:id>/action", methods=["POST"])
def teacher_modifycourse_action(id):
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    if authenticate_teacher_for_course(user_id, id) == "error2":
        return redirect("/teacher")
    
    coursename = request.form["coursename"]
    coursecode = request.form["coursecode"]
    language = request.form["language"]
    level = request.form["level"]
    ects = request.form["ects"]
    limit = request.form["limit"]
    
    # Check coursecode
    if coursecode.strip() == "":
        return render_template("teacher-error-modifycourse.html", message="Course code not given", id=id)
    # Check coursename
    if coursename.strip() == "":
        return render_template("teacher-error-modifycourse.html", message="Course name not given", id=id)
    # Check ects
    try:
        ects = int(ects)
        if ects < 0:
            return render_template("teacher-error-modifycourse.html", message="Amount of ECTS entered incorrectly (enter integer, >=0)", id=id)
    except:
        return render_template("teacher-error-modifycourse.html", message="Amount of ECTS entered incorrectly (enter integer, >=0)", id=id)
    # Check limit
    try:
        limit = int(limit)
        if limit < 0 or limit > 100:
            return render_template("teacher-error-modifycourse.html", message="Limit to complete in % entered incorrectly (enter integer, >=0 and <=100)", id=id)
    except:
        return render_template("teacher-error-modifycourse.html", message="Limit to complete in % entered incorrectly (enter integer, >=0 and <=100)", id=id)

    # Modify course in db
    teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "UPDATE courses SET code=:coursecode, name=:coursename, lang=:language, lev=:level, ects=:ects, lim=:limit WHERE teacher_id=:teacher_id and id=:id"
    db.session.execute(sql, {"coursecode":coursecode, "coursename":coursename, "language":language, "level":level, "ects":ects, "limit":limit, "teacher_id":teacher_id, "id":id})
    db.session.commit()
    
    return redirect("/teacher")


@app.route("/teacher/deletecourse/<int:id>")
def teacher_deletecourse(id):
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    if authenticate_teacher_for_course(user_id, id) == "error2":
        return redirect("/teacher")
    
    parameters = get_course_parameters_for_teacher(id)
    string = parameters[1] + " " + parameters[2]
    return render_template("teacher-deletecourse.html", id=id, course_description=string)


@app.route("/teacher/deletecourse/<int:id>/action", methods=["POST"])
def teacher_deletecourse_action(id):
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    if authenticate_teacher_for_course(user_id, id) == "error2":
        return redirect("/teacher")
    
    deletion = request.form["deletion"]
    if deletion == "yes":
        teacher_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
        sql = "DELETE FROM courses WHERE teacher_id=:teacher_id and id=:id"
        db.session.execute(sql, {"teacher_id":teacher_id, "id":id})
        db.session.commit()
    return redirect("/teacher")


######################### Functionality for 2nd release #########################

@app.route("/teacher/course/<int:id>")
def teacher_course(id):
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    if authenticate_teacher_for_course(user_id, id) == "error2":
        return redirect("/teacher")
    
    # Course parameters
    parameters = get_course_parameters_for_teacher(id)
    
    # Course material
    material_from_db = db.session.execute("SELECT material FROM materials WHERE course_id=:course_id", {"course_id":id}).fetchone()
    if material_from_db == None:
        material = ""
    else:
        material = material_from_db[0]
    
    # Course assignments
    
    
    return render_template("teacher-course.html", id=id, header=parameters[1], parameters=parameters[2], material=material)


@app.route("/teacher/course/<int:id>/modifymaterial")
def teacher_modifymaterial(id):
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    if authenticate_teacher_for_course(user_id, id) == "error2":
        return redirect("/teacher")
    
    # Course parameters
    parameters = get_course_parameters_for_teacher(id)
    
    # Course material
    material_from_db = db.session.execute("SELECT material FROM materials WHERE course_id=:course_id", {"course_id":id}).fetchone()
    if material_from_db == None:
        material = ""
    else:
        material = material_from_db[0]
    
    return render_template("teacher-modifymaterial.html", id=id, header=parameters[1], parameters=parameters[2], material=material)


@app.route("/teacher/course/<int:id>/modifymaterial/action", methods=["POST"])
def teacher_modifymaterial_action(id):
    #Authenticate
    user_id = authenticate_for_teacher_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/student")
    if authenticate_teacher_for_course(user_id, id) == "error2":
        return redirect("/teacher")

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




