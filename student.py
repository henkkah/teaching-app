from flask import redirect, render_template, request, session


from app import app
from app import db
from app import roles
from app import language_mapping
from app import language_mapping_reverse
from app import level_mapping
from app import level_mapping_reverse
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


# Returns [courses, completed]
def get_course_statistics_for_student1(student_id):
    courses, completed = db.session.execute("SELECT COUNT(id), SUM(completed) FROM courses_students WHERE student_id=:student_id", {"student_id":student_id}).fetchone()
    return (courses, completed)


# Returns [attempts, correct]
def get_course_statistics_for_student2(course_id, student_id):
    assignments_on_course_sql = "(SELECT id FROM assignments WHERE course_id=:course_id)"
    attempts_on_course_sql = "SELECT COUNT(id), SUM(correct) FROM attempts WHERE student_id=:student_id AND assignment_id IN " + assignments_on_course_sql
    attempts, correct = db.session.execute(attempts_on_course_sql, {"course_id":course_id, "student_id":student_id}).fetchone()
    return (attempts, correct)


@app.route("/student")
def student():
    #Authenticate
    user_id = authenticate_for_student_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/teacher")
    
    # Stats
    courses, completed = get_course_statistics_for_student1(user_id)
    if completed == None:
        completed = 0
    stats = str(courses) + " enrollments to courses, " + str(completed) + " completed"
    assignments_attempts = 0
    assignments_correct = 0
    
    visible_courses = "(SELECT id FROM courses WHERE visible=:visible)"
    
    ongoing_courses_sql = "SELECT vc.id FROM " + visible_courses + " as vc, courses_students as cs WHERE vc.id = cs.course_id AND cs.student_id=:user_id AND cs.completed=:completed"
    completed_courses_sql = "SELECT vc.id FROM " + visible_courses + " as vc, courses_students as cs WHERE vc.id = cs.course_id AND cs.student_id=:user_id AND cs.completed=:completed"

    ongoing_courses_from_db = db.session.execute(ongoing_courses_sql, {"visible":1, "user_id":user_id, "completed":0})
    completed_courses_from_db = db.session.execute(completed_courses_sql, {"visible":1, "user_id":user_id, "completed":1})
    
    ongoing_courses = []
    for course in ongoing_courses_from_db:
        id, header, parameters = get_course_parameters_for_student(course[0])
        attempts, correct = get_course_statistics_for_student2(course[0], user_id)
        if correct == None:
            correct = 0
        assignments_attempts += attempts
        assignments_correct += correct
        string = header + " " + parameters
        stats_c = str(attempts) + " attempts on assignments, " + str(correct) + " correct"
        ongoing_courses.append((string, stats_c, id))
    completed_courses = []
    for course in completed_courses_from_db:
        id, header, parameters = get_course_parameters_for_student(course[0])
        attempts, correct = get_course_statistics_for_student2(course[0], user_id)
        if correct == None:
            correct = 0
        assignments_attempts += attempts
        assignments_correct += correct
        string = header + " " + parameters
        stats_c = str(attempts) + " attempts on assignments, " + str(correct) + " correct"
        completed_courses.append((string, stats_c, id))
    ongoing_courses.sort()
    completed_courses.sort()
    
    stats += " - " + str(assignments_attempts) + " attempts on assignments, " + str(assignments_correct) + " correct"
    
    return render_template("student.html", ongoing_courses=ongoing_courses, completed_courses=completed_courses, stats=stats)


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
    
    # Data for filters
    languages = language_mapping.values()
    levels = level_mapping.values()
    teachers = db.session.execute("SELECT username FROM users WHERE role=:role", {"role":'teacher'}).fetchall()
    teachers = [teacher[0] for teacher in teachers]
    
    return render_template("student-courses.html", available_courses=available_courses, enrolled_courses=enrolled_courses, languages=languages, levels=levels, teachers=teachers)


