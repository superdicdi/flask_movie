import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy


__author__ = "TuDi"
__date__ = "2018/3/29 下午11:43"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:123456@127.0.0.1:3306/movie?charset=utf8"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["UP_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/")
app.config["SECRET_KEY"] = "12345678"
app.debug = True
db = SQLAlchemy(app)

from app.home import home
from app.admin import admin

app.register_blueprint(home)
app.register_blueprint(admin, url_prefix="/admin")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("home/404.html"), 404
