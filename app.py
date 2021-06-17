from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import getenv


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)


roles = ["teacher", "student"]
language_mapping = {"ENG":"English", "FIN":"Finnish", "SWE":"Swedish"}
language_mapping_reverse = {"English":"ENG", "Finnish":"FIN", "Swedish":"SWE"}
level_mapping = {"BAS":"Basic", "INT":"Intermediate", "ADV":"Advanced"}
level_mapping_reverse = {"Basic":"BAS", "Intermediate":"INT", "Advanced":"ADV"}
assignment_types = ["multiple_choice", "text_field"]


import logging_
import teacher
import student

