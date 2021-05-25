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
        return render_template("wrong-username.html")
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
            return render_template("wrong-password.html")

@app.route("/newuser")
def newuser():
    return render_template("newuser.html")

@app.route("/createuser", methods=["POST"])
def createuser():
    username = request.form["username"]
    password = request.form["password"]
    if "teacher" not in request.form:
        return render_template("role-notchosen.html")
    else:
        teacher = request.form["teacher"]
    
    # Check username
    sql = "SELECT username FROM users WHERE username=:username"
    result = db.session.execute(sql, {"username":username})
    user = result.fetchone()
    if user != None or username.strip() == "": # username in use or empty
        return render_template("username-inuse.html")
    
    # Check password
    if password.strip() == "":
        return render_template("password-empty.html")
    
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









