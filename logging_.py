from flask import redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash


from app import app
from app import db
from app import roles
from app import language_mapping
from app import level_mapping


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
        return render_template("index-error-login.html", message="Incorrect username")
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
            return render_template("index-error-login.html", message="Incorrect password")


@app.route("/createuser")
def createuser():
    return render_template("index-createuser.html")


@app.route("/createuser/action", methods=["POST"])
def createuser_action():
    username = request.form["username"]
    password = request.form["password"]
    if "role" not in request.form:
        return render_template("index-error-createuser.html", message="Role not chosen")
    else:
        role = request.form["role"]
    
    # Check username
    sql = "SELECT username FROM users WHERE username=:username"
    username_in_db = db.session.execute(sql, {"username":username}).fetchone()
    if username_in_db != None or username.strip() == "": # username in use or empty
        return render_template("index-error-createuser.html", message="Username in use")
    
    # Check password
    if password.strip() == "":
        return render_template("index-error-createuser.html", message="Password empty")
    
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


@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")