@app.route("/student/courses/search", methods=["POST"])
def student_courses_search():
    #Authenticate
    user_id = authenticate_for_student_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/teacher")
    
    # Get query
    query = request.form["query"]
    query_c = query.lower().strip()
    courses = db.session.execute("SELECT id, code, name FROM courses").fetchall()
    found_search = []
    if query_c == "":
        search = False
        found_search = [course[0] for course in courses]
    else:
        search = True
        for course in courses:
            if query_c in course[1].lower() or query_c in course[2].lower():
                found_search.append(course[0])
    
    # Get filters
    filter = False
    languages = request.form.getlist("language")
    if len(languages) == 0:
        languages = language_mapping.keys()
        language_filter = ""
    else:
        filter = True
        language_filter = "language"
        for language in languages:
            language_filter += " '" + language + "'"
        languages = [language_mapping_reverse[lang] for lang in languages]
    if len(languages) == 1:
        languages = "('" + languages[0] + "')"
    else:
        languages = str(tuple(languages))
    
    levels = request.form.getlist("level")
    if len(levels) == 0:
        levels = level_mapping.keys()
        level_filter = ""
    else:
        filter = True
        level_filter = "level"
        for level in levels:
            level_filter += " '" + level + "'"
        levels = [level_mapping_reverse[lev] for lev in levels]
    if len(levels) == 1:
        levels = "('" + levels[0] + "')"
    else:
        levels = str(tuple(levels))
    
    ects_min = request.form["ects_min"]
    if ects_min != "":
        filter = True
        ects_min_filter = "ects_min '" + str(ects_min) + "'"
    else:
        ects_min_filter = ""
        ects_min = 0
    ects_max = request.form["ects_max"]
    if ects_max != "":
        filter = True
        ects_max_filter = "ects_max '" + str(ects_max) + "'"
    else:
        ects_max_filter = ""
        ects_max = db.session.execute("SELECT MAX(ects) FROM courses").fetchone()[0]

    limit_min = request.form["limit_min"]
    if limit_min != "":
        filter = True
        limit_min_filter = "limit_min '" + str(limit_min) + "'"
    else:
        limit_min_filter = ""
        limit_min = 0
    limit_max = request.form["limit_max"]
    if limit_max != "":
        filter = True
        limit_max_filter = "limit_max '" + limit_max + "'"
    else:
        limit_max_filter = ""
        limit_max = 100
    
    teacher = request.form["teacher"]
    if teacher == "":
        teacher_filter = ""
        teachers = db.session.execute("SELECT username FROM users WHERE role=:role", {"role":'teacher'}).fetchall()
        teachers = [teacher[0] for teacher in teachers]
    else:
        filter = True
        teacher_filter = "teacher '" + teacher + "'"
        teachers = [teacher]
    teachers_ids = []
    for teacher in teachers:
        teachers_ids.append(db.session.execute("SELECT id FROM users WHERE username=:username", {"username":teacher}).fetchone()[0])
    if len(teachers_ids) == 1:
        teachers_ids = "('" + str(teachers_ids[0]) + "')"
    else:
        teachers_ids = str(tuple(teachers_ids))
    
    
    # Handle filters
    sql = "SELECT id FROM courses WHERE lang IN " + languages + " AND lev IN " + levels + " AND ects >= " + str(ects_min) + " AND ects <= " + str(ects_max) + " AND lim >= " + str(limit_min) + " AND lim <= " + str(limit_max) + " AND teacher_id IN " + teachers_ids
    results = db.session.execute(sql).fetchall()
    found_filter = [result[0] for result in results]
    
    # Handle search and filter
    found = []
    for course in found_search:
        if course in found_filter:
            found.append(course)
    search_or_filter = search or filter
    
    student_id = db.session.execute("SELECT id FROM users WHERE username=:username", {"username":session["username"]}).fetchone()[0]
    
    visible_courses = "(SELECT id FROM courses WHERE visible=:visible)"
    
    enrolled_courses_sql = "(SELECT course_id FROM courses_students WHERE student_id=:student_id AND course_id IN " + visible_courses + ")"
    available_courses_sql = "(SELECT vc.id FROM " + visible_courses + " as vc WHERE vc.id NOT IN " + enrolled_courses_sql + ")"
    
    enrolled_courses_from_db = db.session.execute(enrolled_courses_sql, {"visible":1, "student_id":student_id}).fetchall()
    available_courses_from_db = db.session.execute(available_courses_sql, {"visible":1, "student_id":student_id}).fetchall()
    
    available_courses = []
    for course in available_courses_from_db:
        id, header, parameters = get_course_parameters_for_student(course[0])
        if id in found:
            string = header + " " + parameters
            available_courses.append((string, id))
    enrolled_courses = []
    for course in enrolled_courses_from_db:
        id, header, parameters = get_course_parameters_for_student(course[0])
        if id in found:
            string = header + " " + parameters
            enrolled_courses.append((string, id))
    available_courses.sort()
    enrolled_courses.sort()
    
    # Data for filters
    languages = language_mapping.values()
    levels = level_mapping.values()
    teachers = db.session.execute("SELECT username FROM users WHERE role=:role", {"role":'teacher'}).fetchall()
    teachers = [teacher[0] for teacher in teachers]
    
    return render_template("student-courses.html", available_courses=available_courses, enrolled_courses=enrolled_courses, languages=languages, levels=levels, teachers=teachers, 
                            search_or_filter=search_or_filter, search=search, query=query, language_filter=language_filter, level_filter=level_filter, ects_min_filter=ects_min_filter, ects_max_filter=ects_max_filter,
                            limit_min_filter=limit_min_filter, limit_max_filter=limit_max_filter, teacher_filter=teacher_filter)


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
    
    # Check if course should be marked completed
    row_id, completed = db.session.execute("SELECT id, completed FROM courses_students WHERE student_id=:student_id AND course_id=:course_id", {"student_id":user_id, "course_id":id}).fetchone()
    
    if completed == 0:
        completion_limit = db.session.execute("SELECT lim FROM courses WHERE id=:id", {"id":id}).fetchone()[0]
        
        course_assignments_sql = "(SELECT id FROM assignments WHERE course_id=:course_id)"
        students_correct_attempts_sql = "SELECT assignment_id FROM attempts WHERE student_id=:student_id AND assignment_id IN " + course_assignments_sql + " AND correct=:correct"
        
        course_assignments = db.session.execute(course_assignments_sql, {"course_id":id}).fetchall()
        course_assignments = [course_assignment[0] for course_assignment in course_assignments]
        students_correct_attempts = db.session.execute(students_correct_attempts_sql, {"student_id":user_id, "course_id":id, "correct":1}).fetchall()
        students_correct_attempts = [students_correct_attempt[0] for students_correct_attempt in students_correct_attempts]
        students_correct_attempts = set(students_correct_attempts)
        
        if 100.0 * len(students_correct_attempts) / len(course_assignments) >= completion_limit:
            db.session.execute("UPDATE courses_students SET completed=:completed WHERE id=:id", {"completed":1, "id":row_id})
            db.session.commit()
    # Check ends
    
    # Course parameters
    parameters = get_course_parameters_for_student(id)
    
    if completed == 1:
        completed = True
    else:
        completed = False
    
    # Course material
    material_from_db = db.session.execute("SELECT material FROM materials WHERE course_id=:course_id", {"course_id":id}).fetchone()
    if material_from_db == None:
        material = ""
    else:
        material = material_from_db[0]
    
    # Course assignments
    assignments_from_db = db.session.execute("SELECT id, question, answer, type_ FROM assignments WHERE course_id=:course_id", {"course_id":id}).fetchall()
    assignments = [] # (assignment_id, question, type, [choices], correct, attempts, answer)
    for assignment_from_db in assignments_from_db:
        assignment_id = assignment_from_db[0]
        question = assignment_from_db[1]
        answer = assignment_from_db[2]
        if assignment_from_db[3] == "multiple_choice":
            type_ = True
        else:
            type_ = False
        choices = []
        choices_from_db = db.session.execute("SELECT choice FROM choices WHERE assignment_id=:assignment_id", {"assignment_id":assignment_id}).fetchall()
        for choice in choices_from_db:
            if choice[0] == answer:
                choices.append((choice[0], "checked"))
            else:
                choices.append((choice[0], ""))
        attempts = db.session.execute("SELECT correct FROM attempts WHERE assignment_id=:assignment_id AND student_id=:student_id", {"assignment_id":assignment_id, "student_id":user_id}).fetchall()
        attempts = [attempt[0] for attempt in attempts]
        if sum(attempts) >= 1:
            correct = True
        else:
            correct = False
        len_attempts = len(attempts)
        assignments.append((assignment_id, question, type_, choices, correct, len_attempts, answer))
    
    return render_template("student-course.html", id=id, header=parameters[1], parameters=parameters[2], material=material, assignments=assignments, completed=completed)


