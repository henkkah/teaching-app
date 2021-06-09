from flask import redirect, render_template, request, session


from app import app
from app import db
from app import roles
from app import language_mapping
from app import level_mapping
from app import assignment_types
from logging_ import logout


def authenticate_for_student_page():
    try:
        user_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
        role = db.session.execute("SELECT role FROM users WHERE id=:id", {"id":user_id}).fetchone()[0]
        if role != "student":
            return "error1"
        return user_id
    except: # not logged in
        return "error0"


def authenticate_student_for_course(user_id, course_id):
    enrolled = db.session.execute("SELECT student_id FROM courses_students WHERE student_id=:student_id AND course_id=:course_id", {"student_id":user_id, "course_id":course_id}).fetchone()
    if enrolled == None: # not enrolled
        return "error2"
    return None


# Returns [course_id, "header", "parameters"]
def get_course_parameters_for_student(course_id):
    parameters = db.session.execute("SELECT code, name, lang, lev, ects, lim, teacher_id FROM courses WHERE id=:id", {"id":course_id}).fetchone()
    teacher = db.session.execute("SELECT username FROM users WHERE id=:id", {"id":parameters[6]}).fetchone()[0]
    return_list = []
    return_list.append(course_id) # index 0
    return_list.append(parameters[0] + " " + parameters[1]) # index 1
    return_list.append("[" + language_mapping[parameters[2]] + " | " + level_mapping[parameters[3]] + " | " + str(parameters[4]) + " ECTS | " + str(parameters[5]) + " % to complete | teacher: " + teacher + "]") # index 2
    return return_list


@app.route("/student")
def student():
    #Authenticate
    user_id = authenticate_for_student_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/teacher")
    
    visible_courses = "(SELECT id FROM courses WHERE visible=:visible)"
    
    ongoing_courses_sql = "SELECT vc.id FROM " + visible_courses + " as vc, courses_students as cs WHERE vc.id = cs.course_id AND cs.student_id=:user_id AND cs.completed=:completed"
    completed_courses_sql = "SELECT vc.id FROM " + visible_courses + " as vc, courses_students as cs WHERE vc.id = cs.course_id AND cs.student_id=:user_id AND cs.completed=:completed"

    ongoing_courses_from_db = db.session.execute(ongoing_courses_sql, {"visible":1, "user_id":user_id, "completed":0})
    completed_courses_from_db = db.session.execute(completed_courses_sql, {"visible":1, "user_id":user_id, "completed":1})
    
    ongoing_courses = []
    for course in ongoing_courses_from_db:
        id, header, parameters = get_course_parameters_for_student(course[0])
        string = header + " " + parameters
        ongoing_courses.append((string, id))
    completed_courses = []
    for course in completed_courses_from_db:
        id, header, parameters = get_course_parameters_for_student(course[0])
        string = header + " " + parameters
        completed_courses.append((string, id))
    ongoing_courses.sort()
    completed_courses.sort()
    
    return render_template("student.html", ongoing_courses=ongoing_courses, completed_courses=completed_courses)


@app.route("/student/courses")
def student_courses():
    #Authenticate
    user_id = authenticate_for_student_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/teacher")
    
    student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    
    visible_courses = "(SELECT id FROM courses WHERE visible=:visible)"
    
    enrolled_courses_sql = "(SELECT course_id FROM courses_students WHERE student_id=:student_id AND course_id IN " + visible_courses + ")"
    available_courses_sql = "(SELECT vc.id FROM " + visible_courses + " as vc WHERE vc.id NOT IN " + enrolled_courses_sql + ")"
    
    enrolled_courses_from_db = db.session.execute(enrolled_courses_sql, {"visible":1, "student_id":student_id}).fetchall()
    available_courses_from_db = db.session.execute(available_courses_sql, {"visible":1, "student_id":student_id}).fetchall()
    
    available_courses = []
    for course in available_courses_from_db:
        id, header, parameters = get_course_parameters_for_student(course[0])
        string = header + " " + parameters
        available_courses.append((string, id))
    enrolled_courses = []
    for course in enrolled_courses_from_db:
        id, header, parameters = get_course_parameters_for_student(course[0])
        string = header + " " + parameters
        enrolled_courses.append((string, id))
    available_courses.sort()
    enrolled_courses.sort()
    
    return render_template("student-courses.html", available_courses=available_courses, enrolled_courses=enrolled_courses)


@app.route("/student/joincourse/<int:id>")
def student_joincourse(id):
    #Authenticate
    user_id = authenticate_for_student_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/teacher")
    
    student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    sql = "INSERT INTO courses_students (course_id, student_id, completed) VALUES (:course_id, :student_id, :completed)"
    db.session.execute(sql, {"course_id":id, "student_id":student_id, "completed":0})
    db.session.commit()
    
    return redirect("/student")


@app.route("/student/leavecourse/<int:id>")
def student_leavecourse(id):
    #Authenticate
    user_id = authenticate_for_student_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/teacher")
    if authenticate_student_for_course(user_id, id) == "error2":
        return redirect("/student")
    
    user_id = authenticate_for_student_page()
    if user_id == "error" or authenticate_student_for_course(user_id, id) == "error":
        return redirect("/")
    
    parameters = get_course_parameters_for_student(id)
    string = parameters[1] + " " + parameters[2]
    return render_template("student-leavecourse.html", id=id, course_description=string)


@app.route("/student/leavecourse/<int:id>/action", methods=["POST"])
def student_leavecourse_action(id):
    #Authenticate
    user_id = authenticate_for_student_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/teacher")
    if authenticate_student_for_course(user_id, id) == "error2":
        return redirect("/student")
    
    leaving = request.form["leaving"]
    if leaving == "yes":
        student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
        sql = "DELETE FROM courses_students WHERE student_id=:student_id and course_id=:course_id"
        db.session.execute(sql, {"student_id":student_id, "course_id":id})
        db.session.commit()
    return redirect("/student")


######################### Functionality for 2nd release #########################

@app.route("/student/course/<int:id>")
def student_course(id):
    #Authenticate
    user_id = authenticate_for_student_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/teacher")
    if authenticate_student_for_course(user_id, id) == "error2":
        return redirect("/student")
    
    # Course parameters
    parameters = get_course_parameters_for_student(id)
    
    # Course material
    material_from_db = db.session.execute("SELECT material FROM materials WHERE course_id=:course_id", {"course_id":id}).fetchone()
    if material_from_db == None:
        material = ""
    else:
        material = material_from_db[0]
    
    # Course assignments
    
    
    return render_template("student-course.html", id=id, header=parameters[1], parameters=parameters[2], material=material)