@app.route("/student/course/<int:id>/answerassignment/<int:assignment_id>/action", methods=["POST"])
def student_answerassignment_action(id, assignment_id):
    #Authenticate
    user_id = authenticate_for_student_page()
    if user_id == "error0":
        return redirect("/")
    elif user_id == "error1":
        return redirect("/teacher")
    if authenticate_student_for_course(user_id, id) == "error2":
        return redirect("/student")
    
    if "answer" not in request.form:
        return render_template("/student/course/" + str(id))
    answer = request.form["answer"]
    
    # Check answer and insert attempt into db
    correct_answer = db.session.execute("SELECT answer FROM assignments WHERE id=:id", {"id":assignment_id}).fetchone()[0]
    if answer == correct_answer:
        sql = "INSERT INTO attempts (assignment_id, student_id, answer, correct, time_) VALUES (:assignment_id, :student_id, :answer, :correct, NOW())"
        db.session.execute(sql, {"assignment_id":assignment_id, "student_id":user_id, "answer":answer, "correct":1})
        db.session.commit()
    else: # incorrect answer
        sql = "INSERT INTO attempts (assignment_id, student_id, answer, correct, time_) VALUES (:assignment_id, :student_id, :answer, :correct, NOW())"
        db.session.execute(sql, {"assignment_id":assignment_id, "student_id":user_id, "answer":answer, "correct":0})
        db.session.commit()
    
    return redirect("/student/course/" + str(id))




